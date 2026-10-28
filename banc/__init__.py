"""Banc d'évaluation de Voight-Kampff (T17) : outil du dépôt, hors du paquet publié (ADR-0099).

Il analyse chaque fichier d'un corpus par l'interface publique (``voight_kampff.analyser``),
sans réseau (ES-11, ADR-0100), et mesure par technique et par catégorie du corpus les taux de
faux positifs, de faux négatifs et la part de fichiers non analysables (§8 du cahier), le taux
de faux positifs de chaque règle et le taux par fichier (ADR-0018, ADR-0101, ADR-0104).

``banc.matrice`` tient la matrice exigence → méthode de vérification → résultat (ADR-0024,
ADR-0102).
"""
