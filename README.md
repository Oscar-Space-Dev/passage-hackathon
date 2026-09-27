# Passage — POC recherche et entrepreneuriat

**Projet préexistant déclaré : Oscar-AI**, développé par Sébastien avant le hackathon. Passage est une application autonome réalisée pendant le hackathon X-IA. Son éditeur s'inspire des concepts d'Oscar (cerveau, harnais, révisions) ; aucun code de l'éditeur Oscar n'a été copié. La connexion optionnelle appelle son serveur MCP existant pour lire les programmes et déposer une note après décision humaine.

Passage aide le doctorant à piloter son projet de recherche avec une équipe d'agents. Le coordinateur peut désormais proposer et conserver des livrables de rédaction, de protocole expérimental, de simulation et de logiciel scientifique. Le laboratoire et l'entreprise disposent aussi d'un parcours de valorisation des thèses.

## Marguerite · agent permanent de Passage

Le bouton **Marguerite**, en bas à droite de chaque écran après connexion, ouvre une discussion personnelle persistante. Elle reçoit le projet sélectionné, les travaux existants, les agents prêts et leurs spécialités, les sources pertinentes et les outils MCP accordés. Décrivez votre travail, votre objectif et pourquoi vous utilisez Passage : Marguerite répond avec le compte ChatGPT connecté, conserve une courte mémoire consultable et propose un plan ordonné. Si une action proposée est impossible, elle répare le plan ou demande la donnée manquante avant de le présenter.

Dans le panneau Marguerite, **Conversation vocale** ouvre un dialogue continu : Gradium transcrit la parole et lit les réponses, tandis que le compte ChatGPT connecté produit les réponses et les plans. Les tours sont conservés dans l'historique de Marguerite. Si elle propose un plan, la conversation vocale se termine après sa réponse et le panneau présente les actions à valider ou refuser. La connexion ChatGPT et une clé/voix Gradium configurées dans **Connexions** sont nécessaires.

Le plan affiche ses paramètres et les interventions humaines avant **Valider et exécuter ces actions** ou **Refuser**. Marguerite peut créer un projet, modifier son objectif, son équipe ou ses sources, créer et déléguer une tâche R1–R3, consigner une note avec provenance « marguerite », préparer un schéma de processus vide dans une tâche puis faire formaliser un dessin existant en protocole ou brouillon Pipelex, produire un brouillon de recherche, demander un rapport à un spécialiste, lancer le modèle thermique borné, appeler un outil MCP connecté et accordé ou lancer une mission de coordination. Les actions utilisent les fonctions réelles de Passage ; une approbation ne peut pas être rejouée. Elle suit les missions, délégations et formalisations jusqu'à leur état réel, puis indique les résultats à relire ou les contrôles encore attendus. Une écriture MCP reçoit encore sa propre carte de validation ; les attestations scientifiques, les essais physiques et l'acceptation finale restent du ressort des personnes responsables. Elle peut discuter sans projet sélectionné, mais nécessite la connexion du compte ChatGPT dans **Connexions**.

## Schémas de protocoles et Latitude

Dans une tâche R1–R3, ouvrez **Schémas de protocoles et de processus** pour dessiner des étapes (rectangles), décisions (losanges) et transitions (flèches reliées). L'éditeur Excalidraw est chargé depuis les fichiers locaux de Passage. **Sauvegarder** crée une version avec empreinte SHA-256 ; le dessin peut être exporté en `.excalidraw`. Le propriétaire peut demander à un agent direct actif de formaliser la version sauvegardée en protocole Markdown ou en brouillon `.mthds`. L'agent reçoit le graphe extrait du dessin, et son document conserve la version et l'empreinte d'origine. Il faut relire et déposer explicitement le document ; le brouillon Pipelex n'est ni publié ni exécuté automatiquement.

Pour reconstruire l'éditeur après une modification de son code : `cd diagram-ui`, `npm ci`, puis `npm run build`. Les dépendances sont verrouillées dans `diagram-ui/package-lock.json`. La licence MIT d'Excalidraw est conservée avec les assets livrés.

La connexion Latitude auto-hébergée se règle dans **Connexions**. Voir [LATITUDE_SELFHOST.md](LATITUDE_SELFHOST.md) pour le déploiement et la vérification. Passage exporte seulement des métadonnées d'exécution ; l'option est désactivée tant que l'instance, le projet et la clé ne sont pas configurés.

## Travaux R1–R3 et agents de l'équipe

Les [parcours fonctionnels R1–R3](PARCOURS_R1_R3.md) détaillent les **32 tâches et leurs 128 étapes** : action de la personne, aide possible de l'agent, pièce à vérifier, outil Passage correspondant et actes qui restent hors de l'application. La fiche de chaque tâche affiche ces indications et permet de demander l'aide d'un agent sur une étape précise. Le coordinateur du projet peut aussi cibler une étape lorsqu'il ouvre ou reprend une tâche. Pour terminer une étape, le propriétaire ou un éditeur consigne ce qu'il a vérifié et peut lier une pièce ; auteur, date et historique sont conservés. Une pièce documentaire modifiée rend sa vérification périmée. La clôture exige quatre vérifications humaines actuelles.

