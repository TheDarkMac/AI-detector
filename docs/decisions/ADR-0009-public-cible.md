# ADR-0009 — Public cible prioritaire : journalistes et vérificateurs de faits

- **Statut** : Accepté
- **Date** : 2026-10-26
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T02
- **Exigences liées** : §4 du cahier ; F-06, NF-11 ; constats A-15, A-28

## Contexte

Le §4 du cahier liste cinq profils sans en désigner un prioritaire. Le choix conditionne le périmètre (ADR-0012), le vocabulaire du rapport (NF-11) et les mentions. L'analyse a relevé que le grand public apporte surtout des fichiers dépouillés par les réseaux sociaux (A-15) et que le profil enseignant cumule le risque le plus grave et le module le moins fiable (A-28).

## Options envisagées

### Option A — Journalistes et vérificateurs de faits

- Avantages : ont souvent accès aux originaux ou peuvent les demander ; lisent un rapport argumenté ; besoin central de provenance (C2PA, métadonnées), cohérent avec ADR-0008.
- Inconvénients : public restreint ; attentes élevées sur la vidéo, peu analysable sans IA.

### Option B — RH, assurance, banque

- Avantages : cas très concret (« ce PDF a-t-il été modifié après émission ? ») et facile à évaluer.
- Inconvénients : met la retouche PDF en tête, l'origine IA devient secondaire ; contredit l'accent choisi par ADR-0008.

### Option C — Grand public

- Avantages : le plus large.
- Inconvénients : cas le moins analysable ; l'outil répondrait le plus souvent « rien de concluant » (A-15), avec un fort risque de mauvaise lecture.

### Option D — Juristes, enquêteurs

- Avantages : besoin fort d'éléments vérifiables.
- Inconvénients : exigences de chaîne de conservation et d'horodatage (NF-17) coûteuses dès la V1.

## Décision

Le public prioritaire est celui des **journalistes et vérificateurs de faits**. Les juristes et enquêteurs sont servis en second, par le même rapport vérifiable. Le grand public et les enseignants ne sont pas visés en V1.

## Raisons

- Option A retenue : c'est le profil qui tire le plus d'un outil sans IA (accès aux originaux, lecture argumentée) et dont le besoin correspond à l'objectif principal.
- Option B écartée comme cible prioritaire : le module PDF reste dans la V1 (ADR-0012), donc ce profil est servi en partie.
- Option C écartée : A-15.
- Option D écartée comme cible prioritaire : le coût de NF-17 complet ; ce profil profite du rapport sans qu'on lui doive la chaîne de conservation en V1.
- Profil enseignant écarté tant que le module texte n'a pas de taux d'erreur publiés (A-28, ADR-0013).

## Conséquences

- Le rapport vise un lecteur averti mais non spécialiste ; le vocabulaire renvoie au glossaire (NF-11).
- F-06 (indices de transfert, recommandation d'obtenir l'original) reste essentielle : c'est le geste que ce public peut faire.
- Les mentions (T103) déconseillent l'usage de l'outil pour fonder seul une accusation.
- Hypothèse à confirmer par le recueil d'avis sur prototype (ADR-0026).

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création |
