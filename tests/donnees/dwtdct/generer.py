"""Échantillons du module dwtdct (T32, ADR-0203) : filigranes posés par la bibliothèque de
référence elle-même, comme chaque générateur la pose.

Source : une image de synthèse de 256 x 256 pixels (fractale « plasma » d'ImageMagick, graine
fixe, bruit gaussien), le minimum de la bibliothèque. Fichiers écrits :

- ``aucun.png`` : la source, sans filigrane ;
- ``sd1.png`` : message « StableDiffusionV1 », image en entiers BVR, comme ``put_watermark`` de
  ``scripts/txt2img.py`` (CompVis) ; enregistrée en PNG par Pillow ;
- ``sdxl.png`` : message de SDXL, image en flottants de 0 à 255 en BVR, comme ``WatermarkEmbedder``
  de ``sgm/inference/helpers.py`` (Stability-AI), tronquée en entiers par ``astype(np.uint8)`` ;
- ``sdxl_rvb.png`` : message de SDXL, image en flottants passée en RVB, comme diffusers du
  2023-07-06 au 2024-04-26, arrondie par ``round()`` ;
- ``flux.jpg`` : message de FLUX.1, image en flottants BVR, tronquée par ``.byte()``, enregistrée
  par Pillow en JPEG de qualité 95 sans sous-échantillonnage, comme ``save_image`` de
  ``src/flux/util.py`` (Black Forest Labs) ;
- ``sdxl_420.jpg`` : ``sdxl.png`` réenregistrée par Pillow en JPEG de qualité 95, chrominance en
  4:2:0 ;
- ``sd1_progressif.jpg`` : ``sd1.png`` compressée par cjpeg en progressif, chrominance en 4:2:2,
  un redémarrage toutes les deux MCU ;
- ``rvb.jpg`` : ``flux.jpg`` décompressée puis compressée par cjpeg en RVB (segment Adobe,
  transformation 0) ;
- ``attendus.toml`` : bits concordants que lit le décodeur de la bibliothèque (``cv2.imread``,
  lecture sur huit bits, seuil d'un demi), pour la fiche.

Outils pour la version du dépôt : ImageMagick 7.1.1-43, libjpeg-turbo 2.1.5 (cjpeg, djpeg), et
un environnement Python séparé de celui du projet, qui n'a ni OpenCV ni PyWavelets :
invisible-watermark 0.2.0 installée sans ses dépendances (elle déclare torch), avec
opencv-python-headless 5.0.0, PyWavelets 1.8.0, numpy 2.5.5 et Pillow 13.0.0. Le module
``maxDct`` est chargé seul, comme le fait ``scripts/demo/detect.py`` de Stability-AI.

À lancer depuis ce dossier avec l'interpréteur de cet environnement : ``python -I generer.py``.
Ne régénérer que pour changer les échantillons, puis mettre à jour les valeurs attendues de
``tests/test_dwtdct.py``.
"""

# mypy: ignore-errors
# (OpenCV, PyWavelets et Pillow ne sont pas dans l'environnement du projet.)

import importlib.util
import pathlib
import shutil
import site
import subprocess
import tempfile

import cv2
import numpy as np
from PIL import Image

_CHEMIN = next(
    pathlib.Path(dossier) / "imwatermark" / "maxDct.py"
    for dossier in site.getsitepackages()
    if (pathlib.Path(dossier) / "imwatermark" / "maxDct.py").exists()
)
_SPEC = importlib.util.spec_from_file_location("maxDct", _CHEMIN)
assert _SPEC is not None
assert _SPEC.loader is not None
maxDct = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(maxDct)

SD1 = [int(b) for b in np.unpackbits(np.frombuffer(b"StableDiffusionV1", dtype=np.uint8))]
SDXL = [int(b) for b in bin(0b101100111110110010010000011110111011000110011110)[2:]]
FLUX = [int(b) for b in bin(0b001010101111111010000111100111001111010100101110)[2:]]


def outil(nom: str) -> str:
    chemin = shutil.which(nom)
    if chemin is None:
        raise SystemExit(f"{nom} introuvable")
    return chemin


