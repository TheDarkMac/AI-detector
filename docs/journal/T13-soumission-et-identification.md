# T13 — Soumission et identification

- **Branche** : `tache/T13-soumission-et-identification`
- **Dates** : 2026-10-27 → 2026-10-27
- **Exigences couvertes** : F-01 à F-05 ; ES-01 (ouverture et empreinte), ES-07, ES-08, ES-17 (interface publique) ; F-82 (`hors_perimetre`, `fichier_tronque`, `format_partiel`) ; A-25, A-29, A-31
- **Décisions** : ADR-0070 à ADR-0075
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : format réel par signature binaire, discordance d'extension, refus hors périmètre, empreinte SHA-256 (ADR-0040) vérifiée en fin d'analyse, fichiers polyglottes signalés (ES-07, ES-08) ; plusieurs fichiers par commande, analysés indépendamment (ADR-0015) ; format réel transmis par le processus de travail, option de désactivation des modules (ADR-0063). T12 y avait ajouté : ouverture du fichier par le principal, comparaison des empreintes, interface publique `analyser` ; ADR-0056 : les raisons `format_partiel` et `fichier_tronque`.

## État initial

- PR [#12](https://github.com/TheDarkMac/AI-detector/pull/12) (T10, complément 2) : CI verte sur `485f988` (docs 40410140276, code 40410140183) et sur `9282367` (docs 40438463716, code 40438463749 ; 15 vérifications, CodeRabbit « skipped »). TheDarkMac a retenu les options A et D d'ADR-0068 et validé ADR-0069 : statut « Accepté », `CONTRIBUTING.md` §8 ajouté (commit `9282367`, étapes 9 et 10 du journal de ce complément).
- Mergée le 2026-10-27 à 02:52:25 UTC à la demande explicite de TheDarkMac : `gh pr merge 12 --merge --subject "Merge: T10 (complément 2) — Numérotation des versions et contrôles de la publication (#12)"`. Commit de merge `5c94a1a`, à l'adresse noreply (ADR-0007). Lancements de push `code` et `docs` sur `5c94a1a` : réussis. La ligne de ce complément dans l'index du journal portait « à venir » : corrigée en #12 dans cette tâche.
- **Première publication sur PyPI**, à la demande explicite de TheDarkMac : étiquette annotée `v0.1.0.dev0` posée sur `5c94a1a` et poussée (`CONTRIBUTING.md` §8). Lancement 40441277035 : `construction` vert, premier passage réel des contrôles d'ADR-0069 réussi (étiquette sur `detector`, version PEP 440, `pré-version : true`).
  - Première approbation de l'environnement « pypi » par TheDarkMac non enregistrée (l'API ne montrait aucune approbation, le job `pypi` attendait toujours) ; l'assistant n'a pas approuvé à sa place. Seconde approbation enregistrée.
  - Paquets envoyés le 2026-10-27 à 03:04:28 UTC : wheel `fd9bc2b3…`, identique à la construction locale ; paquet source `4aa3bcdd…`, différent de la construction locale antérieure, faite avant une modification d'un commentaire de `pyproject.toml`.
  - Sur PyPI : `License-Expression: Apache-2.0`, `requires-python >=3.12`, une attestation de provenance par fichier (GitHub, `TheDarkMac/AI-detector`, `publication.yml`, environnement `pypi`).
  - Release `v0.1.0.dev0` publiée à 03:04:41 UTC, marquée pré-version et non « latest » (`/releases/latest` répond 404) ; fichiers : les deux paquets, `SHA256SUMS`, `installation-verrouillee.txt`.
  - Installation dans un environnement neuf depuis PyPI par `uv pip install --require-hashes -r installation-verrouillee.txt` : réussie ; `vk --version` affiche `0.1.0.dev0`, `voight-kampff --modules` « aucun module ». Le nom est désormais réservé sur PyPI.
