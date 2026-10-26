# ADR-0061 — Interface d'un module : une fonction et un contexte

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T12
- **Exigences liées** : NF-03, NF-10 ; ES-04, ES-17 ; ADR-0022, ADR-0036, ADR-0042, ADR-0058, ADR-0060

## Contexte

ADR-0042 fait de chaque technique un sous-paquet de `modules/`, importé seulement par le processus de travail. Il faut fixer ce que ce code expose, comment il lit le fichier et comment il rend ses résultats. Plusieurs règles doivent être appliquées à chaque module, et il vaut mieux qu'elles le soient une fois pour toutes : identifiants d'observation uniques, directions permises par la fiche technique (ADR-0022), garde hors processus de travail (ES-17), résultats écartés en cas d'erreur (ADR-0060), tailles bornées (ES-04).

## Options envisagées

### Option A — Une fonction et un contexte

Chaque module expose `analyser(contexte)`. Le contexte lit le fichier par position et reçoit les résultats (`observer`, `constater`, `non_mener`).

- Avantages : le contexte applique toutes les règles communes ; un module sans état reste une fonction ; les résultats sont gardés par le moteur, qui peut les écarter.
- Inconvénients : le module dépend d'un objet fourni par le moteur, à documenter.

### Option B — Une classe abstraite

Chaque module hérite d'une classe `Module` et définit sa méthode `analyser`.

- Avantages : même contrat, rendu visible par l'héritage.
- Inconvénients : plus de cérémonie, sans rien apporter à un module sans état.

### Option C — Une fonction qui renvoie ses résultats

`analyser(fichier)` renvoie la liste de ses observations, constats et analyses non menées.

- Avantages : aucun objet à fournir.
- Inconvénients : la numérotation des observations, les directions permises et les tailles retombent sur chaque module ; rien n'arrête un module qui accumule des résultats sans borne avant de rendre la main.

## Décision

Option A. Un module est un dossier `modules/<identifiant>/` avec `manifeste.toml` (ADR-0064) et un `__init__.py` qui expose :

```python
def analyser(contexte: Contexte) -> None: ...
```

Le contexte (`voight_kampff._travail.contexte.Contexte`) offre :

| Élément | Rôle |
| --- | --- |
| `module`, `format_reel`, `taille` | Identifiant du module, format identifié (T13), taille du fichier |
| `lire(position, taille)` | Au plus `taille` octets à partir de `position`, moins en fin de fichier ; lecture à position explicite (ADR-0036), bornée |
| `observer(nom, valeur, *, unite, localisation, identifiante)` | Enregistre une observation et renvoie son identifiant `<module>/<n>` |
| `constater(phrase, donnees, regle, *, fondement, categorie, direction, graduation, localisation)` | Enregistre un constat ; ses données sont des observations de ce module, sa direction est permise par le manifeste |
| `non_mener(raison, *, localisation)` | Signale une partie non menée ; raisons admises : `format_partiel`, `fichier_tronque`, `reference_manquante`, `reseau_desactive` |

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : elle ajoute une hiérarchie de classes sans rien vérifier de plus.
- Option C écartée : chaque module devrait refaire les mêmes contrôles, et les résultats ne seraient bornés qu'après coup.

## Conséquences

- Le contexte construit les objets du modèle (ADR-0054) : un résultat invalide lève une exception dans le module, qui devient `erreur_module` ; ses résultats sont écartés (ADR-0060).
- Construire un contexte hors d'un processus de travail verrouillé lève `HorsProcessusDeTravail` (ES-17) : un programme qui importerait un module pour l'appeler dans son propre processus est arrêté.
- Les raisons `erreur_module`, `limite_depassee`, `module_desactive`, `hors_v1` et les raisons d'interruption sont réservées au moteur et au processus principal.
- Un constat ne cite que des observations de son module. Un module qui exploite le résultat d'un autre (T53) demandera d'élargir cette règle, par un nouvel ADR.
- Chaque tâche de technique (T13, T20 et suivantes) écrit son module selon cette interface, avec ses tests.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
