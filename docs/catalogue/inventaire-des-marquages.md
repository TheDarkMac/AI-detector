# Inventaire des marquages et des filigranes invisibles

> Statut : **v1.0**, proposée dans la PR de T31. Inventaire daté : chaque affirmation a été vérifiée le **2026-11-14** sur la source citée, et vaut à cette date. Les marquages évoluent vite : l'inventaire se refait avant chaque version du catalogue qui touche aux marquages.
> Exigences : F-24, F-25, F-26 ; A-03, A-21, A-35 de l'[analyse critique](../01-analyse/analyse-critique-cdc-v0.1.md).
> Décisions : [ADR-0012](../decisions/ADR-0012-perimetre-v1.md), [ADR-0016](../decisions/ADR-0016-frontiere-sans-ia.md), [ADR-0174](../decisions/ADR-0174-inventaire-et-lecteur-dwtdct.md) à [ADR-0179](../decisions/ADR-0179-versions-de-t31.md).

L'inventaire répond à la question d'ADR-0012 : quels filigranes invisibles ont un lecteur public qui n'est pas un réseau de neurones ? Il recense aussi les autres marquages de provenance, pour que le rapport dise lesquels il recherche et lesquels il ne recherche pas (F-25). Les entrées retenues sont inscrites au catalogue, dans [`marquages.toml`](../../src/voight_kampff/donnees/catalogue/marquages.toml) ; le [README du catalogue](README.md) en décrit la forme.

## 1. Méthode

Sources primaires d'abord : code des générateurs et des lecteurs, spécifications, articles. Quand seule une source secondaire est disponible (presse), l'inventaire le dit. Rien n'est affirmé sans source (ERR-0002) ; ce qui n'a pas été vérifié est marqué « non examiné ».

Un schéma est **lisible** par l'outil s'il réunit quatre conditions :

| Condition | Raison |
| --- | --- |
| Algorithme de lecture publié, avec un code de référence | Le rapport doit pouvoir dire comment le constat est établi (ADR-0019) |
| Lecteur sans réseau de neurones | Aucune IA embarquée (ADR-0016) |
| Lecture sans la clé secrète du fournisseur | Une clé publiée ne serait plus secrète ; une clé privée n'est pas disponible |
| Posé par un générateur ou une chaîne de provenance | Un filigrane que personne ne pose sur des contenus générés ne répond à aucune question du rapport |

## 2. Résultat

Un seul schéma de filigrane remplit les quatre conditions : le **dwtDct** de la bibliothèque invisible-watermark, posé par les codes de référence de Stable Diffusion 1, de SDXL et de FLUX.1 (§3). Son lecteur demande de décoder les pixels : il est confié à une tâche à part, T32 ([ADR-0174](../decisions/ADR-0174-inventaire-et-lecteur-dwtdct.md)). Deux marquages qui ne sont pas des filigranes se lisent sans IA et sont déjà recherchés : le manifeste C2PA (module `c2pa`, T30) et le type de source numérique de l'IPTC (module `xmp`, T22). Un troisième, le manifeste C2PA écrit dans un texte brut, se lit de façon déterministe ; sa lecture relève du module texte (T80).

| Marquage | Médias | Posé par | Lecteur public | Réseau de neurones | Clé du fournisseur | Catalogue |
| --- | --- | --- | --- | --- | --- | --- |
| Manifeste C2PA intégré | image, son, vidéo, PDF, bureautique | Générateurs et logiciels qui suivent la C2PA | Oui (c2pa-rs) | Non | Non (signature vérifiée par une liste de confiance) | `M-C2PA`, recherché (`c2pa`) |
| Type de source IPTC dans XMP | formats qui portent du XMP | Générateurs et logiciels qui suivent l'IPTC | Oui (lecture XMP) | Non | Non | `M-IPTC-DST`, recherché (`xmp`) |
| Filigrane dwtDct d'invisible-watermark | image | Codes de référence de SD 1, SDXL, FLUX.1 | Oui | Non | Non (message fixe, publié) | `M-DWTDCT`, lecteur à venir (T32) |
| Manifeste C2PA dans un texte brut | texte | Spécification C2PA 2.3, annexe A.7 | Algorithme publié | Non | Non | `M-C2PA-TEXTE`, lecteur à venir (T80) |
| SynthID (images, son, vidéo) | image, son, vidéo | Services de Google ; d'après la presse, aussi d'autres fournisseurs lus par le même portail | Non : portail SynthID Detector | — | — | `M-SYNTHID`, lecteur propriétaire |
| SynthID Text | texte | Modèles de langage qui l'emploient | Code public | Détecteur entraîné pour chaque clé | Oui | `M-SYNTHID-TEXTE`, clé du fournisseur |
| Filigranes de texte à liste verte | texte | Modèles qui l'emploient | Code public | Non | Oui | `M-LISTE-VERTE`, clé du fournisseur |
| TrustMark (Adobe), variantes Q, C, P | image | Chaînes Content Credentials (liaison souple C2PA) | Oui (MIT) | Oui (décodeurs ResNet) | Non | `M-TRUSTMARK`, lecteur neuronal |
| Video Seal, AudioSeal, Watermark Anything (Meta) | vidéo, image, son | Générateurs qui les emploient | Oui (MIT) | Oui | Non | `M-META-SEAL`, lecteur neuronal |
| InvisMark, WavMark (Microsoft) | image, vidéo, son | Inscrits à la liste C2PA des liaisons souples | Article et code | Oui | Non | `M-MICROSOFT`, lecteur neuronal |

