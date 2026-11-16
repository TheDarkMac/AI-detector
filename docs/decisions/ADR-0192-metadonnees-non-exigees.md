# ADR-0192 — Tables relevées : l'absence de métadonnées n'est pas exigée

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : complément de T40
- **Exigences liées** : F-30, F-14 ; ADR-0154, ADR-0182, ADR-0191

## Contexte

Les règles des tables d'encodeurs logiciels (R-IMAGE-004 à R-IMAGE-007) exigent un JPEG sans aucun bloc de métadonnées lu par le projet (ADR-0154, ADR-0182) : sans métadonnées, ces tables sont le profil d'une image passée par une messagerie ou un réseau social. Il fallait dire si les règles des tables de Photoshop et d'appareils (ADR-0191) l'exigent aussi.

## Options envisagées

### Option A — Aucune condition sur les métadonnées

- Avantages : Photoshop et les appareils écrivent presque toujours des métadonnées ; ce que dit la règle (dernière compression par Photoshop, ou par un appareil) ne dépend pas d'elles.
- Inconvénients : un fichier qui garde l'EXIF d'un appareil et les tables de Photoshop donne le constat de Photoshop ; c'est exact, mais il s'ajoute aux constats des métadonnées.

### Option B — Absence exigée, comme R-IMAGE-004

- Avantages : même forme que les règles de T24 et de T40.
- Inconvénients : la règle ne verrait presque aucun fichier de Photoshop ni d'appareil ; un appareil sans métadonnées est l'exception.

### Option C — Présence exigée pour les appareils

- Avantages : écarte un fichier dépouillé dont les tables seules seraient celles d'un appareil.
- Inconvénients : une condition de plus sans mesure ; la comparaison des tables avec l'appareil déclaré n'est pas possible dans une règle (ADR-0147, ADR-0182).

## Décision

Option A : les règles des tables relevées n'ont qu'une condition, l'empreinte parmi celles relevées.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : la règle n'aurait presque jamais lieu de s'appliquer.
- Option C écartée : la condition ne dirait rien de plus sur l'origine des tables.

## Conséquences

- La raison donnée pour R-IMAGE-004 (ADR-0154) ne vaut pas ici : ces règles ne cherchent pas un passage par une messagerie.
- Des tables d'appareil sous l'EXIF d'un autre appareil ne sont pas relevées comme une discordance ; c'est un point ouvert de l'architecture (§12, comparaison entre modules).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création ; décision prise par TheDarkMac le 2026-11-15, avant le relevé, dans la première session du complément |
