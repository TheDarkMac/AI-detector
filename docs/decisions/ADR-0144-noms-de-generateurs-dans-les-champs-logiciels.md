# ADR-0144 — Noms de générateurs : une liste de noms distinctifs, appliquée à chaque champ logiciel

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T22
- **Exigences liées** : F-12, F-14, F-26 ; ES-09, ES-20 ; C-02 ; ADR-0019, ADR-0084, ADR-0089, ADR-0117, ADR-0133, ADR-0140, ADR-0142

## Contexte

F-12 demande de repérer le nom du logiciel d'un outil de génération connu. Chaque famille de métadonnées a son champ logiciel : `Software` d'EXIF et du PNG, `xmp:CreatorTool` et l'historique XMP, `OriginatingProgram` d'IPTC-IIM, `Creator` et `Producer` d'un PDF, `TSSE` d'ID3, `ISFT` d'un WAV, `ENCODER` de Vorbis, `©too` et `©swr` de QuickTime, `WritingApp` et la balise `ENCODER` d'un WebM, `Application` d'un DOCX, `meta:generator` d'un ODT.

Aucun éditeur de générateur ne documente, à la date de T22, ce qu'il écrit dans ces champs, et aucun générateur ne tourne sur le poste pour le vérifier. Il fallait choisir entre une liste de noms et les seules traces que le code public d'un outil écrit (ADR-0145).

## Options envisagées

### Option A — Liste de noms distinctifs, appliquée à chaque champ logiciel

Une liste de produits de génération dont le nom n'est pas un mot courant, cherchée dans chaque champ logiciel des modules ; le constat dit « le champ nomme X ».

- Avantages : le constat reste vrai même si l'éditeur n'écrit pas ce champ : il rapporte ce que le fichier déclare ; un ajout à la liste ne change que le catalogue (F-26).
- Inconvénients : seize règles portent le même motif, à tenir ensemble ; un nom absent de la liste ou mal écrit n'est pas vu.

### Option B — Signatures attestées seules

Aucune règle sur les noms de logiciel ; seules les traces écrites par un code public (AUTOMATIC1111, ComfyUI, InvokeAI).

- Avantages : chaque règle repose sur une source qui montre l'écriture.
- Inconvénients : F-12 n'est tenue que pour les paramètres, pas pour « le nom du logiciel » qu'elle cite.

## Décision

Option A.

- Liste, sans égard à la casse, chaque nom entre deux limites de mot : Midjourney, DALL·E (`DALL-E`, `DALL·E`, `DALL E`), Stable Diffusion (`StableDiffusion`, `stable-diffusion` compris), Adobe Firefly, ComfyUI, InvokeAI (`Invoke AI`), NovelAI, AUTOMATIC1111, Fooocus, Leonardo.Ai, Ideogram, Craiyon, DreamStudio, ChatGPT, Suno, Udio, ElevenLabs. Chaque nom est celui d'un produit de génération par IA, publié à l'une de ces adresses : midjourney.com, openai.com (DALL·E), chatgpt.com, stability.ai (Stable Diffusion), dreamstudio.ai, adobe.com (Firefly), github.com/comfyanonymous/ComfyUI, github.com/invoke-ai/InvokeAI, novelai.net, github.com/AUTOMATIC1111/stable-diffusion-webui, github.com/lllyasviel/Fooocus, leonardo.ai, ideogram.ai, craiyon.com, suno.com, udio.com, elevenlabs.io. Le 2026-11-13, chacune répondait ; six refusent une requête automatique (code 403), sans que la page ait été lue. Aucune n'a été lue pour savoir ce que le produit écrit dans ses fichiers.
- Noms écartés, parce qu'ils sont des mots courants ou des noms d'autres logiciels : Firefly seul, Imagen, Gemini, Flux, Sora, Runway, Copilot, Designer ; `Dalle` sans séparateur (« dalle » est un mot français).
- Seize règles, une par champ, toutes au même motif, au paramètre `logiciel` : R-EXIF-001, R-TEXTEPNG-005, R-XMP-004 (`xmp:CreatorTool`), R-XMP-005 (`stEvt:softwareAgent` de `xmpMM:History`), R-IPTC-001, R-INFOPDF-001 (`Creator`), R-INFOPDF-002 (`Producer`), R-ID3-001 (`TSSE`), R-INFOWAV-001 (`ISFT`), R-VORBIS-001 (`ENCODER`), R-QUICKTIME-001 (`©too`), R-QUICKTIME-002 (`©swr`), R-MATROSKA-001 (`WritingApp`), R-MATROSKA-002 (balise globale `ENCODER`), R-OOXML-001 (`Application`), R-ODF-001 (`meta:generator`). Un test vérifie qu'elles portent le même motif.
- Direction `origine_ia` (ADR-0142) ; la limite de chaque règle dit qu'un générateur a pu servir à retoucher ou à convertir.
- Champs non retenus : `xmp:tiff:Software` et `quicktime.mdta.com-apple-quicktime-software` (logiciel de l'appareil), `vorbis.vendor` et `matroska.MuxingApp` (bibliothèque, pas logiciel), balises de piste d'un WebM, `TSS` d'ID3v2.2 ; ils restent des observations.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle laisse sans règle la moitié de F-12.
- Un seul motif plutôt qu'une liste par famille : un générateur peut écrire son nom dans n'importe quel champ ; une seule liste se relit et se met à jour d'un coup.
- Noms communs écartés : un faux positif sur « Gemini » ou « Flux », mots d'autres logiciels, coûte plus à la confiance du rapport que le nom manqué.

## Conséquences

- Le motif compte 192 caractères, sous la borne de 1 024, et son programme compilé 181 instructions, sous celle de 5 000 (ADR-0089, mesure faite sur le poste avec la version de RE2 du verrou).
- Ajouter un nom change seize règles : chacune voit sa version augmenter, et le catalogue sa version `Y` (ADR-0085).
- Un générateur qui n'écrit pas son nom, ou l'efface, n'est pas vu ; un fichier peut se dire écrit par un générateur sans l'être (C-02).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création |
