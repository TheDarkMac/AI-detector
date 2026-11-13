# ERR-0010 — Test de la procédure d'empreinte du catalogue : lignes triées par empreinte, pas par chemin

- **Date de constat** : 2026-11-13
- **Tâche en cours** : T22
- **Document ou élément touché** : `tests/test_catalogue.py`, test `test_empreinte_selon_la_procedure_publiee` (T15, commit `01bda86`)
- **Nature** : exécution

## Ce qui était écrit ou fait

Le test recalcule l'empreinte du catalogue livré « selon la procédure publiée » (ADR-0088, `docs/catalogue/README.md` §4) et la compare à celle du chargeur. Il formait une ligne `<sha256 du fichier>  <chemin relatif>` par fichier, puis triait **les lignes** :

```text
lignes = sorted(
    f"{hashlib.sha256(contenu).hexdigest()}  {chemin}\n"
    for chemin, contenu in fichiers(dossier)
)
```

Le tri portait donc sur l'empreinte de chaque fichier, qui ouvre la ligne.

## Ce qui est juste

La procédure trie **les chemins**, puis calcule chaque ligne dans cet ordre : `find . -type f -printf '%P\n' | LC_ALL=C sort | xargs sha256sum | sha256sum`. C'est ce que font le chargeur (`_orchestration/catalogue.py`, `empreinte`) et le script de la CI (`.github/scripts/catalogue.py`), et ce qu'ADR-0088 décrit (« triée par chemin »). Le code livré et l'empreinte inscrite au registre étaient justes ; seul le test était faux.

## Comment l'erreur a été trouvée

Par la suite complète, après l'ajout des premières règles (T22) : le catalogue passe d'un fichier à treize, et le test a donné une autre empreinte que le chargeur. La commande publiée, lancée dans le dossier du catalogue, donne celle du chargeur.

## Cause

Avec un seul fichier (`catalogue.toml`, de T15 à T21), les deux ordres coïncident : le test ne pouvait pas distinguer le tri par chemin du tri par ligne. Le test a été écrit en même temps que le chargeur, sans cas à plusieurs fichiers.

## Correction appliquée

- Le test trie les fichiers par chemin, en octets comme `LC_ALL=C sort`, puis forme les lignes dans cet ordre ; il vérifie qu'il porte sur plus d'un fichier (commit `bc26b0d`, avec les premières règles).
- Aucune empreinte publiée ne change : le registre n'avait qu'une entrée, d'un catalogue à un seul fichier.

## Prévention

- Le catalogue livré a désormais plusieurs fichiers : le test distingue les deux ordres, et le vérifie (`assert len(lignes) > 1`).
- `test_empreinte_change_avec_le_contenu_ou_le_chemin` couvre déjà l'ordre des fichiers pour la fonction `empreinte` ; seul le test de la procédure publiée était en cause.
