"""Tests du catalogue : lecture, validation, empreinte, registre (T15, ADR-0085 à ADR-0088)."""

import hashlib
import importlib.util
import tomllib
import zipfile
from collections.abc import Iterator
from datetime import date
from importlib.resources.abc import Traversable
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
from catalogues import ENTETE, ecrire_catalogue, moteur, regle, regle_dict, toml_regles

from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration import manifestes
from voight_kampff._orchestration.catalogue import CatalogueInvalide, charger, empreinte
from voight_kampff._orchestration.manifestes import Manifeste
from voight_kampff.rapport.modele import Direction

RACINE_DU_DEPOT = Path(__file__).resolve().parents[1]
REGISTRE = RACINE_DU_DEPOT / "docs" / "catalogue" / "versions.toml"


def manifeste(identifiant: str = "alpha", regles: tuple[str, ...] = ()) -> Manifeste:
    directions = (Direction.ORIGINE_IA, Direction.RIEN_DE_PARTICULIER)
    return Manifeste(identifiant, "1.0", ("jpeg",), ("F-10",), regles, "test", directions)


MODULES = (manifeste("alpha", ("R-ALPHA-001",)), manifeste("beta"))
ALPHA = toml_regles(
    regle_dict("R-ALPHA-001"),
    regle_dict("R-ALPHA-002", **moteur({"observation": "n", "motif": "^a", "parametre": "n"})),
)
BETA = toml_regles(regle_dict("R-BETA-001", "beta", **moteur({"observation": "n", "egal": 1})))


def fichiers(dossier: Path) -> list[tuple[str, bytes]]:
    return [
        (chemin.relative_to(dossier).as_posix(), chemin.read_bytes())
        for chemin in dossier.rglob("*")
        if chemin.is_file()
    ]


# Catalogue livré


def test_catalogue_livre_valide() -> None:
    livre = charger(manifestes.decouvrir())
    assert not livre.version.fourni_par_utilisateur
    assert livre.regles == ()  # aucun module livré : aucune règle
    assert livre.version.empreinte == empreinte(fichiers(Path(str(catalogues.livre()))))


def test_empreinte_selon_la_procedure_publiee() -> None:
    # Ce que donne `find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum` (ADR-0088).
    dossier = Path(str(catalogues.livre()))
    lignes = sorted(
        f"{hashlib.sha256(contenu).hexdigest()}  {chemin}\n"
        for chemin, contenu in fichiers(dossier)
    )
    attendue = hashlib.sha256("".join(lignes).encode()).hexdigest()
    assert charger(manifestes.decouvrir()).version.empreinte == attendue


def test_empreinte_change_avec_le_contenu_ou_le_chemin() -> None:
    base = empreinte([("catalogue.toml", b"a"), ("regles/x.toml", b"b")])
    assert base == empreinte([("regles/x.toml", b"b"), ("catalogue.toml", b"a")])  # ordre
    assert base != empreinte([("catalogue.toml", b"a"), ("regles/x.toml", b"c")])
    assert base != empreinte([("catalogue.toml", b"a"), ("regles/y.toml", b"b")])
    assert base != empreinte([("catalogue.toml", b"a\r\n")])


# Registre des versions (ADR-0085)


def registre() -> list[dict[str, str]]:
    versions: list[dict[str, str]] = tomllib.loads(REGISTRE.read_text(encoding="utf-8"))["version"]
    return versions


def test_registre_decrit_le_catalogue_livre() -> None:
    livre = charger(manifestes.decouvrir()).version
    assert registre()[-1] == {
        "version": livre.version,
        "date": livre.date.isoformat(),
        "empreinte": livre.empreinte,
    }, "catalogue modifié : nouvelle version à inscrire au registre (docs/catalogue/README.md)"


def test_registre_ordonne() -> None:
    entrees = registre()
    numeros = [tuple(map(int, entree["version"].split("."))) for entree in entrees]
    dates = [date.fromisoformat(entree["date"]) for entree in entrees]
    assert numeros == sorted(set(numeros)), "versions croissantes, sans doublon"
    assert dates == sorted(dates), "dates dans l'ordre des versions"
    assert len({entree["empreinte"] for entree in entrees}) == len(entrees)


# Catalogue fourni par l'utilisateur (ADR-0086)


def test_catalogue_fourni(tmp_path: Path) -> None:
    dossier = ecrire_catalogue(tmp_path, {"beta": BETA, "alpha": ALPHA})
    fourni = charger(MODULES, dossier)
    assert fourni.version.fourni_par_utilisateur
    assert (fourni.version.version, fourni.version.date) == ("1.2.3", date(2026, 10, 20))
    assert fourni.version.empreinte == empreinte(fichiers(dossier))
    assert fourni.description == "Catalogue de test."
    # Triées par identifiant, quel que soit le fichier.
    assert [r.identifiant for r in fourni.regles] == ["R-ALPHA-001", "R-ALPHA-002", "R-BETA-001"]
    assert fourni.du_module("beta") == (
        regle("R-BETA-001", "beta", **moteur({"observation": "n", "egal": 1})),
    )
    assert [r["identifiant"] for r in fourni.configuration({"beta"})] == ["R-BETA-001"]
    assert charger(MODULES, str(dossier)) == fourni


