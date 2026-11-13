# ADR-0143 — Valeurs IPTC de la source numérique : trois valeurs, une direction chacune, comparaison tolérante

- **Statut** : Accepté
- **Date** : 2026-11-13
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T22
- **Exigences liées** : F-11, F-14, F-81 ; ES-20 ; A-33 ; ADR-0055, ADR-0089, ADR-0117, ADR-0142

## Contexte

F-11 nomme deux valeurs IPTC, `trainedAlgorithmicMedia` et `compositeWithTrainedAlgorithmicMedia`. L'analyse critique (A-33) en signalait d'autres, à vérifier sur la liste de l'IPTC en T22.

Vérification faite le 2026-11-13 :

- Vocabulaire « Digital Source Type » des NewsCodes de l'IPTC, `http://cv.iptc.org/newscodes/digitalsourcetype/` : vingt valeurs, dont trois retirées (`minorHumanEdits`, `softwareImage`, `digitalArt`). La plus récente modification d'une valeur date du 2024-10-23.
- IPTC Photo Metadata Standard 2025.1 (révision 1 du 2025-11-26) : la propriété est `Iptc4xmpExt:DigitalSourceType`, de l'espace `http://iptc.org/std/Iptc4xmpExt/2008-02-29/`, de type adresse (URI), au plus une valeur. Aucun jeu IIM ni aucune étiquette EXIF ne la porte.
- Guide de l'IPTC pour les médias générés (2023-05-09) : la valeur s'écrit par son adresse entière, `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia`.

Trois valeurs parlent d'IA générative :

| Code | Nom donné par l'IPTC | Définition (résumée) |
| --- | --- | --- |
| `trainedAlgorithmicMedia` | Created using Generative AI | Créé par un modèle entraîné sur des contenus captés |
| `compositeWithTrainedAlgorithmicMedia` | Edited using Generative AI | Complété, corrigé ou augmenté par un modèle génératif (remplissage, extension d'image) |
| `compositeSynthetic` | Composite including generative AI elements | Montage dont au moins un élément est généré par IA |

Les autres ne le disent pas : `algorithmicMedia` (algorithme pur, sans données d'entraînement), `algorithmicallyEnhanced` (correction algorithmique qui laisse le contenu inchangé), `composite` et `virtualRecording` (avec ou sans IA générative), `computationalCapture` (fusion de vues par une IA non générative), et les valeurs de capture ou de création humaine.

Deux questions restaient : quelle direction pour chacune des trois valeurs (A-33 en demande une par valeur), et quelle graphie reconnaître.

## Options envisagées

### Direction

- **A — Une direction par valeur** : `trainedAlgorithmicMedia` vers l'origine IA ; `compositeWithTrainedAlgorithmicMedia` et `compositeSynthetic` vers la retouche. Avantage : suit la définition de l'IPTC, qui décrit une retouche ou un montage d'un contenu en partie capté. Inconvénient : s'écarte de la lettre de F-11, qui range la deuxième parmi les déclarations d'origine IA.
- **B — Les trois vers l'origine IA** : suit la lettre de F-11. Inconvénient : un montage retouché par IA est présenté comme une génération entière ; la direction « retouche » (ADR-0055) existe pour ce cas.

### Graphie

- **A — Motif tolérant** : adresse en `http` ou `https`, avec ou sans schéma, ou code seul, sans égard à la casse, blancs et barre oblique finale admis. Avantage : un logiciel qui écrit mal la valeur la déclare quand même ; aucune valeur d'un autre sens ne s'écrit ainsi. Inconvénient : un motif plus long à relire qu'une égalité.
- **B — Adresse exacte** (`egal`) : celle de la norme seule. Avantage : strict. Inconvénient : une valeur mal écrite n'est pas reconnue, sans gain de sûreté.

## Décision

Option A dans les deux cas.

| Règle | Valeur | Direction |
| --- | --- | --- |
| R-XMP-001 | `trainedAlgorithmicMedia` | `origine_ia` |
| R-XMP-002 | `compositeWithTrainedAlgorithmicMedia` | `retouche` |
| R-XMP-003 | `compositeSynthetic` | `retouche` |

- Chaque règle teste l'observation `xmp.Iptc4xmpExt:DigitalSourceType` par le motif RE2 `(?i)^\s*(?:(?:https?://)?cv\.iptc\.org/newscodes/digitalsourcetype/)?<code>/?\s*$` ; la valeur est le paramètre `source` de la phrase.
- Le nom de l'observation vient de l'adresse de l'espace de noms, jamais du préfixe écrit dans le fichier (ADR-0117) : un préfixe choisi ne trompe pas la règle.
- Une valeur en liste, contraire à la cardinalité de la norme, satisfait la règle par l'un de ses éléments (ADR-0089).
- Les autres valeurs n'ont pas de règle : elles restent des observations du rapport. Une valeur de capture (`digitalCapture`) n'est pas un indice d'authenticité : elle se forge comme les autres, et la direction « authenticité » demande ce que la déclaration ne donne pas.

## Raisons

- Options A retenues par TheDarkMac, sur recommandation de l'assistant, sans raison supplémentaire : celles présentées avec les options.
- Direction B écartée : elle fait dire au rapport plus que la déclaration.
- Graphie B écartée : elle ne protège de rien, une valeur forgée s'écrivant aussi bien exactement.
- `algorithmicMedia` sans règle : l'IPTC le définit hors de toute donnée d'entraînement, donc hors de l'IA générative que vise F-11 ; `algorithmicallyEnhanced` et `computationalCapture` décrivent des traitements que l'IPTC dit sans changement du contenu, proches d'une transformation banale qu'aucune règle de T22 ne vise.

## Conséquences

- F-11 est réalisée pour le XMP de tous les formats que lit `xmp` ; la même déclaration dans un manifeste C2PA relève de T30.
- A-33 est vérifiée : la liste de l'analyse critique était exacte ; `compositeWithTrainedAlgorithmicMedia` porte aujourd'hui le nom « Edited using Generative AI ».
- Une nouvelle valeur du vocabulaire demandera une règle nouvelle, donc une version du catalogue, sans changer l'outil (F-26).

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-13 | Création |
