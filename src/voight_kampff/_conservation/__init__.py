"""Chaîne de conservation, optionnelle (NF-17, ADR-0030) : journal et horodatage des rapports.

Rien de ce paquet n'est employé sans une option explicite : sans ``--journal`` ni
``--horodater``, l'outil n'écrit aucune trace et n'envoie aucune requête (ES-15, ES-16).
Seul le processus principal l'importe ; le processus de travail n'en charge rien.
"""
