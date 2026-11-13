# ADR-0124 — Lecteur PDF écrit par le projet ; `pypdf` reporté à T51 et au-delà

- **Statut** : Accepté
- **Date** : 2026-11-12
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T21
- **Exigences liées** : F-10, ES-03, ES-18, ES-19, NF-01, NF-02 ; menaces M-01, M-31 ; ADR-0043, ADR-0078, ADR-0082

## Contexte

Lire le dictionnaire d'information et le XMP d'un PDF suppose de lire sa structure (ISO 32000-2, §7) : le dernier `startxref`, la table des références croisées, classique ou en flux, les sections antérieures (`/Prev`, `/XRefStm`), les objets indirects, les flux d'objets et le filtre `FlateDecode` avec ses prédicteurs. ADR-0043 confie déjà au projet les « révisions et xref PDF » (point 1) et cite `pypdf` comme candidate pour les objets PDF de T50 à T53 (point 2), le choix final revenant à la tâche qui l'utilise (point 6). T21 est la première à lire des objets.

## Options envisagées

### Option A — Lecteur du projet, en Python pur

Module `modules/_lecture/pdf.py` : table des références croisées lue à l'ouverture, objets lus à la demande, `FlateDecode` par `Contexte.decompresser` (ADR-0078), soumis au fuzzing (ES-19).

- Avantages : aucune dépendance ; le lecteur fait exactement ce que la fiche décrit et ne répare rien en silence (ADR-0125) ; chaque objet compte dans le budget (ES-03) ; T50 (révisions incrémentales) a besoin de ce lecteur de toute façon, puisqu'il doit voir les sections une à une.
- Inconvénients : environ 800 lignes à écrire, tester et fuzzer ; couverture des fichiers malformés moindre qu'une bibliothèque mûre.

### Option B — `pypdf` dès T21

- Avantages : bibliothèque BSD-3-Clause en Python pur, mûre, déjà candidate.
- Inconvénients : en mode tolérant, elle reconstruit une table fausse en cherchant les objets dans le fichier, ce qui masque justement ce que T50 doit voir ; une dépendance de plus à examiner et à inscrire au rapport (ADR-0120) ; ses chemins internes ne comptent pas les objets parcourus dans le budget du module (ES-03) ; un analyseur tiers de plus exposé au fichier (M-01).

## Décision

Option A : la structure du PDF est lue par un lecteur écrit par le projet. `pypdf` reste candidate pour les contenus de pages et les polices (T51 à T53), où le lecteur du projet ne va pas.

## Raisons

- Option A retenue par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec l'option.
- Option B écartée : la reconstruction silencieuse contredit l'explicabilité (P-02) et prive T50 de ce qu'il cherche ; le gain de temps d'écriture ne compense pas une dépendance exposée au fichier.

## Conséquences

- `modules/_lecture/pdf.py` : objets PDF typés (`Nom`, `Ref`, `Flux`), `Document` (table, trailer complété par les sections antérieures, objets en cache, flux d'objets), décodage `FlateDecode` et prédicteurs PNG (10 à 15) et TIFF (2, 8 bits). Aucun autre filtre.
- Budget : chaque objet lu et chaque section comptent un objet ; chaque niveau d'imbrication et chaque résolution de référence, un niveau (ADR-0078) ; une lecture du fichier ne dépasse pas 16 Mio (fenêtres de 4 Kio, puis 64 Kio, 1 Mio et 16 Mio).
- Le lecteur ne charge plus rien du disque une fois le processus restreint : le codec UTF-16BE est chargé à l'import (ADR-0079, ERR-0009).
- L'architecture (§9) note que `pypdf` n'est plus prévue pour T50 ; ADR-0043 y renvoie.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-12 | Création ; option choisie par TheDarkMac au début de T21 |
