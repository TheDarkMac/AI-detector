"""Liste de confiance C2PA : chargement, validation, empreinte, rapport (T30, ADR-0171)."""

import base64
import hashlib
import json
from pathlib import Path

import pytest
from c2pa_essai import autorite, ecrire_liste

from voight_kampff._orchestration import catalogue, confiance
from voight_kampff.rapport.modele import VersionConfiance

LIVREE = Path(confiance.livree())  # type: ignore[arg-type]

# Liste livrée (ADR-0165)


@pytest.mark.exigence("ES-09")
def test_liste_livree() -> None:
    liste = confiance.charger()
    assert liste.version.nom == "C2PA Trust List"
    assert liste.version.version == "4"
    assert liste.version.date.isoformat() == "2026-11-04"
    assert liste.version.fourni_par_utilisateur is False
    contenus = [(f.name, f.read_bytes()) for f in LIVREE.iterdir() if f.is_file()]
    assert sorted(nom for nom, _ in contenus) == sorted(
        [confiance.ENTETE, confiance.SIGNATAIRES, confiance.HORODATAGE]
    )
    assert liste.version.empreinte == catalogue.empreinte(contenus)
    assert liste.signataires.count("-----BEGIN CERTIFICATE-----") == 33
    assert liste.horodatage.count("-----BEGIN CERTIFICATE-----") == 24


def test_fichiers_publies_recopies_sans_modification() -> None:
    # SHA-256 des fichiers du commit a95f2c4e4b de c2pa-org/conformance-public (confiance.toml).
    empreintes = {
        confiance.SIGNATAIRES: "148c1c167e98dc909a0d5793d2feee1022aa60fef5c83a0d6b08f67f4446bc37",
        confiance.HORODATAGE: "eca8347ee71e31d226e00c85b15aca356116fefe6c26ed8c0ee1f954115b1990",
    }
    for nom, attendue in empreintes.items():
        assert hashlib.sha256((LIVREE / nom).read_bytes()).hexdigest() == attendue


def test_configuration_envoyee_au_travail() -> None:
    liste = confiance.charger()
    assert liste.configuration() == {
        "signataires": liste.signataires,
        "horodatage": liste.horodatage,
    }


# Liste fournie par l'utilisateur (ADR-0171)


@pytest.mark.exigence("ES-09")
def test_liste_fournie_signalee(tmp_path: Path) -> None:
    dossier = ecrire_liste(tmp_path / "liste")
    liste = confiance.charger(dossier)
    assert liste.version == VersionConfiance(
        "Liste d'essai",
        "1",
        liste.version.date,
        catalogue.empreinte((f.name, f.read_bytes()) for f in dossier.iterdir()),
        fourni_par_utilisateur=True,
    )
    assert liste.signataires == autorite().racine.decode()
    assert liste.horodatage == ""
    assert confiance.charger(str(dossier)).version == liste.version


def test_entete_complet_et_fins_de_ligne_crlf(tmp_path: Path) -> None:
    dossier = ecrire_liste(tmp_path)
    entete = (LIVREE / confiance.ENTETE).read_text(encoding="utf-8")
    (dossier / confiance.ENTETE).write_text(entete, encoding="utf-8")
    pem = autorite().racine.replace(b"\n", b"\r\n")
    (dossier / confiance.SIGNATAIRES).write_bytes(b"Subject\tCN=Essai\r\n" + pem)
    (dossier / confiance.HORODATAGE).write_bytes(autorite().racine)
    liste = confiance.charger(dossier)
    assert liste.version.nom == "C2PA Trust List"
    assert liste.horodatage == autorite().racine.decode()


def test_pem_sans_saut_de_ligne_final(tmp_path: Path) -> None:
    ecrire_liste(tmp_path, autorite().racine.rstrip(b"\n"))
    assert confiance.charger(tmp_path).signataires.endswith("-----END CERTIFICATE-----")


def _bloc(der: bytes) -> bytes:
    return (
        b"-----BEGIN CERTIFICATE-----\n" + base64.b64encode(der) + b"\n-----END CERTIFICATE-----\n"
    )


