# ADR-0021 — Définition de la preuve

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac (adoption de la proposition A-03 de l'analyse critique)
- **Tâche** : T02
- **Exigences liées** : §6, §11 (glossaire), F-21, F-22, F-24, F-80 ; constat A-03

## Contexte

Le glossaire définit la preuve comme un « élément vérifiable qui établit un fait », avec deux exemples : signature valide et filigrane décodé. Or une signature C2PA valide établit qui a signé et que le contenu n'a pas changé depuis, pas que ses déclarations sont vraies ; un signataire hors liste de confiance peut signer n'importe quoi ; la lecture d'un filigrane est en général un test statistique, et certains schémas peuvent être ajoutés à un contenu authentique pour le discréditer (A-03).

## Options envisagées

### Option A — Garder la définition du cahier

- Avantages : aucun écart avec le cahier.
- Inconvénients : l'exemple du §6 présente une déclaration signée comme un fait sur le contenu ; risque d'affirmation fausse au rapport.

### Option B — Définition restreinte, avec l'énoncé exact de ce qui est établi

- Avantages : chaque preuve dit précisément ce qu'elle établit, et seulement cela.
- Inconvénients : phrases de constat plus longues.

## Décision

- Une **preuve** est un fait établi par une vérification **cryptographique ou déterministe**, accompagné de l'**énoncé exact** de ce qu'il établit. Exemple : « le certificat X, reconnu par la liste de confiance Y, a signé un manifeste qui déclare une génération par IA, et le contenu n'a pas changé depuis la signature ».
- Une signature valide **hors liste de confiance** n'est pas une preuve de provenance : c'est un indice, et le rapport le dit.
- Un **filigrane** n'est une preuve que si son schéma est cryptographique et son taux de faux positifs documenté et négligeable ; sinon, c'est un indice, au plus de niveau fort (ADR-0018).

## Raisons

- Option B retenue : elle évite d'affirmer plus que ce que la vérification établit.
- Option A écartée : elle conduit à des affirmations inexactes, contraires à NF-14.

## Conséquences

- Le glossaire du projet (T11, T103) remplace la définition du cahier ; l'écart est inscrit au registre des arbitrages pour l'auteur.
- T30 et T31 rédigent leurs phrases de constat selon cette définition.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
