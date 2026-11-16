# ADR-0194 — Tables d'appareils : une seule marque, jamais sur Photoshop, appareils adaptatifs exclus, une règle par marque

- **Statut** : Accepté
- **Date** : 2026-11-16
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : complément de T40
- **Exigences liées** : F-30 ; ADR-0191, ADR-0193

## Contexte

Certains appareils semblent calculer leurs tables pour chaque image : sur le relevé, les fichiers de 28 modèles n'ont presque jamais les mêmes tables. Le relevé (ADR-0193) a montré trois autres choses : les tables d'appareils sont communes à des familles entières (un même jeu sur 31 compacts Canon) ; beaucoup d'empreintes se trouvent sur plusieurs marques (Nikon et Panasonic, par exemple), ou sur quelques fichiers d'autres logiciels (GIMP, Picasa, la visionneuse de Windows, qui peuvent garder les tables de l'original : rotation sans perte, réglage « qualité de l'original ») ; des fichiers aux métadonnées d'appareil portent des tables de Photoshop (un Nikon D90, par exemple), signe d'un réenregistrement qui n'a pas changé l'EXIF. Il fallait dire quelles empreintes d'appareils livrer, et sous quelles règles.

## Options envisagées

### Appareils adaptatifs

- **A — Exclus, et nommés dans la fiche et les limites** (choix du 2026-11-15) : un modèle d'au moins 4 fichiers lus dont les tables diffèrent presque toutes (empreintes distinctes ≥ 3/4 des fichiers) est adaptatif ; ses fichiers ne comptent pour aucune empreinte.
- **B — Retenir leurs empreintes isolées** : une empreinte vue une fois ne dit rien d'un appareil.

### Empreintes retenues

- **A — Une marque, logiciels tolérés** : au moins 3 fichiers de 2 comptes, d'une seule marque, jamais sur un fichier de Photoshop ; quelques fichiers d'autres logiciels tolérés et nommés dans les limites.
- **B — Strict** : même critère, sans aucun fichier d'un autre logiciel ; les grandes familles Canon (71 et 39 fichiers) seraient exclues.
- **C — Une règle sans marque** : critère A, une seule règle « tables d'un appareil photo ».

## Décision

Option A dans les deux cas : appareils adaptatifs exclus et nommés ; empreintes d'une seule marque, jamais vues sur un fichier de Photoshop, au moins 3 fichiers de 2 comptes, les fichiers d'autres logiciels comptés et nommés dans la règle. Une règle par marque : `R-IMAGE-017` (Apple) à `R-IMAGE-022` (Sony), indice faible vers l'authenticité (ADR-0191), sans condition sur les métadonnées (ADR-0192). La phrase nomme la marque, pas le modèle : les tables sont communes à une famille.

## Raisons

- Les deux options A retenues par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec les options.
- Adaptatifs B écartée : une table vue sur un seul fichier ne se rattache à aucun appareil.
- Empreintes B écartée : elle retirerait les tables les plus répandues, pour des collisions expliquées ; C écartée : la marque est ce que la personne peut confronter à l'EXIF.
- « Jamais sur Photoshop » : une table que Photoshop écrit dirait à tort « appareil » sur un fichier réenregistré ; la règle de Photoshop la nomme déjà.
- Plusieurs marques : une empreinte partagée par deux marques ferait nommer la mauvaise ; elle n'est pas livrée.

## Conséquences

- Sur le relevé : 16 empreintes, de 6 marques (Apple 2, Canon 8, Kodak 1, Olympus 1, Panasonic 3, Sony 1), sur 213 fichiers sources ; aucune empreinte de Nikon ne remplit le critère. La question posée le 2026-11-16 annonçait 22 empreintes et 7 marques : ce compte n'écartait pas encore les fichiers des modèles adaptatifs, que la sélection retire avant de compter (journal du complément).
- Les appareils dont les fichiers de Commons sont rares, et les appareils adaptatifs (la plupart des reflex Nikon et des compacts Olympus et Fujifilm du relevé), ne sont pas reconnus ; la fiche liste ces derniers.
- Un fichier réenregistré par un logiciel qui garde les tables de l'original (GIMP, rotation sans perte) donne le constat de l'appareil : c'est une limite de chaque règle.
- La comparaison des tables avec l'appareil déclaré dans l'EXIF reste un point ouvert de l'architecture (§12, ADR-0182, ADR-0192).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-16 | Création ; appareils adaptatifs décidés par TheDarkMac le 2026-11-15, critère des empreintes le 2026-11-16 |
