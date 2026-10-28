# ADR-0058 — Structure de l'observation et du constat

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T11, validée pendant la revue de la PR de T11
- **Tâche** : T11
- **Exigences liées** : §6 du cahier, F-80, F-81 ; constats A-02, A-03, A-46, A-47 ; ES-13, ES-20 ; ADR-0018, ADR-0020, ADR-0021, ADR-0022, ADR-0042

## Contexte

Le §6 fixe cinq éléments par constat : phrase, donnée observée, règle, catégorie, direction. A-46 relève qu'il manque la version de la règle, la technique, les limites connues, la source d'une preuve et la localisation ; ADR-0018 ajoute le niveau. L'architecture (§6) sépare l'observation (donnée relevée par un module) du constat (ce qu'une règle en tire) ; ADR-0042 laisse à T11 la forme de l'observation. Ces choix n'ont pas fait l'objet d'une question pendant T11 : ils découlent des ADR cités, ont été soumis dans la PR et validés par TheDarkMac.

## Options envisagées

### Option A — Observations séparées, constats qui y renvoient, éléments du catalogue non recopiés

- Avantages : les valeurs tirées du fichier vivent à un seul endroit, qu'on échappe et qu'on masque une fois ; la phrase ne contient aucun texte venu de P2 ; les limites et le taux d'une règle restent dans le catalogue, que P1 a validé.
- Inconvénients : lire un constat demande de suivre des renvois ; le rapport doit être lu avec son catalogue.

### Option B — Constat autonome, qui recopie valeurs, limites et source

- Avantages : chaque constat se lit seul.
- Inconvénients : une même valeur répétée dans plusieurs constats et dans des phrases ; masquage et échappement à faire partout ; textes de limites fournis par P2, donc forgeables (M-10).

## Décision (Option A)

**Observation** : identifiant unique dans le rapport, module, nom de la donnée, valeur (texte, nombre, booléen, ou liste de ceux-ci), unité facultative, localisation facultative, catégorie identifiante facultative (ADR-0057). C'est le seul objet qui porte des valeurs tirées du fichier.

**Constat** :

| Élément | Contenu | Origine |
| --- | --- | --- |
| Phrase | Identifiant de gabarit et paramètres ; chaque paramètre renvoie à une observation du constat | §6, ADR-0020 |
| Données | Identifiants des observations, au moins une | §6, principe d'explicabilité |
| Règle | Identifiant et version, distincts des identifiants d'exigence | A-47 |
| Module | Technique dont relève la règle | A-46 |
| Fondement | `verification_cryptographique`, `verification_deterministe`, `declaration`, `mesure` | ES-20 |
| Catégorie | Preuve, indice, information neutre | F-80 |
| Direction | Une des cinq d'ADR-0055 | F-81 |
| Graduation | Niveau (faible, modéré, fort) et règle évaluée ou non ; indices seulement | ADR-0018 |
| Localisation | Facultative : chemin dans la structure, plage d'octets, page, zone, intervalle de temps | A-46 |

Invariants, vérifiés par le modèle et, sauf le premier, par le schéma :

1. Les paramètres de la phrase renvoient à des observations du constat.
2. Une **preuve** repose sur une vérification cryptographique ou déterministe (ADR-0021, ES-20) et n'a pas de niveau. Une déclaration du fichier n'est donc jamais une preuve.
3. Un **indice** a un niveau et pointe vers une hypothèse (pas « rien de particulier »).
4. Une **information neutre** n'a pas de niveau et pointe vers « rien de particulier » (F-14).
5. Une règle non évaluée est au niveau faible (ADR-0018).

Ce qui n'est pas dans le constat :

- les **limites connues** et le **taux** de la règle : lus dans le catalogue à partir de la référence de la règle (T15, T16) ;
- la **source** d'une preuve (§6) : portée par ses observations (manifeste, certificat, état de la signature) et sa localisation ; la liste de confiance employée figure dans la rubrique Versions (ADR-0023, T30).

## Raisons

- Option A retenue : elle réduit à un seul type d'objet la surface où du contenu hostile entre dans le rapport, ce qui simplifie l'échappement (ES-12) et le masquage (ES-13), et garde dans le catalogue validé ce qui décrit une règle.
- Option B écartée : duplication des valeurs et textes descriptifs forgeables par un P2 compromis.
- Fondement explicite : sans lui, le modèle ne pourrait pas refuser une « preuve » tirée d'une simple déclaration (ES-20, cas d'abus C-02).
- Indice sans hypothèse refusé : ADR-0022 renvoie vers « rien de particulier » ce qu'une technique ne distingue pas ; un tel constat n'est pas un indice mais une information neutre.
- Source non structurée en V1 : sa forme dépend de C2PA (T30) ; T30 pourra ajouter un champ par un nouvel ADR.

## Conséquences

- T15 : le catalogue donne, pour chaque règle, sa version, son fondement, sa catégorie, ses directions permises, son niveau et son taux, ses limites ; T12 vérifie qu'un constat reçu est conforme à sa règle (ADR-0022).
- T16 : la phrase est rendue dans P1 à partir du gabarit et des observations citées, masquées le cas échéant.
- T20 et suivantes : chaque module choisit ses noms d'observation et les documente dans sa fiche.
- Un constat sans observation est impossible : même une absence (« pas de bloc XMP ») est une observation de valeur `false`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création, statut « Proposé » |
| 2026-10-26 | Validé par TheDarkMac pendant la revue de la PR de T11 : statut « Accepté » |
| 2026-10-28 | Renvoi : premiers noms d'observation, métadonnées d'image (ADR-0117, T20) |
