"""Voight-Kampff : analyse de provenance et d'intégrité de fichiers.

L'outil relève les preuves et les indices de génération ou de retouche, sans
modèle d'IA embarqué, et ne délivre aucun verdict certain (ADR-0008, ADR-0018).

L'interface publique de la bibliothèque n'expose que l'analyse par un processus
de travail isolé (ADR-0036, ES-17) : :func:`analyser`, qui rend une
:class:`Analyse` ou lève :class:`AnalyseRefusee` (ADR-0073).
"""

from importlib.metadata import version

from voight_kampff.analyse import Analyse, AnalyseRefusee, MotifRefus, analyser

__all__ = ["Analyse", "AnalyseRefusee", "MotifRefus", "__version__", "analyser"]

__version__: str = version("voight-kampff-forensics")