Dans **Travaux de recherche**, choisissez un projet puis une tâche du catalogue des 32 travaux R1–R3. Chaque tâche expose les pièces attendues, quatre étapes, trois questions propres au métier, le livrable, le rôle de l'agent et la décision humaine. Vous pouvez renseigner ces questions progressivement : chaque sauvegarde conserve ses réponses, son auteur et sa date dans l'historique ; la version courante est exportée et transmise à l'agent de la tâche. Une trame de livrable Markdown reprend les questions, étapes, preuves et décision propres à la tâche. L'agent peut proposer des réponses structurées aux trois questions ; vous les relisez et les reprenez explicitement si elles conviennent. Les trois réponses doivent être renseignées avant validation. Vous pouvez aussi travailler vous-même avec notes, preuves, documents de travail éditables, livrable, fichiers privés, contrôles calculés pour CSV/TSV, Python et JSON. Les PDF et DOCX textuels sont extraits ; une image, un scan ou un XLSX reste une pièce à examiner manuellement. Le plafond est de 8 Mo et 30 fichiers par tâche. Une tâche peut être partagée avec un compte local pour contribution ou relecture ; les hypothèses, certains protocoles et décisions de diffusion exigent un avis de laboratoire sur la version actuelle avant clôture.

Pour un CSV/TSV joint, **Analyse descriptive** calcule localement effectif, moyenne, médiane, minimum, maximum et écart-type d'échantillon pour une variable numérique, éventuellement par groupe. Le résultat conserve l'empreinte du fichier, les colonnes choisies et le nombre de lignes exclues. Un agent délégué peut demander ce calcul pendant son travail ; Passage lui transmet ensuite les chiffres réellement calculés pour sa proposition finale. Le calcul ne constitue ni un test statistique, ni une interprétation causale, ni une validation des mesures.

Dans **Passages sourcés**, associez une affirmation à un passage exact d'un fichier textuel joint ou d'un document de la tâche. Passage vérifie le passage dans le texte extrait et conserve la version et l'empreinte de la source. Un agent peut proposer des passages présents dans les extraits qu'il a reçus ; ils n'entrent dans le registre qu'après votre relecture et votre enregistrement. Une nouvelle version du document rend l'ancrage périmé et bloque la validation tant qu'il n'est pas renouvelé ou archivé. L'export du dossier conserve aussi les ancrages archivés. Un passage vérifié dans un texte ne prouve pas à lui seul l'affirmation scientifique : l'utilisateur reste chargé de cette interprétation.

Le propriétaire peut **lier jusqu'à six livrables validés d'autres tâches du même projet** comme entrées du travail courant. L'agent reçoit des extraits bornés de ces versions, avec identifiant et empreinte ; une version documentaire déposée est lue depuis son historique immuable. Si la source change ou perd sa validation, la tâche aval doit être revue et ne peut pas déléguer ou se clôturer avec l'ancien lien. Une source confidentielle exige son autorisation d'usage par agent avant transmission. Pour partager la tâche aval, les invités doivent aussi avoir accès à chaque tâche source.

Chaque type de tâche possède aussi un **registre répétable à quatre colonnes** : fiches de lecture, essais, commentaires de relecteurs, candidatures, lots budgétaires ou autres éléments propres au travail. L'utilisateur et les éditeurs invités peuvent créer, modifier, archiver et rétablir les lignes. Chaque version conserve son auteur et sa date ; une ligne peut être reliée à une preuve ou un fichier de cette tâche. L'agent lit un extrait des lignes actives et peut proposer jusqu'à douze lignes, reprises seulement après vérification humaine. Le registre figure dans la trame et l'export du dossier.
Pour les tâches comportant une action hors de Passage (essai, exécution de tests, dépôt, transmission, accord ou séance), la clôture exige maintenant une **attestation datée du propriétaire liée à une preuve ou à un fichier** de la tâche. Elle devient périmée après toute modification du dossier, même si une étape est ensuite remise à son état précédent. Les tâches de jury, de relecture confidentielle et de divulgation exigent aussi un contrôle explicite avant de transmettre leurs pièces à un agent. L'attestation est une déclaration traçable ; Passage ne vérifie pas lui-même l'action ni l'autorisation institutionnelle. Le coordinateur masque les pièces non autorisées de ces tâches dans son contexte et ouvre la tâche sans délégation tant que ce contrôle manque.
Chaque tâche dispose d'un export Markdown du dossier avec état, étapes, pièces, versions de documents déposées, commentaires, décisions, limites et empreintes des fichiers ; les fichiers sont téléchargeables séparément.
Dans **Documents de travail**, créez un texte Markdown, LaTeX, Python, R, CSV ou brut, ou ouvrez le texte extrait d'un fichier ou un brouillon d'agent. Chaque sauvegarde crée une version immuable et une empreinte. Un compte invité comme éditeur peut modifier le document ; un relecteur peut commenter un passage exact de sa version courante. Déposez explicitement la version terminée comme livrable avant la validation humaine. Une modification après dépôt rouvre la tâche et impose de déposer la nouvelle version. L'éditeur est un éditeur de texte ; l'import PDF/DOCX ne conserve pas leur mise en page et Passage ne compile ni n'exécute le code. La limite est de 20 documents et 200 000 caractères par document.

