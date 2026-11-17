"""Module ``imagespdf`` : images d'un PDF, acheminées vers les modules d'image (F-63 ; ADR-0223
à ADR-0227 ; fiche ``images-pdf``).

Le module cherche les images de la dernière version du document dans les ressources de ses
pages (``/XObject`` de sous-type ``/Image``, ISO 32000-2, §8.9.5), et dans celles des formes
qu'elles listent (``/Form``, §8.10), sur au plus :data:`FORMES_MAX` niveaux. Une image reprise
par plusieurs pages ou formes est comptée une fois, à la première page où elle se trouve ; elle
y est comptée qu'elle soit dessinée ou non (le flux de contenu n'est pas lu).

Une image dont le seul filtre est ``DCTDecode`` est un JPEG complet, écrit tel quel dans le
fichier (§7.4.8) : le module en donne la plage au moteur, qui la reconnaît et la fait analyser
comme une partie extraite par les modules d'image, sans que rien ne soit décodé ici (ADR-0224,
ADR-0225). Elles le sont dans l'ordre des pages, seize au plus, tant que leur taille cumulée
n'a pas atteint 2 Mio ; les suivantes sont comptées, et le moteur déclare non menée la première
d'entre elles (ADR-0226). Les autres images (pixels
compressés par ``FlateDecode``, JPEG 2000, CCITT, JBIG2, JPEG compressé une seconde fois) sont
comptées par filtre, non analysées. Les images en ligne (``BI``… ``EI``), dans les flux de
contenu, ne sont pas cherchées.

Un document chiffré se parcourt par sa structure, qui ne l'est pas ; ses images, chiffrées, ne
sont ni déchiffrées ni acheminées (ADR-0126). Le module n'émet aucun constat : les règles du
catalogue lisent ses observations (ADR-0227).
"""

from dataclasses import dataclass

from voight_kampff._limites import OBJETS_MAX
from voight_kampff._travail.contexte import Contexte
from voight_kampff.modules._lecture import valeurs
from voight_kampff.modules._lecture.pdf import Document, Flux, Illisible, Nom, Objet, Ref, pages
from voight_kampff.rapport.modele import Localisation, Plage

__all__ = [
    "AUTRE",
    "FILTRES",
    "FORMES_MAX",
    "IMAGES_MAX",
    "OBJETS_RESERVES",
    "PAGES_MAX",
    "SANS_FILTRE",
    "analyser",
]

PAGES_MAX = 4096
"""Pages au plus parcourues ; ``imagespdf.pages`` les compte toutes."""
FORMES_MAX = 8
"""Formes au plus imbriquées sous une page ; au-delà, la forme n'est pas lue."""
IMAGES_MAX = 1 << 16
"""Images au plus retenues ; au-delà, ``imagespdf.recherche_coupee`` le dit."""
OBJETS_RESERVES = 1 << 18
"""Objets du budget (ES-03) gardés pour finir : la recherche s'arrête quand il n'en reste pas
plus, pour que les observations déjà faites soient envoyées (comme ``pagespdf``, ADR-0213)."""

FILTRES = frozenset(
    {
        "ASCIIHexDecode",
        "ASCII85Decode",
        "LZWDecode",
        "FlateDecode",
        "RunLengthDecode",
        "CCITTFaxDecode",
        "JBIG2Decode",
        "DCTDecode",
        "JPXDecode",
        "Crypt",
    }
)
"""Filtres de la norme (§7.4, tableau 6) ; tout autre nom est observé comme :data:`AUTRE`."""
AUTRE = "autre"
SANS_FILTRE = "aucun"
"""Image sans filtre : pixels écrits en clair."""
_JPEG = ("DCTDecode",)
_LOCALISATION = Localisation(chemin="images des pages")


def _nom(objet: Objet) -> str | None:
    return str(objet) if isinstance(objet, Nom) else None


def _dico(valeur: Objet) -> dict[str, Objet] | None:
    if isinstance(valeur, Flux):
        return valeur.dico
    return valeur if isinstance(valeur, dict) else None


@dataclass(frozen=True, slots=True)
class _Image:
    ref: Ref
    flux: Flux
    page: int
    filtres: tuple[str, ...]
    """Noms des filtres, dans l'ordre où ils s'appliquent ; hors de la norme, :data:`AUTRE`."""

    @property
    def jpeg(self) -> bool:
        """JPEG complet, écrit tel quel dans le fichier (§7.4.8)."""
        return self.filtres == _JPEG

    @property
    def description(self) -> str:
        """Ses filtres, joints par « + », ou :data:`SANS_FILTRE`."""
        return "+".join(self.filtres) or SANS_FILTRE


