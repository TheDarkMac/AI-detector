"""Noms des étiquettes EXIF et TIFF, par répertoire (ADR-0117).

Noms de la norme EXIF 3.0 (CIPA DC-008-2023) et de TIFF 6.0 ; s'y ajoutent
quelques étiquettes d'usage courant hors norme, nommées comme par leur auteur (Microsoft,
Adobe). Une étiquette absente de ces tables est nommée par son numéro, ``0x`` et quatre
chiffres hexadécimaux.
"""

from voight_kampff.rapport.modele import CategorieIdentifiante

__all__ = ["IDENTIFIANTES", "NOMS", "TEXTES_UTF16", "nom", "table"]

_TIFF = {
    0x000B: "ProcessingSoftware",
    0x00FE: "NewSubfileType",
    0x00FF: "SubfileType",
    0x0100: "ImageWidth",
    0x0101: "ImageLength",
    0x0102: "BitsPerSample",
    0x0103: "Compression",
    0x0106: "PhotometricInterpretation",
    0x0107: "Thresholding",
    0x0108: "CellWidth",
    0x0109: "CellLength",
    0x010A: "FillOrder",
    0x010D: "DocumentName",
    0x010E: "ImageDescription",
    0x010F: "Make",
    0x0110: "Model",
    0x0111: "StripOffsets",
    0x0112: "Orientation",
    0x0115: "SamplesPerPixel",
    0x0116: "RowsPerStrip",
    0x0117: "StripByteCounts",
    0x0118: "MinSampleValue",
    0x0119: "MaxSampleValue",
    0x011A: "XResolution",
    0x011B: "YResolution",
    0x011C: "PlanarConfiguration",
    0x011D: "PageName",
    0x011E: "XPosition",
    0x011F: "YPosition",
    0x0122: "GrayResponseUnit",
    0x0123: "GrayResponseCurve",
    0x0128: "ResolutionUnit",
    0x0129: "PageNumber",
    0x012D: "TransferFunction",
    0x0131: "Software",
    0x0132: "DateTime",
    0x013B: "Artist",
    0x013C: "HostComputer",
    0x013D: "Predictor",
    0x013E: "WhitePoint",
    0x013F: "PrimaryChromaticities",
    0x0140: "ColorMap",
    0x0141: "HalftoneHints",
    0x0142: "TileWidth",
    0x0143: "TileLength",
    0x0144: "TileOffsets",
    0x0145: "TileByteCounts",
    0x014A: "SubIFDs",
    0x0152: "ExtraSamples",
    0x0153: "SampleFormat",
    0x0201: "JPEGInterchangeFormat",
    0x0202: "JPEGInterchangeFormatLength",
    0x0211: "YCbCrCoefficients",
    0x0212: "YCbCrSubSampling",
    0x0213: "YCbCrPositioning",
    0x0214: "ReferenceBlackWhite",
    0x02BC: "XMLPacket",
    0x4746: "Rating",
    0x4749: "RatingPercent",
    0x8298: "Copyright",
    0x83BB: "IPTC-NAA",
    0x8649: "PhotoshopSettings",
    0x8773: "InterColorProfile",
    0x882A: "TimeZoneOffset",
    0x9C9B: "XPTitle",
    0x9C9C: "XPComment",
    0x9C9D: "XPAuthor",
    0x9C9E: "XPKeywords",
    0x9C9F: "XPSubject",
    0xC4A5: "PrintImageMatching",
    0xC612: "DNGVersion",
    0xC614: "UniqueCameraModel",
    0xEA1C: "Padding",
}

_EXIF = {
    0x829A: "ExposureTime",
    0x829D: "FNumber",
    0x8822: "ExposureProgram",
    0x8824: "SpectralSensitivity",
    0x8827: "PhotographicSensitivity",
    0x8828: "OECF",
    0x8830: "SensitivityType",
    0x8831: "StandardOutputSensitivity",
    0x8832: "RecommendedExposureIndex",
    0x8833: "ISOSpeed",
    0x8834: "ISOSpeedLatitudeyyy",
    0x8835: "ISOSpeedLatitudezzz",
    0x9000: "ExifVersion",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x9010: "OffsetTime",
    0x9011: "OffsetTimeOriginal",
    0x9012: "OffsetTimeDigitized",
    0x9101: "ComponentsConfiguration",
    0x9102: "CompressedBitsPerPixel",
    0x9201: "ShutterSpeedValue",
    0x9202: "ApertureValue",
    0x9203: "BrightnessValue",
    0x9204: "ExposureBiasValue",
    0x9205: "MaxApertureValue",
    0x9206: "SubjectDistance",
    0x9207: "MeteringMode",
    0x9208: "LightSource",
    0x9209: "Flash",
    0x920A: "FocalLength",
    0x9214: "SubjectArea",
    0x927C: "MakerNote",
    0x9286: "UserComment",
    0x9290: "SubSecTime",
    0x9291: "SubSecTimeOriginal",
    0x9292: "SubSecTimeDigitized",
    0x9400: "Temperature",
    0x9401: "Humidity",
    0x9402: "Pressure",
    0x9403: "WaterDepth",
    0x9404: "Acceleration",
    0x9405: "CameraElevationAngle",
    0xA000: "FlashpixVersion",
    0xA001: "ColorSpace",
    0xA002: "PixelXDimension",
    0xA003: "PixelYDimension",
    0xA004: "RelatedSoundFile",
    0xA20B: "FlashEnergy",
    0xA20C: "SpatialFrequencyResponse",
    0xA20E: "FocalPlaneXResolution",
    0xA20F: "FocalPlaneYResolution",
    0xA210: "FocalPlaneResolutionUnit",
    0xA214: "SubjectLocation",
    0xA215: "ExposureIndex",
    0xA217: "SensingMethod",
    0xA300: "FileSource",
    0xA301: "SceneType",
    0xA302: "CFAPattern",
    0xA401: "CustomRendered",
    0xA402: "ExposureMode",
    0xA403: "WhiteBalance",
    0xA404: "DigitalZoomRatio",
    0xA405: "FocalLengthIn35mmFilm",
    0xA406: "SceneCaptureType",
    0xA407: "GainControl",
    0xA408: "Contrast",
    0xA409: "Saturation",
    0xA40A: "Sharpness",
    0xA40B: "DeviceSettingDescription",
    0xA40C: "SubjectDistanceRange",
    0xA420: "ImageUniqueID",
    0xA430: "CameraOwnerName",
    0xA431: "BodySerialNumber",
    0xA432: "LensSpecification",
    0xA433: "LensMake",
    0xA434: "LensModel",
    0xA435: "LensSerialNumber",
    0xA436: "ImageTitle",
    0xA437: "Photographer",
    0xA438: "ImageEditor",
    0xA439: "CameraFirmware",
    0xA43A: "RAWDevelopingSoftware",
    0xA43B: "ImageEditingSoftware",
    0xA43C: "MetadataEditingSoftware",
    0xA460: "CompositeImage",
    0xA461: "SourceImageNumberOfCompositeImage",
    0xA462: "SourceExposureTimesOfCompositeImage",
    0xA500: "Gamma",
    0xEA1C: "Padding",
    0xEA1D: "OffsetSchema",
}

