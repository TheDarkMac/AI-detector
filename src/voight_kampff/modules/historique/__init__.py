"""Module ``historique`` : historique d'édition d'un DOCX ou d'un ODT (F-71 ; T81, ADR-0248 à
ADR-0251 ; fiche ``historique-edition``).

Le module lit, pour son propre compte, ce que le document garde de la façon dont il a été
écrit (ADR-0249) :

- **temps d'édition** et **enregistrements** : ``TotalTime`` des propriétés étendues et
  ``cp:revision`` des propriétés principales d'un DOCX ; ``meta:editing-duration`` et
  ``meta:editing-cycles`` de ``meta.xml`` d'un ODT. La durée est observée en minutes entières ;
- **sessions d'édition** : identifiants de révision (« rsid ») que Word inscrit dans
  ``word/settings.xml`` (``w:rsids``) et sur les paragraphes et courses du corps
  (ECMA-376, partie 1) ; ceux que LibreOffice porte dans les styles
  automatiques de ``content.xml`` (``officeooo:rsid``, ``officeooo:paragraph-rsid``). Les
  caractères du texte visible du corps sont rangés par session ;
- **modifications suivies** et **commentaires** : marques de révision du corps d'un DOCX
  (``w:ins``, ``w:del``, ``w:moveFrom``, ``w:rPrChange``…, ECMA-376, partie 1) et
  commentaires de ``word/comments.xml`` ; régions de ``text:tracked-changes`` et annotations
  (``office:annotation``) de ``content.xml`` d'un ODT. Ils sont comptés, leurs auteurs
  distincts comptés sans être observés (ADR-0250) ; leurs dates servent à une seule
  comparaison, lues sans leur fuseau ;
- **écart** entre création et dernier enregistrement : ``dcterms:created`` et
  ``dcterms:modified`` d'un DOCX, ``meta:creation-date`` et ``dc:date`` d'un ODT, lus comme les
  règles de T23 lisent les dates (ADR-0148) : le plus grand écart que permettent leurs écritures.

Rien n'est observé qui nomme une personne : ni auteur, ni dernier modificateur (ceux-là, les
modules ``ooxml`` et ``odf`` les observent déjà). Le module n'émet aucun constat : les règles du
catalogue lisent ses observations, toutes des informations neutres (ADR-0251).
"""

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import unquote

from voight_kampff._dates import Intervalle, Lecture, lire
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.arbre import Noeud, Ouvrir, lire_arbre, parcourir
from voight_kampff.modules._lecture.zip import Archive, Entree, Illisible
from voight_kampff.rapport.modele import Localisation, RaisonNonMenee

__all__ = ["CHANGEMENTS_DOCX", "analyser", "duree_iso8601", "sans_fuseau"]

# DOCX

_RELATIONS = "http://schemas.openxmlformats.org/package/2006/relationships"
_TRANSITIONNEL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
_STRICT = "http://purl.oclc.org/ooxml/officeDocument/relationships/"
_SORTES = {
    "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties": "core",
    # Écriture des premières versions d'Office 2007, encore lue par les logiciels (ADR-0139).
    f"{_TRANSITIONNEL.lower()}metadata/core-properties": "core",
    f"{_TRANSITIONNEL}extended-properties": "app",
    f"{_STRICT}extendedProperties": "app",
    f"{_TRANSITIONNEL}officeDocument": "principale",
    f"{_STRICT}officeDocument": "principale",
    f"{_TRANSITIONNEL}settings": "reglages",
    f"{_STRICT}settings": "reglages",
    f"{_TRANSITIONNEL}comments": "commentaires",
    f"{_STRICT}comments": "commentaires",
}
"""Relations suivies, par leur type : propriétés depuis le paquet ; réglages et commentaires
depuis la partie principale."""
_W = frozenset(
    {
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://purl.oclc.org/ooxml/wordprocessingml/main",
    }
)
_APP = frozenset(
    {
        "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
        "http://purl.oclc.org/ooxml/officeDocument/extendedProperties",
    }
)
_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
_DCTERMS = "http://purl.org/dc/terms/"
CHANGEMENTS_DOCX = frozenset(
    {
        "ins",
        "del",
        "moveFrom",
        "moveTo",
        "rPrChange",
        "pPrChange",
        "sectPrChange",
        "tblPrChange",
        "tblPrExChange",
        "trPrChange",
        "tcPrChange",
        "tblGridChange",
        "numberingChange",
        "cellIns",
        "cellDel",
        "cellMerge",
    }
)
"""Marques de révision d'ECMA-376 (partie 1) : chacune est une modification suivie,
avec son auteur et sa date. Les bornes d'un déplacement (``moveFromRangeStart``…) n'en sont pas :
le texte déplacé est marqué par ``moveFrom`` et ``moveTo``."""
_SUPPRESSIONS = frozenset({"del", "moveFrom"})
"""Leur texte ne s'affiche pas : il n'est pas compté dans les sessions du texte (ADR-0240)."""

