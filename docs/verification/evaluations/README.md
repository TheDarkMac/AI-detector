# Rapports d'évaluation publiés

> Statut : **v1.0**, proposée dans la PR de T101. Document vivant : toute modification est inscrite à l'historique (§5).
> Décisions : [ADR-0277](../../decisions/ADR-0277-banc-en-parallele-avec-reprise.md) à [ADR-0280](../../decisions/ADR-0280-publication-des-rapports-et-ecarts.md) ; mesures : [ADR-0104](../../decisions/ADR-0104-definition-des-mesures.md) ; bornes : [ADR-0101](../../decisions/ADR-0101-bornes-des-niveaux-et-cible.md).

Ce dossier tient les rapports du banc d'évaluation sur la partie évaluation du [corpus de référence](../corpus-de-reference.md), tels que le banc les a écrits : `evaluation.json` pour les machines, `evaluation.md` rendu depuis lui, sans retouche ([ADR-0280](../../decisions/ADR-0280-publication-des-rapports-et-ecarts.md)). Un test vérifie que le Markdown est bien celui que le banc rend du JSON, et que le corpus évalué est celui du manifeste au dépôt (`tests/test_taux_publies.py`).

## 1. Rapports

| Dossier | Corpus | Catalogue | Rôle | Fin |
| --- | --- | --- | --- | --- |
| [`reference-1.0.0-catalogue-0.20.1/`](reference-1.0.0-catalogue-0.20.1/evaluation.md) | `reference` 1.0.0, 4 467 fichiers | 0.20.1, tous les indices « faible », non évalués | Première passe : mesure qui fonde l'évaluation et le niveau de chaque indice ([ADR-0278](../../decisions/ADR-0278-evaluation-et-niveau-des-indices-au-catalogue.md)) | 2026-11-26 17:56 UTC |
| [`reference-1.0.0-catalogue-0.21.0/`](reference-1.0.0-catalogue-0.21.0/evaluation.md) | idem | 0.21.0, livré : 61 indices évalués, 38 « fort », 15 « modéré », 10 « faible » | Seconde passe : mesure de l'outil livré, citée par les fiches ([ADR-0279](../../decisions/ADR-0279-taux-ecrits-dans-les-fiches.md)) | 2026-11-27 01:11 UTC |

Les deux passes ont analysé chaque fichier deux fois, sans réseau (aucune tentative), trois fichiers à la fois ; aucun fichier n'a donné deux analyses différentes. Les taux de chaque règle sont les mêmes dans les deux passes, comme le niveau d'une règle ne change pas ses constats ; la seule différence est un PDF authentique (`pdf-0203.pdf`) interrompu au délai de 120 secondes à la première passe et non à la seconde : ce délai se mesure en temps écoulé et dépend de la charge du poste ([ADR-0277](../../decisions/ADR-0277-banc-en-parallele-avec-reprise.md)).

## 2. Ce que disent les mesures

Chiffres de la seconde passe ; chaque taux, avec son effectif et son intervalle, est dans le rapport et dans la rubrique « Taux d'erreur » de chaque [fiche](../../techniques/README.md).

- **Taux par fichier** (critère d'ADR-0018) : 8 fichiers authentiques sur 2 384 portent un indice modéré ou fort, ou une preuve, vers l'origine IA ou la retouche : 0,3 %, au plus 0,7 % avec une confiance de 95 %, sous la cible de 5 %. Ce sont huit PDF, par R-PAGESPDF-002 (sept) et R-PAGESPDF-004 (un), deux indices de retouche passés à « modéré ».
- **Preuves** : aucun faux positif.
- **Indices vers la transformation** (images, tables de quantification, double compression) : ils se déclenchent sur des photographies authentiques, jusqu'à 97 sur 825 pour R-IMAGE-004 ; leur taux fixe leur niveau, et ceux qui se déclenchent le plus restent « faible ». Une transformation ne compte pas dans le taux par fichier : elle ne dit ni génération ni retouche.
- **Générés** : 39 des 320 images déclarées générées portent au moins un constat vers l'origine IA, par une déclaration (C2PA, XMP, texte PNG) ou le filigrane dwtDct. Aucun texte, aucun DOCX, ODT ou PDF généré n'est reconnu : les techniques livrées lisent des déclarations et des marquages, que ces fichiers n'ont pas, et la stylométrie est hors de la V1 (ADR-0012).
- **Retouchés** : 9 des 43 PDF retouchés portent un indice de retouche (`pagespdf`) ; aucune retouche d'image, de son, de vidéo, de document ou de texte n'est reconnue. Les retouches du corpus sont mécaniques et ne laissent pas de déclaration (ADR-0275).
- **Non analysables** : chaque technique a sa part, au rapport ; 22 fichiers malformés sont refusés comme format non reconnu ou hors périmètre, ce qui est attendu.

Un faux négatif n'est pas un défaut de l'outil quand le fichier ne porte rien de ce que l'outil lit : l'absence de constat ne dit rien (F-14). Le taux de faux négatifs dit seulement quelle part des fichiers d'une catégorie l'outil n'aide pas à reconnaître.

## 3. Écarts

Un seul écart, dans les deux passes : `authentiques/pdf/pdf-0371.pdf`, arrêt brutal de l'analyse (`ValueError`). L'analyse produit plus de 16 visualisations (cartes ELA des images extraites, tableaux des pages et des révisions), et le processus principal la refuse à la validation (`NOMBRE_MAX_VISUALISATIONS`), au lieu d'une analyse partielle signalée comme telle. Défaut de code, à corriger dans un correctif séparé, avec son erratum, sans régler l'outil sur la partie évaluation ([ADR-0280](../../decisions/ADR-0280-publication-des-rapports-et-ecarts.md)).

## 4. Limites de la mesure

- **Vérité des générés** : déclarée par l'auteur de chaque image sur Wikimedia Commons, non vérifiée ([ADR-0273](../../decisions/ADR-0273-verite-des-originaux.md)) ; les textes générés viennent d'un seul générateur.
- **Vérité des authentiques** : un fichier versé avant le 2022-08-22, sans catégorie de génération ou de retouche, peut avoir été retouché sans le dire ; un constat sur lui compte comme faux positif.
- **Effectifs par format** : la bureautique n'a que 86 authentiques en évaluation, WebP, Ogg et FLAC moins de 150 chacun ; leurs intervalles sont larges, et la borne de Wilson en tient compte.
- **Retouches mécaniques** : faites par des scripts (ADR-0275) ; des retouches soignées relèvent de l'équipe rouge (T102).
- **Datation** : les générateurs changent ; la catégorie « Générés » est à renouveler par une nouvelle version du corpus (A-13), et toute mesure est à refaire avec elle.

## 5. Historique

| Date | Version | Modification | Tâche |
| --- | --- | --- | --- |
| 2026-11-27 | 1.0 | Création : deux passes sur le corpus `reference` 1.0.0 | T101 |
