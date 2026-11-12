#!/bin/sh
# Métadonnées des échantillons relues par exiftool dans exiftool.json (ADR-0122), appelé par
# generer.sh et generer_pdf.sh. Le PDF chiffré n'y figure pas : les modules n'en lisent pas
# les chaînes (ADR-0126), exiftool les déchiffre.
set -eu

exiftool -j -a -G1 -n -D -struct -x System:all -x File:all -x Composite:all \
    photo.jpg image.png image.webp image.heic document.pdf ghostscript.pdf > exiftool.json