# ODT

_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
_META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
_DC = "http://purl.org/dc/elements/1.1/"
_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_STYLE = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
_OFFICEOOO = "http://openoffice.org/2009/office"
"""Espace des extensions de LibreOffice, où il écrit les identifiants de session."""
_HORS_DU_TEXTE = frozenset({(_TEXT, "tracked-changes"), (_OFFICE, "annotation"), (_TEXT, "note")})
"""Ce qui n'est pas le texte du corps : texte supprimé, commentaires, notes (dont un DOCX range
le texte dans d'autres parties)."""
_EXCLUS = frozenset(
    {
        _DC,
        _META,
        "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
        "http://www.w3.org/2000/svg",
    }
)
"""Espaces dont le texte n'est pas celui du document : titre et description d'une image."""

_DUREE = re.compile(
    r"P(?:([0-9]{1,18})Y)?(?:([0-9]{1,18})M)?(?:([0-9]{1,18})D)?"
    r"(?:T(?:([0-9]{1,18})H)?(?:([0-9]{1,18})M)?(?:([0-9]{1,18})(?:[.,][0-9]{1,18})?S)?)?"
)
"""Durée de XML Schema (``xsd:duration``) sans signe ; expression fixe, temps linéaire."""
_FUSEAU = re.compile(r"(?:Z|[+-][0-9]{2}(?::?[0-9]{2})?)\Z")
_MINUTE = 60_000_000
"""Une minute, en microsecondes : l'unité des intervalles de ``_dates``."""
_ENTIER = re.compile(r"[0-9]{1,18}")


def duree_iso8601(texte: str) -> int | None:
    """Minutes entières d'une durée ``xsd:duration`` ; ``None`` si elle ne s'écrit pas ainsi,
    ou compte des années ou des mois, dont la longueur varie."""
    nettoye = texte.strip()
    trouve = _DUREE.fullmatch(nettoye)
    if trouve is None or nettoye in ("P", "PT") or nettoye.endswith("T"):
        return None
    annees, mois, jours, heures, minutes, secondes = (int(g or "0") for g in trouve.groups())
    if annees or mois:
        return None
    return (jours * 86400 + heures * 3600 + minutes * 60 + secondes) // 60


def sans_fuseau(texte: str) -> str:
    """Date d'une modification ou d'un commentaire sans son fuseau : dans un DOCX, Word et
    LibreOffice y écrivent l'heure locale suivie de ``Z`` (ADR-0250)."""
    nettoye = texte.strip()
    if "T" not in nettoye:
        return nettoye
    return _FUSEAU.sub("", nettoye)


def _entier(texte: str) -> int | None:
    """Entier positif ou nul écrit en chiffres (espaces autour admis), sinon ``None``."""
    nettoye = texte.strip().removeprefix("+")
    return int(nettoye) if _ENTIER.fullmatch(nettoye) else None


@dataclass(slots=True)
class _Releve:
    """Ce que le module a trouvé, observé à la fin de la lecture."""

    duree: tuple[int, Localisation] | None = None
    revisions: tuple[int, Localisation] | None = None
    creation: str | None = None
    modification: tuple[str, Localisation] | None = None
    sessions: set[str] = field(default_factory=set)
    sessions_lieu: Localisation | None = None
    texte: Counter[str | None] = field(default_factory=Counter)
    """Caractères du texte visible du corps, par session ; ``None`` : sans session."""
    corps: Localisation | None = None
    """Lieu du corps, s'il a été lu : texte et modifications sont alors observés."""
    modifications: int = 0
    auteurs_modifications: set[str] = field(default_factory=set)
    commentaires: int = 0
    auteurs_commentaires: set[str] = field(default_factory=set)
    commentaires_lieu: Localisation | None = None
    dates: list[str] = field(default_factory=list)
    """Dates des modifications et des commentaires, telles qu'écrites."""


