#!/bin/sh
# Échantillons PDF de l'oracle exiftool (T21, ADR-0122, ADR-0124) :
#
# - document.pdf : texte converti par LibreOffice (table de références croisées classique) ;
# - ghostscript.pdf : page PostScript convertie par Ghostscript (flux de références croisées,
#   flux d'objets) ;
# - chiffre.pdf : même page, chiffrée par Ghostscript (RC4 128 bits, mot de passe utilisateur
#   vide), pour les tests du chiffrement.
#
# exiftool écrit ensuite les métadonnées des deux premiers, par une mise à jour incrémentale,
# puis relire.sh relit tous les échantillons. Outils employés pour la version du dépôt :
# LibreOffice 25.2.3.2, Ghostscript 10.05.1 et exiftool 13.25, sous Debian 13.
#
# À lancer depuis ce dossier : sh generer_pdf.sh. Les PDF changent à chaque génération (dates
# et identifiants écrits par chaque outil) : ne régénérer que pour changer les échantillons.
set -eu

temporaire=$(mktemp -d)
trap 'rm -rf "$temporaire"' EXIT

printf 'Bonjour\n' > "$temporaire/document.txt"
libreoffice --headless --convert-to pdf --outdir "$temporaire" "$temporaire/document.txt" > /dev/null
cp "$temporaire/document.pdf" document.pdf

printf '%%!PS\n/Helvetica findfont 12 scalefont setfont 72 720 moveto (Bonjour) show showpage\n' \
    > "$temporaire/page.ps"
gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pdfwrite -sOutputFile=ghostscript.pdf "$temporaire/page.ps"
gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pdfwrite -sOwnerPassword=proprietaire \
    -dEncryptionR=3 -dKeyLength=128 -sOutputFile=chiffre.pdf "$temporaire/page.ps"

for fichier in document.pdf ghostscript.pdf; do
    exiftool -q -overwrite_original \
        -PDF:Author="Jeanne Exemple" -PDF:Title="Titre accentué" -PDF:Subject="Sujet" \
        -PDF:Keywords="mot1, mot2" -PDF:Creator="Outil 3" \
        -XMP-dc:Creator="Jeanne Exemple" -XMP-dc:Title="Titre" \
        -XMP-pdf:Keywords="mot1, mot2" -XMP-xmp:CreatorTool="Outil 3" \
        -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
        "$fichier"
done

sh relire.sh
