"""Rapport HTML autonome : aucun script, aucune ressource externe (ADR-0025, ADR-0094).

Le document est écrit par ce module, sans moteur de gabarits. Tout texte y entre par :func:`_t`,
qui neutralise les caractères invisibles puis échappe le HTML (ES-12) ; seules les balises
écrites ici sont du HTML. La politique de sécurité du contenu n'autorise que la feuille de style
du document, désignée par son empreinte : ni script, ni image, ni police, ni formulaire, ni
ressource distante (M-20).

Structure pour l'accessibilité (WCAG 2.2 AA, ADR-0025) : langue déclarée, un titre de niveau 1,
rubriques en titres de niveau 2, tableaux avec légende et en-têtes, lien d'évitement, aucune
information portée par la couleur seule ; contraste du texte d'au moins 7:1, des traits d'au moins
3:1, en mode clair comme sombre.
"""

import base64
import hashlib
from collections.abc import Collection, Iterable
from html import escape
from importlib.metadata import version

from voight_kampff.analyse import Analyse
from voight_kampff.rapport._presentation import (
    Presentation,
    etat_partie,
    libelle,
    localisation,
    neutraliser,
    nombre,
    octets,
    texte,
    textes,
)
from voight_kampff.rapport.modele import (
    Categorie,
    CategorieIdentifiante,
    Constat,
    NiveauIsolation,
)

__all__ = ["STYLE", "html", "politique"]

STYLE = """
:root{color-scheme:light dark;--fond:#fff;--texte:#1b1b1b;--discret:#3d3d3d;--lien:#0b4f9c;
--trait:#6b6b6b;--alerte:#fff4e5;--bord-alerte:#8a4b00;--zebre:#f3f3f3}
@media (prefers-color-scheme:dark){:root{--fond:#121212;--texte:#ececec;--discret:#c8c8c8;
--lien:#9cc3ff;--trait:#9a9a9a;--alerte:#2b1d0a;--bord-alerte:#f0b35a;--zebre:#1e1e1e}}
*{box-sizing:border-box}
body{margin:0 auto;max-width:60rem;padding:1rem;background:var(--fond);color:var(--texte);
font:1rem/1.5 system-ui,sans-serif}
a{color:var(--lien)}
a:focus-visible{outline:3px solid var(--lien);outline-offset:2px}
.evitement{position:absolute;left:-100vw}
.evitement:focus{position:static}
h1{font-size:1.75rem}h2{font-size:1.4rem;margin-top:2.5rem;border-bottom:1px solid var(--trait)}
h3{font-size:1.1rem}
.alertes{background:var(--alerte);border-left:6px solid var(--bord-alerte);padding:.5rem 1rem}
.discret{color:var(--discret)}
dl{display:grid;grid-template-columns:minmax(10rem,auto) 1fr;gap:.25rem 1rem}
dt{font-weight:600}dd{margin:0}
dd,td{overflow-wrap:anywhere}
.defilement{overflow-x:auto}
table{border-collapse:collapse;width:100%}
caption{text-align:left;font-weight:600;padding:.25rem 0}
th,td{border:1px solid var(--trait);padding:.25rem .5rem;text-align:left;vertical-align:top}
tbody tr:nth-child(even){background:var(--zebre)}
article{border:1px solid var(--trait);padding:0 1rem .5rem;margin:1rem 0}
@media print{body{max-width:none}.evitement{display:none}article,tr{break-inside:avoid}}
"""
"""Feuille de style du rapport : sa seule ressource, autorisée par son empreinte."""


def politique() -> str:
    """Politique de sécurité du contenu : rien d'autre que la feuille de style (ES-12)."""
    condensat = base64.b64encode(hashlib.sha256(STYLE.encode()).digest()).decode()
    return (
        f"default-src 'none'; style-src 'sha256-{condensat}'; base-uri 'none'; form-action 'none'"
    )


def _t(chaine: str) -> str:
    """Seule entrée du texte dans le document : neutralisé, puis échappé (ES-12)."""
    return escape(neutraliser(chaine), quote=True)


def _terme(cle: str) -> str:
    """Lien vers la définition d'un terme dans le glossaire du rapport (NF-11)."""
    return f'<a href="#g-{cle}">{_t(textes()["glossaire"][cle][0])}</a>'


def _liste(elements: Iterable[str]) -> str:
    return "<ul>" + "".join(f"<li>{_t(element)}</li>" for element in elements) + "</ul>"


def _definitions(couples: Iterable[tuple[str, str]]) -> str:
    """Liste de définitions ; chaque couple est déjà du HTML (libellé, valeur)."""
    return "<dl>" + "".join(f"<dt>{dt}</dt><dd>{dd}</dd>" for dt, dd in couples) + "</dl>"


def _champ(cle: str) -> str:
    return _t(texte(f"champs.{cle}"))