def test_catalogue_sans_regle(tmp_path: Path) -> None:
    assert charger((manifeste(),), ecrire_catalogue(tmp_path)).regles == ()


def ecrire(dossier: Path, chemin: str, contenu: str | bytes) -> None:
    cible = dossier / chemin
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_bytes(contenu.encode() if isinstance(contenu, str) else contenu)


AUTRE_MODULE = toml_regles(regle_dict("R-ALPHA-003", "alpha"))  # dans regles/beta.toml
INCONNU = toml_regles(regle_dict("R-GAMMA-001", "gamma", **moteur({"observation": "n", "egal": 1})))
DIRECTION = toml_regles(
    regle_dict(
        "R-BETA-002",
        "beta",
        categorie="indice",
        direction="retouche",
        niveau="faible",
        **moteur({"observation": "n", "egal": 1}),
    )
)


@pytest.mark.parametrize(
    ("fichier", "contenu", "attendu"),
    [
        pytest.param("LISEZMOI.md", "texte", "inattendu : 'LISEZMOI.md'", id="fichier-a-la-racine"),
        pytest.param("autres/a.toml", "", "inattendu : 'autres'", id="dossier-a-la-racine"),
        # Gamma et non Alpha : sous macOS et Windows, Alpha.toml remplacerait alpha.toml.
        pytest.param("regles/Gamma.toml", ALPHA, "inattendu : regles/'Gamma", id="nom-de-module"),
        pytest.param("regles/alpha.txt", ALPHA, "inattendu", id="extension"),
        pytest.param("regles/sous/a.toml", "", "inattendu", id="sous-dossier"),
        pytest.param("catalogue.toml", "format = ", "TOML illisible", id="entete-illisible"),
        pytest.param("catalogue.toml", b"\xff", "TOML illisible", id="entete-non-utf8"),
        pytest.param("catalogue.toml", "format = 2\n", "catalogue.toml : document", id="format"),
        pytest.param(
            "catalogue.toml",
            ENTETE.replace('"1.2.3"', '"1.2"'),
            "properties/version",
            id="version-incomplete",
        ),
        pytest.param(
            "catalogue.toml",
            ENTETE.replace("2026-10-20", "2026-02-30"),
            "date inexistante",
            id="date-inexistante",
        ),
        pytest.param("regles/alpha.toml", "regle = 1\n", "regles/alpha.toml : document", id="type"),
        pytest.param("regles/beta.toml", AUTRE_MODULE, "d'un autre module", id="autre-module"),
        pytest.param(
            "regles/beta.toml",
            toml_regles(regle_dict("R-BETA-001", "beta", gabarit="g", categorie="preuve")),
            "R-BETA-001 : constat : une preuve",
            id="combinaison",
        ),
        pytest.param(
            "regles/beta.toml",
            toml_regles(
                regle_dict("R-BETA-001", "beta", **moteur({"observation": "n", "motif": "(?=a)"}))
            ),
            "R-BETA-001 : condition.motif : refusé par RE2",
            id="motif-refuse",
        ),
        pytest.param(
            "regles/beta.toml",
            toml_regles(
                regle_dict("R-ALPHA-002", "beta", **moteur({"observation": "n", "egal": 1}))
            ),
            "définie deux fois : R-ALPHA-002",
            id="identifiant-en-double",
        ),
        pytest.param("regles/gamma.toml", INCONNU, "module gamma absent", id="module-inconnu"),
        pytest.param("regles/beta.toml", DIRECTION, "direction non permise", id="direction"),
    ],
)
def test_catalogue_refuse(tmp_path: Path, fichier: str, contenu: str | bytes, attendu: str) -> None:
    dossier = ecrire_catalogue(tmp_path, {"alpha": ALPHA})
    ecrire(dossier, fichier, contenu)
    with pytest.raises(CatalogueInvalide) as erreur:
        charger(MODULES, dossier)
    assert attendu in str(erreur.value)


@pytest.mark.parametrize(
    ("modules", "attendu"),
    [
        pytest.param(
            (manifeste("alpha", ("R-ALPHA-001", "R-ALPHA-009")), manifeste("beta")),
            "règle R-ALPHA-009 absente du catalogue",
            id="regle-citee-absente",
        ),
        pytest.param(
            (manifeste("alpha", ("R-ALPHA-001",)), manifeste("beta", ("R-ALPHA-001",))),
            "module beta : règle R-ALPHA-001 absente du catalogue",
            id="regle-d-un-autre-module",
        ),
        pytest.param(
            (manifeste("alpha", ("R-ALPHA-001", "R-ALPHA-002")), manifeste("beta")),
            "R-ALPHA-002 appliquée par le moteur",
            id="regle-du-moteur-citee",
        ),
        pytest.param(
            (manifeste("alpha"), manifeste("beta")),
            "R-ALPHA-001 : appliquée par le module, absente de son manifeste",
            id="regle-du-module-non-citee",
        ),
    ],
)
def test_catalogue_incoherent_avec_les_manifestes(
    tmp_path: Path, modules: tuple[Manifeste, ...], attendu: str
) -> None:
    dossier = ecrire_catalogue(tmp_path, {"alpha": ALPHA})
    with pytest.raises(CatalogueInvalide, match=attendu):
        charger(modules, dossier)


