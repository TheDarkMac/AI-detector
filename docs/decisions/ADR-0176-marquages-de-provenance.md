# ADR-0176 — Marquages recherchés : les marquages de provenance, pas les signatures de générateurs

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T31
- **Tâche** : T31
- **Exigences liées** : F-12, F-24, F-25 ; ADR-0019, ADR-0055

## Contexte

F-25 parle de « marquages recherchés », F-24 de filigranes, F-12 de signatures de générateurs. Il faut dire ce qui figure dans la liste du rapport : un résultat négatif n'est borné que si l'on sait ce que la liste contient.

## Options envisagées

### Option A — Marquages de provenance

Signaux lisibles par machine, posés exprès pour dire l'origine d'un contenu : manifeste C2PA, champ DigitalSourceType de l'IPTC, filigranes invisibles.

- Avantages : correspond au marquage « dans un format lisible par machine » de l'article 50 de l'AI Act, cité par le cahier (§1) ; liste courte et lisible ; les signatures restent des règles, avec leurs limites.
- Inconvénients : la frontière avec une signature se discute pour certains champs (un champ Software qui nomme un générateur n'est pas posé pour marquer).

### Option B — Filigranes seuls

- Inconvénients : la liste serait vide en V1 ; le C2PA ne figurerait que parmi les techniques.

### Option C — Tout, signatures de générateurs comprises

- Inconvénients : liste longue, qui recoupe les règles du catalogue et leurs constats.

## Décision

Option A. Le catalogue 0.6.0 inscrit comme recherchés le manifeste C2PA intégré (`M-C2PA`, module `c2pa`) et le type de source numérique de l'IPTC (`M-IPTC-DST`, module `xmp`).

## Raisons

- A retenue, recommandation suivie par TheDarkMac.
- B écartée : une liste vide ne borne rien, alors que l'outil recherche bel et bien deux marquages.
- C écartée : les signatures ont déjà leurs règles et leurs constats ; la liste perdrait sa lisibilité.

## Conséquences

- Un champ Software ou un bloc texte PNG qui nomme un générateur reste une règle (F-12), non un marquage ; l'[inventaire](../catalogue/inventaire-des-marquages.md) le dit (§6).
- Le DigitalSourceType déclaré dans les actions d'un manifeste C2PA relève de `M-C2PA`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (réponse de TheDarkMac à la question posée pendant T31) |