class _Lecteur:
    """Archive, contexte, et les erreurs d'une partie déclarées non menées."""

    def __init__(self, contexte: Contexte, archive: Archive) -> None:
        self.contexte = contexte
        self.archive = archive

    def trouver(self, nom: str, *, casse: bool) -> Entree | None:
        try:
            return self.archive.trouver(nom, casse=casse)
        except Illisible as illisible:  # deux entrées de ce nom
            self.contexte.non_mener(illisible.raison, localisation=Localisation(chemin=nom))
            return None

    def lire(self, entree: Entree) -> tuple[bytes, Localisation] | None:
        try:
            return self.archive.lire(entree), self.archive.localisation(entree)
        except Illisible as illisible:
            # La localisation de l'entrée relirait l'en-tête qui vient d'échouer : celle de l'arrêt.
            raison, lieu = illisible.raison, illisible.localisation(self.contexte.taille)
            self.contexte.non_mener(raison, localisation=lieu)
            return None

    def existe(self, nom: str, *, casse: bool) -> bool:
        """Vrai si l'archive a au moins une entrée de ce nom ; sinon, référence manquante."""
        minuscules = _ascii_minuscules(nom)
        if any(
            e.nom == nom if casse else _ascii_minuscules(e.nom) == minuscules
            for e in self.archive.entrees
        ):
            return True
        self.contexte.non_mener(RaisonNonMenee.REFERENCE_MANQUANTE, localisation=Localisation(nom))
        return False

    def designee(self, nom: str) -> tuple[bytes, Localisation] | None:
        """Partie qu'une relation désigne : absente de l'archive, c'est une référence manquante."""
        return self.partie(nom, casse=False) if self.existe(nom, casse=False) else None

    def partie(self, nom: str, *, casse: bool) -> tuple[bytes, Localisation] | None:
        entree = self.trouver(nom, casse=casse)
        return None if entree is None else self.lire(entree)

    def arbre(self, donnees: bytes, lieu: Localisation) -> list[Noeud]:
        racines, partiel = lire_arbre(self.contexte, donnees)
        if partiel:
            self.partiel(lieu)
        return racines

    def parcourir(
        self,
        donnees: bytes,
        lieu: Localisation,
        ouvrir: Ouvrir,
        fermer: Callable[[], object],
        texte: Callable[[str], None],
    ) -> None:
        if parcourir(self.contexte, donnees, ouvrir, fermer, texte):
            self.partiel(lieu)

    def partiel(self, lieu: Localisation) -> None:
        self.contexte.non_mener(RaisonNonMenee.FORMAT_PARTIEL, localisation=lieu)


def analyser(contexte: Contexte) -> None:
    try:
        archive = Archive(contexte)
    except Illisible as illisible:
        contexte.observer("historique.present", False)
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    lecteur = _Lecteur(contexte, archive)
    releve = _Releve()
    if contexte.format_reel == "odt":
        _odt(lecteur, releve)
    else:
        _docx(lecteur, releve)
    _observer(contexte, releve)


# DOCX


def _cible(source: str, cible: str) -> str | None:
    """Nom de la partie que désigne une cible relative à la partie source (OPC, partie 2)."""
    dossier = source.rpartition("/")[0]
    chemin = unquote(cible)
    if all(segment in ("", ".", "..") for segment in chemin.split("/")):
        return None
    segments: list[str] = [] if chemin.startswith("/") or not dossier else dossier.split("/")
    for segment in chemin.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)
    return "/".join(segments)


