# ADR-0272 — Corpus de référence réel, tiré de sources libres, fichiers hors du dépôt

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T100
- **Exigences liées** : §8 et §9 (livrable 5) du cahier, ES-22 ; M-33 ; ADR-0016, ADR-0099, ADR-0103, ADR-0105 ; A-12, A-13

## Contexte

Le §8 du cahier fait des taux d'erreur mesurés sur un corpus un critère d'acceptation de chaque technique, et le livrable 5 est « le corpus de test, ou sa description si les droits d'usage l'imposent ». Le banc (T17) sait évaluer un corpus décrit par un manifeste (ADR-0103) ; il n'a encore éprouvé que le corpus d'essai de neuf fichiers, dont aucun taux n'est publiable (ADR-0105). Le registre des arbitrages laissait à T100 les sources, le volume et les droits. Aucun générateur d'image ne tourne sur le poste (pas de processeur graphique) et l'assistant ne peut télécharger qu'avec l'accord explicite de TheDarkMac.

## Options envisagées

### Option A — Corpus réel tiré de sources libres, fichiers hors du dépôt (recommandée)

Des originaux sous licence libre ou dans le domaine public, téléchargés par des scripts versionnés : Wikimedia Commons (JPEG, PNG, WebP, PDF, MP3, WAV, Ogg, FLAC, WebM), data.gouv.fr (DOCX, ODT sous licence ouverte), Wikipédia en français (textes). Scripts, manifeste et licences au dépôt ; fichiers hors du dépôt.

- Avantages : des fichiers réels d'appareils et de logiciels variés, donc des faux positifs qui disent quelque chose de l'usage réel ; droits connus pour chaque fichier ; aucune redistribution par le dépôt.
- Inconvénients : quelques heures de téléchargement (4 à 8 Go annoncés) ; Commons et data.gouv.fr changent, si bien qu'un nouveau passage des scripts ne redonne pas exactement les mêmes fichiers ; MP4, MOV et M4A n'ont pas de source libre sûre (Commons ne les accepte pas).

### Option B — Description seule

T100 livre le protocole (sources, effectifs, répartition, transformations), le corpus est constitué plus tard.

- Avantages : aucun téléchargement.
- Inconvénients : aucun taux publiable en T101 ; le §8 ne peut être tenu pour aucune technique.

### Option C — Corpus fabriqué sur le poste

Fichiers créés par LibreOffice, ImageMagick, ffmpeg, sans téléchargement.

- Avantages : aucun téléchargement, octets entièrement maîtrisés.
- Inconvénients : aucune photo d'appareil réelle, aucun document d'un autre logiciel que ceux du poste : les faux positifs mesurés ne vaudraient que pour ces fichiers.

## Décision

Option A. TheDarkMac a autorisé, en choisissant cette option, le téléchargement depuis Commons, data.gouv.fr et Wikipédia, dans le volume annoncé.

Précisions de l'assistant :

| Point | Choix |
| --- | --- |
| Sources | `commons.wikimedia.org` et `upload.wikimedia.org`, `www.data.gouv.fr` et `static.data.gouv.fr`, `fr.wikipedia.org` ; toute autre adresse est refusée par les scripts avant la requête, et une redirection vers une autre adresse n'est pas suivie |
| Requêtes | HTTPS, `User-Agent` qui nomme le dépôt, sans donnée personnelle ; une seconde au moins entre deux appels aux API, deux secondes entre deux téléchargements ; reprise après une coupure |
| Volume | Plafond de 8 Gio en tout, tenu par le script de téléchargement ; tailles bornées par famille dans les recherches (8 Mio pour une image, 6 Mio pour un PDF, 5 Mio pour un son ou une vidéo, 10 Mio pour un document) |
| Intégrité | Empreinte SHA-1 publiée par la source vérifiée à chaque téléchargement quand elle existe (Commons, data.gouv.fr) ; fichier écarté sinon |
| Scripts | `banc/reference/`, six phases lancées dans l'ordre depuis la racine du dépôt (`python -m banc.reference.reference_1_listes`, …) : listes, choix et parties, téléchargements, dérivés, retouches par LibreOffice, manifeste |
| Au dépôt | Scripts, textes écrits par l'assistant (ADR-0273), manifeste `corpus.toml` et `effectifs.json` |
| Hors du dépôt | Fichiers du corpus et données brutes (`.gitignore` du dossier) : volume, et licences qui demandent l'attribution et le partage à l'identique |
| Formats sans source | MP4, MOV, M4A et HEIC n'entrent au corpus que comme transformés (conversion d'un original de Commons) ; aucun authentique ni généré de ces formats |

## Raisons

- Option A retenue : seule à mesurer les faux positifs sur des fichiers réels, comme le §8 le demande (« captures d'appareils variés »), avec des droits connus.
- Option B écartée : elle repousserait tout taux publiable, donc toute acceptation de technique.
- Option C écartée : un corpus qui ne connaît que les logiciels du poste mesurerait l'outil sur ce qu'il voit déjà.
- Fichiers hors du dépôt : ADR-0103 le permet (le manifeste désigne leur dossier) ; les licences CC BY-SA exigent attribution et partage, que la page de chaque fichier, citée au manifeste, porte déjà.

## Conséquences

- Le corpus de la version 1.0.0 est l'ensemble des octets constitués sur le poste de TheDarkMac le 2026-11-25 ; le manifeste les identifie un à un. Un tiers retrouve les originaux par leur page et leur empreinte, mais pas les dérivés à l'octet près (dates écrites par Ghostscript et LibreOffice) : un nouveau passage des scripts donne une nouvelle version du corpus.
- La conservation d'une copie des fichiers, hors du dépôt, revient à TheDarkMac (« Reste à faire » du journal de T100).
- Les critères des originaux sont fixés par ADR-0273, les effectifs et les parties par ADR-0274, les dérivés par ADR-0275, le manifeste et sa description par ADR-0276.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
