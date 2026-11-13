#!/bin/sh
# Échantillons audio et vidéo de l'oracle exiftool (T21, complément audio et vidéo, ADR-0135) :
#
# - son.wav : PCM, liste INFO et bloc bext ;
# - son.mp3 : MP3 (LAME), ID3v2.4 en tête et ID3v1 en fin ;
# - son.aac : AAC en trames ADTS, ID3v2 en tête ;
# - son.m4a : AAC dans ISOBMFF, liste ilst de moov/udta/meta ;
# - son.flac : FLAC, bloc VORBIS_COMMENT ;
# - son.ogg, son.opus : Vorbis et Opus dans Ogg, paquets de commentaires ;
# - video.mp4 : MPEG-4 Part 2, clés QuickTime (moov/meta, gestionnaire mdta), XMP ajouté par
#   exiftool ;
# - video.mov : QuickTime, textes ©xxx de moov/udta, XMP ajouté par exiftool ;
# - video.webm : VP8, éléments Info et Tags.
#
# Les balises sont écrites par ffmpeg, le XMP par exiftool ; relire.sh relit ensuite tous les
# échantillons. Outils employés pour la version du dépôt : ffmpeg 7.1.5 et exiftool
# 13.25, sous Debian 13.
#
# À lancer depuis ce dossier : sh generer_media.sh. Les fichiers changent avec les versions des
# bibliothèques, que ffmpeg écrit dans ses balises : ne régénérer que pour changer les
# échantillons.
set -eu

ff() {
    ffmpeg -hide_banner -loglevel error -y "$@"
}

ff -f lavfi -i anullsrc=r=8000:cl=mono -t 0.2 -c:a pcm_s16le \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" \
    -metadata comment="Commentaire" -metadata date="2026-11-13" \
    -write_bext 1 -metadata description="Prise de son" -metadata originator="Enregistreur" \
    -metadata originator_reference="FRXYZ0123456789" -metadata origination_date="2026-11-13" \
    -metadata origination_time="10:00:00" -metadata coding_history="A=PCM,F=8000,W=16,M=mono" \
    son.wav

ff -f lavfi -i anullsrc=r=8000:cl=mono -t 0.2 -c:a libmp3lame -id3v2_version 4 -write_id3v1 1 \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" \
    -metadata comment="Commentaire" -metadata date="2026-11-13" son.mp3

ff -f lavfi -i anullsrc=r=8000:cl=mono -t 0.2 -c:a aac -f adts -write_id3v2 1 \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" son.aac

ff -f lavfi -i anullsrc=r=8000:cl=mono -t 0.2 -c:a aac \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" \
    -metadata comment="Commentaire" -metadata date="2026-11-13" \
    -metadata creation_time="2026-11-13T10:00:00Z" son.m4a

ff -f lavfi -i anullsrc=r=8000:cl=mono -t 0.2 -c:a flac \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" \
    -metadata comment="Commentaire" -metadata date="2026-11-13" son.flac

ff -f lavfi -i anullsrc=r=8000:cl=mono -t 0.2 -c:a libvorbis \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" son.ogg

ff -f lavfi -i anullsrc=r=48000:cl=mono -t 0.2 -c:a libopus \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" son.opus

ff -f lavfi -i color=c=black:s=16x16:r=5:d=0.4 -c:v mpeg4 -movflags use_metadata_tags \
    -metadata title="Titre accentué" -metadata com.apple.quicktime.software="Logiciel 1.0" \
    -metadata creation_time="2026-11-13T10:00:00Z" video.mp4

ff -f lavfi -i color=c=black:s=16x16:r=5:d=0.4 -c:v mpeg4 \
    -metadata title="Titre accentué" -metadata artist="Jeanne Exemple" \
    -metadata creation_time="2026-11-13T10:00:00Z" video.mov

ff -f lavfi -i color=c=black:s=16x16:r=5:d=0.4 -c:v libvpx \
    -metadata title="Titre accentué" -metadata comment="Commentaire" \
    -metadata creation_time="2026-11-13T10:00:00Z" video.webm

for fichier in video.mp4 video.mov; do
    exiftool -q -overwrite_original \
        -XMP-dc:Creator="Jeanne Exemple" -XMP-xmp:CreatorTool="Outil 3" \
        -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
        "$fichier"
done

sh relire.sh
