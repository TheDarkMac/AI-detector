# ADR-0189 — Estimation : calcul en entiers, région du haut de l'image, paramètres et forme de la règle

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T41, validée pendant la revue de la PR de T41
- **Tâche** : T41
- **Exigences liées** : F-31, NF-02, NF-06, ES-03 ; ADR-0018, ADR-0023, ADR-0076, ADR-0078, ADR-0108, ADR-0186, ADR-0188

## Contexte

La méthode (ADR-0186) et le constat (ADR-0188) laissent à fixer : comment calculer sans que le résultat dépende de la machine (NF-06, comparé entre systèmes par la CI, ADR-0108) ; combien de l'image décoder dans le délai (ADR-0076) ; les paramètres de l'estimation ; la forme de la règle.

## Options envisagées

### Calcul

- **A — Entiers de 64 bits** : cosinus en virgule fixe (2^12, écrits en entiers), produits matriciels d'entiers (numpy n'y emploie pas BLAS), quantifications arrondies la moitié loin de zéro comme libjpeg (`jcdctmgr.c`), écarts comparés en fractions exactes.
- **B — Flottants** : plus simple ; mais l'ordre des sommes et les instructions vectorielles varient selon le processeur et la bibliothèque BLAS, et un arrondi qui bascule près d'une demi-unité peut changer un histogramme, donc un compte de traces.

### Étendue décodée

- **A — Région du haut, bornée** : au plus 32 768 blocs de la première composante (environ 2,1 Mpx) et 262 144 blocs décodés en tout ; nombre de lignes calculé sur les balayages annoncés, avant le décodage, réduit d'un quart tant que le budget est dépassé ; format partiel si une seule ligne le dépasse encore.
- **B — Image entière** : jusqu'à environ 60 s pour une image de 24 Mpx très détaillée, en Python pur.

### Forme de la règle

- **A — Une règle, seuil au catalogue** : le module observe le nombre de fréquences tracées ; la règle `R-DOUBLEJPEG-001` porte le seuil (au moins 4), en test `seuil`. La qualité antérieure est une observation, pas un paramètre de la phrase.
- **B — Deux règles** (avec et sans qualité antérieure) : sans négation dans le langage des règles, les deux se déclencheraient ensemble.
- **C — Règle « module »** : le seuil serait dans le code, contre ADR-0018 (« seuils dans le catalogue »).

## Décision

Option A dans les trois cas, avec ces paramètres, dans le code du module et dans la fiche `double-compression-jpeg` :

| Paramètre | Valeur | Raison |
| --- | --- | --- |
| Fréquences | 9 premières après le continu, ordre en zigzag | Les pas y sont petits et les coefficients nombreux |
| Non nuls au moins | 256 par fréquence | En deçà, l'histogramme est trop pauvre (essais sur 4 096 blocs) |
| Pas antérieurs essayés | 1 à min(255, 4 q2 + 16) | Couvre, aux premières fréquences, une première qualité de libjpeg jusqu'à environ 25 pour une seconde à 90 |
| Borne de l'histogramme | Plus petite de 8 à 128 qui contient 99,5 % des valeurs | Les grandes valeurs sont trop rares pour être comparées (l'article recommande 15 q2) |
| Rapport des écarts | 4 | Sur les essais, une image compressée une fois ne dépasse ce rapport qu'à 2 fréquences au plus, des images de synthèse surtout |
| Seuil de la règle | 4 traces | Images compressées une fois : 2 au plus sur les essais |
| Qualité antérieure | À partir de 3 traces, tables de luminance de libjpeg en huit bits | Avec moins de pas, trop de qualités conviennent |
| Recadrage | 4 pixels | Article, §4.1 |

## Raisons

- Calcul A : seul moyen de garantir des rapports identiques entre machines ; B écartée pour le risque de non-reproductibilité, que la CI de T18 relèverait.
- Étendue A : le temps reste borné (9 s pour un bruit aléatoire de 12 Mpx en qualité 100, cas défavorable mesuré ; 1 à 2 s pour une image courante), et 32 768 blocs suffisent aux histogrammes ; B écartée pour le délai. La région du haut est arbitraire mais fixe, et le dire suffit (limite du catalogue).
- Règle A : le seuil se change dans le catalogue sans nouvelle version de l'outil ; B écartée pour le double constat ; C pour ADR-0018.
- Paramètres : fixés à la main sur les essais de T41 (journal) ; à recalibrer sur le corpus (T100).

## Conséquences

- Bornes propres au lecteur : 32 768 blocs de région, 262 144 blocs décodés, 64 balayages, 256 tables de Huffman ; chaque bloc décodé compte un objet du budget (ADR-0078).
- La luminance recalculée diffère de celle de djpeg (IDCT en flottants) d'un niveau sur environ 2 % des pixels : sans effet sur l'estimation, vérifié par les tests.
- Une analyse partielle de l'image n'est pas signalée comme non menée : `doublejpeg.blocs` et `doublejpeg.blocs_image` disent la part examinée.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création, statut « Proposé » |
| 2026-11-15 | Validé par TheDarkMac pendant la revue de la PR de T41 (« Oui, les deux ») : statut « Accepté » |
