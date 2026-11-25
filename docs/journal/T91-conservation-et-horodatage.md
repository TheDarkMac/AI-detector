# T91 — Journal de conservation et horodatage des rapports, optionnels

- **Branche** : `tache/T91-conservation-et-horodatage`
- **Dates** : 2026-11-25
- **Exigences couvertes** : NF-17, ES-16 ; NF-16 (RS-03)
- **Décisions** : ADR-0260 à ADR-0263
- **Errata** : aucun

## Objectif

Repris du [découpage](../00-plan/decoupage-taches.md) : « Journal de chaîne de conservation et horodatage fiable des rapports, optionnels, aucune trace par défaut (ADR-0030) ». ADR-0030 fixait la portée de NF-17 pour un outil local : heure du poste toujours au rapport, marquée non certifiée ; sur activation explicite, un journal chaîné, sans noms de fichier, annoncé à l'activation, « qui » déclaratif, et l'horodatage RFC 3161 de l'empreinte du rapport auprès d'une autorité choisie par l'utilisateur (RS-03). Demandé par TheDarkMac le 2026-11-25 (« t91 »).

## État initial

- PR [#45](https://github.com/TheDarkMac/AI-detector/pull/45) (T90) : les 16 vérifications vertes sur `7603bd8` (CodeRabbit ignoré) ; mergée par l'assistant le 2026-11-25 à 06:04:44 UTC après le « Oui, merge si vert » de TheDarkMac, commit de merge `d67bedf`. Lancements de push sur `d67bedf` : code 45557960985 et docs 45557961080 verts, vérifiés le 2026-11-25.
- Catalogue 0.20.0, schémas 0.13.0, 25 modules livrés. Aucun code réseau dans le paquet ; le processus de travail n'a pas de réseau (ES-17).
- Le rapport inscrivait la date de l'analyse « (UTC) », sans dire qu'elle vient de l'horloge du poste ; NF-17 et ES-16 « à venir » dans la matrice.
- Toujours en attente : voir les journaux de T90, du complément de T81, de T81 et de T80 (« Reste à faire »).

## Déroulé

1. Lecture du découpage, d'ADR-0030, ADR-0012, ADR-0040, ADR-0093, du modèle de menace (M-17, M-18, M-24 à M-28, RS-03, ES-15, ES-16), de la matrice (NF-16, NF-17, ES-15, ES-16), de `cli.py`, de l'export, de la comparaison et des schémas.
2. Quatre questions à TheDarkMac, en un lot, toutes retenues sur recommandation, sans raison supplémentaire : activation par `--journal FICHIER` à chaque commande, avertissement à chaque emploi ([ADR-0260](../decisions/ADR-0260-activation-du-journal-de-conservation.md)) ; soumissions, exports et rapports lus ([ADR-0261](../decisions/ADR-0261-contenu-et-chaine-du-journal.md)) ; un jeton par fichier de rapport ([ADR-0262](../decisions/ADR-0262-horodatage-de-chaque-fichier-de-rapport.md)) ; contenu de la réponse vérifié, non sa signature ([ADR-0263](../decisions/ADR-0263-reponse-de-l-autorite-et-date-non-certifiee.md)).
3. Branche `tache/T91-conservation-et-horodatage` créée depuis `detector` à jour (`d67bedf`).
4. Code : paquet `_conservation/` (P1 seulement) : `_der.py` (lecture et écriture DER minimales), `horodatage.py` (requête, lecture de la réponse, envoi par urllib sans redirection), `journal.py` (journal chaîné, verrou par fichier, vérification) ; schéma `journal.schema.json` ; options `--journal`, `--qui`, `--verifier-journal`, `--horodater` dans `cli.py` ; `comparaison.lire_avec_empreinte` ; date « horloge du poste, non certifiée » dans le rapport HTML et la description du schéma.
5. Essai de bout en bout contre une autorité réelle : autorité racine et autorité d'horodatage d'essai créées par OpenSSL 3.5.9 dans le dossier temporaire de la session, servies sur 127.0.0.1 par un petit serveur qui passe chaque requête à `openssl ts -reply`. `vk --journal … --qui … --rapport … --horodater http://127.0.0.1:8318/` sur `tests/donnees/ela/collage_60_92.jpg` et un fichier absent : quatre entrées (soumission, deux exports horodatés, refus), deux jetons, et `openssl ts -verify -data 1.json -in 1.json.tsr -CAfile …` comme pour `1.html` : « Verification: OK ». Puis `--comparer` journalisé, `--verifier-journal` sur le journal (cohérent, 6 entrées) et sur une copie retouchée (rompu à l'entrée 5, code 1), `--journal` sur cette copie (refusé, code 2), autorité injoignable (code 1, rapports écrits, aucun jeton).
6. Constat en essayant la retouche : la modification de la dernière entrée ne rompt pas la chaîne, qui n'a pas de suivante ; de même la suppression des dernières entrées. Limite inscrite dans ADR-0261 et dans la réponse de `--verifier-journal`.
7. Échantillon `tests/donnees/horodatage/` : requête de l'outil pour une empreinte et un nonce fixés, réponse d'OpenSSL, oracle (heure, numéro, politique) ; écrit par `generer_horodatage.py`, qui vérifie la réponse par `openssl ts -verify` et efface ses clés.
8. Tests : `tests/test_conservation.py` (DER, requête, réponse d'OpenSSL et réponses construites, refus nommés, URL, envoi par une autorité locale et refus d'une redirection, journal et ses ruptures, verrou entre deux processus, limites, ligne de commande, date non certifiée, aucune trace ni requête sans option, réponses hostiles par Hypothesis) ; `test_cli.py` : remplacement de `_preparer` mis à la nouvelle signature. Deux défauts trouvés par ces tests et corrigés avant la suite complète : une heure « AAAAMMJJHHMMSS.Z », sans chiffre après le point, était acceptée ; la taille d'un journal grossi par une autre commande n'était contrôlée qu'après la relecture de sa dernière ligne.
9. Suite complète sous coverage, en 14 minutes 55 : 3 449 tests verts, 4 ignorés (lanceur de l'environnement virtuel, cjpeg de mozjpeg absent), 1 en échec, attendu : la matrice rendue n'était pas encore régénérée. Couverture de tout le paquet à 100 %, du banc à 100 % hors une branche de `banc/matrice.py` que seul le test en échec parcourt.
10. Matrice : NF-17 et ES-16 « réalisées », RS-03 au résultat de NF-16, note d'ES-15 ; matrice régénérée (`python -m banc.matrice`), puis `test_matrice.py`, `test_conservation.py`, `test_cli.py` et `test_schemas.py` relancés (282 verts), et `banc/matrice.py` couvert à 100 %.
11. PR [#46](https://github.com/TheDarkMac/AI-detector/pull/46) ouverte vers `detector` (commits `6e7caee`, `82fee60`, `f5e253a`, `d5cc40b`).

## Problèmes rencontrés

| Problème | Cause | Résolution |
| --- | --- | --- |
| Dernière entrée modifiable sans rompre la chaîne | Propre à toute chaîne d'empreintes : rien ne suit la dernière | Limite dite par `--verifier-journal` et ADR-0261 ; horodater le journal la fermerait, non demandé |
| Heure « …. Z » acceptée | Fraction vide après le point non contrôlée | Contrôle ajouté, cas au test |
| Contrôle de taille après la relecture | Ordre des contrôles dans l'ajout | Taille contrôlée dès la lecture |
| Caractères invisibles écrits en clair dans un test | L'outil d'écriture de l'assistant écrit `​` et ` ` en caractères | Échappements rétablis (Ruff RUF001 l'a signalé) |
| Matrice rendue périmée dans la suite complète | Marqueurs d'exigence nouveaux, matrice non régénérée | Matrice mise à jour et régénérée après la suite, qui lit `docs/verification/` |
| Ruff S607 sur `openssl` dans le script de génération | Programme cherché dans le `PATH` | `shutil.which`, arrêt explicite s'il manque |

## Écarts par rapport au découpage

- « Consultation » de NF-17 : seuls les rapports lus par l'outil (`--comparer`) ; l'ouverture d'un rapport hors de l'outil n'est pas visible (ADR-0261, registre des arbitrages).
- Signature des jetons non vérifiée par l'outil (ADR-0263) : l'heure affichée est celle que l'autorité annonce, la vérification se fait par `openssl ts -verify`.
- Aucun passage sur une autorité publique : il aurait envoyé une empreinte hors du poste sans accord.

## Résultat

- `vk --journal FICHIER [--qui NOM] …` : journal chaîné des soumissions, refus, exports et rapports comparés, sans nom de fichier, annoncé à chaque emploi ; `vk --verifier-journal FICHIER` : 0, 1 ou 2.
- `vk --rapport DOSSIER --horodater URL …` : `1.html.tsr` et `1.json.tsr`, vérifiables par `openssl ts -verify`.
- Rapport HTML : date de l'analyse « horloge du poste, non certifiée ». Export JSON, catalogue et modules inchangés ; schéma publié `journal` ajouté.
- Matrice : NF-17 et ES-16 « réalisées » ; NF-16 reste « partielle » (RS-01, RS-02 au complément de T30).
- Vérification locale : suite complète (étape 9), fichiers touchés relancés (étape 10) ; Ruff, mypy et markdownlint sans erreur ; jetons vérifiés par `openssl ts -verify` (étape 5).

## Reste à faire

- T103 : expliquer ce que vaut le journal, ce qu'il révèle, ses limites (dernière entrée, réécriture entière), comment obtenir le certificat d'une autorité et vérifier un jeton.
- Vérification de la signature d'un jeton par l'outil, par exemple contre les ancres d'horodatage de la C2PA livrées : sur demande, tâche à définir.
- Horodatage du journal lui-même, s'il est demandé.