Pour confier une tâche, ouvrez **Atelier des agents → Créer un agent → Travaux de recherche**, choisissez ses spécialités R1–R3 et complétez le Super Skill Creator. Plusieurs spécialistes peuvent être actifs. Dans le projet, **Composer l'équipe** permet de les affecter directement ; la tâche ne propose que les spécialistes qui la couvrent, ainsi que les agents directs généralistes déjà présents. L'agent reçoit les pièces autorisées et son harnais complet ; sa proposition, le modèle, la révision, les sources déclarées, les contrôles et les limites sont conservés. Il ne peut ni valider le livrable ni lancer un outil externe depuis ce parcours. Une expérience, un dépôt, un test de code ou une décision scientifique doivent être effectués et attestés par les personnes responsables. Le détail des 51 usages R1–R5 et de leurs limites est dans `USAGES_PASSAGE_R1_R5.md`.

Après lecture d'un brouillon, **Demander une correction du dernier brouillon** permet d'écrire un retour précis et de choisir un agent compatible de la même équipe. La nouvelle proposition reçoit le brouillon visé et le retour ; elle conserve leur lien, la consigne humaine, le résumé des changements annoncé par l'agent et une différence de texte calculée localement. Une tâche déjà validée doit d'abord être rouverte par une demande de révision humaine. Le propriétaire reste responsable de relire et d'accepter la nouvelle version.

Vous pouvez aussi décrire la tâche dans le dialogue du projet : le coordinateur connaît le catalogue et les spécialités de l'équipe, ouvre ou reprend une tâche, puis peut y lancer un agent adapté. Retrouvez son état dans **Travaux de recherche**. Une réponse du chat annonçant le lancement ne vaut pas achèvement du brouillon.

## Démarrer

Python 3.11 ou supérieur. Vérifié sous Windows avec Python 3.14.4. Aucun build JavaScript requis.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Ou exécuter `lancer.ps1` depuis PowerShell. Ouvrir **http://127.0.0.1:8088**. Le serveur écoute uniquement sur l'interface locale. API interactive : http://127.0.0.1:8088/docs.

Le corpus public et les programmes fictifs sont préchargés au premier démarrage. Chaque personne choisit « laboratoire », « doctorant/chercheur » ou « entreprise » à l'inscription (mot de passe de 12 caractères minimum). Sur une installation locale, le premier compte devient administrateur. Avec `PASSAGE_PUBLIC_SIGNUP=1`, notamment sur l'aperçu Render, aucun inscrit ne reçoit automatiquement les droits administrateur. Les sessions sont HttpOnly et les rôles sont contrôlés côté serveur. Il n'y a pas encore de vérification d'email, de récupération de mot de passe ou d'invitation d'équipe.

### Aperçu gratuit Render

`render.yaml` crée un service Docker gratuit et place SQLite dans `/tmp/passage.db`. Ce stockage et les connexions ChatGPT, Gradium, Dust et Pipelex sont **temporaires** : une mise en veille, un redéploiement ou un redémarrage peuvent les effacer. Utiliser cet aperçu pour des démonstrations seulement, sans données de recherche confidentielles. Chaque évaluateur peut créer un compte et un projet indépendants ; il doit relier ses propres fournisseurs pour appeler les agents ou la voix. Aucune connexion personnelle de l'installation locale n'est transférée sur Render.

La connexion Google à Passage est optionnelle. Pour l'activer, configurer `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` dans Render, puis autoriser exactement `https://<nom-du-service>.onrender.com/api/auth/google/callback` dans le client OAuth Web Google. Sans cette configuration, l'inscription email/mot de passe reste disponible. L'éditeur Excalidraw, les tâches et les parcours de projet fonctionnent sans fournisseur externe ; Marguerite et les agents nécessitent un compte ChatGPT connecté dans **Connexions**, et la voix nécessite aussi Gradium.

Les connexions aux fournisseurs exigent un accès HTTPS sortant depuis le processus Python. Une restriction réseau peut empêcher Gradium ou un MCP de répondre alors que la clé et le compte sont valides ; l'interface indique alors un échec réseau, pas un succès de connexion.

## Piloter une équipe par projet

Dans **Projets & dialogue**, créer un projet, décrire son objectif et ses contraintes. Les agents actifs lui sont affectés automatiquement. Envoyer une mission globale : le coordinateur choisit le spécialiste, attend son résultat, réévalue et poursuit. Le cerveau du coordinateur est celui d'un agent direct de l'équipe, ou le modèle ChatGPT sélectionné pour ce projet. Huit décisions maximum par message ; le bouton Arrêter prend effet après l'appel en cours.

Dans **Connexions → Ma voix · Gradium**, chaque compte peut enregistrer sa propre clé API et son identifiant de voix. Les deux sont chiffrés sur cette installation ; la clé n'est jamais renvoyée à l'interface. La transcription et la synthèse utilisent cette clé personnelle lorsqu'elle existe, puis la clé d'installation configurée par l'administrateur en secours. Retirer la clé personnelle restaure cet accès de secours.

Le chat permet de rechercher les notices, déléguer les analyses, modifier le nom/l'objectif/l'équipe et utiliser les outils MCP accordés. Conversations, rapports et validations sont privés au propriétaire du projet. Les notices publiques et les données historiques du scénario restent partagées. Le POC ne comprend pas encore l'invitation de membres ni une gestion de plusieurs organisations.

