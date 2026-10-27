# Registre des décisions (ADR)

Un ADR (*Architecture Decision Record*) consigne une décision, son contexte, **les options écartées et pourquoi**, et ses conséquences.

## Règles

- Un fichier par décision : `ADR-NNNN-titre-court.md`, numéro croissant, jamais réutilisé.
- Copier [`gabarit.md`](gabarit.md).
- Un ADR accepté n'est plus modifié sur le fond. Pour changer d'avis, on écrit un nouvel ADR qui le **remplace**, et on passe l'ancien au statut « Remplacé par ADR-NNNN ». Les corrections de forme (coquille, lien) sont admises et notées en bas du fichier.
- Statuts possibles : `Proposé`, `Accepté`, `Remplacé par ADR-NNNN`, `Abandonné`.
- Une décision rejetée mérite aussi un ADR (statut `Abandonné`) si l'option a été sérieusement envisagée.
- « Décideur » indique qui a tranché : TheDarkMac, ou une proposition de l'assistant validée par TheDarkMac.

## Index

| N° | Titre | Statut | Date |
| --- | --- | --- | --- |
| [ADR-0001](ADR-0001-flux-de-travail-git.md) | Flux de travail git : branches, PR et protections | Accepté | 2026-10-26 |
| [ADR-0002](ADR-0002-exclusion-fichiers-assistant.md) | Exclusion locale de `CLAUDE.md` et `.claude/` | Accepté | 2026-10-26 |
| [ADR-0003](ADR-0003-identite-des-commits.md) | Identité des commits et absence de co-auteur | Accepté | 2026-10-26 |
| [ADR-0004](ADR-0004-conventions-de-documentation.md) | Conventions de documentation | Accepté | 2026-10-26 |
| [ADR-0005](ADR-0005-nommage-branches-et-commits.md) | Nommage des branches et messages de commit | Accepté | 2026-10-26 |
| [ADR-0006](ADR-0006-ci-documentaire.md) | Intégration continue documentaire | Accepté | 2026-10-26 |
| [ADR-0007](ADR-0007-adresse-des-commits-de-merge.md) | Adresse e-mail des commits de merge créés par GitHub | Accepté | 2026-10-26 |
| [ADR-0008](ADR-0008-objectif-principal.md) | Objectif principal : provenance et intégrité, accent sur l'origine IA | Accepté | 2026-10-26 |
| [ADR-0009](ADR-0009-public-cible.md) | Public cible prioritaire : journalistes et vérificateurs de faits | Accepté | 2026-10-26 |
| [ADR-0010](ADR-0010-distribution-et-traitement-local.md) | Distribution en ligne de commande et bibliothèque, traitement local hors ligne | Accepté | 2026-10-26 |
| [ADR-0011](ADR-0011-licence-apache-2.md) | Logiciel libre et gratuit sous licence Apache-2.0 | Accepté | 2026-10-26 |
| [ADR-0012](ADR-0012-perimetre-v1.md) | Périmètre de la première version | Accepté | 2026-10-26 |
| [ADR-0013](ADR-0013-module-texte.md) | Module texte réduit aux contrôles déterministes | Accepté | 2026-10-26 |
| [ADR-0014](ADR-0014-controle-avant-publication.md) | Contrôle avant publication limité aux métadonnées en V1 | Accepté | 2026-10-26 |
| [ADR-0015](ADR-0015-lots-flux-et-anteriorite.md) | Analyse par lots, flux, analyse groupée et recherche d'antériorité | Accepté | 2026-10-26 |
| [ADR-0016](ADR-0016-frontiere-sans-ia.md) | Frontière du « sans IA » : seuils calibrés admis, apprentissage exclu | Accepté | 2026-10-26 |
| [ADR-0017](ADR-0017-services-tiers-et-ocr.md) | Services tiers à base d'IA optionnels, lecture des documents numérisés exclue | Accepté | 2026-10-26 |
| [ADR-0018](ADR-0018-synthese-et-graduation.md) | Synthèse sans verdict et graduation fixe des indices | Accepté | 2026-10-26 |
| [ADR-0019](ADR-0019-publicite-des-regles.md) | Règles, seuils et limites entièrement publics | Accepté | 2026-10-26 |
| [ADR-0020](ADR-0020-langue-et-cadre-legal.md) | Français en V1, cadre légal de l'Union européenne | Accepté | 2026-10-26 |
| [ADR-0021](ADR-0021-definition-de-la-preuve.md) | Définition de la preuve | Accepté | 2026-10-26 |
| [ADR-0022](ADR-0022-hypotheses-distinguees.md) | Hypothèses distinguées : rubrique obligatoire de chaque fiche technique | Accepté | 2026-10-26 |
| [ADR-0023](ADR-0023-reproductibilite.md) | Reproductibilité à entrées égales et analyse non interrompue | Accepté | 2026-10-26 |
| [ADR-0024](ADR-0024-methode-de-verification.md) | Une méthode de vérification par exigence | Accepté | 2026-10-26 |
| [ADR-0025](ADR-0025-exports-et-accessibilite.md) | Exports HTML et JSON, accessibilité WCAG 2.2 AA | Accepté | 2026-10-26 |
| [ADR-0026](ADR-0026-validation-du-besoin.md) | Validation du besoin sur prototype, étude d'usage hors V1 | Accepté | 2026-10-26 |
| [ADR-0027](ADR-0027-methode-du-modele-de-menace.md) | Méthode du modèle de menace : STRIDE et cas d'abus | Accepté | 2026-10-26 |
| [ADR-0028](ADR-0028-niveau-d-isolation.md) | Niveau d'isolation : un processus restreint par fichier | Accepté | 2026-10-26 |
| [ADR-0029](ADR-0029-integrite-du-catalogue.md) | Intégrité du catalogue et de la liste de confiance : livrés avec l'outil | Accepté | 2026-10-26 |
| [ADR-0030](ADR-0030-portee-de-nf-17-en-local.md) | Portée de NF-17 en local : journal et horodatage optionnels, aucune trace par défaut | Accepté | 2026-10-26 |
| [ADR-0031](ADR-0031-empreinte-donnee-identifiante.md) | L'empreinte du fichier est une donnée identifiante | Accepté | 2026-10-26 |
| [ADR-0032](ADR-0032-double-usage.md) | Fonctions à double usage admises en V2 avec garde-fous | Accepté | 2026-10-26 |
| [ADR-0033](ADR-0033-politique-des-requetes-sortantes.md) | Politique des requêtes sortantes : aucune URL du fichier résolue sans confirmation | Accepté | 2026-10-26 |
| [ADR-0034](ADR-0034-langage-python.md) | Langage : Python 3.12 ou ultérieur | Accepté | 2026-10-26 |
| [ADR-0035](ADR-0035-systemes-et-mecanismes-d-isolation.md) | Systèmes de la V1 et mécanismes d'isolation : Linux en référence, macOS et Windows | Accepté | 2026-10-26 |
| [ADR-0036](ADR-0036-processus-de-travail-et-protocole.md) | Processus de travail : un interpréteur neuf par fichier, échange en JSON | Accepté | 2026-10-26 |
| [ADR-0037](ADR-0037-gestion-des-dependances.md) | Gestion des dépendances : uv et verrou à empreintes | Accepté | 2026-10-26 |
| [ADR-0038](ADR-0038-format-du-catalogue.md) | Format du catalogue : TOML validé par JSON Schema | Accepté | 2026-10-26 |
| [ADR-0039](ADR-0039-expressions-regulieres-re2.md) | Expressions régulières du catalogue : RE2 | Accepté | 2026-10-26 |
| [ADR-0040](ADR-0040-empreinte-sha-256.md) | Empreinte cryptographique : SHA-256 | Accepté | 2026-10-26 |
| [ADR-0041](ADR-0041-canal-de-distribution.md) | Canal de distribution : PyPI avec attestations de provenance | Accepté | 2026-10-26 |
| [ADR-0042](ADR-0042-modules-et-extension.md) | Modules d'analyse : découverte interne, manifeste déclaratif | Accepté | 2026-10-26 |
| [ADR-0043](ADR-0043-politique-des-bibliotheques.md) | Politique des bibliothèques : Python pur d'abord | Accepté | 2026-10-26 |
| [ADR-0044](ADR-0044-titre-des-commits-de-merge.md) | Titre des commits de merge : toujours fixé à la main | Accepté | 2026-10-26 |
| [ADR-0045](ADR-0045-nom-du-projet.md) | Nom du projet : Voight-Kampff | Accepté | 2026-10-26 |
| [ADR-0046](ADR-0046-visibilite-du-depot.md) | Visibilité du dépôt : public | Accepté | 2026-10-26 |
| [ADR-0047](ADR-0047-formatage-et-analyse-statique.md) | Formatage et analyse statique : Ruff et mypy strict | Accepté | 2026-10-26 |
| [ADR-0048](ADR-0048-cadre-de-tests.md) | Tests : pytest et coverage.py | Accepté | 2026-10-26 |
| [ADR-0049](ADR-0049-construction-du-paquet.md) | Construction du paquet : uv_build, épinglé avec empreintes | Accepté | 2026-10-26 |
| [ADR-0050](ADR-0050-numero-de-version.md) | Numéro de version écrit dans `pyproject.toml` | Accepté | 2026-10-26 |
| [ADR-0051](ADR-0051-integration-continue-du-code.md) | Intégration continue du code : trois systèmes, Python 3.12 à 3.14 | Accepté | 2026-10-26 |
| [ADR-0052](ADR-0052-surveillance-des-failles.md) | Surveillance des failles : pip-audit et Dependabot | Accepté | 2026-10-26 |
| [ADR-0053](ADR-0053-branche-par-defaut.md) | Branche par défaut : `detector` | Accepté | 2026-10-26 |
| [ADR-0054](ADR-0054-representation-du-modele.md) | Représentation du modèle : dataclasses figées et JSON Schema écrits à la main | Accepté | 2026-10-26 |
| [ADR-0055](ADR-0055-cinq-directions.md) | Cinq directions de constat : « transformation » ajoutée à F-81 | Accepté | 2026-10-26 |
| [ADR-0056](ADR-0056-raisons-des-analyses-non-menees.md) | Raisons des analyses non menées : liste fermée, phrase par gabarit | Accepté | 2026-10-26 |
| [ADR-0057](ADR-0057-marquage-des-donnees-identifiantes.md) | Données identifiantes marquées par l'observation, au module qui la produit | Accepté | 2026-10-26 |
| [ADR-0058](ADR-0058-observation-et-constat.md) | Structure de l'observation et du constat | Accepté | 2026-10-26 |
| [ADR-0059](ADR-0059-rapport-et-couverture.md) | Structure du rapport et de la couverture | Accepté | 2026-10-26 |
| [ADR-0060](ADR-0060-resultats-d-un-module-en-erreur.md) | Résultats d'un module en erreur : écartés | Accepté | 2026-10-26 |
| [ADR-0061](ADR-0061-interface-d-un-module.md) | Interface d'un module : une fonction et un contexte | Accepté | 2026-10-26 |
| [ADR-0062](ADR-0062-message-de-fin-de-module.md) | Message « module » : fin de chaque module dans le protocole | Accepté | 2026-10-26 |
| [ADR-0063](ADR-0063-desactivation-et-liste-des-modules.md) | Désactivation des modules et liste en ligne de commande | Accepté | 2026-10-26 |
| [ADR-0064](ADR-0064-manifeste-des-modules.md) | Manifeste des modules : contenu, validation, ordre d'exécution | Accepté | 2026-10-26 |
| [ADR-0065](ADR-0065-lancement-et-reception.md) | Lancement du processus de travail et réception de ses messages | Accepté | 2026-10-26 |
| [ADR-0066](ADR-0066-licence-mit-abandonnee.md) | Passage à la licence MIT | Abandonné | 2026-10-26 |
| [ADR-0067](ADR-0067-fichier-licence-et-declaration.md) | Fichier LICENSE et déclaration de licence du paquet | Accepté | 2026-10-27 |
| [ADR-0068](ADR-0068-numerotation-des-versions.md) | Numérotation des versions publiées | Accepté | 2026-10-27 |
| [ADR-0069](ADR-0069-controles-de-la-publication.md) | Contrôles de la publication : étiquette sur `detector`, pré-version marquée | Accepté | 2026-10-27 |
| [ADR-0070](ADR-0070-identification-du-format.md) | Identification du format par le contenu : vocabulaire, signatures, fin logique | Accepté | 2026-10-27 |
| [ADR-0071](ADR-0071-fichiers-polyglottes.md) | Fichiers polyglottes : chaque format reconnu est analysé | Accepté | 2026-10-27 |
| [ADR-0072](ADR-0072-signalements-de-l-identification.md) | Signalements de l'identification : dans la rubrique Identification | Accepté | 2026-10-27 |
| [ADR-0073](ADR-0073-resultat-et-resume-avant-le-rapport.md) | Avant le rapport : résultat d'analyse et résumé sans donnée identifiante | Accepté | 2026-10-27 |
| [ADR-0074](ADR-0074-texte-colle-reporte.md) | Texte collé : reporté à T80 | Accepté | 2026-10-27 |
| [ADR-0075](ADR-0075-soumission-et-refus.md) | Soumission : ouverture, empreinte vérifiée en fin d'analyse, refus, codes de sortie | Accepté | 2026-10-27 |
| [ADR-0076](ADR-0076-limites-comptees-et-limites-du-systeme.md) | Limites comptées et limites du système : un budget mixte | Accepté | 2026-10-27 |
| [ADR-0077](ADR-0077-valeurs-des-limites.md) | Valeurs des limites : modérées, fixes en V1, refus « hors limites » | Accepté | 2026-10-27 |
| [ADR-0078](ADR-0078-budget-d-un-module-et-raisons.md) | Budget d'un module et raisons des dépassements | Proposé | 2026-10-27 |
| [ADR-0079](ADR-0079-restrictions-sous-linux.md) | Restrictions sous Linux : Landlock sans règle, liste de refus seccomp | Proposé | 2026-10-27 |
| [ADR-0080](ADR-0080-restrictions-sous-macos.md) | Restrictions sous macOS : profil Seatbelt, mémoire surveillée par le principal | Proposé | 2026-10-27 |
| [ADR-0081](ADR-0081-restrictions-sous-windows.md) | Restrictions sous Windows : Job Object posé par le travail, intégrité basse | Proposé | 2026-10-27 |
| [ADR-0082](ADR-0082-fuzzing-par-hypothesis.md) | Fuzzing des analyseurs par Hypothesis | Accepté | 2026-10-27 |
| [ADR-0083](ADR-0083-verification-de-l-isolation.md) | Vérification de l'isolation : depuis un module, et code restreint hors de la couverture | Proposé | 2026-10-27 |
