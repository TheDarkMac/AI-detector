"""Analyse d'un corpus et mesures (§8 du cahier, ADR-0018, ADR-0101, ADR-0104).

Deux temps : :func:`analyser_corpus` analyse chaque fichier d'une partie et n'en garde que ce
que les mesures emploient (:class:`ResultatFichier`) ; :func:`mesurer`, sans effet de bord,
calcule à partir de ces résultats :

- par technique et par catégorie du corpus : faux positifs, faux négatifs, non analysables ;
- par règle d'indice ou de preuve : taux de faux positifs et niveau qu'il permet ;
- le taux de faux positifs par fichier, critère d'acceptation d'ADR-0018 ;
- les écarts qui font échouer l'évaluation.

Chaque fichier est analysé deux fois : deux rapports différents dans les conditions de la
garantie sont un défaut de reproductibilité, compté comme un écart (NF-06, ADR-0113).
"""

import dataclasses
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from banc.corpus import Categorie as CategorieCorpus
from banc.corpus import Corpus, Entree, Origine, Partie
from banc.mesures import Taux
from banc.reseau import ReseauInterdit
from voight_kampff import Analyse, AnalyseRefusee
from voight_kampff._regles import BORNE_MODERE, Regle, niveau_permis
from voight_kampff.rapport import comparaison, export
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
    Direction,
    EtatTechnique,
    Niveau,
)

__all__ = [
    "CIBLE_PAR_FICHIER",
    "ConstatRetenu",
    "EtatFichier",
    "Evaluation",
    "ResultatFichier",
    "analyser_corpus",
    "mesurer",
    "reproduction",
]

CIBLE_PAR_FICHIER = BORNE_MODERE
"""Borne supérieure, à 95 %, du taux de faux positifs par fichier à ne pas dépasser (ADR-0101)."""

DIRECTIONS_FAUTIVES = frozenset({Direction.ORIGINE_IA, Direction.RETOUCHE})
"""Directions d'un constat qui, sur un fichier authentique, sont un faux positif."""

_ATTENDUE: dict[Origine | None, Direction] = {
    Origine.IA: Direction.ORIGINE_IA,
    Origine.RETOUCHE: Direction.RETOUCHE,
}
"""Direction qu'un constat doit prendre sur un fichier de cette origine pour le détecter."""

_CONFONDUE: dict[Origine | None, Direction] = {
    Origine.IA: Direction.RETOUCHE,
    Origine.RETOUCHE: Direction.ORIGINE_IA,
}
"""Direction qui prend une génération pour une retouche, ou l'inverse (§8 : « Retouchés »)."""

_RANG = {Niveau.FAIBLE: 0, Niveau.MODERE: 1, Niveau.FORT: 2}


_CITES = 5
"""Écarts de reproduction cités par fichier ; le reste est compté."""


def _cites(ecarts: Sequence[str]) -> str:
    cites = ", ".join(ecarts[:_CITES])
    return cites if len(ecarts) <= _CITES else f"{cites}… {len(ecarts)} écarts"


def _pourcent(valeur: float) -> str:
    return f"{valeur * 100:.1f}".replace(".", ",") + " %"


class EtatFichier(StrEnum):
    """Ce qu'une technique a pu faire d'un fichier, toutes parties du fichier confondues."""

    ANALYSE = "analyse"
    NON_ANALYSABLE = "non_analysable"
    """Technique concernée, mais non menée : refus, erreur, limite, partie tronquée…"""
    NON_APPLICABLE = "non_applicable"
    """Technique sans objet pour ce format : hors des mesures de ce fichier."""


@dataclass(frozen=True, slots=True)
class ConstatRetenu:
    """Ce que les mesures emploient d'un constat."""

    regle: str
    module: str
    categorie: Categorie
    direction: Direction
    niveau: Niveau | None = None

    @property
    def probant(self) -> bool:
        """Preuve, ou indice de niveau modéré ou fort : ce que compte le taux par fichier."""
        return self.categorie is Categorie.PREUVE or (
            self.categorie is Categorie.INDICE and self.niveau in (Niveau.MODERE, Niveau.FORT)
        )

    @property
    def dirige(self) -> bool:
        """Preuve ou indice : un constat qui pointe vers une hypothèse."""
        return self.categorie is not Categorie.INFORMATION_NEUTRE