def _tableau(legende: str, entetes: list[str], lignes: Iterable[list[str]]) -> str:
    """Tableau ; les cellules sont du texte, échappé ici. Défilement horizontal au clavier."""
    tete = "".join(f'<th scope="col">{_t(entete)}</th>' for entete in entetes)
    corps = "".join(
        "<tr>" + "".join(f"<td>{_t(c)}</td>" for c in ligne) + "</tr>" for ligne in lignes
    )
    return (
        f'<div class="defilement" role="region" tabindex="0" aria-label="{_t(legende)}">'
        f"<table><caption>{_t(legende)}</caption><thead><tr>{tete}</tr></thead>"
        f"<tbody>{corps}</tbody></table></div>"
    )


def _rubrique(identifiant: str, contenu: str) -> str:
    titre = _t(texte(f"rubriques.{identifiant}"))
    return (
        f'<section id="{identifiant}" aria-labelledby="t-{identifiant}">'
        f'<h2 id="t-{identifiant}">{titre}</h2>{contenu}</section>'
    )


def _constat(vue: Presentation, constat: Constat) -> str:
    regle = vue.regle(constat)
    couples = [
        (_champ("categorie"), _terme(constat.categorie)),
        (_terme("direction"), _t(libelle("directions", constat.direction))),
    ]
    if constat.graduation is not None:
        couples.append((_terme("niveau"), _t(libelle("niveaux", constat.graduation.niveau))))
        couples.append((_champ("evaluation"), _t(vue.evaluation(regle))))
    couples += [
        (_terme("fondement"), _t(libelle("fondements", constat.fondement))),
        (
            _terme("regle"),
            _t(
                texte(
                    "formes.regle",
                    identifiant=regle.identifiant,
                    version=regle.version,
                    titre=regle.titre,
                )
            ),
        ),
        (
            _champ("donnees"),
            _liste(
                f"{vue.observation(i).nom} : {vue.valeur(vue.observation(i))}"
                for i in constat.donnees
            ),
        ),
        (_champ("limites"), _liste(regle.limites)),
        (_champ("partie"), _t(str(constat.partie))),
    ]
    if constat.localisation is not None:
        couples.append((_champ("localisation"), _t(localisation(constat.localisation))))
    return f"<article><h3>{_t(vue.phrase(constat))}</h3>{_definitions(couples)}</article>"


def _constats(vue: Presentation, categorie: Categorie, aucun: str) -> str:
    choisis = vue.constats(categorie)
    if not choisis:
        return f"<p>{_t(texte(aucun))}</p>"
    return "".join(_constat(vue, constat) for constat in choisis)


def _identification(vue: Presentation) -> str:
    identification = vue.analyse.identification
    couples = [
        (_champ("nom"), _t(vue.nom())),
        (_terme("format_reel"), _t(identification.format_reel)),
        (_champ("extension"), _t(identification.extension or texte("aucune"))),
        (_champ("taille"), _t(texte("formes.taille", octets=nombre(identification.taille)))),
        (_terme("empreinte"), _t(vue.empreinte())),
        (_champ("date_analyse"), _t(identification.date_analyse.strftime("%Y-%m-%d %H:%M:%S"))),
    ]
    parties = _tableau(
        texte("champs.parties"),
        [
            texte("champs.partie"),
            texte("champs.format"),
            texte("champs.octets"),
            texte("champs.etat"),
        ],
        (
            [str(partie.rang), partie.format, octets(partie.octets), etat_partie(partie)]
            for partie in identification.parties
        ),
    )
    return _definitions(couples) + _liste(vue.signalements()) + parties


def _versions(vue: Presentation) -> str:
    dependances = vue.analyse.dependances
    couples = [
        (_champ("outil"), _t(version("voight-kampff-forensics"))),
        (_champ("catalogue"), _t(vue.catalogue())),
        (
            _champ("dependances"),
            _liste(f"{d.nom} {d.version}" for d in dependances)
            if dependances
            else _t(texte("aucune")),
        ),
    ]
    return _definitions(couples)


def _isolation(vue: Presentation) -> str:
    isolation = vue.analyse.isolation
    couples = [(_terme("isolation"), _t(libelle("isolation", isolation.niveau)))]
    if isolation.niveau is NiveauIsolation.REDUITE:
        couples.append(
            (_champ("manques"), _liste(libelle("manques", m) for m in isolation.manques))
        )
    return _definitions(couples)


def _non_menees(vue: Presentation) -> str:
    non_menees = vue.analyse.non_menees
    if not non_menees:
        return f"<p>{_t(texte('resume.non_menees_aucune'))}</p>"
    return _tableau(
        texte("intros.legende_non_menees"),
        [
            texte("champs.raison"),
            texte("champs.technique"),
            texte("champs.partie"),
            texte("champs.localisation"),
        ],
        (
            [
                vue.non_menee(n),
                n.module or "",
                str(n.partie) if n.partie else "",
                localisation(n.localisation) if n.localisation else "",
            ]
            for n in non_menees
        ),
    )


