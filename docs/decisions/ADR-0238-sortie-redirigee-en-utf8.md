# ADR-0238 — Sortie de `vk` redirigée vers un fichier ou un tube : écrite en UTF-8, quel que soit l'encodage local

- **Statut** : Accepté
- **Date** : 2026-11-18
- **Décideur** : TheDarkMac, en réponse aux deux questions posées par l'assistant au début du correctif d'ERR-0013, options recommandées retenues
- **Tâche** : correctif d'[ERR-0013](../errata/ERR-0013-sortie-redirigee-en-cp1252.md), après T80
- **Exigences liées** : ES-12 ; ADR-0096, ADR-0233

## Contexte

Python écrit `sys.stdout` et `sys.stderr` dans l'encodage local quand ils ne sont pas un terminal. Sous Windows, c'est la page de code ANSI, cp1252 pour une installation en français ou en anglais ; la console, elle, reçoit de l'UTF-8 quelle que soit la page de code (PEP 528). La sortie standard lève alors `UnicodeEncodeError` sur tout caractère que cp1252 n'a pas ; la sortie d'erreur l'écrit en échappement (`backslashreplace`, le réglage de Python pour ce flux).

Or `vk` écrit de tels caractères : la forme `⟨U+XXXX⟩` de la neutralisation (ADR-0096, U+27E8 et U+27E9), et toute valeur tirée d'un fichier ou d'un catalogue qui sort de cp1252 (nom d'un fichier en cyrillique révélé par `--reveler`, titre d'une règle d'un catalogue de l'utilisateur affiché par `--regles`). `vk doc.pdf > sortie.txt` s'arrête donc sur la première ligne qui en porte un, sans écrire la suite (ERR-0013). Le mode UTF-8 de Python ne sera actif par défaut qu'à partir de Python 3.15 (PEP 686) ; le projet prend en charge 3.12 à 3.14.

Deux choix : quoi écrire hors d'un terminal, et que faire d'un caractère que l'encodage retenu ne peut pas écrire.

## Options envisagées

### Option A — Sortie et erreur reconfigurées en UTF-8 quand elles ne sont pas un terminal

- Avantages : couvre la neutralisation et toute valeur, sans rien changer à ce qui est écrit ; la sortie redirigée est la même sous Linux, macOS et Windows ; un terminal garde son encodage.
- Inconvénients : sous Windows, un outil qui lit le tube dans la page de code locale lit mal les lettres accentuées ; `main` appelée depuis un autre programme Python reconfigure les flux de ce programme.

### Option B — UTF-8 toujours, terminal compris

- Avantages : une seule règle, sans test du terminal.
- Inconvénients : un terminal POSIX dont la locale n'est pas en UTF-8 afficherait des caractères faux ; sous Windows, la console reçoit déjà de l'UTF-8 : rien n'y est gagné.

### Option C — Encodage local gardé, caractère absent écrit en ASCII visible (`<U+27E8>`)

- Avantages : un outil de Windows qui lit la page de code locale lit juste les lettres accentuées.
- Inconvénients : une lettre cyrillique, grecque ou chinoise d'une valeur devient un code, et la forme de la neutralisation change selon le système ; un gestionnaire d'erreurs de codec à écrire et à tenir.

### Option D — Neutralisation en ASCII (`<U+XXXX>`) quand la sortie n'est pas un terminal

- Avantages : aucun changement d'encodage.
- Inconvénients : ne corrige que les caractères neutralisés ; une valeur hors de cp1252 lève toujours `UnicodeEncodeError`. Le défaut demeure.

### Option E — Rien dans le code : documenter `PYTHONUTF8=1` ou `-X utf8`

Option envisagée par l'assistant, non posée en question.

- Avantages : aucun code.
- Inconvénients : chaque utilisateur de Windows tombe d'abord sur l'erreur ; `vk`, installé comme commande, ne se lance pas avec `-X`.

### Caractère que l'UTF-8 ne peut pas écrire

Seul un substitut isolé ne s'écrit pas en UTF-8 : un nom de fichier POSIX dont les octets ne sont pas de l'UTF-8 valide, que Python garde en substituts (`surrogateescape`).

- `backslashreplace` : le caractère s'écrit `\udcXX`, visible ; `vk` ne s'arrête jamais sur lui. Réglage que Python applique déjà à la sortie d'erreur.
- `strict` : le réglage par défaut de la sortie standard ; un substitut isolé lève toujours une exception.

## Décision

Option A, avec `backslashreplace`.

- Au début de `main`, avant la lecture des arguments, chacun de `sys.stdout` et `sys.stderr` qui est un `io.TextIOWrapper` et n'est pas un terminal (`isatty()` faux) est reconfiguré : `encoding="utf-8"`, `errors="backslashreplace"`.
- Un terminal, ou un flux qu'un programme appelant a remplacé par un autre type d'objet, est laissé tel quel.
- Les rapports HTML et JSON s'écrivent déjà en UTF-8 (ADR-0092) ; ils ne changent pas. La neutralisation (ADR-0096) non plus : elle s'écrit toujours `⟨U+XXXX⟩`.

## Raisons

- Option A retenue : la seule qui écrive toute valeur sans la changer ni s'arrêter, et qui laisse le terminal tel qu'il est.
- Option B écartée : elle n'apporte rien sous Windows et fausse l'affichage d'un terminal POSIX qui n'est pas en UTF-8.
- Option C écartée : elle change ce qu'un vérificateur lit (une écriture devient une suite de codes) et rend la sortie différente d'un système à l'autre.
- Option D écartée : elle ne corrige qu'une partie du défaut.
- Option E écartée : elle laisse le défaut à chaque utilisateur, et ne vaut pas pour la commande installée.
- `backslashreplace` retenu : un analyseur de provenance ne doit pas s'arrêter sur un nom de fichier ; l'échappement reste visible, et ne peut pas passer pour un autre caractère.

## Conséquences

- `vk … > sortie.txt` et `vk … | outil` écrivent de l'UTF-8 sur tous les systèmes. Sous `cmd.exe`, le fichier reçoit ces octets tels quels.
- Sous PowerShell, la sortie d'une commande externe est lue par PowerShell avant d'être écrite ou passée à la suite : la page de code qu'il emploie pour la lire, et le réglage à donner pour lire de l'UTF-8, sont à vérifier pour la documentation utilisateur (T103), avec la valeur par défaut de `$OutputEncoding` déjà renvoyée à T103 par ADR-0233.
- `main` reconfigure les flux du processus qui l'appelle quand ils ne sont pas un terminal : elle reste le point d'entrée de la commande ; la bibliothèque s'emploie par `analyser` et `analyser_texte`.
- Le test de `vk --texte` de T80 n'a plus besoin de `-X utf8` (retiré) ; `test_vrai_processus_sortie_redirigee_sous_un_encodage_sans_chevrons` impose cp1252 par `PYTHONIOENCODING` sur les trois systèmes de la CI.
- À partir de Python 3.15 (PEP 686), le mode UTF-8 actif par défaut écrit déjà ces flux en UTF-8, avec le gestionnaire `surrogateescape` ; la reconfiguration n'y changera plus que ce gestionnaire, sauf avec `PYTHONUTF8=0`.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-18 | Création, statut « Accepté » : options retenues par TheDarkMac en réponse aux questions |