- Facultatif, seulement sur demande : règle de protection des étiquettes `v*`, `can_admins_bypass` désactivé sur l'environnement « pypi ».
- Toujours en attente : messages à @Jean (reformulations du registre §4, dont F-81, et six questions) ; Dependabot à revoir le lundi 2026-11-02 ; alertes de sécurité de Dependabot désactivées sur le dépôt (à proposer).
- uv n'est pas installé sur le poste ; l'assistant utilise uv 0.13.5 dans un environnement temporaire.
- `detector` à jour avec `origin/detector` (`5c94a1a`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Lecture du découpage (T13), du journal de T12, de l'architecture, d'ADR-0012, ADR-0013, ADR-0015, ADR-0031, ADR-0036, ADR-0040, ADR-0056, ADR-0059, ADR-0061 à ADR-0065, du modèle de menace (ES-07, ES-08, M-06, M-08, M-30), de l'analyse critique (A-25, A-29, A-31) et du code de T12.
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation :
   - fichiers polyglottes : l'assistant recommandait d'analyser le format principal seul ; TheDarkMac a retenu l'analyse de chaque format reconnu ([ADR-0071](../decisions/ADR-0071-fichiers-polyglottes.md)) ;
   - signalements dans la rubrique Identification, recommandation suivie ([ADR-0072](../decisions/ADR-0072-signalements-de-l-identification.md)) ;
   - avant T15 et T16, résultat d'analyse et résumé sans donnée identifiante, recommandation suivie ([ADR-0073](../decisions/ADR-0073-resultat-et-resume-avant-le-rapport.md)) ;
   - texte collé reporté à T80, recommandation suivie ([ADR-0074](../decisions/ADR-0074-texte-colle-reporte.md)).

   Aucune raison supplémentaire donnée. Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0070](../decisions/ADR-0070-identification-du-format.md) (identification) et [ADR-0075](../decisions/ADR-0075-soumission-et-refus.md) (soumission et refus).
3. Branche `tache/T13-soumission-et-identification` créée depuis `detector` à jour (`5c94a1a`) ; uv 0.13.5 réinstallé ; 384 tests verts au départ, couverture 100 %.
4. `formats.py` (vocabulaire et extensions). Modèle : `Partie`, champ `partie` des observations, constats, non menées et techniques, raison `hors_perimetre`, rubrique Identification avec ses champs déduits, vérification des renvois mise en commun (`verifier_resultats`). Schémas du rapport, des messages (message `identification`, partie du message `module`) et des manifestes (formats du périmètre seulement).
5. `_travail/identification.py` : signatures, parcours des structures, chaîne de parties, PDF dans les 1024 premiers octets, ZIP lu depuis la fin, texte en dernier recours. Essai manuel sur 21 échantillons fabriqués : JPEG suivi d'un DOCX, JPEG puis PDF, PDF précédé de bruit, deux JPEG à la suite, ODT, ID3 et MP3, UTF-16, etc. : parties attendues.
6. Processus de travail : contexte limité à sa partie (positions relatives, localisations ramenées au fichier, numérotation continue), message `identification`, empreinte recalculée après les modules, taille par `fstat`.
7. Processus principal : réception partie par partie, `_orchestration/soumission.py` (ouverture, refus, empreinte finale), `analyse.py` (interface publique), commande `vk FICHIER... --desactiver MODULE`. Essai manuel : JPEG + PDF nommé `.png` (deux parties, extension discordante, trois octets non reconnus), fichier vide, GIF, dossier, fichier absent refusés avec leur motif, module inconnu en code 2.
8. Tests : `test_modele.py`, `test_schemas.py`, `travail_factice.py`, `test_orchestration.py`, `test_travail.py` adaptés ; `echantillons.py`, `test_identification.py`, `test_soumission.py` créés ; `test_cli.py` complété. `pythonpath = ["tests"]` ajouté à la configuration de pytest pour partager les échantillons.
9. Couverture portée à 100 % après correction d'échantillons de test et deux simplifications du code (voir ci-dessous).
10. En rédigeant la documentation, relecture d'ADR-0056 : T13 devait produire `format_partiel` et `fichier_tronque`, ce que la première version ne faisait pas. Ajout de l'état « tronquée » d'une partie, distinct d'une fin non établie, et des non menées tirées de l'identification par le principal ; le modèle exige leur présence (ADR-0071).
11. CI : étape « Commande d'analyse depuis le wheel (T13) » ajoutée au job `paquet`. Job rejoué en local : deux constructions identiques ; le wheel contient les nouveaux fichiers ; depuis le wheel installé, `vk` identifie un PDF et refuse un fichier vide (code 1) ; toujours aucun `.pyc` dans `_travail/`.
12. Vérification finale : 626 tests verts, couverture 100 % (lignes et branches) ; Ruff et mypy sans remarque.
13. Documentation : ADR-0070 à ADR-0075 ; renvois dans ADR-0012, ADR-0013, ADR-0015, ADR-0031, ADR-0036, ADR-0040, ADR-0056, ADR-0059, ADR-0061 à ADR-0065 ; architecture v1.6, modèle de données v1.2, glossaire v1.2, découpage v0.12, registre des arbitrages v1.5 ; `README.md` ; index des ADR et du journal.
14. Lint Markdown en local, vérification des fichiers interdits, commits ; branche poussée et PR ouverte vers `detector`.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| `PackageNotFoundError` en lançant un script de modification des schémas | Python du système, sans le paquet installé | Script lancé par `uv run --locked python` |
| Un script de remplacement de texte s'arrête sur un passage introuvable | Ruff avait reformaté le fichier entre-temps | Script repris sur le texte reformaté ; rien n'avait été écrit |
| `ModuleNotFoundError: echantillons` | `--import-mode=importlib` : le dossier des tests n'est pas dans le chemin d'import | `pythonpath = ["tests"]` dans la configuration de pytest |
| Ruff `I001` sur les imports des tests | `echantillons` est classé parmi les modules tiers | Ordre corrigé par `ruff check --fix` |
| Cinq tests d'identification en échec au premier passage | Erreurs dans les échantillons : trame MPEG-2 de 288 octets au lieu de 261 ; JPEG sans `FF D8 FF` ; `%PDF-x` attendu « inconnu » alors que c'est bien du texte ; une seule entrée du répertoire ZIP décalée ; PNG à deux blocs pour un parcours borné à deux | Échantillons et attendus corrigés ; le code était juste |
| Faux enregistrements de fin ZIP jamais examinés | Échantillons de 20 octets au lieu de 22 (longueur du commentaire absente) | Fonction `fin_zip` construite par `struct` |
| Lignes non couvertes dans l'identification | Méthode `_Vue.sous` inutilisée ; borne de boucle inaccessible dans `_noms` | Méthode retirée ; boucle bornée par la longueur du répertoire |
| `format_partiel` et `fichier_tronque` non produits | ADR-0056 relu trop tard, à la rédaction de la documentation | État « tronquée » et non menées tirées de l'identification (étape 10) |
| Non menées `format_partiel` inattendues dans les tests du principal | Le factice annonçait une partie d'un octet dans un fichier de 1 028 | Le factice lit la taille du fichier transmis et y étend ses parties |
| mypy : `element["parties"]` refusé dans le factice | Variable réaffectée par `json.loads` : son type redevient l'union déclarée | Variable distincte |

