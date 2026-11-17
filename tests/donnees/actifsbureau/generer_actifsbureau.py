"""Échantillons et oracle du module actifsbureau (complément bureautique de T52).

Documents écrits par LibreOffice, piloté par son interface UNO, comme les écrirait un auteur :

- ``macros.odt`` : une bibliothèque Basic du document (un module), liée à l'ouverture du
  document (``OnLoad``) et à son enregistrement (``OnSave``), et un bouton de formulaire qui
  l'appelle au clic ;
- ``liens.odt`` : un lien vers un site, une image liée (fichier hors du document), une section
  liée à un autre document, un modèle et un rechargement automatique vers une adresse ;
- ``objet.odt`` : un tableur incorporé (objet OpenDocument, ordinaire) ;
- ``liens.docx`` et ``objet.docx`` : les deux précédents enregistrés en DOCX par LibreOffice.

``oracle.json`` consigne ensuite ce qu'en dit LibreOffice, qui relit chaque document : ses
bibliothèques Basic qui ont un module, ses événements du document liés à une macro, les
événements de ses contrôles de formulaire, son modèle et son rechargement automatique, ses
sections liées, ses images liées, ses objets incorporés et ses liens vers une adresse.

Les fichiers liés (image, section, modèle) sont écrits dans un dossier temporaire, effacé à la
fin : leur chemin reste écrit dans les documents, jamais suivi par l'outil. Les adresses sont
celles du domaine réservé ``example.org`` (RFC 2606) ; LibreOffice n'en consulte aucune.

Outils de la version du dépôt : LibreOffice 25.2.3.2 et son module Python ``uno``, sous Debian 13.
À lancer depuis ce dossier, avec l'interpréteur du système (où ``uno`` est installé) :
``python3 -I generer_actifsbureau.py``. Les documents changent à chaque génération (dates,
identifiants) : ne régénérer que pour changer les échantillons.
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
import time
import zlib

import uno
from com.sun.star.beans import PropertyValue

ICI = pathlib.Path(__file__).resolve().parent
MACRO = "vnd.sun.star.script:Standard.Module1.Main?language=Basic&location=document"
CALC = "47BBB4CB-CE4C-4E80-A591-42D9AE74950F"


def _png() -> bytes:
    """Image d'un pixel, écrite ici (PNG, ISO 15948)."""

    def bloc(sorte: bytes, donnees: bytes) -> bytes:
        crc = zlib.crc32(sorte + donnees).to_bytes(4, "big")
        return len(donnees).to_bytes(4, "big") + sorte + donnees + crc

    entete = (1).to_bytes(4, "big") * 2 + bytes([8, 2, 0, 0, 0])
    pixels = zlib.compress(b"\x00\xff\xff\xff")
    return b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", entete) + bloc(b"IDAT", pixels) + bloc(b"IEND", b"")


def propriete(nom, valeur):
    resultat = PropertyValue()
    resultat.Name = nom
    resultat.Value = valeur
    return resultat


def proprietes(**valeurs):
    return tuple(propriete(nom, valeur) for nom, valeur in valeurs.items())


def _outil(nom: str) -> str:
    chemin = shutil.which(nom)
    if chemin is None:
        raise SystemExit(f"{nom} introuvable")
    return chemin


