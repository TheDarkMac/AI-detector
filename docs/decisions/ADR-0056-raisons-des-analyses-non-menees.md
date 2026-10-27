# ADR-0056 — Raisons des analyses non menées : liste fermée, phrase par gabarit

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant ; liste des raisons fixée par l'assistant
- **Tâche** : T11
- **Exigences liées** : F-82, NF-03, NF-08 ; ES-04, ES-15 ; ADR-0012, ADR-0020, ADR-0023, ADR-0036, ADR-0042

## Contexte

F-82 demande de lister les analyses non menées avec leur raison. Une partie de ces raisons naît dans P2, qui lit un fichier hostile ; ADR-0036 précise qu'un échec devient une analyse non menée « sans contenu du fichier ». ADR-0020 sépare du code les phrases destinées à l'utilisateur.

## Options envisagées

### Option A — Liste fermée de codes, chacun avec sa phrase en gabarit

- Avantages : aucun texte libre venu de P2 n'atteint le rapport ; les phrases sont relues et traduisibles ; les raisons se comptent et se comparent d'un rapport à l'autre.
- Inconvénients : ajouter une raison demande de modifier le modèle et le schéma.

### Option B — Code fermé et précision libre du module

- Avantages : plus expressif (« table de quantification n° 3 illisible »).
- Inconvénients : un texte produit dans P2 à partir d'un fichier hostile entre dans le rapport ; il faut le borner, le neutraliser et le masquer partout.

## Décision

Une analyse non menée porte une **raison** prise dans une liste fermée, le **module** concerné et, au besoin, une **localisation** (partie du fichier concernée). La phrase affichée est le gabarit associé à la raison (ADR-0020), rédigé avec les rapports (T16).

Liste fixée par l'assistant :

| Raison | Sens | Module obligatoire | Interrompt l'analyse |
| --- | --- | --- | --- |
| `hors_v1` | Technique pertinente pour ce format, absente de cette version (ADR-0012) | Oui | Non |
| `module_desactive` | Désactivée par l'utilisateur (ADR-0042) | Oui | Non |
| `format_partiel` | Partie du fichier que l'outil ne sait pas lire (A-25) | Non | Non |
| `fichier_tronque` | Fichier tronqué ou corrompu (NF-03) | Non | Non |
| `reference_manquante` | Référence nécessaire non fournie (CU-4) | Oui | Non |
| `reseau_desactive` | Requête sortante nécessaire, désactivée (ADR-0010, ADR-0033) | Oui | Non |
| `erreur_module` | Exception dans le module (ADR-0042) | Oui | Non |
| `limite_depassee` | Limite de taille, de mémoire ou de décompression (NF-02, T14) | Non | Oui |
| `delai_depasse` | Délai dépassé (NF-08) | Non | Oui |
| `arret_processus` | Arrêt anormal du processus de travail (ADR-0036) | Non | Oui |
| `message_invalide` | Message de P2 non conforme (ES-04) | Non | Oui |

- Sans module, la raison porte sur l'analyse du fichier entier.
- Le rapport est **interrompu**, donc hors garantie de reproductibilité (ADR-0023), dès qu'une de ses raisons figure dans la dernière colonne. Cette propriété est calculée, jamais saisie.

## Raisons

- Option A retenue : rien du fichier ne peut passer par une raison (ES-04, ES-15), et la liste est assez courte pour être relue en entier.
- Option B écartée : elle ouvre au contenu hostile un chemin de plus vers le rapport, pour un gain de précision que la localisation couvre déjà en partie.
- Interruption : les quatre raisons retenues dépendent de la machine ou d'un processus compromis ; une erreur de module, déterministe, se reproduit à l'identique et ne rompt pas la garantie.

## Conséquences

- Ajouter une raison change le modèle, le schéma et `VERSION_SCHEMA` (ADR-0054).
- T12 produit `erreur_module`, `arret_processus` et `message_invalide` ; T13 `format_partiel` et `fichier_tronque` ; T14 `limite_depassee` et `delai_depasse` ; T30 `reseau_desactive`.
- T16 rédige un gabarit par raison.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-26 | Renvoi : T12 produit `erreur_module`, `arret_processus`, `message_invalide`, `module_desactive`, et déjà `limite_depassee` et `delai_depasse` avec des valeurs provisoires (ADR-0065) |
| 2026-10-27 | Complété par ADR-0071 (T13) : raison `hors_perimetre` ajoutée ; `fichier_tronque` et `format_partiel` produits à partir de l'identification ; partie d'une analyse non menée |
