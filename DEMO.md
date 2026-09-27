# Vidéo de candidature Passage — 2 minutes maximum

## Version actuelle : animation en collage, 118,9 secondes

La [vidéo finale en collage](demo/Passage_demo_collage.mp4) suit le scientifique narrateur et ses échanges avec Marguerite. Des éléments de papier découpé montrent la circulation du travail : besoin → plan soumis à approbation → lecteur de sources → agent protocole → agent code → retour au coordinateur → preuves → décision humaine. Une dernière scène ouvre sur les autres usages : direction de thèse et relecture, laboratoire et coordination, ingénierie et tests, entreprise et transfert. Les outils et leurs droits apparaissent dans le dossier partagé. Les voix Gradium sont distinctes : `l2nzlZ4fcaobSwPk` pour le scientifique et `FXxJ9mANRq6BCTX5` pour Marguerite. Le montage suit directement les neuf clips vocaux et leurs horodatages pour aligner le personnage et la voix à chaque scène.

Le script exact est dans [demo/dialogue-v2.json](demo/dialogue-v2.json), les temps dans [demo/dialogue_timing-v2.json](demo/dialogue_timing-v2.json), et le montage reproductible dans [demo/build_video_collage.py](demo/build_video_collage.py). Il s’agit d’une animation pédagogique, pas d’une capture d’exécution d’un fournisseur tiers. La version précédente reste archivée dans [demo/Passage_demo.mp4](demo/Passage_demo.mp4).

## Montage livré : dialogue illustré, 98,57 secondes

La [vidéo MP4](demo/Passage_demo.mp4) met en scène un scientifique en blouse, cheveux en bataille et barbe de quelques jours, face à Marguerite. Leurs répliques alternent sur huit scènes. La voix du scientifique utilise l’identifiant Gradium `l2nzlZ4fcaobSwPk` choisi par l’auteur ; Marguerite reprend la voix Gradium `FXxJ9mANRq6BCTX5` de Passage. Les personnages originaux sont animés par un léger mouvement vertical. Le montage a été décodé et sa durée mesurée à 1 min 38,57 s. Le dialogue exact est dans [demo/dialogue.json](demo/dialogue.json) ; les durées de chaque réplique sont dans [demo/dialogue_timing.json](demo/dialogue_timing.json).

Il s’agit d’une **présentation illustrée**, sans capture d’une exécution externe réussie. Les scènes Dust, Pipelex et Jinkō expliquent les connexions et leurs conditions. Les images et les dialogues ne prétendent pas montrer une expérience scientifique exécutée ni une réponse en direct d’un fournisseur non vérifié.

**Angle :** suivre un doctorant qui passe d’une question de recherche à un travail vérifiable avec une équipe d’agents. Montrer une action réellement disponible, sa validation et sa trace. La voix off est générée avec Gradium ; les captures montrent Passage, sans clé ni donnée privée.

| Temps cible | Écran | Idée à transmettre |
| --- | --- | --- |
| 0–8 s | Titre Passage, inscription Doctorant | À qui sert Passage et pour quel problème |
| 8–20 s | Projet et catalogue des travaux R1–R3 | Un projet se décompose en tâches scientifiques concrètes |
| 20–33 s | Marguerite : demande préparée, plan visible, bouton de validation | L’agent dialogue, propose, puis attend l’accord humain |
| 33–46 s | Dossier d’une tâche : questions, pièces, étapes et brouillon d’agent | Les travaux et leurs preuves restent consultables |
| 46–57 s | Schéma Excalidraw, formalisation en brouillon de protocole | Du dessin à une méthode révisable |
| 57–69 s | Atelier : cerveau ChatGPT, harnais Super Skill Creator V4 | Un agent est configurable et contrôlé avant usage |
| 69–81 s | Connexions : Gradium, Dust et Pipelex MCP ; retour au projet | Les partenaires enrichissent le travail dans un même espace |

**Durée visée :** 81 secondes, générique compris, pour une narration Gradium mesurée à 75,9 secondes. Prévoir des captures montées et de légers zooms ; ne pas attendre un appel LLM pendant l’enregistrement. Si un résultat est déjà préparé, afficher sa date et son état réel. Ne pas montrer Jinkō comme intégré avant un essai SDK réussi. Ne pas affirmer que Dust ou Pipelex exécute un agent à partir de Passage si seule la connexion MCP est démontrée.

Une première version illustrée, [demo/Passage_demo_76s.mp4](demo/Passage_demo_76s.mp4), est disponible. Elle dure 76,97 secondes, contient la narration Gradium réelle et sert de base au montage final avec des captures du service publié.