Le champ de dialogue et sa dictée Gradium acceptent aussi « Crée un projet [nom] », « Ouvre le projet [nom exact] », « Mes validations en attente », « Statut de la mission » et « Arrête la mission ». S'il n'y a qu'une carte en attente, la commande ouvre son projet et l'affiche ; elle ne confirme rien. Le sélecteur de projets indique le nombre de validations en attente. Pour gérer le cerveau du projet : « Liste les modèles ChatGPT », « Quel modèle utilise ce projet ? », « Utilise le modèle ChatGPT [nom exact] » et « Reviens au modèle de l’agent ». Le modèle demandé est vérifié dans le catalogue du compte connecté ; après un changement vocal, la session reprend automatiquement avec ce modèle. Ces commandes de gestion sont traitées directement, sans appel au modèle. La lecture vocale optionnelle annonce aussi les réponses immédiates. La commande d’ouverture ne voit que les projets du compte connecté.

Le chat utilise les **agents réels**. L'ancien sélecteur « Simulation explicite » a été retiré de l'interface : il produisait des réponses illustratives répétitives. Le coordinateur reçoit le dernier message et l'historique récent du projet ; une question de suivi doit utiliser les travaux déjà obtenus plutôt que relancer la mission initiale. ChatGPT est le cerveau par défaut ; une connexion du compte dans Passage est nécessaire pour les appels réels.

Le bouton rond **Conversation vocale** ouvre un dialogue continu depuis l'accueil ou sur le projet sélectionné. Sans projet, un agent direct actif fournit le cerveau ChatGPT ; « crée un projet [nom] » ou « ouvre le projet [nom] » fait basculer vers ce projet après la réponse parlée, puis la conversation reprend automatiquement. Une carte en attente de validation arrête la voix et s'affiche dans le projet. Les échanges directs avant projet sont temporaires. Le microphone reste actif pendant que Gradium transcrit la parole et synthétise la réponse ; les deux transcriptions apparaissent dans la fenêtre vocale, et la reprise de parole peut interrompre la lecture. Dans un projet, le LLM est ChatGPT via le serveur Codex connecté **dans Passage**, sauf choix délibéré d'un autre fournisseur pour ce projet. Le bouton **Terminer** ferme la session et le microphone ; les messages transcrits sont conservés dans le projet. Ce mode passe explicitement en Appels réels, utilise la clé Gradium du compte ou de l'installation côté serveur et demande toujours une validation dans la carte pour les écritures MCP. Le relais ChatGPT utilise les droits Codex de l'abonnement, pas les crédits API OpenAI ni la voix native de ChatGPT. Son adaptateur rend actuellement une décision complète par tour, ce qui peut rendre la première réponse lente. La dictée **Parler** reste disponible pour préparer un message écrit.

En mode **Appels réels**, « Liste les agents Dust » et « Liste les méthodes Pipelex » lisent les catalogues MCP du compte connecté, même sans projet sélectionné. Les outils de lecture correspondants doivent être autorisés dans Connexions. La réponse peut être lue par Gradium ; cette consultation ne lance ni agent Dust ni méthode Pipelex. Les commandes reconnaissent aussi « Piplex », variante phonétique observée dans une transcription Gradium du nom Pipelex.

« Montre la méthode Pipelex Passage Recherche doctorale » lit la signature de cette méthode par son identifiant de catalogue. Les guillemets et les accents sont facultatifs dans la commande vocale. Passage exige `pipelex_list_methods` et `pipelex_show_method`, vérifie le nom dans le catalogue personnel et affiche uniquement la signature et le modèle d’entrées retournés par Pipelex. Cette commande ne lance pas la méthode.

Les appels MCP déclarés en lecture seule peuvent avancer automatiquement. Les autres appels affichent leurs paramètres exacts et attendent Confirmer/Refuser. Un état de livraison incertain bloque le double envoi. Le mode Simulation est une répétition déterministe explicitement annoncée ; il n'appelle aucun sponsor.

## Démonstration et appels réels

Le mode de démonstration déterministe reste dans l'API et les tests de recette, mais il n'est plus proposé dans l'interface. Les notices de démonstration restent réelles ; les publications et l'entreprise du scénario sont fictives et signalées comme telles.

Pour utiliser l'API OpenAI, copier `.env.example` vers `.env` et renseigner `OPENAI_API_KEY`. Pour utiliser les droits du compte ChatGPT, choisir **Connexions → Mon compte ChatGPT**, se connecter par navigateur ou code, puis choisir un modèle dans le projet. Les réglages API peuvent aussi être saisis dans **Connexions** : les clés restent en mémoire par défaut ; cochez **Conserver sur cette installation (chiffré)** pour les retrouver après redémarrage. Les réglages persistants sont chiffrés dans la base, avec la clé locale `data/runtime/oauth.key` à sauvegarder séparément avec précaution. Ne jamais commiter `.env`. L'application ne renvoie pas les valeurs secrètes à l'interface.

### Comptes personnels ChatGPT, Dust et Pipelex

