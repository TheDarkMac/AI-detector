# Données personnelles : analyse des traitements au regard du RGPD

> Statut : **v1.0**, proposée dans la PR de T92. Document vivant : toute tâche qui ajoute un traitement (une écriture, une donnée gardée, une requête sortante) met à jour le §4 dans sa PR et l'inscrit à l'historique (§7).

NF-13, reformulée par [ADR-0020](../decisions/ADR-0020-langue-et-cadre-legal.md) : l'outil respecte la réglementation de l'Union européenne sur les données personnelles, le règlement (UE) 2016/679 (RGPD). Elle se vérifie par analyse ([ADR-0024](../decisions/ADR-0024-methode-de-verification.md)) : ce document recense ce que l'outil fait des données personnelles et le confronte aux principes du règlement ([ADR-0267](../decisions/ADR-0267-analyse-des-traitements-rgpd.md)). Les mentions destinées à l'utilisateur sont à T103.

**Ce document n'est pas un avis juridique.** Il décrit le comportement de l'outil, vérifié par ses tests ; la qualification juridique des rôles et la conformité d'un usage donné ne sont pas établies ici (ADR-0020).

## 1. Périmètre

| Élément | Valeur |
| --- | --- |
| Version examinée | Branche `detector` après T92 (2026-11-25) : ligne de commande `vk` et bibliothèque, 25 modules, catalogue 0.20.0, schémas 0.13.0 |
| Mode de fonctionnement | Local, sans compte ni service, hors ligne par défaut ([ADR-0010](../decisions/ADR-0010-distribution-et-traitement-local.md)) |
| Hors périmètre | Interface web locale (après la V1) ; requêtes de vérification des certificats C2PA RS-01 et RS-02 (complément de T30, non livré) ; corpus d'évaluation du banc (T100) |

## 2. Rôles

- **Le projet** distribue un logiciel. Rien ne lui parvient : ni fichier, ni rapport, ni journal, ni télémétrie, ni compte. Il ne traite donc aucune donnée pour le compte de l'utilisateur, et ne détermine pas pourquoi un fichier est analysé.
- **L'utilisateur** (journaliste, vérificateur, juriste, ADR-0009) choisit les fichiers, la raison de leur analyse, ce qu'il garde et à qui il le transmet. Les données personnelles que contiennent ses fichiers sont traitées à sa demande, sur son poste. Le règlement laisse aux États membres le soin de concilier la protection des données avec la liberté d'expression et d'information, traitements à des fins journalistiques compris (article 85) ; l'étendue de ces dérogations varie d'un État à l'autre.
- **L'autorité d'horodatage**, si l'utilisateur en choisit une (`--horodater URL`, RS-03) : elle reçoit une requête de son poste (§4).

## 3. Données personnelles en jeu

| Où | Données | Protection |
| --- | --- | --- |
| Fichiers analysés | Métadonnées nominatives (auteur, créateur, dernier modificateur), numéros de série d'appareils, coordonnées GPS, lieux nommés, textes libres (commentaires, descriptions) ; contenu (personnes sur une image, texte d'un document), qui peut contenir des données de catégories particulières (article 9) | L'outil n'en recherche aucune pour elle-même ; il les lit parce qu'elles sont dans le fichier |
| Résumé du terminal et rapports | Les données ci-dessus que relèvent les modules, nom du fichier, empreinte du fichier ; date de l'analyse | Chaque donnée identifiante est marquée par son module dans l'une des huit catégories d'ES-13 et masquée par défaut ; `--reveler CATEGORIE` la montre, et le rapport l'annonce en tête (ADR-0031, ADR-0093, ADR-0119, ADR-0159) ; ni chemin, ni nom de machine, ni utilisateur du système (ES-14) |
| Journal de conservation | Empreintes des fichiers soumis et des rapports, format réel, catégories levées, dates, nom déclaré par `--qui` ; aucun nom de fichier | Tenu seulement sur demande, annoncé à chaque emploi ; une empreinte suffit à qui détient l'original pour confirmer la possession (M-27, ADR-0260, ADR-0261) |
| Demande d'horodatage | Empreinte d'un rapport ; adresse IP du poste et heure de la demande, inhérentes à la connexion | Envoyée seulement sur demande, annoncée à chaque emploi (ADR-0262). Une adresse IP peut être une donnée personnelle, y compris dynamique, pour qui dispose des moyens d'identifier son titulaire (CJUE, *Breyer*, C-582/14, 19 octobre 2016) |
| Hors de l'outil | Historique du shell (lignes de commande, noms de fichier compris), défilement du terminal, mémoire écrite sur le disque par le système, copies des rapports par d'autres logiciels | Nommés par `vk --conservation`, sans promesse (ADR-0266) |

## 4. Traitements

Chaque ligne est un traitement que l'outil effectue ; le lieu et la durée sont ceux qu'affichent le bloc de fin de commande, la rubrique « Conservation des données » du rapport HTML et `vk --conservation` (NF-05, ADR-0264, ADR-0265).

