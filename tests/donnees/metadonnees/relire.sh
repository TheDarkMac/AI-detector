#!/bin/sh
# Métadonnées des échantillons relues par exiftool dans exiftool.json (ADR-0122), appelé par
# generer.sh, generer_pdf.sh, generer_media.sh et generer_bureautique.sh. Le PDF chiffré n'y
# figure pas : les modules n'en lisent pas les chaînes (ADR-0126), exiftool les déchiffre. Le groupe de famille 4
# (-G1:4) numérote les balises répétées (« Copy1 ») : sans lui, la sortie JSON n'en garde
# qu'une (ADR-0135). Les entrées d'une archive ZIP (groupe ZIP) relèvent de la structure : les
# modules ne les observent pas (ADR-0141).
set -eu

exiftool -j -a -G1:4 -n -D -struct -x System:all -x File:all -x Composite:all -x ZIP:all \
    photo.jpg image.png image.webp image.heic document.pdf ghostscript.pdf \
    son.wav son.mp3 son.aac son.m4a son.flac son.ogg son.opus video.mp4 video.mov video.webm \
    document.docx document.odt \
    > exiftool.json