def _relations(lecteur: _Lecteur, source: str) -> dict[str, str] | None:
    """Première partie de chaque sorte suivie que désignent les relations internes d'une partie
    ; ``None`` si ses relations manquent."""
    dossier, _, nom = source.rpartition("/")
    lue = lecteur.partie(f"{dossier}/_rels/{nom}.rels" if dossier else "_rels/.rels", casse=False)
    if lue is None:
        return None
    trouvees: dict[str, str] = {}
    for racine in lecteur.arbre(*lue):
        for relation in racine.enfants:
            if not relation.est(_RELATIONS, "Relationship"):
                continue
            if relation.attributs.get(("", "TargetMode")) == "External":
                continue
            sorte = _SORTES.get(relation.attributs.get(("", "Type"), ""))
            cible = _cible(source, relation.attributs.get(("", "Target"), ""))
            if sorte is not None and cible is not None:
                trouvees.setdefault(sorte, cible)
    return trouvees


def _docx(lecteur: _Lecteur, releve: _Releve) -> None:
    paquet = _relations(lecteur, "") or {}
    if "app" in paquet:
        _app(lecteur, releve, paquet["app"])
    if "core" in paquet:
        _core(lecteur, releve, paquet["core"])
    principale = paquet.get("principale")
    if principale is None:
        lecteur.contexte.non_mener(
            RaisonNonMenee.REFERENCE_MANQUANTE, localisation=Localisation("_rels/.rels")
        )
        return
    annexes = _relations(lecteur, principale) or {}
    if "reglages" in annexes:
        _reglages(lecteur, releve, annexes["reglages"])
    lue = lecteur.designee(principale)
    if lue is None:
        return
    _corps_docx(lecteur, releve, *lue)
    releve.commentaires_lieu = lue[1]
    if "commentaires" in annexes:
        commentaires = lecteur.designee(annexes["commentaires"])
        if commentaires is not None:
            _commentaires_docx(lecteur, releve, *commentaires)


def _texte_de(noeud: Noeud) -> str:
    return "".join(noeud.texte)


def _app(lecteur: _Lecteur, releve: _Releve, nom: str) -> None:
    lue = lecteur.designee(nom)
    if lue is None:
        return
    for racine in lecteur.arbre(*lue):
        for element in racine.enfants:
            if element.espace in _APP and element.nom == "TotalTime" and releve.duree is None:
                minutes = _entier(_texte_de(element))
                if minutes is not None:
                    releve.duree = (minutes, lue[1])


def _core(lecteur: _Lecteur, releve: _Releve, nom: str) -> None:
    lue = lecteur.designee(nom)
    if lue is None:
        return
    for racine in lecteur.arbre(*lue):
        for element in racine.enfants:
            texte = _texte_de(element).strip()
            if element.est(_CP, "revision") and releve.revisions is None:
                nombre = _entier(texte)
                if nombre is not None:
                    releve.revisions = (nombre, lue[1])
            elif element.est(_DCTERMS, "created") and releve.creation is None and texte:
                releve.creation = texte
            elif element.est(_DCTERMS, "modified") and releve.modification is None and texte:
                releve.modification = (texte, lue[1])


def _valeur_w(attributs: dict[tuple[str, str], str], nom: str) -> str | None:
    """Attribut WordprocessingML d'un élément, quel que soit l'espace (transitionnel, strict)."""
    for (espace, local), valeur in attributs.items():
        if local == nom and espace in _W:
            return valeur
    return None


def _rsid(attributs: dict[tuple[str, str], str], nom: str) -> str | None:
    valeur = (_valeur_w(attributs, nom) or "").strip()
    return valeur.upper() or None


def _reglages(lecteur: _Lecteur, releve: _Releve, nom: str) -> None:
    """Identifiants de session de ``w:rsids`` : la racine et chaque ``w:rsid``."""
    lue = lecteur.designee(nom)
    if lue is None:
        return
    for racine in lecteur.arbre(*lue):
        for rsids in racine.enfants:
            if rsids.espace not in _W or rsids.nom != "rsids":
                continue
            for rsid in rsids.enfants:
                if rsid.espace in _W and rsid.nom in ("rsid", "rsidRoot"):
                    valeur = _rsid(rsid.attributs, "val")
                    if valeur is not None:
                        releve.sessions.add(valeur)
                        releve.sessions_lieu = lue[1]


