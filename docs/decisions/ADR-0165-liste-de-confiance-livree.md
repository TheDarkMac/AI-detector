# ADR-0165 — Liste de confiance livrée : C2PA Trust List et C2PA TSA Trust List

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T30
- **Tâche** : T30
- **Exigences liées** : F-21, F-22 ; ES-09 ; ADR-0021, ADR-0029, ADR-0038

## Contexte

F-22 distingue une signature valide d'une signature valide « hors liste de confiance » : il faut une liste. Le 2026-11-14 :

- la C2PA publie la C2PA Trust List (signataires des produits de son programme de conformité) et la C2PA TSA Trust List (autorités d'horodatage), dans `c2pa-org/conformance-public`, en PEM et en JSON (format LoTE), sous licence CC-BY 4.0 ; séquence 4 des deux, émises le 2026-11-04, prochaine émission annoncée le 2027-02-02 ; 33 et 24 certificats ;
- la liste intérimaire du CAI (ITL) est figée depuis le 2026-01-01 ; la documentation de la C2PA admet qu'un vérificateur la consulte pendant la transition, à condition de distinguer les signataires des deux listes.

## Options envisagées

### Option A — Liste officielle et liste TSA

- Avantages : la liste que la C2PA désigne comme référence ; un seul niveau de confiance à expliquer.
- Inconvénients : des contenus signés sous la seule ITL apparaissent « hors liste ».

### Option B — Liste officielle et ITL, distinguées

- Avantages : reconnaît les contenus signés pendant la période intérimaire.
- Inconvénients : un état de plus au rapport, une liste figée à suivre.

### Option C — Aucune liste livrée

- Avantages : aucun choix de confiance fait par le projet.
- Inconvénients : toute signature est « hors liste » sans démarche de l'utilisateur.

## Décision

Option A. `donnees/confiance/` contient `signataires.pem` et `horodatage.pem`, copies exactes de `C2PA-TRUST-LIST.pem` et `C2PA-TSA-TRUST-LIST.pem` au commit `a95f2c4e4b` (SHA-256 vérifiés par un test), et `confiance.toml` : nom, séquence, dates, source, licence et attribution. Une liste fournie par l'utilisateur la remplace (ADR-0171).

## Raisons

- A retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : la C2PA encourage à quitter l'ITL ; un utilisateur qui en a besoin la fournit lui-même.
- C écartée : rend la distinction de F-22 inutile par défaut.
- Format publié gardé (ADR-0038) : PEM, que c2pa-rs lit tel quel, lignes « Subject » comprises (essai).

## Conséquences

- La liste vieillit avec l'outil : sa version et sa date sont au rapport ; une mise à jour change l'empreinte, donc les conditions de reproductibilité (ADR-0112).
- La procédure de mise à jour est dans la fiche `provenance-c2pa`.
- Un signataire reconnu par la seule ITL est « hors liste » : la limite figure dans les règles.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (choix de TheDarkMac) |
