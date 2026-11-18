# ADR-0237 — Constats des caractères invisibles ou substitués : douze informations neutres ; module `caracteres` et versions de T80

- **Statut** : Accepté
- **Date** : 2026-11-17
- **Décideur** : TheDarkMac, par les options retenues pour les invisibles et les homoglyphes (ADR-0234, ADR-0235) ; règles et versions précisées par l'assistant
- **Tâche** : T80
- **Exigences liées** : F-24, F-73, F-80, F-81 ; A-43 ; ADR-0021, ADR-0152, ADR-0158, ADR-0232 à ADR-0236

## Contexte

Comme `actifsbureau` (ADR-0231), le module n'émet aucun constat : des règles « moteur » du catalogue lisent ses observations. A-43 demande une direction par cas. Les deux options retenues (ADR-0234, ADR-0235) tiennent chaque relevé pour une information neutre : l'outil voit le caractère, pas l'intention.

## Décision

Une règle par famille, direction « rien de particulier », fondement « vérification déterministe », seuil par définition, calibrage « manuel » :

| Règle | Condition | Phrase |
| --- | --- | --- |
| R-CARACTERES-001 | `caracteres.controles.inhabituels` ≥ 1 | contrôles et leurs codes |
| R-CARACTERES-002 | `caracteres.bidirectionnels.inhabituels` ≥ 1 | bidirectionnels hors d'un texte de droite à gauche ; l'ordre affiché peut différer de l'ordre écrit |
| R-CARACTERES-003 | `caracteres.etiquettes.inhabituels` ≥ 1 | étiquettes hors d'un drapeau ; texte invisible cité au rapport |
| R-CARACTERES-004 | `caracteres.selecteurs.inhabituels` ≥ 1 | sélecteurs hors de leur emploi ordinaire |
| R-CARACTERES-005 | `caracteres.sans_chasse.inhabituels` ≥ 1 | caractères sans chasse hors de leur emploi ordinaire |
| R-CARACTERES-006 | `caracteres.espaces.inhabituels` ≥ 1 | espaces ou séparateurs inhabituels |
| R-CARACTERES-007 | `caracteres.prive.inhabituels` ≥ 1 | caractères à usage privé |
| R-CARACTERES-008 | `caracteres.homoglyphes` ≥ 1 | mots mêlés, lettres substituées et leurs écritures |
| R-CARACTERES-009 | `caracteres.compatibilite.inhabituels` ≥ 1 | lettres de compatibilité, par nature |
| R-CARACTERES-010 | `caracteres.c2pa.completes` ≥ 1 | manifeste(s) C2PA, version de l'enveloppe, longueur ; ni signature ni empreinte vérifiées |
| R-CARACTERES-011 | `caracteres.c2pa.corrompues` ≥ 1 | enveloppe(s) corrompue(s) |
| R-CARACTERES-012 | `caracteres.c2pa` ≥ 2 | plusieurs enveloppes, une seule prévue |

- Le texte des étiquettes n'est pas un paramètre de phrase : il reste à son observation, masquée par défaut (ADR-0234).
- Le module lit un contenu qui peut désigner une source (le texte des étiquettes) : il ne rejoint pas les modules sans métadonnées du résumé (ADR-0158) ; une analyse non menée de `caracteres` rend le contrôle avant publication incomplet.

| Élément | Version |
| --- | --- |
| Module `caracteres` | 0.1.0, format `texte`, exigences F-73, F-24, F-25, ES-12, direction `rien_de_particulier`, aucune bibliothèque |
| Tables Unicode | 18.0.0 (`_unicode.py`) |
| Catalogue | 0.16.0 (`Y` : règles ajoutées, marquage recherché, ADR-0152), format 3 inchangé ; description resserrée pour tenir dans 1 024 caractères |
| Schémas du rapport et des messages | 0.11.0 : champ `saisie` de l'identification, nom absent d'un texte collé (ADR-0233) ; la configuration du travail peut annoncer un texte collé |
| Paquet | Inchangé (ADR-0050) |

## Raisons

- Une règle par famille : chaque phrase dit ce que la famille peut faire (cacher un texte, changer l'ordre d'affichage, couper un mot) et ses emplois ordinaires sont dans ses limites.
- Information neutre partout : options A d'ADR-0234 et d'ADR-0235, retenues par TheDarkMac ; aucune mesure ne fonde un indice (A-43).
- Schéma en version mineure (0.10.0 → 0.11.0) : un champ requis s'ajoute à l'identification, un rapport 0.10.0 ne se relit pas comme 0.11.0.

## Conséquences

- La part de textes ordinaires qui déclenchent chaque règle (copier-coller depuis le web, documents bilingues, mises en page) se mesurera sur le corpus de référence (T100).
- `tests/test_caracteres.py` vérifie chaque règle sur un texte construit, et qu'un texte ordinaire (insécables, émoji composé) n'en déclenche aucune.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-17 | Création, avec les options d'ADR-0234 et d'ADR-0235 retenues au début de T80 |
| 2026-11-18 | Renvoi : R-CARACTERES-013 (texte masqué) et `caracteres` 0.2.0, catalogue 0.17.0 ([ADR-0242](ADR-0242-texte-masque-et-versions-du-complement-de-t80.md)) (complément de T80) |
