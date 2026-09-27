# Performance en déploiement

## Incident du 27 septembre 2026

Une lecture initiale de `/api/state` a duré 89,72 s avant une erreur HTTP 502.
Le regroupement des lectures de configuration a réduit cette mesure à 4,05 s,
encore insuffisant pour une interface utilisable. Ces mesures proviennent de
requêtes authentifiées vers Render, depuis le poste de développement.

Causes identifiées dans le code : connexions distantes recréées à chaque lecture,
lectures sérialisées derrière un verrou d'écriture, collections chargées en série,
lectures répétées de configuration et de connexion personnelle ChatGPT.

## Correction

- Transports de lecture distants réutilisés par thread, sans partage simultané
  d'une connexion entre threads. Fermeture après erreur ou inactivité de 30 s.
- Lectures indépendantes du verrou d'écriture ; les écritures restent validées
  dans la base distante. Aucun cache de base locale n'est ajouté.
- Collections de l'accueil et de la liste des projets regroupées en une requête.
  Leur instantané est limité à l'appel et n'est jamais conservé entre utilisateurs.
- Session et compte courant lus ensemble à chaque requête ; ni droits ni sessions
  ne sont mis en cache. Une révocation reste immédiatement applicable.
- Fenêtre de nouveau projet et navigation affichées avant les appels réseau.

## Contrôles reproductibles

`python -m pytest tests/test_read_performance.py tests/test_remote_store.py tests/test_configuration_snapshot.py tests/test_teams.py tests/test_codex_protocol_errors.py -q`

Le budget vérifié est de quatre lectures SQL maximum pour l'accueil administrateur,
authentification incluse, et deux pour la liste des projets. Les tests vérifient
aussi la fraîcheur des droits, les données relues avec le vrai pilote libSQL,
l'absence d'attente derrière le verrou d'écriture et la confidentialité des équipes.

L'image Docker vérifie le lancement réel de Codex App Server sous l'utilisateur
non privilégié de production avant de pouvoir être publiée. Un arrêt sans message
du processus renvoie une erreur contrôlée au lieu d'une exception IndexError.

## Mesures publiques après publication de `906644d`

Le 27 septembre à 22 h 19 (Paris), appels HTTP authentifiés depuis le poste de
développement, sans proxy, sur Render Free et Turso. Trois appels successifs :

| Requête | Première mesure | Deuxième | Troisième |
| --- | ---: | ---: | ---: |
| `/api/state` | 1,796 s | 0,610 s | 0,609 s |
| `/api/projects` | 0,281 s | 0,219 s | 0,391 s |
| `/api/brains/chatgpt/status` | 0,297 s | 0,218 s | 0,204 s |

Trois appels simultanés ont répondu en 0,968 s (état), 0,812 s (projets) et
0,812 s (santé). Ce petit échantillon n'est pas un test de charge ni une garantie
de temps maximal ; le réveil d'une instance Render inactive n'est pas mesuré.

Le démarrage réel du parcours ChatGPT par code a répondu HTTP 200 en 1,657 s,
avec les champs `loginId`, `type`, `userCode`, `verificationUrl` attendus. Le code
n'a pas été imprimé ni conservé dans le dépôt. Ce contrôle vérifie le début de
l'autorisation ; une approbation OpenAI et une réponse réelle de l'agent restent
nécessaires pour valider une connexion utilisateur de bout en bout.
