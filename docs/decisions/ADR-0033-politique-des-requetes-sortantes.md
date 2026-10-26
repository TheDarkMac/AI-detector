# ADR-0033 — Politique des requêtes sortantes : aucune URL du fichier résolue sans confirmation

- **Statut** : Proposé
- **Date** : 2026-10-26
- **Décideur** : proposition de l'assistant, non posée en question pendant T03, soumise à TheDarkMac dans la PR de T03
- **Tâche** : T03
- **Exigences liées** : F-21, NF-04, NF-16 ; constats A-36, A-42 ; ADR-0010, ADR-0017 ; menaces M-14 à M-16, M-18

## Contexte

ADR-0010 rend toute requête sortante optionnelle et désactivée par défaut, mais ne dit pas ce qu'elle peut faire une fois activée. Le modèle de menace montre que la plus dangereuse n'est pas celle qui part vers un service connu : c'est celle dont l'**adresse est écrite dans le fichier**. Un manifeste C2PA peut être distant, récupéré par une URL (A-36) ; un DOCX peut référencer un modèle ou une image distante ; un XMP peut contenir des liens. L'auteur du fichier, s'il cherche la source (A3), choisit cette URL, peut la rendre propre à chaque exemplaire, et apprend, si elle est résolue, l'adresse, l'heure et l'exemplaire analysé (M-14). Par ailleurs, A-42 proposait d'étendre NF-16 au contenu, pas seulement aux données identifiantes.

Ce point n'a pas été posé en question : il a été identifié en rédigeant le modèle, après les deux lots de questions.

## Options envisagées

### Option A — Aucune URL du fichier résolue automatiquement ; manifeste distant sur confirmation par fichier

- Avantages : ferme la balise de pistage ; garde la vérification d'un manifeste distant possible quand l'utilisateur en accepte le risque, en connaissance de l'hôte.
- Inconvénients : une étape de plus pour l'utilisateur qui a activé les vérifications en ligne.

### Option B — Manifeste distant récupéré automatiquement quand les vérifications en ligne sont activées

- Avantages : plus simple à l'usage.
- Inconvénients : activer « vérifications en ligne » pour la révocation suffit à déclencher une balise posée par l'adversaire ; l'utilisateur n'a pas consenti à contacter cet hôte-là.

### Option C — Manifestes distants jamais récupérés

- Avantages : le plus sûr.
- Inconvénients : un manifeste distant reste toujours « non vérifiable », même quand l'utilisateur accepte le risque.

## Décision

1. **Aucune URL issue du fichier n'est résolue automatiquement**, quels que soient les réglages.
2. **Manifeste C2PA distant** (RS-02) : seule exception ; récupéré sur confirmation explicite, pour ce fichier, après affichage de l'hôte ; sans redirection vers un autre hôte, sans cookie ; soumis à la même vérification cryptographique qu'un manifeste intégré. Sans confirmation, l'état est « non vérifiable », avec la raison.
3. **Révocation** (RS-01) : listes de révocation (CRL) préférées à OCSP, car elles ne révèlent pas quel certificat est vérifié.
4. **Toute requête** : TLS vérifié ; réponse vérifiée (signature OCSP, signature du manifeste) avant usage ; réponse et date inscrites au rapport (ADR-0023).
5. **NF-16 étendue au contenu** pour le projet : « Toute requête qui quitte le poste est inventoriée, réduite au minimum, et n'emporte jamais le fichier, son contenu ni ses données identifiantes, sauf service tiers activé explicitement par l'utilisateur, avec son consentement pour ce fichier. »

## Raisons

- Option A proposée : elle ferme la menace la plus grave du §6.3 du modèle (M-14, cote haute) sans supprimer une vérification utile.
- Option B écartée : le consentement donné pour la révocation ne vaut pas consentement à contacter un hôte choisi par l'adversaire.
- Option C écartée : plus restrictive que nécessaire, dès lors que l'utilisateur voit l'hôte avant d'accepter.
- Extension de NF-16 au contenu : aucune requête de la V1 n'emporte de contenu, la contrainte ne coûte rien maintenant ; elle protège les futures requêtes du type F-72 (A-42).

## Conséquences

- T30 réalise les points 2 à 4 ; T21 et T52 garantissent que les liens et références distantes des DOCX, ODT et PDF ne sont jamais suivis.
- L'inventaire des requêtes sortantes du [modèle de menace](../modele-de-menace/modele-de-menace.md) (§6.3) applique cette politique.
- La reformulation de NF-16 complète celle d'ADR-0017 au registre des arbitrages, à faire valider par l'auteur du cahier.
- Si TheDarkMac ne valide pas cette proposition, un nouvel ADR fixera l'option retenue et le modèle de menace sera révisé.

## Historique

| Date | Modification |
| --- | --- |
| 2026-10-26 | Création, statut « Proposé » |
