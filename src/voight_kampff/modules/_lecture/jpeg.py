"""Coefficients DCT quantifiés d'un JPEG, par le décodage entropique (T.81 ; ADR-0185, ADR-0187).

Le lecteur parcourt les segments du JPEG entier, balayages compris, et décode les codes de
Huffman des procédés séquentiels (SOF0, SOF1) et progressif (SOF2), en huit bits : il rend les
coefficients quantifiés de la première composante (la luminance d'un JPEG en YCbCr), sans
transformée inverse ni conversion de couleurs. Le codage arithmétique, le procédé sans perte, le
procédé hiérarchique et la précision de douze bits ne sont pas lus (format partiel).

Seule une région du haut de l'image est décodée : les premières lignes de blocs de la première
composante, au plus :data:`BLOCS_REGION` blocs, et au plus :data:`VISITES_MAX` blocs décodés en
tout, balayages et autres composantes compris (ADR-0189). Le nombre de lignes se déduit des
balayages annoncés, avant le décodage : il est le même sur toutes les machines. Un balayage qui
ne porte pas la première composante est sauté sans être décodé.

Un JPEG malformé n'y lève jamais d'exception : la lecture s'arrête et rend sa raison, fichier
tronqué si les données manquent avant la fin de la région, format partiel sinon.
"""

import re
from array import array
from dataclasses import dataclass

from voight_kampff._protocole import TAILLE_MAX_LECTURE
from voight_kampff._travail.contexte import Contexte
from voight_kampff.rapport.modele import Localisation, Plage, RaisonNonMenee

__all__ = [
    "BALAYAGES_MAX",
    "BLOCS_REGION",
    "VISITES_MAX",
    "Coefficients",
    "Lecture",
    "lire",
]

BLOCS_REGION = 1 << 15
"""Blocs de la première composante décodés au plus : 32 768, soit 2,1 millions de pixels."""
VISITES_MAX = 1 << 18
"""Blocs décodés au plus, toutes composantes et tous balayages confondus : 262 144."""
BALAYAGES_MAX = 64
"""Balayages au plus ; au-delà, format partiel (un JPEG progressif courant en a une dizaine)."""

_SEQUENTIELS = frozenset({0xC0, 0xC1})
_PROGRESSIF = 0xC2
_NON_LUS = frozenset(
    {0xC3, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF, 0xDC, 0xDE, 0xDF}
)
"""Procédés sans perte, hiérarchiques et arithmétiques (SOF3, SOF5 à SOF7, SOF9 à SOF15), JPG,
DAC, DNL, DHP et EXP (T.81, tableau B.1)."""
_LUS = frozenset({0xC0, 0xC1, 0xC2, 0xC4, 0xDA, 0xDB, 0xDD})
"""Segments dont le lecteur lit le contenu : SOF0 à SOF2, DHT, SOS, DQT, DRI."""
_TABLES_MAX = 256
"""Tables de Huffman définies au plus ; chacune coûte une table de lecture de 65 536 entrées."""
_FIN = re.compile(rb"\xff[^\x00\xd0-\xd7]")
"""Fin des données entropiques : un marqueur autre qu'un octet de remplissage ou RSTn."""
_RST = re.compile(rb"\xff[\xd0-\xd7]")
_OCTETS_PAR_BLOC = 420
"""Octets au plus d'un bloc dans les données entropiques : 27 bits du coefficient continu,
26 bits pour chacun des 63 autres, doublés par le remplissage des octets 0xFF."""
_MORCEAU = 1 << 20


@dataclass(frozen=True, slots=True)
class Coefficients:
    """Coefficients quantifiés de la première composante, sur la région décodée."""

    largeur: int
    """Largeur de l'image, en pixels (segment SOF)."""
    hauteur: int
    procede: str
    """``sequentiel`` ou ``progressif``."""
    precision_table: bool
    """Table de quantification de la composante en seize bits."""
    table: tuple[int, ...]
    """Table de quantification de la composante, 64 valeurs dans l'ordre du segment DQT."""
    colonnes: int
    """Blocs par ligne qui recouvrent la composante."""
    lignes: int
    """Lignes de blocs décodées ; :attr:`hauteur_region` pixels de la composante."""
    largeur_composante: int
    """Largeur de la composante en pixels, sous-échantillonnage compris."""
    hauteur_region: int
    blocs_image: int
    """Blocs de la composante dans l'image entière."""
    valeurs: array[int]
    """``lignes * colonnes * 64`` entiers signés de 64 bits, bloc après bloc dans l'ordre de la
    trame, chaque bloc dans l'ordre en zigzag du segment DQT."""


