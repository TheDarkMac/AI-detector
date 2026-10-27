# ADR-0013 — Module texte réduit aux contrôles déterministes

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : F-70 à F-73, NF-16 ; constats A-28, A-41, A-42

## Contexte

Le cahier reconnaît que le module texte est « le moins fiable sans IA » (§10). La stylométrie (F-70) n'a pas de seuil défendable sans texte de référence et pénalise les auteurs qui écrivent dans une langue seconde (A-41) ; la vérification des références (F-72) envoie le contenu d'une bibliographie à des bases externes (A-42).

## Options envisagées

### Option A — F-73 et F-71 seulement

- Avantages : deux contrôles déterministes (caractères invisibles, homoglyphes ; historique d'édition DOCX/ODT) ; aucune requête sortante.
- Inconvénients : aucune mesure du style ; le texte collé ne reçoit que F-73.

### Option B — Aucun module texte en V1

- Avantages : V1 plus courte.
- Inconvénients : perd deux contrôles fiables et peu coûteux.

### Option C — Option A, plus F-70 en information neutre

- Avantages : donne des mesures au lecteur.
- Inconvénients : des chiffres de style seront lus comme des indices, quelle que soit leur catégorie ; biais contre les auteurs en langue seconde.

## Décision

En V1, le module texte comprend **F-73** (T80) et **F-71** (T81, absence d'historique = information neutre). **F-70** et **F-72** sont hors V1.

## Raisons

- Option A retenue : seuls ces contrôles donnent un résultat vérifiable sans modèle.
- Option B écartée : coût faible pour un apport réel.
- Option C écartée : risque de mauvaise lecture supérieur à l'apport (A-41).
- F-72 écartée de la V1 : requêtes sortantes portant sur le contenu (A-42), contraires au fonctionnement hors ligne par défaut (ADR-0010) ; une référence introuvable n'est d'ailleurs qu'un indice faible.

## Conséquences

- Le profil enseignant n'est pas visé (ADR-0009).
- Si F-70 revient, ce sera seulement en comparaison à des textes de référence fournis par l'utilisateur ou en information neutre, par un nouvel ADR.
- Si F-72 revient, NF-16 devra couvrir le contenu, pas seulement les données identifiantes (A-42), et la fonction sera désactivable.
- Les métadonnées DOCX et ODT restent lues en V1 (T21). L'extension de F-71 aux modifications suivies et l'extraction des images embarquées (A-24) seront examinées en T81.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
| 2026-10-27 | Renvoi : texte collé reporté à T80 par ADR-0074 (T13) |
