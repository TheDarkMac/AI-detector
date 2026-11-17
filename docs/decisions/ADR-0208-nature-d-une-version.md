# ADR-0208 — Nature d'une version : objets changés comparés entrée par entrée, rangés par leur type et ce qui les désigne

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T50, validée pendant la revue de la PR
- **Tâche** : T50
- **Exigences liées** : F-60, F-61, F-82, NF-14, ES-03 ; ADR-0125, ADR-0207

## Contexte

F-60 demande de distinguer les ajouts légitimes : linéarisation (ADR-0207), signature électronique, formulaire rempli. La norme prévoit d'autres ajouts sans changement du contenu affiché : annotations, métadonnées, informations de validation à long terme d'une signature (DSS, horodatage du document). Les droits d'une signature de certification (DocMDP, §12.8.2.2) classent les changements permis en trois niveaux : aucun ; formulaire et signatures ; formulaire, signatures et annotations. T51 décrira les objets ajoutés ou remplacés un par un (F-61) : T50 n'en tire que la nature de chaque version.

## Options envisagées

### Option A — Classement par type et par désignation (proposée)

1. Les entrées d'une version sont comparées à la version précédente : un objet est ajouté (aucune entrée en usage avant), remplacé (entrée en usage différente), supprimé (entrée libre, en usage avant) ; une entrée redite à l'identique ne change rien.
2. Chaque objet changé est rangé d'après son type : dictionnaire de signature, d'horodatage ou DSS, champ ou widget de signature → **signature** ; champ (`/FT`, ou `/T` avec `/Kids` ou `/Parent`) et widget → **formulaire** ; autre annotation (`/Type /Annot`, ou un `/Subtype` nommé avec `/Rect`) → **annotation** ; dictionnaire Info du trailer, flux `/Type /Metadata` → **métadonnées** ; section en flux, flux d'objets, objet nul → structure.
3. Le catalogue est comparé clé par clé à celui de la version précédente : `AcroForm` → formulaire, `DSS` et `Perms` → signature, `Metadata` → métadonnées, `Version` et `Extensions` → structure ; toute autre clé → **non reconnue**. Les objets changés que désignent ces clés en prennent la nature.
4. Une page remplacée dont seule la clé `/Annots` change prend la nature des annotations ajoutées (formulaire ou signature si elles le sont toutes, annotation sinon) ; une page ajoutée, supprimée ou changée ailleurs, un nœud de l'arbre des pages changé → non reconnue.
5. Un tableau indirect dont chaque élément est une annotation ou un champ (`/Annots`, `/Fields`) en prend la nature (4 096 éléments au plus examinés).
6. Les objets changés que désigne un objet d'une nature permise en prennent la nature, de proche en proche : apparences, polices et images d'une annotation, certificats d'un DSS.
7. Un objet ajouté qu'aucun objet changé ne désigne est cherché depuis le catalogue et le dictionnaire Info de la version (65 536 objets au plus) : introuvable, il ne change rien de ce qu'elle affiche et compte comme structure ; trouvé, il reste non reconnu ; parcours borné ou interrompu par un objet illisible, il est non lu.
8. Tout autre objet changé → **non reconnue** ; un objet qui ne se lit pas → **non lue**, et l'analyse non menée le dit.

La nature d'une version est la liste des natures de ses objets, structure exceptée (« structure » si elle ne change que des objets de structure) ; la première version est « originale ».

- Avantages : prudente : ce qui n'est pas reconnu est dit tel ; vérifiable sur les objets cités par le rapport ; coût borné.
- Inconvénients : un ajout légitime d'un type non prévu (nouvelle clé du catalogue écrite par un logiciel) est non reconnu ; une apparence d'annotation ou de formulaire qui recouvre le contenu n'est pas vue.

### Option B — Règles par champ, à la manière de pyHanko

Comparer chaque objet changé avec son ancienne valeur, clé par clé, selon des règles écrites par type de champ, et vérifier les droits DocMDP.

- Avantages : plus fin ; détecte un remplissage de champ interdit par le signataire.
- Inconvénients : beaucoup plus de code et de cas ; pyHanko 0.38.1, avec sa politique par défaut, range lui-même l'ajout d'une annotation de texte parmi les modifications « OTHER » (vérifié sur `signe_annote.pdf`) : même une implémentation mûre ne couvre pas tout.

### Option C — Compter les objets, sans les ranger

- Avantages : aucun classement contestable.
- Inconvénients : ne répond pas à F-60, qui demande de distinguer les ajouts légitimes.

## Décision

Option A.

## Raisons

- A : répond à F-60 avec un classement que le rapport peut expliquer (P-02), et qui dit « non reconnue » plutôt que de deviner (NF-14).
- B écartée pour T50 : coût sans proportion avec l'indice faible qu'elle alimente (ADR-0211) ; la comparaison des droits DocMDP aux changements reste possible plus tard (observation `revisionspdf.docmdp`, ADR-0209).
- C écartée : ne répond pas à l'exigence.
- Points 6 et 7 ajoutés après les premiers essais : pyHanko écrit une apparence vide qu'il ne désigne plus, et range les polices d'une apparence dans des objets à part ; sans eux, chaque signature serait non reconnue.

## Conséquences

- Observations : `revisionspdf.natures`, `revisionspdf.ajoutes`, `revisionspdf.remplaces`, `revisionspdf.supprimes` (une valeur par version), `revisionspdf.versions_non_reconnues`.
- Vérifié sur les échantillons de `tests/donnees/revisions` (Ghostscript, LibreOffice, exiftool, pyHanko) : champs ajoutés, formulaire rempli, champ de signature, signature d'approbation et de certification, annotation, métadonnées, linéarisation sont reconnus ; un flux de contenu ajouté à une page est non reconnu.
- Limites dites par la fiche et par les règles : attaques « par ombre » (Mainka, Mladenov et Rohlmann, NDSS 2021), qui préparent dans la version signée un contenu caché qu'une mise à jour d'apparence révèle ; document préparé pour qu'un objet ancien désigne un numéro encore libre (point 7 : trouvé, il reste non reconnu).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création, statut « Proposé » |
| 2026-11-16 | Validé par TheDarkMac pendant la revue de la PR (« Oui, valide les deux ») : statut « Accepté » |
| 2026-11-17 | Renvoi : objets changés décrits un par un, avec leur nature, dans le tableau `objets_revisions` (T51, ADR-0217) ; une apparence d'annotation qui recouvre le contenu est désormais relevée par `pagespdf` (ADR-0214) |
