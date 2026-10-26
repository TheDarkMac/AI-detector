# ADR-0012 — Périmètre de la première version

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §3, §5 du cahier ; priorisation des exigences F et NF (§10) ; constats A-09, A-35, A-38, A-40

## Contexte

Le §10 demande de fixer le périmètre de la V1 (médias, formats, techniques, ordre) et la priorisation des exigences. L'analyse a montré que la liste du §5.4 est un catalogue de candidats plutôt qu'un engagement (A-09), et que plusieurs exigences sont presque vides une fois le « sans IA » appliqué : F-24 (A-35), F-51 (A-38), F-41 et F-42 (A-40). Le choix suit l'objectif (ADR-0008) et le public (ADR-0009).

## Options envisagées

### Option A — Socle, métadonnées, C2PA, structure PDF et analyses JPEG

- Avantages : ce qui produit des preuves ou des indices peu contestables, sur tous les médias pour les métadonnées et C2PA ; le PDF sert directement les vérificateurs et, en second, les profils RH ; les deux analyses JPEG sont bien documentées et peu ambiguës.
- Inconvénients : pas d'analyse du signal audio ni vidéo en V1.

### Option B — Chemin critique minimal : socle, métadonnées, C2PA

- Avantages : le plus court.
- Inconvénients : aucune analyse de structure ni de signal ; l'outil n'aurait presque rien à dire d'un fichier sans métadonnées ni manifeste.

### Option C — Option A, plus ELA et audio de base

- Avantages : ELA est attendue du public visé ; l'audio couvrirait un média de plus.
- Inconvénients : l'ELA est souvent mal lue et ne distingue pas la génération (A-02) ; V1 nettement plus longue.

### Option D — Tout le §5

- Avantages : respecte le cahier à la lettre.
- Inconvénients : très long ; engage des exigences presque vides sans IA (F-24, F-51, F-70).

## Décision

### Contenu de la V1

| Phase | Tâches V1 | Exigences |
| --- | --- | --- |
| P1 — Socle | T10 à T18 | F-01 à F-05, F-80 à F-83 ; toutes les NF (NF-06 et NF-19 reformulées : ADR-0023, ADR-0019) |
| P2 — Métadonnées | T20 à T25 (T25 limité par ADR-0014) | F-06, F-10 à F-14, F-90 (partie métadonnées) |
| P3 — Provenance | T30 ; T31 réduit (voir ci-dessous) | F-20 à F-23, F-24 (point d'extension), F-25, F-26 |
| P4 — Image | T40, T41 | F-30, F-31 |
| P5 — PDF | T50 à T53 | F-60 à F-63, F-84 (chronologie des révisions) |
| P8 — Texte | T80, T81 (ADR-0013) | F-71, F-73 |
| P9 — Restitution | T90 (ligne de commande et rapport HTML), T91 (portée fixée en T03), T92, T95 | NF-05, NF-11, NF-12, NF-17, NF-19 |
| P10 — Qualité et livrables | T100 à T103, T105 (ADR-0026) | §8, §9 |

Tous les formats du §3 sont acceptés en V1 (F-01) : chacun reçoit au moins l'identification, les métadonnées et la recherche C2PA ; les analyses qui ne s'y appliquent pas figurent dans les analyses non menées (F-82). La matrice « format × technique » (A-23) est tenue dans les fiches techniques (ADR-0022) et le catalogue (T15).

### Précisions par exigence

- **F-24** : T31 se limite à l'inventaire des filigranes dont un lecteur public, non neuronal, est disponible, et à un point d'extension du catalogue. Si l'inventaire ne trouve aucun schéma lisible, le catalogue V1 est vide et le rapport le dit (F-25).
- **F-63** : extraction de la couche texte native et des images ; aucune lecture des documents numérisés (ADR-0017).
- **F-84** : en V1, seule la chronologie des révisions PDF ; les autres visualisations arrivent avec leurs techniques.

Les lignes P9 et P10 n'ont pas fait l'objet d'une question : elles découlent des NF, qui s'appliquent toutes à la V1, et des livrables du §9. Proposition de l'assistant, soumise à TheDarkMac dans la PR de T02.

### Candidats pour une V2 (ordre non fixé)

T42 (ELA), T43 (bruit), T44 (CFA), T45 (PRNU), T54 (comparaison PDF à des références), P6 audio (T60, T61, T63), P7 vidéo (T70 à T73), T93 et T94 (après T03, ADR-0014), analyse groupée (ADR-0015).

- **F-51** sera réécrite avant T71 : seules les analyses applicables à une image vidéo décodée sont retenues (F-33 au plus), F-30, F-31, F-32 et F-34 ne s'y appliquent pas (A-38).
- **F-41** sera limitée au silence numérique et au plancher de bruit (A-40).

### Hors V1, sans engagement

T62 (ENF : aucune base de référence identifiée, A-40), T82 (stylométrie) et T83 (références bibliographiques), voir ADR-0013.

### Ordre

Chemin critique T00 → T04, puis socle T10 → T18, puis métadonnées (P2), C2PA (T30), recueil d'avis sur prototype (ADR-0026), T31, analyses JPEG (T40, T41), PDF (T50 → T53), texte (T80, T81).

## Raisons

- Option A retenue : elle couvre l'objectif principal sur tous les médias par les métadonnées et C2PA, et ajoute les analyses de structure les plus utiles au public visé, sans s'engager sur des techniques fragiles.
- Option B écartée : un fichier dépouillé de ses métadonnées n'aurait aucune analyse ; le PDF est trop central pour le public visé.
- Option C écartée : l'ELA ne distingue pas la génération et demande un travail d'avertissement important ; l'audio n'est pas prioritaire pour ce public.
- Option D écartée : A-09, A-35, A-38, A-41.

## Conséquences

- Le §5 du cahier sert de catalogue de candidats ; la V1 ne prétend pas le couvrir. La couverture (F-25, F-82) dit au lecteur ce qui n'a pas été analysé.
- Les critères d'acceptation du §8 s'appliquent aux exigences de la V1 seulement.
- Le découpage passe en v0.6 : statut V1, V2 ou hors V1 de chaque tâche.
- Périmètre provisoire jusqu'au recueil d'avis sur prototype (ADR-0026) ; un changement donnera un nouvel ADR.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
