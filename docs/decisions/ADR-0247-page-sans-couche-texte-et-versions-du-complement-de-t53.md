# ADR-0247 — Page sans couche texte native : raison `document_numerise` ; versions du complément de T53

- **Statut** : Accepté
- **Date** : 2026-11-19
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (définition de la page, forme de la non menée et versions précisées par l'assistant)
- **Tâche** : T53 (complément texte)
- **Exigences liées** : F-63, F-82, F-25 ; ADR-0017, ADR-0056, ADR-0060, ADR-0152, ADR-0223

## Contexte

ADR-0017 exclut la lecture des documents numérisés et veut qu'« une page PDF sans couche texte native donne une analyse non menée (F-82), avec cette raison » ; ADR-0223 a renvoyé au complément de T53 de dire ce qu'elle devient. Les raisons d'une analyse non menée forment une liste fermée (ADR-0056) ; un module ne peut en donner que quatre (`format_partiel`, `fichier_tronque`, `reference_manquante`, `reseau_desactive`), dont aucune ne dit qu'une page n'est pas lue parce que la lecture des documents numérisés est exclue.

## Options envisagées

### Option A — Nouvelle raison `document_numerise` (recommandée)

Une raison de la liste fermée, qu'un module peut donner, propre à une technique : « Page sans couche texte native, non lue : la lecture des documents numérisés est exclue. » Schémas 0.12.0.

- Avantages : le rapport dit exactement ce qui n'a pas été fait, et pourquoi.
- Inconvénients : changement des schémas du rapport et des messages.

### Option B — `format_partiel`, localisé

`format_partiel`, localisé « page N (sans couche texte native) ».

- Avantages : aucun changement de schéma.
- Inconvénients : la raison dit qu'une portion du fichier n'a pas su être lue, ce qui n'est pas le cas.

### Option C — Une observation seule

Compter et lister les pages sans texte, sans analyse non menée ; ADR-0017 modifié.

- Avantages : le plus simple.
- Inconvénients : le rapport ne dirait pas, à la couverture, qu'une partie du texte n'est pas analysée.

## Décision

Option A. Précisions de l'assistant :

- Est sans couche texte native une page dont le contenu et ses formes peignent au moins une image (`Do` d'une image, image en ligne) sans montrer aucun code, ni visible, ni invisible. Une page blanche, ou de dessins sans image, ne l'est pas ; l'apparence d'une annotation ne compte ni pour les codes ni pour les images.
- Une analyse non menée par document, s'il a de telles pages, localisée « page(s) sans couche texte native : 2, 5, … » (seize numéros au plus, puis « … ») ; observations `caracteres.pages_sans_texte` (nombre) et `caracteres.pages_sans_texte.pages` (liste). Ses images restent analysées par les modules d'image (ADR-0225).
- `document_numerise` est propre à une technique : la non menée nomme son module (`RAISONS_PROPRES_A_UNE_TECHNIQUE`, schéma du rapport) ; elle n'interrompt pas l'analyse.

| Élément | Version |
| --- | --- |
| Module `caracteres` | 0.3.0 : format `pdf` ajouté ; exigence F-63 ; bibliothèque `expat` inchangée ; direction inchangée |
| Module `pagespdf` | 0.1.0 inchangée : sa lecture des polices est déplacée dans `_lecture/polices.py`, sans changement (ADR-0243) |
| Catalogue | 0.18.0 (`Y` : règle ajoutée, ADR-0152), format 3 inchangé ; R-CARACTERES-014 ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.12.0 (`Y` : valeur ajoutée à une liste fermée) : raison `document_numerise` |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : une raison qui dit autre chose que ce qui s'est passé.
- Option C écartée : la couverture tairait une partie du texte non analysée, ce que F-82 interdit.
- Une non menée par document plutôt que par page : un document numérisé de cinq cents pages n'en fait pas cinq cents.

## Conséquences

- Un rapport 0.12.0 peut porter la raison `document_numerise` ; un lecteur qui ne connaît que 0.11.0 la refuse.
- Une page d'image qui porte du texte, même invisible (la couche d'un logiciel de reconnaissance), n'est pas sans couche texte : elle est lue, et R-CARACTERES-014 le dit (ADR-0245).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-19 | Création ; option choisie par TheDarkMac au début du complément de T53, dans une seconde question |
