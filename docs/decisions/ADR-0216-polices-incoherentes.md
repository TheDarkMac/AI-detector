# ADR-0216 — Polices incohérentes : même police en plusieurs incorporations sur une page, codes hors de la plage déclarée

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (clés de comparaison précisées par l'assistant)
- **Tâche** : T51
- **Exigences liées** : F-61, P-02 ; ADR-0213, ADR-0215

## Contexte

« Polices incohérentes » (F-61) : un texte ajouté par un autre outil que celui qui a écrit la page emploie souvent la même police que le texte voisin, mais incorporée autrement (un autre sous-ensemble, ou pas incorporée du tout) ; ou bien il réemploie la police de la page, dont le sous-ensemble ne contient que les caractères du texte d'origine. Un sous-ensemble porte un préfixe de six capitales (`ABCDEF+Arial`, §9.9.2) et une police simple déclare la plage de ses codes (`/FirstChar`, `/LastChar`).

## Options envisagées

### Option A — Familles et codes (recommandée)

Une même police employée sur une page par plusieurs polices d'incorporation différente (sous-ensembles distincts, incorporée et non incorporée, TrueType et CFF) ; et des codes dessinés hors de la plage que la police déclare.

- Avantages : les deux traces d'un texte ajouté ; aucune lecture du programme des polices.
- Inconvénients : un document fusionné, ou un logiciel qui découpe une police en plusieurs sous-ensembles, déclenche la première.

### Option B — Codes hors plage seuls

- Avantages : presque aucune cause ordinaire.
- Inconvénients : un texte ajouté avec sa propre police n'est pas vu.

### Option C — Familles seules

- Avantages : voit le texte ajouté avec sa propre police.
- Inconvénients : ne voit pas le réemploi de la police de la page.

## Décision

Option A. Précisions de l'assistant :

- **Nom d'une police** : son `/BaseFont`, sans le préfixe d'un sous-ensemble (six capitales A à Z suivies de `+`) ; 64 caractères au plus. Les polices Type3 et sans nom ne sont pas comparées.
- **Incorporation** : le couple (préfixe, programme) : préfixe vide ou non, programme `FontFile`, `FontFile2`, `FontFile3` ou aucun (pour une police composite, celui de sa descendante). Une page sur laquelle un même nom peint du texte visible sous au moins deux couples compte ce nom une fois. Deux objets de même nom et de même couple ne comptent pas (un logiciel peut écrire deux fois la même police).
- **Codes hors plage** : pour une police simple qui déclare ses largeurs, chaque code de texte visible hors de `/FirstChar` à `/LastChar` (à défaut de `/LastChar`, la fin des largeurs) ; les polices composites, dont un code absent des largeurs prend `/DW` comme la norme le permet, ne sont pas lues ici.
- Le texte invisible ne compte ni pour l'une ni pour l'autre.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- B écartée : laisse passer l'ajout d'un texte dans sa propre police, le cas d'un outil qui fusionne une page.
- C écartée : laisse passer le réemploi d'un sous-ensemble, le cas d'un éditeur qui écrit avec la police de la page.

## Conséquences

- Règles R-PAGESPDF-003 et R-PAGESPDF-004 (ADR-0218).
- Les documents fusionnés et les sous-ensembles multiples déclencheront R-PAGESPDF-003 ; la mesure sur le corpus (T100) dira à quelle fréquence.
- Un glyphe absent du programme incorporé, mais dans la plage déclarée, n'est pas vu : il faudrait lire les programmes TrueType et CFF.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T51 |