def _changement(releve: _Releve, attributs: dict[tuple[str, str], str], auteurs: set[str]) -> None:
    auteur = (_valeur_w(attributs, "author") or "").strip()
    if auteur:
        auteurs.add(auteur)
    date = _valeur_w(attributs, "date")
    if date:
        releve.dates.append(date)


def _corps_docx(lecteur: _Lecteur, releve: _Releve, donnees: bytes, lieu: Localisation) -> None:
    """Texte visible du corps rangé par session, et marques de révision."""
    releve.corps = lieu
    pile: list[str] = []
    """Noms locaux des éléments WordprocessingML ouverts (autres espaces : chaîne vide)."""
    paragraphes: list[str | None] = []
    """Session par défaut des courses de chaque paragraphe ouvert (``w:rsidRDefault``)."""
    courses: list[str | None] = []
    """Session de chaque course ouverte : la sienne (``w:rsidR``), sinon celle du paragraphe."""
    suppressions = 0

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        nonlocal suppressions
        local = nom if espace in _W else ""
        pile.append(local)
        if local == "p":
            paragraphes.append(_rsid(attributs, "rsidRDefault"))
        elif local == "r":
            courses.append(_rsid(attributs, "rsidR") or (paragraphes[-1] if paragraphes else None))
        elif local in CHANGEMENTS_DOCX:
            releve.modifications += 1
            _changement(releve, attributs, releve.auteurs_modifications)
            if local in _SUPPRESSIONS:
                suppressions += 1

    def fermer() -> None:
        nonlocal suppressions
        local = pile.pop()
        if local == "p":
            paragraphes.pop()
        elif local == "r":
            courses.pop()
        elif local in _SUPPRESSIONS:
            suppressions -= 1

    def texte(contenu: str) -> None:
        if pile and pile[-1] == "t" and not suppressions:
            releve.texte[courses[-1] if courses else None] += len(contenu)

    lecteur.parcourir(donnees, lieu, ouvrir, fermer, texte)


def _commentaires_docx(
    lecteur: _Lecteur, releve: _Releve, donnees: bytes, lieu: Localisation
) -> None:
    releve.commentaires_lieu = lieu

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        if espace in _W and nom == "comment":
            releve.commentaires += 1
            _changement(releve, attributs, releve.auteurs_commentaires)

    lecteur.parcourir(donnees, lieu, ouvrir, lambda: None, lambda _texte: None)


# ODT


def _odt(lecteur: _Lecteur, releve: _Releve) -> None:
    meta = lecteur.partie("meta.xml", casse=True)
    if meta is not None:
        _meta(lecteur, releve, *meta)
    if not lecteur.existe("content.xml", casse=True):
        return
    lue = lecteur.partie("content.xml", casse=True)
    if lue is not None:
        _contenu_odt(lecteur, releve, *lue)


def _meta(lecteur: _Lecteur, releve: _Releve, donnees: bytes, lieu: Localisation) -> None:
    for racine in lecteur.arbre(donnees, lieu):
        if not racine.est(_OFFICE, "document-meta"):
            continue
        for bloc in racine.enfants:
            if not bloc.est(_OFFICE, "meta"):
                continue
            for element in bloc.enfants:
                texte = _texte_de(element).strip()
                if element.est(_META, "editing-duration") and releve.duree is None:
                    minutes = duree_iso8601(texte)
                    if minutes is not None:
                        releve.duree = (minutes, lieu)
                elif element.est(_META, "editing-cycles") and releve.revisions is None:
                    nombre = _entier(texte)
                    if nombre is not None:
                        releve.revisions = (nombre, lieu)
                elif element.est(_META, "creation-date") and releve.creation is None and texte:
                    releve.creation = texte
                elif element.est(_DC, "date") and releve.modification is None and texte:
                    releve.modification = (texte, lieu)


@dataclass(slots=True)
class _Ouvert:
    """Élément ouvert de ``content.xml`` : son nom, et la session de son texte."""

    espace: str
    nom: str
    session: str | None


