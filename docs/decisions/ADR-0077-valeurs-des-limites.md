# ADR-0077 — Valeurs des limites : modérées, fixes en V1, refus « hors limites »

- **Statut** : Accepté
- **Date** : 2026-10-27
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant (deux questions)
- **Tâche** : T14
- **Exigences liées** : F-04, NF-02, NF-08, ES-03 ; ADR-0012, ADR-0035, ADR-0065, ADR-0075, ADR-0076

## Contexte

T12 a posé des valeurs provisoires (ADR-0065) : délai de 60 s, tailles des messages. F-04 demande de refuser un fichier « hors limites » avec un message explicite, ce que T13 a laissé à T14 (ADR-0075). Restent à fixer la taille d'entrée, la mémoire du processus de travail et le délai, et à dire si l'utilisateur peut les changer. Le périmètre de la V1 (ADR-0012) : images, PDF, documents bureautiques, texte.

## Options envisagées

Valeurs (taille d'entrée, mémoire, délai par fichier) :

### Option A — Modérées : 1 Gio, 2 Gio, 120 s

- Avantages : large pour les formats de la V1, sans laisser un fichier occuper un poste ordinaire.
- Inconvénients : un très gros PDF numérisé peut être refusé.

### Option B — Strictes : 256 Mio, 1 Gio, 60 s

- Avantages : charge du poste plus faible.
- Inconvénients : plus de refus « hors limites » sur les gros PDF.

### Option C — Larges : 4 Gio, 8 Gio, 600 s

- Avantages : presque aucun refus.
- Inconvénients : une bombe de décompression peut occuper le poste longtemps.

Réglage par l'utilisateur :

### Option D — Fixes en V1

- Avantages : comportement identique partout, rapport plus simple à reproduire.
- Inconvénients : aucun recours pour un fichier juste au-dessus d'une limite.

### Option E — Réglables à la baisse seulement

- Avantages : utile sur un serveur ou pour un lot.
- Inconvénients : une option de plus, et des rapports qui dépendent d'elle.

### Option F — Réglables librement

- Avantages : un fichier hors limites peut être analysé.
- Inconvénients : le rapport doit inscrire les limites employées ; un réglage trop large expose le poste.

## Décision

Options A et D. Valeurs dans `src/voight_kampff/_limites.py`, lues par les deux processus :

| Limite | Valeur | Appliquée par |
| --- | --- | --- |
| Taille d'un fichier soumis | 1 Gio | Processus principal, avant toute lecture (F-04) |
| Mémoire du processus de travail | 2 Gio | Système (Linux, Windows), surveillance du principal (macOS) |
| Délai d'une analyse | 120 s, durée écoulée | Processus principal |
| Temps processeur du processus de travail | 120 s | Système |
| Attente de la fin du travail | 5 s | Processus principal |
| Ligne, sortie, configuration, lecture par un module | 1 Mio, 64 Mio, 16 Mio, 16 Mio | Inchangées depuis ADR-0065, désormais fixées |

Les valeurs comptées du budget d'un module sont fixées par [ADR-0078](ADR-0078-budget-d-un-module-et-raisons.md).

Un fichier de plus de 1 Gio est refusé avec le motif `hors_limites` : « fichier trop volumineux : l'outil analyse au plus 1 Gio ». La taille annoncée par le système est contrôlée avant le hachage ; si le fichier grandit pendant le hachage, la lecture s'arrête au bloc qui dépasse, et le refus est le même.

## Raisons

- Option A retenue : les images et documents de la V1 restent loin de 1 Gio, et 2 Gio laissent la place de décoder une grande image.
- Option B écartée : trop de refus pour un gain de charge faible.
- Option C écartée : elle laisse une bombe occuper le poste dix minutes.
- Option D retenue : la reproductibilité (ADR-0023) suppose les mêmes limites ; un réglage pourra venir par un nouvel ADR, avec les limites inscrites au rapport.
- Options E et F écartées pour la V1 : chacune ajoute au rapport une variable dont dépend le résultat.
- Valeurs fixées dans le code et non envoyées par la configuration : le processus de travail les applique avant de recevoir quoi que ce soit (ADR-0036). ADR-0065 prévoyait d'ajouter les limites à la configuration : c'est inutile.
- Refus avant toute lecture : ni hachage de plusieurs gigaoctets, ni lancement du processus de travail.

## Conséquences

- `MotifRefus.HORS_LIMITES` s'ajoute aux refus d'ADR-0075 ; code de sortie 1, comme les autres refus.
- Un changement de valeur change le comportement de l'outil : il passe par un nouvel ADR et figure dans les notes de version.
- Le délai de 120 s inclut la validation des messages par le processus principal : un module très bavard en consomme une part (journal de T14).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création |
