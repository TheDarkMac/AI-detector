# ADR-0153 — Indices de transfert retenus : signatures, captures d'écran, dimensions, tables de libjpeg

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T24
- **Exigences liées** : F-06, F-14, F-26, F-30 ; A-32, A-34 ; ADR-0022, ADR-0055, ADR-0144, ADR-0150, ADR-0151

## Contexte

F-06 demande de signaler les indices de transfert par messagerie ou de capture d'écran (recompression, dimensions typiques, métadonnées absentes), qui réduisent la portée des analyses. A-32 demande que les listes de référence (« dimensions typiques ») soient dans le catalogue, versionnées ; A-34, que l'absence de métadonnées reste neutre vis-à-vis de l'origine IA, mais utilisable comme indice de transfert. T23 a écrit les règles d'absence, une par module, en informations neutres (ADR-0151).

Faisabilité, établie avant la question :

- les douze modules de métadonnées observent déjà des champs où des outils de capture et des plateformes écrivent une marque reconnaissable ;
- aucun module n'observe les dimensions réelles d'une image ni ses tables de quantification ; une règle ne compare que les observations d'un même module (ADR-0147) ;
- les tailles des messageries ne sont documentées par aucun éditeur ; deux études les relèvent, à des dates différentes et sans concorder sur tout (Telegram à 2 560 en 2016, à 1 280 en 2020) ;
- la recompression est le sujet de T40 (tables connues, F-30) et de T41 (double compression, F-31).

## Options envisagées

Question posée à TheDarkMac, plusieurs choix permis : quelles familles T24 écrit-elle ?

- **Signatures documentées** : FBMD de Facebook dans le jeu IPTC SpecialInstructions (source : IPTC), `Software` à `gnome-screenshot` d'un PNG (source : code de gnome-screenshot). Avantage : catalogue seul, sur les observations existantes. Inconvénient : ne voit que ces deux outils.
- **« Screenshot » d'Apple** : `UserComment` à `Screenshot`, en EXIF ou en XMP (macOS, iOS). Avantage : les captures de deux systèmes très répandus. Inconvénient : seules des sources de témoignages, pas une documentation d'Apple ; à écrire dans les limites de la règle.
- **Dimensions typiques** : un nouveau module lit les dimensions réelles et compte les blocs de métadonnées ; une règle relève un JPEG sans métadonnées dont le côté long est dans une liste datée. Avantage : le cas le plus fréquent, une image reçue par une messagerie, qui ne porte plus aucune marque. Inconvénients : un nouveau module ; des tailles qui changent sans prévenir.
- **Recompression (avancer T40)** : reconnaître les tables de quantification. Avantage : F-06 nomme la recompression. Inconvénient : une partie de T40 avancée ; une seule lecture ne mesure pas une double compression (T41).

Seconde question, si les dimensions sont retenues : quelle liste de tailles ?

- **Liste sourcée et datée** : les tailles des articles trouvés, chacune avec son article et son année, dans le catalogue (A-32). Avantage : F-06 réalisée ; mise à jour sans nouvelle version de l'outil (F-26). Inconvénient : des tailles de 2016 et 2020.
- **Observer sans règle** : dimensions observées, aucune règle avant la mesure du corpus (T100). Avantage : rien d'affirmé sans mesure. Inconvénient : F-06 resterait partielle.

## Décision

Les quatre familles, et la liste sourcée et datée.

| Famille | Règles | Source |
| --- | --- | --- |
| Capture d'écran d'Apple | `R-EXIF-014` (`exif.exif.UserComment`), `R-XMP-013` (`xmp.exif:UserComment`) : égal à `Screenshot` | Témoignages, communauté d'Apple, fil 255854599 (lu le 2026-11-13) |
| Capture d'écran de GNOME | `R-TEXTEPNG-007` (`textepng.Software`) : égal à `gnome-screenshot` | gnome-screenshot, `src/screenshot-application.c`, option `tEXt::Software` (commit `4e03093f`, 2012, archive `commits-list` de GNOME, lue le 2026-11-14) |
| Marque de Facebook | `R-IPTC-003` (`iptc.SpecialInstructions`) : motif `^FBMD` | IPTC, « IPTC investigates: what does Facebook do with your photo metadata? », 22 juillet 2019 (lu le 2026-11-14) |
| Dimensions d'une messagerie | `R-IMAGE-001` à `R-IMAGE-003` : JPEG, aucun bloc de métadonnées, côté long parmi 960, 1 080, 1 280, 1 600, 2 048, 2 560 (paysage, portrait, carré) | Giudice et al., arXiv:1610.06347, 2016, tableau III ; Bertini et al., arXiv:2006.03903, 2020, tableau 1 (lus le 2026-11-13) |
| Recompression | `R-IMAGE-004` : JPEG, aucun bloc de métadonnées, tables de libjpeg à une qualité reconnue | Annexe K de T.81 et `jcparam.c` de libjpeg ; recompression systématique des plateformes : Giudice et al. 2016, tableau III |

Tailles, par source :

| Côté long | Giudice et al. 2016 | Bertini et al. 2020 |
| --- | --- | --- |
| 960 | Facebook (basse qualité) | — |
| 1 080 | Instagram | Instagram |
| 1 280 | Tumblr | Telegram, Tumblr, Viber, WeChat |
| 1 600 | WhatsApp, Tinypic | WhatsApp |
| 2 048 | Facebook (haute qualité), Twitter, Google+ | Facebook, Flickr, Google+, LinkedIn, Pinterest, Twitter |
| 2 560 | Telegram | VK |

Bertini et al. notent quatre écarts à leur tableau : de grandes images d'Instagram, Pinterest, Tumblr et WhatsApp ramenées à 1 350 × 1 080, 2 064 × 1 161, 1 920 × 1 080 et 1 600 × 900 ; seules les tailles des tableaux sont retenues, la dernière ayant déjà son côté long dans la liste.

La forme exacte de chaque règle, le module qui lit les dimensions et les tables, et ce qui est écarté sont dans [ADR-0154](ADR-0154-module-image.md) ; leur nature dans [ADR-0155](ADR-0155-nature-d-un-indice-de-transfert.md).

## Raisons

- Les quatre familles retenues par TheDarkMac, sur recommandation de l'assistant pour les trois premières ; la recompression ajoutée par TheDarkMac, que l'assistant recommandait de laisser à T40 et T41. La règle retenue ne lit que les tables de libjpeg et ne mesure aucune double compression : T40 garde la comparaison à d'autres tables connues, T41 la double compression.
- Liste sourcée et datée retenue par TheDarkMac, sur recommandation de l'assistant : F-06 réalisée, la liste au catalogue (A-32), ses limites écrites dans chaque règle.
- « Observer sans règle » écartée : F-06 resterait partielle alors que les sources existent, même datées.

## Conséquences

- F-06 est réalisée dans les limites écrites dans chaque règle ; F-30 devient partielle (tables de libjpeg seules).
- Une taille, une marque ou un outil de capture s'ajoutent au catalogue sans nouvelle version de l'outil (F-26) ; une nouvelle étude, ou la mesure sur le corpus (T100), peut changer la liste.
- Les règles d'absence de T23 restent des informations neutres (F-14) ; les règles de dimensions et de tables les citent dans leur description (A-34) et lisent leur propre compte des métadonnées.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création |
