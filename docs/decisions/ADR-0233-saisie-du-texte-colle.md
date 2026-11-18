# ADR-0233 — Saisie du texte collé : entrée standard, transmis au processus de travail après la configuration ; ni nom ni extension, empreinte des octets

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (protocole, champ `saisie` et refus précisés par l'assistant)
- **Tâche** : T80
- **Exigences liées** : F-01, F-05, F-73, ES-01, ES-04, ES-15 ; A-29 ; ADR-0036, ADR-0040, ADR-0070, ADR-0073, ADR-0074, ADR-0112

## Contexte

Le §3 du cahier range le « texte collé » parmi les médias ; A-29 relève qu'il n'est pas un fichier : F-02 (format par le contenu), F-03 (extension) et F-05 (empreinte du fichier) ne s'y appliquent pas, et aucune exigence ne décrit sa saisie. ADR-0074 a renvoyé à T80 la forme de la saisie, son canal vers le processus de travail, les analyses applicables et ce que le rapport dit à la place du nom et de l'empreinte. Le processus de travail lit d'ordinaire un fichier régulier par le descripteur que lui transmet le principal (ADR-0036) ; il ne doit rien écrire sur le disque (ES-15).

## Options envisagées

### Option A — Entrée standard ; empreinte des octets (recommandée)

`vk --texte` lit l'entrée standard jusqu'à sa fin : un tube, ou un collage au terminal terminé par Ctrl-D (Ctrl-Z puis Entrée sous Windows). UTF-8 strict, 16 Mio au plus. Le principal transmet les octets au processus de travail par l'entrée standard de celui-ci, après la configuration, sans fichier temporaire. Le format `texte` est posé sans identification par signature. Le rapport dit « texte collé » à la place du nom, sans extension ; l'empreinte est le SHA-256 des octets reçus. Interface de bibliothèque : `analyser_texte()`.

- Avantages : aucun fichier ; le texte collé suit le même déroulé qu'un fichier, isolation et contrôles de l'empreinte compris ; `--comparer` sait dire si deux rapports portent sur le même texte (ADR-0112).
- Inconvénients : un second canal d'entrée dans le processus de travail ; le texte est en mémoire dans les deux processus, d'où la limite.

### Option B — Entrée standard, sans empreinte

Même saisie, aucune empreinte au rapport, lecture littérale d'ADR-0074.

- Avantages : rien de ce qui pourrait désigner une source.
- Inconvénients : le champ devient facultatif au modèle ; `--comparer` ne peut plus dire qu'il s'agit du même texte. L'empreinte est déjà masquée par défaut (ADR-0031).

### Option C — Fichier anonyme en mémoire

Le principal écrit le texte dans un fichier en mémoire (`memfd_create`) et en transmet le descripteur : le protocole ne change pas.

- Avantages : le processus de travail lit un descripteur, comme pour un fichier.
- Inconvénients : `memfd_create` n'existe que sous Linux ; macOS et Windows demanderaient chacun un autre moyen, à sécuriser.

## Décision

Option A. Précisions de l'assistant :

| Point | Choix |
| --- | --- |
| Commande | `vk --texte`, sans fichier ; `--rapport` écrit `1.html` et `1.json`. Au terminal, une ligne sur la sortie d'erreur dit de coller le texte puis Ctrl-D |
| Bibliothèque | `analyser_texte(texte, desactiver=…, catalogue=…, confiance=…)`, où `texte` est une chaîne (encodée en UTF-8) ou ses octets |
| Limite | `TAILLE_MAX_TEXTE` : 16 Mio d'octets UTF-8 ; au-delà, refus « texte collé trop long » avant le lancement du travail |
| Refus | Texte vide, trop long, ou qui n'est pas de l'UTF-8 (chaîne à substitut isolé comprise) : motifs `texte_vide`, `texte_hors_limites`, `texte_illisible` de `AnalyseRefusee` |
| Lancement | Commande du travail `--texte` au lieu de `--descripteur` ; seuls les trois flux standard sont hérités |
| Protocole | La configuration annonce la longueur (`"texte": n`) ; les `n` octets suivent sa ligne sur l'entrée standard. Le travail refuse une longueur hors de 1 à 16 Mio, un texte incomplet, ou un texte annoncé sans `--texte` (et l'inverse) : défaut de l'outil, le processus s'arrête |
| Identification | Une seule partie `texte` si les octets sont de l'UTF-8, avec ou sans marque d'ordre ; aucune sinon. Aucune signature n'est cherchée (A-29), et les caractères de contrôle sont admis : `caracteres` les relève |
| Lecture | Le travail garde le texte en mémoire et le lit par position, comme un fichier (`FichierEnMemoire`) ; l'empreinte finale est celle de ces octets, comparée à celle du principal |
| Rapport | Champ `saisie` de l'identification : `fichier` ou `texte_colle` ; un texte collé n'a pas de nom (schéma : `nom` absent), donc pas d'extension ; une seule partie `texte`, sans partie extraite. Schémas du rapport et des messages en 0.11.0 |
| Présentation | « nom : aucun : texte collé » ; signalement « Texte collé : il n'a ni nom ni extension ; son empreinte est celle de ses octets en UTF-8 » |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : l'empreinte est utile à la reproductibilité (NF-06) et déjà masquée par défaut.
- Option C écartée : un mécanisme par système, quand l'entrée standard du travail existe déjà sur les trois.
- 16 Mio : un texte collé dépasse rarement quelques centaines de Kio ; la limite est celle d'une lecture de module (`TAILLE_MAX_LECTURE`) et de la configuration. Un texte plus long s'enregistre dans un fichier, analysé jusqu'à 1 Gio.
- Pas de contrôle d'UTF-8 par le principal : il ne lit pas le contenu pour l'interpréter (ES-01) ; c'est le travail qui reconnaît, ou non, une partie.

## Conséquences

- A-29 et la ligne « saisie de texte » du registre des arbitrages (§4) sont réalisées ; F-01 couvre le texte collé.
- Un texte collé reçoit les analyses du format `texte` : `caracteres` (F-73), et à la couverture la stylométrie et les références, hors V1. Le marquage `M-C2PA-TEXTE` y est recherché.
- Le terminal peut changer le texte avant l'outil (fins de ligne, caractères invisibles retirés par certains terminaux) : l'outil analyse les octets reçus, que l'empreinte désigne. La documentation utilisateur (T103) recommandera un tube depuis le presse-papiers ou un fichier.
- Sous Windows, PowerShell envoie aux programmes externes un texte encodé selon sa variable `$OutputEncoding` (page `about_Character_Encoding` de Microsoft, lue le 2026-11-17) : si elle ne vaut pas UTF-8, un texte non ASCII est refusé comme illisible, ou abîmé. Sa valeur par défaut selon la version de PowerShell n'a pas été vérifiée : à établir pour la documentation utilisateur (T103).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création ; option choisie par TheDarkMac au début de T80 |
