"""Voight-Kampff : analyse de provenance et d'intégrité de fichiers.

L'outil relève les preuves et les indices de génération ou de retouche, sans
modèle d'IA embarqué, et ne délivre aucun verdict certain (ADR-0008, ADR-0018).

L'interface publique de la bibliothèque n'exposera que l'analyse par un
processus de travail isolé (ADR-0036, ES-17) ; elle est construite à partir de
T11 et T12.
"""

from importlib.metadata import version

__all__ = ["__version__"]

__version__: str = version("voight-kampff-forensics")
