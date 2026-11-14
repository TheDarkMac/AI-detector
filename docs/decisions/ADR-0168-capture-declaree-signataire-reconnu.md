# ADR-0168 — Capture déclarée sous un signataire reconnu : preuve, direction authenticité

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Décideur** : TheDarkMac, sur recommandation de l'assistant, en réponse à une question posée pendant T30
- **Tâche** : T30
- **Exigences liées** : F-23, F-80, F-81 ; ES-20 ; ADR-0021, ADR-0143

## Contexte

ADR-0143 n'a pas fait de règle pour une capture déclarée dans le XMP : elle se forge comme toute déclaration. Dans un manifeste C2PA valide signé par un signataire de la liste de confiance, la même déclaration est signée par un produit reconnu, et le contenu n'a pas changé depuis.

## Options envisagées

### Option A — Preuve, authenticité

- Avantages : symétrique de l'origine IA ; énonce ce que la vérification établit (ADR-0021).
- Inconvénients : un lecteur pressé peut y lire une preuve de la scène.

### Option B — Information neutre

- Avantages : aucune direction tirée d'une déclaration.
- Inconvénients : traite autrement deux déclarations signées de même force.

## Décision

Option A : règle R-C2PA-003 pour `digitalCapture` et `computationalCapture`, sous un signataire reconnu seulement. Sous un certificat hors liste ou une signature invalide, aucune règle de capture (ADR-0143).

## Raisons

- A retenue par TheDarkMac, sur recommandation de l'assistant.
- B écartée : asymétrie sans fondement entre deux déclarations signées.
- `computationalCapture` comprise : l'IPTC la définit comme une capture par un appareil dont les vues sont fusionnées par une IA non générative (ADR-0143).

## Conséquences

- La phrase et les limites de R-C2PA-003 disent qu'un appareil compromis ou la photographie d'un écran donnent aussi une capture signée.

## Historique

| Date | Modification |
| --- | --- |
| 2026-11-14 | Création, statut « Accepté » (choix de TheDarkMac) |