def _contenu_odt(lecteur: _Lecteur, releve: _Releve, donnees: bytes, lieu: Localisation) -> None:
    """Styles automatiques et leurs sessions, puis texte du corps, modifications et
    commentaires : les styles automatiques précèdent le corps (OpenDocument, partie 3)."""
    releve.corps = lieu
    releve.commentaires_lieu = lieu
    sessions: dict[tuple[str, str], str] = {}
    """Session du texte de chaque style automatique, par famille et nom."""
    pile: list[_Ouvert] = []
    style: list[tuple[str, str]] = []
    automatiques = 0
    corps = 0
    hors_du_texte = 0
    paragraphes = 0
    saisie: list[str] | None = None
    """Texte de l'auteur ou de la date en cours de lecture."""
    cible: tuple[str, bool] = ("", False)
    """Nom de l'élément saisi (``creator`` ou ``date``), et vrai pour une modification."""

    def ouvrir(espace: str, nom: str, attributs: dict[tuple[str, str], str]) -> None:
        nonlocal automatiques, corps, hors_du_texte, paragraphes, saisie, cible
        session = pile[-1].session if pile else None
        element = (espace, nom)
        if element == (_OFFICE, "automatic-styles"):
            automatiques += 1
        elif element == (_STYLE, "style") and automatiques:
            famille = attributs.get((_STYLE, "family"), "")
            style.append((famille, attributs.get((_STYLE, "name"), "")))
        elif element == (_STYLE, "text-properties") and automatiques and style:
            _sessions_odt(releve, sessions, style[-1], attributs, lieu)
        elif element == (_OFFICE, "text"):
            corps += 1
        elif element in _HORS_DU_TEXTE:
            hors_du_texte += 1
        if element == (_TEXT, "changed-region"):
            releve.modifications += 1
        elif element == (_OFFICE, "annotation") and corps:
            releve.commentaires += 1
        elif espace == _DC and nom in ("creator", "date") and pile:
            parent = (pile[-1].espace, pile[-1].nom)
            if parent in ((_OFFICE, "change-info"), (_OFFICE, "annotation")):
                saisie, cible = [], (nom, parent[1] == "change-info")
        if espace == _TEXT and nom in ("p", "h"):
            paragraphes += 1
            session = sessions.get(("paragraph", attributs.get((_TEXT, "style-name"), "")))
        elif element == (_TEXT, "span"):
            nom_style = attributs.get((_TEXT, "style-name"), "")
            session = sessions.get(("text", nom_style), session)
        pile.append(_Ouvert(espace, nom, session))

    def fermer() -> None:
        nonlocal automatiques, corps, hors_du_texte, paragraphes, saisie
        ouvert = pile.pop()
        element = (ouvert.espace, ouvert.nom)
        if element == (_OFFICE, "automatic-styles"):
            automatiques -= 1
        elif element == (_STYLE, "style") and automatiques and style:
            style.pop()
        elif element == (_OFFICE, "text"):
            corps -= 1
        elif element in _HORS_DU_TEXTE:
            hors_du_texte -= 1
        elif ouvert.espace == _TEXT and ouvert.nom in ("p", "h"):
            paragraphes -= 1
        if saisie is not None and ouvert.espace == _DC:
            _saisie(releve, cible, "".join(saisie).strip())
            saisie = None

    def texte(contenu: str) -> None:
        if saisie is not None:
            saisie.append(contenu)
        elif corps and paragraphes and not hors_du_texte and pile[-1].espace not in _EXCLUS:
            releve.texte[pile[-1].session] += len(contenu)

    lecteur.parcourir(donnees, lieu, ouvrir, fermer, texte)


def _sessions_odt(
    releve: _Releve,
    sessions: dict[tuple[str, str], str],
    style: tuple[str, str],
    attributs: dict[tuple[str, str], str],
    lieu: Localisation,
) -> None:
    """Sessions d'un style automatique : celle de son texte, et celle de ses paragraphes."""
    for nom in ("rsid", "paragraph-rsid"):
        valeur = attributs.get((_OFFICEOOO, nom), "").strip().upper()
        if not valeur:
            continue
        releve.sessions.add(valeur)
        releve.sessions_lieu = lieu
        if nom == "rsid":
            sessions[style] = valeur


def _saisie(releve: _Releve, cible: tuple[str, bool], valeur: str) -> None:
    """Auteur ou date d'une modification ou d'un commentaire d'un ODT."""
    if not valeur:
        return
    champ, modification = cible
    if champ == "date":
        releve.dates.append(valeur)
    elif modification:
        releve.auteurs_modifications.add(valeur)
    else:
        releve.auteurs_commentaires.add(valeur)