@dataclass(frozen=True, slots=True)
class ResultatFichier:
    """Résultat d'une analyse, réduit à ce que les mesures emploient."""

    entree: Entree
    techniques: Mapping[str, EtatFichier]
    constats: tuple[ConstatRetenu, ...] = ()
    refus: str | None = None
    """Motif du refus (``MotifRefus``) : aucune technique n'a analysé le fichier."""
    erreur: str | None = None
    """Nom de l'exception d'une analyse qui s'est arrêtée brutalement (critère du §8)."""
    interrompue: bool = False
    non_reproduit: tuple[str, ...] = ()
    """Ce qui diffère entre les deux analyses du fichier, dans les conditions de la garantie :
    chemins des champs du rapport, ou issues différentes (ADR-0113)."""

    @property
    def analyse(self) -> bool:
        """Faux si le fichier n'a donné aucun résultat : refus ou arrêt brutal."""
        return self.refus is None and self.erreur is None

    def etat(self, module: str) -> EtatFichier:
        return self.techniques.get(module, EtatFichier.NON_APPLICABLE)

    def constats_de(self, module: str) -> Iterable[ConstatRetenu]:
        return (constat for constat in self.constats if constat.module == module)


def depuis_analyse(entree: Entree, analyse: Analyse, modules: Iterable[str]) -> ResultatFichier:
    techniques = {}
    for module in modules:
        etats = {t.etat for t in analyse.couverture.techniques if t.module == module}
        if etats & {EtatTechnique.APPLIQUEE, EtatTechnique.PARTIELLE}:
            techniques[module] = EtatFichier.ANALYSE
        elif EtatTechnique.NON_MENEE in etats:
            techniques[module] = EtatFichier.NON_ANALYSABLE
        else:
            techniques[module] = EtatFichier.NON_APPLICABLE
    constats = tuple(
        ConstatRetenu(
            c.regle.identifiant,
            c.module,
            c.categorie,
            c.direction,
            None if c.graduation is None else c.graduation.niveau,
        )
        for c in analyse.constats
    )
    return ResultatFichier(entree, techniques, constats, interrompue=analyse.interrompue)


type Issue = Analyse | AnalyseRefusee


def _issue(analyser_fichier: Callable[[Path], Analyse], chemin: Path) -> Issue:
    try:
        return analyser_fichier(chemin)
    except AnalyseRefusee as refus:
        return refus


def reproduction(premiere: Issue, seconde: Issue) -> tuple[str, ...]:
    """Ce qui diffère entre deux analyses du même fichier, dans la garantie (ADR-0113).

    Deux refus doivent avoir le même motif ; deux analyses, le même rapport, comparé en entier,
    masquage levé (ADR-0108). Hors garantie (analyse interrompue), rien n'est relevé.
    """
    match premiere, seconde:
        case AnalyseRefusee(), AnalyseRefusee():
            if premiere.motif is seconde.motif:
                return ()
            return (f"refus « {premiere.motif.value} » puis « {seconde.motif.value} »",)
        case Analyse(), Analyse():
            tout = list(CategorieIdentifiante)
            resultat = comparaison.comparer(
                export.document(premiere, tout), export.document(seconde, tout)
            )
            if not resultat.defaut:
                return ()
            return tuple(ecart.chemin for ecart in resultat.nature(comparaison.Nature.RESULTAT))
        case _:
            return ("analysé une fois, refusé l'autre",)


def analyser_corpus(
    corpus: Corpus,
    partie: Partie,
    analyser_fichier: Callable[[Path], Analyse],
    modules: Sequence[str],
) -> list[ResultatFichier]:
    """Analyse chaque fichier de la partie deux fois, dans l'ordre du manifeste.

    Un fichier absent ou modifié arrête tout (``CorpusInvalide``) ; une tentative d'accès au
    réseau aussi (:class:`ReseauInterdit`). Un refus est un résultat ; toute autre exception est
    un arrêt brutal, noté par son seul nom, et l'évaluation continue. Le résultat retenu est
    celui de la première analyse ; la seconde n'est comparée qu'à elle (ADR-0113).
    """
    sans_analyse = dict.fromkeys(modules, EtatFichier.NON_ANALYSABLE)
    resultats = []
    for entree in corpus.partie(partie):
        chemin = corpus.verifier(entree)
        try:
            premiere = _issue(analyser_fichier, chemin)
            seconde = _issue(analyser_fichier, chemin)
        except ReseauInterdit:
            raise
        except Exception as erreur:  # arrêt brutal : c'est ce que le §8 demande de compter
            resultats.append(ResultatFichier(entree, sans_analyse, erreur=type(erreur).__name__))
            continue
        ecarts = reproduction(premiere, seconde)
        if isinstance(premiere, AnalyseRefusee):
            resultat = ResultatFichier(entree, sans_analyse, refus=premiere.motif.value)
        else:
            resultat = depuis_analyse(entree, premiere, modules)
        resultats.append(dataclasses.replace(resultat, non_reproduit=ecarts))
    return resultats


# Mesures


