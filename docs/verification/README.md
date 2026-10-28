# Vérification : banc d'évaluation et matrice

> Statut : **v1.1** ; v1.0 mergée avec T17, v1.1 proposée dans la PR de T18. Document vivant : toute modification est inscrite à l'historique (§5).

Ce dossier tient la [matrice de vérification](matrice.md) : chaque exigence du cahier, de sécurité et chaque principe directeur, avec son état, ses méthodes de vérification et leur résultat ([ADR-0024](../decisions/ADR-0024-methode-de-verification.md)). Les taux d'erreur des techniques sont mesurés par le banc d'évaluation, paquet `banc/` du dépôt ([ADR-0099](../decisions/ADR-0099-banc-outil-du-depot.md)).

| Élément | Fichier |
| --- | --- |
| Matrice : états, méthodes autres que « test », résultats | [`matrice.toml`](matrice.toml) |
| Matrice rendue (générée, ne pas modifier) | [`matrice.md`](matrice.md) |
| Contrôle et rendu de la matrice | `banc/matrice.py` |
| Banc d'évaluation | `banc/` (commande `python -m banc`) |
| Schéma du manifeste d'un corpus | `banc/corpus.schema.json` |
| Corpus d'essai (démonstration, rien de publiable) | `banc/essai/` |

## 1. Tenir la matrice à jour

Dans la PR d'une tâche :

1. Marquer chaque test qui vérifie une exigence : `pytestmark = pytest.mark.exigence("F-10")` pour le sujet d'un fichier, `@pytest.mark.exigence("ES-05")` sur un test pour une exigence annexe. Un identifiant absent de la matrice est refusé dès la collecte.
2. Mettre à jour, dans `matrice.toml`, l'état des exigences touchées (`realisee`, `partielle`, `a_venir`, `hors_v1`), leurs tâches, leurs méthodes ; pour une méthode autre que « test », la justification, et pour une exigence réalisée, la preuve et le résultat ([ADR-0106](../decisions/ADR-0106-contenu-et-controles-de-la-matrice.md)).
3. Régénérer la matrice, puis la vérifier :

```bash
uv run --locked python -m banc.matrice
```

```bash
uv run --locked python -m banc.matrice --verifier
```

`tests/test_matrice.py` lance la vérification : une matrice incohérente ou périmée fait échouer les tests. Chaque passage de la CI joint aussi la matrice remplie avec le résultat de chaque test (artefact `matrice-<système>-<python>`).

## 2. Décrire un corpus

Un corpus est un dossier avec un manifeste `corpus.toml` ([ADR-0103](../decisions/ADR-0103-manifeste-du-corpus.md)) : en-tête (`format`, `nom`, `version`, `date`, `nature`, `description`), puis une table `[[fichiers]]` par fichier :

```toml
[[fichiers]]
chemin = "generes/portrait-01.png"
empreinte = "…64 chiffres hexadécimaux…"
categorie = "genere"            # authentique, genere, transforme, retouche, malforme
partie = "evaluation"           # calibrage ou evaluation
groupe = "portrait-01"          # original dont dérive le fichier
origine = "ia"                  # authentique, ia, retouche ; absente seulement pour un malformé
provenance = { source = "…", licence = "…", date = "2026-10-28", generateur = "… 2.1" }
```

Un fichier transformé porte en plus `transformation` (`messagerie`, `capture-ecran`…). Tous les fichiers d'un groupe sont dans la même partie ; la partie évaluation ne sert jamais à régler un seuil ([ADR-0016](../decisions/ADR-0016-frontiere-sans-ia.md)). Changer un fichier ou une partie, c'est publier une nouvelle version du corpus.

## 3. Lancer le banc

Le banc ne démarre que sous Linux, dans un espace de noms réseau vide ([ADR-0100](../decisions/ADR-0100-evaluation-sans-reseau.md)) :

```bash
unshare -rn uv run --locked python -m banc CHEMIN/corpus.toml --sortie DOSSIER
```

Si `unshare -rn` est refusé (Ubuntu 24.04 et suivantes), autoriser les espaces de noms sans privilège le temps de l'évaluation : `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`.

Options : `--partie calibrage` (aucun taux publiable), `--catalogue DOSSIER` (catalogue candidat), `--desactiver MODULE`. Le banc écrit `evaluation.json` et `evaluation.md` dans `DOSSIER`, sans rien écraser ([ADR-0105](../decisions/ADR-0105-rapport-d-evaluation-et-corpus-d-essai.md)).

| Code | Sens |
| --- | --- |
| 0 | Évaluation menée, aucun écart |
| 1 | Évaluation menée, au moins un écart : arrêt brutal, deux analyses différentes d'un même fichier, niveau du catalogue non permis par la mesure, preuve fautive, cible par fichier non atteinte ou non mesurable |
| 2 | Rien n'est évalué : réseau présent, corpus invalide ou modifié, dossier inutilisable, catalogue invalide, module inconnu |
| 3 | Tentative d'accès au réseau pendant l'évaluation : aucun rapport écrit |

Sur le corpus d'essai, le code attendu est 1 : quatre authentiques ne suffisent pas à établir la cible par fichier.

## 4. Lire les mesures

Définitions : [ADR-0104](../decisions/ADR-0104-definition-des-mesures.md) ; bornes : [ADR-0101](../decisions/ADR-0101-bornes-des-niveaux-et-cible.md).

- Par technique et par catégorie : part non analysable (sur les fichiers où la technique s'applique), faux positifs (sur les authentiques analysés), faux négatifs (sur les générés ou retouchés analysés), confusions entre génération et retouche.
- Par règle de preuve ou d'indice : taux de faux positifs et niveau qu'il permet ; à recopier dans l'`evaluation` de la règle au catalogue (taux, effectif, borne supérieure).
- Taux par fichier : sur les authentiques, preuves et indices modérés ou forts ; cible : borne supérieure au plus 5 %.

Chaque taux est donné avec son effectif et l'intervalle de Wilson à 95 % : « 2/40 : 5,0 % [1,4 % ; 16,5 %] ».

## 5. Reproductibilité

Le banc analyse chaque fichier deux fois et compare les deux rapports en entier ; un défaut de reproductibilité est un écart ([ADR-0113](../decisions/ADR-0113-deux-analyses-par-fichier-au-banc.md)). Deux rapports JSON du même fichier, écrits sur deux postes ou à deux dates, se comparent par la commande de l'outil ([ADR-0112](../decisions/ADR-0112-comparaison-de-deux-rapports.md)) :

```bash
uv run --locked vk --comparer A.json B.json
```

Code 0 : aucun écart de résultat ; 1 : résultats différents ; 2 : rapport illisible. La commande dit si la garantie s'applique (même empreinte, même extension, mêmes versions, interpréteur compris, aucune analyse interrompue) ; écrire les rapports avec `--reveler empreinte` pour établir qu'il s'agit du même fichier. La CI compare les rapports du corpus d'essai entre Linux, macOS et Windows, sous Python 3.12 à 3.14 (job `reproductibilite`, [ADR-0110](../decisions/ADR-0110-variations-locales-et-entre-systemes.md)).

## 6. Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-10-28 | 1.0 | Création | T17 |
| 2026-10-28 | 1.1 | Double analyse au banc (§3), reproductibilité et `vk --comparer` (§5) | T18 |
