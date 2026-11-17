# ADR-0223 — Périmètre de T53 : images d'un PDF et leur acheminement ; couche texte renvoyée à un complément après T80

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T53
- **Exigences liées** : F-63 ; ADR-0017, ADR-0042, ADR-0061, ADR-0123, ADR-0147

## Contexte

F-63 demande l'« extraction des images et de la couche texte native, puis analyse par les modules image et texte » ; ADR-0017 en a exclu la lecture des documents numérisés. ADR-0042 et l'architecture (§7, §12) confient à T53 l'acheminement des résultats d'un module vers un autre, dans le même processus de travail ; ADR-0061 et ADR-0147 lui renvoient aussi le constat qui cite les observations d'un autre module.

Au début de T53, des modules d'image existent (métadonnées, C2PA, tables de quantification, double compression, ELA, filigrane dwtDct) ; aucun module texte n'existe : T80 (caractères invisibles et homoglyphes) vient après T53 dans l'ordre de la V1 (ADR-0012). Aucune règle du catalogue ne compare encore les observations de deux modules.

## Options envisagées

### Option A — Images et acheminement ; couche texte dans un complément de T53 après T80 (recommandée)

T53 livre le mécanisme d'acheminement et les images d'un PDF. La couche texte (texte en Unicode par `/ToUnicode`, les encodages standard et la liste de glyphes d'Adobe) est renvoyée à un complément de T53, fait après T80, quand un module texte pourra la recevoir, comme T21 et T40 ont eu les leurs (ADR-0123, ADR-0180). Le constat qui cite les observations d'un autre module n'est pas fait : aucune règle ne le demande.

- Avantages : une PR relisible ; le texte extrait a un module pour le lire dès qu'il existe ; ADR-0061 n'est élargi que quand une règle en aura besoin.
- Inconvénients : F-63 n'est réalisée qu'en partie jusqu'au complément.

### Option B — Images et texte dans T53

Le texte est extrait, observé par page, et acheminé vers le format « texte » sans module pour le lire avant T80.

- Avantages : F-63 couverte d'un coup.
- Inconvénients : un texte extrait que rien n'analyse ; décodage des polices (CMap, encodages, glyphes) écrit et testé sans le module qui en dira les besoins (caractères invisibles, homoglyphes).

### Option C — Images dans T53, texte dans T80

- Avantages : pas de complément.
- Inconvénients : T80 mélangerait deux sujets, l'extraction d'un PDF et les caractères invisibles (découpage, §1).

## Décision

Option A : T53 achemine les images d'un PDF vers les modules d'image ; la couche texte native est renvoyée à un complément de T53, fait après T80 ; ADR-0061 reste inchangé.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : l'extraction du texte serait écrite sans le module qui la lira.
- Option C écartée : une tâche, un sujet (découpage, §1).

## Conséquences

- F-63 est réalisée pour les images ; la matrice le dit et nomme le complément pour le texte.
- Le complément de T53 dira ce que devient une page sans couche texte native : analyse non menée, avec sa raison (ADR-0017).
- Le constat qui cite les observations de deux modules (date d'un PDF contre date EXIF d'une image qu'il contient, par exemple) reste ouvert à l'architecture (§12), pour la tâche qui en écrira la première règle.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T53 |
