"""Module c2pa : détection, vérification, états et déclarations d'un manifeste C2PA (T30).

Les fichiers sont signés pendant les tests par une autorité d'essai (``c2pa_essai.py``) : avec la
liste de confiance d'essai, le signataire est reconnu ; avec la liste livrée, il ne l'est pas.
Contrôles déterministes : vérifiés par ces tests de conformité, sans taux sur corpus (A-55).
"""

import io
import json
from collections.abc import Callable, Iterator, Mapping
from importlib import metadata
from pathlib import Path
from typing import Any

import c2pa as bibliotheque
import pytest
from c2pa_essai import (
    FICHIERS,
    IPTC,
    NUMERO,
    SIGNATAIRE,
    TITRE,
    autorite,
    ecrire_liste,
    manifeste,
    signer,
    signer_distant,
)

from voight_kampff import Analyse, analyser
from voight_kampff._orchestration import catalogue as catalogues
from voight_kampff._orchestration.manifestes import decouvrir
from voight_kampff._travail import garde
from voight_kampff._travail.contexte import Ancres, Contexte
from voight_kampff._travail.fichier import Fichier
from voight_kampff.modules import c2pa
from voight_kampff.rapport import export
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
    Direction,
    EtatTechnique,
    Fondement,
    Partie,
    Plage,
    RaisonNonMenee,
)

pytestmark = pytest.mark.exigence("F-20", "F-21", "F-22")

FICHIERS_DU_DEPOT = Path(__file__).parent / "donnees" / "metadonnees"


def analyse_de(tmp_path: Path, contenu: bytes, nom: str = "fichier.jpg", **options: Any) -> Analyse:
    chemin = tmp_path / nom
    chemin.write_bytes(contenu)
    return analyser(chemin, **options)


def reconnue(tmp_path: Path) -> Path:
    """Liste de confiance d'essai, où l'autorité d'essai est une ancre."""
    return ecrire_liste(tmp_path / "liste")


def valeurs(analyse: Analyse) -> dict[str, Any]:
    return {o.nom: o.valeur for o in analyse.observations if o.module == "c2pa"}


def regles(analyse: Analyse) -> list[str]:
    return [c.regle.identifiant for c in analyse.constats if c.module == "c2pa"]


def constat(analyse: Analyse, identifiant: str) -> Any:
    return next(c for c in analyse.constats if c.regle.identifiant == identifiant)


def couverture(analyse: Analyse) -> EtatTechnique:
    return next(t.etat for t in analyse.couverture.techniques if t.module == "c2pa")


# États de la vérification (F-22, ADR-0169) et constats (ADR-0170)


@pytest.mark.exigence("F-23", "ES-20")
def test_generation_declaree_signataire_reconnu(tmp_path: Path) -> None:
    analyse = analyse_de(tmp_path, signer(), confiance=reconnue(tmp_path))
    assert valeurs(analyse) == {
        "c2pa.present": True,
        "c2pa.etat": "valide",
        "c2pa.manifestes": 1,
        "c2pa.validation_results.failure": (),
        "c2pa.validation_results.informational": ("signingCredential.ocsp.skipped",),
        "c2pa.signature_info.alg": "Es256",
        "c2pa.signature_info.issuer": "Essai",
        "c2pa.signature_info.common_name": SIGNATAIRE,
        "c2pa.signature_info.cert_serial_number": str(NUMERO),
        "c2pa.claim_generator_info": ("GenX 2.1",),
        "c2pa.title": TITRE,
        "c2pa.actions.action": ("c2pa.created",),
        "c2pa.actions.softwareAgent": ("GenX",),
        "c2pa.actions.digitalSourceType": (IPTC + "trainedAlgorithmicMedia",),
        "c2pa.ingredients": 0,
    }
    assert regles(analyse) == ["R-C2PA-007", "R-C2PA-001"]
    preuve = constat(analyse, "R-C2PA-001")
    assert (preuve.categorie, preuve.direction, preuve.fondement) == (
        Categorie.PREUVE,
        Direction.ORIGINE_IA,
        Fondement.VERIFICATION_CRYPTOGRAPHIQUE,
    )
    assert constat(analyse, "R-C2PA-007").categorie is Categorie.INFORMATION_NEUTRE
    assert couverture(analyse) is EtatTechnique.APPLIQUEE
    assert analyse.confiance.fourni_par_utilisateur is True