Aucun de ces problèmes n'est une erreur d'une analyse ou d'une décision antérieure : pas d'erratum. L'oubli de l'étape 10 a été rattrapé avant tout commit.

## Écarts par rapport au découpage

- **Ajout** : analyse de chaque partie d'un polyglotte (ADR-0071), avec `partie` dans le modèle et le protocole ; état « tronquée » d'une partie et non menées tirées de l'identification.
- **Ajout** : formats reconnus hors périmètre (GIF, ZIP, EXE…), pour un refus qui nomme le format et un polyglotte qui nomme ses parties (ADR-0070).
- **Ajout** : hachage de nouveau par le principal quand le travail s'arrête avant d'envoyer son empreinte (ADR-0075).
- **Ajout** : `pythonpath = ["tests"]` dans la configuration de pytest, et une étape au job `paquet` de la CI.
- **Reporté** à T14 : refus « hors limites » (F-04), limites de taille avant le lancement, fuzzing de l'identification (ES-19).
- **Reporté** à T16 : rapport construit à partir d'une analyse, exports, masquage, gabarits des signalements ; le résumé du terminal sera revu.
- **Reporté** à T80 : saisie du texte collé (A-29, ADR-0074).

## Résultat

- Soumission : ouverture unique, refus de ce qui n'est pas un fichier régulier, empreinte à l'ouverture et vérifiée en fin d'analyse, refus explicites ; plusieurs fichiers par commande, chacun dans son processus de travail.
- Identification par le contenu dans le processus de travail : 17 formats du périmètre et 14 formats nommés ; parties d'un polyglotte, fin logique, octets non reconnus, extension et concordance dans la rubrique Identification.
- Interface publique `voight_kampff.analyser` et commande `vk FICHIER... --desactiver MODULE` ; aucun module d'analyse livré, donc aucune technique dans la couverture.
- Vérification locale : les commandes de `CONTRIBUTING.md` §1 passent (626 tests, couverture 100 %) ; construction reproductible ; commande d'analyse lancée depuis le wheel installé.

## Reste à faire

- Validation par TheDarkMac d'ADR-0070 et ADR-0075, au statut « Proposé ».
- T14 : limites, refus « hors limites », fuzzing des analyseurs dont l'identification ; restrictions et Job Object.
- T15 : catalogue, règles citées par les manifestes, techniques hors V1 par format.
- T16 : rapport à partir d'une analyse, exports, masquage, gabarits des raisons et des signalements.
- T80 : saisie du texte collé.
- Toujours en attente : messages à @Jean ; Dependabot à revoir le 2026-11-02 ; alertes de sécurité de Dependabot à proposer ; règle de protection des étiquettes et `can_admins_bypass`, sur demande.
