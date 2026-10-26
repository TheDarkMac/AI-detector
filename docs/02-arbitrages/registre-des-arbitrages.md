# Registre des arbitrages

> Statut : **v1.4** ; v1.0 mergée avec T02, v1.1 avec T03, v1.2 avec T04, v1.3 avec T10, v1.4 proposée dans la PR de T11. Document vivant : toute modification est inscrite à l'historique (§7).
> Sources : [cahier des charges v0.1](../00-cahier-des-charges/cahier-des-charges-v0.1.md), §10 ; [analyse critique](../01-analyse/analyse-critique-cdc-v0.1.md), §6 et §8.
> Tâche : T02. Date de rédaction : 2026-10-26.

## 1. Objet

Ce registre fait le point, pour chaque point ouvert, de ce qui a été tranché, par quel ADR, et de ce qui est reporté, à quelle tâche et pourquoi. Il tient lieu des cases à cocher du §10 du cahier, qui n'est pas modifié dans le dépôt (document source).

### Méthode

1. Les points ouverts du §10 du cahier et du §6 de l'analyse ont été regroupés en 16 questions, posées à TheDarkMac en quatre lots, avec deux à quatre options chacune et une recommandation de l'assistant.
2. Quinze questions étaient à choix unique : TheDarkMac a suivi la recommandation pour quatorze d'entre elles ; pour les services tiers, il a retenu l'option « optionnels » au lieu de « exclus » (ADR-0017). La seizième, à choix multiple, proposait d'adopter quatre propositions de l'analyse : il les a toutes retenues (ADR-0021 à ADR-0024).
3. Chaque choix a donné un ADR. Les **raisons** écrites dans les ADR sont celles présentées avec les options ; TheDarkMac n'en a pas donné d'autres.
4. Le statut V1 des tâches de restitution et de qualité (P9, P10) n'a pas fait l'objet d'une question ; l'assistant l'a déduit des NF et des livrables du §9, et le soumet dans la PR (ADR-0012).
5. Les points qui dépendent d'une mesure, d'une tâche ultérieure ou de l'auteur du cahier sont **reportés**, avec leur raison. Reporter est aussi un arbitrage : il est soumis à TheDarkMac dans la PR.

## 2. Points ouverts du §10 du cahier

