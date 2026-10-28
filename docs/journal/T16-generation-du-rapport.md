# T16 — Génération du rapport

- **Branche** : `tache/T16-generation-du-rapport`
- **Dates** : 2026-10-28
- **Exigences couvertes** : F-83, §6 du cahier, NF-11, NF-12, NF-14, NF-18 ; ES-12, ES-13, ES-14 ; F-80 (phrases), F-82 (phrases des raisons) ; A-44, A-48, A-49
- **Décisions** : ADR-0091 à ADR-0098
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : génération du rapport, résumé sans verdict (ADR-0018), rubriques du §6, exports HTML autonome et JSON avec schéma (ADR-0025), masquage par défaut des données identifiantes, empreinte comprise (ADR-0031), protection du HTML contre l'injection (ES-12), avertissement. S'y ajoutaient les points laissés à T16 : texte des phrases de constat (ADR-0020, journal de T15), une phrase par raison de non-menée (ADR-0056) et par signalement de l'identification (ADR-0072), catalogue fourni mis en évidence (ADR-0086), résumé du terminal revu (ADR-0073), gabarit HTML et moyen d'échappement (architecture §12).

## État initial

- PR [#15](https://github.com/TheDarkMac/AI-detector/pull/15) (T15), ouverte le 2026-10-27 depuis `tache/T15-catalogue-de-regles`. Déjà consigné dans le journal de T15 (étapes 16 et 17) : CI sur `d6a01fe` (code 40568844786, en échec sous macOS et Windows sur un test de casse, corrigé par `32bd6db`), ADR-0088 à ADR-0090 acceptés (`dfe5c2f`).
- CI sur `dfe5c2f` verte : code 40587952293, docs 40587952036 ; 15 vérifications, CodeRabbit « skipped » ; vérifiée avant le merge.
- Mergée le 2026-10-27 à 21:40:09 UTC à la demande explicite de TheDarkMac (« La CI de la PR #15 est verte : vérifie-la, puis merge avec le titre … ») : `gh pr merge 15 --merge --subject "Merge: T15 — Catalogue de règles versionné et daté (#15)"`. Commit de merge `af3ad40`, à l'adresse noreply (ADR-0007). Lancements de push sur `af3ad40` : docs 40588696275 réussi ; code 40588696530, encore en cours au moment du merge, réussi à 21:42:42 UTC (premier passage de `catalogue.py base HEAD^1` en push). La ligne de T15 dans l'index du journal portait « à venir » : corrigée en #15 dans cette tâche.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement.
- uv n'est pas installé sur le poste ; l'assistant a réinstallé uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`af3ad40`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : T16 dépend de T11 à T15, mergées. Aucun module n'est livré : une analyse réelle n'a pas de constat, les exports sont donc éprouvés sur le rapport de test complet (`tests/conftest.py`) et sur le processus de travail factice. Lecture du découpage, du journal de T15, d'ADR-0018, ADR-0020, ADR-0021, ADR-0025, ADR-0031, ADR-0056, ADR-0057, ADR-0059, ADR-0068, ADR-0073, ADR-0084, ADR-0086, ADR-0088, du §6 du cahier, d'ES-12 à ES-14 et M-20 à M-23 du modèle de menace, de l'architecture (§3, §4, §12), du modèle de données, du glossaire, et du code du modèle, de l'analyse, de la soumission, des règles et de la commande.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation ; les quatre recommandations ont été suivies, sans raison supplémentaire :
   - texte des phrases : dans la règle du catalogue ([ADR-0091](../decisions/ADR-0091-texte-des-phrases-dans-la-regle.md)) ;
   - écriture des rapports : `--rapport DOSSIER`, fichiers nommés par le rang ([ADR-0092](../decisions/ADR-0092-ecriture-des-rapports.md)) ;
   - levée du masquage : `--reveler CATEGORIE`, sans raccourci « tout » ([ADR-0093](../decisions/ADR-0093-levee-du-masquage.md)) ;
   - HTML : bibliothèque standard, sans script, politique de sécurité stricte ([ADR-0094](../decisions/ADR-0094-html-par-la-bibliotheque-standard.md)).

   Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0095](../decisions/ADR-0095-export-json-masque.md) (export JSON masqué, schéma 0.2.0), [ADR-0096](../decisions/ADR-0096-neutralisation-des-caracteres-invisibles.md) (neutralisation), [ADR-0097](../decisions/ADR-0097-regles-citees-et-interface-d-export.md) (règles citées, interface d'export), [ADR-0098](../decisions/ADR-0098-contenu-ordre-et-textes-du-rapport.md) (contenu, ordre et textes).
3. Branche `tache/T16-generation-du-rapport` créée depuis `detector` à jour (`af3ad40`) ; 819 tests verts au départ, un sauté (lanceur de Windows).
4. Règles : champ `phrase` (schéma `regles`, `Regle.textes`), emplacements vérifiés au chargement, remplacement littéral (`emplacements`, `remplir`) ; aide des tests `regle_dict` : une phrase par défaut qui cite les paramètres.
5. Analyse : `Analyse.regles` (règles citées, conformité vérifiée), `Analyse.regle`, `Analyse.rapport()` ; la soumission joint les règles du catalogue que citent les constats.
6. Modèle et schémas : `VERSION_SCHEMA` 0.2.0 ; schéma du rapport étendu à l'export (objet `masquage`, nom, empreinte et valeur absents sous condition) ; `verifier_masquage` ; `Rapport.depuis_dict` refuse un export masqué.
7. Textes du rapport dans `rapport/textes.toml` ; `rapport/_presentation.py` (neutralisation, échappement JSON, valeurs, phrases, signalements, alertes, résumé) ; `rapport/export.py` (masquage, JSON validé avant d'être rendu, `valider`) ; `rapport/_html.py` (document, feuille de style, politique). Le paquet exporte `exporter_json`, `exporter_html`, `CategorieIdentifiante`.
8. Rendu vérifié dans le navigateur intégré, servi depuis le dossier temporaire par `python3 -m http.server` sur 127.0.0.1 : feuille de style appliquée, aucune erreur de politique dans la console. Intitulés redondants (« Couverture » trois fois, terme du glossaire seul dans un paragraphe) remplacés par une introduction et des légendes propres à chaque tableau ; taille groupée par milliers ; chaque preuve du résumé précédée de sa direction.
9. Commande : `--rapport DOSSIER`, `--reveler CATEGORIE`, résumé revu (alertes, nom et empreinte masqués ou levés, phrases des signalements et des raisons, résumé d'ADR-0018), sortie neutralisée, avertissement après le dernier fichier analysé. Essai de bout en bout : un fichier dont le nom contient U+202E s'affiche `doc⟨U+202E⟩fdp.txt`, s'écrit `‮` dans le JSON, `⟨U+202E⟩` dans le HTML ; rapports créés en `0600` ; une deuxième commande vers le même dossier s'arrête (code 2) sans rien écraser.
10. Premier passage de toute la suite : 11 échecs, tous attendus (sorties du terminal changées ; analyses des tests d'orchestration construites sans les règles citées).
11. Tests ajoutés : `tests/test_rapport.py` (analyse et rapport, JSON masqué par catégorie, relecture, validation d'un export altéré, échappement JSON, neutralisation, HTML autonome, politique, structure, ordre des rubriques, masquage et levée, échappement des valeurs, fuzzing d'une valeur quelconque, contenu des constats, alertes, libellés de chaque énumération, absence de tournure de certitude) ; cas nouveaux dans `test_cli.py` (rapports par rang, levée, catégorie inconnue, rapport existant, dossier inutilisable, rapport non écrit, sortie neutralisée), `test_regles.py` (phrase), `test_schemas.py` (données absentes sans masquage, masquage incomplet).
12. CI : étape « Rapports HTML et JSON depuis le wheel (T16) » du job `paquet` : `vk --rapport`, JSON validé par `export.valider`, nom et empreinte absents, HTML avec politique et sans script. Répétée en local sur un wheel construit avec les contraintes épinglées : `textes.toml`, `export.py` et `_html.py` sont dans le wheel, l'étape passe.
13. Contrastes calculés (formule WCAG) pour chaque couple de couleurs de la feuille de style : texte de 7,2:1 à 17,2:1, traits de 5,3:1 à 8,8:1, en mode clair et sombre.
14. Vérification locale : `uv lock --check` ; Ruff (format et analyse) et mypy sans remarque ; pip-audit, aucune faille connue ; 889 tests verts, un sauté (lanceur de Windows), couverture 100 % lignes et branches. Un premier passage de la couverture, lancé pendant qu'un autre tournait, donnait 99 % : les deux partageaient les fichiers de mesure des sous-processus ; relancé seul, 100 %.
15. Documentation : ADR-0091 à ADR-0098 ; renvois dans ADR-0018, ADR-0020, ADR-0025, ADR-0031, ADR-0054, ADR-0056, ADR-0057, ADR-0059, ADR-0068, ADR-0072, ADR-0073, ADR-0084, ADR-0086, ADR-0090 ; architecture v1.9, modèle de données v1.5, glossaire v1.5, découpage v0.15, registre des arbitrages v1.8, guide du catalogue v1.1 ; `README.md`, `CONTRIBUTING.md` (§5, §9), `docs/README.md` ; index des ADR et du journal.
16. Lint Markdown en local (`npx --yes markdownlint-cli2@0.23.2`) ; aucun fichier interdit suivi. Commits, branche poussée, PR ouverte vers `detector`.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Le rapport HTML ouvert depuis un fichier local ne se laissait ni capturer ni lire par le navigateur intégré | Le panneau montre un fichier local en image figée | Dossier temporaire servi sur 127.0.0.1 par `python3 -m http.server`, le temps de la vérification |
| `echapper_json` aurait échappé les sauts de ligne de l'indentation | Le saut de ligne est un caractère de contrôle (Cc) | Seuls les caractères à partir de U+0020 sont échappés : `json.dumps` échappe déjà, dans une chaîne, tous ceux d'en dessous ; ce qui reste est la mise en forme |
| Un dossier `--rapport` qui est un fichier aurait été annoncé « rapport existant » | `mkdir` lève `FileExistsError`, la même exception qu'une création exclusive refusée | Les deux cas sont distingués avant l'analyse, chacun avec son message (code 2) |
| Ruff (RUF001) signale les caractères invisibles et espaces ambigus des tests | Les tests de neutralisation les écrivent exprès | Règle désactivée pour `tests/test_rapport.py` seulement, avec commentaire dans `pyproject.toml` |
| Test d'échappement : nom `<b>nom</b>.jpg` refusé par le modèle | Une barre oblique fait d'un nom un chemin (ES-14) | Nom `<i>nom.jpg` |
| Test d'une règle non conforme : la règle modifiée était elle-même invalide | Une information neutre ne peut pas pointer vers l'origine IA | Fondement changé (vérification déterministe au lieu de cryptographique) : règle valide, constat non conforme |
| Un nom de fichier avec ESC ne peut pas être créé sous Windows | Windows interdit les caractères de contrôle dans un nom | Le test de la commande emploie U+202E ; ESC et les autres contrôles sont vérifiés par les tests unitaires de la neutralisation |
| « voir la rubrique Analyses non menées » au terminal | Phrase du résumé commune au terminal et au HTML, alors que le terminal n'a pas de rubrique | Phrase réduite au nombre d'analyses non menées |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum.

## Écarts par rapport au découpage

- **Écart avec ADR-0059** : le schéma du rapport décrit aussi l'export masqué (`masquage`, champs absents) ; le modèle reste sans masquage (ADR-0095).
- **Écart avec ADR-0085** : le `format` du catalogue reste 1 malgré le champ `phrase` obligatoire, aucune version publiée n'ayant lu de règle (ADR-0091).
- **Ajout** : neutralisation au terminal et dans le JSON, en plus du HTML (ES-12, ADR-0096) ; rapports en `0600` ; glossaire dans le rapport (NF-11) ; étape de CI depuis le wheel.
- **Non fait** : liste de garde par nom d'observation, que permettait ADR-0057, faute de module qui marque une donnée ; visualisations (F-84), qui arrivent avec leurs techniques (A-44 : nouvel ADR pour `img-src`) ; audit d'accessibilité par un outil automatique, la conformité WCAG étant vérifiée par inspection et démonstration (ADR-0024) ; trace de la levée dans un journal de conservation, à T91 (A-49).
- **Modèle de menace inchangé** : ES-12 à ES-14 sont réalisées par ces ADR, sans menace nouvelle ; RR-08 (rapport démasqué transmis) reste un risque résiduel.

## Résultat

- `vk FICHIER...` affiche un résumé sans verdict, masqué par défaut, neutralisé ; `--rapport DOSSIER` écrit `<rang>.html` et `<rang>.json` sans rien écraser ; `--reveler CATEGORIE` lève une catégorie et l'annonce en tête.
- `exporter_json` rend un document conforme au schéma du rapport 0.2.0, données masquées absentes ; `exporter_html` un document autonome, sans script, sous politique de sécurité stricte, structuré pour WCAG 2.2 AA.
- Phrases des constats dans les règles du catalogue ; textes du rapport dans `rapport/textes.toml`.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent (889 tests, couverture 100 %).

## Reste à faire

- Relecture par TheDarkMac des textes du rapport (`rapport/textes.toml`) et des ADR proposés (ADR-0095 à ADR-0098).
- T17 : banc d'évaluation ; T18 : reproductibilité, à partir de `Analyse.rapport()`.
- T20, T22 : premières règles, avec leur phrase ; premier marquage de données identifiantes.
- T91 : trace de la levée du masquage (NF-17) ; T103 : mentions définitives.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
