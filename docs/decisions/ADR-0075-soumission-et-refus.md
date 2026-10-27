# ADR-0075 — Soumission : ouverture, empreinte vérifiée en fin d'analyse, refus, codes de sortie

- **Statut** : Proposé
- **Date** : 2026-10-27
- **Décideur** : l'assistant, soumis à TheDarkMac dans la PR de T13
- **Tâche** : T13
- **Exigences liées** : F-01, F-04, F-05, NF-03, ES-01, ES-08, ES-14 ; M-06, M-30 ; ADR-0036, ADR-0040, ADR-0059, ADR-0073

## Contexte

ES-08 : seuls les fichiers réguliers sont acceptés ; le processus de travail recalcule l'empreinte de ce qu'il a analysé, et un écart avec celle du processus principal invalide le rapport. ADR-0059 en tire qu'un rapport n'est construit que si les deux empreintes sont égales. Mais un processus de travail arrêté (délai, message invalide) n'envoie pas d'empreinte, et NF-03 veut alors un rapport partiel, pas une absence de résultat. F-04 demande de refuser un fichier hors périmètre avec un message explicite.

## Options envisagées

Sur le point qui demande un arbitrage, l'empreinte d'une analyse interrompue :

### Option A — Le principal hache de nouveau le fichier

Si le travail n'a pas envoyé d'empreinte, le principal, une fois le travail terminé, hache le fichier par le même descripteur et compare.

- Avantages : ES-08 vérifiée dans tous les cas ; le résultat partiel de NF-03 est livré quand le fichier n'a pas changé.
- Inconvénients : une lecture complète de plus, dans le cas rare d'une interruption.

### Option B — Aucun résultat sans empreinte du travail

- Avantages : lecture stricte d'ADR-0059.
- Inconvénients : contredit NF-03 ; une analyse interrompue ne livre rien, même pas ce qui a abouti.

### Option C — Résultat partiel marqué « empreinte non vérifiée »

- Avantages : aucune lecture de plus.
- Inconvénients : un état de plus dans le modèle ; un résultat peut porter sur un fichier modifié.

## Décision

Option A, dans le déroulé suivant (`_orchestration/soumission.py`) :

1. Les modules à désactiver sont vérifiés avant toute lecture (`ModuleInconnu`).
2. Ouverture unique en lecture seule, sans blocage (`O_NONBLOCK` : un tube nommé n'immobilise pas l'outil, M-30), sans terminal de contrôle ; `fstat` sur le descripteur : tout ce qui n'est pas un fichier régulier est refusé.
3. Empreinte SHA-256 et taille par ce descripteur ; un fichier vide est refusé sans lancer de processus de travail.
4. Le même descripteur est transmis au processus de travail : un lien remplacé entre-temps ne change pas le fichier analysé (M-06).
5. Le travail recalcule l'empreinte **après les modules**, sur ce qu'il a lu. Si elle manque, le principal hache de nouveau. Une empreinte différente refuse le fichier.
6. Puis : aucune partie reçue (arrêt avant l'identification), aucune partie reconnue, aucune partie du périmètre : refus.

| Motif (`MotifRefus`) | Cas |
| --- | --- |
| `illisible` | Ouverture impossible ; le message du système suit |
| `non_regulier` | Dossier, périphérique, tube |
| `vide` | Taille nulle |
| `format_inconnu` | Aucun format reconnu |
| `hors_perimetre` | Formats reconnus, aucun du périmètre ; ils sont nommés |
| `fichier_modifie` | Empreinte finale différente |
| `analyse_impossible` | Processus de travail arrêté avant l'identification ; la raison suit |

- Le message d'un refus ne cite ni le chemin ni le nom (ES-14). « Hors limites » (F-04) est laissé à T14, qui fixe les limites.
- Le nom retenu est le dernier élément du chemin ; ce que le modèle refuse (barre oblique inverse d'un nom POSIX, octets non UTF-8) est remplacé par U+FFFD.
- La date d'analyse est prise au début de la soumission, en UTC, à la seconde.
- Codes de sortie de la commande : 0 si chaque fichier a été analysé, même partiellement ; 1 si au moins un a été refusé ; 2 pour une commande invalide (option inconnue, module inconnu, comme argparse).

## Raisons

- Option A retenue : elle concilie ES-08 et NF-03 sans ajouter d'état au modèle.
- Option B écartée : un délai dépassé ne doit pas faire perdre les analyses abouties.
- Option C écartée : un résultat dont on ne sait pas s'il porte sur le fichier identifié n'a pas de valeur de preuve.
- Empreinte en fin d'analyse plutôt qu'au début dans le travail : c'est ce que les modules ont lu qui doit être identique (« vérifiée en fin d'analyse », découpage de T13).
- Arrêt avant l'identification traité en refus : sans format, aucune analyse n'a pu commencer ; le motif et la raison disent pourquoi.

## Conséquences

- ADR-0059 est précisé : un rapport n'est construit que si l'empreinte finale, du travail ou à défaut du principal, est égale à celle du début.
- T14 ajoute le refus « hors limites » et les limites de taille avant le lancement.
- La documentation utilisateur (T103) reprend les motifs de refus et les codes de sortie.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
