# ADR-0171 — Liste de confiance : chargement par P1, configuration de P2, rubrique Versions, liste fournie

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur proposition de l'assistant non posée en question pendant T30, validée pendant la revue de la PR de T30
- **Tâche** : T30
- **Exigences liées** : F-21, NF-06 ; ES-09 ; ADR-0023, ADR-0029, ADR-0059, ADR-0086, ADR-0088, ADR-0112

## Contexte

ADR-0023 et ADR-0059 prévoyaient la liste de confiance parmi les données externes du rapport ; ES-09 demande qu'elle soit validée au chargement, sa version et son empreinte au rapport, et qu'une liste fournie soit signalée.

## Options envisagées

### Option A — Comme le catalogue

Dossier (`confiance.toml`, `signataires.pem`, `horodatage.pem` facultatif), chargé et validé par P1 avant toute lecture, empreinte calculée comme celle du catalogue, ancres remises à P2 dans la configuration ; `Versions.confiance` (nom, version, date, empreinte, fournie) ; `--confiance DOSSIER` et `analyser(confiance=...)`.

- Avantages : mêmes garanties et même procédure que le catalogue.
- Inconvénients : schéma du rapport et des messages changés.

### Option B — Liste lue par P2 dans le paquet

- Avantages : rien à transmettre.
- Inconvénients : aucune validation dans P1 ; liste fournie impossible.

## Décision

Option A ; `VERSION_SCHEMA` 0.5.0. P1 valide l'en-tête par son schéma et chaque fichier PEM ligne à ligne : ASCII, texte imprimable hors des blocs, blocs `CERTIFICATE` seuls, base64 d'une structure DER ; 4 Mio et 1 024 certificats par fichier au plus. Les certificats eux-mêmes ne sont décodés que par c2pa-rs.

## Raisons

- A retenue : ES-09 et ADR-0086 appliqués à l'identique.
- B écartée : contraire à ES-09.
- Décodage X.509 laissé à c2pa-rs : P1 n'a pas de lecteur X.509, et en ajouter un ferait deux lecteurs qui pourraient diverger.

## Conséquences

- c2pa-rs ignore sans erreur un bloc DER qui n'est pas un certificat (essai) : un signataire qu'il devait reconnaître est « hors liste ». Limite inscrite à la fiche.
- Changer de liste change les conditions de la garantie de reproductibilité (`vk --comparer`).
- La liste est chargée et inscrite même quand le module c2pa est désactivé.
- Le banc n'inscrit pas la liste : aucune règle C2PA n'y est mesurée (A-55).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Validé par TheDarkMac pendant la revue de la PR de T30 (« Oui, les cinq ») : statut « Accepté » |