## Voix off

Le texte exact est conservé dans [demo/voix-off.txt](demo/voix-off.txt). La voix Gradium est enregistrée dans `demo/voix-off.wav` (75,9 secondes). Ajuster le montage à l’audio, puis exporter un MP4 de moins de deux minutes. Vérifier la lecture sonore avant l’envoi.

## Contrôles avant dépôt

1. Refaire le parcours dans l’aperçu public avec un compte évaluateur neuf.
2. Masquer clés, adresses privées et données confidentielles ; utiliser un projet de démonstration.
3. Vérifier les badges « réel »/« simulation » et l’état des exécutions avant d’enregistrer.
4. Ajouter l’URL publique de la vidéo et du dépôt dans le formulaire ; relire chaque réponse avant soumission.

## Proposition à valider pour la vidéo finale — 116 secondes

**Fil conducteur :** une doctorante veut concevoir un protocole pour tester un programme d’analyse de données de recherche. Passage doit transformer cette demande en travail contrôlable, pas annoncer un résultat scientifique sans preuve. Filmer le vrai site publié, utiliser des données de démonstration et monter les temps d’attente. Les sorties d’agents montrées doivent provenir d’une exécution réelle datée ; si la connexion personnelle ChatGPT n’est pas prête, filmer seulement les écrans dont le fonctionnement est vérifié. La voix choisie est `l2nzlZ4fcaobSwPk` dans Gradium. Cette proposition n’est pas encore validée par l’auteur.

| Temps | Écran / action à filmer | Voix proposée |
| --- | --- | --- |
| 0–12 s | Passage, doctorante, demande précise dans Marguerite. | « Je prépare une thèse et je dois tester un programme qui analyse mes données. Par où commencer, et comment garder des preuves de ce que j’ai vérifié ? » |
| 12–29 s | Marguerite restitue le besoin et propose un plan ; gros plan sur **Valider et exécuter**. | « Marguerite ne prétend pas que le programme fonctionne déjà. Elle découpe ma demande : cadrer les données, définir le protocole, préparer les tests et garder une trace des décisions. Je vois chaque action avant de l’autoriser. » |
| 29–46 s | Validation, projet et tâche R1 créés ; ouvrir le dossier. | « J’approuve. Passage organise le projet et ouvre un travail doctoral avec les questions à résoudre, les pièces attendues et les contrôles qui restent à ma charge. » |
| 46–63 s | Atelier : agent spécialisé, cerveau ChatGPT, harnais, doctrine Super Skill Facilitator ; montrer le refus d’une définition incomplète seulement si recette obtenue. | « Pour ce travail, Marguerite peut préparer un agent spécialisé. Son cerveau est mon compte ChatGPT ; son harnais décrit mission, sources, mémoire, compétences et outils. Sa définition est versionnée et contrôlée avant usage. » |
| 63–82 s | Dessin du protocole dans l’éditeur Excalidraw ; formalisation en brouillon `.mthds`. | « Je dessine les étapes du test. Passage conserve le schéma et aide à le formaliser en protocole ou en brouillon de méthode Pipelex. Je relis le document avant toute publication ou exécution externe. » |
| 82–101 s | Dossier : source, brouillon, version, preuve, point de validation ; si possible résultat d’une action réelle. | « Le résultat reste dans le dossier, avec ses sources, ses versions et ce qui manque encore. L’agent prépare ; moi, je vérifie les données, décide si le test est valable et valide le livrable. » |
| 101–116 s | Connexions et code : voix Gradium active, MCP Dust/Pipelex, adaptateur Jinkō, test d’isolation des comptes, lien GitHub public. | « Gradium donne la voix à Passage. Dust et Pipelex enrichissent les outils avec des autorisations explicites ; le SDK Jinkō est prévu pour lire un projet connecté. Le code, les tests et leurs limites sont publics. Essayez Passage avec votre propre compte. » |

**Montage :** durée cible 116 s, deux secondes de marge ; la narration doit être régénérée avec la voix choisie après validation du texte. Montrer au moins une transition réelle plan → accord → action → preuve. Inscrire à l’image « brouillon à vérifier » sur le `.mthds` et « compte Jinkō réel à connecter » sur le SDK tant que sa recette n’est pas faite. Ne pas simuler un succès de Marguerite, de Dust, de Pipelex ou de Jinkō. L’ancienne vidéo illustrée de 77 s reste une maquette de présentation, pas la preuve de ce parcours.
