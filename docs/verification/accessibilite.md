# Accessibilité de l'interface de la V1 : grille WCAG 2.2 AA

> Statut : **v1.0**, proposée dans la PR de T90. Document vivant : toute tâche qui change la structure ou la feuille de style du rapport HTML repasse les critères qu'elle touche et l'inscrit à l'historique (§6).

Le rapport HTML vise WCAG 2.2 niveau AA ([ADR-0025](../decisions/ADR-0025-formats-export-et-accessibilite.md)). Cette grille donne, pour chaque critère des niveaux A et AA, son résultat et la façon dont il a été vérifié ([ADR-0256](../decisions/ADR-0256-verification-de-wcag-2-2-aa.md)) : outil (axe-core), calcul, inspection du code et du document, essai au clavier ou à une taille d'écran donnée. La ligne de commande est traitée à part (§4).

## 1. Ce qui a été essayé

| Élément | Valeur |
| --- | --- |
| Outil | axe-core 4.14.0 (publié le 2026-10-05), installé par `npm install --no-save --ignore-scripts axe-core@4.14.0` dans un dossier temporaire du poste, hors du dépôt ; `axe.min.js` de SHA-256 `20c09fe157a8a34a30e241aaa1fcdade657734f08ab379ecfbeb7d45cc46e878` |
| Règles d'axe-core | Étiquettes `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa` et `best-practice` |
| Navigateur | Navigateur intégré de l'application de bureau de Claude (Chromium), rapports servis sur 127.0.0.1 par `python3 -m http.server` |
| Affichages | Mode clair et mode sombre (`prefers-color-scheme` émulé) ; largeur du panneau du navigateur (de 370 à 1 009 px selon l'essai) et largeur de 320 px |
| Date | 2026-11-25, sur la branche `tache/T90-interface` |

Rapports essayés, écrits par `vk … --rapport` depuis les échantillons du dépôt :

| N° | Fichier | Particularité |
| --- | --- | --- |
| 1 | `tests/donnees/ela/collage_60_92.jpg` | Deux indices, carte ELA masquée par défaut |
| 2 | `tests/donnees/imagesbureau/libreoffice.docx` | Trois parties, dont deux extraites ; phrase de règle qui cite une longue adresse |
| 3 | `tests/donnees/revisions/signe_modifie.pdf` | Visualisations en tableaux (versions et objets changés) |
| 4 | `tests/donnees/caracteres/texte.docx`, `--reveler nom_de_fichier` | Alertes en tête (masquage levé) |
| 5 | `tests/donnees/ela/collage_60_92.jpg`, `--reveler contenu` | Carte ELA affichée, avec son alternative |

Procédure, à refaire pour une nouvelle vérification :

1. Écrire les rapports, puis une **copie** de chacun pour l'audit : la balise `<meta http-equiv="Content-Security-Policy" …>` y est retirée (elle interdit tout script, ADR-0094) et deux scripts sont ajoutés avant `</body>` : `axe.min.js` et le script d'audit ci-dessous. La page est sinon identique au rapport.
2. Ouvrir chaque copie, en mode clair puis sombre, à la largeur de la fenêtre puis à 320 px, et appeler `await __audit()` et `__refusion()` dans la console.
3. Faire le parcours au clavier (Tab) : lien d'évitement, sommaire, zones de défilement des tableaux.

```javascript
// Audit d'une copie de rapport : axe-core et contraste calculé de chaque élément qui porte
// du texte, son fond cherché dans ses ancêtres.
window.__audit = async function () {
  const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa',
    'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']}, resultTypes: ['violations', 'incomplete']});
  const rgb = s => s.match(/[\d.]+/g).map(Number);
  const lum = c => { const [x, y, z] = c.slice(0, 3).map(v => { v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * x + 0.7152 * y + 0.0722 * z; };
  const fond = e => { for (; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor);
    if (c.length < 4 || c[3] > 0) return c; } return [255, 255, 255]; };
  let min = 99, n = 0;
  for (const e of document.querySelectorAll('body *')) {
    if (![...e.childNodes].some(t => t.nodeType === 3 && t.textContent.trim())) continue;
    n++;
    const a = lum(rgb(getComputedStyle(e).color)), b = lum(fond(e));
    min = Math.min(min, (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05));
  }
  return {violations: r.violations.map(v => v.id + ' x' + v.nodes.length),
    incomplets: r.incomplete.map(v => v.id + ' x' + v.nodes.length), elementsTexte: n,
    contrasteMin: min.toFixed(2)};
};
// Refusion (1.4.10), espacement du texte (1.4.12), cibles du sommaire (2.5.8).
window.__refusion = function () {
  const d = document.documentElement;
  const cibles = [...document.querySelectorAll('nav a')].map(a => a.getBoundingClientRect())
    .filter(r => r.height < 24 || r.width < 24).length;
  const avant = {largeurPage: d.scrollWidth, fenetre: d.clientWidth, ciblesSous24: cibles};
  const st = document.createElement('style');
  st.textContent = '*{line-height:1.5!important;letter-spacing:.12em!important;' +
    'word-spacing:.16em!important}p{margin-bottom:2em!important}';
  document.head.appendChild(st);
  const coupes = [...document.querySelectorAll('body *')].filter(e => {
    const c = getComputedStyle(e);
    return (c.overflowY === 'hidden' || c.overflow === 'hidden') && e.scrollHeight > e.clientHeight + 1;
  }).length;
  const apres = {largeurPage: d.scrollWidth, elementsCoupes: coupes};
  st.remove();
  return {avant, espacement: apres};
};
```

## 2. Résultats d'ensemble

- **axe-core** : aucune violation sur les cinq rapports, en mode clair et sombre, à la largeur du panneau et à 320 px, après les corrections du §3. Seuls résultats « incomplets » : `color-contrast`, de 22 à 101 éléments selon le rapport, tous dans les zones de défilement des tableaux, dont axe-core ne détermine pas le fond ; le contraste de ces éléments est calculé par le script ci-dessus.
- **Contraste du texte**, calculé sur chacun des 580 à 1 323 éléments de texte de chaque rapport : au moins 8,04:1 en mode clair et 10,40:1 en mode sombre (le plus faible : le lien d'évitement, couleur des liens sur le fond). Contraste des traits (bordures, contour du focus) : de 5,3:1 à 8,8:1, calculé en T16 sur les mêmes couleurs, inchangées.
- **Refusion à 320 px** : la page ne défile pas horizontalement (largeur de la page égale à celle de la fenêtre) ; seuls les tableaux défilent, dans leur zone, ce que 1.4.10 admet pour un contenu à deux dimensions.
- **Espacement du texte** (valeurs de 1.4.12) : aucun débordement, aucun élément coupé.
- **Cibles** : liens du sommaire de 24 px de haut au moins, lien d'évitement de 24 px ; les 57 liens plus petits du rapport 2 sont des termes du glossaire, dans les listes de définitions, et aucun cercle de 24 px centré sur l'un d'eux ne touche une autre cible (exception d'espacement de 2.5.8).
- **Clavier** : le premier Tab mène au lien d'évitement, qui apparaît ; puis le sommaire, les liens et les zones de défilement dans l'ordre du document, chacun avec un contour de 3 px de la couleur des liens.

## 3. Défauts trouvés et corrigés en T90

| Défaut | Critère | Trouvé par | Correction |
| --- | --- | --- | --- |
| La rubrique « Observations » et la zone de son tableau portaient le même nom, « Observations » | Bonne pratique d'axe-core (`landmark-unique`), 1.3.1 | axe-core, rapport 1 | Légende du tableau : « Données relevées, une par ligne » |
| Un titre de constat qui cite une longue adresse débordait de 320 px | 1.4.10 | Mesure de la largeur, rapport 2 | Titres, paragraphes et éléments de liste coupables n'importe où, comme les valeurs et les cellules (ADR-0259) |
| Liens du sommaire de 22 px de haut | 2.5.8 | Mesure des cibles | Marges verticales de 0,2 rem (ADR-0259) |
| Contour du focus d'une zone de défilement laissé au navigateur | 2.4.7 | Inspection de la feuille de style | Même contour que les liens (ADR-0259) |

## 4. Grille des critères

Résultats : **C** conforme, **NA** non applicable (le rapport n'a ni média, ni formulaire, ni script, ni délai). Une seule page : les critères qui portent sur un ensemble de pages s'entendent ici d'un rapport à l'autre, tous écrits par le même gabarit.

### Perceptible

| Critère | Niveau | Résultat | Vérification |
| --- | --- | --- | --- |
| 1.1.1 Contenu non textuel | A | C | La seule image, la carte ELA, porte une alternative qui dit ce qu'elle est et où se lisent ses valeurs (rapport 5), précédée de son avertissement d'interprétation ; les visualisations des PDF sont des tableaux (rapport 3) |
| 1.2.1 à 1.2.3 Média temporel préenregistré | A | NA | Aucun son ni vidéo |
| 1.2.4, 1.2.5 Sous-titres en direct, audiodescription | AA | NA | Aucun son ni vidéo |
| 1.3.1 Information et relations | A | C | Titres de niveaux 1 à 3, rubriques en `section` nommées par leur titre, tableaux avec légende et en-têtes `scope="col"`, listes de définitions, listes ; `test_rapport.py`, axe-core |
| 1.3.2 Ordre séquentiel logique | A | C | L'ordre du document est l'ordre de lecture ; aucun positionnement ne le change, hors du lien d'évitement hors écran |
| 1.3.3 Caractéristiques sensorielles | A | C | Les textes renvoient aux rubriques par leur nom (« listés à la rubrique Couverture ») ; aucun ne repose sur la forme, la couleur ou la seule position |
| 1.3.4 Orientation | AA | C | Aucune orientation imposée |
| 1.3.5 Identifier la finalité des champs | AA | NA | Aucun champ de saisie |
| 1.4.1 Utilisation de la couleur | A | C | Les alertes ont un titre (« Attention ») et une bordure ; aucune information portée par la couleur seule |
| 1.4.2 Contrôle du son | A | NA | Aucun son |
| 1.4.3 Contraste (minimum) | AA | C | 8,04:1 au moins en clair, 10,40:1 en sombre, calculé sur chaque élément de texte |
| 1.4.4 Redimensionnement du texte | AA | C | Tailles en `rem`, aucune hauteur fixe ; à 320 px, ce qui vaut un grossissement de 400 % d'une fenêtre de 1 280 px, rien n'est perdu |
| 1.4.5 Texte sous forme d'image | AA | C | Aucun texte en image |
| 1.4.10 Redistribution | AA | C | Après correction (§3) : pas de défilement horizontal de la page à 320 px, hors des tableaux |
| 1.4.11 Contraste du contenu non textuel | AA | C | Traits et contour du focus de 5,3:1 à 8,8:1 ; la carte ELA est une mesure dont les teintes sont la donnée, décrite par son alternative et par les observations |
| 1.4.12 Espacement du texte | AA | C | Valeurs du critère appliquées : aucun débordement, aucune coupure |
| 1.4.13 Contenu au survol ou au focus | AA | NA | Aucun contenu qui apparaît au survol ; le lien d'évitement, qui apparaît au focus, reste jusqu'à ce que le focus le quitte et ne masque rien |

### Utilisable

| Critère | Niveau | Résultat | Vérification |
| --- | --- | --- | --- |
| 2.1.1 Clavier | A | C | Liens et zones de défilement des tableaux (`tabindex="0"`) atteints par Tab ; à 320 px, une zone qui déborde défile jusqu'au bout par la flèche droite (rapport 5) |
| 2.1.2 Pas de piège au clavier | A | C | Essai au clavier, rapport 4 |
| 2.1.4 Raccourcis clavier | A | NA | Aucun raccourci (aucun script) |
| 2.2.1 Réglage du délai | A | NA | Aucun délai |
| 2.2.2 Mettre en pause, arrêter, masquer | A | NA | Aucun contenu animé |
| 2.3.1 Pas plus de trois flashs | A | NA | Aucun contenu animé |
| 2.4.1 Contourner des blocs | A | C | Lien d'évitement vers le résumé, qui passe le sommaire ; rubriques en régions nommées |
| 2.4.2 Titre de page | A | C | « Rapport d'analyse — format réel » |
| 2.4.3 Parcours du focus | A | C | Ordre du document ; essai au clavier |
| 2.4.4 Fonction du lien | A | C | Liens du sommaire nommés par leur rubrique ; liens du glossaire par leur terme |
| 2.4.5 Accès multiples | AA | NA | Une seule page ; le sommaire et les titres y donnent deux accès à chaque rubrique |
| 2.4.6 En-têtes et étiquettes | AA | C | Rubriques nommées ; chaque constat titré par sa phrase |
| 2.4.7 Visibilité du focus | AA | C | Contour de 3 px sur les liens et, après correction (§3), sur les zones de défilement ; essai au clavier |
| 2.4.11 Focus non masqué (minimum) | AA | C | Aucun élément fixe ou collant |
| 2.5.1 Gestes pour le contrôle du pointeur | A | NA | Aucun geste |
| 2.5.2 Annulation de l'action du pointeur | A | C | Liens natifs, activés au relâchement |
| 2.5.3 Étiquette dans le nom | A | C | Nom de chaque lien égal à son texte ; nom de chaque zone de défilement égal à la légende de son tableau |
| 2.5.4 Activation par le mouvement | A | NA | Aucune |
| 2.5.7 Mouvements de glissement | AA | NA | Aucun |
| 2.5.8 Taille de la cible (minimum) | AA | C | Après correction (§3) : sommaire et lien d'évitement de 24 px au moins ; termes du glossaire sous l'exception d'espacement |

### Compréhensible

| Critère | Niveau | Résultat | Vérification |
| --- | --- | --- | --- |
| 3.1.1 Langue de la page | A | C | `<html lang="fr">` |
| 3.1.2 Langue d'un passage | AA | C | Les passages dans une autre langue sont des noms propres (« Video Seal », « C2PA Trust List ») ou des valeurs lues dans le fichier, de langue inconnue : le critère les excepte |
| 3.2.1 Au focus | A | C | Aucun changement de contexte au focus |
| 3.2.2 À la saisie | A | NA | Aucune saisie |
| 3.2.3 Navigation cohérente | AA | C | Même sommaire, dans le même ordre, pour chaque rapport |
| 3.2.4 Identification cohérente | AA | C | Mêmes libellés pour les mêmes fonctions d'un rapport à l'autre (`textes.toml`) |
| 3.2.6 Aide cohérente | A | NA | Aucun mécanisme d'aide |
| 3.3.1 Identification des erreurs | A | NA | Aucune saisie |
| 3.3.2 Étiquettes ou instructions | A | NA | Aucune saisie |
| 3.3.3 Suggestion après une erreur | AA | NA | Aucune saisie |
| 3.3.4 Prévention des erreurs | AA | NA | Aucune saisie |
| 3.3.7 Saisie redondante | A | NA | Aucune saisie |
| 3.3.8 Authentification accessible (minimum) | AA | NA | Aucune authentification |

### Robuste

| Critère | Niveau | Résultat | Vérification |
| --- | --- | --- | --- |
| 4.1.2 Nom, rôle et valeur | A | C | Éléments natifs ; zones de défilement `role="region"` nommées ; axe-core |
| 4.1.3 Messages d'état | AA | NA | Document statique |

Le critère 4.1.1 (analyse syntaxique) est retiré de WCAG 2.2 ; les identifiants du document sont uniques, ce que vérifie axe-core (`duplicate-id`).

## 5. Ligne de commande

WCAG s'applique au contenu web ; la ligne de commande est vérifiée par analogie, sur les points qui la concernent :

- Aucune information portée par la couleur, ni par la mise en forme : la sortie est du texte brut, sans séquence d'échappement (ADR-0025) ; les caractères invisibles d'un fichier sont montrés sous une forme visible (ADR-0096).
- Chaque fichier est repéré par son rang (« [2/3] »), chaque ligne de son résumé commence par ce qu'elle dit (« format réel », « partie 1, techniques appliquées », « non menée »), ce qu'un lecteur d'écran lit ligne à ligne.
- Le résumé ne nomme que ce qui a été fait ou non fait, les non applicables comptées (ADR-0258) ; les techniques sont nommées en langage courant (ADR-0257) ; les nombres s'accordent.
- Aucun délai : `--texte` attend la fin de l'entrée et le dit (« Collez le texte à analyser, puis Ctrl-D… »).
- Les refus et les erreurs s'écrivent sur la sortie d'erreur, au rang du fichier, avec leur raison.

Limites relevées, laissées à la documentation utilisateur (T103) : les codes de sortie ne sont décrits que dans le module `cli`, pas dans `vk --help` ; les messages qu'écrit `argparse` lui-même (« usage: », « options: », erreurs de syntaxe d'une commande) restent en anglais, Python ne livrant pas leur traduction française.

## 6. Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-11-25 | 1.0 | Création : grille de WCAG 2.2 AA, cinq rapports, axe-core 4.14.0 ; quatre défauts corrigés | T90 |
