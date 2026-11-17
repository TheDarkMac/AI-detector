# ADR-0218 — Constats des pages d'un PDF : quatre indices faibles vers la retouche ; module `pagespdf` et versions de T51

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (direction et niveau posés avec les options d'ADR-0214 et d'ADR-0216 ; règles et versions précisées par l'assistant)
- **Tâche** : T51
- **Exigences liées** : F-61, F-80, F-81, F-90, ES-20 ; ADR-0018, ADR-0101, ADR-0152, ADR-0158, ADR-0211, ADR-0214, ADR-0216

## Contexte

Les relevés d'ADR-0214 et d'ADR-0216 disent où un texte a pu être posé sur un autre, caché, ou écrit par un autre outil. Comme pour `revisionspdf` (ADR-0211), le module n'émet aucun constat : des règles « moteur » du catalogue lisent ses observations. Les options choisies par TheDarkMac le disaient déjà : « en indice faible vers la retouche ». Un indice non évalué sur le corpus de référence reste « faible » (ADR-0101).

## Options envisagées

### Option A — Une règle par relevé (retenue)

- **R-PAGESPDF-001** : `pagespdf.superpositions` ≥ 1 ;
- **R-PAGESPDF-002** : `pagespdf.caches` ≥ 1 ;
- **R-PAGESPDF-003** : `pagespdf.familles_melangees` ≥ 1 ;
- **R-PAGESPDF-004** : `pagespdf.codes_hors_plage` ≥ 1.

Chacune nomme la première page concernée.

- Avantages : chaque constat dit ce qui a été vu, avec ses propres limites.
- Inconvénients : quatre règles à mesurer au banc.

### Option B — Une règle qui réunit les relevés

- Avantages : un seul constat.
- Inconvénients : une phrase qui ne dit plus ce qui a été vu, et des limites qui ne s'appliquent qu'à une partie des cas.

## Décision

Option A. Précisions de l'assistant :

- Direction « retouche » : les quatre relevés désignent un contenu changé, pas un encodage (la transformation) ; un PDF n'a pas d'origine IA à lire dans ses contenus.
- Fondement « vérification déterministe » : la structure et la géométrie sont lues telles qu'elles sont déclarées, sans mesure statistique ; une règle d'indice reste un indice (ES-20).
- Seuils par définition (au moins un relevé), calibrage « manuel » décrit dans chaque règle ; `pagespdf.superpositions_d_un_signe` n'a pas de règle (ADR-0214).
- Une analyse non menée du module ne rend pas le contrôle avant publication incomplet : il ne lit aucune métadonnée (ADR-0158) ; `pagespdf` rejoint les modules sans métadonnées du résumé.

| Élément | Version |
| --- | --- |
| Module `pagespdf` | 0.1.0, format PDF, exigence F-61, directions `retouche` et `rien_de_particulier`, aucune bibliothèque |
| Module `revisionspdf` | 0.2.0 (ADR-0217) |
| Catalogue | 0.12.0 (`Y` : règles ajoutées, ADR-0152), format 3 inchangé ; description raccourcie pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.9.0 (ADR-0217) |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A : une règle par relevé, comme T50 en a une par cas (ADR-0211) ; chaque phrase dit au lecteur quoi aller voir et à quelle page.
- Option B écartée : une phrase commune perdrait ce qui distingue un cache d'une police d'une autre incorporation.

## Conséquences

- Sur les échantillons : `document.pdf` et `ghostscript.pdf` ne déclenchent rien ; `superpose.pdf` R-PAGESPDF-001 ; `cache.pdf` et `annotation.pdf` R-PAGESPDF-001 et 002 ; `cache_seul.pdf` R-PAGESPDF-002 ; `fusion.pdf` R-PAGESPDF-003 ; `hors_plage.pdf` R-PAGESPDF-004.
- La part de documents ordinaires qui déclenchent chaque règle se mesurera sur le corpus de référence (T100) ; un niveau plus élevé demandera cette mesure.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; direction et niveau choisis par TheDarkMac au début de T51, avec les options d'ADR-0214 et d'ADR-0216 |
