# ADR-0090 — Constat d'une règle : cité par son identifiant, contrôlé par le processus principal

- **Statut** : Proposé
- **Date** : 2026-10-27
- **Décideur** : l'assistant, proposition non posée en question pendant T15, soumise dans la PR de T15
- **Tâche** : T15
- **Exigences liées** : F-80, F-81, NF-07 ; ES-04, ES-20 ; M-10 ; RR-01 ; ADR-0018, ADR-0058, ADR-0061, ADR-0064, ADR-0084

## Contexte

Avant T15, un module construisait lui-même tout son constat (ADR-0061) : phrase, référence de règle, fondement, catégorie, direction, graduation. Le catalogue n'existant pas, personne ne vérifiait que ces champs étaient ceux de la règle citée. Avec le catalogue (ADR-0084), la règle fixe ces champs ; il fallait dire qui les écrit et qui les vérifie.

## Options envisagées

### Option A — Le module cite la règle, le catalogue fixe le reste

`contexte.constater(regle, donnees, parametres)` : le contexte prend gabarit, catégorie, direction, fondement et graduation dans la règle ; le processus principal vérifie que chaque constat reçu les porte.

- Avantages : une seule source pour ce que dit un constat ; un module ne peut pas, par erreur, graduer un indice autrement que son catalogue.
- Inconvénients : l'interface des modules change (ADR-0061).

### Option B — Le module écrit tout, le principal vérifie

L'interface d'ADR-0061 reste ; le principal refuse un constat qui contredit sa règle.

- Avantages : interface inchangée.
- Inconvénients : chaque module recopie des valeurs du catalogue ; une mise à jour du catalogue (un niveau) fait échouer un module qui ne la reflète pas.

### Option C — Le module écrit tout, sans vérification

- Avantages : aucun travail.
- Inconvénients : le catalogue n'engage plus les constats ; contraire à NF-07.

## Décision

Option A.

- Interface : `constater(regle, donnees, parametres=None, *, localisation=None)`. `regle` est l'identifiant d'une règle « module » de ce module dans le catalogue ; `parametres` associe chaque paramètre déclaré par la règle à une observation de `donnees`. Le contexte refuse (exception dans le module, donc `erreur_module`, ADR-0060) une règle absente ou appliquée par le moteur, et des paramètres différents de ceux de la règle.
- Les constats du moteur (ADR-0089) passent par le même chemin, avec les mêmes contrôles de direction et de données.
- Le processus principal reçoit, avec la configuration, les règles des modules actifs ; pour chaque constat reçu, il vérifie que la règle existe, est de ce module, a cette version, et que gabarit, noms des paramètres, catégorie, direction, fondement et graduation sont ceux de la règle. Tout écart est un message invalide (`message_invalide`, ADR-0065).

## Raisons

- Option A : la règle publiée est ce qui fait foi (ADR-0019) ; la faire recopier par le module crée deux sources qui peuvent diverger.
- Option B écartée : elle détecte la divergence au lieu de l'empêcher.
- Option C écartée : un constat dont la graduation ne vient pas de sa règle contredit ADR-0018.

## Conséquences

- ADR-0061 est précisé : nouvelle signature de `constater`. Aucun module n'était livré : rien d'autre à adapter que les tests.
- RR-01 est réduit sans être levé : un processus de travail compromis peut encore forger le constat d'une règle existante d'un module actif, sur ses propres observations, mais plus inventer une règle, une version ni un niveau.
- T16 lit dans le catalogue, à partir de la référence du constat, le titre, les limites et l'évaluation de la règle.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
