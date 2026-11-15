#!/bin/sh
# Échantillons de la double compression JPEG (T41, ADR-0186) : une image de synthèse de
# 384 × 256 pixels (fractale « plasma » d'ImageMagick, graine fixe, légèrement floutée), compressée
# une fois ou deux fois par cjpeg, décompressée entre les deux par djpeg ; versions progressive et
# à intervalles de redémarrage écrites sans perte par jpegtran, qui garde les coefficients.
# Outils employés pour la version du dépôt : ImageMagick 7.1.1-43 et libjpeg-turbo 2.1.5
# (cjpeg, djpeg, jpegtran), sous Debian 13.
#
# À lancer depuis ce dossier : sh generer.sh. La fractale peut changer d'une version
# d'ImageMagick à l'autre : ne régénérer que pour changer les échantillons, et relancer
# tests/test_double_compression.py.
set -eu

source=$(mktemp)
trap 'rm -f "$source"' EXIT
magick -seed 41 -size 384x256 plasma:fractal -blur 0x0.6 ppm:"$source"

cjpeg -quality 75 "$source" > simple_75.jpg
cjpeg -quality 90 "$source" > simple_90.jpg
cjpeg -quality 50 "$source" | djpeg | cjpeg -quality 75 > double_50_75.jpg
cjpeg -quality 60 "$source" | djpeg | cjpeg -quality 90 > double_60_90.jpg
jpegtran -progressive double_60_90.jpg > double_60_90_progressif.jpg
jpegtran -restart 5B double_60_90.jpg > double_60_90_redemarrage.jpg
cjpeg -quality 60 -grayscale "$source" | djpeg | cjpeg -quality 90 -grayscale \
    | jpegtran -progressive > double_60_90_gris_progressif.jpg
cjpeg -quality 75 -sample 1x1 "$source" | jpegtran -progressive -restart 3B > simple_75_444_progressif.jpg