@dataclass(frozen=True, slots=True)
class MesureTechnique:
    """Une technique sur une catégorie du corpus (§8 du cahier)."""

    module: str
    categorie: CategorieCorpus
    effectif: int
    non_applicables: int
    non_analysables: Taux
    """Sur les fichiers où la technique s'applique."""
    faux_positifs: Taux
    """Sur les fichiers authentiques analysés : au moins un constat vers l'IA ou la retouche."""
    faux_negatifs: Taux
    """Sur les fichiers générés ou retouchés analysés : aucun constat dans la bonne direction."""
    confusions: int
    """Fichiers générés pris pour retouchés, ou l'inverse."""

    def vers_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "categorie": self.categorie.value,
            "effectif": self.effectif,
            "non_applicables": self.non_applicables,
            "non_analysables": self.non_analysables.vers_dict(),
            "faux_positifs": self.faux_positifs.vers_dict(),
            "faux_negatifs": self.faux_negatifs.vers_dict(),
            "confusions": self.confusions,
        }


@dataclass(frozen=True, slots=True)
class MesureRegle:
    """Taux de faux positifs d'une règle de preuve ou d'indice (ADR-0018, ADR-0101)."""

    regle: Regle
    faux_positifs: Taux
    chemins: tuple[str, ...]
    """Fichiers du corpus qui portent un faux positif de la règle."""

    @property
    def niveau_permis(self) -> Niveau | None:
        """Pour un indice mesuré ; sans mesure, seul « faible » est permis (ADR-0018)."""
        borne = self.faux_positifs.borne_superieure
        if self.regle.categorie is not Categorie.INDICE or borne is None:
            return None
        return niveau_permis(borne)

    @property
    def ecart(self) -> str | None:
        """Ce que la mesure contredit dans le catalogue, s'il y a lieu."""
        regle = self.regle
        if regle.categorie is Categorie.PREUVE:
            if self.faux_positifs.nombre:
                return f"la preuve {regle.identifiant} a des faux positifs"
            return None
        niveau, permis = regle.niveau or Niveau.FAIBLE, self.niveau_permis or Niveau.FAIBLE
        if _RANG[niveau] > _RANG[permis]:
            return (
                f"l'indice {regle.identifiant} est au niveau « {niveau.value} » ; la mesure "
                f"permet au plus « {permis.value} »"
            )
        return None

    def vers_dict(self) -> dict[str, Any]:
        regle = self.regle
        return {
            "identifiant": regle.identifiant,
            "version": regle.version,
            "module": regle.module,
            "categorie": regle.categorie.value,
            "direction": regle.direction.value,
            "niveau": None if regle.niveau is None else regle.niveau.value,
            "evaluee": regle.evaluation is not None,
            "faux_positifs": self.faux_positifs.vers_dict(),
            "niveau_permis": None if self.niveau_permis is None else self.niveau_permis.value,
            "chemins": list(self.chemins),
            "ecart": self.ecart,
        }


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Mesures d'une partie du corpus, et écarts qui font échouer l'évaluation."""

    partie: Partie
    resultats: tuple[ResultatFichier, ...]
    techniques: tuple[MesureTechnique, ...]
    regles: tuple[MesureRegle, ...]
    par_fichier: Mapping[CategorieCorpus, Taux]
    ecarts: tuple[str, ...] = field(default=())

    @property
    def cible_atteinte(self) -> bool | None:
        """Critère d'ADR-0018 sur les authentiques ; ``None`` s'il n'est pas mesurable."""
        borne = self.par_fichier[CategorieCorpus.AUTHENTIQUE].borne_superieure
        return None if borne is None else borne <= CIBLE_PAR_FICHIER

    def vers_dict(self) -> dict[str, Any]:
        effectifs = Counter(r.entree.categorie for r in self.resultats)
        return {
            "partie": self.partie.value,
            "fichiers": {
                "total": len(self.resultats),
                "par_categorie": {c.value: effectifs[c] for c in CategorieCorpus},
                "refus": dict(sorted(Counter(r.refus for r in self.resultats if r.refus).items())),
                "arrets_brutaux": dict(
                    sorted(Counter(r.erreur for r in self.resultats if r.erreur).items())
                ),
                "interrompues": sum(r.interrompue for r in self.resultats),
                "non_reproduits": sum(bool(r.non_reproduit) for r in self.resultats),
            },
            "techniques": [mesure.vers_dict() for mesure in self.techniques],
            "regles": [mesure.vers_dict() for mesure in self.regles],
            "par_fichier": {
                "categories": {c.value: t.vers_dict() for c, t in self.par_fichier.items()},
                "cible": CIBLE_PAR_FICHIER,
                "cible_atteinte": self.cible_atteinte,
            },
            "ecarts": list(self.ecarts),
        }


