# Voight-Kampff

Outil d'analyse de fichiers qui relève les preuves et les indices de génération ou de retouche par IA, **sans embarquer aucun modèle d'IA**.

L'outil ne délivre pas de verdict certain : il distingue ce qui se vérifie (signature, métadonnée, filigrane documenté) de ce qui se mesure seulement (anomalies du signal), et explique chaque constat.

Le projet est en cours de construction. Sur la branche `detector`, la commande `vk FICHIER...` identifie le format réel de chaque fichier par son contenu, signale une extension discordante, un fichier polyglotte ou des données après la fin logique, et vérifie que le fichier n'a pas changé pendant l'analyse. Chaque fichier est lu par un processus restreint : sans réseau ni accès au disque sous Linux et macOS, avec des restrictions réduites sous Windows, que la commande affiche ; un fichier de plus de 1 Gio est refusé. Aucune technique d'analyse n'est encore livrée. Le paquet `voight-kampff-forensics` est réservé sur PyPI par une pré-version sans analyse (`0.1.0.dev0`) ; il installe les commandes `voight-kampff` et `vk`.

Le développement se fait sur la branche `detector`. Voir `CONTRIBUTING.md` et `docs/` sur cette branche.

## Licence

Le dépôt, code et documentation compris, est publié sous licence [Apache-2.0](LICENSE).
