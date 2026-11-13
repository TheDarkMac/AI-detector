# ADR-0137 — Lecteur ZIP écrit par le projet ; `zipfile` écarté

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21 (complément bureautique)
- **Exigences liées** : ES-03, ES-05, ES-18, ES-19, NF-06 ; menaces M-02, M-03, M-05 ; ADR-0043, ADR-0070, ADR-0078, ADR-0079

## Contexte

DOCX et ODT sont des archives ZIP. ES-05 demande des archives « lues en mémoire, jamais extraites sur disque, avec les limites d'ES-03 » (taille décompressée cumulée et rapport de compression : bombe de décompression, M-02). ADR-0043 range `zipfile` parmi ce que couvre la bibliothèque standard. L'identification (ADR-0070) lit déjà l'enregistrement de fin et le répertoire central, ZIP64 compris, pour situer l'archive et la classer, et le contexte du module sait décompresser du deflate brut en comptant chaque bloc (`Contexte.decompresser`, ADR-0078).

## Options envisagées

### Option A — Lecteur du projet

`modules/_lecture/zip.py`, en Python pur : enregistrement de fin lu comme l'identification, répertoire central, entrées stockées ou deflate, décompression par `Contexte.decompresser("deflate")`.

- Avantages : la décompression passe par le compteur du budget, sans recompter à côté ; l'archive est trouvée exactement comme l'identification l'a située (données avant l'archive, positions relatives à elle ou au fichier) ; la lecture est stricte là où un lecteur permissif peut être trompé (entrées en double, en-tête local différent) ; rien n'est chargé après les restrictions ; environ 200 lignes, soumises au fuzzing (ES-19).
- Inconvénients : un analyseur de plus à tenir ; écart à la liste d'ADR-0043, à consigner.

### Option B — `zipfile` de la bibliothèque standard

- Avantages : conforme à ADR-0043 ; lecteur éprouvé.
- Inconvénients : sa décompression interne échappe au compteur du budget (il faudrait lire par morceaux et déclarer chacun par `compter_decompression`) ; sa recherche du début d'une archive précédée de données peut différer de l'identification ; il lit aussi bzip2, LZMA et le chiffrement ZipCrypto, dont les modules se chargent à la première utilisation, après les restrictions (ERR-0009) ; il prend sans le dire la dernière de deux entrées de même nom.

## Décision

Option A. Le lecteur :

- trouve le dernier enregistrement de fin dont le commentaire tient dans la partie, puis l'enregistrement ZIP64 juste avant son localisateur quand un champ vaut sa valeur maximale ;
- lit le répertoire central (16 Mio au plus), chaque entrée comptant un objet ; tailles et position d'une entrée lues dans son champ ZIP64 quand elles y sont ;
- nomme une entrée en UTF-8 si son drapeau le dit, en CP437 sinon (codec chargé à l'import) ;
- ne lit une entrée que sur demande, par son nom ; refuse (format partiel) deux entrées de même nom, un en-tête local dont le nom diffère de celui du répertoire central, une entrée chiffrée, une compression autre que stockée ou deflate, des données de plus de 16 Mio ; dit tronquée une entrée qui déborde de la partie ;
- ne vérifie ni le CRC ni la taille décompressée déclarée.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : budget de décompression contourné, et comportements à neutraliser un par un ; ADR-0043 (point 6) prévoit qu'un écart à sa liste soit consigné dans l'ADR de la tâche, ce que fait celui-ci.
- Entrées en double refusées plutôt que l'une choisie : deux lecteurs peuvent prendre l'une ou l'autre, et un fichier pourrait montrer à l'outil d'autres propriétés que celles que voit un traitement de texte.
- CRC non vérifié : il ne change pas ce que l'entrée déclare, comme le CRC des pages Ogg (ADR-0132) ; la vérification de l'intégrité est hors de F-10.

## Conséquences

- `zipfile` reste employé par les tests seulement, comme écrivain indépendant des archives bien formées ; les archives malformées sont écrites octet par octet (`tests/bureautique.py`).
- Le lecteur est soumis au fuzzing avec les modules de métadonnées (ES-19).
- Un tableur ou une présentation (T81 ou plus tard) liront leurs entrées par le même lecteur.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; option choisie par TheDarkMac au début du complément |
