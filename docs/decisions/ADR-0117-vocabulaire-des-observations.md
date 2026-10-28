# ADR-0117 — Vocabulaire des observations de métadonnées

- **Statut** : Proposé
- **Date** : 2026-10-28
- **Décideur** : assistant, proposition non posée en question pendant T20, à valider pendant la revue de la PR de T20
- **Tâche** : T20
- **Exigences liées** : F-10, F-11, F-12, F-14 ; ADR-0054, ADR-0058, ADR-0084, ADR-0114

## Contexte

ADR-0058 laisse chaque module choisir ses noms d'observation et les documenter dans sa fiche. Ceux de T20 sont les premiers, et ils comptent au-delà du rapport : les règles « moteur » du catalogue nomment l'observation qu'elles testent (ADR-0084). Les règles de T22 (origine IA déclarée, signatures de générateurs) et de T23 (incohérences) liront ces noms ; ils doivent être stables et ne pas pouvoir être usurpés par le fichier. Un nom d'observation est un identifiant (ADR-0054) : 128 caractères au plus, lettres ASCII, chiffres, `.`, `_` exclu, `:`, `/`, `-`.

## Options envisagées

### Option A — Nom tiré de la norme, préfixé par la famille

`exif.<répertoire>.<étiquette>`, `xmp.<préfixe>:<propriété>`, `iptc.<jeu>`, `textepng.<mot-clé>` ; préfixe XMP déduit de l'adresse de l'espace de noms.

- Avantages : lisible dans le rapport ; une règle s'écrit avec le nom que la norme donne au champ ; un fichier ne choisit pas le nom de ses propriétés connues.
- Inconvénients : une table de noms par famille à tenir ; des noms hors norme pour les champs inconnus.

### Option B — Numéros et adresses bruts

`exif.0x8769.0x9003`, `xmp.{http://…}DateCreated`.

- Avantages : aucune table.
- Inconvénients : illisible ; les adresses ne tiennent pas dans un identifiant (`{`, `#`, longueur).

### Option C — Préfixe XMP écrit dans le fichier

- Avantages : aucune table d'espaces.
- Inconvénients : un fichier qui déclare `xmlns:dc="http://autre/"` ferait passer sa propriété pour `dc:creator` ; une règle de T22 sur `Iptc4xmpExt:DigitalSourceType` serait trompée par un préfixe choisi.

## Décision

Option A.

| Famille | Nom | Partie variable |
| --- | --- | --- |
| Toutes | `<famille>.present` | Toujours observé, vrai ou faux (F-14, ADR-0058) |
| Toutes | `<famille>.blocs` | Nombre de blocs, s'il y en a |
| EXIF | `exif.<répertoire>.<étiquette>` | Répertoire `ifd0`, `ifd1`…, `exif`, `gps`, `interop` ; étiquette nommée par EXIF 3.0 ou TIFF 6.0, sinon `0x` et quatre chiffres hexadécimaux |
| EXIF | `exif.ordre` | `II` ou `MM` |
| XMP | `xmp.<préfixe>:<propriété>[.<préfixe>:<champ>…]` | Préfixe usuel d'un espace connu, `ns<k>` sinon ; champs d'une structure à la suite |
| XMP | `xmp.espace.ns<k>`, `xmp.x:xmptk`, `xmp.etendu.blocs` | Adresse d'un espace inconnu ; outil d'écriture ; morceaux étendus |
| IPTC | `iptc.<jeu>` | Nom de l'IIM 4.2, sinon `<enregistrement>:<numéro>` |
| IPTC | `iptc.photoshop.ressources` | Identifiants des ressources Photoshop |
| PNG | `textepng.<mot-clé>[.langue]` | Mot-clé du bloc |
| Toutes | `<nom>.taille`, `<nom>.longueur` | Taille d'une donnée binaire ; longueur d'une valeur coupée (ADR-0118) |

- Préfixes XMP : table `ESPACES` de `modules/_lecture/xmp.py`, préfixe de la spécification qui définit chaque espace (Adobe XMP, IPTC, CIPA, MWG, PLUS, Google, Microsoft, Apple) ; un espace inconnu prend `ns1`, `ns2`… dans l'ordre de première apparition dans le paquet, et son adresse est observée sous `xmp.espace.ns<k>`.
- Partie tirée du fichier (nom local XMP, mot-clé PNG) : tout caractère hors des lettres ASCII, des chiffres et du tiret devient un tiret, le point compris ; le nom entier est coupé à 119 caractères, pour que `<nom>.longueur` reste un identifiant.
- Deux observations peuvent porter le même nom (deux blocs EXIF, deux mots-clés PNG identiques) : leur identifiant et leur localisation les distinguent.

## Raisons

- Option A : les règles s'écrivent avec les noms des normes, que les vérificateurs connaissent, et le rapport se lit (NF-11).
- Option B écartée : illisible, et une adresse d'espace n'est pas un identifiant valide.
- Option C écartée : elle laisse le fichier choisir le nom sous lequel une règle le lira (cas d'abus C-02).
- `present` toujours observé : une absence se teste sur l'observation qui la dit (ADR-0084), jamais sur l'absence d'une observation.
- Noms de la norme EXIF plutôt que ceux d'exiftool : la norme fait foi, exiftool n'est qu'un oracle de test (ADR-0043) ; la fiche signale les écarts connus (`PhotographicSensitivity`, « ISO » chez exiftool).
- Un espace inconnu numéroté plutôt que nommé par le préfixe du fichier : deux paquets peuvent donner le même préfixe à deux adresses ; la numérotation suit le document, donc reste reproductible (NF-06).

## Conséquences

- Les règles de T22 et T23 citent ces noms ; un changement de nom est un changement de version du module et des règles qui le citent.
- Une règle qui teste un espace inconnu teste `xmp.espace.ns<k>` par motif, sans pouvoir rattacher ses propriétés à l'adresse : à revoir si T22 en a besoin.
- Les fiches techniques listent ces noms.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-28 | Création, statut « Proposé » |
