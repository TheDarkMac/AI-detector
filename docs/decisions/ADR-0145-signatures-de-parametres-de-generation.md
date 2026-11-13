# ADR-0145 — Signatures de paramètres de génération : celles que montre le code public d'un outil

- **Statut** : Proposé
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T22, à valider pendant la revue de la PR de T22
- **Tâche** : T22
- **Exigences liées** : F-12, F-14, F-26 ; ES-09, ES-20 ; C-02 ; ADR-0084, ADR-0089, ADR-0117, ADR-0118, ADR-0142, ADR-0144

## Contexte

F-12 cite les « paramètres de génération » parmi les traces des outils connus. Plusieurs outils de génération d'images enregistrent leurs réglages dans le fichier : requête, nombre d'étapes, graine, modèle. Le projet ne cite une signature que s'il peut en montrer la source (précédent d'ERR-0002) : aucun générateur ne tourne sur le poste, et aucun échantillon produit par un générateur n'est dans le dépôt.

Le code source des outils libres montre ce qu'ils écrivent. Vérifié le 2026-11-13 :

| Outil | Source | Ce qu'il écrit |
| --- | --- | --- |
| stable-diffusion-webui d'AUTOMATIC1111 | `modules/images.py`, `modules/processing.py` (`create_infotext`), branche `master` | PNG : bloc texte `parameters` ; JPEG et WebP : étiquette EXIF `UserComment`, codée « unicode » par piexif. Texte : la requête, `Negative prompt: …` s'il y en a une, puis la ligne `Steps: …, Sampler: …, …` |
| ComfyUI | `nodes.py` (`SaveImage`), `execution.py`, branche `master` | PNG : bloc texte `prompt`, le graphe en JSON, dont chaque nœud porte la clé `class_type` ; un bloc par clé des informations supplémentaires de l'interface (dont `workflow`) |
| InvokeAI | `invokeai/app/services/image_files/image_files_disk.py`, branche `main` | PNG : blocs texte `invokeai_metadata`, `invokeai_workflow`, `invokeai_graph`, `invokeai_resolved_inputs` |
| InvokeAI 2 | `ldm/invoke/pngwriter.py`, version 2.3.5 | PNG : blocs texte `sd-metadata` (JSON) et `Dream` |

NovelAI et Midjourney n'ont pas de code public ; les descriptions trouvées de leurs métadonnées sont celles de tiers, divergentes : aucune signature propre ne leur est donnée.

## Options envisagées

### Option A — Une règle par trace attestée, sur un trait propre au format

Pour chaque outil, la trace la moins ambiguë : un motif propre au format du texte, ou un mot-clé qui nomme l'outil.

- Avantages : chaque règle cite sa source ; un mot-clé générique (`prompt`, `parameters`) ne suffit pas seul à faire un constat.
- Inconvénients : le motif ne voit que les 4 096 premiers caractères d'un texte (ADR-0118).

### Option B — Présence du mot-clé seule

Constat dès qu'un bloc `parameters`, `prompt` ou `workflow` existe.

- Avantages : insensible à la coupe des textes.
- Inconvénients : `prompt` et `parameters` sont des mots courants, qu'un autre logiciel peut employer.

### Option C — Lire le texte en entier pour ces mots-clés

Lever, pour ces blocs, la coupe à 4 096 caractères.

- Avantages : la ligne des paramètres est vue même après une longue requête.
- Inconvénients : change ADR-0118 et le module `textepng` pour un cas rare ; un texte entier au rapport grossit chaque constat.

## Décision

Option A.

| Règle | Observation | Test |
| --- | --- | --- |
| R-TEXTEPNG-001 (AUTOMATIC1111, PNG) | `textepng.parameters` | motif `Steps: [0-9]+, Sampler:` |
| R-EXIF-002 (AUTOMATIC1111, JPEG et WebP) | `exif.exif.UserComment` | même motif |
| R-TEXTEPNG-002 (ComfyUI) | `textepng.prompt` | motif `"class_type"\s*:` |
| R-TEXTEPNG-003 (InvokeAI) | `textepng.invokeai-metadata` | présente |
| R-TEXTEPNG-004 (InvokeAI 2) | `textepng.sd-metadata` | présente |

- Direction `origine_ia`, indice faible de déclaration (ADR-0142).
- La phrase n'a pas de paramètre : elle dit le format reconnu, sans recopier la requête ; le texte entier figure parmi les données du constat, comme toute observation.
- Le mot-clé `invokeai_metadata` est observé `textepng.invokeai-metadata` : le tiret bas devient un tiret (ADR-0117).
- Traces écartées : le bloc `workflow` de ComfyUI (écrit par l'interface, pas par `SaveImage`, et sans trait propre dans ses premiers caractères), le bloc `Dream` d'InvokeAI 2 (mot courant), les blocs `invokeai_workflow`, `invokeai_graph` et `invokeai_resolved_inputs` (écrits avec `invokeai_metadata` : un constat de plus pour le même fait).

## Raisons

- Option A proposée : elle tient la règle du projet sur les sources, et chaque motif porte sur un trait du format que l'outil documente par son code.
- Option B écartée : un faux positif sur un logiciel qui emploie le mot-clé `prompt` pour autre chose.
- Option C écartée : la coupe protège le rapport d'un texte démesuré ; une requête de plus de 4 096 caractères est rare, et la limite est écrite dans la règle.

## Conséquences

- Les autres interfaces qui reprennent ces formats sont vues sous le nom du format : la limite de chaque règle le dit.
- Un outil sans code public n'a de règle que par son nom (ADR-0144) ou par une déclaration IPTC (ADR-0143).
- Un échantillon réel de chaque outil, ajouté au corpus (T100), permettra de mesurer ces règles.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création, statut « Proposé » |
