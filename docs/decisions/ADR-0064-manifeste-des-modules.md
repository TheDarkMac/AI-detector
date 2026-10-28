# ADR-0064 — Manifeste des modules : contenu, validation, ordre d'exécution

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T12, validée pendant la revue de la PR de T12
- **Tâche** : T12
- **Exigences liées** : NF-09, NF-10, F-25 ; M-31 ; ADR-0022, ADR-0038, ADR-0042, ADR-0063

## Contexte

ADR-0042 fixe le principe : chaque module livre un manifeste TOML (ADR-0038) que le processus principal lit et valide sans importer le code. Il en donne le contenu : identifiant, version, formats, exigences, règles du catalogue, fiche technique, dépendances envers d'autres modules. Restaient à fixer la forme exacte de chaque champ, ce que le code vérifie en plus du schéma, l'ordre d'exécution, et le sort d'un manifeste invalide.

## Options envisagées

### Option A — Schéma fermé, directions permises dans le manifeste

Tous les champs obligatoires, aucun champ inconnu, et un champ de plus : les directions que la fiche technique permet au module (ADR-0022).

- Avantages : la contrainte d'ADR-0022 est vérifiée deux fois, dans le contexte du module (ADR-0061) et par le processus principal à la réception ; un manifeste incomplet est vu tout de suite.
- Inconvénients : la fiche technique et le manifeste répètent la même liste ; un test devra vérifier leur accord quand les fiches existeront.

### Option B — Schéma ouvert, directions tenues par le catalogue seul

- Avantages : aucune répétition.
- Inconvénients : le catalogue n'existe pas avant T15 ; un constat de direction interdite ne serait refusé par personne d'ici là. Un champ inconnu (faute de frappe) passerait sans bruit.

## Décision

Option A. Champs de `manifeste.toml`, validés par `schemas/manifeste.schema.json` :

| Champ | Forme | Vérifié par le code en plus |
| --- | --- | --- |
| `identifiant` | Minuscules et chiffres, commence par une lettre, 32 caractères au plus | Égal au nom du dossier, donc au nom d'import |
| `version` | Version (même forme que dans le rapport) | — |
| `formats` | 1 à 64 identifiants, sans doublon | Vocabulaire des formats fixé en T13 |
| `exigences` | 1 à 64 identifiants `F-xx`, `NF-xx`, `ES-xx`, sans doublon | — |
| `regles` | Identifiants de règles, sans doublon, éventuellement vide | Existence dans le catalogue (T15) |
| `fiche` | Nom de fichier en minuscules et tirets : `docs/techniques/<fiche>.md` | Un test vérifie que la fiche existe pour chaque module livré |
| `directions` | 1 à 5 directions (F-81, ADR-0055), sans doublon | Tout constat d'une autre direction est refusé |
| `requiert` | Identifiants de modules, sans doublon, éventuellement vide | Modules existants, autres que lui-même, sans cycle |

- **Ordre d'exécution** : un module s'exécute après ceux qu'il requiert ; à rang égal, dans l'ordre de leurs identifiants. Deux analyses exécutent donc les modules dans le même ordre (NF-06).
- **Manifeste invalide** : les manifestes sont livrés avec l'outil, un manifeste invalide est un défaut de l'outil. La découverte s'arrête avec `ManifesteInvalide`, qui nomme le module et la règle du schéma en cause, comme pour un catalogue invalide (ADR-0029). Aucune analyse n'a lieu avec un ensemble de modules incohérent.
- **Découverte** : sont des modules les sous-dossiers de `modules/` qui contiennent `manifeste.toml` ; tout le reste est ignoré. Le processus de travail importe ces mêmes dossiers, par la même fonction (`voight_kampff.modules.dossiers`).

## Raisons

- Option A retenue, proposée par l'assistant et validée par TheDarkMac : elle vérifie ADR-0022 dès T12, et un manifeste ne peut pas dire autre chose que ce que le schéma admet.
- Option B écartée : elle repousse à T15 une vérification possible maintenant, et laisse passer les champs mal nommés.
- Identifiant en minuscules et chiffres : il sert de nom d'import Python et de préfixe des identifiants d'observation, dont la forme (ADR-0054) n'admet pas le tiret bas.
- Arrêt sur manifeste invalide plutôt que module ignoré : ignorer un module en silence fausserait la couverture (F-25).

## Conséquences

- Chaque tâche de technique livre un manifeste conforme ; le test des modules livrés vérifie leur fiche dès que `docs/techniques/` existe.
- Les versions des bibliothèques qu'un module emploie (rubrique Versions, ADR-0023) ne sont pas encore au manifeste : elles seront ajoutées avec le premier module qui en emploie une, et lues avant le verrouillage du processus de travail.
- T15 vérifie que les règles citées existent dans le catalogue et que leurs directions sont permises par le manifeste de leur module.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR de T12 : statut « Accepté » |
| 2026-10-27 | Vocabulaire des formats fixé par ADR-0070 (T13) : seuls les formats du périmètre sont admis |
| 2026-10-27 | Précisé par ADR-0084 (T15) : `regles` cite les règles « module » du module, et elles seules ; existence, module et directions vérifiés au chargement du catalogue |
| 2026-10-28 | Précisé par ADR-0120 (T20) : champ `bibliotheques` ; concordance des fiches et des manifestes testée |