# Observations


def _ecart(creation: str | None, modification: str | None) -> int | None:
    """Plus grand écart, en minutes entières arrondies au-dessus, que permettent les écritures
    des deux dates ; ``None`` si l'une ne se lit pas, ou si la création suit certainement le
    dernier enregistrement (ce que dit une règle de T23)."""
    if creation is None or modification is None:
        return None
    debut, fin = lire(Lecture.ISO8601, creation), lire(Lecture.ISO8601, modification)
    if not isinstance(debut, Intervalle) or not isinstance(fin, Intervalle):
        return None
    microsecondes = fin.fin - debut.debut
    if microsecondes <= 0:
        return None
    return (microsecondes + _MINUTE - 1) // _MINUTE


def _posterieures(releve: _Releve) -> int | None:
    """Modifications et commentaires certainement datés après le dernier enregistrement ;
    ``None`` si cette date ne se lit pas, ou si aucune de leurs dates ne se lit."""
    if releve.modification is None:
        return None
    fin = lire(Lecture.ISO8601, releve.modification[0])
    if not isinstance(fin, Intervalle):
        return None
    lues = [lire(Lecture.ISO8601, sans_fuseau(date)) for date in releve.dates]
    intervalles = [lue for lue in lues if isinstance(lue, Intervalle)]
    if not intervalles:
        return None
    return sum(fin.avant(lue) for lue in intervalles)


def _observer(contexte: Contexte, releve: _Releve) -> None:
    present = (
        releve.duree is not None
        or releve.revisions is not None
        or bool(releve.sessions)
        or releve.modifications > 0
        or releve.commentaires > 0
    )
    contexte.observer("historique.present", present)
    if releve.duree is not None:
        minutes, lieu = releve.duree
        valeurs.observer(
            contexte,
            "historique.duree",
            valeurs.entier(minutes),
            unite="minutes",
            localisation=lieu,
        )
    if releve.revisions is not None:
        nombre, lieu = releve.revisions
        valeurs.observer(
            contexte, "historique.revisions", valeurs.entier(nombre), localisation=lieu
        )
    if releve.sessions:
        contexte.observer(
            "historique.sessions", len(releve.sessions), localisation=releve.sessions_lieu
        )
    if releve.corps is not None:
        _texte(contexte, releve)
        contexte.observer(
            "historique.modifications", releve.modifications, localisation=releve.corps
        )
        if releve.modifications:
            contexte.observer("historique.modifications.auteurs", len(releve.auteurs_modifications))
        contexte.observer(
            "historique.commentaires", releve.commentaires, localisation=releve.commentaires_lieu
        )
        if releve.commentaires:
            contexte.observer("historique.commentaires.auteurs", len(releve.auteurs_commentaires))
    modification = releve.modification[0] if releve.modification is not None else None
    enregistrement = releve.modification[1] if releve.modification is not None else None
    ecart = _ecart(releve.creation, modification)
    if ecart is not None:
        valeurs.observer(
            contexte,
            "historique.ecart",
            valeurs.entier(ecart),
            unite="minutes",
            localisation=enregistrement,
        )
    posterieures = _posterieures(releve)
    if posterieures is not None:
        contexte.observer("historique.posterieures", posterieures, localisation=enregistrement)


def _texte(contexte: Contexte, releve: _Releve) -> None:
    """Caractères du texte visible du corps, et leur partage entre sessions."""
    total = sum(releve.texte.values())
    sans_session = releve.texte.get(None, 0)
    contexte.observer(
        "historique.texte.caracteres", total, unite="caractères", localisation=releve.corps
    )
    if total == 0:
        return
    contexte.observer("historique.texte.sans_session", sans_session, unite="caractères")
    par_session = [n for session, n in releve.texte.items() if session is not None]
    if not par_session:
        return
    avec_session = total - sans_session
    contexte.observer("historique.texte.sessions", len(par_session))
    contexte.observer("historique.texte.part", max(par_session) * 100 // avec_session, unite="%")


def _ascii_minuscules(texte: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in texte)
