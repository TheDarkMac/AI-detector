# T30 — C2PA : détection, vérification, états et déclarations

- **Branche** : `tache/T30-c2pa`
- **Dates** : 2026-11-14
- **Exigences couvertes** : F-20, F-21, F-22, F-23 ; ES-09, ES-20 ; ES-06 et ES-10 en partie
- **Décisions** : ADR-0164 à ADR-0173 ; ADR-0165 à ADR-0168 et ADR-0173 acceptés, les autres proposés
- **Errata** : aucun

## Objectif

Détecter un manifeste C2PA, vérifier sa signature, l'intégrité du contenu signé et la chaîne de certificats, afficher l'état de la vérification et restituer ce que le manifeste déclare (F-20 à F-23), avec la liste de confiance au rapport (ES-09) et sans aucune requête sortante (ADR-0033).

## État initial

- PR [#26](https://github.com/TheDarkMac/AI-detector/pull/26) (T25). Sur `c4df5a0` : docs 43560486668 en échec, comme prévu, sur l'étape « Aucun ADR au statut Proposé » (ADR-0129) ; code 43560486430 vert. ADR-0160 et ADR-0163 validés par TheDarkMac pendant la revue (« Oui, les deux », 2026-11-14), passés à « Accepté » (`7f6a471`) : docs 43562095164 et code 43562095076 verts.
- L'assistant a mergé la PR le 2026-11-14 à 05:45:07 UTC, après le « CI verte, merge » de TheDarkMac : commit de merge `45c006a`, à l'adresse noreply (ADR-0007). Lancements de push sur `45c006a` : docs 43563031073 et code 43563031077 verts.
- La ligne « T25 » de l'index du journal portait « à venir » : corrigée en #26 dans cette tâche.
- Toujours en attente : messages à @Jean ; alertes de sécurité de Dependabot (à proposer) ; règle de protection des étiquettes `v*` et `can_admins_bypass`, sur demande seulement ; contrôle des ADR en tâche requise séparée (ADR-0129, option B) ; échec unique de la première campagne de fuzzing de T24, non reproduit.
- `detector` à jour avec `origin/detector` (`45c006a`), arbre de travail propre, identité locale `TheDarkMac <hei.ando14@gmail.com>`.

## Déroulé

1. Faisabilité : F-20 à F-23, A-03, A-33, A-36, A-55 ; ADR-0021, ADR-0023, ADR-0033, ADR-0043, ADR-0058, ADR-0084, ADR-0143 ; architecture §9 et §12 ; modèle de menace (RS-01, RS-02, ES-06, ES-09, ES-10, ES-20). `c2pa-python` 0.39.0 examiné (paquets, dépendances, réglages, lecture sous les restrictions de Linux) ; listes de confiance de la C2PA et liste intérimaire du CAI consultées (ADR-0164, ADR-0165).
2. Quatre questions à TheDarkMac, en un lot, chacune avec une recommandation ; les quatre recommandations retenues : liste officielle et liste TSA ([ADR-0165](../decisions/ADR-0165-liste-de-confiance-livree.md)) ; requêtes en ligne dans un complément ([ADR-0166](../decisions/ADR-0166-requetes-en-ligne-hors-de-t30.md)) ; manifeste invalide en indice faible vers la transformation ([ADR-0167](../decisions/ADR-0167-manifeste-invalide.md)) ; capture sous un signataire reconnu en preuve d'authenticité ([ADR-0168](../decisions/ADR-0168-capture-declaree-signataire-reconnu.md)). Les autres choix, faits par l'assistant, sont soumis dans la PR : [ADR-0164](../decisions/ADR-0164-bibliotheque-c2pa.md), [ADR-0169](../decisions/ADR-0169-etats-et-observations-c2pa.md), [ADR-0170](../decisions/ADR-0170-regles-du-module-c2pa.md), [ADR-0171](../decisions/ADR-0171-liste-de-confiance-au-rapport.md), [ADR-0172](../decisions/ADR-0172-versions-de-t30.md).
3. Branche `tache/T30-c2pa` créée depuis `detector` à jour (`45c006a`) ; `c2pa-python` ajouté (`uv add`), avec `cryptography`, `cffi`, `pycparser` et `toml` au verrou.
4. Liste de confiance : `donnees/confiance/`, schéma `confiance`, chargeur `_orchestration/confiance.py`, limites `TAILLE_MAX_CONFIANCE` et `CERTIFICATS_MAX`.
5. Modèle : `VersionConfiance`, `Versions.confiance`, `VERSION_SCHEMA` 0.5.0 ; configuration de P2 (`confiance`), `Ancres` dans le contexte des modules ; `analyser(confiance=...)`, `--confiance` ; Versions du HTML, du terminal, alerte d'une liste fournie, comparaison.
6. Module `c2pa` 0.1.0 et ses douze règles ; catalogue 0.5.0, empreinte au registre.
7. Tests : `tests/c2pa_essai.py` (autorité d'essai, signature pendant les tests), `tests/test_c2pa.py`, `tests/test_confiance.py` ; attentes mises à jour dans les tests du terminal, de la soumission, de l'orchestration, du modèle, du travail, des manifestes, de la reproductibilité et des règles de T22 à T24.
8. Fiche `provenance-c2pa` ; matrice (F-20 à F-23, ES-06, ES-09, ES-10, ES-20) régénérée.
9. PR [#27](https://github.com/TheDarkMac/AI-detector/pull/27) ouverte à la demande de TheDarkMac avant la fin de la vérification ; corrections et documentation poussées ensuite sur la même branche.
10. Adresse d'un manifeste distant trouvée en clair dans l'export masqué, observée par `xmp` ; TheDarkMac choisit de la masquer (« Yes, mask it », 2026-11-14) : `dcterms:provenance` marquée numéro de série, `xmp` 0.7.0, limite de R-C2PA-011 corrigée, empreinte de 0.5.0 recalculée ([ADR-0173](../decisions/ADR-0173-adresse-d-un-manifeste-distant.md)).

## Vérification

- Ruff (format et analyse) et mypy sans remarque.
- Premier passage complet, mesuré par coverage : 24 échecs sur 1 930 tests, tous des attentes à mettre à jour (voir « Problèmes rencontrés ») ; couverture de 99 %, module `c2pa` à 84 %.
- Second passage complet après corrections, mesuré par coverage comme en CI : 1 945 tests verts et un ignoré (lanceur de l'environnement virtuel), en 8 min 30 s ; couverture de 100 %. Lint Markdown sans erreur ; matrice régénérée.
- Essai sur le poste : JPEG du dépôt signé par l'autorité d'essai ; avec la liste d'essai, état « valide », preuve R-C2PA-001 ; avec la liste livrée, « valide_hors_liste », indice R-C2PA-004 ; nom commun et numéro du certificat masqués au résumé et à l'export.

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Lecture en erreur « Io » dans P2 | c2pa-python lit par `readinto`, que le flux du module n'avait pas | Flux fondé sur `readinto` |
| Un PDF sans table des références donnait « le fichier porte des données C2PA » | c2pa-rs refuse le conteneur (`InvalidAsset`), sans rien dire d'un manifeste | Recherche non menée, `format_partiel`, sans observation (ADR-0169) |
| Les essais de confiance donnaient « Valid » au lieu de « Trusted » | Scripts d'essai qui régénéraient l'autorité sans re-signer le fichier | Autorité créée une fois par session de tests |
| c2pa-rs refuse une création sans source numérique, une ouverture sans ingrédient cité | Contrôles de c2pa-rs à la signature | Manifeste d'essai sans source : ouverture d'un ingrédient étiqueté |
| `erreur_module` dans les tests de l'orchestration | Le catalogue des tests n'avait pas les règles du module c2pa, que ce module cite | Règles du module c2pa livré ajoutées au catalogue des tests |
| Un catalogue fourni sans règle refusé | Le manifeste du module c2pa cite ses règles « module » (ADR-0084) | Comportement voulu, consigné (ADR-0170) ; tests adaptés |
| Couverture du module c2pa à 84 % | Les processus de travail des tests ne sont pas mesurés (environnement vidé) | Mêmes cas exécutés dans le processus des tests |
| Adresse d'un manifeste distant en clair dans l'export masqué | Observée par `xmp`, sans marquage | Marquée numéro de série (ADR-0173) |
| Règles de T22 à T24 comptées avec celles de T30 | Tests qui définissaient leurs règles par catégorie sur tout le catalogue | Règles du module c2pa écartées de ces ensembles |

## Écarts par rapport au découpage

- **Ajouté** : liste de confiance fournie par l'utilisateur (`--confiance`) ; recherche non menée sur un conteneur illisible.
- **Reporté** : manifeste distant sur confirmation et révocation en ligne (ADR-0166) ; marquages recherchés de la couverture (F-25), laissés à T31.
- **Non fait** : assertions d'identité du CAWG, vignettes.

## Résultat

- Le rapport dit si le fichier porte un manifeste C2PA, dans quel état est sa vérification et pourquoi, ce qu'il déclare, et quelle liste de confiance a servi.
- Une source numérique déclarée donne une preuve sous un signataire reconnu, un indice faible sinon ; un écart d'empreinte, un indice faible de transformation.

## Reste à faire

- Complément de T30 : requêtes de P1 sur confirmation (RS-01, RS-02).
- T31 : marquages recherchés (F-25). T105 : recueil d'avis sur prototype, désormais possible (ADR-0026).