def test_dossier_absent_ou_sans_entete(tmp_path: Path) -> None:
    with pytest.raises(CatalogueInvalide, match="dossier introuvable"):
        charger(MODULES, tmp_path / "absent")
    (tmp_path / "regles").mkdir()
    with pytest.raises(CatalogueInvalide, match=r"en-tête catalogue\.toml absent"):
        charger(MODULES, tmp_path)


def test_trop_de_fichiers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalogues, "FICHIERS_MAX_CATALOGUE", 2)
    dossier = ecrire_catalogue(tmp_path, {"alpha": ALPHA, "beta": BETA})
    with pytest.raises(CatalogueInvalide, match="plus de 2 fichiers"):
        charger(MODULES, dossier)


def test_trop_volumineux(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dossier = ecrire_catalogue(tmp_path, {"alpha": ALPHA})
    taille = sum(len(contenu) for _, contenu in fichiers(dossier))
    monkeypatch.setattr(catalogues, "TAILLE_MAX_CATALOGUE", taille - 1)
    with pytest.raises(CatalogueInvalide, match="Mio"):
        charger(MODULES, dossier)
    # Sans taille annoncée (ressource d'un paquet), la limite est contrôlée à la lecture.
    with pytest.raises(CatalogueInvalide, match="Mio"):
        charger(MODULES, cast(Traversable, Ressource(dossier)))


class Ressource:
    """Fichier ou dossier vu comme une ressource de paquet, qui n'est pas un ``Path``."""

    def __init__(self, chemin: Path) -> None:
        self._chemin = chemin
        self.name = chemin.name

    def is_dir(self) -> bool:
        return self._chemin.is_dir()

    def is_file(self) -> bool:
        return self._chemin.is_file()

    def iterdir(self) -> Iterator["Ressource"]:
        return map(Ressource, self._chemin.iterdir())

    def read_bytes(self) -> bytes:
        return self._chemin.read_bytes()


def test_trop_de_regles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalogues, "REGLES_MAX", 2)
    dossier = ecrire_catalogue(tmp_path, {"alpha": ALPHA, "beta": BETA})
    with pytest.raises(CatalogueInvalide, match="plus de 2 règles"):
        charger(MODULES, dossier)


# Contrôle de la CI face à la révision de base (.github/scripts/catalogue.py)


def script_de_la_ci() -> ModuleType:
    chemin = RACINE_DU_DEPOT / ".github" / "scripts" / "catalogue.py"
    specification = importlib.util.spec_from_file_location("catalogue_ci", chemin)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_ecarts_releves_par_la_ci() -> None:
    ci = script_de_la_ci()
    publiee = {"version": "0.1.0", "date": "2026-10-27", "empreinte": "a" * 64}
    suivante = {"version": "0.2.0", "date": "2026-11-02", "empreinte": "b" * 64}
    ancienne = regle_dict("R-ALPHA-001")
    anciennes = ci.regles([toml_regles(ancienne)])
    assert ci.ecarts([publiee], [publiee, suivante], anciennes, anciennes) == []
    # Nouvelle version d'une règle modifiée : admise.
    nouvelle = ci.regles([toml_regles(ancienne | {"version": "2", "titre": "Autre"})])
    assert ci.ecarts([publiee], [publiee], anciennes, nouvelle) == []
    assert ci.ecarts(
        [publiee],
        [publiee | {"empreinte": "c" * 64}],
        anciennes,
        ci.regles([toml_regles(ancienne | {"titre": "Autre"})]),
    ) == [
        "registre : la version 0.1.0 a été modifiée ou retirée",
        "règle R-ALPHA-001 : modifiée sans nouvelle version (1)",
    ]
    assert ci.ecarts([], [], nouvelle, anciennes) == [
        "règle R-ALPHA-001 : version 1 inférieure à 2"
    ]


def test_catalogue_d_un_wheel(tmp_path: Path) -> None:
    ci = script_de_la_ci()
    wheel = tmp_path / "paquet.whl"
    dossier = Path(str(catalogues.livre()))
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("voight_kampff/donnees/", b"")
        for chemin, contenu in fichiers(dossier):
            archive.writestr(f"voight_kampff/donnees/catalogue/{chemin}", contenu)
        archive.writestr("voight_kampff/autre.toml", b"hors du catalogue")
    livre = charger(manifestes.decouvrir()).version
    assert ci.du_paquet(str(wheel)) == {
        "version": livre.version,
        "date": livre.date.isoformat(),
        "empreinte": livre.empreinte,
    }