| Traitement | Déclenché par | Données | Lieu | Durée | Destinataires | Vérifié par |
| --- | --- | --- | --- | --- | --- | --- |
| Analyse d'un fichier | `vk FICHIER` | Contenu entier du fichier | Lu là où il se trouve, sans copie sur le disque ni modification ; mémoire d'un processus de travail ouvert pour lui seul, privé de réseau et d'écriture quand son isolation est complète (ADR-0028) | Durée de l'analyse | Aucun | `tests/test_traces.py` (ES-15), `tests/test_isolation.py` |
| Analyse d'un texte collé | `vk --texte` | Texte lu sur l'entrée standard | Mémoire | Durée de l'analyse | Aucun | `tests/test_caracteres.py`, `tests/test_conservation_donnees.py` |
| Résumé au terminal | Toute analyse | Résultats ; données identifiantes masquées, sauf `--reveler` | Terminal de l'utilisateur | Hors de l'outil (défilement du terminal) | Aucun | `tests/test_cli.py` |
| Rapports | `--rapport DOSSIER` | Résultats ; données identifiantes masquées, sauf `--reveler` | Dossier choisi ; sous Linux et macOS, lisibles par leur seul propriétaire ; jamais écrasés (ADR-0092) | Jusqu'à leur suppression par l'utilisateur | Ceux à qui l'utilisateur les transmet | `tests/test_cli.py`, `tests/test_rapport.py` |
| Comparaison | `--comparer A B` | Deux rapports JSON | Lus là où ils se trouvent ; mémoire | Durée de la commande | Aucun | `tests/test_reproductibilite.py` |
| Journal de conservation | `--journal FICHIER` | §3 | Fichier choisi ; sous Linux et macOS, lisible par son seul propriétaire | Jusqu'à sa suppression par l'utilisateur | Aucun | `tests/test_conservation.py` |
| Horodatage | `--horodater URL` | Empreinte de chaque rapport écrit ; adresse IP et heure | Autorité choisie par l'utilisateur ; jeton écrit à côté du rapport | Politique de l'autorité, que l'outil ne connaît pas ; jeton gardé comme le rapport | L'autorité | `tests/test_conservation.py` |
| Catalogue et liste de confiance fournis | `--catalogue`, `--confiance` | Règles et certificats, aucune donnée personnelle attendue | Lus là où ils se trouvent | Durée de la commande | Aucun | `tests/test_catalogue.py`, `tests/test_confiance.py` |

Sans `--rapport`, `--journal` ni `--horodater`, une analyse n'écrit rien et n'envoie rien : seuls restent le terminal et ce qui échappe à l'outil.

## 5. Principes du règlement

| Principe | Ce que fait l'outil | Ce qui revient à l'utilisateur |
| --- | --- | --- |
| Licéité, loyauté, transparence (article 5, 1, a) | Dit où et combien de temps il garde chaque donnée (NF-05) ; ne fonde aucun traitement par lui-même | La base légale de ses traitements (article 6), l'information des personnes concernées (articles 13 et 14), selon les dérogations de l'article 85 qui s'appliquent à lui |
| Limitation des finalités (article 5, 1, b) | Un fichier ne sert qu'à l'analyse demandée : ni réutilisation, ni transmission, ni corpus constitué (NF-04) | Ne pas réemployer les rapports à une autre fin sans base légale |
| Minimisation (article 5, 1, c) | Masquage par défaut, au terminal comme dans les rapports ; journal sans noms de fichier ; horodatage d'une empreinte seulement. Les données du fichier sont toutes lues : l'analyse en a besoin | Ne lever le masquage (`--reveler`) que pour une catégorie nécessaire, et ne transmettre un rapport démasqué qu'à qui en a besoin (RR-08) |
| Exactitude (article 5, 1, d) | Reproduit les données telles qu'il les lit, sans les corriger ; une métadonnée peut être fausse, et les constats le disent (NF-14) | Ne pas tenir une métadonnée pour vraie parce qu'elle est au rapport |
| Limitation de la conservation (article 5, 1, e) | Rien gardé par défaut (ES-15) ; rapports, jetons et journal écrits sur demande, à l'emplacement choisi ; l'outil n'efface rien de lui-même | Fixer la durée de conservation des rapports et du journal, et les supprimer à son terme |
| Intégrité et confidentialité (article 5, 1, f ; article 32) | Processus de travail restreint par fichier (ADR-0028) ; aucune télémétrie ; fichiers écrits lisibles par leur seul propriétaire sous Linux et macOS ; rapports et journal non chiffrés | Protéger le poste et ses sauvegardes (chiffrement du disque, droits d'accès sous Windows) |
| Protection des données dès la conception et par défaut (article 25) | Défauts : aucune trace, aucune requête sortante, données identifiantes masquées ; chaque écart est une option explicite, annoncée à son emploi (ADR-0030, ADR-0031, ADR-0260, ADR-0262) | — |
| Transferts hors de l'Union (chapitre V, articles 44 et suivants) | Aucun par défaut ; seule l'autorité d'horodatage reçoit une requête, et c'est l'utilisateur qui la choisit | Choisir une autorité dont la localisation et la politique conviennent à son usage |
| Droits des personnes concernées (articles 15 à 22) | Le projet ne détient aucune donnée : aucune demande ne peut lui être utilement adressée ; l'outil n'a pas de fonction de recherche d'une personne dans les rapports | Répondre aux demandes sur les rapports et le journal qu'il garde |
| Registre des activités et analyse d'impact (articles 30 et 35) | Ce document décrit les traitements de l'outil (§4), à reprendre par l'utilisateur | Tenir son registre et mener, si elle est requise, l'analyse d'impact |

## 6. Ce qui reste

- **T103** : mentions destinées à l'utilisateur, tirées du §5 (colonne « Ce qui revient à l'utilisateur ») : base légale et information des personnes, durée de conservation des rapports et du journal, choix de l'autorité d'horodatage, traces hors de l'outil et comment les limiter (ADR-0266).
- **Complément de T30** : requêtes RS-01 et RS-02, à ajouter au §4 avant leur livraison.
- **Après la V1** : interface web locale, à examiner avec sa propre analyse.
- Aucune relecture par un juriste n'a été faite. Elle n'est pas prévue par le découpage ; à décider par TheDarkMac.

## 7. Historique

| Date | Version | Modification | Tâche |
| --- | --- | --- | --- |
| 2026-11-25 | 1.0 | Création | T92 |