_GPS = {
    0x0000: "GPSVersionID",
    0x0001: "GPSLatitudeRef",
    0x0002: "GPSLatitude",
    0x0003: "GPSLongitudeRef",
    0x0004: "GPSLongitude",
    0x0005: "GPSAltitudeRef",
    0x0006: "GPSAltitude",
    0x0007: "GPSTimeStamp",
    0x0008: "GPSSatellites",
    0x0009: "GPSStatus",
    0x000A: "GPSMeasureMode",
    0x000B: "GPSDOP",
    0x000C: "GPSSpeedRef",
    0x000D: "GPSSpeed",
    0x000E: "GPSTrackRef",
    0x000F: "GPSTrack",
    0x0010: "GPSImgDirectionRef",
    0x0011: "GPSImgDirection",
    0x0012: "GPSMapDatum",
    0x0013: "GPSDestLatitudeRef",
    0x0014: "GPSDestLatitude",
    0x0015: "GPSDestLongitudeRef",
    0x0016: "GPSDestLongitude",
    0x0017: "GPSDestBearingRef",
    0x0018: "GPSDestBearing",
    0x0019: "GPSDestDistanceRef",
    0x001A: "GPSDestDistance",
    0x001B: "GPSProcessingMethod",
    0x001C: "GPSAreaInformation",
    0x001D: "GPSDateStamp",
    0x001E: "GPSDifferential",
    0x001F: "GPSHPositioningError",
}

_INTEROP = {
    0x0001: "InteroperabilityIndex",
    0x0002: "InteroperabilityVersion",
    0x1000: "RelatedImageFileFormat",
    0x1001: "RelatedImageWidth",
    0x1002: "RelatedImageLength",
}

NOMS = {"exif": _EXIF, "gps": _GPS, "interop": _INTEROP}
"""Tables par sous-répertoire ; IFD0, IFD1 et suivants emploient celle de TIFF."""

TEXTES_UTF16 = frozenset({0x9C9B, 0x9C9C, 0x9C9D, 0x9C9E, 0x9C9F})
"""Étiquettes de Microsoft : octets d'un texte UTF-16 petit-boutiste."""

_NOMINATIVES = {
    ("tiff", 0x013B),  # Artist
    ("tiff", 0x013C),  # HostComputer
    ("tiff", 0x8298),  # Copyright
    ("tiff", 0x9C9D),  # XPAuthor
    ("exif", 0xA430),  # CameraOwnerName
    ("exif", 0xA437),  # Photographer
    ("exif", 0xA438),  # ImageEditor
}
_SERIES = {("exif", 0xA420), ("exif", 0xA431), ("exif", 0xA435)}
_FICHIERS = {("tiff", 0x010D), ("exif", 0xA004)}

IDENTIFIANTES: dict[tuple[str, int], CategorieIdentifiante] = {
    **dict.fromkeys(_NOMINATIVES, CategorieIdentifiante.METADONNEE_NOMINATIVE),
    **dict.fromkeys(_SERIES, CategorieIdentifiante.NUMERO_DE_SERIE),
    **dict.fromkeys(_FICHIERS, CategorieIdentifiante.NOM_DE_FICHIER),
}
"""Étiquettes identifiantes hors GPS, par table ; tout le répertoire GPS l'est (ADR-0119)."""


def table(repertoire: str) -> str:
    """Table d'un répertoire : ``tiff`` pour IFD0, IFD1 et suivants."""
    return repertoire if repertoire in NOMS else "tiff"


def nom(repertoire: str, etiquette: int) -> str:
    """Nom d'une étiquette dans son répertoire, ou son numéro."""
    noms = NOMS.get(repertoire, _TIFF)
    return noms.get(etiquette, f"0x{etiquette:04x}")