@pytest.mark.exigence("F-23", "ES-20")
def test_generation_declaree_signataire_hors_liste(tmp_path: Path) -> None:
    analyse = analyse_de(tmp_path, signer())  # liste livrée : l'autorité d'essai n'y est pas
    assert valeurs(analyse)["c2pa.etat"] == "valide_hors_liste"
    assert valeurs(analyse)["c2pa.validation_results.failure"] == ("signingCredential.untrusted",)
    assert regles(analyse) == ["R-C2PA-008", "R-C2PA-004"]
    indice = constat(analyse, "R-C2PA-004")
    assert (indice.categorie, indice.direction, indice.fondement) == (
        Categorie.INDICE,
        Direction.ORIGINE_IA,
        Fondement.DECLARATION,
    )
    assert indice.graduation is not None
    assert indice.graduation.niveau == "faible"
    assert analyse.confiance.nom == "C2PA Trust List"


@pytest.mark.parametrize(
    ("source", "reconnu", "attendues"),
    [
        ("compositeWithTrainedAlgorithmicMedia", True, ["R-C2PA-007", "R-C2PA-002"]),
        ("compositeSynthetic", False, ["R-C2PA-008", "R-C2PA-005"]),
        ("digitalCapture", True, ["R-C2PA-007", "R-C2PA-003"]),
        ("computationalCapture", True, ["R-C2PA-007", "R-C2PA-003"]),
        # Capture sous un certificat non reconnu : aucun constat d'authenticité (ADR-0168).
        ("digitalCapture", False, ["R-C2PA-008"]),
        ("algorithmicMedia", True, ["R-C2PA-007"]),
    ],
)
def test_source_numerique_declaree(
    tmp_path: Path, source: str, reconnu: bool, attendues: list[str]
) -> None:
    liste = reconnue(tmp_path) if reconnu else None
    analyse = analyse_de(tmp_path, signer(definition=manifeste(source)), confiance=liste)
    assert regles(analyse) == attendues


def test_capture_signataire_reconnu_preuve_d_authenticite(tmp_path: Path) -> None:
    analyse = analyse_de(
        tmp_path, signer(definition=manifeste("digitalCapture")), confiance=reconnue(tmp_path)
    )
    preuve = constat(analyse, "R-C2PA-003")
    assert (preuve.categorie, preuve.direction) == (Categorie.PREUVE, Direction.AUTHENTICITE)


@pytest.mark.exigence("ES-20")
def test_contenu_change_depuis_la_signature(tmp_path: Path) -> None:
    signe = bytearray(signer())
    signe[-10] ^= 0xFF  # dans les données de l'image, couvertes par l'empreinte signée
    analyse = analyse_de(tmp_path, bytes(signe), confiance=reconnue(tmp_path))
    assert valeurs(analyse)["c2pa.etat"] == "invalide"
    assert valeurs(analyse)["c2pa.validation_results.failure"] == ("assertion.dataHash.mismatch",)
    # Sous une signature qui ne se vérifie pas, la déclaration n'est qu'un indice (ADR-0167).
    assert regles(analyse) == ["R-C2PA-009", "R-C2PA-006", "R-C2PA-004"]
    indice = constat(analyse, "R-C2PA-006")
    assert (indice.categorie, indice.direction, indice.fondement) == (
        Categorie.INDICE,
        Direction.TRANSFORMATION,
        Fondement.VERIFICATION_CRYPTOGRAPHIQUE,
    )


def test_aucun_manifeste(tmp_path: Path) -> None:
    analyse = analyse_de(tmp_path, (FICHIERS_DU_DEPOT / "photo.jpg").read_bytes())
    assert valeurs(analyse) == {"c2pa.present": False, "c2pa.etat": "absent"}
    assert regles(analyse) == ["R-C2PA-012"]
    assert constat(analyse, "R-C2PA-012").categorie is Categorie.INFORMATION_NEUTRE


