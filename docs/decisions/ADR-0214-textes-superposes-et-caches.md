# ADR-0214 — Textes superposés et caches : texte sur un texte différent, rectangle opaque sur un texte, apparences des annotations comprises

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (seuils, exclusions et annotations précisés par l'assistant)
- **Tâche** : T51
- **Exigences liées** : F-61, P-02 ; ADR-0208, ADR-0211, ADR-0213

## Contexte

« Textes superposés » (F-61) désigne la retouche la plus courante d'un PDF : écrire un nouveau texte (un montant, une date, un nom) à la place de celui d'origine, soit par-dessus, soit après l'avoir caché sous un rectangle de la couleur du fond. L'outil peut ajouter son texte au contenu de la page, ou dans l'apparence d'une annotation (texte libre, tampon) que T50 range parmi les ajouts permis (ADR-0208). Une mise en page ordinaire pose ses textes côte à côte et peint ses fonds avant le texte.

## Options envisagées

### Option A — Texte sur texte et caches (recommandée)

Deux textes différents dont les boîtes se recouvrent au moins à moitié (le même texte légèrement décalé, faux gras ou ombre, exclu) ; un rectangle plein et opaque peint sur un texte déjà posé (cache), avec ou sans nouveau texte dessus. Le texte invisible (mode 3, couche d'un document numérisé) est exclu.

- Avantages : couvre les deux façons de remplacer un texte ; le caviardage qui laisse le texte ressort aussi.
- Inconvénients : il faut l'état des chemins et de l'opacité en plus de celui du texte.

### Option B — Texte sur texte seul

- Avantages : plus simple.
- Inconvénients : un texte caché sous un rectangle, sans nouveau texte exactement dessus, n'est pas vu.

### Option C — Flux ajoutés seuls

Les textes posés par un flux de contenu qu'une version ultérieure ajoute à une page, sans calcul de position.

- Avantages : aucun calcul géométrique.
- Inconvénients : rien sur un document réécrit d'un seul tenant après retouche ; redit en partie R-REVISIONSPDF-002.

## Décision

Option A. Précisions de l'assistant :

- **Recouvrement** : au moins la moitié (`RECOUVREMENT`) de la plus petite des deux boîtes pour deux textes ; de la boîte du texte pour un cache. Un texte n'est compté qu'une fois, au premier texte qu'il recouvre ; un texte caché, au premier rectangle.
- **Signes** : les espaces (code 32 d'une police simple) ne sont pas des signes ; un texte sans signe n'est pas comparé. Quand l'un des deux textes n'a qu'un signe, le recouvrement est compté à part (`pagespdf.superpositions_d_un_signe`), sans règle : les accents posés à part et les symboles composés en font autant.
- **Même texte** : deux textes aux mêmes codes ne comptent pas (faux gras, ombre, texte redit).
- **Rectangle** : opérateur `re`, ou quatre segments aux côtés alignés sur les axes, refermés ou non, rempli (`f`, `F`, `f*`, `B`, `B*`, `b`, `b*`) d'une peinture opaque : `/ca` de 1, mode de fusion `Normal` ou `Compatible`, sans masque doux. Un rectangle qui ne reste pas aligné sur les axes après la matrice (rotation autre qu'un quart de tour) n'est pas compté. La couleur n'est pas comparée au fond.
- **Annotations** : l'apparence normale (`/AP /N`, celle de `/AS` s'il y en a plusieurs) de chaque annotation visible est interprétée après le contenu de la page, placée dans son rectangle (§12.5.5) ; les champs de formulaire (`Widget`) et les fenêtres (`Popup`) ne le sont pas, ni une annotation invisible, cachée ou non vue (`/F`).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- B écartée : laisse passer le cache sans texte exactement superposé, et le caviardage qui laisse le texte.
- C écartée : ne voit pas une retouche réécrite d'un seul tenant ; la chronologie de T50 dit déjà quelles versions changent le contenu.
- Annotations comprises : sans elles, un texte posé par une annotation de texte libre passerait pour un ajout permis (limite d'ADR-0208 et de R-REVISIONSPDF-002, attaques « par ombre ») ; champs de formulaire exclus, parce qu'un champ est d'ordinaire posé sur une zone d'attente (trait, cadre, texte « à remplir ») qu'il recouvre par construction.
- Un signe à part : un chiffre changé seul est une retouche possible, mais un accent posé sur une lettre est courant ; le compte reste aux observations pour le lecteur.

## Conséquences

- Règles R-PAGESPDF-001 et R-PAGESPDF-002 (ADR-0218).
- Les mises en page qui superposent des textes (formulaire aplati, filigrane textuel, surimpression) déclenchent R-PAGESPDF-001 ; la mesure sur le corpus (T100) dira à quelle fréquence.
- Une image, une forme courbe ou un dégradé posés sur un texte ne sont pas des caches dans cette version.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T51 |
