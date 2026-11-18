"""Voight-Kampff : analyse de provenance et d'intégrité de fichiers.

L'outil relève les preuves et les indices de génération ou de retouche, sans
modèle d'IA embarqué, et ne délivre aucun verdict certain (ADR-0008, ADR-0018).

L'interface publique de la bibliothèque n'expose que l'analyse par un processus
de travail isolé (ADR-0036, ES-17) : :func:`analyser` pour un fichier,
:func:`analyser_texte` pour un texte collé (ADR-0233), qui rendent une
:class:`Analyse` ou lèvent :class:`AnalyseRefusee` (ADR-0073) ; et l'export de son
rapport, masqué par défaut : :func:`exporter_json`, :func:`exporter_html`, dont
``reveler`` nomme les :class:`CategorieIdentifiante` à montrer (ADR-0097).
"""

from importlib.metadata import version

from voight_kampff.analyse import Analyse, AnalyseRefusee, MotifRefus, analyser, analyser_texte
from voight_kampff.rapport.export import exporter_html, exporter_json
from voight_kampff.rapport.modele import CategorieIdentifiante

__all__ = [
    "Analyse",
    "AnalyseRefusee",
    "CategorieIdentifiante",
    "MotifRefus",
    "__version__",
    "analyser",
    "analyser_texte",
    "exporter_html",
    "exporter_json",
]

__version__: str = version("voight-kampff-forensics")
