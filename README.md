# Portfolio — Emmanuel Froissant

Portfolio personnel sous la forme d'un bureau macOS imaginaire : écran de
veille, barre de menus, dock, icônes déplaçables, fenêtres, lecteur de
musique, et deux études de cas protégées par mot de passe.

---

## La technologie

**HTML, CSS et JavaScript, écrits à la main. Rien d'autre.**

Pas de React, pas de Vite, pas de Next.js, pas de npm, pas d'étape de
compilation. Tout l'interface tient dans un seul fichier de 255 Ko, à côté
de ses images et de ses sons.

Ce n'est pas un oubli, c'est le choix de départ. Un fichier unique n'a pas
de dépendances qui vieillissent, pas de build à réparer dans deux ans, et
se lit entièrement d'un bout à l'autre. Le seul outil du projet est un
petit script Python qui chiffre les études privées.

Les seules bibliothèques utilisées sont celles du navigateur :

| Ce qui est utilisé | Pour quoi |
|---|---|
| Web Animations API | ouverture et fermeture des fenêtres |
| Pointer Events | déplacement des icônes et des fenêtres |
| WebCrypto (AES-256-GCM, PBKDF2) | déchiffrement des études protégées |
| `<audio>` | lecteur de musique et son d'entrée |
| `localStorage` | mémorise le fond d'écran choisi |

---

## Les fichiers

```
index.html              toute l'interface : structure, styles, comportement
*.webp / *.jpg          images, chacune en deux tailles (1x et 2x)
*.mp3 / *.ogg           audio, chacun en deux formats
*.enc                   illustrations des études privées, chiffrées
cv-emmanuel-froissant.pdf
verrou.py               chiffre les études privées — outil, pas site
verrou-source/          textes et images en clair — JAMAIS EN LIGNE
```

Chaque image existe en WebP **et** en JPEG : le navigateur prend le format
qu'il comprend. Chaque son existe en Opus **et** en MP3, pour la même
raison. C'est pour ça qu'il y a autant de fichiers.

---

## Lancer le site en local

**Le double-clic ne suffit pas.** Ouvert directement depuis le disque, le
fichier est servi en `file://` : le navigateur considère alors la page et
ses images comme deux sites étrangers et bloque une partie des
fonctionnalités — dont le déchiffrement des études protégées.

Il faut servir le dossier. Dans le Terminal, une seule fois :

```bash
cd chemin/vers/le/dossier      # ou glisse le dossier dans la fenêtre
python3 -m http.server 8000
```

Puis ouvre <http://localhost:8000/index.html>.

Laisse la fenêtre du Terminal ouverte tant que tu travailles. `Ctrl-C`
pour arrêter.

---

## Fabriquer la version de production

**Il n'y a pas de build.** Les fichiers du dossier *sont* le site : ce que
tu vois en local est exactement ce qui sera en ligne.

Une seule opération est nécessaire avant chaque mise en ligne — poser le
mot de passe des études privées :

```bash
python3 verrou.py "le mot de passe à donner aux recruteurs"
```

Ce que fait le script, à chaque exécution :

1. tire un sel neuf et dérive une clé du mot de passe (PBKDF2, 250 000 tours) ;
2. compresse puis chiffre le texte de chaque étude protégée ;
3. chiffre les illustrations vers des fichiers `.enc` ;
4. **efface de la page les textes en clair** et retire du dossier les
   images en clair de ces études ;
5. remet l'interrupteur `VERROU_OUVERT` à `false`.

Le point 5 est un garde-fou : comme il faut lancer ce script pour poser un
mot de passe, une page préparée pour la mise en ligne ne peut pas rester
ouverte par accident.

Changer le mot de passe = relancer le script. Rien à modifier à la main.

---

## Vérifier avant d'envoyer

Trois points, dans cet ordre :

1. **`verrou-source/` n'est pas dans le dépôt.** Il est listé dans
   `.gitignore`. Vérifie-le une fois de plus avant le premier envoi : un
   fichier envoyé reste dans l'historique Git même après suppression.
2. **`VERROU_OUVERT` vaut `false`** dans `index.html`. S'il vaut
   `true`, les études privées sont ouvertes à tout le monde et le mot de
   passe est écrit en clair dans la page.
3. **Le mot de passe ne se trouve nulle part** dans les fichiers envoyés.
   Il vit dans ton CV envoyé par courriel, pas dans le dépôt.

---

## Mettre en ligne

Le site n'étant que des fichiers statiques, n'importe quel hébergeur
convient. Deux options gratuites :

**GitHub Pages** — dépôt public obligatoire en offre gratuite. Dans le
dépôt : `Settings` → `Pages` → source `main`, dossier `/ (root)`. L'adresse
sera `https://<ton-compte>.github.io/<nom-du-dépôt>/`.

**Netlify** — accepte les dépôts privés. Tu relies ton dépôt GitHub, tu
laisses les champs « build command » et « publish directory » vides
(puisqu'il n'y a pas de build), et c'est en ligne.

Le fichier servi par défaut à la racine s'appelle déjà `index.html` : les
deux hébergeurs le trouveront sans réglage.

---

## Ce qui reste à faire

- [x] Poser le vrai mot de passe (`verrou.py`)
- [x] Vérifier que le CV du site ne contient pas le mot de passe
- [ ] Remettre des morceaux dans le lecteur, ou griser Précédent /
      Suivant / Aléatoire tant qu'il n'y a qu'un seul titre
- [ ] Version mobile : la tuile « Logiciels » n'est pas encore atteignable
- [ ] Fond d'écran « Ciel rose »
- [ ] Encre adaptative : sur trois des quatre fonds, le texte blanc du
      bureau ne passe pas les seuils de contraste
