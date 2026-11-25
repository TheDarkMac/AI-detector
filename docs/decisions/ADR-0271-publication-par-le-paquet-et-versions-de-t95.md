# ADR-0271 — Publication par le paquet, sans changement de la release ; versions de T95

- **Statut** : Accepté
- **Date** : 2026-11-25
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T95
- **Exigences liées** : NF-19, NF-07 ; ADR-0019, ADR-0029, ADR-0041, ADR-0085, ADR-0088, ADR-0152

## Contexte

La release GitHub d'une version (`.github/workflows/publication.yml`, ADR-0041) porte les paquets, leurs empreintes, le fichier d'installation verrouillé et la version et l'empreinte du catalogue (`CATALOGUE.txt`). Depuis ADR-0268, les fiches sont dans le paquet. Reste à savoir s'il faut joindre aussi à la release une archive des fiches et du catalogue.

En préparant T95, l'assistant a cherché chaque chemin `docs/…` cité par un fichier du paquet : un seul n'existe pas. L'en-tête de `marquages.toml`, écrit en T31, renvoie à `docs/techniques/filigranes-invisibles.md`, qui n'a jamais existé ; l'inventaire des marquages, livré par la même tâche, est `docs/catalogue/inventaire-des-marquages.md`.

## Options envisagées

### Option A — Le paquet suffit (recommandée)

- Avantages : fiches et catalogue sont dans le wheel et le sdist joints à chaque release et publiés sur PyPI, avec leurs empreintes ; workflow inchangé.
- Inconvénients : pour lire une fiche sans installer l'outil, il faut ouvrir le wheel (une archive ZIP) ou le dépôt.

### Option B — Archive des fiches et du catalogue jointe à la release

- Avantages : lisible sans installer.
- Inconvénients : `publication.yml` à modifier, que seul TheDarkMac peut pousser (jeton sans droit `workflow`) ; une troisième copie à garder identique ; le dépôt public, à l'étiquette de la version, donne déjà la même chose.

## Décision

Option A.

- `publication.yml` est inchangé. Le catalogue, les fiches et le détail des règles sont publiés par le paquet, lisibles par `vk --regles`, `vk --regle IDENTIFIANT` et `vk --fiche MODULE`, et par le dépôt public.
- NF-19 passe à « réalisée » : la publicité se constate dans le paquet et se vérifie par les tests.
- **Chemin corrigé** : l'en-tête de `marquages.toml` renvoie à `docs/catalogue/inventaire-des-marquages.md`. Le texte seul change : catalogue **0.20.1** (`Z`, ADR-0152), du 2026-11-25, empreinte inscrite au registre. Un test vérifie désormais que chaque chemin `docs/….md` cité par un fichier du paquet existe.
- Modules, schémas (0.13.0) et rapport JSON inchangés.

## Raisons

- Option A retenue par TheDarkMac, sans raison supplémentaire, sur la recommandation de l'assistant.
- Option B écartée : elle duplique ce que publient déjà le paquet et le dépôt, et demande un workflow que l'assistant ne peut pas pousser.
- Correction en 0.20.1 plutôt qu'à la prochaine version du catalogue : T95 publie le catalogue, qui ne doit pas renvoyer à un document absent ; la correction ne change aucun constat.

## Conséquences

- La release d'une version porte, par le paquet, les fiches de ses modules.
- Le registre `docs/catalogue/versions.toml` reçoit l'entrée 0.20.1.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-25 | Création |
