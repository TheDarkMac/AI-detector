# ADR-0072 — Signalements de l'identification : dans la rubrique Identification

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T13
- **Exigences liées** : F-03, ES-07, §6 du cahier ; ADR-0014, ADR-0031, ADR-0059, ADR-0070, ADR-0071

## Contexte

L'identification établit trois signalements : une extension qui ne correspond pas au format réel (F-03), un fichier reconnu dans plusieurs formats, des données après la fin logique (ES-07). Il faut décider où le rapport les porte.

## Options envisagées

### Option A — Champs de la rubrique Identification

- Avantages : ce sont des faits établis par le moteur, sans interprétation ; disponibles dès T13, sans catalogue ; le lecteur les trouve avec le format réel.
- Inconvénients : ils ne sont pas des constats : T16 doit les mettre en avant dans le résumé par lui-même.

### Option B — Constats tirés de règles du catalogue

- Avantages : même forme que les autres constats ; niveau et taux de faux positifs par règle.
- Inconvénients : attend T15 ; une discordance d'extension n'indique aucune origine, elle prendrait une direction (« transformation ») qui ne lui convient pas toujours.

## Décision

Option A. La rubrique Identification porte :

| Champ | Contenu | Identifiant |
| --- | --- | --- |
| `nom`, `empreinte` | Inchangés | Oui (ADR-0014, ADR-0031) |
| `format_reel` | Format de la partie 1 | Non |
| `parties` | Rang, format, plage d'octets, fin connue, tronquée (ADR-0071) | Non |
| `extension` | Extension du nom, en minuscules ; absente s'il n'en a pas | Non |
| `extension_concordante` | Vrai si l'extension est l'une de celles du format réel ; absente sans extension | Non |
| `octets_non_reconnus` | Plages qu'aucune partie ne couvre, dans l'ordre | Non |

`extension`, `extension_concordante` et `octets_non_reconnus` sont **déduits** du nom et des parties : écrits dans le JSON pour le lecteur, recalculés et comparés à la relecture. Un polyglotte se lit au nombre de parties de formats différents ; des données après la fin logique, à une dernière plage non reconnue qui finit le fichier.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle repousse F-03 à T15 et range un fait d'identification parmi des indices d'origine.
- L'extension n'est pas masquée avec le nom : seule, elle ne désigne personne, et le lecteur en a besoin pour comprendre une discordance.
- Concordance mesurée contre le format réel (partie 1) : c'est ce que F-03 compare.

## Conséquences

- T16 met ces signalements dans le résumé et les rédige par gabarits.
- Les plages non reconnues et les parties tronquées ou hors périmètre figurent aussi parmi les analyses non menées (ADR-0071) : la rubrique Identification dit ce qui a été vu, F-82 ce qui n'a pas été analysé.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
