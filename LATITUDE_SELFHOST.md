# Latitude auto-hébergé avec Passage

Latitude sert ici à observer les exécutions d’agents de Passage. Le connecteur envoie une trace OTLP par exécution terminée, avec identifiants techniques, état, durée, fournisseur et modèle lorsqu’ils sont connus. Il n’envoie pas les messages, résultats, fichiers, noms de personnes ou secrets. L’export est désactivé par défaut et son échec n’annule pas une tâche Passage réussie.

La version actuelle de Latitude est un produit d’observabilité agentique sous licence MIT. Son déploiement sur un seul hôte comprend `web`, `api`, `ingest`, `workers`, `workflows` et des services Postgres, ClickHouse, Redis, Temporal et SeaweedFS. Seules les fonctions de traces sont nécessaires à ce raccordement ; Latitude peut les lancer sans clé de fournisseur de modèle.

## Installer Latitude sur un hôte Docker

Suivre la [procédure officielle Single-host](https://docs.latitude.so/deployment/single-host) et récupérer ensemble `docker-stack.yml`, `.env.example`, `docker/init-db.sh`, `docker/seaweedfs/init.sh` et `docker/clickhouse/storage.xml` depuis la même révision Latitude. Copier `.env.example` en `.env.production`, définir les secrets de chiffrement et d’authentification, changer les mots de passe d’infrastructure et configurer l’acheminement des emails pour le premier compte. Fixer `LAT_IMAGE_TAG` à une version publiée. Garder `.env.production` et les volumes de données hors du dépôt Passage.

Depuis ce répertoire de déploiement, la commande officielle de démarrage est :

```sh
docker compose --env-file .env.production -f docker-stack.yml up -d
```

Vérifier la santé des conteneurs avec `docker compose --env-file .env.production -f docker-stack.yml ps`, puis ouvrir l’interface Latitude, créer le compte et un projet, et générer une clé API pour l’ingestion. Sur un hôte local conforme au Compose officiel, `web` écoute sur `3000`, `api` sur `3001` et `ingest` sur `3002`. Pour un hôte distant, utiliser HTTPS et la véritable URL du service `ingest`.

## Relier Passage

Dans **Passage → Connexions → Latitude · auto-hébergé**, renseigner :

- **Export des traces** : Activé.
- **URL ingest** : `http://127.0.0.1:3002` si Latitude tourne sur le même hôte ; ne pas ajouter `/v1/traces`.
- **Slug du projet Latitude** : le slug exact du projet créé dans Latitude.
- **Clé API Latitude** : la clé de cet espace, conservée chiffrée si l’option de conservation est cochée.

Passage envoie à `URL/v1/traces` avec les en-têtes `Authorization: Bearer` et `X-Latitude-Project`. Le service doit renvoyer HTTP `202`. L’état de livraison de chaque exécution est enregistré comme `latitude_export: sent` ou `failed` ; une erreur est aussi journalisée localement. Le formulaire « Configuré » indique la présence des paramètres, pas une trace effectivement reçue. Une vérification de bout en bout exige une exécution réelle de Passage et sa présence dans Latitude.

Sur cette machine de développement Windows, la commande `docker` n’est actuellement pas disponible. La liaison Passage est prête mais aucune instance Latitude ni clé d’ingestion n’a pu être testée ici.

Sources : [déploiement officiel](https://docs.latitude.so/deployment/single-host), [contrat OTLP officiel](https://docs.latitude.so/telemetry/otel-exporter).