def poser(image: np.ndarray, bits: list[int]) -> np.ndarray:
    return maxDct.EmbedMaxDct(bits, wmLen=len(bits)).encode(image)


def lire_reference(chemin: str, bits: list[int], inversee: bool = False) -> int:
    bvr = cv2.imread(chemin)
    if inversee:
        bvr = np.ascontiguousarray(bvr[:, :, ::-1])
    lus = maxDct.EmbedMaxDct([], wmLen=len(bits)).decode(bvr)
    return int(sum(int(a) == b for a, b in zip(lus, bits, strict=True)))


def main() -> None:
    with tempfile.TemporaryDirectory() as dossier:
        source = f"{dossier}/source.ppm"
        subprocess.run(
            [
                outil("magick"),
                "-seed",
                "32",
                "-size",
                "256x256",
                "plasma:fractal",
                "-attenuate",
                "0.3",
                "+noise",
                "Gaussian",
                f"ppm:{source}",
            ],
            check=True,
        )
        rvb = np.array(Image.open(source).convert("RGB"))
        Image.fromarray(rvb).save("aucun.png")
        # Stable Diffusion 1 : entiers, BVR.
        sortie = poser(cv2.cvtColor(rvb, cv2.COLOR_RGB2BGR), SD1)
        Image.fromarray(sortie[:, :, ::-1]).save("sd1.png")
        flottants = rvb.astype(np.float32)
        # SDXL (generative-models) : flottants, BVR, tronqués.
        sortie = poser(np.ascontiguousarray(flottants[:, :, ::-1]), SDXL)[:, :, ::-1]
        Image.fromarray((255.0 * np.clip(sortie / 255, 0, 1)).astype(np.uint8)).save("sdxl.png")
        # SDXL (diffusers, 2023-07-06 au 2024-04-26) : flottants passés en RVB, arrondis.
        sortie = np.clip(2 * (poser(np.ascontiguousarray(flottants), SDXL) / 255 - 0.5), -1, 1)
        image = (np.clip(sortie / 2 + 0.5, 0, 1) * 255).round().astype(np.uint8)
        Image.fromarray(image).save("sdxl_rvb.png")
        # FLUX.1 : flottants, BVR, tronqués par .byte(), JPEG de qualité 95 en 4:4:4.
        sortie = poser(np.ascontiguousarray(flottants[:, :, ::-1]), FLUX)[:, :, ::-1]
        x = 2 * np.clip(sortie / 255, 0, 1) - 1
        Image.fromarray((127.5 * (x + 1.0)).astype(np.uint8)).save(
            "flux.jpg", quality=95, subsampling=0
        )
        Image.open("sdxl.png").save("sdxl_420.jpg", quality=95, subsampling=2)
        Image.open("sd1.png").save(f"{dossier}/sd1.ppm")
        with open("sd1_progressif.jpg", "wb") as fichier:
            subprocess.run(
                [
                    outil("cjpeg"),
                    "-quality",
                    "95",
                    "-sample",
                    "2x1",
                    "-restart",
                    "2B",
                    "-progressive",
                    f"{dossier}/sd1.ppm",
                ],
                stdout=fichier,
                check=True,
            )
        Image.open("flux.jpg").save(f"{dossier}/flux.ppm")
        with open("rvb.jpg", "wb") as fichier:
            subprocess.run(
                [outil("cjpeg"), "-quality", "95", "-rgb", f"{dossier}/flux.ppm"],
                stdout=fichier,
                check=True,
            )
    lignes = [
        "# Bits concordants que lit le décodeur d'invisible-watermark 0.2.0 (generer.py).",
        "",
    ]
    for nom, bits, inversee in [
        ("aucun.png", SD1, False),
        ("sd1.png", SD1, False),
        ("sdxl.png", SDXL, False),
        ("sdxl_rvb.png", SDXL, True),
        ("flux.jpg", FLUX, False),
        ("sdxl_420.jpg", SDXL, False),
        ("sd1_progressif.jpg", SD1, False),
    ]:
        lignes.append(f'"{nom}" = {lire_reference(nom, bits, inversee)}')
    pathlib.Path("attendus.toml").write_text("\n".join(lignes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
