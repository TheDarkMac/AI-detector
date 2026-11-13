# ADR-0138 — Relations et références des documents bureautiques ni lues ni suivies

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21 (complément bureautique)
- **Exigences liées** : ES-06, ES-13, F-10 ; menace M-14 ; ADR-0033

## Contexte

Un DOCX peut désigner des ressources hors de l'archive : un modèle distant (relation `attachedTemplate` en `TargetMode="External"`, procédé connu de balise de pistage ou de chargement de contenu, M-14), des liens, des images liées ; ses propriétés étendues portent une liste des liens du document (`HLinks`). Un ODT désigne son modèle et une adresse de rechargement par des attributs `xlink:href` de ses métadonnées. ADR-0033 demande que les liens et références distantes des DOCX et ODT ne soient jamais suivis (T21 et T52) ; ES-06 interdit de résoudre une URL issue du fichier. Restait à dire si ces cibles figurent au rapport.

## Options envisagées

### Option A — Ni lues ni suivies, garantie testée

Seules les relations vers les parties de propriétés sont lues, et suivies à l'intérieur de l'archive ; toute autre relation, toute liste de liens et tout attribut `xlink` sont ignorés.

- Avantages : ce complément reste dans F-10 (les propriétés) ; aucune adresse ne figure au rapport, donc aucune n'est à marquer ni à masquer ; la garantie d'ES-06 tient par construction, et un test la vérifie sur un DOCX à modèle distant.
- Inconvénients : un modèle distant n'est pas signalé au rapport.

### Option B — Cibles externes observées, jamais suivies

- Avantages : le modèle distant d'un DOCX, signe d'un fichier piégé, serait visible.
- Inconvénients : sort des propriétés de F-10 vers la structure du document (T52, T81) ; une adresse ou un chemin local au rapport demande son propre marquage des données identifiantes (ES-13).

## Décision

Option A :

- `ooxml` lit les seules relations du paquet (`_rels/.rels`) dont le type désigne une partie de propriétés ; une telle relation externe, sans cible ou en double n'est pas suivie, et elle est non menée (format partiel) avec un chemin qui ne porte pas sa cible ;
- `ooxml` ne lit pas `HLinks` ; `odf` ne lit aucun attribut de l'espace `xlink` ;
- aucun module n'ouvre de connexion, ni ne lit de fichier hors de celui qu'on lui confie (le processus de travail en est de toute façon empêché, ADR-0083).

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : hors de F-10, et une donnée identifiante de plus à marquer ; le signalement d'un modèle distant revient à l'analyse de la structure du document (T52, T81).
- `HyperlinkBase` (propriété étendue) reste lu : c'est une propriété déclarée, jamais résolue, marquée nom de fichier (ADR-0140).

## Conséquences

- ES-06 devient partielle dans la matrice : réalisée pour DOCX et ODT, à venir pour C2PA (T30) et PDF (T52).
- Un test vérifie, sur un DOCX à modèle distant et relation de propriétés externe, et sur un ODT à modèle `xlink`, qu'aucune adresse n'est au rapport et qu'aucune connexion n'est tentée.
- Signaler un modèle distant demandera un nouvel ADR (T52 ou T81).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création ; option choisie par TheDarkMac au début du complément |