Statuts : **Tranché** (ADR cité), **Reporté** (tâche citée), **Non tranché** (en attente d'une information).

### Produit

| Point | Statut | Décision ou raison du report | Référence |
| --- | --- | --- | --- |
| Nom du projet | Tranché (T10) | Voight-Kampff ; paquet PyPI `voight-kampff-forensics`, import `voight_kampff`, commandes `voight-kampff` et `vk`. Le nom de travail « AI-detector » promettait une détection que l'outil ne fait pas seul (ADR-0008, NF-14). Réservation sur PyPI par une première publication, qui attend le fichier `LICENSE` (ADR-0011). | ADR-0045 |
| Public cible prioritaire | Tranché | Journalistes et vérificateurs ; juristes en second | ADR-0009 |
| Mode de distribution | Tranché | Ligne de commande et bibliothèque | ADR-0010 |
| Modèle économique et licence | Tranché | Libre et gratuit, Apache-2.0 | ADR-0011 |
| Langues | Tranché | Français en V1, textes traduisibles | ADR-0020 |
| Périmètre de la V1 | Tranché (provisoire) | Socle, métadonnées, C2PA, structure PDF, JPEG, texte réduit | ADR-0012, ADR-0026 |
| Place du module texte | Tranché | F-73 et F-71 seulement | ADR-0013 |
| Lots et flux | Tranché | Lots simples en V1 ; flux hors périmètre | ADR-0015 |
| Validation du besoin | Tranché | Recueil d'avis sur prototype après T30 | ADR-0026 |
| Analyse groupée d'une affaire | Tranché | Candidate V2 | ADR-0015 |

### Principe « sans IA »

| Point | Statut | Décision ou raison du report | Référence |
| --- | --- | --- | --- |
| Frontière exacte | Tranché | Seuils calibrés admis sur un corpus séparé ; aucun modèle appris | ADR-0016 |
| Services tiers fondés sur l'IA | Tranché | Optionnels, désactivés par défaut, rubrique séparée ; aucun en V1 | ADR-0017 |
| Principe définitif ou contrainte de V1 | Non tranché | La question n'a pas été posée isolément ; ADR-0016 s'applique au moteur sans limite de durée tant qu'aucun ADR ne le remplace. | ADR-0016 |
| Articulation avec le cahier « Vérification assistée par IA open source » | Non tranché | Cahier compagnon indisponible (question 3 à l'auteur). L'export JSON permet un appel par un autre outil. | ADR-0017, ADR-0025 |
| Lecture des documents numérisés (F-63) | Tranché | Exclue ; analyse non menée | ADR-0017 |

### Rapport

| Point | Statut | Décision ou raison du report | Référence |
| --- | --- | --- | --- |
| Forme de la synthèse globale | Tranché | Résumé structuré, ni score ni verdict | ADR-0018 |
| Graduation et combinaison | Tranché | Niveau fixe par règle, d'après son taux mesuré ; aucune combinaison arithmétique | ADR-0018 |
| Formats d'export | Tranché | HTML autonome et JSON avec schéma | ADR-0025 |
| Accès au détail des règles (NF-19) | Tranché | Tout est public | ADR-0019 |

### Données et cadre légal

| Point | Statut | Décision ou raison du report | Référence |
| --- | --- | --- | --- |
| Traitement local ou serveur | Tranché | Local | ADR-0010 |
| Hors ligne ou connexion requise | Tranché | Hors ligne par défaut ; requêtes sortantes optionnelles | ADR-0010 |
| Conservation, compte | Tranché | Aucun compte ; l'outil ne conserve aucun fichier. Portée de NF-17 en local : journal et horodatage optionnels, aucune trace par défaut (T03) ; réalisation en T91. | ADR-0010, ADR-0030 |
| Pays visés | Tranché | Union européenne, RGPD | ADR-0020 |
| Responsabilité en cas de faux positif, mentions | Reporté | Question juridique hors du ressort de l'assistant ; l'outil ne délivre aucun verdict (ADR-0018) et ne vise pas l'enseignement (ADR-0009). Mentions rédigées en T103. | T103 |
| Anonymisation des marques (F-90) | Tranché | Hors périmètre | ADR-0014 |

### Qualité

| Point | Statut | Décision ou raison du report | Référence |
| --- | --- | --- | --- |
| Limites de taille, de durée, temps d'analyse | Reporté | Isolation tranchée en T03 (ADR-0028) ; valeurs dépendant de mesures sur le socle | T14 |
| Seuils d'acceptation | Reporté en partie | Principe tranché : taux par technique et taux par fichier, publiés avec effectif et intervalle (A-54). Valeurs fixées avant l'acceptation de la première technique. | ADR-0018, T17 |
| Constitution du corpus | Reporté en partie | Séparation calibrage / évaluation tranchée ; sources, volume et droits en T100 | ADR-0016, T100 |
| Références des modules comparatifs | Tranché | F-35 et F-64 hors V1 (références fournies par l'utilisateur, comme le prévoit le cahier) ; F-42 hors V1 faute de base de référence | ADR-0012 |
| Niveau d'accessibilité | Tranché | WCAG 2.2 AA pour le rapport HTML | ADR-0025 |
| Priorisation des exigences F et NF | Tranché | Exigences de la V1 listées dans ADR-0012 ; les autres sont des candidates | ADR-0012 |

## 3. Points ajoutés par l'analyse critique (§6)

| N° | Point | Statut | Référence |
| --- | --- | --- | --- |
| 1 | Objectif principal | Tranché | ADR-0008 |
| 2 | Définition de la preuve | Tranché | ADR-0021 |
| 3 | Hypothèses distinguées par technique | Tranché | ADR-0022 |
| 4 | Reproductibilité | Tranché | ADR-0023 |
| 5 | NF-19 contre explicabilité et licence | Tranché | ADR-0019 |
| 6 | Taux de faux positifs par fichier, combinaison | Tranché | ADR-0018 |
| 7 | Séparation calibrage / évaluation | Tranché | ADR-0016 |
| 8 | Double usage des techniques d'identification de source | Tranché : hors V1 (ADR-0014), admises en V2 avec garde-fous (ADR-0032) | ADR-0014, ADR-0032 |
| 9 | Contenu du catalogue et authentification de ses mises à jour | Intégrité tranchée en T03 : livré avec l'outil, version et empreinte au rapport (ADR-0029). Format d'écriture tranché en T04 : TOML validé par JSON Schema (ADR-0038), expressions RE2 (ADR-0039). Contenu et schéma en T15 ; ADR-0019 implique que les seuils sont publics, donc peuvent y figurer. Question 5 à l'auteur en attente. | ADR-0029, T15 |
| 10 | Niveau d'isolation de l'analyse | Tranché en T03 : processus restreint par fichier ; mécanismes par système tranchés en T04 | ADR-0028, ADR-0035, ADR-0036 |
| 11 | Recherche d'antériorité | Tranché : hors périmètre | ADR-0015 |
| 12 | Faisabilité de l'étude d'usage | Tranché : hors V1 | ADR-0026 |

Autres constats de l'analyse adressés à T02 :

| Constat | Traitement |
| --- | --- |
| A-08 Méthode de vérification | ADR-0024 (proposé dans le lot 4, retenu par TheDarkMac) |
| A-23 Matrice format × technique | Tenue dans les fiches techniques et le catalogue (ADR-0022, ADR-0012) |
| A-24 DOCX/ODT comme conteneurs | Examiné en T81 (ADR-0013) ; non tranché |
| A-35, A-38, A-40, A-41 | ADR-0012, ADR-0013 |
| A-45, A-51 | ADR-0014, ADR-0020 |

Constats de l'analyse adressés à T04 :

| Constat | Traitement |
| --- | --- |
| A-05 Reproductibilité : versions figées | ADR-0037 ; conditions récapitulées dans l'[architecture](../architecture/architecture.md) §10 |
| A-16 Bibliothèque exécutée dans le processus appelant | ADR-0036 (analyse par le processus de travail seulement) |
| A-30 Algorithme d'empreinte | ADR-0040 : SHA-256 du fichier entier |
| A-53 Niveau d'isolation | ADR-0035 : mécanismes par système |

## 4. Exigences du cahier reformulées pour le projet

Le cahier n'est pas modifié (document source). Ces reformulations s'appliquent au projet et sont soumises à l'auteur du cahier.

| Exigence | Formulation du cahier (résumée) | Formulation retenue pour le projet | ADR |
| --- | --- | --- | --- |
| NF-06 | Même fichier, même version de l'outil et du catalogue : mêmes constats | Même fichier ; mêmes versions de l'outil, du catalogue et des dépendances ; mêmes données externes ; analyse non interrompue : mêmes constats | ADR-0023 |
| NF-13 | Réglementation des pays où l'outil est proposé | Réglementation de l'Union européenne, dont le RGPD | ADR-0020 |
| NF-16 | Aucune requête sortante n'emporte le fichier | Aucune n'emporte le fichier, **son contenu** ni ses données identifiantes, sauf service tiers activé explicitement par l'utilisateur, avec son consentement pour ce fichier | ADR-0017, ADR-0033 |
| NF-17 | Journal « qui, quand » de chaque soumission, consultation, export ; horodatage fiable | Heure du poste, non certifiée, toujours au rapport ; journal (« qui » déclaratif) et horodatage RFC 3161 sur activation explicite | ADR-0030 |
| NF-01 | Analyse « de façon isolée » | Un processus restreint par fichier, sans réseau ; isolation réduite signalée au rapport | ADR-0028 |
| F-05 | Empreinte inscrite au rapport | Inscrite, mais masquée par défaut comme donnée identifiante | ADR-0031 |
| NF-19 | Accès au détail des règles selon une politique | Le détail des règles et des seuils est public ; la robustesse repose sur la combinaison des techniques et la publication de leurs limites | ADR-0019 |
| F-24 | Rechercher les filigranes à lecteur public | Point d'extension ; catalogue V1 limité aux schémas lisibles sans réseau de neurones, éventuellement vide | ADR-0012 |
| F-51 | Appliquer F-30 à F-34 aux images clés vidéo | À réécrire avant T71 : seules les analyses applicables à une image vidéo décodée | ADR-0012 |
| F-41 | Silences, plancher de bruit, respirations | Silence numérique et plancher de bruit | ADR-0012 |
| F-63 | Extraction ; lecture des documents numérisés ouverte | Couche texte native seulement ; document numérisé = analyse non menée | ADR-0017 |
| Glossaire « Preuve » | Élément vérifiable qui établit un fait | Fait établi par une vérification cryptographique ou déterministe, avec l'énoncé exact de ce qu'il établit ; reprise dans le [glossaire du projet](../glossaire.md) (T11) | ADR-0021 |
| F-81 | Directions : origine IA, retouche, authenticité, rien de particulier | Cinq directions : origine IA, retouche, **transformation**, authenticité, rien de particulier | ADR-0055 |
| Glossaire, « signature » | Désigne aussi les traces d'outils de génération (F-12) | Réservé au sens cryptographique ; « empreinte d'outil » pour F-12 (A-10) | Glossaire du projet (T11) |
| §8, couverture | Chaque exigence couverte par un test | Chaque exigence a une méthode de vérification et un résultat consigné | ADR-0024 |
| §8, étude d'usage | Critère d'acceptation | Hors V1 | ADR-0026 |
| §8, ajout | — | Taux de faux positifs par fichier mesuré et publié | ADR-0018 |

## 5. En attente de l'auteur du cahier

Les six questions du §8 de l'analyse restent sans réponse au 2026-10-26. Les décisions qui en dépendent ont été prises sans elles et seront revues par un nouvel ADR si une réponse diverge :

| Question | Décision exposée |
| --- | --- |
| 1. Objectif principal | ADR-0008 |
| 2. Schéma « chaîne d'analyse » | Aucune |
| 3. Cahier compagnon | Articulation non tranchée (§2) |
| 4. §5.4 engagement ou catalogue | ADR-0012 (traité comme catalogue de candidats) |
| 5. Seuils dans le catalogue | T15 ; ADR-0019 |
| 6. Source de la date du 2 décembre 2026 | Aucune |

## 6. Effets sur les autres documents

- [Découpage](../00-plan/decoupage-taches.md) v0.6 : statut V1, V2 ou hors V1 de chaque tâche ; T105 ajoutée ; T31, T90, T95 redéfinies.
- [Analyse critique](../01-analyse/analyse-critique-cdc-v0.1.md) : renvoi vers ce registre.
- [Modèle de menace](../modele-de-menace/modele-de-menace.md) (T03) : points 8, 9 et 10 du §3, portée de NF-17 ; reformulations de NF-01, NF-16, NF-17 et F-05 au §4 ; découpage v0.7.
- [Architecture](../architecture/architecture.md) (T04) : points 9 et 10 du §3, nom du projet (§2), constats adressés à T04 (§3) ; découpage v0.8.
- T10 : nom du projet tranché (§2, ADR-0045) ; architecture v1.1.
- T11 : F-81 et glossaire reformulés (§4, ADR-0055) ; [modèle de données](../modele-de-donnees/modele-de-donnees.md) et [glossaire du projet](../glossaire.md) créés ; architecture v1.2, découpage v0.10.

## 7. Historique

| Date | Version | Modification | Origine |
| --- | --- | --- | --- |
| 2026-10-26 | 1.0 | Création | T02 |
| 2026-10-26 | 1.1 | Arbitrages de T03 : conservation et limites (§2), points 8 à 10 (§3), reformulations de NF-01, NF-16, NF-17, F-05 (§4), effets (§6) | T03 |
| 2026-10-26 | 1.2 | Choix de T04 : nom du projet désormais nécessaire avant T10 (§2), points 9 et 10, constats adressés à T04 (§3), effets (§6) | T04 |
| 2026-10-26 | 1.3 | Nom du projet tranché : Voight-Kampff (§2, ADR-0045) ; effets (§6) | T10 |
| 2026-10-26 | 1.4 | Reformulations de F-81 et du glossaire (§4, ADR-0055) ; effets (§6) | T11 |