@pytest.mark.exigence("ES-06", "ES-10")
def test_manifeste_distant_non_recupere(tmp_path: Path) -> None:
    adresse = "https://exemple.invalid/manifestes/exemplaire-7f3a.c2pa"
    analyse = analyse_de(tmp_path, signer_distant(adresse))
    assert valeurs(analyse) == {
        "c2pa.present": True,
        "c2pa.etat": "non_verifiable",
        "c2pa.erreur": "Remote",
        "c2pa.distant.hote": "exemple.invalid",
    }
    assert regles(analyse) == ["R-C2PA-011"]
    raisons = [(n.raison, n.module) for n in analyse.non_menees if n.module == "c2pa"]
    assert raisons == [(RaisonNonMenee.RESEAU_DESACTIVE, "c2pa")]
    assert couverture(analyse) is EtatTechnique.PARTIELLE
    # Le module c2pa n'inscrit que l'hôte ; l'adresse entière, qui peut désigner l'exemplaire,
    # est observée par xmp et masquée par défaut comme un numéro de série (ADR-0173).
    c2pa_seul = [o.valeur for o in analyse.observations if o.module == "c2pa"]
    assert not any("exemplaire-7f3a" in str(valeur) for valeur in c2pa_seul)
    [provenance] = [o for o in analyse.observations if o.nom == "xmp.dcterms:provenance"]
    assert provenance.valeur == adresse
    assert provenance.identifiante is CategorieIdentifiante.NUMERO_DE_SERIE
    assert "exemplaire-7f3a" not in export.exporter_json(analyse)
    assert "exemplaire-7f3a" not in export.exporter_html(analyse)
    assert "exemplaire-7f3a" in export.exporter_json(analyse, reveler=("numero_de_serie",))


def test_manifeste_illisible(tmp_path: Path) -> None:
    signe = bytearray(signer())
    debut = signe.find(b"jumb")
    signe[debut + 4 : debut + 8] = b"zzzz"  # boîte JUMBF de description remplacée
    analyse = analyse_de(tmp_path, bytes(signe))
    assert valeurs(analyse) == {
        "c2pa.present": True,
        "c2pa.etat": "non_verifiable",
        "c2pa.erreur": "Verify",
    }
    assert regles(analyse) == ["R-C2PA-010"]


def test_conteneur_illisible_recherche_non_menee(tmp_path: Path) -> None:
    # PDF sans table des références : c2pa-rs ne sait pas où chercher un manifeste.
    analyse = analyse_de(tmp_path, b"%PDF-1.7\n1 0 obj<<>>endobj\n%%EOF\n", "document.pdf")
    assert valeurs(analyse) == {}
    raisons = [n.raison for n in analyse.non_menees if n.module == "c2pa"]
    assert raisons == [RaisonNonMenee.FORMAT_PARTIEL]
    assert couverture(analyse) is EtatTechnique.NON_MENEE


@pytest.mark.parametrize("format_", sorted(FICHIERS))
def test_tous_les_formats_du_module(tmp_path: Path, format_: str) -> None:
    nom = FICHIERS[format_]
    analyse = analyse_de(tmp_path, signer(format_), nom, confiance=reconnue(tmp_path))
    assert analyse.identification.format_reel == format_
    assert valeurs(analyse)["c2pa.etat"] == "valide"
    assert regles(analyse) == ["R-C2PA-007", "R-C2PA-001"]


def test_formats_du_manifeste() -> None:
    [livre] = [m for m in decouvrir() if m.identifiant == "c2pa"]
    assert set(livre.formats) == set(c2pa.FORMATS) == set(FICHIERS)
    assert livre.directions == tuple(Direction)
    assert livre.regles == tuple(f"R-C2PA-{n:03d}" for n in range(1, 13))


