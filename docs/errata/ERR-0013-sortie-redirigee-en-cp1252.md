# ERR-0013 — Sortie de `vk` redirigée sous Windows : écrite en cp1252, arrêtée par la neutralisation

- **Date de constat** : 2026-11-17
- **Tâche en cours** : T80
- **Document ou élément touché** : `src/voight_kampff/cli.py` (sortie écrite dans l'encodage du flux depuis T10, neutralisation `⟨U+XXXX⟩` et valeurs révélées depuis T16) ; application d'ADR-0096 ; `tests/test_caracteres.py` (`-X utf8` de T80), `tests/test_traces.py`
- **Nature** : exécution

## Ce qui était écrit ou fait

`vk` écrivait ses lignes par `print`, dans l'encodage que Python donne à la sortie standard. Hors d'un terminal, c'est l'encodage local : cp1252 sous Windows pour une installation en français ou en anglais, avec le gestionnaire d'erreurs `strict`. Toute ligne qui porte un caractère absent de cp1252 levait `UnicodeEncodeError` : la forme `⟨U+XXXX⟩` de la neutralisation (ADR-0096 ; U+27E8 et U+27E9 n'existent pas en cp1252), comme une valeur en cyrillique, en grec ou en chinois. La commande s'arrêtait avec une pile d'appels et le code 1, sans écrire les lignes suivantes ni l'avertissement. Reproduit sous Linux en imposant l'encodage : `PYTHONIOENCODING=cp1252 vk --reveler nom_de_fichier` sur un fichier nommé `a`, U+202E, `b.txt`, sortie redirigée vers un fichier : `UnicodeEncodeError: 'charmap' codec can't encode character '\u27e8'`.

## Ce qui est juste

Hors d'un terminal, la sortie et l'erreur de `vk` s'écrivent en UTF-8, avec `backslashreplace` ([ADR-0238](../decisions/ADR-0238-sortie-redirigee-en-utf8.md)) : toute ligne s'écrit, la neutralisation et les valeurs comprises.

## Comment l'erreur a été trouvée

Échec de CI sous Windows pendant T80 (journal de T80, étape 13) : le test de `vk --texte`, qui lisait en UTF-8 la sortie écrite dans un fichier, recevait du cp1252. Le test a été contourné par `-X utf8`, et le défaut renvoyé à sa propre PR (journal de T80, « Reste à faire »).

## Cause

- Les tests de la commande lisaient sa sortie par `capsys` de pytest, toujours en UTF-8, ou par un interpréteur lancé sous Linux et macOS, où l'encodage local est l'UTF-8. Aucun test ne redirigeait la sortie sous un encodage qui n'a pas `⟨`.
- Les tests qui lancent `vk` par un interpréteur (`test_cli.py`, `test_traces.py`, `test_reproductibilite.py`, `test_caracteres.py`) n'y lisent aucune ligne neutralisée, sauf celui de T80 ; contourné par `-X utf8`, il ne vérifiait plus la commande telle qu'un utilisateur la lance.

## Correction appliquée

- `cli.py` : `_sortie_en_utf8`, appelée au début de `main`, reconfigure en UTF-8, avec `backslashreplace`, chacun de `sys.stdout` et `sys.stderr` qui n'est pas un terminal (ADR-0238).
- Tests (`tests/test_cli.py`) : `test_vrai_processus_sortie_redirigee_sous_un_encodage_sans_chevrons` lance `python -m voight_kampff --reveler nom_de_fichier` avec `PYTHONIOENCODING=cp1252`, sortie dans un fichier, et y lit `⟨U+202E⟩` et les accents en UTF-8 ; `test_flux_redirige_reecrit_en_utf8` vérifie l'encodage, le gestionnaire et l'échappement d'un substitut isolé ; `test_terminal_et_flux_quelconque_laisses`, qu'un terminal et un flux d'un autre type restent tels quels. Les deux premiers échouent sans la correction (`UnicodeEncodeError`), vérifié sous Linux.
- `tests/test_traces.py` : la sortie de `vk` lue dans un tube est décodée en UTF-8, plus dans l'encodage local (cp1252 sous Windows, qui ne définit pas tous les octets de l'UTF-8).
- `tests/test_caracteres.py` : `-X utf8` retiré de la commande de `test_vrai_processus_texte_colle_par_la_commande`, qui vérifie désormais la correction sous Windows avec l'encodage local réel.

## Prévention

- Le test lancé avec `PYTHONIOENCODING=cp1252` tourne sur les trois systèmes de la CI : une sortie qui ne passe plus par la reconfiguration y échoue partout, pas seulement sous Windows.
- Un test qui lance `vk` ne contourne plus l'encodage de sa sortie (`-X utf8`, `PYTHONUTF8`) : il la lit telle qu'un utilisateur la recevrait.
- ADR-0096 renvoie à ADR-0238.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-18 | Création |
