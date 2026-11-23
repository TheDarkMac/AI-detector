# ADR-0226 — Borne des images extraites d'un fichier : seize au plus, dans l'ordre des pages, jusqu'à 2 Mio

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, en deux temps : seize images d'abord, puis le budget de 2 Mio, après la mesure de l'assistant
- **Tâche** : T53
- **Exigences liées** : F-63, F-82, NF-06, NF-08, ES-03 ; ADR-0023, ADR-0076, ADR-0077, ADR-0078, ADR-0224, ADR-0225

## Contexte

Une partie extraite passe par tous les modules de son format : pour un JPEG, huit modules, dont trois qui décodent ses données entropiques en Python (double compression, ELA, filigrane dwtDct). Le délai d'analyse d'un fichier est fixe, 120 s (ADR-0077) ; au-delà, l'analyse est interrompue et sort de la garantie de reproductibilité (ADR-0023). Un document peut porter des centaines d'images.

Mesures de l'assistant, sur le poste de développement (4 cœurs), temps des modules d'image seuls, au-delà des 2,5 s de lancement du processus de travail :

| Image JPEG | Octets | `dwtdct` | `ela` | `doublejpeg` | Autres modules | Total |
| --- | --- | --- | --- | --- | --- | --- |
| 400 × 300 | 41 Kio | 0,4 s | 0,1 s | 0,1 s | < 0,1 s | 0,6 s |
| 800 × 600 | 144 Kio | 1,0 s | 1,1 s | 0,8 s | < 0,1 s | 2,9 s |
| 1 600 × 1 200 | 534 Kio | 4,4 s | 3,0 s | 2,9 s | < 0,5 s | 10,5 s environ |
| 2 480 × 3 508 | 2,3 Mio | 9,3 s | 5,0 s | 2,9 s | < 0,5 s | 17,5 s environ |
| 4 000 × 3 000 | 3,2 Mio | 10,0 s | 6,1 s | 3,9 s | 1,0 s | 21 s environ |

Le coût suit surtout la taille des données compressées, environ 20 ms par Kio jusqu'à 2 Mo, moins au-delà (ELA et la double compression bornent les blocs qu'ils examinent). Un PDF de dix-sept photos de 4 000 × 3 000 a été interrompu à 120 s.

## Options envisagées

### Première question, avant la mesure

- **Option A — Seize images, dans l'ordre des pages (recommandée alors)** : les seize premières images distinctes ; les suivantes comptées et déclarées non menées pour limite dépassée.
- **Option B — Les seize plus grandes** : vise les photos, mais une petite image retouchée peut être laissée de côté.
- **Option C — Toutes** : un document très illustré dépasse le délai.

TheDarkMac a retenu l'option A, sur recommandation de l'assistant, qui la présentait comme tenant dans le délai. La mesure ci-dessus l'a démentie : seize photos demandent plus de 300 s.

### Seconde question, après la mesure

- **Option D — Budget de 2 Mio (recommandée)** : dans l'ordre des pages, seize images au plus, tant que la somme de leurs tailles, lue dans la structure (`/Length`), n'a pas atteint 2 Mio ; celle qui franchit le seuil est encore analysée, les suivantes non. Une photo seule l'est toujours ; pire cas estimé alors à 50 s environ (mesure : voir Conséquences).
- **Option E — Quatre images** : simple à dire ; environ 80 s estimées pour quatre photos de 12 Mpx, interruption au-delà.
- **Option F — Garder seize** : un document de plus de cinq ou six photos est interrompu.

## Décision

Option D. Précisions de l'assistant :

- Bornes dans `_limites.py` : `OCTETS_EXTRAITS_MAX` (2 Mio) ; dans le modèle, `NOMBRE_MAX_EXTRAITES` (16), qui borne aussi la liste du rapport et du message `extraction`.
- Le moteur tient le compte pour tout le fichier : chaque contenu accepté par un contexte compte, qu'il soit reconnu ou non ensuite (ADR-0224). Le contexte refuse un contenu quand seize ont été acceptés, ou quand les octets acceptés atteignent le seuil.
- La première extraction refusée est déclarée non menée pour `limite_depassee`, localisée par sa page et son objet, sans module (comme une limite du fichier) ; le module compte toutes les refusées (`imagespdf.au_dela`) et R-IMAGESPDF-003 le dit (ADR-0227).
- L'ordre est celui de la recherche (ADR-0225) : pages, puis ressources de chaque page dans l'ordre du fichier, puis formes.

## Raisons

- Option D retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option A abandonnée : elle ne tient pas le délai, contrairement à ce que l'assistant avait annoncé sans mesure.
- Options B et C écartées à la première question : B laisse de côté une petite image ; C dépasse le délai.
- Option E écartée : quatre photos de grande taille dépassent déjà le délai sur un poste plus lent.
- Option F écartée : elle interrompt l'analyse des documents illustrés.
- Taille lue dans la structure plutôt que dimensions : le coût suit la taille des données ; elle est connue sans lire le JPEG, et ne peut pas mentir sur la plage analysée.

## Conséquences

- Le même document donne les mêmes parties extraites sur toutes les machines (NF-06) ; le délai reste un garde-fou, plus la borne ordinaire.
- Un document dont la première image fait plus de 2 Mio n'en fait analyser qu'une : R-IMAGESPDF-003 et la non menée le disent.
- La borne est à revoir si le décodage entropique devient plus rapide (coût d'import de numpy, décodage en numpy) ; une nouvelle mesure sur le corpus (T100) dira la part de documents dont des images ne sont pas analysées.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création : seize images (option A), choisies par TheDarkMac au début de T53 ; remplacées le même jour par le budget de 2 Mio (option D), après la mesure de l'assistant |
| 2026-11-23 | Renvoi : bornes reprises pour les images d'un DOCX ou d'un ODT, dans l'ordre de l'archive ; une image compressée compte pour sa taille décompressée ([ADR-0253](ADR-0253-images-cherchees-dans-un-docx-et-un-odt.md), [ADR-0254](ADR-0254-parties-extraites-decompressees.md)) (complément de T81) |
