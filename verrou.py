#!/usr/bin/env python3
"""Chiffre les études de cas protégées et les injecte dans index.html.

    python3 verrou.py "mon nouveau mot de passe"

Ce que fait le script, à chaque exécution :

  1. tire un sel neuf, dérive une clé du mot de passe (PBKDF2-SHA256,
     250 000 itérations) et fabrique un jeton de vérification ;
  2. compresse puis chiffre le texte de chaque étude protégée
     (verrou-source/<id>.html) et le pose dans la page en base64 ;
  3. chiffre chaque illustration de verrou-source/medias/ vers un
     fichier .enc à côté de index.html ;
  4. efface de index.html le texte en clair, et du dossier de
     publication les images en clair de ces études.

Le dossier verrou-source/ est ta copie de travail. Il contient les textes
et les images en clair : NE LE METS PAS EN LIGNE. Seuls index.html,
les .enc et les médias des parties publiques doivent être téléversés.

Changer le mot de passe = relancer ce script. Rien à modifier à la main.
"""

import base64, glob, gzip, hashlib, os, re, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

RACINE     = os.path.dirname(os.path.abspath(__file__))
PAGE       = os.path.join(RACINE, 'index.html')
# verrou-source vit UN CRAN AU-DESSUS du dépôt, volontairement.
#
# Tant qu'il était à l'intérieur, ne pas le publier reposait sur une règle
# — une ligne de .gitignore — et une règle peut ne pas être copiée. Elle ne
# l'a pas été, et les textes en clair sont partis sur GitHub.
#
# Dehors, Git ne peut pas l'atteindre : ce n'est plus une interdiction, c'est
# une impossibilité. On garde quand même la ligne dans .gitignore, au cas où
# le dossier reviendrait un jour à l'intérieur.
SOURCE     = os.path.join(RACINE, '..', 'verrou-source')
if not os.path.isdir(SOURCE):                 # disposition d'avant
    SOURCE = os.path.join(RACINE, 'verrou-source')
MEDIAS     = os.path.join(SOURCE, 'medias')
ETUDES     = ('loblaw', 'roche')
ITERATIONS = 250_000

DEBUT = '  <!-- PAQUETS CHIFFRÉS — produits par verrou.py, ne pas modifier -->'
FIN   = '  <!-- /PAQUETS CHIFFRÉS -->'

b64 = lambda o: base64.b64encode(o).decode()


def bornes_doc(html, idc):
    """Les bornes du <div class="doc" id="doc-<idc>"> en comptant les div."""
    a = html.find('id="doc-%s"' % idc)
    if a < 0:
        raise SystemExit('étude introuvable dans la page : ' + idc)
    a = html.rfind('<div', 0, a)
    prof, j = 0, a
    while True:
        m = re.compile(r'</?div\b').search(html, j)
        if not m:
            raise SystemExit('div non refermée : ' + idc)
        prof += 1 if m.group(0) == '<div' else -1
        j = m.end()
        if prof == 0:
            return a, j


def vider_page(html, idc):
    """Remplace le contenu de l'<article class="doc__page"> par du vide."""
    a, z = bornes_doc(html, idc)
    doc = html[a:z]
    ka = doc.find('>', doc.find('<article class="doc__page">')) + 1
    kz = doc.rfind('</article>')
    if ka <= 0 or kz < ka:
        raise SystemExit('article introuvable : ' + idc)
    return html[:a] + doc[:ka] + '\n' + doc[kz:] + html[z:]


