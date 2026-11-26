"""Journal de reprise d'une évaluation (ADR-0277).

L'évaluation du corpus de référence dure des heures : une coupure (réseau, redémarrage) ne doit
pas tout faire recommencer. Avec ``--reprise FICHIER``, le banc note chaque résultat dès qu'il
est connu, une ligne JSON par fichier, et, relancé avec le même journal, ne réanalyse que les
fichiers qui n'y sont pas.

- La première ligne décrit l'évaluation : corpus (nom, version, empreinte du manifeste), partie,
  version de l'outil et empreinte de son code, version et empreinte du catalogue, modules
  mesurés et désactivés. Un journal d'une autre évaluation est refusé : des résultats d'un autre
  code ou d'un autre catalogue ne se mêlent pas. L'empreinte du code compte parce que, dans un
  dépôt de travail, la version de l'outil ne change pas à chaque modification.
- Chaque ligne suivante est un résultat (:meth:`ResultatFichier.vers_dict`) : chemin, empreinte,
  états des techniques, constats retenus (règle, module, catégorie, direction, niveau), refus,
  arrêt brutal, écarts de reproduction. Aucun contenu de fichier ni message d'erreur (ES-15).
- Chaque ligne est écrite d'un bloc et mise sur le disque avant la suivante ; une dernière ligne
  incomplète, laissée par une coupure, est retirée à la reprise. Toute autre ligne illisible
  fait refuser le journal.

Le journal n'est pas un rapport : il reste sur le poste, à l'endroit que choisit qui lance le
banc, et n'est jamais publié. Les mesures ne viennent que du rapport écrit à la fin.
"""

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, BinaryIO, Self

import voight_kampff
from banc.corpus import Corpus, Partie
from banc.evaluation import ResultatFichier
from voight_kampff.rapport.modele import VersionCatalogue

__all__ = ["FORMAT", "Journal", "JournalInvalide", "empreinte_du_code", "entete"]

FORMAT = 1
"""Format du journal ; un journal d'un autre format est refusé."""


class JournalInvalide(ValueError):
    """Journal d'une autre évaluation, ou illisible : rien n'est analysé."""


def empreinte_du_code(paquet: Path | None = None) -> str:
    """SHA-256 des fichiers du paquet installé (code, catalogue, textes), chemins compris.

    Les processus de travail chargent ce paquet : deux évaluations d'empreintes égales ont
    analysé avec le même code. Les fichiers compilés (``__pycache__``) sont ignorés.
    """
    racine = paquet or Path(voight_kampff.__file__).parent
    empreinte = hashlib.sha256()
    for fichier in sorted(racine.rglob("*")):
        if fichier.is_file() and "__pycache__" not in fichier.parts:
            relatif = fichier.relative_to(racine).as_posix().encode("utf-8")
            contenu = fichier.read_bytes()
            empreinte.update(len(relatif).to_bytes(8, "big") + relatif)
            empreinte.update(len(contenu).to_bytes(8, "big") + contenu)
    return empreinte.hexdigest()


def entete(
    corpus: Corpus,
    partie: Partie,
    *,
    outil: str,
    catalogue: VersionCatalogue,
    modules: list[str],
    desactiver: list[str],
) -> dict[str, Any]:
    """Ce qui identifie une évaluation : deux journaux d'en-têtes égaux sont interchangeables."""
    return {
        "reprise": FORMAT,
        "corpus": {"nom": corpus.nom, "version": corpus.version, "empreinte": corpus.empreinte},
        "partie": partie.value,
        "outil": {"version": outil, "code": empreinte_du_code()},
        "catalogue": {"version": catalogue.version, "empreinte": catalogue.empreinte},
        "modules": list(modules),
        "desactiver": sorted(desactiver),
    }


def _ligne(document: Mapping[str, Any]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"


class Journal:
    """Journal ouvert : :meth:`noter` y ajoute un résultat, mis sur le disque aussitôt."""

    def __init__(self, fichier: BinaryIO, resultats: dict[str, ResultatFichier]) -> None:
        self._fichier = fichier
        self.resultats = resultats
        """Résultats déjà notés, par chemin du fichier dans le corpus."""

    @classmethod
    def ouvrir(cls, chemin: str | Path, corpus: Corpus, attendu: Mapping[str, Any]) -> Self:
        """Crée le journal, ou relit celui d'une évaluation interrompue d'en-tête ``attendu``.

        Lève :class:`JournalInvalide` si le journal est celui d'une autre évaluation, si une
        ligne autre que la dernière est illisible, ou s'il ne peut pas être ouvert.
        """
        chemin = Path(chemin)
        try:
            fichier = chemin.open("r+b") if chemin.exists() else chemin.open("x+b")
        except OSError as erreur:
            raise JournalInvalide(f"journal de reprise inutilisable ({erreur.strerror})") from None
        try:
            resultats = cls._relire(fichier, corpus, attendu)
        except JournalInvalide:
            fichier.close()
            raise
        return cls(fichier, resultats)

    @staticmethod
    def _relire(
        fichier: BinaryIO, corpus: Corpus, attendu: Mapping[str, Any]
    ) -> dict[str, ResultatFichier]:
        lignes = fichier.read().split(b"\n")
        # Après le dernier saut de ligne : vide, ou ligne interrompue par une coupure.
        fin = sum(len(ligne) + 1 for ligne in lignes[:-1])
        fichier.seek(fin)
        fichier.truncate()
        if fin == 0:
            fichier.write(_ligne(attendu))
            fichier.flush()
            os.fsync(fichier.fileno())
            return {}
        try:
            document = json.loads(lignes[0])
        except ValueError:
            raise JournalInvalide("journal de reprise illisible (ligne 1)") from None
        if document != dict(attendu):
            raise JournalInvalide(
                "journal de reprise d'une autre évaluation (corpus, partie, outil, catalogue ou "
                "modules différents)"
            )
        entrees = {entree.chemin: entree for entree in corpus.entrees}
        resultats: dict[str, ResultatFichier] = {}
        for numero, ligne in enumerate(lignes[1:-1], start=2):
            try:
                document = json.loads(ligne)
                entree = entrees[document["chemin"]]
                if entree.partie.value != attendu["partie"] or entree.chemin in resultats:
                    raise ValueError
                resultats[entree.chemin] = ResultatFichier.depuis_dict(entree, document)
            except (ValueError, TypeError, KeyError, AttributeError):
                raise JournalInvalide(f"journal de reprise illisible (ligne {numero})") from None
        return resultats

    def noter(self, resultat: ResultatFichier) -> None:
        """Ajoute un résultat au journal, mis sur le disque avant de rendre la main."""
        self._fichier.write(_ligne(resultat.vers_dict()))
        self._fichier.flush()
        os.fsync(self._fichier.fileno())
        self.resultats[resultat.entree.chemin] = resultat

    def fermer(self) -> None:
        self._fichier.close()
