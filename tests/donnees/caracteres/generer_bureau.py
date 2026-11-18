"""Échantillons et oracle du module caracteres pour le DOCX et l'ODT (complément de T80).

Un document écrit par LibreOffice, piloté par son interface UNO, comme l'écrirait un auteur,
enregistré en ODT (``texte.odt``) et en DOCX (``texte.docx``) :

- corps : un mot mêlé (``p\\u0430ypal``, a cyrillique) ; un espace sans chasse dans un mot ;
  une portion masquée par sa mise en forme (``CharHidden``) qui porte un espace sans chasse ;
  une suppression suivie (modifications enregistrées) d'un passage qui porte un forçage
  bidirectionnel ;
- note de bas de page : un texte écrit en étiquettes Unicode ;
- en-tête de la page : une espace cadratin (U+2003) ;
- commentaire : un caractère à usage privé.

``oracle.json`` consigne ce que LibreOffice relit de chaque document : le texte de ses
paragraphes, notes, en-tête et commentaires, en points de code.

Outils de la version du dépôt : LibreOffice 25.2.3.2 et son module Python ``uno``, sous Debian 13.
À lancer depuis ce dossier, avec l'interpréteur du système (où ``uno`` est installé) :
``python3 -I generer_bureau.py``. Les documents changent à chaque génération (dates,
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

import uno
from com.sun.star.beans import PropertyValue

ICI = pathlib.Path(__file__).resolve().parent
MELE = "Payez sur p\u0430ypal ici."
SANS_CHASSE = "Un mot\u200bcoupé en deux. "
MASQUE = "consigne\u200bmasquée"
SUPPRIME = "passage\u202esupprimé"
NOTE = "Note" + "".join(chr(0xE0000 + ord(c)) for c in "cache")
ENTETE = "En-tête\u2003large"
COMMENTAIRE = "Avis\ue000privé"


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
        tube = f"vk-caracteres-{os.getpid()}"
        soffice = shutil.which("soffice")
        if soffice is None:
            raise SystemExit("soffice introuvable")
        self._processus = subprocess.Popen(
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

    def nouveau(self):
        return self.bureau.loadComponentFromURL(
            "private:factory/swriter", "_blank", 0, proprietes(Hidden=True)
        )

    def ouvrir(self, chemin: pathlib.Path):
        return self.bureau.loadComponentFromURL(
            chemin.as_uri(), "_blank", 0, proprietes(Hidden=True, MacroExecutionMode=0)
        )

    def fermer(self) -> None:
        with contextlib.suppress(Exception):
            self.bureau.terminate()
        self._processus.wait(timeout=60)


def ecrire(office: Office) -> None:
    document = office.nouveau()
    texte = document.Text
    curseur = texte.createTextCursor()
    texte.insertString(curseur, MELE, False)
    texte.insertControlCharacter(curseur, 0, False)  # PARAGRAPH_BREAK
    texte.insertString(curseur, SANS_CHASSE, False)
    curseur.setPropertyValue("CharHidden", True)
    texte.insertString(curseur, MASQUE, False)
    curseur.setPropertyValue("CharHidden", False)
    texte.insertControlCharacter(curseur, 0, False)
    texte.insertString(curseur, "Avant " + SUPPRIME + " après.", False)
    note = document.createInstance("com.sun.star.text.Footnote")
    texte.insertTextContent(curseur, note, False)
    note.setString(NOTE)
    commentaire = document.createInstance("com.sun.star.text.textfield.Annotation")
    commentaire.Content = COMMENTAIRE
    commentaire.Author = "Relecture"
    texte.insertTextContent(curseur, commentaire, False)
    style = document.StyleFamilies.getByName("PageStyles").getByName("Standard")
    style.HeaderIsOn = True
    style.HeaderText.setString(ENTETE)
    # Suppression enregistrée comme modification suivie.
    document.RecordChanges = True
    recherche = document.createSearchDescriptor()
    recherche.SearchString = SUPPRIME
    trouve = document.findFirst(recherche)
    trouve.setString("")
    document.RecordChanges = False
    document.storeToURL((ICI / "texte.odt").as_uri(), proprietes(FilterName="writer8"))
    document.storeToURL((ICI / "texte.docx").as_uri(), proprietes(FilterName="MS Word 2007 XML"))
    document.close(True)


def _points(chaine: str) -> list[str]:
    return [f"U+{ord(c):04X}" for c in chaine]


def releve(document) -> dict[str, object]:
    paragraphes = []
    enumeration = document.Text.createEnumeration()
    while enumeration.hasMoreElements():
        paragraphes.append(_points(enumeration.nextElement().getString()))
    notes = [
        _points(document.Footnotes.getByIndex(i).getString())
        for i in range(document.Footnotes.Count)
    ]
    style = document.StyleFamilies.getByName("PageStyles").getByName("Standard")
    entete = _points(style.HeaderText.getString()) if style.HeaderIsOn else []
    commentaires = []
    champs = document.TextFields.createEnumeration()
    while champs.hasMoreElements():
        champ = champs.nextElement()
        if champ.supportsService("com.sun.star.text.textfield.Annotation"):
            commentaires.append(_points(champ.Content))
    suppressions = []
    modifications = document.Redlines.createEnumeration()
    while modifications.hasMoreElements():
        modification = modifications.nextElement()
        if modification.RedlineType == "Delete":
            debut = modification.RedlineStart
            curseur = debut.getText().createTextCursorByRange(debut)
            curseur.gotoRange(modification.RedlineEnd, True)
            suppressions.append(_points(curseur.getString()))
    return {
        "paragraphes": paragraphes,
        "notes": notes,
        "entete": entete,
        "commentaires": commentaires,
        "suppressions": suppressions,
    }


def main() -> None:
    dossier = pathlib.Path(tempfile.mkdtemp())
    office = Office(dossier)
    try:
        ecrire(office)
        oracle = {}
        for nom in ("texte.odt", "texte.docx"):
            document = office.ouvrir(ICI / nom)
            oracle[nom] = releve(document)
            document.close(True)
    finally:
        office.fermer()
        shutil.rmtree(dossier, ignore_errors=True)
    oracle["outils"] = {"LibreOffice": "25.2.3.2"}
    texte_ = json.dumps(oracle, ensure_ascii=False, indent=2, sort_keys=True)
    (ICI / "oracle.json").write_text(texte_ + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