class Office:
    """LibreOffice sans affichage, joint par un tube nommé, avec un profil jetable."""

    def __init__(self, dossier: pathlib.Path) -> None:
        tube = f"vk-actifsbureau-{os.getpid()}"
        self._processus = subprocess.Popen(
            [
                _outil("soffice"),
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
        self.smgr = distant.ServiceManager
        self.contexte = distant
        self.bureau = self.smgr.createInstanceWithContext("com.sun.star.frame.Desktop", distant)

    def nouveau(self):
        return self.bureau.loadComponentFromURL(
            "private:factory/swriter", "_blank", 0, proprietes(Hidden=True)
        )

    def ouvrir(self, chemin: pathlib.Path):
        return self.bureau.loadComponentFromURL(
            chemin.as_uri(), "_blank", 0, proprietes(Hidden=True, MacroExecutionMode=0)
        )

    def fermer(self) -> None:
        # La liaison se coupe pendant l'arrêt : l'exception qui en vient est attendue.
        with contextlib.suppress(Exception):
            self.bureau.terminate()
        self._processus.wait(timeout=60)


def enregistrer(document, chemin: pathlib.Path, filtre: str) -> None:
    document.storeToURL(chemin.as_uri(), proprietes(FilterName=filtre))


def texte(document, contenu: str) -> None:
    curseur = document.Text.createTextCursor()
    curseur.gotoEnd(False)
    document.Text.insertString(curseur, contenu, False)


# Documents


def macros(office: Office) -> None:
    document = office.nouveau()
    texte(document, "Document à macros.")
    bibliotheques = document.BasicLibraries
    if not bibliotheques.hasByName("Standard"):
        bibliotheques.createLibrary("Standard")
    bibliotheques.getByName("Standard").insertByName(
        "Module1", 'Sub Main\n  MsgBox "Bonjour"\nEnd Sub\n'
    )
    script = uno.Any(
        "[]com.sun.star.beans.PropertyValue",
        proprietes(EventType="Script", Script=MACRO),
    )
    for evenement in ("OnLoad", "OnSave"):
        uno.invoke(document.Events, "replaceByName", (evenement, script))
    # Bouton de formulaire qui appelle la macro au clic.
    forme = document.createInstance("com.sun.star.drawing.ControlShape")
    taille = uno.createUnoStruct("com.sun.star.awt.Size")
    taille.Width, taille.Height = 4000, 1000
    forme.setSize(taille)
    bouton = document.createInstance("com.sun.star.form.component.CommandButton")
    bouton.Label = "Bouton"
    bouton.Name = "Bouton"
    forme.setControl(bouton)
    document.DrawPage.add(forme)
    formulaire = bouton.getParent()
    rang = next(i for i in range(formulaire.Count) if formulaire.getByIndex(i) == bouton)
    description = uno.createUnoStruct("com.sun.star.script.ScriptEventDescriptor")
    description.ListenerType = "XActionListener"
    description.EventMethod = "actionPerformed"
    description.ScriptType = "Script"
    description.ScriptCode = MACRO
    formulaire.registerScriptEvent(rang, description)
    enregistrer(document, ICI / "macros.odt", "writer8")
    document.close(True)


def liens(office: Office, dossier: pathlib.Path) -> None:
    image = dossier / "logo.png"
    image.write_bytes(_png())
    section = office.nouveau()
    texte(section, "Texte d'une section liée.")
    enregistrer(section, dossier / "section.odt", "writer8")
    section.close(True)

    document = office.nouveau()
    texte(document, "Document à liens. ")
    curseur = document.Text.createTextCursor()
    curseur.gotoEnd(False)
    document.Text.insertString(curseur, "Un site", True)
    curseur.HyperLinkURL = "https://example.org/page"
    curseur.gotoEnd(False)
    document.Text.insertString(curseur, ".", False)

    fournisseur = office.smgr.createInstanceWithContext(
        "com.sun.star.graphic.GraphicProvider", office.contexte
    )
    graphique = fournisseur.queryGraphic(proprietes(URL=image.as_uri(), LoadAsLink=True))
    cadre = document.createInstance("com.sun.star.text.TextGraphicObject")
    cadre.Graphic = graphique
    document.Text.insertTextContent(document.Text.getEnd(), cadre, False)

    lien = uno.createUnoStruct("com.sun.star.text.SectionFileLink")
    lien.FileURL = (dossier / "section.odt").as_uri()
    partie = document.createInstance("com.sun.star.text.TextSection")
    partie.FileLink = lien
    document.Text.insertTextContent(document.Text.getEnd(), partie, False)

    proprietes_ = document.DocumentProperties
    proprietes_.TemplateURL = (dossier / "modele.ott").as_uri()
    proprietes_.TemplateName = "Modèle"
    proprietes_.AutoloadURL = "https://example.org/autre.odt"
    proprietes_.AutoloadSecs = 60
    enregistrer(document, ICI / "liens.odt", "writer8")
    enregistrer(document, ICI / "liens.docx", "MS Word 2007 XML")
    document.close(True)


def objet(office: Office) -> None:
    document = office.nouveau()
    texte(document, "Document à objet incorporé.")
    incorpore = document.createInstance("com.sun.star.text.TextEmbeddedObject")
    incorpore.CLSID = CALC
    document.Text.insertTextContent(document.Text.getEnd(), incorpore, False)
    enregistrer(document, ICI / "objet.odt", "writer8")
    enregistrer(document, ICI / "objet.docx", "MS Word 2007 XML")
    document.close(True)


# Oracle


def _paragraphes(document):
    enumeration = document.Text.createEnumeration()
    while enumeration.hasMoreElements():
        yield enumeration.nextElement()


def _liens(document) -> int:
    nombre = 0
    for paragraphe in _paragraphes(document):
        if not paragraphe.supportsService("com.sun.star.text.Paragraph"):
            continue
        morceaux = paragraphe.createEnumeration()
        while morceaux.hasMoreElements():
            morceau = morceaux.nextElement()
            if morceau.HyperLinkURL.startswith(("http:", "https:")):
                nombre += 1
    return nombre


def _evenements_des_controles(document) -> int:
    nombre = 0
    formulaires = document.DrawPage.Forms
    for i in range(formulaires.Count):
        formulaire = formulaires.getByIndex(i)
        for j in range(formulaire.Count):
            nombre += sum(1 for e in formulaire.getScriptEvents(j) if e.ScriptCode)
    return nombre


def relevé(document) -> dict[str, object]:
    bibliotheques = document.BasicLibraries
    avec_module = sorted(
        nom for nom in bibliotheques.ElementNames if bibliotheques.getByName(nom).hasElements()
    )
    evenements = sorted(
        nom
        for nom in document.Events.ElementNames
        if any(p.Name == "Script" and p.Value for p in document.Events.getByName(nom) or ())
    )
    sections = document.TextSections
    liees = sum(1 for nom in sections.ElementNames if sections.getByName(nom).FileLink.FileURL)
    graphiques = document.GraphicObjects
    images = sum(1 for nom in graphiques.ElementNames if graphiques.getByName(nom).Graphic.Linked)
    proprietes_ = document.DocumentProperties
    return {
        "bibliotheques_basic": len(avec_module),
        "evenements_du_document": evenements,
        "evenements_des_controles": _evenements_des_controles(document),
        "modele": bool(proprietes_.TemplateURL),
        "rechargement": bool(proprietes_.AutoloadURL),
        "sections_liees": liees,
        "images_liees": images,
        "objets_incorpores": document.EmbeddedObjects.Count,
        "liens": _liens(document),
    }


def main() -> None:
    dossier = pathlib.Path(tempfile.mkdtemp())
    office = Office(dossier)
    try:
        macros(office)
        liens(office, dossier)
        objet(office)
        oracle = {}
        for nom in ("macros.odt", "liens.odt", "liens.docx", "objet.odt", "objet.docx"):
            document = office.ouvrir(ICI / nom)
            oracle[nom] = relevé(document)
            document.close(True)
    finally:
        office.fermer()
        shutil.rmtree(dossier, ignore_errors=True)
    oracle["outils"] = {"LibreOffice": "25.2.3.2"}
    texte_ = json.dumps(oracle, ensure_ascii=False, indent=2, sort_keys=True)
    (ICI / "oracle.json").write_text(texte_ + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
