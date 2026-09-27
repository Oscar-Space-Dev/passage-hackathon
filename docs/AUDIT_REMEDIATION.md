# Réponse à l’audit du 27 septembre 2026

## Correctifs de livraison

- Un agent privé ne peut plus être choisi comme coordinateur par un autre compte. Le choix de l’agent vocal sans projet applique la même règle de visibilité.
- Les dépôts de fichiers et d’entrées exigent le droit d’édition. Les relecteurs utilisent les commentaires et avis de relecture ; ils ne peuvent plus rouvrir un travail approuvé par un dépôt.
- L’accès à un travail ne sauvegarde plus de changement pendant un GET. L’obsolescence des sources et les délégations interrompues sont présentées comme un état effectif, sans modifier la révision stockée.
- Sur une installation à inscription publique, le catalogue partagé, l’import global et les paramètres du laboratoire sont réservés à l’administrateur. Le rôle « laboratoire » d’un nouvel inscrit ne donne aucun droit global.
- Les transitions de Marguerite utilisent un verrou par utilisateur, avec registre faible. Les conversations de comptes distincts ne partagent plus le verrou tenu pendant un appel LLM. Une conversation reste sérialisée pour protéger ses plans.
- Les lectures de collections d’un travail utilisent des filtres SQL paramétrés et des index JSON (work_id, project_id, owner_id, user_id, email). Les identifiants de champs sont validés avant construction de la requête.
- Les morceaux de fichiers distants sont lus en une requête bornée, dans l’ordre du manifeste, avec contrôle de présence et empreinte du fichier complet.
- Le polling des missions vocales utilise un thread pour les lectures SQL synchrones.
- L’exécution de scripts MCP locaux Oscar est désactivée sur l’installation publique. Ailleurs, le sous-processus reçoit uniquement un environnement minimal et les paramètres Oscar dédiés.
- `.python-version` fixe Python 3.12, comme l’image de production.

## Vérification

`tests/test_audit_regressions.py` reproduit les accès privés, les écritures par relecteur, les GET sans mutation, la portée du catalogue, l’isolation des verrous et l’utilisation effective d’un index. Les tests existants des travaux, sources liées, fichiers, voix, Marguerite et stockage distant complètent ces contrôles.

Les mesures antérieures de latence restent dans [PERFORMANCE.md](PERFORMANCE.md). Les nouveaux index ne justifient pas à eux seuls une nouvelle promesse de temps de réponse : il faut mesurer les parcours déployés.

## Travail restant

- Découper `workflows.py` et `projects.py` en services sans cycles, avec routes minces.
- Réduire davantage les lectures du détail d’un travail et déplacer l’extraction de fichiers hors du verrou global des projets.
- Remplacer les autres verrous globaux par des transactions ou des contrôles de révision par ressource ; séparer les files de travaux courts et longs.
- Clarifier le rôle de simulation de l’administrateur, typer les routes restantes, durcir les en-têtes après vérification de compatibilité avec Excalidraw et la voix.
- Ajouter la purge des états expirés et examiner le rattachement Google des comptes existants.
- Compléter les contrôles des définitions d’agents, supprimer les constantes de démonstration restantes et produire un verrouillage complet des dépendances.

Aucun découpage structurel complet ni audit de sécurité exhaustif n’est revendiqué par ce lot.
