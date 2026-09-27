# Passage

**Une équipe d’agents pour conduire un projet de recherche, du premier article au livrable vérifié.**

Passage aide les doctorants à organiser leurs travaux, rédiger, préparer des protocoles, analyser des données et cadrer une simulation ou un logiciel scientifique. Marguerite, l’agent permanent, discute du besoin, propose des actions concrètes dans Passage, puis les exécute après validation. Le scientifique conserve la décision et la validation des résultats.

Projet de **Sébastien Tricoire** pour le **X-IA Hackathon — Rise of Agents X**. L’éditeur d’agents s’inspire de la doctrine Super Skill Creator V4 du projet antérieur **Oscar-AI**, déclaré comme préexistant. Passage possède son propre code, ses contrats et ses contrôles.

**Code source public :** [Oscar-Space-Dev/passage-hackathon](https://github.com/Oscar-Space-Dev/passage-hackathon).

## Essayer en trois minutes

1. Ouvrez [Passage sur Render](https://passage-hackathon.onrender.com/).
2. Créez un compte **Doctorant/chercheur**, **Laboratoire** ou **Entreprise**. Chaque compte garde ses propres projets et conversations.
3. Créez un projet, ouvrez **Travaux de recherche**, choisissez une tâche R1–R3 et parcourez ses étapes, questions et contrôles humains.
4. Ouvrez **Marguerite** pour décrire un objectif. Elle propose un plan ; rien n’est exécuté avant **Valider et exécuter**.
5. Pour une réponse d’agent réelle, reliez votre compte ChatGPT dans **Connexions**. La voix Gradium de démonstration est déjà configurée sur le site public ; elle utilise le quota de Passage. Vous pouvez aussi enregistrer votre propre clé.

Le déploiement Render exige une base Turso externe pour conserver comptes et projets lors des redémarrages. N’y chargez pas de données confidentielles pendant le hackathon.

**Inscription :** nom, email et mot de passe de 12 caractères minimum. La connexion Google n’est pas encore configurée sur cet aperçu. Les comptes créés sur une installation locale ne sont pas transférés sur le site public. Sur Render Free, un réveil après inactivité peut prendre une minute.

**ChatGPT :** dans **Connexions**, lancez la connexion par code d’appareil, ouvrez la page OpenAI indiquée, puis saisissez le code affiché. Si OpenAI le demande, ouvrez [les paramètres de sécurité ChatGPT](https://chatgpt.com/settings/security), descendez à **Sécurité des applications** et activez **« Connexion par code d’appareil pour Codex, Excel, PowerPoint et Word »**. Revenez dans Passage, générez un nouveau code si le précédent a expiré, puis vérifiez que le statut indique **Connecté**. Chaque utilisateur connecte son propre compte ; l’abonnement ChatGPT ne fournit pas une clé API OpenAI.

**Recette publique du 27 septembre 2026 :** inscriptions, création d’un projet et d’un fichier, sauvegarde d’un schéma, invitation liée à son destinataire et refus d’accès entre comptes vérifiés sur Render. Les données ont survécu à un redéploiement. Un compte laboratoire créé publiquement ne peut pas modifier le catalogue commun. Gradium a renvoyé un vrai fichier audio à un compte sans clé personnelle. La génération et le renouvellement d’un code de connexion ChatGPT répondent ; une réponse réelle de Marguerite sur un compte évaluateur reste à vérifier.

**Présentation :** [vidéo d’animation en collage, 111 secondes](demo/Passage_demo_collage.mp4) · [dossier Word](demo/Passage_dossier_hackathon.docx) · [scénario et voix](DEMO.md). Le scientifique sert de fil narrateur ; Marguerite montre comment les agents coopèrent dans un projet. La vidéo illustre les parcours ; elle ne constitue pas une capture d’exécutions de fournisseurs externes.

## Guide de prise en main et de configuration

Ce guide concerne [le site public](https://passage-hackathon.onrender.com/). Prévoyez une adresse email à laquelle vous avez accès, un mot de passe d’au moins 12 caractères et, pour les essais avec un agent réel, un compte ChatGPT dont la connexion par code d’appareil est autorisée. Le premier chargement sur Render Free peut être lent après une période d’inactivité. Aucun compte de démonstration partagé n’est nécessaire.

### 1. Créer son espace Passage

1. Ouvrez le site, choisissez **Créer un compte**, puis renseignez nom, email et mot de passe.
2. Choisissez le profil **Doctorant/chercheur**, **Laboratoire** ou **Entreprise**. Ce profil oriente l’interface ; il ne donne pas accès aux données des autres comptes.
3. Connectez-vous. La navigation de gauche donne accès à **Projets & dialogue**, **Travaux de recherche**, **Mes équipes**, **Bibliothèque**, **Exécutions** et **Connexions**.
4. Déconnectez-vous puis reconnectez-vous pour retrouver votre espace. Sur le site public, la base Turso garde les comptes, projets et fichiers après un redémarrage de Render.

La connexion Google n’est pas activée sur cet aperçu. Elle nécessiterait un client OAuth configuré par l’administrateur. L’inscription avec ChatGPT n’est pas proposée : relier ChatGPT comme moteur d’agent est une opération distincte de la création du compte Passage. Il n’y a pas encore de procédure de réinitialisation du mot de passe sur l’aperçu.

### 2. Connecter son compte ChatGPT pour les agents

1. Dans Passage, ouvrez **Connexions → Mon compte ChatGPT**. Si le statut est **Non connecté**, ouvrez **Aide : connecter mon compte ChatGPT**.
2. Dans un autre onglet, ouvrez [ChatGPT → Paramètres → Sécurité et connexion](https://chatgpt.com/settings/security) avec **le même compte** que celui à relier. Tout en bas, sous **Sécurité des applications**, activez **« Activer la connexion par code d’appareil pour Codex, Excel, PowerPoint et Word »**. Le libellé anglais possible est *Enable device code authentication*.
3. Revenez dans Passage et cliquez **Connecter mon compte ChatGPT** ou **Utiliser un code**, selon le bouton affiché. Passage montre une page officielle OpenAI et un code à usage limité.
4. Cliquez **Ouvrir la page de connexion**, saisissez ce code et terminez l’autorisation chez OpenAI. Si vous aviez tenté la connexion avant d’activer l’option de sécurité, cliquez d’abord **Générer un nouveau code** dans Passage : l’ancien peut être invalide.
5. Revenez dans **Connexions**, cliquez **Vérifier la connexion** et attendez le statut **Connecté**. Vous pouvez alors créer un projet avec **ChatGPT · modèle par défaut de mon compte**, ou choisir un des modèles que Passage obtient de votre compte.

Si l’option de sécurité n’apparaît pas, vérifiez le compte ChatGPT sélectionné et faites défiler toute la page. Pour un compte d’établissement, l’administrateur peut devoir autoriser la connexion par code. Le message d’OpenAI mentionnant `codex login --device-auth` ne demande aucune commande à lancer par le testeur : Passage gère cette étape. Si un code expire, générez-en un autre. **Un code généré ne prouve pas que la connexion a réussi** : vérifiez le statut **Connecté**, puis faites un essai de réponse réelle. La connexion est personnelle et enregistrée chiffrée ; **Déconnecter** supprime sa sauvegarde. Les crédits de l’abonnement ChatGPT/Codex sont distincts d’une clé API OpenAI et de sa facturation.

### 3. Régler la voix Gradium

1. Dans **Connexions → Ma voix · Gradium**, vérifiez la pastille **Voix de démonstration active**. Sur l’aperçu public, vous pouvez essayer la voix sans saisir de clé : le quota Gradium de Passage est utilisé.
2. Pour employer votre propre quota, ouvrez **Utiliser ma propre clé Gradium**, saisissez votre clé et un identifiant de voix, puis cliquez **Enregistrer ma voix**. La clé n’est pas réaffichée par l’interface.
3. Dans **Projets & dialogue**, cochez **Lire les réponses avec Gradium** pour obtenir la lecture orale des réponses, ou cliquez **Parler** pour dicter. Le navigateur demandera l’autorisation du micro ; vous pouvez relire la transcription avant l’envoi, ou cocher **Envoyer la commande vocale dès sa transcription**.
4. Pour le dialogue continu, ouvrez le mode conversation et terminez la session avec son bouton **Terminer**. Si vous retirez votre clé personnelle, Passage réutilise la clé de démonstration quand elle est disponible.

Le chemin de synthèse Gradium a été vérifié sur le site public avec un vrai fichier audio. La qualité de la transcription, l’autorisation du micro et l’écoute sur votre appareil dépendent du navigateur et doivent être essayées par le testeur.

### 4. Connecter Dust et Pipelex par MCP

1. Ouvrez **Connexions**, puis descendez à **Dust & Pipelex · MCP officiel**. Chaque carte affiche **Non connecté** ou **Connecté** pour *votre propre compte*.
2. Sur **Dust**, **Dust Europe** ou **Pipelex**, cliquez **Connecter avec OAuth**. Connectez-vous chez le service correspondant et approuvez l’accès sur sa page officielle. Revenez à Passage ; le statut doit passer à **Connecté**.
3. Cochez uniquement les outils dont l’agent peut disposer, puis cliquez **Autoriser la sélection**. Le bouton **Actualiser les outils** relit le catalogue ; selon les droits accordés, **Voir les agents** ou **Voir les méthodes** donne un contrôle en lecture.
4. Dans un projet, demandez par exemple « liste les agents Dust » ou « liste les méthodes Pipelex ». Pour une action externe, lisez la carte **Votre validation** et cliquez **Confirmer** ou **Refuser**. L’autorisation OAuth seule ne vaut pas approbation d’une écriture.

Cette connexion MCP personnelle n’est pas une clé API de moteur Dust ou Pipelex. Les cartes **Clés API de l’installation**, visibles par l’administrateur, configurent séparément l’exécution d’agents publiés et peuvent indiquer **À configurer** alors que votre OAuth MCP fonctionne. L’aperçu ne fournit pas de compte Dust ou Pipelex partagé à tous les testeurs : utilisez vos propres comptes pour ce scénario. **Exporter méthode doctorant** produit un fichier `.mthds` ; cela ne publie ni n’exécute la méthode dans Pipelex.

### 5. Connecter un projet Jinkō

1. Munissez-vous d’un compte Jinkō, d’une **clé API personnelle** et de l’**identifiant d’un projet Jinkō** auquel cette clé donne accès. Aucun projet Jinkō de test n’est fourni publiquement.
2. Dans **Connexions → Mon projet Jinkō**, renseignez les deux champs, puis validez. Passage vérifie l’association et conserve la clé chiffrée pour votre compte.
3. Cliquez **Voir les modèles** pour une lecture SDK. Reliez aussi ChatGPT et utilisez **Créer mon agent Jinkō** pour créer un agent Passage qui pourra lire les modèles, états, diagnostics et résultats autorisés.
4. Lancez cet agent dans votre projet Passage et vérifiez ses lectures dans **Exécutions**. Il ne crée, ne modifie et ne lance pas d’essai Jinkō.

L’adaptateur SDK et ses contrôles ont des tests automatisés, mais ce parcours n’a pas encore été validé avec un vrai projet Jinkō sur l’aperçu public. Les tests du SDK utilisent des réponses contrôlées : ne les confondez pas avec une connexion sponsor réussie.

## Scénarios testables dans Passage

Chaque scénario ci-dessous indique ce que le parcours démontre, les clics à effectuer et ce qu’il faut observer. Les fonctions de rangement, de versionnement et de partage sont accessibles sans fournisseur LLM ; les générations d’agents exigent un cerveau connecté. Pour une démo courte, suivez **A → B → C → E → F → H**. Pour une recette complète, parcourez aussi les autres scénarios et consultez les [32 fiches de tâches R1–R3](PARCOURS_R1_R3.md).

### A. Première connexion, projet et dialogue

**But.** Créer un espace de recherche privé et mobiliser une équipe d’agents autour d’un objectif.

1. Terminez l’inscription et, si vous voulez une réponse d’agent, [connectez ChatGPT](#2-connecter-son-compte-chatgpt-pour-les-agents).
2. Ouvrez **Projets & dialogue → Nouveau projet**. Donnez un nom, décrivez **Objectif et résultat attendu** et le contexte. Laissez **ChatGPT · modèle par défaut de mon compte**, puis cliquez **Créer le projet**.
3. Dans **Agents mobilisables**, cliquez **Composer l’équipe** pour choisir les spécialistes actifs. Saisissez un objectif précis dans le dialogue, puis cliquez **Envoyer**.
4. Revenez à un autre écran puis au projet : retrouvez les messages et les travaux associés. Si le cerveau n’est pas connecté, Passage doit indiquer l’erreur de connexion, sans présenter une réponse fictive comme un résultat.

**À constater.** Le projet existe dans le sélecteur **Projet**, le cerveau par défaut est ChatGPT, et les échanges restent dans ce projet et ce compte.

### B. Marguerite propose puis exécute un plan approuvé

**But.** Passer d’un besoin en langage naturel à des actions traçables dans Passage, avec une décision explicite de l’utilisateur.

1. Cliquez le bouton flottant **Marguerite** depuis un écran de l’application. Décrivez un besoin comme : « Je prépare une expérience de validation d’un programme d’analyse. Propose un projet, une tâche de protocole et les vérifications humaines. »
2. Lisez **Plan de Marguerite**, ses actions proposées et ce qu’elle attend encore de vous. Corrigez les informations manquantes dans la conversation si nécessaire.
3. Cliquez **Refuser** pour vérifier que les actions ne sont pas exécutées, ou **Valider et exécuter ces actions** si la proposition convient.
4. Ouvrez le projet et **Exécutions** pour vérifier les objets réellement créés et les éventuelles erreurs. Une proposition écrite seule n’est pas une exécution réussie.

**À constater.** Le consentement précède les créations ; chaque action a un résultat ou une erreur visible. Une réponse réelle de Marguerite sur un compte public évaluateur reste à confirmer après la connexion ChatGPT de ce compte.

### C. Travail doctoral guidé : de la question au livrable

**But.** Tester le même mécanisme sur les rôles **R1 doctorant**, **R2 jeune docteur** et **R3 directeur de thèse**. Passage propose 32 parcours avec questions métier, registre, preuves et décision humaine.

1. Ouvrez **Travaux de recherche**, choisissez votre projet, puis **Nouvelle tâche**. Sélectionnez une fiche R1, R2 ou R3 et saisissez son cadrage.
2. Cliquez **Ouvrir** sur la tâche. Lisez **Entrées attendues**, **Livrable**, **Validation** et les étapes du **Parcours de travail**.
3. Utilisez **Renseigner les questions**, **Ajouter une ligne**, **Joindre un fichier** ou **Créer un document** selon l’étape. Ajoutez des preuves puis cochez **Vérifier cette étape** avec une note fondée sur ce qui a vraiment été fait.
4. Si un agent réel est connecté, cliquez **Confier cette étape** ou **Demander un brouillon à un agent**. Relisez sa proposition et, si utile, **Reprendre dans un document**. Pour finir, cliquez **Valider ou demander une révision** : les questions, étapes, contrôles et livrable requis doivent être présents.

**À constater.** Le dossier conserve les versions, l’auteur des vérifications, le brouillon de l’agent et la décision humaine. Une étape physique ou réglementaire extérieure reste à effectuer par la personne responsable ; Passage n’en déduit pas l’accomplissement.

### D. Littérature et sources de thèses

**But.** Associer des notices réelles au raisonnement et rendre les affirmations contrôlables.

1. Dans **Bibliothèque**, parcourez les notices et leurs liens vers la source originale.
2. Dans **Projets & dialogue**, sélectionnez un projet puis **Sources du projet → Choisir les sources**. Filtrez par titre ou identifiant, cochez jusqu’à huit notices et cliquez **Enregistrer les sources**.
3. Ouvrez une tâche **Lire et classer la littérature** ou **Construire l’état de l’art**. Joignez une source, rédigez un document, puis utilisez **Ancrer un passage** pour relier une affirmation à une citation exacte d’une pièce textuelle.
4. Modifiez la version du document source et vérifiez que l’ancrage est signalé comme à revérifier ; confirmez uniquement après lecture de la version actuelle.

**À constater.** Les notices citent `theses.fr` et ne réhébergent pas les manuscrits. Le lien entre affirmation, extrait et version est visible. Une notice ou un résumé n’est pas une preuve de la validité scientifique de son contenu.

### E. Écriture de thèse et relecture

**But.** Rédiger une section traçable et soumettre une version définie à une relecture.

1. Créez une tâche **Rédiger thèse et articles** (`r1-writing`) ou **Relire manuscrits et articles** (`r3-manuscripts`). Renseignez les questions du dossier.
2. Cliquez **Créer une trame métier** ou **Créer un document** ; choisissez Markdown ou LaTeX et écrivez une section. Cliquez **Sauvegarder une version** après chaque modification substantielle.
3. Ajoutez un passage sourcé et, avec ChatGPT connecté, **Demander un brouillon à un agent** ou **Demander une correction du dernier brouillon**. Comparez le résultat à vos données et sources avant de le reprendre.
4. Déposez explicitement la version voulue comme livrable, invitez un relecteur si le parcours l’exige, puis utilisez **Valider ou demander une révision**.

**À constater.** Historique des versions, provenance des propositions, avis lié à une version et contrôles bloquants avant validation. Passage n’invente pas une source manquante comme citation vérifiée.

### F. Concevoir un protocole avec le tableau Excalidraw

**But.** Dessiner le processus scientifique, puis en faire un brouillon structuré que le chercheur peut corriger.

1. Créez une tâche **Concevoir une expérience** (`r1-experiment-design`) ou une autre tâche pertinente. Dans son dossier, cliquez **Créer un schéma**.
2. Donnez un titre et cliquez **Créer et dessiner**. Dans l’éditeur intégré, dessinez des **rectangles** pour les étapes, **losanges** pour les décisions et **flèches reliées** pour les transitions. Inscrivez les paramètres ou critères dans les formes.
3. Cliquez **Sauvegarder** dans l’éditeur, puis revenez à la tâche. Vous pouvez rouvrir le dessin et **Exporter .excalidraw**.
4. Après connexion de ChatGPT et ajout d’un agent direct à l’équipe du projet, cliquez **Formaliser avec un agent**. Choisissez **Protocole Markdown** ou **Brouillon de méthode Pipelex .mthds**, puis **Demander la formalisation**.

**À constater.** Le schéma est versionné ; l’agent doit signaler les transitions ou données ambiguës. Le texte obtenu reste un brouillon à relire. Le fichier `.mthds` n’est pas une méthode Pipelex déjà publiée.

### G. Réalisation d’expérience et cahier de laboratoire

**But.** Préparer l’essai, enregistrer ce qui a été réellement fait et séparer les faits des propositions de l’agent.

1. Créez **Réaliser une expérience** (`r1-experiment-run`) ou **Tenir le cahier de laboratoire** (`r1-notebook`). Indiquez protocole, échantillons, paramètres et livrable attendu.
2. Ajoutez une ligne de registre par essai ou observation avec **Ajouter une ligne** ; joignez un fichier de mesure ou une preuve avec **Joindre un fichier** ou **Ajouter une preuve**.
3. Pour les points de contrôle du dossier, utilisez **Attester avec une preuve** uniquement si l’action a été menée et si la pièce correspond. Le brouillon d’agent peut préparer une fiche, mais ne remplace pas la manipulation.
4. Vérifiez les étapes, déposez le livrable et demandez la décision finale.

**À constater.** Les relevés, versions, incidents et déclarations humaines restent dans le dossier. Une attestation indique qui la déclare ; Passage ne contrôle pas physiquement l’essai.

### H. Simulation ou programme scientifique

**But.** Transformer une demande vague en spécification, code ou protocole de calcul avec limites explicites.

1. Créez **Écrire ou adapter du code scientifique** (`r1-code`) ou, depuis **Projets & dialogue**, formulez une demande de simulation avec données, hypothèses, sorties et tests attendus.
2. Dans la tâche, cliquez **Créer un document** et choisissez le format **Python** ou **R**. Consignez les contraintes, entrées/sorties, exemples et tests de référence. Versionnez le texte avec **Sauvegarder une version**.
3. Demandez un brouillon à un agent connecté, puis relisez les hypothèses et confrontez le programme à des cas connus. Utilisez **Ajouter une preuve** ou **Joindre un fichier** pour les résultats d’un outil scientifique que vous avez réellement exécuté.
4. Faites valider la tâche seulement après avoir rempli ses questions, vérifié ses étapes et déposé le livrable.

**À constater.** Passage peut produire une spécification, un code et un dossier de contrôle. Il ne prétend pas avoir exécuté un code arbitraire ou validé un modèle biologique. Les exemples simplifiés indiquent qu’il s’agit de démonstrations, pas de résultats expérimentaux.

### I. Travail en équipe et protection entre comptes

**But.** Inviter des collaborateurs sans ouvrir automatiquement les projets ou conversations privés.

1. Créez deux comptes Passage avec des emails différents. Avec le premier, ouvrez **Mes équipes → Créer une équipe**, nommez-la et choisissez son type.
2. Cliquez **Inviter une personne**, saisissez l’email exact du second compte et préparez le lien. Transmettez ce lien vous-même : Passage n’envoie pas d’email. L’invitation expire après sept jours.
3. Connectez-vous avec le second compte et acceptez l’invitation. Vérifiez que le projet et ses conversations ne sont toujours pas visibles par défaut.
4. Avec le propriétaire, ouvrez la tâche voulue, cliquez **Inviter un relecteur**, saisissez l’email du second compte et choisissez **Relecteur** ou **Éditeur**. Reconnectez-vous au second compte pour retrouver cette tâche dans **Travaux partagés avec moi**.

**À constater.** Le partage porte sur une tâche précise. Un relecteur peut lire et donner son avis ; un éditeur peut contribuer aux étapes. L’accès à un autre projet ou agent privé reste refusé. Si une tâche dépend de livrables liés, partagez aussi ces tâches sources.

### J. Agents personnels et atelier du harnais

**But.** Composer un agent opérant avec cerveau, rôle, skill, contexte, mémoire et outils autorisés.

1. Sur une installation où vous êtes administrateur, ouvrez **Atelier des agents**. Ouvrez le harnais d’un agent actif ou créez votre spécialiste ; examinez mandat, modèle, outils et révision.
2. Choisissez ChatGPT via Codex comme cerveau et les seuls connecteurs nécessaires. N’ajoutez un modèle local que par choix délibéré. Cliquez **Tester** avec un compte ChatGPT relié, puis examinez **Exécutions**.
3. Pour un agent créé par Marguerite, demandez-lui explicitement le rôle, les entrées, sorties et validations souhaités ; approuvez le plan. Vérifiez ensuite sa fiche privée et sa place dans l’équipe du projet.

**À constater.** Une définition d’agent ou un badge actif ne prouve pas qu’un fournisseur est joignable : seule une exécution réussie le montre. L’atelier global est réservé à l’administrateur ; Marguerite peut préparer des spécialistes privés selon les droits du compte.

### K. Traces, refus et export du dossier

**But.** Vérifier la chaîne de responsabilité des actions et récupérer le travail.

1. Après un échange ou une délégation, ouvrez **Exécutions** pour voir le modèle déclaré, l’agent, les outils, le statut et les erreurs éventuelles.
2. Dans une tâche, inspectez l’historique des documents et des contrôles. Refusez un brouillon incorrect ou demandez une révision, puis comparez la nouvelle version.
3. Cliquez **Exporter le dossier** pour obtenir le Markdown de la tâche ; utilisez **Exporter le texte** sur un document et **Exporter .excalidraw** sur un schéma.

**À constater.** Le dossier exporté porte les pièces et décisions présentes. Une erreur de fournisseur reste une erreur visible ; elle n’est pas transformée en succès simulé.

### État réel des essais

| Parcours | Sur le site public au 27/09/2026 |
| --- | --- |
| Inscription, projet, tâche/fichier, schéma, invitation, séparation entre comptes et persistance après redéploiement | Vérifiés par recette réelle ou contrôles d’accès sur Render |
| Synthèse vocale Gradium avec quota de démonstration | Vérifiée avec un vrai fichier audio |
| ChatGPT par code d’appareil | Génération et renouvellement vérifiés ; connexion complète d’un compte évaluateur et réponse réelle de Marguerite encore à constater |
| Marguerite, brouillons d’agent, formalisation du dessin, Jinkō SDK | Contrats et tests automatisés disponibles ; réussite de bout en bout avec comptes externes personnels non attestée sur l’aperçu |
| Dust et Pipelex MCP | Connexion personnelle et droits requis ; aucune connexion partagée n’est fournie aux évaluateurs |
| Expérience physique, validation scientifique et publication Pipelex | Réservées aux personnes ou services compétents ; Passage en prépare le dossier |

Pour une recette reproductible, utilisez des données non confidentielles et notez la date, le compte de test, l’URL, la tâche, le résultat observé et toute erreur. Les critères détaillés des 32 tâches figurent dans [PARCOURS_R1_R3.md](PARCOURS_R1_R3.md).

## Limites et périmètre du hackathon

Le projet doit être évalué sur ce qu’il exécute réellement. Les cas ci-dessous séparent les fonctions vérifiées, les intégrations partielles et ce qui n’a pas été développé pendant le hackathon.

| État | Fonction | Limite concrète pour le testeur |
| --- | --- | --- |
| Développé et vérifié sur le site public | Inscription par email, projets personnels, tâches et documents, schémas, invitation et partage explicite, isolation entre comptes, persistance Turso | Le site Render Free peut être lent au premier réveil ; aucune donnée sensible ne doit être utilisée pour la démo. |
| Développé et vérifié sur le site public | Synthèse vocale Gradium via la clé de démonstration | L’écoute dépend du navigateur ; la transcription micro et la conversation vocale doivent être essayées sur l’appareil du testeur. Le quota est limité. |
| Développé mais recette publique incomplète | Connexion ChatGPT personnelle via code d’appareil et Marguerite | Le code et son renouvellement fonctionnent. La validation OpenAI complète, la restauration après redémarrage et une réponse réelle sur un compte évaluateur ne sont pas encore attestées de bout en bout. Si la connexion échoue, aucune réponse fictive n’est substituée. |
| Développé mais dépend des comptes du testeur | Dust et Pipelex par OAuth MCP, catalogue d’outils, autorisations et validations avant écritures | Les comptes MCP sont personnels. Aucune connexion commune ni clé de moteur API Dust/Pipelex n’est mise à disposition sur l’aperçu. Le brouillon `.mthds` n’est ni publié ni exécuté automatiquement. |
| Développé partiellement | Jinkō SDK dans un agent Passage | Les lectures et contrôles sont testés avec des réponses simulées. Un vrai projet et une clé Jinkō sont nécessaires ; aucun essai n’a été lancé ni modifié. |
| Développé partiellement | Marguerite et Super Skill Facilitator | La doctrine, le plan avec approbation et la création d’un spécialiste privé sont implémentés. Leur enchaînement complet avec le compte ChatGPT d’un évaluateur et tous les connecteurs externes reste à vérifier en conditions réelles. |
| Développé partiellement | Recherche de thèses | Le corpus initial contient des notices et liens vers les sources, pas tous les manuscrits ni une indexation mondiale exhaustive. L’import continu, la déduplication à grande échelle et les droits de réutilisation des textes complets restent à traiter. |
| Préparé, non déployé sur l’aperçu | Latitude auto-hébergé | La stratégie et la configuration sont documentées ; aucun service Latitude opérationnel n’est fourni aux évaluateurs. |
| Non développé pour cette remise | Connexion ou création de compte Passage par ChatGPT, récupération de mot de passe, envoi automatique d’invitations par email | Utilisez l’inscription email/mot de passe et transmettez manuellement les liens d’invitation. La connexion Google n’apparaît que si un client OAuth est configuré ; elle est absente de l’aperçu. |
| Hors du périmètre de Passage | Exécution d’une expérience physique, validation d’une simulation scientifique, publication d’une méthode Pipelex, exécution de code arbitraire sans environnement contrôlé | Passage aide à cadrer, écrire, vérifier et conserver les preuves ; le chercheur ou un service externe compétent réalise et valide ces opérations. |

La démonstration vidéo est **animée et illustrée** : ses personnages, schémas et dialogues montrent l’usage visé. Elle ne doit pas être interprétée comme une preuve d’exécution en direct de Marguerite, Dust, Pipelex ou Jinkō. Les vérifications techniques et les correctifs de l’audit sont décrits dans [docs/AUDIT_REMEDIATION.md](docs/AUDIT_REMEDIATION.md).

## Ce qui fonctionne

| Parcours | Résultat dans Passage | Contrôle humain |
| --- | --- | --- |
| Recherche documentaire | Notices de thèses avec source et statut ; recherche et comparaison | Vérifier le manuscrit et les affirmations |
| Travaux doctoraux | 32 tâches R1–R3, documents versionnés, preuves, registres, exports | Valider les étapes, protocoles et livrables |
| Agents | Cerveau ChatGPT via Codex par défaut ; harnais versionné, spécialités et outils | Approuver le plan et relire les propositions |
| Marguerite | Conversation personnelle ; création de projets, tâches, schémas et spécialistes après validation | Accepter ou refuser chaque plan |
| Voix | Transcription et synthèse Gradium en dialogue continu | Autoriser le micro et vérifier la transcription |
| Schémas | Dessin local basé sur Excalidraw ; brouillon de protocole ou `.mthds` | Relire et publier la méthode séparément |
| Équipes | Invitation par lien personnel, annuaire et partage explicite des tâches | Accepter l’invitation ; choisir les dossiers partagés |
| Jinkō SDK | Lectures de modèles, états, diagnostics et résultats par un agent personnel ChatGPT | Connecter le projet ; relire les conclusions |
| Dust / Pipelex | Comptes MCP OAuth, catalogue d’outils accordés et appels contrôlés | Accorder les outils et approuver les écritures |

**Limites visibles :** Passage prépare des expériences, simulations et programmes, mais ne réalise pas une manipulation physique ni ne valide un résultat scientifique. Un export `.mthds` n’est pas une méthode Pipelex publiée. Les API de moteur Dust et Pipelex demandent des clés distinctes de leurs connexions MCP OAuth. La clé API OpenAI est facultative et facturée séparément de l’abonnement ChatGPT. L’adaptateur Jinkō utilise le SDK officiel 1.12.1 ; les tests automatisés utilisent des réponses contrôlées. Un essai sur un vrai projet Jinkō reste à effectuer avec une clé fournie par son propriétaire. Le lancement et la modification d’essais Jinkō ne sont pas encore proposés.

**État des fournisseurs sur l’aperçu :** la voix Gradium de démonstration est active. ChatGPT, Dust et Pipelex se relient au compte de chaque utilisateur. L’accès Jinkō réel n’est pas configuré sur l’aperçu. La connexion Google à Passage attend un client OAuth. Le dépôt ne présente aucune exécution non vérifiée comme un résultat obtenu.

## Lancer localement

Prérequis : Python 3.12 recommandé (comme Render), Node.js et le CLI officiel Codex si vous souhaitez utiliser votre compte ChatGPT. La consultation des écrans et des données initiales reste possible sans fournisseur LLM. Utilisez un environnement virtuel propre : le SDK Jinkō récent et certains outils CLI Pipelex ont des contraintes de dépendances distinctes ; les connexions Pipelex de Passage passent par HTTP/MCP et ne nécessitent pas ce CLI.

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
                    ├── Jinkō SDK personnel (lectures choisies par l’agent)
                    ├── Excalidraw local → protocole / brouillon .mthds
                    └── SQLite locale ou Turso distant (comptes, projets, preuves, historique)
```

Une exécution garde le modèle déclaré, la révision de l’agent, les données autorisées, les traces et les erreurs. Les projets et conversations sont liés au compte. Un agent personnel créé par Marguerite reste privé à son propriétaire. Les outils externes ne sont disponibles qu’après connexion et autorisation ; une écriture demande une validation supplémentaire.

Les paramètres optionnels sont documentés dans [.env.example](.env.example). Ne mettez jamais `.env`, clés, bases SQLite ou données de recherche privées dans le dépôt.

## Aperçu Render

[render.yaml](render.yaml) décrit un service Docker **Free** avec `/api/health` comme sonde et `PASSAGE_PUBLIC_SIGNUP=1`. Configurez `TURSO_DATABASE_URL` (format `libsql://` pour la base créée sur Turso Cloud), `TURSO_AUTH_TOKEN` et une clé Fernet stable `PASSAGE_ENCRYPTION_KEY` dans les variables privées Render. Le serveur refuse de démarrer sans base distante. Comptes, projets, notices, conversations, connexions chiffrées et fichiers de travail sont conservés dans Turso ; le disque Render ne sert que de cache. Chaque évaluateur crée son propre compte et relie ses propres fournisseurs. Les identifiants de l’installation locale ne sont pas transférés. En déploiement, ChatGPT se connecte par code à valider sur la page officielle OpenAI. Son cache d’authentification personnel est sauvegardé chiffré dans Turso puis restauré après perte du cache serveur ; la déconnexion supprime cette sauvegarde. Une expiration ou révocation par OpenAI peut toujours demander une reconnexion. Le parcours par code peut devoir être activé dans les paramètres de sécurité ChatGPT ([documentation officielle](https://learn.chatgpt.com/docs/auth)). La restauration est vérifiée en test ; la recette réelle sur Render reste à effectuer.

Pour produire la clé Fernet, lancez `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` et copiez le résultat uniquement dans les variables privées Render. Gardez cette valeur : en la changeant, les connexions OAuth déjà enregistrées ne seront plus déchiffrables. Les notices de thèses stockent des métadonnées et des liens vers la source ; le projet ne réhéberge pas tous les manuscrits.

La connexion Google est optionnelle : elle n’apparaît que si `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` sont configurés avec l’URL de retour `/api/auth/google/callback`. L’inscription par email et mot de passe fonctionne sans Google. L’aperçu ne dispose pas encore de récupération de mot de passe. Dans **Mes équipes**, créez une équipe puis préparez un lien d’invitation valable sept jours. Transmettez-le vous-même au destinataire : aucun email automatique n’est envoyé. L’acceptation exige un compte avec l’adresse invitée. Une équipe ne donne aucun accès implicite aux projets ou conversations ; partagez les tâches individuellement depuis leur dossier.

## Connecter un agent Jinkō

Dans **Connexions → Mon projet Jinkō**, saisissez la clé API et l’identifiant du projet. Passage vérifie leur association puis conserve la clé chiffrée pour votre seul compte. Reliez aussi ChatGPT, puis cliquez **Créer mon agent Jinkō** : le harnais applique les six étapes du Facilitator et, si un projet Passage est sélectionné, rejoint son équipe. L’agent peut choisir jusqu’à trois lectures SDK par appel de raisonnement. Les observations sont transmises à son cerveau et les opérations apparaissent dans les traces. Aucun essai Jinkō n’est créé, modifié ou lancé par ces outils.

## Documents utiles

- [Spécification fonctionnelle](SPEC_FONCTIONNELLE.md)
- [Parcours des 32 tâches R1–R3](PARCOURS_R1_R3.md)
- [Usages des personas R1–R5](USAGES_PASSAGE_R1_R5.md)
- [Scénario vidéo et narration](DEMO.md)
- [Dossier Word pour le jury](demo/Passage_dossier_hackathon.docx)
- [Première vidéo de 77 secondes avec voix Gradium](demo/Passage_demo_76s.mp4)
- [Latitude auto-hébergé](LATITUDE_SELFHOST.md)
- [Correctifs et limites de l’audit](docs/AUDIT_REMEDIATION.md)

**Licences et provenance :** l’éditeur de dessin embarque Excalidraw sous licence MIT, conservée dans [LICENSE-EXCALIDRAW.txt](passage/static/diagram/LICENSE-EXCALIDRAW.txt). Les notices initiales renvoient à leurs sources publiques. Oscar-AI reste un projet antérieur distinct.
