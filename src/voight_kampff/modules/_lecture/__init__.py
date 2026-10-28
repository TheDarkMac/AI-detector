"""Lecteurs de structure communs aux modules de métadonnées (ADR-0043, ADR-0114).

Écrits par le projet, en Python pur, sans bibliothèque tierce : la bibliothèque standard
suffit, expat compris pour le XML de XMP (ADR-0116). Ils ne sont importés que par les modules,
donc seulement dans le processus de travail ; ce dossier n'a pas de manifeste et n'est pas un
module (ADR-0064).

Chaque lecteur reçoit le contexte du module : il lit le fichier par lui, compte ses objets et son
imbrication contre le budget du module (ADR-0078). Un fichier malformé n'y lève jamais
d'exception : le lecteur s'arrête et le dit, et le module en fait une analyse non menée.
"""
