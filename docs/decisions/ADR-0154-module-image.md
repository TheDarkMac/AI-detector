# ADR-0154 — Module `image` et forme des règles de transfert

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T24, validée pendant la revue de la PR de T24
- **Tâche** : T24
- **Exigences liées** : F-06, F-14, F-30, NF-10, ES-19 ; A-32, A-34 ; ADR-0042, ADR-0114, ADR-0115, ADR-0147, ADR-0150, ADR-0153

## Contexte

ADR-0153 retient des règles qui lisent les dimensions réelles d'une image, le nombre de ses blocs de métadonnées et ses tables de quantification. Aucun module ne les observe : le lecteur de conteneurs (`_lecture/conteneurs.py`, ADR-0115) ne relève que les blocs de métadonnées, et une règle ne compare que les observations d'un même module (ADR-0147). Restait à dire où les lire, et la forme précise des règles que la question laissait ouverte.

## Options envisagées

### Où lire dimensions, métadonnées et tables

- **A — Un module `image`, sur le lecteur de conteneurs étendu** : le lecteur relève aussi les blocs de structure (SOF et DQT d'un JPEG, `IHDR` d'un PNG, `VP8X`, `"VP8 "`, `VP8L` d'un WebP) sous deux natures nouvelles, que les modules de métadonnées ignorent ; le module `image` lit ces blocs et compte les autres. Avantages : un seul parcours de conteneur, déjà fuzzé et borné ; toutes les observations d'une règle dans un module ; les modules de métadonnées inchangés. Inconvénient : le lecteur partagé change.
- **B — Dans le module `exif`** : il connaît déjà le JPEG. Inconvénients : les dimensions et les tables ne sont pas de l'EXIF ; une image sans EXIF, le cas visé, n'aurait plus de sens dans ce module.
- **C — Comparaison entre modules** (absences de `exif`, `xmp`, `iptc` combinées) : point ouvert de l'architecture (§12), que T23 n'a pas écrit ; plus lourd que le compte des blocs.

### Recompression

- **A — Tables de libjpeg reconnues à l'identique** : la table 0 est celle de luminance de l'annexe K mise à l'échelle par libjpeg à une qualité de 1 à 100, la table 1 celle de chrominance à la même qualité. Avantages : déterministe ; chaque qualité donne une table différente, donc une qualité unique ; vérifiable contre ImageMagick, qui encode par libjpeg.
- **B — Qualité estimée de n'importe quelles tables** (méthode d'ImageMagick ou de JPEGsnoop). Inconvénients : aucune méthode unique (Giudice et al. 2016 l'écartent pour cette raison) ; une estimation n'est pas une lecture.

### Condition des règles de structure

- Absence : `image.metadonnees` égal à 0, compte des blocs EXIF, XMP, XMP étendu, Photoshop (IPTC) et texte PNG, observé seulement si le parcours est allé à son terme (un parcours interrompu ne dit pas que les blocs manquent).
- Dimensions : JPEG seulement (`image.jpeg.tables` présente) : les études ne portent que sur des JPEG, et un PNG à ces tailles est d'abord une capture ou un export.
- Côté long : la largeur parmi la liste et plus grande que la hauteur (paysage), la hauteur parmi la liste et plus grande que la largeur (portrait), la largeur parmi la liste et égale à la hauteur (carré) ; trois règles, comme les dimensions de T23 (ADR-0150), une condition ne portant qu'un test.
- Tables : absence de métadonnées et qualité libjpeg reconnue. Sans l'absence, un JPEG d'appareil ou de logiciel qui emploie ces tables et garde son EXIF serait relevé.

## Décision

Option A dans les deux cas, et les conditions ci-dessus.

- Lecteur de conteneurs : natures `TRAME` et `QUANTIFICATION`, et l'ensemble `STRUCTURE` ; les modules de métadonnées, qui filtrent par nature, ne changent pas.
- Module `image` 0.1.0 : formats JPEG, PNG, WebP ; observations `image.metadonnees`, `image.trame`, `image.largeur`, `image.hauteur` (en `px`), `image.jpeg.tables`, `image.jpeg.qualite_ijg` ; aucune règle « module » ; fiche [`structure-image`](../techniques/structure-image.md).
- Tailles : celles d'ADR-0153, dont 960 (Facebook, basse qualité) et 1 080 (Instagram), relevées dans les mêmes tableaux que les tailles nommées dans la question.
- Signatures : valeurs exactes (`Screenshot`, `gnome-screenshot`) ou préfixe (`^FBMD`), sans égard à aucune autre forme ; la valeur qui suit `FBMD` n'est pas interprétée.
- Écartés, avec leur raison :
  - HEIC : ses dimensions sont dans une propriété `ispe` associée à l'élément principal par `ipma`, que le lecteur ne suit pas ; les messageries étudiées rendent des JPEG ;
  - autres outils de capture (Windows, Android, KDE, capture intégrée à GNOME Shell) : aucune source trouvée de la valeur qu'ils écrivent ;
  - nom du fichier (`Screenshot_…`, `IMG-…-WA…`) : le rapport le masque par défaut, comme donnée identifiante (ADR-0014, NF-18), et un nom se change sans rien toucher au fichier ;
  - dimensions des écrans pour les captures : aucune liste fermée possible ;
  - autres marques de plateformes (Instagram, Twitter, WhatsApp) : aucune source qui décrive une marque écrite dans le fichier ;
  - tables de mozjpeg, d'appareils ou de plateformes : comparaison à d'autres tables connues, laissée à T40 (F-30) ; double compression laissée à T41 (F-31).

## Raisons

- Lecteur étendu et module `image` : le cas visé est une image sans métadonnées ; ce qui reste à lire est sa structure, qui n'appartient à aucune famille de métadonnées. Un seul parcours garde les limites comptées et le fuzzing existants (ES-19).
- B écartée pour la lecture : elle range dans l'EXIF ce qui n'en est pas. C écartée : elle demande la comparaison entre modules, et un compte des blocs suffit.
- Tables à l'identique : seule une lecture exacte donne une observation déterministe (NF-06) ; une qualité estimée dépendrait de la méthode.
- JPEG seulement pour les dimensions et absence pour les tables : réduire les constats sur des fichiers que les sources ne décrivent pas.

## Conséquences

- La qualité libjpeg et les dimensions réelles sont des observations, au rapport même sans constat ; T40 pourra lire d'autres tables à partir des mêmes segments, T41 la double compression.
- Le module est ajouté à la campagne de fuzzing des modules de métadonnées (`tests/test_fuzzing.py`), avec des échantillons qui portent SOF, DQT de huit et seize bits, `"VP8 "` et `VP8L`.
- Un JPEG enregistré par un logiciel qui emploie libjpeg sans écrire de métadonnées, à l'une des tailles de la liste, donne deux indices faibles de transformation sans en avoir subi : les limites des règles le disent, et la mesure sur le corpus (T100) dira ce que valent ces règles.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T24 (« Oui, les deux ») : statut « Accepté » |
