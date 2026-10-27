# ADR-0078 — Budget d'un module et raisons des dépassements

- **Statut** : Proposé
- **Date** : 2026-10-27
- **Décideur** : l'assistant, proposition non posée en question pendant T14, soumise dans la PR de T14
- **Tâche** : T14
- **Exigences liées** : NF-02, NF-03, NF-08, ES-03, ES-04, ES-05 ; M-02, M-03, M-10 ; ADR-0023, ADR-0056, ADR-0060, ADR-0061, ADR-0065, ADR-0076, ADR-0077

## Contexte

ADR-0076 fixe le principe : ce qui se compte est compté par le moteur et reste dans la garantie de reproductibilité ; la mémoire et le temps sont des garde-fous du système, hors garantie. Il faut en tirer l'interface offerte aux modules, les valeurs comptées et les raisons portées par le rapport. Or ADR-0056 classe `limite_depassee` parmi les raisons qui interrompent l'analyse, et ADR-0065 l'emploie aussi quand le processus principal reçoit une ligne ou une sortie trop longue.

## Options envisagées

Sur le point qui demande un arbitrage, les raisons :

### Option A — Une raison de plus pour la mémoire du système

`limite_depassee` désigne une limite comptée et n'interrompt plus ; `memoire_depassee`, nouvelle, désigne la mémoire du système et interrompt. Une ligne ou une sortie trop longue reçue par le principal devient `message_invalide`.

- Avantages : chaque raison a un seul sens, et la propriété « interrompue », calculée depuis la raison (ADR-0056), reste exacte.
- Inconvénients : une raison de plus dans la liste fermée ; ADR-0056 et ADR-0065 évoluent.

### Option B — `limite_depassee` pour tout, toujours interruptive

- Avantages : aucun changement du modèle.
- Inconvénients : une limite comptée, identique partout, sortirait l'analyse de la garantie : le choix d'ADR-0076 n'aurait aucun effet dans le rapport.

### Option C — Interruption selon la présence d'un module

`limite_depassee` d'un module n'interromprait pas ; sans module, si.

- Avantages : aucune raison nouvelle.
- Inconvénients : une même raison à deux sens ; la propriété « interrompue » ne dépendrait plus de la seule raison.

## Décision

Option A, et les points suivants.

### Budget d'un module sur une partie

Tenu par son contexte (ADR-0061), remis à zéro pour chaque module et chaque partie :

| Méthode du contexte | Limite | Valeur |
| --- | --- | --- |
| Résultats envoyés (existant) | Ligne ; sortie entière, moins une réserve de 64 Kio | 1 Mio ; 64 Mio |
| `compter_decompression(compresses, decompresses)` | Octets décompressés cumulés | 512 Mio |
| | Rapport décompressés / compressés, au-delà de 16 Mio décompressés | 1000 |
| `decompresser(donnees, methode)` | Flux zlib, deflate brut ou gzip, lu par blocs de 1 Mio, chaque bloc compté | idem |
| `compter_objets(nombre)` | Objets parcourus (entrées, objets, blocs, balises) | 2²⁰ |
| `verifier_dimensions(largeur, hauteur)` | Pixels déclarés, avant tout décodage | 2²⁷ |
| `imbrication()` (bloc `with`) | Profondeur d'imbrication | 64 |

Un dépassement lève `LimiteDepassee` et marque le contexte : même si le module intercepte l'exception, ses résultats sont écartés et il est non mené pour `limite_depassee` (ADR-0060), et les autres modules continuent.

### Mémoire et temps

- `MemoryError` dans un module (Linux et Windows, où le système refuse l'allocation) : module non mené pour `memoire_depassee`, résultats écartés ; l'analyse continue avec les modules suivants, mais elle est interrompue au sens d'ADR-0023.
- Sous macOS, le principal arrête le travail au-delà de la limite (ADR-0080) : analyse interrompue pour `memoire_depassee`.
- Processus tué par sa limite de temps processeur (`SIGXCPU` sous Linux et macOS) : `delai_depasse`, comme le délai du principal. Pour le savoir, quand le flux se ferme avant la fin, le principal attend la fin du processus (au plus 5 s) et lit son code.

### Tailles du flux reçues par le principal

Le contexte refuse, avant l'envoi, toute ligne de plus de 1 Mio et toute sortie au-delà de 64 Mio : un processus de travail honnête ne les dépasse jamais. Le principal qui les reçoit tient donc un travail défaillant ou compromis : `message_invalide`, qui interrompt, au lieu de `limite_depassee` (ADR-0065).

### Version du schéma

`VERSION_SCHEMA` reste `0.1.0` : sa règle de numérotation sera fixée à la première publication du schéma (ADR-0054, T16), et T13 a déjà modifié le modèle sans la changer.

## Raisons

- Option A retenue : la seule où la raison dit à la fois ce qui s'est passé et si la garantie tient.
- Option B écartée : elle annule dans le rapport l'effet d'ADR-0076.
- Option C écartée : une raison à deux sens se lit mal, et ADR-0056 veut une propriété calculée depuis la raison seule.
- Budget par module et par partie : un module gourmand ne prive pas les suivants (NF-03), et le résultat ne dépend pas de l'ordre des modules.
- Rapport de compression contrôlé au-delà de 16 Mio seulement : un petit flux très compressible (une image unie) est normal ; une bombe ne l'est qu'en grand.
- Valeurs : 512 Mio décompressés tiennent dans 2 Gio de mémoire, même avec une copie ; 2²⁷ pixels (environ 11 600 × 11 600) font 512 Mio en RGBA ; 2²⁰ objets, comme le parcours de l'identification (ADR-0070) ; 64 niveaux suffisent aux structures de la V1.
- Décompression fournie par le moteur : les modules de T20 et T21 liront des flux deflate (PNG, ZIP, PDF) ; une fonction bornée commune évite que chacun réinvente la borne.

## Conséquences

- La liste fermée d'ADR-0056 gagne `memoire_depassee` (modèle, schéma du rapport) ; `limite_depassee` y perd la marque « interrompt ».
- ADR-0065 : les deux premières lignes de son tableau des écarts donnent désormais `message_invalide`.
- Un module qui décompresse autrement que par `decompresser` (bibliothèque tierce) déclare ses octets par `compter_decompression`, à mesure qu'ils sortent ; règle à rappeler dans la fiche de chaque module (T20, T21).
- Le principal attend au plus 5 s la fin d'un processus de travail dont le flux s'est fermé trop tôt.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-27 | Création, statut « Proposé » |