class _Recherche:
    """Parcourt les ressources des pages et range leurs images, dans l'ordre."""

    def __init__(self, contexte: Contexte, document: Document) -> None:
        self._contexte = contexte
        self._document = document
        self.images: list[_Image] = []
        self._vus: set[Ref] = set()
        """Images et formes déjà lues : chacune l'est une fois."""
        self.illisible: Illisible | None = None
        self.arrete = False
        """Vrai si la recherche s'est arrêtée avant le budget (:data:`OBJETS_RESERVES`)."""
        self.coupee = False
        """Vrai si une limite (:data:`FORMES_MAX`, :data:`IMAGES_MAX`) a été atteinte."""

    def continuer(self) -> bool:
        """Faux dès qu'il ne reste plus que :data:`OBJETS_RESERVES` objets du budget."""
        if self._contexte.objets > OBJETS_MAX - OBJETS_RESERVES:
            self.arrete = True
        return not self.arrete

    def page(self, numero: int, ressources: Objet) -> bool:
        """Images des ressources d'une page et de ses formes ; faux si elle n'est pas lue en
        entier. Une page illisible n'arrête pas les autres."""
        try:
            return self._ressources(numero, ressources)
        except Illisible as illisible:
            self.illisible = self.illisible or illisible
            return False

    def _ressources(self, numero: int, ressources: Objet) -> bool:
        pile: list[tuple[Objet, int]] = [(ressources, 0)]
        entiere = True
        while pile:
            designees, profondeur = pile.pop()
            dico = _dico(self._document.resoudre(designees)) or {}
            objets = _dico(self._document.resoudre(dico.get("XObject"))) or {}
            formes: list[tuple[Objet, int]] = []
            for designe in objets.values():
                if not self.continuer():
                    return False
                if not isinstance(designe, Ref) or designe in self._vus:
                    continue  # un flux est toujours un objet indirect (§7.3.8)
                flux = self._document.resoudre(designe)
                if not isinstance(flux, Flux):
                    continue
                self._contexte.compter_objets()
                nature = _nom(self._document.resoudre(flux.dico.get("Subtype")))
                if nature == "Form":
                    if profondeur >= FORMES_MAX:
                        self.coupee = True
                        entiere = False
                        continue
                    self._vus.add(designe)
                    formes.append((flux.dico.get("Resources"), profondeur + 1))
                elif nature == "Image":
                    if len(self.images) >= IMAGES_MAX:
                        self.coupee = True
                        return False
                    self._vus.add(designe)
                    self.images.append(_Image(designe, flux, numero, self._filtres(flux)))
            pile.extend(reversed(formes))
        return entiere

    def _filtres(self, flux: Flux) -> tuple[str, ...]:
        designes = self._document.resoudre(flux.dico.get("Filter"))
        liste = designes if isinstance(designes, list) else [] if designes is None else [designes]
        noms = (_nom(self._document.resoudre(filtre)) for filtre in liste)
        return tuple(nom if nom in FILTRES else AUTRE for nom in noms)


# Analyse


def analyser(contexte: Contexte) -> None:
    try:
        document = Document(contexte)
        liste, trouvees = pages(contexte, document, PAGES_MAX)
    except Illisible as illisible:
        contexte.non_mener(illisible.raison, localisation=illisible.localisation(contexte.taille))
        return
    recherche = _Recherche(contexte, document)
    lues = 0
    for numero, (_, ressources) in enumerate(liste, start=1):
        if not recherche.continuer():
            break
        lues += recherche.page(numero, ressources)
    if (erreur := recherche.illisible) is not None:
        contexte.non_mener(erreur.raison, localisation=erreur.localisation(contexte.taille))
    contexte.observer("imagespdf.pages", trouvees, localisation=_LOCALISATION)
    contexte.observer("imagespdf.pages_lues", lues)
    if recherche.arrete:
        contexte.observer("imagespdf.arret_avant_budget", True)
    if recherche.coupee:
        contexte.observer("imagespdf.recherche_coupee", True)
    images = recherche.images
    contexte.observer("imagespdf.images", len(images))
    if "Encrypt" in document.trailer:
        # Données des flux chiffrées : rien n'est acheminé, rien n'est déchiffré (ADR-0126).
        contexte.observer("imagespdf.chiffre", True)
        return
    _acheminer(contexte, document, [image for image in images if image.jpeg])
    autres = [image for image in images if not image.jpeg]
    contexte.observer("imagespdf.non_acheminees", len(autres))
    if autres:
        filtres = sorted({image.description for image in autres})
        valeurs.observer(contexte, "imagespdf.non_acheminees.filtres", filtres)
        pages_ = sorted({image.page for image in autres})
        valeurs.observer(contexte, "imagespdf.non_acheminees.pages", pages_)


def _acheminer(contexte: Contexte, document: Document, jpeg: list[_Image]) -> None:
    """Donne au moteur la plage de chaque JPEG, dans l'ordre des pages (ADR-0225, ADR-0226)."""
    acheminees: list[int] = []
    au_dela = 0
    for image in jpeg:
        chemin = document.localisation(image.ref, "image").chemin
        localisation = Localisation(chemin=chemin, page=image.page)
        plage = Plage(image.flux.debut, image.flux.longueur) if image.flux.longueur else None
        if plage is None:
            continue  # flux vide : rien à analyser, compté parmi les images
        if contexte.extraire("jpeg", plage, localisation):
            acheminees.append(image.page)
        else:
            au_dela += 1
    contexte.observer("imagespdf.jpeg", len(jpeg))
    contexte.observer("imagespdf.acheminees", len(acheminees))
    if acheminees:
        valeurs.observer(contexte, "imagespdf.acheminees.pages", sorted(set(acheminees)))
    if au_dela:
        contexte.observer("imagespdf.au_dela", au_dela)
