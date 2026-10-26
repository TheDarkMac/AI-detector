# ADR-0067 — Fichier LICENSE et déclaration de licence du paquet

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac pour la portée ; l'assistant pour la déclaration, le texte et l'absence de NOTICE, soumis dans la PR
- **Tâche** : T10 (complément)
- **Exigences liées** : §10 (modèle économique et licence) ; ADR-0011, ADR-0041, ADR-0045, ADR-0049

## Contexte

ADR-0011 fixe la licence Apache-2.0, mais le fichier `LICENSE` attendait que l'auteur du cahier des charges, @Jean, dise sous quelle licence son document, versionné dans le dépôt public (ADR-0046), peut être diffusé. Le workflow de publication refuse de publier sans `LICENSE` (T10). Le 2026-10-27, TheDarkMac rapporte l'accord de @Jean : la licence Apache-2.0 couvre aussi son cahier. Il reste à fixer la portée du fichier, la façon de déclarer la licence dans le paquet, le texte exact et l'éventuel fichier `NOTICE`.

## Options envisagées

### Portée

- **Option A — Tout le dépôt, cahier compris** *(retenue)* : possible depuis l'accord de @Jean.
- **Option B — Tout le dépôt sauf `docs/00-cahier-des-charges/`**, droits réservés à son auteur : proposée par l'assistant tant que l'accord n'était pas connu ; le paquet ne contient pas ce dossier, donc la publication n'était pas bloquée. Inconvénient : un document public sans licence, que personne ne peut réutiliser.
- **Option C — Attendre encore** : bloque la première publication, donc la réservation du nom (ADR-0045).

### Déclaration dans le paquet

- **Option D — Expression SPDX et fichier de licence (PEP 639)** *(retenue)* : `license = "Apache-2.0"` et `license-files = ["LICENSE"]` dans `pyproject.toml`. Métadonnées 2.4 : champs `License-Expression` et `License-File`, fichier copié dans `.dist-info/licenses/` du wheel et à la racine du paquet source.
- **Option E — Table `license = { file = "LICENSE" }` et classificateur `License :: OSI Approved :: Apache Software License`** : forme antérieure, dépréciée par PEP 639 ; le classificateur ne distingue pas les versions de la licence.
- **Option F — Classificateur seul** : aucun texte de licence livré avec le paquet, alors qu'Apache-2.0 (§4 a) demande de joindre une copie de la licence à toute redistribution.

### Texte

- **Option G — Texte officiel intégral**, tel que publié par la fondation Apache (<https://www.apache.org/licenses/LICENSE-2.0.txt>), annexe d'application comprise *(retenue)* : SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`, 202 lignes, identique à l'usage courant ; un outil de détection de licence le reconnaît sans ambiguïté.
- **Option H — Texte sans l'annexe** : plus court, mais s'écarte du fichier de référence sans gain.

### Fichier NOTICE

- **Option I — Aucun fichier `NOTICE`** *(retenue)* : Apache-2.0 ne l'exige pas ; le projet n'intègre aucune œuvre tierce dont la licence imposerait des mentions.
- **Option J — Fichier `NOTICE`** avec le nom du projet et de ses auteurs : toute redistribution devrait alors le reproduire (§4 d), contrainte sans contrepartie aujourd'hui.

## Décision

Le fichier `LICENSE` contient le texte officiel intégral d'Apache-2.0 et couvre tout le dépôt, cahier des charges compris. Le paquet déclare la licence par l'expression SPDX `Apache-2.0` et livre le fichier (PEP 639). Pas de fichier `NOTICE`.

## Raisons

- Option A retenue : l'accord de @Jean levait la seule réserve d'ADR-0011. Option B écartée pour cette raison ; option C, parce qu'elle retardait la réservation du nom sans motif.
- Option D retenue : forme normalisée actuelle, prise en charge par `uv_build` 0.13.5 (ADR-0049) ; PyPI affiche l'expression. Option E écartée : dépréciée, et PEP 639 autorise les outils à refuser un classificateur de licence à côté d'une expression. Option F écartée : contraire à §4 a de la licence.
- Option G retenue : texte de référence, reconnu par les outils. Option H écartée : aucun gain.
- Option I retenue : aucune mention n'est requise ; option J écartée, elle ajoute une obligation aux redistributeurs.

## Conséquences

- La construction reste reproductible (deux constructions identiques vérifiées) ; le job `paquet` de la CI vérifie la présence de `LICENSE` dans les deux paquets et le champ `License-Expression: Apache-2.0`.
- La première publication ne dépend plus que de l'éditeur de confiance PyPI et d'une étiquette de version (ADR-0041, ADR-0045).
- Si une œuvre tierce est un jour intégrée au dépôt (code copié, données), sa licence est vérifiée selon ADR-0043 et un fichier `NOTICE` est réexaminé.
- L'accord de @Jean est rapporté par TheDarkMac, sans trace écrite dans le dépôt ; à conserver de son côté.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
| 2026-10-27 | Validé par TheDarkMac pendant la revue de la PR : statut « Accepté » |
