# ADR-0186 — Méthode de détection : premier pas de quantification estimé par calibrage

- **Statut** : Accepté
- **Date** : 2026-11-15
- **Décideur** : TheDarkMac, parmi les options proposées par l'assistant
- **Tâche** : T41
- **Exigences liées** : F-31, NF-09, NF-14 ; A-38 ; ADR-0012, ADR-0185

## Contexte

F-31 demande de détecter une double compression JPEG, sans IA embarquée (ADR-0012). Une image décompressée puis réenregistrée sur la même grille de blocs garde, dans l'histogramme de chaque fréquence, un motif périodique dû aux deux quantifications successives.

Sources, lues le 2026-11-15 :

- J. Lukáš, J. Fridrich, « Estimation of Primary Quantization Matrix in Double Compressed JPEG Images », DFRWS 2003 (texte de l'université de Binghamton) : §2, effets de la double quantification sur les histogrammes ; §4.1, « Compatibility Test » : l'image est recadrée (par exemple de 4 pixels) pour désaccorder la grille, recompressée avec chaque table candidate puis avec la table du fichier ; le pas antérieur est celui dont l'histogramme est le plus proche, coefficient par coefficient ; le reste de la table peut être complété par « la table standard la plus proche ». L'article retient surtout un classifieur à réseau de neurones (§4.3).
- Popescu et Farid (« Statistical Tools for Digital Forensics », 2004), cités de mémoire par l'assistant pour la périodicité des histogrammes : non relus pendant T41, donc pas cités comme source dans le code ni dans la fiche.

Essais sur un prototype hors du dépôt : 36 images (trois images sans perte du poste, compressées une fois en qualités 75 et 90, ou deux fois de 50 à 95 puis 75 et 90, par cjpeg de libjpeg-turbo 2.1.5) ; une photographie JPEG (`grace_hopper.jpg` de matplotlib, qualité 80) réenregistrée de 70 à 95, recadrée et redimensionnée ; deux images synthétiques.

## Options envisagées

### Option A — Premier pas estimé par calibrage (recommandée)

- Avantages : interprétable fréquence par fréquence (« la luminance semble quantifiée d'abord au pas 11 ») ; nomme une qualité antérieure de libjpeg quand les pas la donnent ; sur les essais, 22 des 24 doubles compressions à qualité croissante relevées, aucune simple compression au-delà de 2 traces sur 9.
- Inconvénients : demande la luminance recalculée (numpy, ADR-0185) ; ne voit pas la double compression non alignée ; faible quand la seconde qualité est plus basse que la première.

### Option B — Périodicité des histogrammes, sans recalcul des pixels

- Avantages : Python pur possible ; rapide.
- Inconvénients : un score de périodicité, sans pas estimé ; seuil plus fragile face aux images dont l'histogramme s'écarte d'une loi lisse.

### Option C — Les deux, et la double compression non alignée (grille décalée)

- Avantages : couvre le recadrage entre deux compressions.
- Inconvénients : périmètre et PR nettement plus longs ; méthodes supplémentaires à éprouver sans corpus (T100).

## Décision

Option A : le test de compatibilité de Lukáš et Fridrich (§4.1), fréquence par fréquence, sur les 9 premières fréquences de la luminance ; les détails de calcul et les paramètres sont fixés par ADR-0189.

## Raisons

- Retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : sans pas estimé, le constat ne dit pas ce qui a été trouvé ; et le calibrage, possible avec numpy, rend la comparaison plus sûre.
- C écartée : la non alignée reste une limite connue, à reprendre dans une tâche à part si le recueil d'avis (T105) ou le corpus (T100) la demandent.
- Le classifieur de l'article n'est pas repris : ce serait une IA embarquée (ADR-0012).

## Conséquences

- Écarts à l'article, choisis sur les essais : histogrammes signés et écart quadratique plutôt que valeurs absolues et norme L1 ; simulation dans le domaine des coefficients, sans retour aux pixels entre les deux quantifications (l'article fait la même simplification, §4.1.1) ; décision par le rapport des écarts de la simple et de la double quantification (ADR-0189). Ils sont dits dans la fiche `double-compression-jpeg`.
- Limites portées au catalogue : non alignée, mêmes tables, qualités proches, images de synthèse, région du haut seulement.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-15 | Création |