def _couverture(vue: Presentation) -> str:
    couverture = vue.analyse.couverture
    techniques = _tableau(
        texte("intros.legende_couverture"),
        [
            texte("champs.technique"),
            texte("champs.partie"),
            texte("champs.version"),
            texte("champs.etat"),
        ],
        (
            [
                t.module,
                str(t.partie),
                t.version or texte("formes.hors_version"),
                libelle("etats", t.etat),
            ]
            for t in couverture.techniques
        ),
    )
    marquages = couverture.marquages_recherches
    return (
        f"<p>{_t(texte('intros.couverture'))}</p>"
        + techniques
        + _definitions(
            [
                (
                    _champ("marquages"),
                    _liste(marquages) if marquages else _t(texte("aucun")),
                )
            ]
        )
    )


def _donnees_identifiantes(vue: Presentation) -> str:
    etats = _tableau(
        texte("intros.legende_identifiantes"),
        [texte("champs.categorie_identifiante"), texte("champs.masquage")],
        (
            [
                libelle("identifiantes", c),
                texte("formes.masquee") if vue.masquee(c) else texte("formes.levee"),
            ]
            for c in CategorieIdentifiante
        ),
    )
    intro = _t(texte("intros.donnees_identifiantes"))
    return f"<p>{intro}</p>{etats}<p>{_t(texte('formes.lever'))}</p>"


def _observations(vue: Presentation) -> str:
    observations = vue.analyse.observations
    if not observations:
        return f"<p>{_t(texte('aucune'))}</p>"
    return f"<p>{_t(texte('intros.observations'))}</p>" + _tableau(
        texte("intros.legende_observations"),
        [
            texte("champs.identifiant"),
            texte("champs.technique"),
            texte("champs.partie"),
            texte("champs.nom_observation"),
            texte("champs.valeur"),
            texte("champs.localisation"),
        ],
        (
            [
                o.identifiant,
                o.module,
                str(o.partie),
                o.nom,
                vue.valeur(o),
                localisation(o.localisation) if o.localisation else "",
            ]
            for o in observations
        ),
    )


def _glossaire() -> str:
    entrees = textes()["glossaire"]
    return (
        "<dl>"
        + "".join(
            f'<dt id="g-{cle}">{_t(terme)}</dt><dd>{_t(definition)}</dd>'
            for cle, (terme, definition) in entrees.items()
        )
        + "</dl>"
    )


def _resume(vue: Presentation) -> str:
    return _liste(vue.resume())


def html(analyse: Analyse, masquees: Collection[CategorieIdentifiante]) -> str:
    """Document HTML complet du rapport, dans l'ordre d'ADR-0098."""
    vue = Presentation(analyse, masquees)
    alertes = vue.alertes()
    entete = (
        f'<section class="alertes" aria-labelledby="t-alertes">'
        f'<h2 id="t-alertes">{_t(texte("rubriques.alertes"))}</h2>{_liste(alertes)}</section>'
        if alertes
        else ""
    )
    corps = "".join(
        [
            entete,
            _rubrique(
                "avertissement", "".join(f"<p>{_t(p)}</p>" for p in textes()["avertissement"])
            ),
            _rubrique("resume", _resume(vue)),
            _rubrique("identification", _identification(vue)),
            _rubrique("versions", _versions(vue)),
            _rubrique("isolation", _isolation(vue)),
            _rubrique("preuves", _constats(vue, Categorie.PREUVE, "resume.preuves_aucune")),
            _rubrique("indices", _constats(vue, Categorie.INDICE, "resume.indices_aucun")),
            _rubrique(
                "informations",
                _constats(vue, Categorie.INFORMATION_NEUTRE, "aucune"),
            ),
            _rubrique("non_menees", _non_menees(vue)),
            _rubrique("couverture", _couverture(vue)),
            _rubrique("donnees_identifiantes", _donnees_identifiantes(vue)),
            _rubrique("observations", _observations(vue)),
            _rubrique("glossaire", _glossaire()),
        ]
    )
    titre = _t(texte("titre"))
    outil = _t(f"Voight-Kampff {version('voight-kampff-forensics')}")
    date = _t(analyse.identification.date_analyse.strftime("%Y-%m-%d %H:%M:%S UTC"))
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{politique()}">\n'
        '<meta name="referrer" content="no-referrer">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{titre} — {_t(analyse.identification.format_reel)}</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n"
        f'<a class="evitement" href="#resume">{_t(texte("evitement"))}</a>\n'
        f'<header><h1>{titre}</h1><p class="discret">{outil} · {date}</p></header>\n'
        f"<main>\n{corps}\n</main>\n</body>\n</html>\n"
    )