@dataclass(frozen=True, slots=True)
class Lecture:
    """Coefficients lus, ou la raison de l'arrêt et sa position."""

    coefficients: Coefficients | None
    arret: RaisonNonMenee | None = None
    position: int = 0

    def localisation_arret(self) -> Localisation:
        return Localisation(chemin="données entropiques du JPEG", octets=Plage(self.position, 1))


class _Arret(Exception):
    def __init__(self, raison: RaisonNonMenee, position: int) -> None:
        super().__init__(raison)
        self.raison = raison
        self.position = position


@dataclass(frozen=True, slots=True)
class _Composante:
    identifiant: int
    horizontal: int
    vertical: int
    table: int


@dataclass(frozen=True, slots=True)
class _Balayage:
    composantes: tuple[tuple[int, list[int], list[int]], ...]
    """Indice de la composante dans la trame, tables de Huffman continue et alternative."""
    debut: int
    fin: int
    ss: int
    se: int
    ah: int
    al: int
    intervalle: int
    """Intervalle de redémarrage, en MCU ; 0 sans redémarrage."""


def lire(contexte: Contexte) -> Lecture:
    """Coefficients de la première composante, sur la région du haut de l'image."""
    try:
        return Lecture(_Lecteur(contexte).lire())
    except _Arret as arret:
        return Lecture(None, arret.raison, arret.position)


def _huffman(comptes: bytes, symboles: bytes, position: int) -> list[int]:
    """Table de lecture sur 16 bits : ``longueur << 8 | symbole``, 0 pour un code absent."""
    table = [0] * 65536
    code = 0
    rang = 0
    for longueur in range(1, 17):
        for _ in range(comptes[longueur - 1]):
            if code >= 1 << longueur:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            decalage = 16 - longueur
            debut = code << decalage
            table[debut : debut + (1 << decalage)] = [longueur << 8 | symboles[rang]] * (
                1 << decalage
            )
            rang += 1
            code += 1
        code <<= 1
    return table


