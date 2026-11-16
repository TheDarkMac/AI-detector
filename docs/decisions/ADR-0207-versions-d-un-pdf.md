# ADR-0207 — Versions d'un PDF : sections de la chaîne regroupées, fin par la marque `%%EOF`, reconstitution par la plage

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T50, validée pendant la revue de la PR
- **Tâche** : T50
- **Exigences liées** : F-60, F-82, NF-06, ES-03, ES-15 ; ADR-0124, ADR-0125

## Contexte

Une mise à jour incrémentale (ISO 32000-2, §7.5.6) ajoute à la fin du fichier les objets qu'elle change, une section de références croisées dont `/Prev` désigne la précédente, puis `startxref` et `%%EOF`. Le fichier garde donc chacune de ses versions, et la version *k* en est le début, jusqu'à sa marque `%%EOF`. F-60 demande de reconstituer ces versions. Deux cas font plusieurs sections d'une seule écriture : la linéarisation (annexe F), dont la table de la première page, au début du fichier, désigne par `/Prev` la table principale, à la fin ; un fichier hybride, dont la table classique est complétée par un flux (`/XRefStm`, §7.5.8.4). Le lecteur du projet suit déjà la chaîne depuis le dernier `startxref` (ADR-0124), sans rien reconstruire (ADR-0125).

Vérifié sur un PDF linéarisé par Ghostscript 10.05.1 (`-dFastWebView`) puis mis à jour par exiftool 13.25 : le dernier `startxref` désigne la table de la première page, dont `/Prev` désigne la table principale ; le `/Prev` de la mise à jour désigne la table de la première page.

## Options envisagées

### Option A — Les sections de la chaîne, regroupées (proposée)

- Une version par section de la chaîne `/Prev`, de la plus ancienne à la plus récente. Les deux sections les plus anciennes ne font qu'une version si le premier objet du fichier est un dictionnaire de linéarisation (`/Linearized`), que la plus récente des deux précède l'autre dans le fichier et que son `/Prev` la désigne. Une section en flux qui complète une table (`/XRefStm`) appartient à la version de la table.
- Fin d'une version : après le `%%EOF` qui suit le `startxref` de sa section, et sa fin de ligne (CR, LF ou CR LF) ; des blancs, des commentaires et `endobj` sont permis avant `startxref`. Sans cette marque, la fin du trailer ou de l'objet flux, et l'observation `revisionspdf.sans_marque_de_fin`. La linéarisation prend la plus grande des fins de ses deux sections.
- Reconstitution : la fin de chaque version au rapport (observation `revisionspdf.fins`, colonne « Fin » de la chronologie, ADR-0212). Les premiers octets du fichier jusqu'à cette fin sont la version.
- Avantages : la structure déclarée, rien de deviné (ADR-0125) ; la reconstitution tient en un nombre que l'utilisateur vérifie avec n'importe quel outil (`head -c`) ; aucun fichier écrit.
- Inconvénients : des sections hors de la chaîne (une mise à jour dont le `/Prev` a été coupé, des données ajoutées sans section) ne sont pas vues comme des versions.

### Option B — Chercher les marques dans tout le fichier

Compter les `%%EOF`, `xref` et `startxref` du fichier, comme le font certains outils d'expertise.

- Avantages : voit aussi les sections que la chaîne ne désigne plus.
- Inconvénients : une heuristique : ces mots peuvent se trouver dans un flux ou une chaîne, et la linéarisation y laisse deux marques ; contraire à la lecture stricte (ADR-0125).

### Option C — Écrire chaque version dans un fichier

Une option de la ligne de commande écrirait les versions à côté du rapport.

- Avantages : l'utilisateur ouvre directement chaque version.
- Inconvénients : écrire le contenu d'un fichier suspect sur le poste, au-delà du rapport (ES-15) ; une interface de plus, alors que la plage suffit.

## Décision

Option A.

## Raisons

- A : ce qui est observé est ce que la structure déclare (P-02) ; la plage reconstitue chaque version sans rien écrire.
- B écartée : heuristique et contraire à ADR-0125. Pour en garder ce qui est vérifiable, les octets qui suivent la fin de la dernière version sont observés (`revisionspdf.octets_apres_fin`).
- C écartée : la plage suffit, et l'outil n'écrit que son rapport (ES-15). Une extraction pourra être reprise par un nouvel ADR si le besoin est exprimé (T105).
- Linéarisation : la linéarisation écrit ses deux sections en une fois ; les compter comme deux versions ferait croire à une mise à jour. pyHanko 0.38.1, pris pour oracle, les compte comme deux révisions : l'écart est attendu et vérifié par les tests.

## Conséquences

- Le lecteur PDF expose la chaîne (`Document.chaine`, une `Section` par section : position, forme, trailer, fin, marque, complément en flux), les entrées que déclare une section (`Document.entrees`), une vue du document à une section (`Document.vue`) et le premier objet du fichier (`Document.premier_objet`).
- Énumérer les entrées d'une section compte une entrée par objet parcouru (ES-03).
- Observations : `revisionspdf.versions`, `revisionspdf.sections`, `revisionspdf.linearise`, `revisionspdf.linearisation.longueur` (la clé `/L`, longueur du fichier linéarisé), `revisionspdf.fins`, `revisionspdf.sans_marque_de_fin`, `revisionspdf.octets_apres_fin`. Les listes ont une valeur par version et sont coupées comme les autres listes du projet, leur longueur entière observée à part.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création, statut « Proposé » |
| 2026-11-16 | Validé par TheDarkMac pendant la revue de la PR (« Oui, valide les deux ») : statut « Accepté » |