Dans **Connexions**, le compte ChatGPT se relie via Codex App Server par navigateur ou par code d'appareil, utile si le retour local du navigateur échoue. Chaque compte local Passage possède son propre espace d’authentification ; Passage ne copie pas les identifiants de l’application Codex du poste. Le catalogue des modèles et les limites s’affichent après autorisation. Les appels utilisent les droits Codex de ce compte ; ils ne consomment pas le crédit de l’API OpenAI, facturé séparément.

Pour utiliser ce compte dans un projet, choisissez le modèle ChatGPT au moment de créer le projet ou ouvrez **Objectif & équipe → Cerveau de ce projet**. Les choix proposés proviennent du catalogue du compte connecté. Ce réglage ne change pas le modèle des autres projets ni le harnais de l'agent coordinateur. Il s'applique au chat et à la conversation vocale Gradium du projet. Vous pouvez aussi revenir au modèle propre de l'agent. Un changement est refusé pendant une mission en cours. La connexion réelle du compte puis une inférence restent nécessaires pour vérifier l'usage de cette offre sur cette installation.

Dust et Pipelex offrent deux parcours distincts : OAuth MCP donne accès aux outils autorisés du workspace ; les anciens moteurs d’agents et méthodes publiées utilisent leurs propres clés API. Dust peut bloquer les appels programmatiques quand son plafond mensuel est atteint. Pipelex expose les méthodes publiées du compte, qui intègrent leur propre choix de modèle ; le nom d’une méthode ne représente pas un identifiant de modèle LLM. Consultez la page Connexions pour l'état actuel des accès.

Après confirmation d'une demande « Demande à Pipelex de… », la carte de validation conserve l'identifiant de l'exécution durable renvoyé par le MCP. Le bouton **Lire état et résultat Pipelex** interroge `pipelex_run_status` et `pipelex_run_results`, puis affiche leurs réponses dans le projet. Ces lectures exigent les deux permissions MCP correspondantes. Le lancement d'un run ne constitue pas un résultat terminé ; le contrôle doit être relancé si Pipelex indique que le travail continue.

Avant de préparer cette carte, Passage lit aussi `pipelex_show_method` et vérifie que la méthode doctorale accepte toujours `request: native.Text` et retourne `native.Text`. Les droits `pipelex_list_methods`, `pipelex_show_method` et `pipelex_run` sont nécessaires. Si le contrat a changé, aucune carte de lancement n'est créée ; la signature vérifiée apparaît dans la carte lorsque la préparation réussit.

Au moment de confirmer, Passage relit la signature. Si elle a changé depuis la préparation, la carte indique « Contrat modifié » et aucun run ne part. Si cette lecture échoue temporairement, la carte reste en attente pour un nouvel essai ; le lancement n'est pas déclaré incertain puisqu'aucun appel `pipelex_run` n'a été envoyé.

La commande « Demande à Dust de… » fonctionne aussi dans le chat et, après transcription Gradium, à la voix. En mode réel, elle prépare une conversation avec l'agent Dust par défaut et montre exactement le titre et le message qui seront transmis. L'appel `create_conversation` attend la confirmation de la carte. Si Dust renvoie un identifiant exploitable, **Lire la réponse Dust** consulte uniquement cette conversation avec `get_conversation_messages`, à condition que l'outil soit accordé. Un retour incertain n'est jamais relancé automatiquement. Dans ce cas, **Retrouver dans Dust** ou « Retrouve la conversation Dust » peuvent consulter `list_conversations`, si ce droit est accordé, pour rattacher une conversation portant exactement le titre unique de la carte. La commande vocale exige qu'une seule conversation soit incertaine dans le projet ; sinon, il faut choisir sa carte. Le statut reste incertain jusqu'à vérification des messages ; aucun autre titre n'est conservé. La recherche examine au maximum quatre pages récentes et peut donc ne pas retrouver une conversation plus ancienne.

Pour choisir un agent du compte Dust, utiliser « Liste les agents Dust », puis « Demande à l’agent Dust analyst de [travail] » en remplaçant `analyst` par le nom voulu. Les guillemets sont facultatifs, et « deep dive » peut désigner l’agent `deep-dive` si le nom normalisé reste unique. Passage vérifie que ce nom apparaît une seule fois dans le catalogue accessible avant de préparer la carte ; les droits `list_agents` et `create_conversation` sont nécessaires. Une demande identique au même agent ne crée pas deux cartes. Aucun agent n'est lancé avant confirmation.

Les commandes **« Réponse Dust »** et **« Statut Pipelex »** relisent la dernière action confirmée du projet en mode réel, par texte ou transcription vocale. Passage affiche la réponse complète dans la carte et annonce un extrait brut dans le dialogue ; cet extrait n'est pas une analyse scientifique validée.

Les quatre agents utilisent par défaut le compte ChatGPT relié à Passage et son modèle disponible par défaut (`auto`), modifiable dans l'atelier. Le moteur direct utilise Codex App Server pour les agents ChatGPT ; l'API Responses reste disponible seulement si un agent choisit explicitement OpenAI API. Un refus, une citation invalide ou une erreur fournisseur fait échouer l'exécution et conserve les dossiers précédents. Il n'y a pas de repli silencieux vers une simulation.

