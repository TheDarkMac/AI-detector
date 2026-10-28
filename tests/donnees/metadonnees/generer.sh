#!/bin/sh
# Échantillons de l'oracle exiftool (T20, ADR-0043, ADR-0122) : quatre images de 8 × 8 pixels
# (64 × 64 pour HEIC) créées par ImageMagick, métadonnées écrites par exiftool, puis métadonnées
# relues par exiftool dans exiftool.json. Outils employés pour la version du dépôt :
# ImageMagick 7.1.1-43 (libheif 1.19.8, libwebp 1.5.0) et exiftool 13.25, sous Debian 13.
#
# À lancer depuis ce dossier : sh generer.sh. Les images changent à chaque génération (dates
# écrites par ImageMagick dans les blocs texte PNG) : ne régénérer que pour changer les
# échantillons, et relancer les tests de l'oracle.
set -eu

magick -size 8x8 xc:'#336699' -strip photo.jpg
magick -size 8x8 xc:'#336699' -strip -define png:exclude-chunks=date,time image.png
magick -size 8x8 xc:'#336699' -strip image.webp
magick -size 64x64 xc:'#336699' -strip image.heic

for fichier in photo.jpg image.png image.webp image.heic; do
    exiftool -q -overwrite_original \
        -EXIF:Make=Fabricant -EXIF:Model="Modèle 1" -EXIF:Software="Logiciel 2.1" \
        -EXIF:Artist="Jeanne Exemple" -EXIF:Copyright="© Exemple" \
        -EXIF:DateTimeOriginal="2026:10:28 10:00:00" -EXIF:ExposureTime=0.004 -EXIF:FNumber=2.8 \
        -EXIF:ISO=200 -EXIF:SerialNumber=SN0001 -EXIF:UserComment="Commentaire" \
        -EXIF:GPSLatitude=48.8566 -EXIF:GPSLatitudeRef=N \
        -EXIF:GPSLongitude=2.3522 -EXIF:GPSLongitudeRef=E \
        -XMP-dc:Creator="Jeanne Exemple" -XMP-dc:Title="Titre" -XMP-dc:Subject=un -XMP-dc:Subject=deux \
        -XMP-xmp:CreatorTool="Outil 3" -XMP-photoshop:Credit="Agence" \
        -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
        "$fichier"
done
exiftool -q -overwrite_original -IPTC:Keywords=mot1 -IPTC:Keywords=mot2 \
    -IPTC:By-line="Jeanne Exemple" -IPTC:City=Paris -IPTC:CopyrightNotice="© Exemple" \
    -IPTC:ObjectName=Objet photo.jpg
exiftool -q -overwrite_original -PNG:Author="Jeanne Exemple" -PNG:Comment="Un commentaire" \
    -PNG:Software="Logiciel PNG" image.png

exiftool -j -a -G1 -n -D -struct -x System:all -x File:all -x Composite:all \
    photo.jpg image.png image.webp image.heic > exiftool.json
