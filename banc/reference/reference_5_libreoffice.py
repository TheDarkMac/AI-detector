"""Phase 5 du corpus de référence (T100) : retouches faites par l'interface de LibreOffice.

Exécute les tâches que la phase 4 a écrites dans ``uno.json`` (ADR-0275) :

- ``paragraphe-ajoute`` (DOCX, ODT) : un paragraphe tapé à la fin du document par le répartiteur
  de commandes de l'interface (``.uno:InsertText``), comme le ferait une personne, puis le
  document enregistré dans son format ;
- ``remplacement`` (DOCX, ODT) : le premier nombre du document, ou à défaut le premier mot d'au
  moins sept lettres, remplacé, puis le document enregistré dans son format ;
- ``edition-libreoffice`` (PDF) : le PDF ouvert dans Draw (import des PDF), une zone de texte
  ajoutée sur la première page, puis exporté en PDF.

Écrit ``uno.resultats.json``. Outils : LibreOffice et son module Python ``uno``, sous Debian 13.
À lancer depuis la racine du dépôt, avec l'interpréteur du système (où ``uno`` est installé) :
``python3 -I banc/reference/reference_5_libreoffice.py``.
"""
# mypy: ignore-errors
# (uno n'est pas dans l'environnement du projet.)

import contextlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import threading
import time

import uno
from com.sun.star.awt import Point, Size
from com.sun.star.beans import PropertyValue

ICI = pathlib.Path(__file__).resolve().parent
TACHES = ICI / "uno.json"
RESULTATS = ICI / "uno.resultats.json"
PARAGRAPHES = (
    "Mise à jour : le montant est porté à 1 250 euros.",
    "Ce document annule et remplace la version précédente.",
    "Validé en réunion le 14 mars 2021.",
)
FILTRES = {".docx": "MS Word 2007 XML", ".odt": "writer8", ".pdf": "draw_pdf_Export"}
DUREE_MAX = 300
"""Secondes par tâche : au-delà, LibreOffice est arrêté et relancé, la tâche notée en échec (un
PDF de 13 pages a bloqué Draw plus de dix minutes pendant T100)."""


def propriete(nom, valeur):
    resultat = PropertyValue()
    resultat.Name = nom
    resultat.Value = valeur
    return resultat


def proprietes(**valeurs):
    return tuple(propriete(nom, valeur) for nom, valeur in valeurs.items())


class Office:
    """LibreOffice sans affichage, joint par un tube nommé, avec un profil jetable."""

    def __init__(self, dossier: pathlib.Path) -> None:
        self.tue = False
        tube = f"vk-corpus-{os.getpid()}-{id(dossier)}"
        soffice = shutil.which("soffice")
        if soffice is None:
            raise SystemExit("soffice introuvable")
        self._processus = subprocess.Popen(  # noqa: S603 (soffice du poste, arguments fixes)
            [
                soffice,
                "--headless",
                "--invisible",
                "--norestore",
                f"-env:UserInstallation={(dossier / 'profil').as_uri()}",
                f"--accept=pipe,name={tube};urp;",
            ]
        )
        local = uno.getComponentContext()
        resolveur = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local
        )
        for _ in range(120):
            try:
                distant = resolveur.resolve(f"uno:pipe,name={tube};urp;StarOffice.ComponentContext")
                break
            except Exception:  # LibreOffice pas encore prêt
                time.sleep(0.5)
        else:
            raise RuntimeError("LibreOffice ne répond pas")
        self.bureau = distant.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", distant
        )
        self.repartiteur = distant.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.DispatchHelper", distant
        )

    def ouvrir(self, chemin: pathlib.Path, **options):
        return self.bureau.loadComponentFromURL(
            chemin.as_uri(), "_blank", 0, proprietes(Hidden=True, MacroExecutionMode=0, **options)
        )

    def tuer(self) -> None:
        """Appelé par la minuterie d'une tâche trop longue."""
        self.tue = True
        with contextlib.suppress(Exception):
            self._processus.kill()

    def vivant(self) -> bool:
        return self._processus.poll() is None

    def fermer(self) -> None:
        with contextlib.suppress(Exception):
            self.bureau.terminate()
        try:
            self._processus.wait(timeout=60)
        except subprocess.TimeoutExpired:
            self._processus.kill()
            self._processus.wait()


