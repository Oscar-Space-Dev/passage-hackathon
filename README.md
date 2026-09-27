# Passage

**Une équipe d’agents pour conduire un projet de recherche, du premier article au livrable vérifié.**

Passage aide les doctorants à organiser leurs travaux, rédiger, préparer des protocoles, analyser des données et cadrer une simulation ou un logiciel scientifique. Marguerite, l’agent permanent, discute du besoin, propose des actions concrètes dans Passage, puis les exécute après validation. Le scientifique conserve la décision et la validation des résultats.

Projet réalisé pour le **X-IA Hackathon — Rise of Agents X**. L’éditeur d’agents s’inspire de la doctrine Super Skill Creator V4 du projet antérieur **Oscar-AI**, déclaré comme préexistant. Passage possède son propre code, ses contrats et ses contrôles.

## Essayer en trois minutes

1. Ouvrez l’URL de l’aperçu Render une fois publiée, ou lancez l’application localement ci-dessous.
2. Créez un compte **Doctorant/chercheur**, **Laboratoire** ou **Entreprise**. Chaque compte garde ses propres projets et conversations.
3. Créez un projet, ouvrez **Travaux de recherche**, choisissez une tâche R1–R3 et parcourez ses étapes, questions et contrôles humains.
4. Ouvrez **Marguerite** pour décrire un objectif. Elle propose un plan ; rien n’est exécuté avant **Valider et exécuter**.
5. Pour une réponse d’agent réelle, reliez votre compte ChatGPT dans **Connexions**. Pour le dialogue vocal, configurez aussi Gradium.

Le déploiement Render exige une base Turso externe pour conserver comptes et projets lors des redémarrages. N’y chargez pas de données confidentielles pendant le hackathon.

## Ce qui fonctionne

| Parcours | Résultat dans Passage | Contrôle humain |
| --- | --- | --- |
| Recherche documentaire | Notices de thèses avec source et statut ; recherche et comparaison | Vérifier le manuscrit et les affirmations |
| Travaux doctoraux | 32 tâches R1–R3, documents versionnés, preuves, registres, exports | Valider les étapes, protocoles et livrables |
| Agents | Cerveau ChatGPT via Codex par défaut ; harnais versionné, spécialités et outils | Approuver le plan et relire les propositions |
| Marguerite | Conversation personnelle ; création de projets, tâches, schémas et spécialistes après validation | Accepter ou refuser chaque plan |
| Voix | Transcription et synthèse Gradium en dialogue continu | Autoriser le micro et vérifier la transcription |
| Schémas | Dessin local basé sur Excalidraw ; brouillon de protocole ou `.mthds` | Relire et publier la méthode séparément |
| Dust / Pipelex | Comptes MCP OAuth, catalogue d’outils accordés et appels contrôlés | Accorder les outils et approuver les écritures |

**Limites visibles :** Passage prépare des expériences, simulations et programmes, mais ne réalise pas une manipulation physique ni ne valide un résultat scientifique. Un export `.mthds` n’est pas une méthode Pipelex publiée. Les API de moteur Dust et Pipelex demandent des clés distinctes de leurs connexions MCP OAuth. La clé API OpenAI est facultative et facturée séparément de l’abonnement ChatGPT. Jinkō est en cours d’intégration via son SDK.

## Lancer localement

Prérequis : Python 3.11 ou plus, Node.js et le CLI officiel Codex si vous souhaitez utiliser votre compte ChatGPT. La consultation des écrans et des données initiales reste possible sans fournisseur LLM.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Ouvrez `http://127.0.0.1:8088`. Au premier démarrage local, le premier compte devient administrateur. Les comptes suivants choisissent leur profil. Le corpus de départ contient des notices publiques, et les programmes de démonstration sont fictifs. Aucun modèle local n’est utilisé par défaut.

Pour vérifier les contrats principaux :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_guide.py tests/test_workflows.py -q
```

## Connexions et architecture

```text
Utilisateur ── Passage ── Marguerite (plan puis approbation)
                    ├── ChatGPT via Codex (cerveau personnel)
                    ├── Gradium (transcription et voix)
                    ├── Agents à harnais versionné ── tâches R1–R3
                    ├── Dust / Pipelex via MCP OAuth (outils accordés)
                    ├── Excalidraw local → protocole / brouillon .mthds
                    └── SQLite locale ou Turso distant (comptes, projets, preuves, historique)
```

Une exécution garde le modèle déclaré, la révision de l’agent, les données autorisées, les traces et les erreurs. Les projets et conversations sont liés au compte. Un agent personnel créé par Marguerite reste privé à son propriétaire. Les outils externes ne sont disponibles qu’après connexion et autorisation ; une écriture demande une validation supplémentaire.

Les paramètres optionnels sont documentés dans [.env.example](.env.example). Ne mettez jamais `.env`, clés, bases SQLite ou données de recherche privées dans le dépôt.

## Aperçu Render

[render.yaml](render.yaml) décrit un service Docker **Free** avec `/api/health` comme sonde et `PASSAGE_PUBLIC_SIGNUP=1`. Configurez `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` et une clé Fernet stable `PASSAGE_ENCRYPTION_KEY` dans les variables privées Render. Le serveur refuse de démarrer sans base distante. Comptes, projets, notices, conversations, connexions chiffrées et fichiers de travail sont conservés dans Turso ; le disque Render ne sert que de cache. Chaque évaluateur crée son propre compte et relie ses propres fournisseurs. Les identifiants de l’installation locale ne sont pas transférés. La session locale du CLI Codex reste sur le disque éphémère : une reconnexion ChatGPT peut être nécessaire après une mise en veille.

Pour produire la clé Fernet, lancez `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` et copiez le résultat uniquement dans les variables privées Render. Gardez cette valeur : en la changeant, les connexions OAuth déjà enregistrées ne seront plus déchiffrables. Les notices de thèses stockent des métadonnées et des liens vers la source ; le projet ne réhéberge pas tous les manuscrits.

La connexion Google est optionnelle : elle n’apparaît que si `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` sont configurés avec l’URL de retour `/api/auth/google/callback`. L’inscription par email et mot de passe fonctionne sans Google. L’aperçu ne dispose pas encore de récupération de mot de passe ni d’invitations d’équipe.

## Documents utiles

- [Spécification fonctionnelle](SPEC_FONCTIONNELLE.md)
- [Parcours des 32 tâches R1–R3](PARCOURS_R1_R3.md)
- [Usages des personas R1–R5](USAGES_PASSAGE_R1_R5.md)
- [Scénario vidéo et narration](DEMO.md)
- [Latitude auto-hébergé](LATITUDE_SELFHOST.md)

**Licences et provenance :** l’éditeur de dessin embarque Excalidraw sous licence MIT, conservée dans [LICENSE-EXCALIDRAW.txt](passage/static/diagram/LICENSE-EXCALIDRAW.txt). Les notices initiales renvoient à leurs sources publiques. Oscar-AI reste un projet antérieur distinct.
