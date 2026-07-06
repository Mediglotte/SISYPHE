# SISYPHE — dépôt prêt à publier (application mobile PWA)

Ce dossier contient **tout le nécessaire** pour mettre SISYPHE en ligne et le rendre
**installable** sur téléphone (Android / iPhone) et ordinateur, **utilisable hors-ligne**.

Vous n'avez rien à modifier dans les fichiers. Il suffit de **publier ce dossier**
sur GitHub puis d'**activer GitHub Pages**. Comptez ~10 minutes la première fois.

---

## ⚠️ À savoir avant de commencer
Pour que la publication soit **gratuite**, le dépôt doit être **public**
(sur un compte GitHub gratuit, GitHub Pages ne fonctionne pas sur un dépôt privé).
Le code de SISYPHE est déjà libre de droit, donc c'est sans souci.

---

## Étape 1 — Publier le dossier avec GitHub Desktop

1. Rangez ce dossier `sisyphe-app` à un endroit **permanent** de votre ordinateur
   (par ex. `Documents`), pas dans les téléchargements temporaires.
2. Ouvrez **GitHub Desktop**.
3. Menu **File → Add local repository…**
4. Cliquez **Choose…** et sélectionnez le dossier `sisyphe-app`, puis **Add repository**.
5. GitHub Desktop dira que ce n'est pas encore un dépôt Git et proposera
   **« create a repository »** (créer un dépôt ici) → cliquez dessus.
6. Sur l'écran de création, laissez les champs par défaut et cliquez
   **Create repository**.
7. En haut, cliquez **Publish repository**.
   - **Décochez** « Keep this code private » (le dépôt doit être **public**, voir plus haut).
   - Laissez le nom `sisyphe-app` (ou choisissez le vôtre) → **Publish repository**.

✅ Votre code est maintenant en ligne sur GitHub.

---

## Étape 2 — Activer GitHub Pages (mise en ligne du site)

1. Dans GitHub Desktop : menu **Repository → View on GitHub** (ouvre la page du dépôt
   dans votre navigateur). Connectez-vous si demandé.
2. Sur la page du dépôt, cliquez l'onglet **Settings** (roue dentée, en haut).
3. Dans le menu de gauche, cliquez **Pages**.
4. Sous **Build and deployment → Source**, choisissez **« Deploy from a branch »**.
5. **Branch** : sélectionnez **main**, dossier **/ (root)** → **Save**.
6. Patientez ~1 minute puis **rafraîchissez la page**. Une bannière affiche :
   *« Your site is live at … »* avec une adresse du type
   **`https://VOTRE-COMPTE.github.io/sisyphe-app/`**.

✅ SISYPHE est en ligne. Notez / copiez cette adresse.

---

## Étape 3 — Installer l'application sur le téléphone

Ouvrez l'adresse ci-dessus dans le navigateur du téléphone :

- **Android (Chrome)** : menu **⋮** → **« Installer l'application »**
  (ou « Ajouter à l'écran d'accueil »).
- **iPhone (Safari)** : bouton **Partager** (carré avec flèche) → **« Sur l'écran d'accueil »**.

Une icône SISYPHE apparaît sur l'écran d'accueil. **Après cette première ouverture
en ligne, l'application fonctionne hors-ligne.**

---

## Mettre à jour SISYPHE plus tard

Quand une nouvelle version du fichier est disponible (ex. après la veille hebdomadaire) :

1. Remplacez le fichier **`index.html`** de ce dossier par le nouveau
   (renommez le `sisyphe.html` mis à jour en `index.html`).
2. Dans GitHub Desktop, la modification apparaît à gauche. En bas à gauche,
   écrivez un petit résumé (ex. « maj veille ») puis **Commit to main**.
3. Cliquez **Push origin** (en haut).

Le site se met à jour tout seul en ~1 minute. Les utilisateurs connectés reçoivent
la nouvelle version à l'ouverture suivante.

> 💡 Après une **grosse** mise à jour, ouvrez `service-worker.js` et changez la ligne
> `const CACHE = 'sisyphe-v1';` en `'sisyphe-v2'` (puis `v3`, etc.) : cela force le
> rafraîchissement du cache hors-ligne sur les téléphones.

---

## Bon à savoir

- **Hors-ligne / fichier seul** : `index.html` reste utilisable seul, en le double-cliquant
  (sans Internet). Les fonctions PWA (installation, cache) ne s'activent qu'en ligne (HTTPS),
  c'est normal.
- **Polices** : chargées en ligne, avec repli automatique sur les polices du système
  hors-ligne (aucun impact sur le contenu clinique).
- **Confidentialité** : aucune donnée patient n'est envoyée ; tout reste sur l'appareil.

---

## Contenu du dossier
```
index.html               SISYPHE (l'application complète, un seul fichier)
manifest.webmanifest     identité de l'app (nom, couleurs, icônes)
service-worker.js        cache hors-ligne
.nojekyll                indique à GitHub de publier les fichiers tels quels
icons/                   icônes (avec texte en grand, sans texte en petit)
LICENSE                  licence d'utilisation
```

_SISYPHE — créé par le Dr Pierre BALAZ. Outil libre, non commercial, au service des soignants._
