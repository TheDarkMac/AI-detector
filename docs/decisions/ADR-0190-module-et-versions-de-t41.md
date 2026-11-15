# ADR-0190 — Module `doublejpeg`, un fil pour OpenBLAS, contrôle avant publication, versions de T41

- **Statut** : Proposé
- **Date** : 2026-11-15
- **Décideur** : l'assistant, soumis à TheDarkMac dans la PR de T41
- **Tâche** : T41
- **Exigences liées** : F-31, NF-02, NF-06, NF-09, NF-10 ; ADR-0042, ADR-0064, ADR-0065, ADR-0085, ADR-0120, ADR-0154, ADR-0184

## Contexte

T41 ajoute une technique (F-31), un lecteur (`_lecture/jpeg.py`), une dépendance (numpy, ADR-0185) et une règle. Restaient : où loger la technique, comment numpy démarre dans le processus de travail, et quelles versions changent.

## Options envisagées

### Emplacement de la technique

- **A — Module à part, `doublejpeg`** : sa fiche, ses observations (`doublejpeg.*`), sa version ; il se désactive seul (`--desactiver doublejpeg`) ; une erreur de décodage n'atteint pas le module `image`.
- **B — Dans le module `image`** : une fiche et un module de moins ; mais une erreur du décodeur interromprait aussi la lecture des dimensions et des tables, et la fiche `structure-image` décrit une lecture de structure, sans décodage (ADR-0154).

### Fils d'OpenBLAS

- **A — Un fil, par `OPENBLAS_NUM_THREADS=1` dans l'environnement du processus de travail**, seule valeur ajoutée à l'environnement vidé d'ADR-0065.
- **B — Environnement inchangé** : OpenBLAS, chargé par numpy à son import, crée un fil par cœur (4 sur le poste), chacun avec sa mémoire ; sur une machine à nombreux cœurs, la limite de 2 Gio du processus (ADR-0077) pourrait être atteinte dès l'import, et le module ne s'en sert pas (produits d'entiers, ADR-0189).

### Contrôle avant publication

- **A — Une analyse non menée de `doublejpeg` ne rend pas le contrôle incomplet**, comme celles des techniques hors V1 : le module ne lit aucune métadonnée, donc aucune marque identifiante ne reste non lue par sa faute (raison d'ADR-0158). Liste des modules concernés tenue dans `rapport/_presentation.py`.
- **B — ADR-0158 tel quel** : un JPEG que le décodeur ne lit pas (codage arithmétique, douze bits, JPEG sans données d'image) ferait dire au résumé que le contrôle est incomplet, alors que toutes ses métadonnées ont été lues.
- **C — Champ du manifeste** (« lit des métadonnées ») : plus général, mais un changement du schéma des manifestes pour un seul module.

### Versions

- **A — Module `doublejpeg` 0.1.0 ; catalogue 0.8.0, format 3 inchangé ; schéma du manifeste étendu (`numpy` admis dans `bibliotheques`) ; schéma du rapport inchangé (0.6.0)** : une règle ajoutée change `Y` du catalogue (guide, §5) ; les observations sont des noms libres (ADR-0058).
- **B — Catalogue 0.7.1** : réservé à un texte seul.

## Décision

Option A dans les quatre cas.

## Raisons

- Emplacement A : erreurs séparées (ADR-0061) et désactivation propre ; B écartée pour ces deux raisons.
- Fils A : supprime un risque sans rien coûter ; vérifié sur le poste (1 fil au lieu de 4 ; import sans bytecode de 0,44 à 0,57 s dans les deux cas, à la mesure près). B écartée par prudence : le risque n'a pas pu être mesuré, faute de machine à nombreux cœurs, et le fil supplémentaire ne sert à rien.
- Contrôle A : fidèle à la raison d'ADR-0158 ; B écartée parce qu'elle annoncerait à tort des marques non lues ; C écartée tant qu'un seul module est concerné, à reprendre si d'autres modules de signal arrivent (T42 à T45).
- Versions A : la règle du guide du catalogue ; B la contredirait.

## Conséquences

- `--modules` liste `doublejpeg 0.1.0` ; les tests qui citent la liste des modules, le compte des règles et la couverture d'une analyse la suivent.
- `_orchestration/travail.py` : `_environnement()` rend `OPENBLAS_NUM_THREADS=1`, plus `SYSTEMROOT` sous Windows ; ADR-0065 renvoie à cet ADR.
- ADR-0158 renvoie à cet ADR ; `tests/test_controle_publication.py` le vérifie.
- `vk --comparer` voit un écart de versions entre un rapport de T40 et un rapport de T41 sur le même JPEG, ce qui est exact.
- Le complément de T40, mené en parallèle, prévoit lui aussi une nouvelle version du catalogue et de nouveaux ADR : celle des deux PR mergée la seconde renumérote sa version du catalogue et ses ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création, statut « Proposé » |