class _Lecteur:
    __slots__ = (
        "_balayages",
        "_composantes",
        "_contexte",
        "_definies",
        "_hauteur",
        "_huffman",
        "_intervalle",
        "_largeur",
        "_procede",
        "_quantification",
        "_table",
    )

    def __init__(self, contexte: Contexte) -> None:
        self._contexte = contexte
        self._quantification: dict[int, tuple[bool, tuple[int, ...]]] = {}
        self._huffman: dict[tuple[int, int], list[int]] = {}
        self._definies = 0
        self._intervalle = 0
        self._composantes: tuple[_Composante, ...] = ()
        self._largeur = 0
        self._hauteur = 0
        self._procede = 0
        self._table: tuple[bool, tuple[int, ...]] | None = None
        self._balayages: list[_Balayage] = []

    # Segments

    def lire(self) -> Coefficients:
        self._segments()
        if not self._composantes or self._table is None:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, self._contexte.taille)
        return self._decoder()

    def _segments(self) -> None:
        contexte = self._contexte
        position = 2
        while True:
            tete = contexte.lire(position, 4)
            if len(tete) < 2:
                if self._balayages:
                    return  # EOI manquant après le dernier balayage : toléré
                raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
            if tete[0] != 0xFF:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            marqueur = tete[1]
            contexte.compter_objets()
            if marqueur == 0xFF:
                position += 1
                continue
            if marqueur == 0xD9:
                return
            if marqueur == 0x01 or 0xD0 <= marqueur <= 0xD8:
                if marqueur == 0xD8:
                    raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
                position += 2
                continue
            if len(tete) < 4:
                raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
            longueur = int.from_bytes(tete[2:4], "big") - 2
            debut = position + 4
            if longueur < 0 or marqueur == 0x00:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            if debut + longueur > contexte.taille:
                raise _Arret(RaisonNonMenee.FICHIER_TRONQUE, position)
            if marqueur in _NON_LUS:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            donnees = contexte.lire(debut, longueur) if marqueur in _LUS else b""
            position = debut + longueur
            if marqueur == 0xDB:
                self._dqt(donnees, position)
            elif marqueur == 0xC4:
                self._dht(donnees, position)
            elif marqueur == 0xDD:
                if len(donnees) < 2:
                    raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
                self._intervalle = int.from_bytes(donnees[:2], "big")
            elif marqueur in _SEQUENTIELS or marqueur == _PROGRESSIF:
                self._sof(marqueur, donnees, position)
            elif marqueur == 0xDA:
                position = self._sos(donnees, position)

    def _dqt(self, donnees: bytes, position: int) -> None:
        rang = 0
        while rang < len(donnees):
            precision, identifiant = donnees[rang] >> 4, donnees[rang] & 0x0F
            taille = 128 if precision else 64
            octets = donnees[rang + 1 : rang + 1 + taille]
            if precision > 1 or identifiant > 3 or len(octets) < taille:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            valeurs = (
                tuple(int.from_bytes(octets[i : i + 2], "big") for i in range(0, 128, 2))
                if precision
                else tuple(octets)
            )
            if 0 in valeurs:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            self._quantification[identifiant] = (bool(precision), valeurs)
            rang += 1 + taille

    def _dht(self, donnees: bytes, position: int) -> None:
        rang = 0
        while rang < len(donnees):
            classe, identifiant = donnees[rang] >> 4, donnees[rang] & 0x0F
            comptes = donnees[rang + 1 : rang + 17]
            nombre = sum(comptes)
            symboles = donnees[rang + 17 : rang + 17 + nombre]
            if classe > 1 or identifiant > 3 or len(comptes) < 16 or len(symboles) < nombre:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            self._definies += 1
            if self._definies > _TABLES_MAX:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            self._huffman[classe, identifiant] = _huffman(comptes, symboles, position)
            rang += 17 + nombre

    def _sof(self, marqueur: int, donnees: bytes, position: int) -> None:
        if self._composantes or len(donnees) < 6:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        precision = donnees[0]
        hauteur = int.from_bytes(donnees[1:3], "big")
        largeur = int.from_bytes(donnees[3:5], "big")
        nombre = donnees[5]
        # Douze bits, hauteur donnée par un segment DNL, image vide : non lus.
        if precision != 8 or not hauteur or not largeur or not 1 <= nombre <= 4:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        if len(donnees) < 6 + 3 * nombre:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        composantes: list[_Composante] = []
        for i in range(nombre):
            identifiant, facteurs, table = donnees[6 + 3 * i : 9 + 3 * i]
            horizontal, vertical = facteurs >> 4, facteurs & 0x0F
            if not 1 <= horizontal <= 4 or not 1 <= vertical <= 4 or table > 3:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            if any(c.identifiant == identifiant for c in composantes):
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            composantes.append(_Composante(identifiant, horizontal, vertical, table))
        self._contexte.verifier_dimensions(largeur, hauteur)
        self._composantes = tuple(composantes)
        self._largeur, self._hauteur = largeur, hauteur
        self._procede = marqueur

    def _sos(self, donnees: bytes, position: int) -> int:
        """Lit l'en-tête du balayage, repère ses données entropiques ; position après elles."""
        if not self._composantes or len(self._balayages) >= BALAYAGES_MAX or not donnees:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        nombre = donnees[0]
        if not 1 <= nombre <= 4 or len(donnees) < 4 + 2 * nombre:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        ss, se = donnees[1 + 2 * nombre], donnees[2 + 2 * nombre]
        ah, al = donnees[3 + 2 * nombre] >> 4, donnees[3 + 2 * nombre] & 0x0F
        indices: list[tuple[int, int, int]] = []
        for i in range(nombre):
            identifiant = donnees[1 + 2 * i]
            indice = next(
                (j for j, c in enumerate(self._composantes) if c.identifiant == identifiant), -1
            )
            if indice < 0 or (indices and indice <= indices[-1][0]):
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
            indices.append((indice, donnees[2 + 2 * i] >> 4, donnees[2 + 2 * i] & 0x0F))
        self._verifier_balayage(nombre, ss, se, ah, al, indices, position)
        fin = self._fin_entropie(position)
        if indices[0][0] == 0:
            composantes = []
            for indice, continu, alternatif in indices:
                # Seules les tables dont le balayage se sert doivent exister.
                tables = (
                    self._huffman.get((0, continu)) if ss == 0 and ah == 0 else [],
                    self._huffman.get((1, alternatif)) if se > 0 else [],
                )
                if tables[0] is None or tables[1] is None:
                    raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
                composantes.append((indice, tables[0], tables[1]))
            if self._table is None:
                table = self._quantification.get(self._composantes[0].table)
                if table is None:
                    raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
                self._table = table
            self._balayages.append(
                _Balayage(tuple(composantes), position, fin, ss, se, ah, al, self._intervalle)
            )
        return fin

    def _verifier_balayage(
        self,
        nombre: int,
        ss: int,
        se: int,
        ah: int,
        al: int,
        indices: list[tuple[int, int, int]],
        position: int,
    ) -> None:
        """Paramètres admis du balayage (T.81, B.2.3 et G.1.1.1)."""
        if (
            nombre > 1
            and sum(
                self._composantes[i].horizontal * self._composantes[i].vertical
                for i, _, _ in indices
            )
            > 10
        ):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        if self._procede == _PROGRESSIF:
            continu = ss == 0 and se == 0
            alternatif = 1 <= ss <= se <= 63 and nombre == 1
            raffinement = ah == 0 or ah == al + 1
            if not (continu or alternatif) or not raffinement or al > 13:
                raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)
        elif (ss, se, ah, al) != (0, 63, 0, 0):
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, position)

    def _fin_entropie(self, debut: int) -> int:
        """Position du premier marqueur qui suit les données entropiques, ou la fin du fichier."""
        contexte = self._contexte
        position = debut
        while position < contexte.taille:
            morceau = contexte.lire(position, _MORCEAU + 1)
            trouve = _FIN.search(morceau)
            if trouve is not None:
                return position + trouve.start()
            position += max(1, len(morceau) - 1)
        return contexte.taille

    # Décodage

    def _decoder(self) -> Coefficients:
        composantes = self._composantes
        premiere = composantes[0]
        hmax = max(c.horizontal for c in composantes)
        vmax = max(c.vertical for c in composantes)
        mcu_colonnes = -(-self._largeur // (8 * hmax))
        largeur_c = -(-self._largeur * premiere.horizontal // hmax)
        hauteur_c = -(-self._hauteur * premiere.vertical // vmax)
        colonnes = -(-largeur_c // 8)
        lignes_image = -(-hauteur_c // 8)
        seule = len(composantes) == 1
        grille = colonnes if seule else mcu_colonnes * premiere.horizontal
        entrelaces = any(len(b.composantes) > 1 for b in self._balayages)
        # Lignes de la région : au plus BLOCS_REGION blocs, au plus VISITES_MAX blocs décodés. Un
        # balayage entrelacé décode des lignes de MCU entières ; les lignes en trop sont oubliées.
        lignes = max(1, min(lignes_image, BLOCS_REGION // colonnes))
        while lignes > 1 and self._visites(lignes, colonnes, mcu_colonnes) > VISITES_MAX:
            lignes = lignes * 3 // 4
        if self._visites(lignes, colonnes, mcu_colonnes) > VISITES_MAX:
            raise _Arret(RaisonNonMenee.FORMAT_PARTIEL, self._balayages[0].debut)
        stockage = -(-lignes // premiere.vertical) * premiere.vertical if entrelaces else lignes
        valeurs = array("q", bytes(8 * 64 * stockage * grille))
        for balayage in self._balayages:
            self._balayage(balayage, valeurs, grille, lignes, colonnes, mcu_colonnes)
        if grille != colonnes or stockage != lignes:
            valeurs = _colonnes(valeurs, grille, colonnes, lignes)
        precision, table = self._table or (False, ())
        return Coefficients(
            largeur=self._largeur,
            hauteur=self._hauteur,
            procede="progressif" if self._procede == _PROGRESSIF else "sequentiel",
            precision_table=precision,
            table=table,
            colonnes=colonnes,
            lignes=lignes,
            largeur_composante=largeur_c,
            hauteur_region=min(hauteur_c, 8 * lignes),
            blocs_image=colonnes * lignes_image,
            valeurs=valeurs,
        )

    def _visites(self, lignes: int, colonnes: int, mcu_colonnes: int) -> int:
        """Blocs décodés pour une région de ``lignes`` lignes, tous balayages compris."""
        composantes = self._composantes
        mcu_lignes = -(-lignes // composantes[0].vertical)
        visites = 0
        for balayage in self._balayages:
            if len(balayage.composantes) == 1:
                visites += lignes * colonnes
            else:
                visites += (
                    mcu_lignes
                    * mcu_colonnes
                    * sum(
                        composantes[i].horizontal * composantes[i].vertical
                        for i, _, _ in balayage.composantes
                    )
                )
        return visites

    def _balayage(
        self,
        balayage: _Balayage,
        valeurs: array[int],
        grille: int,
        lignes: int,
        colonnes: int,
        mcu_colonnes: int,
    ) -> None:
        """Décode le balayage jusqu'à la dernière ligne de la région."""
        composantes = self._composantes
        # Blocs à décoder, dans l'ordre du balayage : (composante, ligne, colonne) par MCU.
        if len(balayage.composantes) == 1:
            unites = [(0, 0, 0)]
            mcus = lignes * colonnes
            par_ligne = colonnes
        else:
            unites = [
                (rang, v, h)
                for rang, (i, _, _) in enumerate(balayage.composantes)
                for v in range(composantes[i].vertical)
                for h in range(composantes[i].horizontal)
            ]
            par_ligne = mcu_colonnes
            mcus = -(-lignes // composantes[0].vertical) * mcu_colonnes
        self._contexte.compter_objets(mcus * len(unites))
        intervalle = balayage.intervalle or mcus
        borne = mcus * len(unites) * _OCTETS_PAR_BLOC + (mcus // intervalle + 1) * 2 + 16
        donnees = self._entropie(balayage.debut, min(balayage.fin - balayage.debut, borne))
        morceaux = [m.replace(b"\xff\x00", b"\xff") for m in _RST.split(donnees)]
        if len(morceaux) < -(-mcus // intervalle):
            raise self._manque(balayage)
        premiere = composantes[0]
        for numero in range(-(-mcus // intervalle)):
            debut = numero * intervalle
            fin = min(mcus, debut + intervalle)
            positions = []
            for mcu in range(debut, fin):
                ligne_mcu, colonne_mcu = divmod(mcu, par_ligne)
                for rang, v, h in unites:
                    if len(balayage.composantes) == 1:
                        positions.append((ligne_mcu * grille + colonne_mcu) * 64)
                    elif balayage.composantes[rang][0] == 0:
                        ligne = ligne_mcu * premiere.vertical + v
                        colonne = colonne_mcu * premiere.horizontal + h
                        positions.append((ligne * grille + colonne) * 64)
                    else:
                        positions.append(-1 - rang)
            if not _intervalle(morceaux[numero], balayage, positions, valeurs, self._procede):
                raise self._manque(balayage)

    def _manque(self, balayage: _Balayage) -> _Arret:
        if balayage.fin >= self._contexte.taille:
            return _Arret(RaisonNonMenee.FICHIER_TRONQUE, balayage.debut)
        return _Arret(RaisonNonMenee.FORMAT_PARTIEL, balayage.debut)

    def _entropie(self, debut: int, taille: int) -> bytes:
        """``taille`` octets à partir de ``debut``, par lectures d'au plus 16 Mio."""
        fin = debut + taille
        return b"".join(
            self._contexte.lire(position, min(TAILLE_MAX_LECTURE, fin - position))
            for position in range(debut, fin, TAILLE_MAX_LECTURE)
        )


def _colonnes(valeurs: array[int], grille: int, colonnes: int, lignes: int) -> array[int]:
    """Retire les blocs de remplissage des MCU à droite de la composante."""
    gardees = array("q")
    for ligne in range(lignes):
        debut = ligne * grille * 64
        gardees.extend(valeurs[debut : debut + colonnes * 64])
    return gardees


def _intervalle(
    donnees: bytes, balayage: _Balayage, positions: list[int], valeurs: array[int], procede: int
) -> bool:
    """Décode les blocs d'un intervalle de redémarrage ; faux si les données manquent.

    ``positions`` donne, pour chaque bloc dans l'ordre, sa place dans ``valeurs`` ; un bloc d'une
    autre composante (valeur négative ``-1 - rang``) est décodé puis oublié.
    """
    if procede != _PROGRESSIF:
        return _sequentiel(donnees, balayage, positions, valeurs)
    if balayage.ss == 0:
        return _continu_progressif(donnees, balayage, positions, valeurs)
    if balayage.ah == 0:
        return _alternatif_premier(donnees, balayage, positions, valeurs)
    return _alternatif_raffine(donnees, balayage, positions, valeurs)


# Les quatre fonctions suivantes gardent le lecteur de bits dans des variables locales : c'est le
# cœur du décodage, appelé pour chaque code. ``tampon`` porte ``bits`` bits non lus ; il est
# rechargé de quatre octets quand il en porte moins de 32, de zéros au-delà des données (comme
# libjpeg) ; ``lus`` compte les octets chargés. Les données manquent si plus de bits ont été
# consommés que les données n'en portent.


def _etendre(bits: int, taille: int) -> int:
    """Valeur signée d'un nombre de ``taille`` bits (T.81, figure F.12)."""
    return bits if bits >= 1 << (taille - 1) else bits - (1 << taille) + 1


def _sequentiel(
    donnees: bytes, balayage: _Balayage, positions: list[int], valeurs: array[int]
) -> bool:
    tables = balayage.composantes
    predictions = [0] * len(tables)
    tampon = bits = lus = 0
    disponibles = len(donnees) * 8
    for position in positions:
        rang = 0 if position >= 0 else -1 - position
        _, continu, alternatif = tables[rang]
        if bits < 32:
            tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                donnees[lus : lus + 4].ljust(4, b"\x00")
            )
            lus += 4
            bits += 32
        code = continu[(tampon >> (bits - 16)) & 0xFFFF]
        if not code or code & 0xFF > 11:
            return False
        bits -= code >> 8
        taille = code & 0xFF
        if taille:
            predictions[rang] += _etendre((tampon >> (bits - taille)) & ((1 << taille) - 1), taille)
            bits -= taille
        if position >= 0:
            valeurs[position] = predictions[rang]
        k = 1
        while k < 64:
            if bits < 32:
                tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                    donnees[lus : lus + 4].ljust(4, b"\x00")
                )
                lus += 4
                bits += 32
            code = alternatif[(tampon >> (bits - 16)) & 0xFFFF]
            if not code:
                return False
            bits -= code >> 8
            r, taille = (code >> 4) & 0x0F, code & 0x0F
            if not taille:
                if r != 15:
                    break
                k += 16
                continue
            k += r
            if k > 63:
                return False
            if position >= 0:
                valeurs[position + k] = _etendre(
                    (tampon >> (bits - taille)) & ((1 << taille) - 1), taille
                )
            bits -= taille
            k += 1
        if lus * 8 - bits > disponibles:
            return False
    return True


def _continu_progressif(
    donnees: bytes, balayage: _Balayage, positions: list[int], valeurs: array[int]
) -> bool:
    tables = balayage.composantes
    predictions = [0] * len(tables)
    al = balayage.al
    premier = balayage.ah == 0
    tampon = bits = lus = 0
    disponibles = len(donnees) * 8
    for position in positions:
        rang = 0 if position >= 0 else -1 - position
        if bits < 32:
            tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                donnees[lus : lus + 4].ljust(4, b"\x00")
            )
            lus += 4
            bits += 32
        if premier:
            code = tables[rang][1][(tampon >> (bits - 16)) & 0xFFFF]
            if not code or code & 0xFF > 11:
                return False
            bits -= code >> 8
            taille = code & 0xFF
            if taille:
                predictions[rang] += _etendre(
                    (tampon >> (bits - taille)) & ((1 << taille) - 1), taille
                )
                bits -= taille
            if position >= 0:
                valeurs[position] = predictions[rang] << al
        else:
            bits -= 1
            if position >= 0 and (tampon >> bits) & 1:
                valeurs[position] |= 1 << al
        if lus * 8 - bits > disponibles:
            return False
    return True


def _alternatif_premier(
    donnees: bytes, balayage: _Balayage, positions: list[int], valeurs: array[int]
) -> bool:
    alternatif = balayage.composantes[0][2]
    ss, se, al = balayage.ss, balayage.se, balayage.al
    fin_de_bande = 0
    tampon = bits = lus = 0
    disponibles = len(donnees) * 8
    for position in positions:
        if fin_de_bande:
            fin_de_bande -= 1
            continue
        k = ss
        while k <= se:
            if bits < 32:
                tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                    donnees[lus : lus + 4].ljust(4, b"\x00")
                )
                lus += 4
                bits += 32
            code = alternatif[(tampon >> (bits - 16)) & 0xFFFF]
            if not code:
                return False
            bits -= code >> 8
            r, taille = (code >> 4) & 0x0F, code & 0x0F
            if not taille:
                if r != 15:
                    fin_de_bande = (1 << r) - 1
                    if r:
                        fin_de_bande += (tampon >> (bits - r)) & ((1 << r) - 1)
                        bits -= r
                    break
                k += 16
                continue
            k += r
            if k > se:
                return False
            valeurs[position + k] = (
                _etendre((tampon >> (bits - taille)) & ((1 << taille) - 1), taille) << al
            )
            bits -= taille
            k += 1
        if lus * 8 - bits > disponibles:
            return False
    return True


def _alternatif_raffine(
    donnees: bytes, balayage: _Balayage, positions: list[int], valeurs: array[int]
) -> bool:
    """Raffinement des coefficients alternatifs (T.81, G.1.2.3 ; decode_mcu_AC_refine de
    libjpeg)."""
    alternatif = balayage.composantes[0][2]
    ss, se = balayage.ss, balayage.se
    plus, moins = 1 << balayage.al, -1 << balayage.al
    fin_de_bande = 0
    tampon = bits = lus = 0
    disponibles = len(donnees) * 8
    for position in positions:
        k = ss
        if bits < 32:
            tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                donnees[lus : lus + 4].ljust(4, b"\x00")
            )
            lus += 4
            bits += 32
        if not fin_de_bande:
            # Au moins 31 bits à chaque tour : le bloc commence rechargé, et la boucle des
            # corrections recharge avant chaque bit qu'elle lit. Un code (16 bits au plus) suivi
            # d'un signe ou de la longueur d'une série (14 bits au plus) y tient.
            while k <= se:
                code = alternatif[(tampon >> (bits - 16)) & 0xFFFF]
                if not code:
                    return False
                bits -= code >> 8
                r, taille = (code >> 4) & 0x0F, code & 0x0F
                nouveau = 0
                if taille:
                    bits -= 1
                    nouveau = plus if (tampon >> bits) & 1 else moins
                elif r != 15:
                    fin_de_bande = 1 << r
                    if r:
                        fin_de_bande += (tampon >> (bits - r)) & ((1 << r) - 1)
                        bits -= r
                    break
                # Coefficients déjà non nuls : un bit de correction chacun ; r coefficients
                # nuls passés avant celui qui devient non nul.
                while k <= se:
                    if bits < 32:
                        tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                            donnees[lus : lus + 4].ljust(4, b"\x00")
                        )
                        lus += 4
                        bits += 32
                    valeur = valeurs[position + k]
                    if valeur:
                        bits -= 1
                        if (tampon >> bits) & 1 and not valeur & plus:
                            valeurs[position + k] = valeur + (plus if valeur >= 0 else moins)
                    else:
                        if not r:
                            break
                        r -= 1
                    k += 1
                if nouveau:
                    if k > se:
                        return False
                    valeurs[position + k] = nouveau
                k += 1
        if fin_de_bande:
            while k <= se:
                if bits < 32:
                    tampon = (tampon & ((1 << bits) - 1)) << 32 | int.from_bytes(
                        donnees[lus : lus + 4].ljust(4, b"\x00")
                    )
                    lus += 4
                    bits += 32
                valeur = valeurs[position + k]
                if valeur:
                    bits -= 1
                    if (tampon >> bits) & 1 and not valeur & plus:
                        valeurs[position + k] = valeur + (plus if valeur >= 0 else moins)
                k += 1
            fin_de_bande -= 1
        if lus * 8 - bits > disponibles:
            return False
    return True