def main():
    # Ce script change la serrure. Il ne doit jamais le faire sur un
    # malentendu : pas de mot de passe par défaut, pas d'argument accepté à
    # la légère. « python3 verrou.py --aide » a déjà chiffré tout un dossier
    # avec « --aide » pour mot de passe — d'où les trois garde-fous ci-dessous.
    if len(sys.argv) != 2:
        raise SystemExit(
            'Usage :  python3 verrou.py "ton mot de passe"\n'
            'Un seul argument, entre guillemets. Aucune valeur par défaut :\n'
            'poser une serrure est un geste qui se déclare.')
    mdp = sys.argv[1]
    if mdp.startswith('-'):
        raise SystemExit(
            'Un mot de passe qui commence par « - » ressemble à une option.\n'
            'Ce script n’en a aucune. Si c’est vraiment ton mot de passe,\n'
            'change-le : il te posera le même doute dans six mois.')
    if len(mdp) < 8:
        raise SystemExit('Mot de passe trop court : 8 caractères au minimum.')

    # Dernière porte, sautée quand l'entrée n'est pas un terminal (script).
    if sys.stdin.isatty():
        print('Nouveau mot de passe : %s%s%s  (%d caractères)'
              % (mdp[0], '•' * (len(mdp) - 2), mdp[-1], len(mdp)))
        print('Les études seront rechiffrées et l’ancien mot de passe cessera')
        print('de fonctionner immédiatement.')
        if input('Continuer ? (oui/non) ').strip().lower() not in ('oui', 'o'):
            raise SystemExit('Annulé — rien n’a été touché.')

    html = open(PAGE, encoding='utf-8').read()

    sel = os.urandom(16)
    cle = hashlib.pbkdf2_hmac('sha256', mdp.encode(), sel, ITERATIONS, 32)
    aes = AESGCM(cle)

    iv_jeton = os.urandom(12)
    jeton = aes.encrypt(iv_jeton, b'deverrouille', None)

    # ---- 1. les textes -----------------------------------------------------
    paquets, poids_txt = [], 0
    for idc in ETUDES:
        chemin = os.path.join(SOURCE, '%s.html' % idc)
        if not os.path.exists(chemin):
            raise SystemExit('source manquante : ' + chemin)
        clair = open(chemin, 'rb').read()
        # mtime figé : deux exécutions du script sur un texte inchangé
        # produisent alors le même gzip, ce qui rend les diffs lisibles.
        tasse = gzip.compress(clair, mtime=0)
        iv = os.urandom(12)
        paquets.append(
            '  <script type="application/octet-stream" data-paquet="%s" data-iv="%s">%s</script>'
            % (idc, b64(iv), b64(aes.encrypt(iv, tasse, None))))
        poids_txt += len(clair)
        html = vider_page(html, idc)

    bloc = '\n'.join([DEBUT] + paquets + [FIN, ''])
    if DEBUT in html:
        a = html.find(DEBUT)
        z = html.find(FIN, a) + len(FIN) + 1
        html = html[:a] + bloc + html[z:]
    else:
        ancre = '  <!-- ============ VEILLE ============ -->'
        if ancre not in html:
            raise SystemExit('ancre d’insertion introuvable')
        html = html.replace(ancre, bloc + '\n' + ancre, 1)

    # ---- 2. les illustrations ----------------------------------------------
    n_img, poids_img = 0, 0
    for src in sorted(glob.glob(os.path.join(MEDIAS, '*'))):
        nom = os.path.basename(src)
        octets = open(src, 'rb').read()
        iv = os.urandom(12)
        open(os.path.join(RACINE, nom + '.enc'), 'wb').write(iv + aes.encrypt(iv, octets, None))
        n_img += 1
        poids_img += len(octets)
        # les versions en clair quittent le dossier de publication
        base = re.sub(r'-\d+\.\w+$', '', nom)
        for clair in glob.glob(os.path.join(RACINE, base + '-*.webp')) + \
                     glob.glob(os.path.join(RACINE, base + '-*.jpg')):
            os.remove(clair)

    # ---- 3. le sel et le jeton ---------------------------------------------
    for cle_js, val in (('sel', b64(sel)), ('jetonIv', b64(iv_jeton)),
                        ('jeton', b64(jeton))):
        motif = r"(%s: ')[^']*(')" % cle_js
        if not re.search(motif, html):
            raise SystemExit('champ VERROU introuvable : ' + cle_js)
        html = re.sub(motif, lambda m: m.group(1) + val + m.group(2), html, count=1)
    html = re.sub(r'(iter: )\d+', r'\g<1>%d' % ITERATIONS, html, count=1)

    # Garde-fou : l'interrupteur de travail est remis à false à chaque
    # exécution. Comme il faut lancer ce script pour poser un mot de passe,
    # une page préparée pour la mise en ligne ne peut pas rester ouverte.
    html, n_switch = re.subn(r'const VERROU_OUVERT = true;',
                             'const VERROU_OUVERT = false;', html)

    open(PAGE, 'w', encoding='utf-8').write(html)

    print('Mot de passe    : %s' % ('•' * len(mdp)))
    print('Textes chiffrés : %d études, %d caractères' % (len(ETUDES), poids_txt))
    print('Images chiffrées: %d fichiers, %d Ko' % (n_img, poids_img // 1024))
    print('Page            : %d Ko' % (len(html) // 1024))
    if n_switch:
        print('Mode travail    : refermé (VERROU_OUVERT remis à false)')
    print('\nÀ publier : index.html, les *.enc, et les médias des parties'
          '\npubliques. Jamais verrou-source/.')


if __name__ == '__main__':
    main()
