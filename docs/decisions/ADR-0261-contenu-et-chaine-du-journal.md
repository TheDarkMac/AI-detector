# ADR-0261 — Contenu du journal : soumissions, refus, exports et rapports lus ; une ligne JSON chaînée par SHA-256

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T91
- **Exigences liées** : NF-17, ES-16 ; A-49 ; ADR-0030, ADR-0040, ADR-0093, ADR-0233 ; menaces M-27, M-28

## Contexte

NF-17 demande de journaliser « chaque soumission, consultation et export ». En ligne de commande, l'outil voit les soumissions et les exports, mais pas l'ouverture d'un rapport HTML dans un navigateur. ADR-0030 exclut les noms de fichier et demande une chaîne qui rende une modification détectable. Le journal de T16 renvoyait aussi à T91 la trace de la levée du masquage (A-49, ADR-0093).

## Options envisagées

### Option A — Soumission, refus, export et rapports lus par l'outil (recommandée)

Soumission : empreinte du fichier ou du texte, format réel, catégories dont le masquage est levé. Refus : motif. Export : empreinte de chaque fichier de rapport écrit, et de son jeton d'horodatage. Consultation : empreinte de chaque rapport lu par `--comparer`.

- Avantages : les trois actes de NF-17, dans la mesure où l'outil les voit ; l'empreinte du fichier relie la soumission à ses rapports, même quand le rapport la masque (ADR-0031).
- Inconvénients : « consultation » ne couvre pas la lecture d'un rapport hors de l'outil.

### Option B — Soumission et export seulement

- Avantages : plus simple.
- Inconvénients : un des trois actes de NF-17 manque, alors que l'outil lit des rapports (`--comparer`).

### Option C — Empreintes des rapports seulement

- Avantages : moins révélateur en cas de saisie : l'empreinte du fichier reçu n'y est pas.
- Inconvénients : le rapport JSON masque l'empreinte par défaut ; la chaîne ne relierait plus le fichier à son rapport, ce qui est l'objet d'une chaîne de conservation.

## Décision

Option A. Le journal est un fichier texte en UTF-8, une entrée par ligne, chaque ligne un objet JSON terminé par un saut de ligne, conforme au schéma publié `journal` (`src/voight_kampff/schemas/journal.schema.json`, format 1) :

| Champ | Toutes les entrées |
| --- | --- |
| `format` | 1 |
| `numero` | rang de l'entrée, à partir de 1, sans trou |
| `date` | heure UTC du poste, à la seconde, non certifiée |
| `evenement` | `soumission`, `refus`, `export` ou `consultation` |
| `qui` | nom déclaré par `--qui`, absent sans lui |
| `precedente` | empreinte SHA-256 des octets de la ligne précédente, sans son saut de ligne ; 64 zéros pour la première |

| Événement | Champs propres |
| --- | --- |
| `soumission` | `saisie` (`fichier` ou `texte_colle`), `empreinte` du fichier ou du texte, `format_reel`, `levees` (catégories montrées par `--reveler`, A-49) |
| `refus` | `saisie`, `motif` (ADR-0075, ADR-0233) ; pas d'empreinte, un refus pouvant précéder la lecture |
| `export` | `soumission` (numéro de l'entrée), `rapport` (`html` ou `json`), `empreinte` du fichier écrit, et `horodatage` (`autorite`, `heure` annoncée, `jeton` : empreinte du `.tsr`) s'il en a un |
| `consultation` | `empreinte` du rapport JSON lu par `--comparer` |

- Jamais de nom de fichier, de chemin, ni de rang dans la commande ; l'URL de l'autorité d'horodatage est la seule adresse inscrite.
- La soumission est inscrite avant l'affichage du résumé, chaque export après l'écriture de son fichier et de son jeton, les consultations avant l'affichage de la comparaison : rien n'est montré sans être journalisé.
- La vérification exige en plus du schéma : numéros à la suite, chaîne des empreintes, dernière ligne terminée, export renvoyant à une soumission antérieure.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : elle tait un acte que l'outil voit.
- Option C écartée : sans l'empreinte du fichier soumis, le journal ne dit plus de quel fichier un rapport est issu ; ADR-0030 a déjà choisi de la garder, avec l'avertissement qui va avec (M-27).
- Chaîne par l'empreinte de la ligne précédente, plutôt qu'une signature par une clé locale : une clé sur le poste ne prouverait rien de plus contre son propriétaire (RR-06), et la chaîne se vérifie sans l'outil, avec `sha256sum`.
- Une ligne JSON par entrée : un ajout ne réécrit rien, et une ligne inachevée par une coupure se repère.

## Conséquences

- Limites de la chaîne, dites par `--verifier-journal` et à documenter en T103 : qui a le fichier peut le récrire en entier ; la dernière entrée peut être modifiée, et des entrées finales supprimées, sans rompre la chaîne. Horodater le journal lui-même fermerait ce point ; non demandé par ADR-0030, il n'est pas fait.
- Le schéma `journal` rejoint les schémas publiés ; son format change par un nouveau numéro, comme celui de la liste de confiance (ADR-0171).
- `comparaison.lire_avec_empreinte` rend l'empreinte des octets lus, pour que la consultation porte sur le fichier réellement comparé.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