def paragraphe(office: Office, document, rang: int) -> str:
    texte = PARAGRAPHES[rang % len(PARAGRAPHES)]
    document.CurrentController.ViewCursor.gotoEnd(False)
    cadre = document.CurrentController.Frame
    office.repartiteur.executeDispatch(cadre, ".uno:InsertPara", "", 0, ())
    office.repartiteur.executeDispatch(cadre, ".uno:InsertText", "", 0, proprietes(Text=texte))
    return f"paragraphe « {texte} » tapé à la fin, par l'interface de LibreOffice"


def remplacer(document) -> str:
    for motif, nouveau, quoi in (
        (r"[0-9]+", "1250", "premier nombre"),
        (r"\b[[:alpha:]]{7,}\b", "modifié", "premier mot d'au moins sept lettres"),
    ):
        recherche = document.createSearchDescriptor()
        recherche.SearchString = motif
        recherche.SearchRegularExpression = True
        trouve = document.findFirst(recherche)
        if trouve is not None:
            ancien = trouve.getString()
            trouve.setString(nouveau)
            return f"{quoi} remplacé ({len(ancien)} caractères par « {nouveau} »), par LibreOffice"
    raise ValueError("rien à remplacer")


def editer_pdf(document) -> str:
    page = document.DrawPages.getByIndex(0)
    forme = document.createInstance("com.sun.star.drawing.TextShape")
    position = Point()
    position.X, position.Y = 2000, 2000
    taille = Size()
    taille.Width, taille.Height = 9000, 1200
    forme.Position = position
    forme.Size = taille
    page.add(forme)
    forme.setString("Montant : 1 250 EUR")
    forme.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
    forme.FillColor = 0xFFFFFF
    return "zone de texte « Montant : 1 250 EUR » ajoutée sur la première page dans Draw"


def executer(office: Office, tache: dict, rang: int) -> str:
    entree = ICI.joinpath(*tache["entree"].split("/"))
    sortie = ICI.joinpath(*tache["chemin"].split("/"))
    sortie.parent.mkdir(parents=True, exist_ok=True)
    options = {"FilterName": "draw_pdf_import"} if entree.suffix == ".pdf" else {}
    document = office.ouvrir(entree, **options)
    if document is None:
        raise ValueError("document non ouvert")
    try:
        if tache["operation"] == "edition-libreoffice":
            description = editer_pdf(document)
        elif tache["operation"] == "paragraphe-ajoute":
            description = paragraphe(office, document, rang)
        else:
            description = remplacer(document)
        document.storeToURL(sortie.as_uri(), proprietes(FilterName=FILTRES[sortie.suffix]))
    finally:
        with contextlib.suppress(Exception):
            document.close(True)
    if not sortie.exists():
        raise ValueError("document non enregistré")
    return description


def main() -> None:
    taches = json.loads(TACHES.read_text(encoding="utf-8"))
    resultats = json.loads(RESULTATS.read_text(encoding="utf-8")) if RESULTATS.exists() else {}
    with tempfile.TemporaryDirectory() as temporaire:
        office = Office(pathlib.Path(temporaire))
        try:
            for rang, tache in enumerate(taches):
                if tache["chemin"] in resultats:
                    continue
                minuterie = threading.Timer(DUREE_MAX, office.tuer)
                minuterie.start()
                try:
                    resultats[tache["chemin"]] = {
                        "etat": "fait",
                        "description": executer(office, tache, rang),
                    }
                except Exception as erreur:  # document que LibreOffice ne sait pas traiter
                    ICI.joinpath(*tache["chemin"].split("/")).unlink(missing_ok=True)
                    nom = "DelaiDepasse" if office.tue else type(erreur).__name__
                    resultats[tache["chemin"]] = {"etat": "echec", "erreur": nom}
                finally:
                    minuterie.cancel()
                if not office.vivant():
                    office.fermer()
                    office = Office(pathlib.Path(temporaire) / f"relance-{rang}")
                print(f"{tache['chemin']} : {resultats[tache['chemin']]['etat']}", flush=True)
                RESULTATS.write_text(json.dumps(resultats, ensure_ascii=False, indent=1))
        finally:
            office.fermer()


if __name__ == "__main__":
    main()
