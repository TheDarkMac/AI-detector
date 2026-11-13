# ERR-0009 — Codecs UTF-16 et Shift_JIS chargés après les restrictions : module `exif` en erreur

- **Date de constat** : 2026-11-12
- **Tâche en cours** : T21
- **Document ou élément touché** : `src/voight_kampff/modules/exif/__init__.py` (module `exif` 0.1.0, T20) ; fiche `metadonnees-exif` ; application d'ADR-0079
- **Nature** : exécution

## Ce qui était écrit ou fait

Le module `exif` décode les étiquettes `XP…` en UTF-16LE, et le commentaire `UserComment` en UTF-16 s'il est marqué `UNICODE`, en Shift_JIS s'il est marqué `JIS` (fiche `metadonnees-exif`, ADR-0118). Python charge un codec à sa première utilisation, en important un module de `encodings`, sauf pour UTF-8, Latin-1 et ASCII. Dans le processus de travail, ce premier usage a lieu après les restrictions, qui interdisent toute lecture du disque (ADR-0079) : l'import échoue, `exif` lève une exception, et tous ses résultats sur la partie sont écartés (ADR-0060). Vérifié par `vk` sur `detector` : un JPEG qui porte `XPAuthor`, ou un commentaire `JIS`, a son analyse EXIF « non menée » pour erreur du module.

## Ce qui est juste

Un module charge à son import tout ce dont il aura besoin (ADR-0079), codecs compris : `codecs.lookup` place le codec dans le cache de l'interpréteur, et le décodage ne lit plus rien sur le disque.

## Comment l'erreur a été trouvée

Le premier test de T21 dans un vrai processus de travail, sur le PDF de Ghostscript de l'oracle, a mis `infopdf` en erreur : le titre du document, écrit par exiftool en UTF-16BE, ne se décodait pas. La recherche des autres décodages des modules a trouvé ceux d'`exif`.

## Cause

Les tests de T20 exécutent les modules dans le processus des tests, sans restrictions, où les codecs se chargent sans peine. Le seul test des modules de T20 dans un vrai processus de travail lit un JPEG sans étiquette `XP…` ni commentaire marqué. ADR-0079 prévoyait que la règle soit « vérifiée par leurs tests » : aucun test ne la vérifiait pour un import implicite comme celui d'un codec.

## Correction appliquée

- `exif` 0.1.1 : `codecs.lookup` des codecs UTF-16LE, UTF-16BE et Shift_JIS à l'import du module ; fiche mise à jour.
- Lecteur PDF de T21 : `codecs.lookup` d'UTF-16BE à l'import (`modules/_lecture/pdf.py`).
- Test `test_vrai_processus_decode_les_textes_utf16_et_jis` (`tests/test_orchestration.py`) : un JPEG à étiquette `XPAuthor` et commentaire `JIS`, un JPEG à commentaire `UNICODE`, un PDF à titre UTF-16BE, analysés dans un vrai processus de travail ; il échoue sans la correction, vérifié.
- Mêmes changements dans la branche `tache/T21-extraction-pdf`.

## Prévention

- Le test ci-dessus garde chaque codec employé par les modules ; les autres décodages des modules emploient UTF-8, Latin-1 ou ASCII, que l'interpréteur décode sans rien charger.
- ADR-0079 renvoie à cet erratum : la règle « rien n'est importé à la demande » vaut aussi pour les imports implicites (codecs). Chaque nouveau module de métadonnées passe par un test dans un vrai processus de travail sur un échantillon qui emploie ses décodages.
