# ADR-0091 — Texte des phrases de constat dans la règle du catalogue

- **Statut** : Accepté
- **Date** : 2026-10-28
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T16
- **Exigences liées** : §6 du cahier, F-26, F-80, NF-06, NF-07, NF-11, NF-14 ; ADR-0020, ADR-0058, ADR-0084, ADR-0086, ADR-0088, ADR-0090

## Contexte

Un constat porte une phrase : un identifiant de gabarit et des paramètres qui renvoient à des observations (ADR-0058). La règle du catalogue fixe ce gabarit (ADR-0084), mais le texte de la phrase n'était écrit nulle part : ADR-0020 le veut « hors du code, par langue », et T15 l'a laissé à T16. Il faut décider où il vit, sachant qu'un catalogue fourni par l'utilisateur peut ajouter des règles « moteur » avec des gabarits nouveaux (ADR-0086).

## Options envisagées

### Option A — Dans la règle

Un champ `phrase = { fr = "… {parametre} …" }` dans chaque règle ; au chargement, les emplacements `{nom}` du texte doivent être exactement les paramètres déclarés.

- Avantages : la règle dit tout ce que dit son constat ; changer une phrase change la version et l'empreinte du catalogue, donc se lit au rapport (NF-06, NF-07) ; un catalogue fourni se suffit à lui-même.
- Inconvénients : une même phrase employée par deux règles est écrite deux fois ; une langue de plus demandera un nouveau format du catalogue.

### Option B — Un fichier de phrases dans le catalogue

`phrases/fr.toml` (gabarit → texte) dans le dossier du catalogue.

- Avantages : une phrase partagée par plusieurs règles n'est écrite qu'une fois ; une langue = un fichier.
- Inconvénients : modifie la forme du dossier fixée par ADR-0088 ; deux fichiers à relire ensemble pour comprendre une règle.

### Option C — Dans l'outil, hors catalogue

`rapport/phrases/fr.toml` dans le paquet.

- Avantages : le catalogue ne change pas.
- Inconvénients : une règle ajoutée par l'utilisateur avec un gabarit nouveau n'aurait pas de texte et serait refusée ; changer une phrase exigerait une nouvelle version de l'outil, contre F-26.

## Décision

Option A.

- La règle porte `phrase`, une table qui associe une langue à un texte ; en V1, la seule langue admise est `fr`, obligatoire (ADR-0020). Texte de 1 à 1 024 caractères.
- Un emplacement s'écrit `{nom}`, où `nom` suit la syntaxe d'un paramètre. Les emplacements d'un texte sont exactement les paramètres de la règle (déclarés pour une règle « module », portés par les conditions pour une règle « moteur ») ; un paramètre peut figurer plusieurs fois. Toute autre accolade rend la règle invalide : le texte n'a aucun moyen d'en écrire une littéralement.
- À l'export, chaque emplacement est remplacé, littéralement, par la valeur affichée de l'observation que désigne le paramètre, ou par la mention de son masquage (ADR-0093). Le remplacement n'interprète ni le nom (pas de `str.format`, qui suivrait `{a.b}` comme un attribut) ni la valeur.
- Le gabarit reste l'identifiant de la phrase pour un lecteur du JSON ; le contrôle de conformité d'un constat à sa règle est inchangé (ADR-0090).
- Le `format` du catalogue reste 1 : aucune version publiée de l'outil ne lisait encore de règle, et le catalogue livré 0.1.0 n'en contient aucune ; son empreinte ne change pas.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle change la forme du catalogue et sépare une règle de sa phrase, pour un gain (phrase partagée) que rien ne demande encore.
- Option C écartée : elle rend impossible une règle nouvelle dans un catalogue fourni, et lie le texte du rapport à la version de l'outil plutôt qu'à celle du catalogue.
- Format inchangé : passer à `format = 2` pour un champ que nul n'a pu écrire ne protégerait aucun lecteur ; le registre et la CI comparent des règles, et il n'y en a aucune.

## Conséquences

- Schéma `regles` : champ `phrase` obligatoire. Code : `Regle.textes`, `emplacements()` et `remplir()` dans `_regles.py`.
- Le guide du catalogue (`docs/catalogue/README.md`) montre le champ dans son exemple.
- Une phrase se relit en même temps que la règle qui la porte ; NF-14 s'applique à ce texte comme aux autres textes de l'outil.
- Une deuxième langue sera un nouveau format du catalogue (ADR-0085).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création |
