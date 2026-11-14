# ADR-0169 — États de la vérification et vocabulaire des observations du module c2pa

- **Statut** : Proposé
- **Date** : 2026-11-14
- **Décideur** : l'assistant, choix non posé en question pendant T30, à valider pendant la revue de la PR de T30
- **Tâche** : T30
- **Exigences liées** : F-20, F-22, F-23 ; ES-13 ; A-36 ; ADR-0057, ADR-0117, ADR-0118

## Contexte

F-22 nomme cinq états ; A-36 demandait de les aligner sur la validation C2PA. c2pa-rs donne un `validation_state` (`Trusted`, `Valid`, `Invalid`), des codes de validation (succès, information, échec) pour le manifeste actif et pour les ingrédients, ou une erreur.

## Options envisagées

### Option A — Cinq états de F-22, tirés de `validation_state`, raisons par les codes C2PA

- Avantages : vocabulaire du cahier ; les codes de la spécification disent la raison sans traduction.
- Inconvénients : les codes sont en anglais.

### Option B — Codes de c2pa-rs seuls

- Avantages : aucune correspondance à tenir.
- Inconvénients : s'écarte de F-22.

## Décision

Option A. `Trusted` → `valide` ; `Valid` → `valide_hors_liste` ; `Invalid` → `invalide` ; une erreur de c2pa-rs, ou un état inconnu → `non_verifiable`, avec le genre d'erreur (`c2pa.erreur`), jamais le reste du message ; aucune donnée C2PA → `absent`. Un conteneur que c2pa-rs ne sait pas lire (variante `InvalidAsset`, « asset could not be parsed ») ne dit rien d'un manifeste : recherche non menée (`format_partiel`), sans observation. Observations nommées d'après la sortie JSON de c2pa-rs (fiche `provenance-c2pa`). Marqués identifiants : `signature_info.common_name` (nominative), `signature_info.cert_serial_number` (numéro de série), `title` et titres des ingrédients (texte libre) ; l'organisation du certificat non.

## Raisons

- A retenue : F-22 et A-36 ensemble.
- B écartée : le cahier demande ces cinq états.
- Genre seul de l'erreur : le message de c2pa-rs cite des parties du fichier (adresse d'un manifeste distant, par exemple).
- Hôte seul pour un manifeste distant : l'adresse entière peut désigner l'exemplaire (M-14).

## Conséquences

- Un PDF que c2pa-rs ne lit pas donne une technique non menée, pas un état.
- Le module `xmp` observe l'adresse entière d'un manifeste distant (`xmp.dcterms:provenance`) : masquée comme un numéro de série depuis ADR-0173.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Proposé » |
| 2026-11-14 | Renvoi : adresse d'un manifeste distant masquée dans le XMP (ADR-0173) |