@pytest.mark.exigence("F-23")
def test_ingredient_restitue(tmp_path: Path) -> None:
    original = signer()
    derive = signer(definition=manifeste(None), contenu=original, ingredient=original)
    analyse = analyse_de(tmp_path, derive, confiance=reconnue(tmp_path))
    lues = valeurs(analyse)
    assert lues["c2pa.manifestes"] == 2
    assert lues["c2pa.ingredients"] == 1
    assert lues["c2pa.ingredients.title"] == ("Original",)
    assert lues["c2pa.ingredients.relationship"] == ("parentOf",)
    assert lues["c2pa.actions.action"] == ("c2pa.opened",)
    assert "c2pa.actions.digitalSourceType" not in lues
    # Les actions de l'ingrédient ne fondent aucune règle : seul le manifeste actif compte.
    assert regles(analyse) == ["R-C2PA-007"]


@pytest.mark.exigence("ES-13", "F-90")
def test_signataire_et_titre_masques_par_defaut(tmp_path: Path) -> None:
    analyse = analyse_de(tmp_path, signer(), confiance=reconnue(tmp_path))
    categories = {o.nom: o.identifiante for o in analyse.observations if o.module == "c2pa"}
    assert (
        categories["c2pa.signature_info.common_name"] is CategorieIdentifiante.METADONNEE_NOMINATIVE
    )
    assert (
        categories["c2pa.signature_info.cert_serial_number"]
        is CategorieIdentifiante.NUMERO_DE_SERIE
    )
    assert categories["c2pa.title"] is CategorieIdentifiante.TEXTE_LIBRE
    assert categories["c2pa.signature_info.issuer"] is None
    masque = export.exporter_json(analyse)
    for valeur in (SIGNATAIRE, str(NUMERO), TITRE):
        assert valeur not in masque
    assert SIGNATAIRE in export.exporter_json(analyse, reveler=("metadonnee_nominative",))


def test_version_de_la_bibliotheque_au_rapport(tmp_path: Path) -> None:
    analyse = analyse_de(tmp_path, signer())
    noms = {d.nom: d.version for d in analyse.dependances}
    assert noms["c2pa-python"] == metadata.version("c2pa-python")
    # Version de c2pa-rs que la fiche provenance-c2pa associe à cette version de c2pa-python.
    assert (metadata.version("c2pa-python"), bibliotheque.sdk_version()) == ("0.39.0", "0.92.0")


def test_ancre_mal_formee_ignoree_par_la_bibliotheque(tmp_path: Path) -> None:
    # Structure DER qui n'est pas un certificat : admise par P1, ignorée par c2pa-rs (ADR-0171).
    bloc = b"-----BEGIN CERTIFICATE-----\nMAMCAQA=\n-----END CERTIFICATE-----\n"
    liste = ecrire_liste(tmp_path / "liste", bloc)
    assert valeurs(analyse_de(tmp_path, signer(), confiance=liste))["c2pa.etat"] == (
        "valide_hors_liste"
    )


# Réglages sans réseau (ADR-0164, ADR-0166)


@pytest.mark.exigence("ES-06", "ES-10")
def test_reglages_sans_reseau() -> None:
    reglages = c2pa.reglages(Ancres("A", "B"))
    assert reglages["core"]["allowed_network_hosts"] == []
    assert reglages["verify"]["remote_manifest_fetch"] is False
    assert reglages["verify"]["ocsp_fetch"] is False
    assert reglages["trust"]["anchors"] == [
        {"trust_kind": "manifest", "trust_anchors": "A"},
        {"trust_kind": "tsa", "trust_anchors": "B"},
    ]
    assert c2pa.reglages(Ancres())["trust"]["anchors"] == []


# Fonctions du module


@pytest.mark.parametrize(
    ("message", "genre"),
    [
        ("Remote: must fetch remote manifests from url https://a.b/c", "Remote"),
        ("ManifestNotFound: no JUMBF data found", "ManifestNotFound"),
        ("sans deux-points", "Other"),
        ("Deux mots: x", "Other"),
        ("", "Other"),
        ("é: x", "Other"),
    ],
)
def test_genre_d_erreur(message: str, genre: str) -> None:
    assert c2pa.genre_d_erreur(Exception(message)) == genre


