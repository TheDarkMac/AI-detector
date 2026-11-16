# ADR-0206 — Constat du dwtDct : trois règles du catalogue, indice faible vers l'origine IA ; module `dwtdct` et versions de T32

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T32, validée pendant la revue de la PR
- **Tâche** : T32
- **Exigences liées** : F-24, F-25, F-80, F-81, ES-20 ; ADR-0018, ADR-0021, ADR-0050, ADR-0085, ADR-0101, ADR-0152, ADR-0174, ADR-0177, ADR-0188

## Contexte

ADR-0174 demandait à T32 de fixer la direction et le niveau du constat, qui n'est jamais une preuve (ADR-0021 : message public et fixe, schéma non cryptographique). Les modules de signal de T41 et T42 n'émettent aucun constat : ils observent, et une règle « moteur » du catalogue lit leurs observations (ADR-0188). Un indice sans évaluation sur le corpus de référence reste au niveau « faible » (ADR-0101) ; le corpus de référence est l'affaire de T100.

## Options envisagées

### Option A — Trois règles « moteur », une par message (proposée)

- `R-DWTDCT-001` (Stable Diffusion 1), `R-DWTDCT-002` (SDXL, les deux ordres des couleurs), `R-DWTDCT-003` (FLUX.1) : catégorie indice, direction origine IA, fondement « mesure », niveau faible, calibrage « manuel » décrit dans la règle ; condition `dwtdct.concordants_<message> >= seuil` (ADR-0204).
- Avantages : comme T41 ; seuils et limites publics, au catalogue ; la phrase nomme le code de référence.
- Inconvénients : trois règles pour un même schéma.

### Option B — Une règle « module », appliquée par le code

- Avantages : une seule règle.
- Inconvénients : le seuil passe dans le code ; un catalogue fourni par l'utilisateur ne pourrait pas le changer.

### Option C — Quatre règles, SDXL et SDXL aux couleurs échangées à part

- Avantages : le constat dit l'ordre des couleurs.
- Inconvénients : une image de SDXL se lit aussi dans l'autre ordre (48 et 46 bits sur un essai) : deux constats pour un même filigrane. Écartée pendant T32, après cette mesure ; l'échange est une observation (`dwtdct.rouge_et_bleu_echanges_sdxl`).

## Décision

Option A, et :

| Élément | Version |
| --- | --- |
| Module `dwtdct` | 0.1.0, formats JPEG, PNG, WebP, HEIC (les deux derniers non menés, ADR-0202), exigence F-24, direction `origine_ia`, bibliothèque numpy |
| Catalogue | 0.10.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; `M-DWTDCT` recherché par `dwtdct`, au lieu de `lecteur_a_venir` |
| Schémas du rapport et des messages | Inchangés : 0.7.0 |
| Paquet | Inchangé (ADR-0050 : la version suit les publications) |

Une analyse non menée du module ne rend pas le contrôle avant publication incomplet : il ne lit aucune métadonnée, comme `doublejpeg` et `ela` (ADR-0158, ADR-0190, ADR-0201).

Observations du module : `dwtdct.pixels_image` ; `dwtdct.chrominance` (faux pour une image en niveaux de gris) ; `dwtdct.blocs`, `dwtdct.blocs_image` ; pour chaque message, `dwtdct.concordants_<message>`, et s'il y a lieu `dwtdct.indetermines_<message>` ; `dwtdct.rouge_et_bleu_echanges_sdxl`.

## Raisons

- A proposée par l'assistant : même forme qu'ADR-0188, et le catalogue reste maître des seuils (ADR-0019).
- B écartée : un seuil hors du catalogue échappe à un catalogue fourni (ADR-0086).
- C écartée : double compte d'un même filigrane, mesuré.
- Direction « origine IA » : le message est posé par le code de génération, sur sa sortie. Il ne prouve rien (n'importe qui peut le poser) et son absence ne dit rien ; les limites de chaque règle le disent.
- Lecture d'ADR-0022, comme ADR-0142 pour une déclaration : la règle ne prétend pas reconnaître une image générée à son signal ; elle lit un marquage que seuls les codes de génération posent. Une transformation banale ne l'écrit pas : elle le conserve (compression JPEG en 4:4:4) ou l'efface (redimensionnement, recadrage) ; le relevé de T32 vérifie qu'aucune image authentique, recompressée et redimensionnée par Commons, n'atteint les seuils (ADR-0204). La rubrique « hypothèses distinguées » de la fiche le dit, et laisse la mesure sur la partie évaluation du corpus à T100 ; tant qu'elle manque, le niveau reste « faible ».

## Conséquences

- Le rapport d'une image marquée porte un indice faible vers l'origine IA, qui nomme le code de référence et le nombre de bits concordants.
- La raison `lecteur_a_venir` n'est plus employée que par `M-C2PA-TEXTE` (T80).
- Évaluation sur le corpus de référence, et un niveau plus élevé s'il le permet : T100.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création, statut « Proposé » |
| 2026-11-16 | Validé par TheDarkMac pendant la revue de la PR (« Oui, valide ADR-0206 ») : statut « Accepté » |