def _mesure_technique(
    module: str, categorie: CategorieCorpus, resultats: Sequence[ResultatFichier]
) -> MesureTechnique:
    dans = [r for r in resultats if r.entree.categorie is categorie]
    concernes = [r for r in dans if r.etat(module) is not EtatFichier.NON_APPLICABLE]
    analyses = [r for r in concernes if r.etat(module) is EtatFichier.ANALYSE]
    authentiques = [r for r in analyses if r.entree.origine is Origine.AUTHENTIQUE]
    detectables = [r for r in analyses if r.entree.origine in _ATTENDUE]
    faux_positifs = sum(
        any(c.dirige and c.direction in DIRECTIONS_FAUTIVES for c in r.constats_de(module))
        for r in authentiques
    )
    faux_negatifs = confusions = 0
    for resultat in detectables:
        origine = resultat.entree.origine
        directions = {c.direction for c in resultat.constats_de(module) if c.dirige}
        faux_negatifs += _ATTENDUE[origine] not in directions
        confusions += _CONFONDUE[origine] in directions
    return MesureTechnique(
        module=module,
        categorie=categorie,
        effectif=len(dans),
        non_applicables=len(dans) - len(concernes),
        non_analysables=Taux(len(concernes) - len(analyses), len(concernes)),
        faux_positifs=Taux(faux_positifs, len(authentiques)),
        faux_negatifs=Taux(faux_negatifs, len(detectables)),
        confusions=confusions,
    )


def _population(regle: Regle, resultats: Sequence[ResultatFichier]) -> list[ResultatFichier]:
    """Fichiers sur lesquels un constat de la règle serait faux (ADR-0104)."""
    analyses = [r for r in resultats if r.etat(regle.module) is EtatFichier.ANALYSE]
    if regle.direction is Direction.AUTHENTICITE:
        contraires = {CategorieCorpus.GENERE, CategorieCorpus.RETOUCHE}
        return [r for r in analyses if r.entree.categorie in contraires]
    return [r for r in analyses if r.entree.categorie is CategorieCorpus.AUTHENTIQUE]


def _mesure_regle(regle: Regle, resultats: Sequence[ResultatFichier]) -> MesureRegle:
    population = _population(regle, resultats)
    fautifs = [
        r.entree.chemin
        for r in population
        if any(c.regle == regle.identifiant for c in r.constats_de(regle.module))
    ]
    return MesureRegle(regle, Taux(len(fautifs), len(population)), tuple(fautifs))


def _par_fichier(categorie: CategorieCorpus, resultats: Sequence[ResultatFichier]) -> Taux:
    """Part des fichiers authentiques analysés qui portent au moins un constat probant faux."""
    population = [
        r
        for r in resultats
        if r.analyse and r.entree.categorie is categorie and r.entree.origine is Origine.AUTHENTIQUE
    ]
    fautifs = sum(
        any(c.probant and c.direction in DIRECTIONS_FAUTIVES for c in r.constats)
        for r in population
    )
    return Taux(fautifs, len(population))


def mesurer(
    partie: Partie,
    resultats: Sequence[ResultatFichier],
    modules: Sequence[str],
    regles: Sequence[Regle],
) -> Evaluation:
    """Mesures d'une partie ; les écarts ne portent sur les taux que pour l'évaluation.

    Seules les règles des modules mesurés (``modules``) le sont : celles d'un module désactivé
    n'ont aucun fichier où il ait été analysé.
    """
    techniques = tuple(
        _mesure_technique(module, categorie, resultats)
        for module in modules
        for categorie in CategorieCorpus
    )
    mesures_regles = tuple(
        _mesure_regle(regle, resultats)
        for regle in regles
        if regle.categorie is not Categorie.INFORMATION_NEUTRE and regle.module in modules
    )
    par_fichier = {
        categorie: _par_fichier(categorie, resultats)
        for categorie in (CategorieCorpus.AUTHENTIQUE, CategorieCorpus.TRANSFORME)
    }
    ecarts = [
        f"{r.entree.chemin} : arrêt brutal de l'analyse ({r.erreur})"
        for r in resultats
        if r.erreur is not None
    ]
    ecarts += [
        f"{r.entree.chemin} : deux analyses différentes ({_cites(r.non_reproduit)})"
        for r in resultats
        if r.non_reproduit
    ]
    evaluation = Evaluation(partie, tuple(resultats), techniques, mesures_regles, par_fichier)
    if partie is Partie.EVALUATION:
        ecarts += [mesure.ecart for mesure in mesures_regles if mesure.ecart is not None]
        match evaluation.cible_atteinte:
            case None:
                ecarts.append("taux par fichier non mesurable : aucun fichier authentique analysé")
            case False:
                borne = par_fichier[CategorieCorpus.AUTHENTIQUE].borne_superieure or 0.0
                ecarts.append(
                    f"taux par fichier : borne supérieure de {_pourcent(borne)} au-delà de la "
                    f"cible de {CIBLE_PAR_FICHIER * 100:g} %"
                )
    return Evaluation(
        partie, tuple(resultats), techniques, mesures_regles, par_fichier, tuple(ecarts)
    )