@pytest.mark.parametrize(
    ("message", "attendu"),
    [
        ("Remote: must fetch remote manifests from url https://Hote.Exemple/x", "hote.exemple"),
        ("Remote: must fetch remote manifests from url http://h.ex:8080/x?y", "h.ex"),
        ("Remote: could not fetch the remote manifest remote URI", None),
        ("Other: must fetch remote manifests from url https://h.ex/x", None),
        ("Remote: must fetch remote manifests from url ftp://h.ex/x", None),
        ("Remote: must fetch remote manifests from url https:///x", None),
        ("Remote: must fetch remote manifests from url https://[::1/x", None),
        ("Remote: must fetch remote manifests from url https://h_é.ex/x", None),
        ("Remote: must fetch remote manifests from url https://" + "a" * 254 + "/x", None),
    ],
)
def test_hote_du_manifeste_distant(message: str, attendu: str | None) -> None:
    assert c2pa.hote(Exception(message)) == attendu


def test_conteneur_illisible() -> None:
    assert c2pa.illisible(Exception("Other: asset could not be parsed: Could not parse"))
    assert not c2pa.illisible(Exception("Verify: asset could not be parsed"))
    assert not c2pa.illisible(Exception("Other: autre chose"))


@pytest.mark.parametrize(
    ("valeur", "code"),
    [
        (IPTC + "trainedAlgorithmicMedia", "trainedalgorithmicmedia"),
        (" https://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture/ ", "digitalcapture"),
        ("compositeSynthetic", "compositesynthetic"),
    ],
)
def test_code_iptc(valeur: str, code: str) -> None:
    assert c2pa.code_iptc(valeur) == code


@pytest.mark.parametrize(
    ("etat", "attendu"),
    [
        ("Trusted", "valide"),
        ("Valid", "valide_hors_liste"),
        ("Invalid", "invalide"),
        ("Autre", "non_verifiable"),
        (None, "non_verifiable"),
    ],
)
def test_etat_de(etat: str | None, attendu: str) -> None:
    assert c2pa.etat_de({} if etat is None else {"validation_state": etat}) == attendu


# Le module dans le processus des tests, sur une sortie de c2pa-rs construite à la main