@pytest.mark.exigence("ES-09")
@pytest.mark.parametrize(
    ("contenu", "message"),
    [
        pytest.param("é".encode(), "ASCII", id="non-ascii"),
        pytest.param(b"", "aucun certificat", id="vide"),
        pytest.param(b"Subject\tCN=x\n", "aucun certificat", id="sans-certificat"),
        pytest.param(b"\x01\n", "hors d'un certificat", id="caractere-de-controle"),
        pytest.param(
            b"-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----\n",
            "hors d'un certificat",
            id="cle-privee",
        ),
        pytest.param(
            b"-----BEGIN CERTIFICATE-----\nAA AA\n-----END CERTIFICATE-----\n",
            "dans un certificat",
            id="blanc-dans-le-bloc",
        ),
        pytest.param(
            b"-----BEGIN CERTIFICATE-----\n\n-----END CERTIFICATE-----\n",
            "dans un certificat",
            id="ligne-vide-dans-le-bloc",
        ),
        pytest.param(b"-----BEGIN CERTIFICATE-----\nMAA=\n", "non fermé", id="non-ferme"),
        pytest.param(
            b"-----BEGIN CERTIFICATE-----\nMA=A\n-----END CERTIFICATE-----\n",
            "base64",
            id="base64-invalide",
        ),
        pytest.param(_bloc(b"\x02\x01\x00"), "DER", id="pas-une-sequence"),
        pytest.param(_bloc(b"0"), "DER", id="trop-court"),
    ],
)
def test_pem_invalide_refuse(tmp_path: Path, contenu: bytes, message: str) -> None:
    ecrire_liste(tmp_path, contenu)
    with pytest.raises(confiance.ConfianceInvalide, match=message):
        confiance.charger(tmp_path)


def test_trop_de_certificats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(confiance, "CERTIFICATS_MAX", 1)
    ecrire_liste(tmp_path, autorite().racine * 2)
    with pytest.raises(confiance.ConfianceInvalide, match="plus de 1 certificats"):
        confiance.charger(tmp_path)


_ENTETE = 'format = 1\nnom = "x"\nversion = "1"\ndate = "2026-11-14"\ndescription = "x"\n'


@pytest.mark.parametrize(
    ("entete", "message"),
    [
        pytest.param(b"nom = ", "TOML illisible", id="toml"),
        pytest.param(b"\xff", "TOML illisible", id="non-utf8"),
        pytest.param(b'format = 1\nnom = "x"\n', "confiance.toml", id="champs-manquants"),
        pytest.param(_ENTETE.replace("1", "2", 1).encode(), "confiance.toml", id="autre-format"),
        pytest.param(
            _ENTETE.replace("2026-11-14", "2026-02-30").encode(),
            "date inexistante",
            id="date-inexistante",
        ),
        pytest.param(
            (_ENTETE + 'prochaine_mise_a_jour = "2027-13-01"\n').encode(),
            "prochaine_mise_a_jour inexistante",
            id="prochaine-inexistante",
        ),
    ],
)
def test_entete_invalide_refuse(tmp_path: Path, entete: bytes, message: str) -> None:
    ecrire_liste(tmp_path)
    (tmp_path / confiance.ENTETE).write_bytes(entete)
    with pytest.raises(confiance.ConfianceInvalide, match=message):
        confiance.charger(tmp_path)


def test_dossier_et_fichiers_refuses(tmp_path: Path) -> None:
    with pytest.raises(confiance.ConfianceInvalide, match="introuvable"):
        confiance.charger(tmp_path / "absent")
    ecrire_liste(tmp_path / "a")
    (tmp_path / "a" / "autre.pem").write_bytes(b"")
    with pytest.raises(confiance.ConfianceInvalide, match="inattendu"):
        confiance.charger(tmp_path / "a")
    ecrire_liste(tmp_path / "b")
    (tmp_path / "b" / confiance.HORODATAGE).mkdir()
    with pytest.raises(confiance.ConfianceInvalide, match="inattendu"):
        confiance.charger(tmp_path / "b")
    for absent in (confiance.ENTETE, confiance.SIGNATAIRES):
        dossier = ecrire_liste(tmp_path / absent)
        (dossier / absent).unlink()
        with pytest.raises(confiance.ConfianceInvalide, match=f"{absent} absent"):
            confiance.charger(dossier)


