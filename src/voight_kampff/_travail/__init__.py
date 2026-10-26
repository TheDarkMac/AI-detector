"""Processus de travail : un par fichier, lancé par ``python -I -B -m voight_kampff._travail``.

Il importe les modules, se verrouille, envoie l'état de l'isolation avant de lire le moindre
octet du fichier, reçoit la configuration, puis exécute les modules et renvoie leurs résultats
en lignes JSON (ADR-0036, ADR-0062, ADR-0065).
"""