Un utilisateur peut ajouter délibérément un modèle local depuis l'atelier avec **Ajouter un modèle local**, puis choisir son modèle et activer l'agent. Aucun modèle local n'est proposé ni utilisé par défaut. Le POC ne télécharge aucun modèle.

Les anciennes sorties locales restent dans `examples/` pour audit. L'instance courante a migré ses agents actifs vers ChatGPT ; leurs anciennes révisions restent consultables dans l'atelier.

Un modèle local ou un autre fournisseur compatible peut être configuré avec `COMPATIBLE_BASE_URL`, une clé éventuelle et un identifiant de modèle. Le serveur doit prendre en charge Chat Completions et JSON mode. La validation des sorties reste locale. Les outils MCP déclenchés par le modèle sont implémentés pour le moteur OpenAI direct ; cette combinaison est refusée sur le moteur compatible.

## Ce que contient le POC

- Laboratoire : 61 notices LRCS dans le corpus initial, import réel/rafraîchissement conservateur, lecture unitaire ou par lot, publication/retrait, export CSV.
- Bibliothèque : notices publiées, recherche textuelle, rapprochement d'un besoin avec explications, accès aux sources.
- Fiche : résumés source/généré/corrigé distincts, maturité et droits à vérifier, dossiers Opportunité/Incorporation, dialogue de suivi, exports Markdown.
- Programmes : création locale, propositions, acceptation/refus, notes, signal visible côté doctorant et consultations distinctes.
- Atelier : création guidée, duplication, définition du cerveau et du harnais, contexte/mémoire/outils, révisions, tests et snapshots.

### Créer un agent avec le Super Skill Creator

Dans **Atelier des agents → Créer un agent**, choisir le rôle métier. Passage prépare un brouillon inactif selon la méthode **Super Skill Creator V4** d'OSCAR AI, adaptée au POC. L'éditeur guide six étapes : cadrer la mission, choisir le cerveau, écrire le skill et les pièces, accorder les outils, contrôler, puis enregistrer une révision et tester. Le déclencheur, les sources lues, les décisions humaines, le point de vérification et le livrable sont à renseigner par le créateur ; ils ne sont pas inventés par le modèle.

**Contrôler le brouillon** affiche les points manquants. Un brouillon incomplet peut être sauvegardé, mais ne peut être activé ni exécuté. Les pièces processus, workflow et expérience sont facultatives au départ ; lorsqu'elles sont renseignées, elles entrent dans le harnais assemblé et les snapshots d'exécution. La mémoire reste validée manuellement. Les quatre rôles initiaux conservent leur contrat de sortie. Le rôle « Travaux de recherche » produit un brouillon structuré pour les spécialités choisies. La capacité `work.read` donne seulement accès au contexte autorisé fourni par la tâche ; elle ne crée pas un outil exécutable.

Sources d'inspiration lues dans le projet préexistant : `Oscar-AI/SUPER_SKILL_creator_v2.md`, `SUPER_SKILL_creator_v3.md`, `SUPER_SKILL_creator_v4.md` et `backend/app/doctrine_creation.py`. Passage utilise sa propre implémentation dans `passage/creator.py` et `passage/static/creator.js`.
- Connexions : OpenAI, endpoint compatible, Dust, Pipelex, Oscar et serveurs MCP Streamable HTTP avec liste d'outils autorisés.
- Exécutions : traitements asynchrones, étapes, durée, erreurs et provenance.

## Dust : notre éditeur reste la source de vérité