## 3. Le filigrane dwtDct d'invisible-watermark

**Bibliothèque.** [invisible-watermark](https://github.com/ShieldMnt/invisible-watermark) (ShieldMnt, MIT), version 0.2.0 sur PyPI (2023-07-06). Elle offre trois méthodes : `dwtDct` (par défaut), `dwtDctSvd` et `rivaGan`, cette dernière un réseau de neurones. Ses dépendances déclarées comprennent `opencv-python` et `torch`, même pour les deux premières : l'outil ne peut pas l'employer telle quelle (ADR-0016, ADR-0043).

**Algorithme** (lu dans `imwatermark/maxDct.py`) :

1. L'image, en BGR, est convertie en YUV par OpenCV (`COLOR_BGR2YUV`), recadrée à un multiple de 4 pixels.
2. Pour chaque canal dont l'échelle est positive parmi les deux premiers (Y, U) : transformée en ondelettes de Haar à un niveau ; seule la bande basse fréquence (`ca1`) est employée. Les échelles par défaut sont `[0, 36, 36]` et la boucle ne parcourt que les canaux 0 et 1 : seul U porte le message.
3. La bande est découpée en blocs de 4 × 4 ; chaque bloc porte un bit, les bits du message se répétant dans l'ordre des blocs.
4. À la lecture, chaque bloc donne un score tiré de son plus grand coefficient DCT non trivial, quantifié à l'échelle 36 ; les scores d'un même bit sont moyennés, et le bit vaut 1 si la moyenne dépasse 127/255.
5. Le lecteur refuse une image de moins de 256 × 256 pixels (produit des côtés inférieur à 65 536).

Le lecteur rend toujours des bits : la présence du filigrane se juge en comparant ces bits au message attendu, ce qui demande un seuil de bits concordants. Le taux de faux positifs dépend de ce seuil et de la distribution des bits lus sur des images non marquées ; il n'est pas mesuré (T32).

**Messages posés.**

| Générateur | Code | Message | Longueur |
| --- | --- | --- | --- |
| Stable Diffusion 1 | [CompVis, `scripts/txt2img.py`](https://github.com/CompVis/stable-diffusion/blob/main/scripts/txt2img.py) | octets de « StableDiffusionV1 » | 136 bits |
| SDXL | [Stability-AI, `sgm/inference/helpers.py`](https://github.com/Stability-AI/generative-models/blob/main/sgm/inference/helpers.py) ; repris par [diffusers](https://github.com/huggingface/diffusers/blob/main/src/diffusers/pipelines/stable_diffusion_xl/watermark.py) | `0xB3EC907BB19E` | 48 bits |
| FLUX.1 | [Black Forest Labs, `src/flux/util.py`](https://github.com/black-forest-labs/flux/blob/main/src/flux/util.py) | `0x2AFE879CF52E`, écrit par `bin()`, qui retire les deux zéros de tête | 46 bits |

Dans diffusers, le pipeline SDXL pose le filigrane par défaut si invisible-watermark est installée (`add_watermarker`). Stable Diffusion 2 poserait « SDV2 » ; seules des copies du script l'attestent, le dépôt d'origine (`Stability-AI/stablediffusion`) répondant 404 le 2026-11-14 : non retenu.

**Robustesse**, selon le README de la bibliothèque (essais sur une image de 1960 × 1080, message de 64 bits) : la méthode résiste à la compression JPEG, au bruit, à la luminosité, à la superposition et au masquage ; elle ne résiste ni au redimensionnement de moitié, ni au recadrage qui change les proportions, ni à la rotation.

**Ce qu'il établirait.** Un message dwtDct retrouvé est un indice que l'image est passée par un de ces codes de référence ; il ne prouve rien (ADR-0021) : le message est public et fixe, n'importe qui peut le poser sur une photo ; le schéma n'est pas cryptographique. Son absence ne dit rien : la plupart des interfaces peuvent ne pas le poser, et un redimensionnement l'efface.

## 4. Les autres schémas

- **SynthID** (Google) : image, son, vidéo. La vérification passe par le portail SynthID Detector ([billet de Google](https://blog.google/innovation-and-ai/products/google-synthid-ai-content-detector/) de son lancement, en 2025) ; d'après la presse, il est ouvert au public depuis octobre 2026 et ses conditions interdisent la vérification en masse. Aucun lecteur public.
- **SynthID Text** ([dépôt](https://github.com/google-deepmind/synthid-text), Apache-2.0 ; [documentation](https://ai.google.dev/responsible/docs/safeguards/synthid)) : le code est public et intégré à Transformers, mais la détection demande les clés du fournisseur et un détecteur bayésien entraîné pour chaque clé ; la documentation recommande de garder les clés secrètes.
- **Filigranes à liste verte** ([Kirchenbauer et al.](https://arxiv.org/abs/2301.10226)) : détection par un test statistique (score z) que l'article dit publiable, à condition de connaître la clé, la fonction de hachage et le découpage en jetons. Aucun fournisseur connu de l'inventaire ne publie les siens.
- **TrustMark** ([dépôt](https://github.com/adobe/trustmark), MIT, modèles compris) : encodeur et décodeur sont des réseaux, fondés sur ResNet-50, ou ResNet-18 pour la variante compacte C, d'après sa FAQ ; implémentations Python (PyTorch), JavaScript, Rust et C++ (ONNX). Inscrit à la liste C2PA des liaisons souples (identifiants 4, 5 et 13).
- **Meta** : [Video Seal](https://github.com/facebookresearch/videoseal) (incrusteur et extracteur entraînés ensemble), [AudioSeal](https://github.com/facebookresearch/audioseal) (générateur et détecteur), [Watermark Anything](https://github.com/facebookresearch/watermark-anything) (dépôt archivé), tous sous MIT et tous neuronaux.
- **Microsoft** : [InvisMark](https://arxiv.org/abs/2411.07795) (« architectures de réseaux de neurones » selon son résumé) et [WavMark](https://github.com/wavmark/wavmark) (modèle PyTorch), inscrits à la liste C2PA des liaisons souples (identifiants 19 et 20).
- **Recherche, non posés par un fournisseur connu de l'inventaire** : Stable Signature ([arXiv 2303.15435](https://arxiv.org/abs/2303.15435)) se lit par un extracteur pré-entraîné ; Tree-Ring ([arXiv 2305.20030](https://arxiv.org/abs/2305.20030)) se lit en inversant le processus de diffusion, donc avec le modèle ; RivaGAN, troisième méthode d'invisible-watermark, est un réseau. Non inscrits.
- **audiowmark** ([S. Westerfeld](https://uplex.de/audiowmark/README.html), GPL) : algorithme de lecture public et sans réseau de neurones (« patchwork » dans le spectre) ; sa documentation recommande une clé AES de 128 bits, sans laquelle un message ainsi posé ne se lit pas. Aucun générateur connu de l'inventaire ne l'emploie. Non inscrit.

## 5. Liste C2PA des liaisons souples

La [liste des algorithmes de liaison souple](https://github.com/c2pa-org/softbinding-algorithm-list) de la C2PA (fichier `softbinding-algorithm-list.json`, 28 entrées le 2026-11-14, SHA-256 `bf59c699d9dcfb5376ad56794d0bd5657ac841f2b03ba56b2b324366bed2acaa`) recense les filigranes et empreintes perceptuelles qui permettent de retrouver un manifeste retiré du fichier. Une inscription n'est pas une certification. Au-delà des entrées vues au §4 :

| Entrées | Type | Examen |
| --- | --- | --- |
| Digimarc Validate ; Steg.AI ; Trufo (deux variantes) ; Overlai ; Teletrax (Kinetiq) ; castLabs ; Imatag ; NAGRA NexGuard ; Mentaport ; SonicOrigin ; ContentLens (cinq variantes) ; MarkAny ; Verimatrix | Filigranes | Non examinés un par un : l'adresse d'information de chacun est la page d'un produit ou d'une API commerciale, ou un article ; aucun n'est connu de l'inventaire pour être posé par un générateur. Non inscrits au catalogue |
| ATSC A/334, A/335, A/336 | Filigranes de diffusion télévisuelle | Normes de radiodiffusion, sans lien connu avec la génération. Non inscrits |
| LumaTrace | Filigrane | Implémentation de référence annoncée en Java ; non examinée. Non inscrit |
| ISCC v0 (ISO 24138) ; Adobe ICN ; DigiCAP | Empreintes, pas des marquages | Une empreinte n'est pas posée dans le contenu : elle se compare à une base. Hors du champ |

## 6. Ce que l'inventaire ne couvre pas

- Les marquages **visibles** (logo, mention incrustée) : ils se lisent à l'œil, l'outil ne fait pas de reconnaissance d'image (ADR-0016).
- Les **signatures de générateurs** dans les métadonnées (champ Software, blocs texte PNG) : ce sont des règles du catalogue (F-12, T22), pas des marquages ([ADR-0176](../decisions/ADR-0176-marquages-de-provenance.md)).
- Les caractères invisibles qu'un modèle de langage laisserait dans un texte sans schéma publié : rien ne les documente comme un marquage.

## 7. Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-11-14 | 1.0 | Création | T31 |