@pytest.fixture(autouse=True)
def _verrouille(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(garde, "_verrouille", True)


@pytest.fixture
def contexte(tmp_path: Path) -> Iterator[Contexte]:
    contenu = b"\xff\xd8\xff\xd9" * 4
    chemin = tmp_path / "f.jpg"
    chemin.write_bytes(contenu)
    with chemin.open("rb") as fichier:
        yield Contexte(
            "c2pa",
            set(Direction),
            Fichier(fichier.fileno()),
            Partie(1, "jpeg", Plage(0, len(contenu)), fin_connue=True),
            64 << 20,
            regles=catalogues.charger(decouvrir()).du_module("c2pa"),
        )


class _Lecteur:
    def __init__(self, document: Mapping[str, Any]) -> None:
        self._document = document

    def __enter__(self) -> "_Lecteur":
        return self

    def __exit__(self, *_exception: object) -> None:
        return None

    def json(self) -> str:
        return json.dumps(self._document)


def resultats(
    contexte: Contexte, monkeypatch: pytest.MonkeyPatch, document: Mapping[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    monkeypatch.setattr(bibliotheque.Reader, "try_create", lambda *_a, **_o: _Lecteur(document))
    c2pa.analyser(contexte)
    messages = [json.loads(ligne) for ligne in contexte.lignes]
    observations = {
        m["observation"]["nom"]: m["observation"]["valeur"]
        for m in messages
        if m["type"] == "observation"
    }
    identifiants = [
        m["constat"]["regle"]["identifiant"] for m in messages if m["type"] == "constat"
    ]
    return observations, identifiants


@pytest.mark.exigence("F-23")
def test_sortie_sans_resultats_detailles_ni_manifeste_actif(
    contexte: Contexte, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = {
        "validation_state": "Invalid",
        "validation_status": [{"code": "claimSignature.mismatch"}, {"sans": "code"}, "x"],
        "manifests": [],
    }
    observations, identifiants = resultats(contexte, monkeypatch, document)
    assert observations == {
        "c2pa.present": True,
        "c2pa.etat": "invalide",
        "c2pa.manifestes": 0,
        "c2pa.validation_results.failure": ["claimSignature.mismatch"],
        "c2pa.validation_results.informational": [],
        "c2pa.ingredients": 0,
    }
    assert identifiants == ["R-C2PA-009", "R-C2PA-006"]


@pytest.mark.exigence("F-23")
def test_manifeste_de_la_premiere_version_et_ingredients_invalides(
    contexte: Contexte, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = {
        "validation_state": "Valid",
        "active_manifest": "m",
        "manifests": {
            "m": {
                "claim_generator": "Outil/1.0",
                "claim_generator_info": [{"autre": 1}, "x"],
                "assertions": [
                    {
                        "label": "c2pa.actions",
                        "data": {
                            "actions": [
                                {"action": "c2pa.edited", "softwareAgent": "Retoucheur 3"},
                                {"sans": "action"},
                                {"action": "c2pa.opened", "softwareAgent": 7},
                            ]
                        },
                    },
                    {"label": "c2pa.thumbnail.claim.jpeg", "data": {"actions": [{"action": "x"}]}},
                    {"label": "c2pa.actions.v2", "data": "pas un objet"},
                ],
                "ingredients": [{"title": "A", "relationship": "componentOf"}, {"title": ""}],
                "signature_info": {"alg": "Ps256", "time": "2026-11-14T08:00:00+00:00"},
            }
        },
        "validation_results": {
            "activeManifest": {"failure": [{"code": "signingCredential.untrusted"}]},
            "ingredientDeltas": [
                {"validationDeltas": {"failure": [{"code": "assertion.dataHash.mismatch"}]}},
                {"validationDeltas": {}},
            ],
        },
    }
    observations, identifiants = resultats(contexte, monkeypatch, document)
    assert observations["c2pa.claim_generator_info"] == ["Outil/1.0"]
    assert observations["c2pa.actions.action"] == ["c2pa.edited", "c2pa.opened"]
    assert observations["c2pa.actions.softwareAgent"] == ["Retoucheur 3"]
    assert observations["c2pa.signature_info.time"] == "2026-11-14T08:00:00+00:00"
    assert observations["c2pa.ingredients"] == 2
    assert observations["c2pa.ingredients.title"] == ["A"]
    assert observations["c2pa.ingredients.relationship"] == ["componentOf"]
    assert observations["c2pa.ingredients.validationDeltas.failure"] == [
        "assertion.dataHash.mismatch"
    ]
    assert identifiants == ["R-C2PA-008"]


def test_invalide_sans_ecart_d_empreinte(
    contexte: Contexte, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Un certificat expiré rend le manifeste invalide sans dire le contenu changé (ADR-0167).
    document = {
        "validation_state": "Invalid",
        "active_manifest": "m",
        "manifests": {
            "m": {"assertions": [{"label": "c2pa.actions", "data": {"actions": [{"action": "x"}]}}]}
        },
        "validation_results": {
            "activeManifest": {"failure": [{"code": "signingCredential.expired"}]}
        },
    }
    observations, identifiants = resultats(contexte, monkeypatch, document)
    assert identifiants == ["R-C2PA-009"]
    assert observations["c2pa.actions.action"] == ["x"]
    assert "c2pa.actions.softwareAgent" not in observations


def test_etat_inconnu_non_verifiable(contexte: Contexte, monkeypatch: pytest.MonkeyPatch) -> None:
    observations, identifiants = resultats(contexte, monkeypatch, {"validation_state": "Autre"})
    assert observations["c2pa.etat"] == "non_verifiable"
    assert observations["c2pa.erreur"] == "ValidationState"
    assert identifiants == ["R-C2PA-010"]


def test_reglages_refuses_hors_du_constat(
    contexte: Contexte, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Des ancres que c2pa-rs refuse sont un défaut de la liste : le module lève, le moteur en
    # fait une analyse non menée (ADR-0060), sans rien dire du fichier.
    def refuser(*_arguments: object) -> None:
        raise bibliotheque.C2paError("Signature: COSE error parsing certificate")

    monkeypatch.setattr(bibliotheque.Context, "from_dict", refuser)
    with pytest.raises(bibliotheque.C2paError):
        c2pa.analyser(contexte)
    assert contexte.lignes == ()


def _altere(contenu: bytes) -> bytes:
    signe = bytearray(contenu)
    signe[-10] ^= 0xFF
    return bytes(signe)


def _jumbf_casse(contenu: bytes) -> bytes:
    signe = bytearray(contenu)
    debut = signe.find(b"jumb")
    signe[debut + 4 : debut + 8] = b"zzzz"
    return bytes(signe)


@pytest.mark.exigence("F-23", "ES-20")
@pytest.mark.parametrize(
    ("cas", "reconnu", "format_", "attendues", "raisons"),
    [
        ("ia", True, "jpeg", ["R-C2PA-007", "R-C2PA-001"], []),
        ("retouche", True, "jpeg", ["R-C2PA-007", "R-C2PA-002"], []),
        ("capture", True, "jpeg", ["R-C2PA-007", "R-C2PA-003"], []),
        ("capture", False, "jpeg", ["R-C2PA-008"], []),
        ("ia", False, "jpeg", ["R-C2PA-008", "R-C2PA-004"], []),
        ("altere", True, "jpeg", ["R-C2PA-009", "R-C2PA-006", "R-C2PA-004"], []),
        ("casse", False, "jpeg", ["R-C2PA-010"], []),
        ("distant", False, "jpeg", ["R-C2PA-011"], ["reseau_desactive"]),
        ("absent", False, "jpeg", ["R-C2PA-012"], []),
        ("illisible", False, "pdf", [], ["format_partiel"]),
    ],
)
def test_module_dans_le_processus_des_tests(
    tmp_path: Path,
    cas: str,
    reconnu: bool,
    format_: str,
    attendues: list[str],
    raisons: list[str],
) -> None:
    # Mêmes cas que les analyses de bout en bout, sans processus de travail : la couverture du
    # code mesure aussi ce que c2pa-rs renvoie réellement (ADR-0170).
    sources = {"ia": "trainedAlgorithmicMedia", "retouche": "compositeSynthetic"}
    contenus: dict[str, Callable[[], bytes]] = {
        "ia": lambda: signer(),
        "retouche": lambda: signer(definition=manifeste(sources["retouche"])),
        "capture": lambda: signer(definition=manifeste("digitalCapture")),
        "altere": lambda: _altere(signer()),
        "casse": lambda: _jumbf_casse(signer()),
        "distant": lambda: signer_distant("https://exemple.invalid/m.c2pa"),
        "absent": lambda: (FICHIERS_DU_DEPOT / "photo.jpg").read_bytes(),
        "illisible": lambda: b"%PDF-1.7\n1 0 obj<<>>endobj\n%%EOF\n",
    }
    contenu = contenus[cas]()
    chemin = tmp_path / "f"
    chemin.write_bytes(contenu)
    ancres = Ancres(autorite().racine.decode()) if reconnu else Ancres()
    with chemin.open("rb") as fichier:
        module = Contexte(
            "c2pa",
            set(Direction),
            Fichier(fichier.fileno()),
            Partie(1, format_, Plage(0, len(contenu)), fin_connue=True),
            64 << 20,
            regles=catalogues.charger(decouvrir()).du_module("c2pa"),
            ancres=ancres,
        )
        c2pa.analyser(module)
    messages = [json.loads(ligne) for ligne in module.lignes]
    assert [m["constat"]["regle"]["identifiant"] for m in messages if m["type"] == "constat"] == (
        attendues
    )
    assert [m["non_menee"]["raison"] for m in messages if m["type"] == "non_menee"] == raisons


def test_flux_de_la_partie(contexte: Contexte) -> None:
    flux = c2pa._Flux(contexte)
    assert flux.readable()
    assert flux.seekable()
    assert flux.read() == b"\xff\xd8\xff\xd9" * 4
    assert flux.tell() == 16
    assert flux.seek(-4, io.SEEK_END) == 12
    assert flux.seek(2, io.SEEK_CUR) == 14
    assert flux.read(8) == b"\xff\xd9"
    assert flux.read(8) == b""
    with pytest.raises(ValueError, match="négative"):
        flux.seek(-1)
    with pytest.raises(io.UnsupportedOperation):
        flux.write(b"x")
