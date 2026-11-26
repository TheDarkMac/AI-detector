# ADR-0274 — Effectifs : 400 authentiques en évaluation par famille, un original sur trois en calibrage

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; cibles par format et règle de répartition précisées par l'assistant
- **Tâche** : T100
- **Exigences liées** : §8 du cahier, ES-22 ; ADR-0016, ADR-0101, ADR-0103, ADR-0104 ; A-12, A-54

## Contexte

ADR-0101 fonde le niveau d'une règle sur la borne supérieure de Wilson à 95 % de son taux de faux positifs : sans aucun faux positif, il faut 381 fichiers authentiques analysés pour « fort », 73 pour « modéré » et pour la cible par fichier. ADR-0016 sépare le corpus en calibrage et évaluation, et ADR-0103 laisse la partie au choix de qui constitue le corpus, à condition qu'elle soit fixée avant toute mesure et que les fichiers d'un groupe restent ensemble.

## Options envisagées

### Option A — 400 authentiques en évaluation par famille, un tiers des groupes en calibrage (recommandée)

- Avantages : « fort » reste atteignable pour une règle sans faux positif ; le calibrage garde assez de fichiers pour régler un seuil.
- Inconvénients : environ 600 authentiques par famille à télécharger.

### Option B — Environ 100 par catégorie et par famille

- Avantages : plus rapide.
- Inconvénients : aucune règle ne peut atteindre « fort » ; une seule erreur suffit à faire tomber « modéré ».

### Option C — 1 000 authentiques par famille

- Avantages : intervalles plus étroits.
- Inconvénients : volume et durée d'évaluation bien plus grands ; au-delà du volume annoncé (ADR-0272).

## Décision

Option A. Cibles par format, précisées par l'assistant (fichiers tirés ; le nombre réellement obtenu est au manifeste et dans la description du corpus) :

| Famille | Formats et cibles d'authentiques | Générés |
| --- | --- | --- |
| Image | JPEG 600, PNG 200, WebP 100 | 600 images déclarées (JPEG, PNG, WebP) |
| PDF | 600 | 40 textes de l'assistant rendus en PDF |
| Audio | MP3 220, WAV 200, Ogg 120, FLAC 120 | aucun |
| Vidéo | WebM 600 | aucun |
| Bureautique | DOCX 450, ODT 150, autant que data.gouv.fr en a d'éligibles | 40 textes en DOCX, 40 en ODT |
| Texte | 600 extraits de Wikipédia, portés à tous les éligibles (849), voir ci-dessous | 40 textes de l'assistant |

Répartition :

- chaque original est son propre groupe ; ses transformés, retouchés et malformés (ADR-0275) sont dans ce groupe ;
- dans chaque format, les originaux sont tirés dans un ordre fixé par la graine 100 ; le premier, le quatrième, le septième… vont en calibrage, les autres en évaluation, soit un tiers en calibrage ;
- les textes de l'assistant et les pièges fabriqués suivent la même règle, dans l'ordre de leur nom ;
- la partie est écrite en phase 2, avant tout téléchargement, et ne change plus qu'avec une nouvelle version du corpus.

Complément des textes : une fois téléchargés, 102 des 600 textes tirés avaient moins de 500 caractères de paragraphes (articles faits surtout de tableaux ou de listes), ce qui ne laissait que 323 textes en évaluation. La cible des textes a été portée à tous les articles éligibles (849), avant toute mesure : le tirage se poursuit dans le même ordre, les 600 premiers gardent leur rang et leur partie (vérifié : les 3 972 choix antérieurs sont identiques), et la règle d'un sur trois s'applique aux suivants.

## Raisons

- Option A retenue : elle garde « fort » atteignable sans dépasser le volume annoncé.
- Option B écartée : elle rendrait impossible le niveau le plus utile au lecteur du rapport.
- Option C écartée : coût sans rapport avec le gain pour la V1.
- Un tiers en calibrage : assez pour régler un seuil (200 authentiques par famille), sans priver l'évaluation de l'effectif de « fort ».
- Partie fixée par le rang de tirage, avant tout téléchargement : aucune mesure ne peut l'avoir influencée (M-33), et la règle se vérifie en relisant les scripts.

## Conséquences

- Le nombre réel d'authentiques en évaluation d'une famille peut rester sous 400 quand la source n'en a pas assez (DOCX et ODT de data.gouv.fr) ou qu'un fichier est écarté (empreinte différente, texte trop court) : la description du corpus le dit par format.
- Les règles d'un format rare (WebP, Ogg, FLAC) sont mesurées sur moins de fichiers que leur famille ; leur niveau en tient compte par la borne de Wilson.
- Un recalibrage n'emploie que la partie calibrage (ADR-0016) ; l'évaluation de T101 n'emploie que l'autre.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
