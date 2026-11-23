"""Échantillons et oracle du module historique (T81).

Un document écrit par LibreOffice en trois sessions, comme l'écrirait un auteur : le texte est
tapé par le répartiteur de commandes de l'interface (``.uno:InsertText``), qui passe par le
traitement de la saisie, où LibreOffice marque chaque passage de l'identifiant de la session
(rsid) ; ``insertString`` de l'API ne le fait pas.

- session 1 : un document neuf, un paragraphe, enregistré en ODT (``sessions.odt``) ;
- session 2 : le document rouvert, un paragraphe ajouté, puis un autre tapé avec les
  modifications enregistrées (une insertion suivie), et un commentaire ; enregistré ;
- session 3 : rouvert, un paragraphe ajouté, enregistré, puis exporté en DOCX
  (``sessions.docx``), où LibreOffice n'écrit ni rsid ni temps d'édition non nul.

``oracle.json`` consigne ce que LibreOffice relit de chaque document : longueur du texte de
chaque portion du corps et identifiant de session qu'il lui donne (propriété ``Rsid``), nombre
de modifications suivies et de commentaires, nombre de leurs auteurs distincts, cycles et durée
d'édition (``DocumentProperties``).

Outils de la version du dépôt : LibreOffice 25.2.3.2 et son module Python ``uno``, sous Debian 13.
À lancer depuis ce dossier, avec l'interpréteur du système (où ``uno`` est installé) :
``python3 -I generer_historique.py``. Les documents changent à chaque génération (dates,
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
PREMIER = "Premier paragraphe, écrit dans la première session."
DEUXIEME = "Deuxième paragraphe, ajouté à la réouverture."
SUIVI = "Troisième paragraphe, tapé avec les modifications enregistrées."
COMMENTAIRE = "Relu."
TROISIEME = "Quatrième paragraphe, dans la troisième session."


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
        tube = f"vk-historique-{os.getpid()}"
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
        self.repartiteur = distant.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.DispatchHelper", distant
        )

    def nouveau(self):
        return self.bureau.loadComponentFromURL(
            "private:factory/swriter", "_blank", 0, proprietes(Hidden=True)
        )

    def ouvrir(self, chemin: pathlib.Path):
        return self.bureau.loadComponentFromURL(
            chemin.as_uri(), "_blank", 0, proprietes(Hidden=True, MacroExecutionMode=0)
        )

    def taper(self, document, texte: str) -> None:
        """Un paragraphe tapé à la fin du document, par l'interface."""
        document.CurrentController.ViewCursor.gotoEnd(False)
        cadre = document.CurrentController.Frame
        self.repartiteur.executeDispatch(cadre, ".uno:InsertText", "", 0, proprietes(Text=texte))
        self.repartiteur.executeDispatch(cadre, ".uno:InsertPara", "", 0, ())

    def fermer(self) -> None:
        with contextlib.suppress(Exception):
            self.bureau.terminate()
        self._processus.wait(timeout=60)


def ecrire(office: Office) -> None:
    odt = ICI / "sessions.odt"
    document = office.nouveau()
    office.taper(document, PREMIER)
    document.storeAsURL(odt.as_uri(), proprietes(FilterName="writer8"))
    document.close(True)

    document = office.ouvrir(odt)
    office.taper(document, DEUXIEME)
    document.RecordChanges = True
    office.taper(document, SUIVI)
    document.RecordChanges = False
    commentaire = document.createInstance("com.sun.star.text.textfield.Annotation")
    commentaire.Content = COMMENTAIRE
    commentaire.Author = "Relecture"
    curseur = document.Text.createTextCursor()
    curseur.gotoStart(False)
    document.Text.insertTextContent(curseur, commentaire, False)
    document.store()
    document.close(True)

    document = office.ouvrir(odt)
    office.taper(document, TROISIEME)
    document.store()
    document.storeToURL((ICI / "sessions.docx").as_uri(), proprietes(FilterName="MS Word 2007 XML"))
    document.close(True)


def releve(document) -> dict[str, object]:
    portions = []
    paragraphes = document.Text.createEnumeration()
    while paragraphes.hasMoreElements():
        morceaux = paragraphes.nextElement().createEnumeration()
        while morceaux.hasMoreElements():
            portion = morceaux.nextElement()
            if portion.TextPortionType != "Text" or not portion.getString():
                continue
            portions.append({"longueur": len(portion.getString()), "rsid": portion.Rsid})
    auteurs_modifications = set()
    modifications = 0
    enumeration = document.Redlines.createEnumeration()
    while enumeration.hasMoreElements():
        modification = enumeration.nextElement()
        modifications += 1
        if modification.RedlineAuthor:
            auteurs_modifications.add(modification.RedlineAuthor)
    auteurs_commentaires = set()
    commentaires = 0
    champs = document.TextFields.createEnumeration()
    while champs.hasMoreElements():
        champ = champs.nextElement()
        if champ.supportsService("com.sun.star.text.textfield.Annotation"):
            commentaires += 1
            if champ.Author:
                auteurs_commentaires.add(champ.Author)
    infos = document.DocumentProperties
    return {
        "portions": portions,
        "modifications": modifications,
        "auteurs_modifications": len(auteurs_modifications),
        "commentaires": commentaires,
        "auteurs_commentaires": len(auteurs_commentaires),
        "cycles": infos.EditingCycles,
        "duree_secondes": infos.EditingDuration,
    }


def main() -> None:
    dossier = pathlib.Path(tempfile.mkdtemp())
    office = Office(dossier)
    try:
        ecrire(office)
        oracle = {}
        for nom in ("sessions.odt", "sessions.docx"):
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
