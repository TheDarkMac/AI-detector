#!/bin/sh
# Échantillons DOCX et ODT de l'oracle exiftool (T21, complément bureautique, ADR-0141) :
#
# - document.odt : meta.xml (titre, sujet, mots-clés, auteurs, dates, cycles et durée
#   d'édition, statistiques, générateur, propriétés utilisateur typées) ;
# - document.docx : mêmes métadonnées, en propriétés principales, étendues et personnalisées
#   (docProps/core.xml, app.xml, custom.xml).
#
# LibreOffice écrit les deux depuis un document OpenDocument à plat (.fodt) ; relire.sh relit
# ensuite tous les échantillons. Outils employés pour la version du dépôt : LibreOffice
# 25.2.3.2 et exiftool 13.25, sous Debian 13.
#
# À lancer depuis ce dossier : sh generer_bureautique.sh. Les fichiers changent à chaque
# génération (dates des entrées ZIP, version écrite par LibreOffice) : ne régénérer que pour
# changer les échantillons.
set -eu

temporaire=$(mktemp -d)
trap 'rm -rf "$temporaire"' EXIT

cat > "$temporaire/document.fodt" <<'FIN'
<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
 <office:meta>
  <dc:title>Titre accentué</dc:title>
  <dc:subject>Sujet</dc:subject>
  <dc:description>Commentaire</dc:description>
  <meta:keyword>mot1</meta:keyword>
  <meta:keyword>mot2</meta:keyword>
  <meta:initial-creator>Jeanne Exemple</meta:initial-creator>
  <dc:creator>Paul Relecteur</dc:creator>
  <meta:creation-date>2026-11-01T10:20:30</meta:creation-date>
  <dc:date>2026-11-02T11:21:31</dc:date>
  <meta:editing-cycles>7</meta:editing-cycles>
  <meta:editing-duration>PT1H2M3S</meta:editing-duration>
  <dc:language>fr-FR</dc:language>
  <meta:user-defined meta:name="Outil">Générateur 3</meta:user-defined>
  <meta:user-defined meta:name="Note" meta:value-type="float">4.5</meta:user-defined>
  <meta:user-defined meta:name="Relu" meta:value-type="boolean">true</meta:user-defined>
 </office:meta>
 <office:body><office:text><text:p>Bonjour</text:p></office:text></office:body>
</office:document>
FIN

for format in odt docx; do
    libreoffice --headless --convert-to "$format" --outdir "$temporaire" \
        "$temporaire/document.fodt" > /dev/null
    cp "$temporaire/document.$format" "document.$format"
done

sh relire.sh