1. Configurer `DUST_API_KEY`, `DUST_WORKSPACE_ID` et éventuellement `DUST_BASE_URL` (dont l'instance européenne).
2. Ouvrir l'agent Incorporation, choisir Dust et le modèle disponible dans son workspace ; enregistrer.
3. **Publier dans Dust** transmet la projection de la révision. L'identifiant distant est enregistré.
4. Lancer un dossier ou poser une question en mode réel. Chaque échange transmet le contexte et les derniers dossiers ; le fil est conservé dans Passage.

Une modification locale invalide la synchronisation et nécessite une nouvelle publication. Les connecteurs MCP personnalisés ne sont pas projetés automatiquement dans Dust : le POC refuse une publication qui les ignorerait. L'export JSON Dust est disponible pour inspection. La publication crée une nouvelle configuration distante ; le nettoyage des anciennes configurations reste à l'opérateur.

## Pipelex dans le harnais

1. Ouvrir un agent (Lecteur conseillé), sélectionner Pipelex, le modèle et la version de méthode ; enregistrer.
2. **Exporter .mthds** produit une méthode avec le mandat, le skill, le contexte, la mémoire et le contrat de sortie. Entrée `request` de type `Text`, sortie `Text` contenant le rapport JSON.
3. Publier cette méthode dans le compte Pipelex avec ses outils habituels, puis renseigner sa référence dans le harnais (ou `PIPELEX_METHOD_REF`). Utiliser une référence versionnée.
4. Configurer `PIPELEX_API_KEY`. Passage appelle `POST /v1/start`, suit l'identifiant distant et valide le rapport retourné.

La définition distante doit correspondre au fichier exporté. Le modèle affiché pour Pipelex est le modèle **déclaré** dans le harnais ; Passage ne peut pas attester d'un changement manuel du modèle dans le compte distant. Une référence seule ne prouve pas cette synchronisation.

La bibliothèque Python Pipelex n'est pas requise au lancement du POC. L'exécution d'un harnais utilise l'API hébergée. Le coordinateur peut aussi utiliser le MCP officiel Pipelex après connexion OAuth et sélection des outils dans Connexions. Ces deux accès sont distincts.

Les quatre fichiers de `methods/` sont également validés avec **Pipelex 0.65.0**, y compris son exécution à blanc. Reproduire :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-pipelex.txt
.\.venv\Scripts\python.exe scripts\validate_pipelex.py
```

Ce script exporte les profils initiaux, prépare uniquement la configuration du projet `.pipelex/` et ne déclenche aucune inférence. Un identifiant de validation factice permet au catalogue de charger les spécifications OpenAI sans clé ; il reste dans le processus du script. La validation de méthode ne constitue pas un appel réussi au service Pipelex hébergé.

## Oscar et outils MCP

Par défaut `PASSAGE_OSCAR=demo`. Les programmes de `data/programmes_demo.json` sont **rédigés pour le scénario**, pas exportés d'un Oscar connecté. Les notes acceptées sont persistées en base et dans `data/notes_demo.json`.

Pour connecter l'Oscar de l'opérateur :

```dotenv
PASSAGE_OSCAR=mcp
OSCAR_URL=http://127.0.0.1:8000
OSCAR_TOKEN=jeton-agent-a-renseigner-localement
OSCAR_COMPANY=1
OSCAR_MCP_SCRIPT=C:/chemin/Oscar-AI/backend/passerelle/oscar_mcp.py
```

Le serveur stdio existant reçoit `OSCAR_API`, `OSCAR_JETON`, `OSCAR_COMPANY`. Seuls `oscar_projets`, `oscar_contexte`, `oscar_deposer_avis` sont accessibles dans cet adaptateur. Le POC n'accède pas implicitement au trousseau Oscar. En cas d'envoi ambigu d'une note, il affiche « livraison à vérifier » et bloque une répétition automatique.

Dans **Connexions → Dust & Pipelex**, cliquer « Connecter avec OAuth », ouvrir le lien d'autorisation, puis revenir choisir les outils autorisés. Serveurs officiels : `https://dust.tt/mcp`, `https://eu.dust.tt/mcp`, `https://mcp.pipelex.com/mcp`. `PASSAGE_PUBLIC_URL` doit correspondre à l'adresse utilisée dans le navigateur ; le retour est `/api/mcp/oauth/callback`. Dust peut restreindre les redirections au niveau du workspace. Les clés HTTP Dust ne fonctionnent pas pour son MCP. Les jetons OAuth sont chiffrés en SQLite, avec une clé locale dans `data/runtime/oauth.key` : conserver base et clé ensemble pour une sauvegarde, sans les commiter. Déconnecter retire les accès locaux ; la révocation distante se fait chez le fournisseur.

Après avoir accordé `list_agents` à Dust ou `pipelex_list_methods` à Pipelex, les boutons **Voir les agents** et **Voir les méthodes** affichent les noms et descriptions du compte connecté. Ces lectures passent par le MCP officiel, avec les seules permissions déjà accordées. Elles ne lancent ni conversation Dust ni méthode Pipelex. Les modèles LLM sont configurés dans les agents Dust ou les méthodes Pipelex ; ce catalogue n’est pas une liste de modèles bruts.

Le bouton **Exporter méthode doctorant** télécharge `methods/recherche_doctorale.mthds`. Son pipe prépare une proposition de rédaction, protocole, simulation ou logiciel à partir d'une demande et de sources fournies. Le fichier est validé à blanc avec Pipelex 0.65.0 et une copie a été enregistrée et validée dans le catalogue privé de ce compte Pipelex. Le modèle hébergé est `gpt-5.4-mini` ; il ne lance ni expérience physique, ni calcul, ni test de code. Sur cette installation, `pipelex_run` est autorisé dans le MCP ; chaque exécution doit encore être confirmée dans la carte du projet. Le projet **Vérification MCP Pipelex** contient une carte préparée pour cet essai, sans run distant lancé.
Dans un projet sélectionné, écrire ou dicter « **Demande à Pipelex de préparer…** » consulte le catalogue autorisé, retrouve cette méthode et vérifie sa signature avant de préparer ses entrées. Passage affiche alors une carte de validation ; aucun appel d'inférence n'est envoyé tant que la carte n'est pas confirmée. La commande nécessite les permissions `pipelex_list_methods`, `pipelex_show_method` et `pipelex_run`. Une demande identique déjà en attente n'ajoute pas de seconde carte.
Après confirmation, la réponse brute du MCP reste consultable dans cette carte. `pipelex_run` lance une exécution durable et peut ne renvoyer que son identifiant. **Statut Pipelex** lit l'état et les résultats ; le dialogue distingue une méthode en cours, terminée ou échouée à partir des champs structurés et indique le délai de relecture conseillé par Pipelex. Une demande répétée pendant ce délai réutilise la dernière lecture, sans rappeler le MCP. Le contenu brut demeure dans la carte pour vérification avant usage.

Dans **Projets & dialogue**, ouvrez un projet, cliquez **Choisir les sources** et sélectionnez jusqu'à huit notices theses.fr, puis demandez par exemple « Rédige une section de thèse à partir des sources du projet ». Le coordinateur confie le brouillon au cerveau choisi pour le projet. Passage refuse les références hors sélection et les citations absentes des résumés. Un second agent direct actif de la même équipe et du même fournisseur relit le brouillon si disponible. Son avis et les corrections demandées apparaissent dans **Livrables de recherche** et dans l'export Markdown, avec les liens des notices. Ce contrôle établit la provenance des extraits, pas la validité scientifique de toutes les affirmations. Le doctorant valide et révise le texte final. Pour un protocole, une simulation ou un programme, la génération propose une méthode ou du code mais n'exécute ni matériel expérimental, ni calcul, ni tests logiciels ; seul le calcul batterie explicite utilise un modèle exécuté.
Une première exception calculable est disponible pour la démonstration batteries : le coordinateur peut lancer un **modèle thermique simplifié** à partir de huit paramètres fournis explicitement (courant, résistance, capacité thermique, refroidissement, températures ambiante et initiale, durée, pas). Passage intègre numériquement `C × dT/dt = I² × R − h × (T − T_amb)`, conserve les paramètres et la série, puis exporte la série en CSV. Le résultat est marqué « calcul exécuté · modèle simplifié », avec ses hypothèses et sa validation expérimentale à faire. Le modèle n'exécute aucun code généré par un LLM et ne vaut pas mesure de batterie réelle.

Les connecteurs MCP personnalisés utilisent Streamable HTTP avec un jeton configuré côté serveur ; ils sont accordés individuellement au harnais. OAuth est pris en charge pour les trois services officiels ci-dessus. Le transport SSE historique n'est pas inclus.

## Données et confiance

76 notices et leurs détails ont été collectés le 25/09/2026 dans `data/corpus_theses.json`. Aucun PDF stocké. Le corpus contient 61 notices liées au LRCS et des travaux d'autres laboratoires, notamment DRIVE et Chimie ParisTech. Les noms et affiliations restent ceux de theses.fr.

Les publications initiales représentent une validation **simulée dans le POC**. Aucun accord des laboratoires réels ni relation avec Vélia Mobilité (entreprise fictive) n'est revendiqué. Les nouvelles notices importées sont privées.

Les sorties sont contraintes par schéma ; les citations sont contrôlées contre les résumés fournis. Cela ne prouve pas la vérité scientifique des interprétations. L'analyse n'utilise pas le texte intégral ni une recherche de brevets/concurrents. Le dossier le signale. La présélection de recherche limite le corpus LLM à 25 fiches et indique le nombre examiné.

**Voix Gradium :** configurer `GRADIUM_API_KEY` et `GRADIUM_VOICE_ID`. Dans le chat, Parler ouvre le micro ; Terminer le ferme et transmet le WAV à Gradium. La transcription est affichée pour relecture avant envoi au coordinateur. Une case distincte permet l'envoi dès la transcription, y compris sans projet sélectionné pour créer ou ouvrir un projet à la voix ; la relecture reste le comportement par défaut. « Lire les réponses avec Gradium » active la synthèse sur les deux écrans. Capture limitée à 60 secondes, mono 24 kHz / 16 bits. L'audio est envoyé au service Gradium et n'est pas persisté par Passage. Les erreurs restent visibles ; aucun remplacement silencieux par la dictée du navigateur. Sans accès Gradium, le clavier reste disponible. Aucun MCP officiel Gradium n'est supposé : cette intégration utilise ses API vocales REST. Jinko reste non connecté.

## Vérifier et développer

```powershell
python -m pytest tests -q
python -m compileall -q passage run.py
node --check passage/static/app.js
```

Les tests utilisent des bases temporaires isolées. Les tests de contrat fournisseurs simulent les réponses HTTP et ne consomment pas de crédits. Une connexion réelle aux fournisseurs doit être vérifiée séparément.

Le bouton d'import du corpus agit sur la base locale ; le fichier livré permet un premier lancement sans import.

Structure : `passage/main.py` (API et cas d'usage), `agents.py` (harnais et contrats), `integrations.py` (services), `sources.py` (theses.fr), `store.py` (SQLite), `static/` (interface), `tests/` (recette).

La base locale est `data/passage.db`, modifiable via `PASSAGE_DB`. Sauvegarder ce fichier serveur arrêté pour conserver les travaux. Les exécutions en cours sont signalées comme interrompues après un redémarrage ; elles ne sont pas relancées automatiquement.

## Documents

- [Spécification fonctionnelle détaillée](SPEC_FONCTIONNELLE.md)
- [Scénario de démonstration](DEMO.md)

Membre de l'équipe : Sébastien. Nom du produit provisoire. Le dépôt public exclut les bases, les secrets, les sessions et le journal de travail local.

### Reprise des connexions MCP

Le SDK MCP est fixé à la version 1.30.0 utilisée en recette. L’adaptateur restaure explicitement la date d’expiration et redécouvre les métadonnées OAuth validées avant le renouvellement d’un jeton sauvegardé. Une mise à jour du SDK doit repasser le test de reprise OAuth. Pour ce workspace Dust, utiliser **Dust Europe** ; le serveur global refuse son jeton régional.