def test_taille_bornee(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ecrire_liste(tmp_path)
    taille = sum(f.stat().st_size for f in tmp_path.iterdir())
    monkeypatch.setattr(confiance, "TAILLE_MAX_CONFIANCE", taille - 1)
    with pytest.raises(confiance.ConfianceInvalide, match="Mio"):
        confiance.charger(tmp_path)


class _SansTaille:
    """Fichier d'un dossier qui n'annonce pas sa taille (ressource d'un paquet)."""

    def __init__(self, chemin: Path) -> None:
        self.name = chemin.name
        self._chemin = chemin

    def is_file(self) -> bool:
        return True

    def read_bytes(self) -> bytes:
        return self._chemin.read_bytes()


class _DossierSansTaille:
    def __init__(self, chemin: Path) -> None:
        self._chemin = chemin

    def is_dir(self) -> bool:
        return True

    def iterdir(self) -> list[_SansTaille]:
        return [_SansTaille(f) for f in self._chemin.iterdir()]


def test_taille_lue_quand_elle_n_est_pas_annoncee(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ecrire_liste(tmp_path)
    dossier = _DossierSansTaille(tmp_path)
    assert confiance.charger(dossier).version.fourni_par_utilisateur  # type: ignore[arg-type]
    monkeypatch.setattr(confiance, "TAILLE_MAX_CONFIANCE", 8)
    with pytest.raises(confiance.ConfianceInvalide, match="Mio"):
        confiance.charger(dossier)  # type: ignore[arg-type]


# Au rapport (ADR-0171)


def test_version_au_rapport_et_relue(tmp_path: Path) -> None:
    from voight_kampff import analyser

    chemin = tmp_path / "photo.jpg"
    chemin.write_bytes((Path(__file__).parent / "donnees/metadonnees/photo.jpg").read_bytes())
    rapport = analyser(chemin, confiance=ecrire_liste(tmp_path / "liste")).rapport()
    document = rapport.vers_dict()
    assert document["versions"]["confiance"]["nom"] == "Liste d'essai"
    assert document["versions"]["confiance"]["fourni_par_utilisateur"] is True
    assert type(rapport).depuis_dict(json.loads(json.dumps(document))) == rapport


@pytest.mark.parametrize(
    "champ",
    [
        pytest.param({"nom": ""}, id="nom-vide"),
        pytest.param({"nom": "x" * 129}, id="nom-trop-long"),
        pytest.param({"nom": "\ud800"}, id="nom-non-encodable"),
        pytest.param({"version": "4 bis"}, id="version"),
        pytest.param({"empreinte": "0"}, id="empreinte"),
    ],
)
def test_version_de_liste_invalide(champ: dict[str, str]) -> None:
    valeurs = {"nom": "Liste", "version": "1", "empreinte": "a" * 64} | champ
    with pytest.raises(ValueError, match="confiance"):
        VersionConfiance(
            valeurs["nom"],
            valeurs["version"],
            confiance.charger().version.date,
            valeurs["empreinte"],
            False,
        )


# Ligne de commande et soumission (ADR-0171)


def test_commande_avec_une_liste_fournie(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from voight_kampff.cli import main

    chemin = tmp_path / "photo.jpg"
    chemin.write_bytes((Path(__file__).parent / "donnees/metadonnees/photo.jpg").read_bytes())
    assert main(["--confiance", str(ecrire_liste(tmp_path / "liste")), str(chemin)]) == 0
    sortie = capsys.readouterr().out
    assert "attention : Liste de confiance C2PA fournie par l'utilisateur" in sortie
    assert "liste de confiance C2PA : Liste d'essai 1 du 2026-11-14, empreinte " in sortie
    assert "fournie par l'utilisateur\n" in sortie


def test_commande_refuse_une_liste_invalide(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from voight_kampff.cli import main

    with pytest.raises(SystemExit) as sortie:
        main(["--confiance", str(tmp_path / "absente"), str(tmp_path / "f.jpg")])
    assert sortie.value.code == 2
    assert "liste de confiance invalide : liste de confiance : dossier introuvable" in (
        capsys.readouterr().err
    )


def test_soumission_avec_une_liste_deja_validee(tmp_path: Path) -> None:
    from voight_kampff._orchestration import soumission

    chemin = tmp_path / "photo.jpg"
    chemin.write_bytes((Path(__file__).parent / "donnees/metadonnees/photo.jpg").read_bytes())
    liste = confiance.charger(ecrire_liste(tmp_path / "liste"))
    assert soumission.soumettre(chemin, confiance=liste).confiance == liste.version
