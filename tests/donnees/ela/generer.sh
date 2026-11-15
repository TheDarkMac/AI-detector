#!/bin/sh
# Échantillons de l'ELA (T42, ADR-0199) : une image de synthèse de 256 × 192 pixels (fractale
# « plasma » d'ImageMagick, graine fixe, bruit gaussien), compressée une fois à 60, décompressée,
# puis un carré de 64 × 64 pixels de l'image sans perte collé au milieu, et le tout enregistré à 92
# (collage_60_92.jpg) ; la même image compressée une seule fois à 92 (simple_92.jpg) ; le collage
# en progressif, coefficients gardés par jpegtran (collage_60_92_progressif.jpg).
# Outils employés pour la version du dépôt : ImageMagick 7.1.1-43 et libjpeg-turbo 2.1.5
# (cjpeg, djpeg, jpegtran), sous Debian 13.
#
# À lancer depuis ce dossier : sh generer.sh. La fractale peut changer d'une version
# d'ImageMagick à l'autre : ne régénérer que pour changer les échantillons, puis mettre à jour
# les empreintes attendues de tests/test_ela.py.
set -eu

dossier=$(mktemp -d)
trap 'rm -rf "$dossier"' EXIT
magick -seed 42 -size 256x192 plasma:fractal -attenuate 0.4 +noise Gaussian ppm:"$dossier/source.ppm"
cjpeg -quality 60 "$dossier/source.ppm" | djpeg > "$dossier/q60.ppm"
magick "$dossier/q60.ppm" \( "$dossier/source.ppm" -crop 64x64+96+64 \) -geometry +96+64 \
    -composite ppm:"$dossier/collage.ppm"
cjpeg -quality 92 "$dossier/collage.ppm" > collage_60_92.jpg
cjpeg -quality 92 "$dossier/source.ppm" > simple_92.jpg
jpegtran -progressive collage_60_92.jpg > collage_60_92_progressif.jpg
