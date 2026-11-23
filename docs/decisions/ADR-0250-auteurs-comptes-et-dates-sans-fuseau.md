# ADR-0250 — Auteurs des modifications et des commentaires comptés, non lus ; leurs dates lues sans fuseau

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (dates précisées par l'assistant)
- **Tâche** : T81
- **Exigences liées** : F-71, ES-13 ; ADR-0057, ADR-0140, ADR-0148, ADR-0158, ADR-0240

## Contexte

Chaque modification suivie et chaque commentaire porte le nom de son auteur (`w:author`, `dc:creator`) et une date (`w:date`, `dc:date`). Les auteurs sont des tiers, souvent des relecteurs, et non l'auteur du document, que les modules `ooxml` et `odf` lisent déjà, marqué `metadonnee_nominative` (ADR-0140). ADR-0240 a laissé à T81 la lecture des auteurs et des dates.

Pour les dates, l'assistant a vérifié que Word écrit dans un DOCX l'heure locale suivie de `Z` et la relit comme une heure locale ([MS-OI29500, §2.1.313](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/2f42e7a6-a014-4392-8461-53a493241d28)), et que LibreOffice fait de même ([bogue 134589](https://www.libreoffice.org/bugzilla/show_bug.cgi?id=134589)) ; dans un ODT, LibreOffice l'écrit sans fuseau. LibreOffice écrit aussi une date nulle (`0-00-00T00:00:00Z` dans un DOCX, `0000-00-00T00:00:00` dans un ODT) pour un commentaire sans date.

## Options envisagées

### Option A — Comptés, non lus (recommandée)

Le rapport dit combien d'auteurs distincts ont laissé des modifications ou des commentaires, sans leurs noms ; les dates sont gardées pour une comparaison.

- Avantages : moins de données identifiantes au rapport (ES-13) ; le vérificateur voit les noms en ouvrant le document.
- Inconvénients : le rapport ne dit pas qui a relu.

### Option B — Noms observés et marqués

Comme `dc:creator` : noms observés, marqués `metadonnee_nominative`, masqués par défaut et comptés par le contrôle avant publication.

- Avantages : plus complet.
- Inconvénients : une liste de tiers au rapport, que le contrôle avant publication devrait suivre.

## Décision

Option A. Précisions de l'assistant :

- Un auteur se compte par le nom écrit, espaces autour ôtés, avec sa casse ; un nom vide ne compte pas. Les auteurs des modifications et ceux des commentaires sont comptés à part.
- Aucun nom n'est observé ; le module ne lit aucune métadonnée identifiante, et rejoint les modules sans métadonnées du résumé (ADR-0158).
- Les dates des modifications et des commentaires sont lues sans leur fuseau (`Z`, `±hh:mm`, `±hhmm`, `±hh`), donc dans tous ceux de UTC-12 à UTC+14 (ADR-0148) ; une date qui ne suit pas l'écriture ISO 8601, dont la date nulle de LibreOffice, n'est pas lue. Elles ne servent qu'à compter celles qui suivent certainement le dernier enregistrement du document ; elles ne sont pas observées.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : des noms de tiers au rapport, pour un apport que l'ouverture du document donne déjà.
- Dates sans fuseau : lire le `Z` d'une heure locale ferait naître des incohérences de quelques heures sur tout document écrit hors de UTC.

## Conséquences

- Un même relecteur écrit sous deux noms compte pour deux ; l'inspecteur de document de Word, qui retire auteurs et dates, fait compter zéro auteur.
- Une modification n'est dite postérieure au dernier enregistrement que plus de 14 heures après lui, ou 26 si sa date n'a pas de fuseau.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-23 | Création ; option choisie par TheDarkMac au début de T81 |
