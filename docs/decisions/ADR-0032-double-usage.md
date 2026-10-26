# ADR-0032 — Fonctions à double usage admises en V2 avec garde-fous

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T03
- **Exigences liées** : F-35, F-90, F-91, CU-4, CU-5, NF-15 ; §3 du cahier (hors périmètre : identification de personnes) ; constats A-14, A-39, A-45 ; ADR-0014 ; cas d'abus C-03

## Contexte

Trois fonctions servent à la fois à protéger et à identifier une source (A-14) : l'empreinte de capteur (F-35, T45) relie une photo à un appareil ; les points de traçage d'imprimante (F-90, T94) révèlent l'imprimante et la date d'impression ; la comparaison d'exemplaires (F-91, T93) montre les variantes propres à chaque destinataire. ADR-0014 a reporté T93 et T94 après le modèle de menace, au plus tôt en V2. L'adversaire à considérer est l'organisation qui cherche l'auteur d'une fuite (A4).

Constat qui fonde l'arbitrage : cette organisation n'a pas besoin de l'outil. Elle connaît les variantes qu'elle a diffusées et peut comparer elle-même ; des outils libres décodent déjà les points de traçage. Le gain que l'outil lui apporte est faible ; celui qu'il apporte au journaliste, qui veut savoir quoi neutraliser avant de publier, est réel.

## Options envisagées

### Option A — Admises en V2 avec garde-fous

- Avantages : le journaliste détecte les marques invisibles avant publication ; le projet ne livre pas d'outil d'attribution.
- Inconvénients : le code étant libre, un tiers peut ajouter ce que le projet s'interdit.

### Option B — Admises sans restriction

- Avantages : fonctions complètes ; des outils libres le font déjà.
- Inconvénients : le projet devient aussi un outil d'identification de source, contre NF-15 et le hors-périmètre du §3.

### Option C — Exclues définitivement

- Avantages : aucun double usage.
- Inconvénients : le journaliste perd la détection des marques invisibles ; T45 sert aussi l'authenticité (CU-4).

## Décision

T45, T93 et T94 restent candidates pour la V2 (ADR-0012), sous ces garde-fous :

- **T94 (points de traçage)** : signale la **présence** d'un motif de traçage et recommande de ne pas publier le document tel quel ; **ne décode ni** le numéro de série **ni** la date.
- **T93 (comparaison d'exemplaires)** : montre les zones qui diffèrent entre les exemplaires fournis, présentées comme « à neutraliser avant publication » ; **n'attribue aucun exemplaire** à un destinataire et ne tient aucun registre de destinataires.
- **T45 (PRNU)** : compare seulement à des photos de référence fournies par l'utilisateur, avec la direction « même appareil » ou « non concluant » ; aucune base d'empreintes d'appareils.
- La fiche technique de chacune décrit le double usage et ce que la fonction s'interdit.

## Raisons

- Option A retenue : elle garde la valeur protectrice de ces fonctions pour le public visé (ADR-0009) en refusant ce qui ne sert qu'à identifier.
- Option B écartée : elle fait du projet un outil d'identification de source, à rebours de NF-15.
- Option C écartée : elle prive le journaliste d'une protection, alors que l'adversaire dispose déjà d'autres moyens.

## Conséquences

- Le découpage précise T45, T93 et T94 ; ADR-0014 est complété, non remplacé (il reportait la décision à T03).
- Le modèle de menace porte ces garde-fous (ES-21) et le risque résiduel du code libre (RR-07).
- Toute levée d'un garde-fou demandera un nouvel ADR et une révision du modèle de menace.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
