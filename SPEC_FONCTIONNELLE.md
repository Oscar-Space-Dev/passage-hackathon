# Passage — spécification fonctionnelle du POC

Version 2.2 — 26 septembre 2026. Nom provisoire. Auteur du projet : Sébastien.

## Marguerite · agent transversal

Marguerite est accessible depuis chaque écran du compte local. Sa conversation et une mémoire courte de ce que l'utilisateur a explicitement dit de son activité, de ses objectifs et de son usage de Passage sont conservées par utilisateur. Le projet sélectionné est le contexte prioritaire. Marguerite observe ses tâches, agents actifs et spécialités, sources, livrables, validations en attente et exécutions récentes. Elle reçoit un index des notices accessibles et les résumés les plus pertinents pour la demande, ainsi que les schémas des outils MCP réellement connectés et autorisés. Une question simple reçoit une réponse sans mutation.

Le panneau propose une conversation vocale continue. Gradium assure la reconnaissance et la synthèse ; le compte ChatGPT connecté à Passage traite chaque tour avec le même cerveau et le même historique que le dialogue textuel de Marguerite. Les tours reconnus sont enregistrés séparément. Lorsqu'un plan est proposé, Marguerite annonce qu'il est à relire, termine le dialogue vocal après la réponse et affiche la validation dans son panneau. Une réponse parlée peut être rejouée depuis sa transcription. L'utilisateur contrôle l'ouverture et l'arrêt du microphone.

Pour une demande de travail, elle prépare au plus dix actions ordonnées avec paramètres visibles et les étapes réservées à l'humain. Son catalogue exécutable couvre projet, objectif, équipe, sources, tâche R1–R3, note de tâche, délégation, schéma de processus vide lié à une tâche, formalisation d'un schéma dessiné en protocole ou brouillon Pipelex, rapport de spécialiste, brouillon de recherche, calcul thermique déterministe, outil MCP accordé et mission de coordination. Le plan privilégie une tâche existante pertinente et un agent prêt de l'équipe. L'accès à chaque projet, tâche, notice, agent et outil, ainsi que les contrats de paramètres, sont revalidés côté serveur avant de montrer le plan et avant son approbation. Un plan invalide est corrigé par un second tour du modèle ; si cela échoue, aucune action n'est préparée et l'utilisateur reçoit le blocage explicite.

L'approbation du plan est nécessaire avant toute mutation. Chaque résultat est journalisé avec son identifiant ; un échec arrête les actions suivantes. Une délégation, mission ou formalisation de schéma lancée reste « en cours » jusqu'à l'état terminal de son run, et un brouillon, dessin préparé ou calcul terminé reste « à relire » lorsque le contrôle humain est requis. Le plan ne peut pas être approuvé deux fois. Les écritures MCP conservent leur validation propre, indépendante de celle du plan ; Marguerite ne confirme pas une manipulation physique, un résultat scientifique, un partage confidentiel ni une publication à la place de l'utilisateur. Le dialogue textuel reste disponible pendant une exécution ; un second plan d'actions n'est pas lancé avant sa fin.

**Registres métier R1–R3 :** les 32 définitions contiennent un registre répétable avec titre et quatre colonnes propres à la tâche. Un utilisateur ou éditeur peut créer jusqu'à 100 lignes actives, les réviser, archiver et rétablir. La première colonne identifie la ligne ; les autres peuvent rester inconnues pendant le travail. Chaque version est conservée avec auteur et date, et peut référencer une preuve humaine ou un fichier de la même tâche. Les lignes actives figurent dans la trame du livrable et, par extraits bornés, dans le contexte de l'agent ; toutes les versions figurent dans l'export. L'agent peut retourner au plus douze lignes proposées sous forme de quatre textes ordonnés ; l'utilisateur les relit, les corrige et les enregistre explicitement avec lien de provenance. Les lignes de registre ne certifient aucune action externe et ne remplacent pas les points de contrôle.

**Chaîne des travaux R1–R3 :** le propriétaire peut sélectionner jusqu'à six tâches achevées du même projet comme sources du travail courant. Le lien conserve l'identifiant du livrable accepté et la révision source ; les cycles et liens entre projets sont refusés. Le dossier et son export montrent l'état actuel ou périmé du lien. L'agent reçoit l'extrait borné de la pièce ou de la version documentaire acceptée, son empreinte et ses identifiants. Une source confidentielle doit posséder son contrôle d'usage par agent ; un lien changé pendant l'exécution fait échouer le brouillon. Toute modification de source rouvre à la lecture une tâche aval achevée et bloque sa validation ou délégation tant que le lien n'est pas actualisé. L'accès d'un invité à la tâche aval exige aussi son accès à toutes les sources liées, pour éviter qu'une réponse d'agent ne lui révèle indirectement une source privée.

**Questions de travail R1–R3 :** chacun des 32 types comporte trois questions métier. L'utilisateur ou un éditeur invité peut y répondre progressivement ; la sauvegarde contrôle la révision pour éviter d'écraser une modification concurrente et conserve une version immuable avec auteur et date. Les réponses courantes et leur historique figurent dans le dossier et l'export ; les réponses courantes cadrent la proposition de l'agent. Une réponse vide reste visible comme information manquante ; elle n'est pas inventée par Passage. Une modification rouvre un travail validé et périme les attestations concernées.

**Production du livrable :** une trame Markdown par tâche reprend le livrable attendu, les trois questions, les quatre étapes, les preuves et la décision réservée à l'humain. L'utilisateur peut la créer comme document ou livrable direct. Le schéma de sortie de l'agent possède trois champs distincts de propositions, correspondant aux questions ; les fournisseurs locaux qui omettent ces champs laissent les propositions vides. L'utilisateur peut relire, modifier et reprendre ces propositions dans ses réponses, avec un lien de provenance vers le brouillon. La clôture exige des réponses non vides aux trois questions ; une réponse « inconnue » ou « non applicable » doit être formulée explicitement et reste soumise à la relecture humaine. Ces réponses ne prouvent aucun fait externe.

**Points de contrôle R1–R3 :** le catalogue associe maintenant des attestations obligatoires aux tâches impliquant expérience physique, tests exécutés, traitement de données, accord de diffusion, dépôt ou transmission, passation, candidature, financement, séance de jury, rapport de revue et cours donné. Le propriétaire déclare une date, une portée et une preuve humaine ou un fichier de la tâche. Les attestations sont conservées avec auteur et empreinte de la révision du dossier ; toute modification du matériau invalide leur usage pour la clôture. Pour les dossiers de jury, revue et divulgation, une attestation distincte est exigée avant une délégation ou formalisation par agent. Le coordinateur ne reçoit pas le titre libre ni la dernière pièce de ces tâches tant que le contrôle manque. Un utilisateur peut toujours travailler sans agent. Ces attestations ne certifient pas les faits externes.

**Schémas et observabilité ajoutés :** chaque tâche R1–R3 peut contenir jusqu'à 20 schémas Excalidraw locaux de 300 éléments et 750 Ko chacun. Une sauvegarde crée une version immuable avec empreinte ; l'éditeur et le relecteur suivent les droits de la tâche. Un graphe déterministe extrait les étapes, décisions et flèches reliées ; les éléments sans libellé ou lien produisent des avertissements. Un agent direct de l'équipe peut formaliser une version en protocole Markdown ou en méthode Pipelex `.mthds` brouillon, avec traçabilité vers le schéma. Le document et sa validation restent sous contrôle humain. L'export optionnel vers Latitude auto-hébergé envoie des traces OTLP d'exécution avec métadonnées techniques seulement. L'instance Latitude n'a pas été lancée sur cette machine dépourvue de Docker ; voir `LATITUDE_SELFHOST.md`.

**Analyse descriptive des données :** dans une tâche contenant un CSV/TSV complet et extractible, l'utilisateur choisit une colonne numérique et éventuellement une colonne de groupes. Passage calcule localement, pour 100 000 lignes et 20 groupes maximum, les effectifs, moyennes, médianes, extrêmes et écarts-types d'échantillon. Il conserve les colonnes, l'empreinte du fichier et les lignes exclues dans une pièce calculée, liée à la révision de la tâche. Un agent peut demander ce calcul dans sa première réponse structurée ; Passage vérifie le fichier et les colonnes, exécute le calcul sans lancer de code utilisateur et demande ensuite à l'agent une proposition finale fondée sur le résultat. Ce service n'est pas une inférence statistique ni une validation scientifique des données.

**Passages sourcés R1–R3 :** un utilisateur ou éditeur peut relier jusqu'à 100 affirmations actives à des passages exacts de fichiers textuels ou de documents de la même tâche. Passage vérifie la présence du passage dans le texte extrait, conserve version et SHA-256, puis indique si la source est toujours actuelle. Un ancrage périmé doit être renouvelé sur la nouvelle version ou archivé avant la validation de la tâche. L'export conserve les ancrages actifs et archivés. Les agents reçoivent un extrait borné des ancrages actifs et peuvent proposer jusqu'à douze passages figurant dans les extraits de sources effectivement transmis ; les propositions absentes sont écartées avec une limite explicite. L'utilisateur relit et adopte une proposition explicitement, avec contrôle renouvelé du texte et de la version. Une correspondance textuelle n'établit pas la validité de l'interprétation scientifique.

**Révision itérative des agents :** pour chaque tâche R1–R3, le propriétaire peut désigner le dernier brouillon d'agent, saisir une correction précise et choisir un agent direct actif compatible de l'équipe. La demande contrôle la révision courante du dossier. L'agent reçoit explicitement le brouillon visé et le retour humain en plus des pièces et registres autorisés ; sa réponse distingue le nouveau contenu, un résumé des changements et les limites. Passage conserve le lien entre les deux brouillons, la consigne et une différence textuelle calculée localement, affichée et exportée. La validation demeure humaine. Une tâche déjà achevée doit d'abord être rouverte pour éviter de conserver simultanément un livrable approuvé et une délégation en cours.

**Parcours de chaque étape :** le catalogue R1–R3 contient maintenant un contrat explicite pour les 128 étapes des 32 tâches : action humaine, aide de l'agent, pièce attendue, outil Passage à ouvrir et signalement d'un acte extérieur. L'interface affiche ces éléments sur chaque étape et permet de viser cette étape lors d'une délégation ; un agent ne reçoit pas de mandat d'exécuter l'action extérieure. Le coordinateur peut transmettre un numéro d'étape dans son action `work`. Le brouillon, l'export et la trame conservent la portée ciblée et les critères de vérification. Le document généré `PARCOURS_R1_R3.md` donne le parcours fonctionnel complet, sans ordre de livraison ni roadmap.

**Orientation corrigée après retour utilisateur :** l'expérience principale est le pilotage d'une équipe d'agents par objectif de projet, avec coordination et réévaluation autonomes. La section 11 précise cette exigence ; la section 12 décrit le périmètre désormais implémenté et ses limites de recette.

## 1. Objet et décisions

Passage aide le doctorant à faire avancer son travail de recherche : exploiter ses sources, structurer la rédaction, préparer des expériences, définir des simulations et concevoir des logiciels scientifiques dédiés. Le projet de recherche rassemble objectifs, sources, données, hypothèses, échanges et livrables ; une équipe d’agents coordonnée l’aide à progresser avec des résultats traçables et révisables par le doctorant. La valorisation des travaux en laboratoire et leur rapprochement avec les besoins industriels restent un débouché complémentaire du produit.

Le POC conserve le parcours de démonstration existant, de l'import d'une vraie thèse jusqu'à une proposition acceptée dans un programme de R&D. Ses spécialisations livrées sont aujourd’hui surtout orientées vers la lecture, l’opportunité, le rapprochement et l’incorporation. L’assistance de recherche doctorale est l’orientation produit retenue ; les exemples de demandes dans l’interface amorcent ce parcours sans prétendre que des expériences physiques, des simulations exécutables ou des logiciels scientifiques sont déjà réalisés et validés par le POC.

Cette spécification s'appuie sur les trois documents fournis (cadrage du 25/09, personas et proposition de roadmap) et les décisions de cette conversation. La demande du 25/09 de rédiger la spec et réaliser le POC autorise la construction. Le calendrier de la roadmap antérieure n'est pas une obligation de cette spec. Le dépôt public et la vidéo de candidature relèvent de la soumission au hackathon ; le POC fournit les instructions et le scénario pour la préparer.

Décisions acquises : notre éditeur est la source de vérité des agents ; Dust est un exécuteur facultatif ; Pipelex représente les méthodes exécutables du harnais. L'inspiration fonctionnelle vient d'Oscar-AI, projet préexistant à déclarer. Aucun code de son éditeur n'est copié. L'application reste autonome et utilise Oscar uniquement pour lire les programmes et déposer une proposition acceptée.

## 2. Utilisateurs et responsabilités

| Profil du POC | Actions | Limites |
|---|---|---|
| Laboratoire / valorisation | Configurer le laboratoire, importer, lancer la lecture, consulter les dossiers et les indicateurs | Les conclusions des agents restent révisables |
| Directeur de thèse | Rendre visible ou retirer une fiche | La publication est toujours une action humaine tracée |
| Doctorant | Piloter un projet de recherche, travailler avec une équipe d’agents sur ses sources, sa rédaction, ses protocoles, simulations et logiciels ; consulter sa fiche, corriger le résumé, voir consultations et propositions | Les conclusions, méthodes et livrables doivent rester vérifiables et révisables ; les expériences et calculs exigent leurs outils et données réels |
| Entreprise / ingénieur | Décrire un besoin, lire les résultats, demander un dossier et proposer une thèse | Accès limité aux fiches visibles |
| Chef de programme | Accepter ou refuser une proposition | Seule l'acceptation produit une note |
| Administrateur du POC | Créer, modifier, versionner et tester les agents et leurs connexions | Un agent ne peut publier ni accepter à sa place |

Les comptes locaux portent un rôle contrôlé côté serveur. Le premier compte est administrateur ; les suivants sont entreprise jusqu'à modification par l'administrateur. Seul l'administrateur peut changer de profil dans le sélecteur. Le POC reste une installation locale avec un laboratoire partagé et une entreprise fictive de scénario. Les projets restent privés au propriétaire ; il peut partager une tâche précise avec un compte local comme contributeur ou relecteur sans donner accès au projet entier. Les notices d'autres laboratoires ne sont jamais réattribuées au LRCS.

Chaque compte peut fournir sa propre clé Gradium et sa voix pour les commandes vocales. Passage les conserve chiffrées et les utilise pour les appels STT/TTS de ce compte ; sans configuration personnelle, la clé d'installation reste disponible. L'interface n'affiche jamais la valeur du secret et le compte peut le retirer.

## 3. Parcours démontré

1. Le laboratoire LRCS (Amiens) importe ses thèses depuis theses.fr. Le nombre est celui renvoyé au moment de l'import, et non une constante de 61.
2. Le Lecteur prépare une fiche à partir du titre, des résumés et mots-clés. Le niveau de documentation est visible. Une thèse en cours ne reçoit pas des résultats supposés acquis.
3. Le directeur vérifie la fiche puis la rend visible. Le doctorant peut corriger son résumé.
4. L'ingénieur décrit : « En charge rapide, nos cellules dépassent 45 °C et vieillissent deux fois plus vite. On cherche à limiter l'échauffement sans alourdir le pack. »
5. Le Rapprochement classe les fiches publiées et explique les correspondances, les limites et les rejets. Le classement réel dépend du modèle et des sources ; aucun identifiant de thèse ne force le rang.
6. L'ingénieur ouvre une fiche et obtient un dossier d'incorporation. Une consultation est comptée une fois par entreprise et par thèse.
7. Il propose le travail au programme « Pack 2027 — charge rapide en 20 minutes ». Le chef de programme accepte ou refuse. Une note n'est créée qu'après acceptation.
8. Le doctorant retrouve ce signal. Le laboratoire produit un dossier d'opportunité, y compris une conclusion négative ou « à approfondir ».

Les trois cas de référence sont Che Daud (2014DIJOS078, comportement thermique), Caroline Mir (2019PSLEC037, sulfures complexes) et Félix Bourseau (impression 3D d'une batterie polymère, identifiant découvert à l'import). La première apporte un point de départ pertinent sans prouver une performance en charge rapide sur vélo. La seconde est un rapprochement faible ; la troisième doit pouvoir être écartée. Les métadonnées et résumés viennent de la source publique, conservée avec date de collecte.

## 4. Navigation et écrans

### F01 — Vue d'ensemble

Afficher les thèses du laboratoire, les fiches visibles, les consultations d'entreprises, les dossiers produits et les propositions en attente. Fournir un accès aux derniers événements et au parcours de démo. Les compteurs proviennent de la base. Un bandeau distingue démonstration et appels réels, ainsi que l'état Oscar.

### F02 — Laboratoire

Champs : nom, sigle, ville, requête de recherche. L'import affiche son avancement, le nombre trouvé, le nombre retenu pour le laboratoire, les ajouts, les mises à jour et les erreurs. Le filtre laboratoire accepte les partenaires de type laboratoire ou équipe ; la comparaison utilise le nom normalisé. Les résultats sont dédoublonnés par identifiant. Un second import conserve visibilité, corrections et dossiers.

Liste filtrable par titre/auteur et statut, avec titre, auteur, directeur, date, établissement, laboratoire, état de lecture et visibilité. Actions : ouvrir, lire une fiche, lire les fiches non traitées, publier/retirer après contrôle. Les nouvelles importations sont privées. Le statut et les dates de theses.fr sont affichés sans déduction automatique.

Une panne réseau affiche l'erreur et ne détruit pas les données. Un corpus public daté livré avec le dépôt rend le parcours consultable hors ligne. Le bouton d'import réel reste distinct de ce corpus.

### F03 — Fiche de thèse / espace doctorant

Afficher source et lien theses.fr, titre, personnes, affiliations, dates, résumés d'origine, mots-clés, lecture de l'agent, documentation utilisée et incertitudes. Séparer résumé original, résumé généré et correction humaine. Les modifications humaines sont historisées avec date et profil.

Les volets affichent fiche de lecture, opportunité, incorporation, activité. La publication/retrait est réservée au profil directeur/laboratoire dans le POC. Une fiche retirée disparaît de la recherche entreprise et ses dossiers ne sont plus servis par les routes entreprise.

Le compteur représente des entreprises distinctes et non des clics. L'entreprise de démonstration est explicitement fictive. Le suivi affiche les propositions en attente, acceptées ou refusées.

### F04 — Bibliothèque et besoin industriel

Champ de besoin multiligne, exemple prérempli accessible en un clic, filtres textuels et statut. Recherche classique disponible sans modèle. Le rapprochement intelligent prend les fiches publiées et le besoin ; le serveur valide les identifiants retournés et conserve la requête. L'écran précise le nombre de fiches effectivement analysées et une éventuelle limite du POC.

Une carte de résultat contient rang, pertinence, explication, éléments étayés, limites, confiance et accès au dossier. Les rejets sont lisibles. Un résultat vide n'est pas remplacé par une recommandation artificielle. Aucune fiche privée n'est envoyée à l'agent de recherche entreprise.

La voix utilise Gradium après activation explicite du micro. Le navigateur capture un WAV mono 24 kHz/16 bits limité à 60 secondes ; l'API Gradium transcrit la commande. Par défaut, la transcription reste visible et modifiable avant envoi. Une option distincte permet l'envoi automatique, y compris sans projet sélectionné pour créer ou ouvrir un projet par commande vocale. La synthèse des réponses s'active séparément sur les deux écrans. Clé API et identifiant de voix nécessaires ; les échecs ne déclenchent pas de fournisseur de remplacement silencieux.

### F05 — Dossiers

Tous les dossiers présentent dans cet ordre : pertinence pour le besoin ; éléments démontrés/documentés ; vérifications nécessaires ; contacts ; confiance et motifs d'incertitude. Chaque dossier conserve l'agent, sa révision, le moteur, le modèle, le mode démo/réel, la date et les sources.

**Lecture** : résumé accessible, résultats explicitement étayés, maturité estimée avec justification, droits connus/inconnus, manques documentaires. L'absence de brevet dans la notice ne vaut pas liberté d'exploitation.

**Opportunité** : verdict « favorable », « à approfondir » ou « défavorable » ; application visée ; bénéficiaires et marché à examiner ; différenciation ; travaux/concurrents connus ou recherche non faite ; preuves manquantes ; prochaines vérifications. Aucune taille de marché ni estimation économique inventée. L'application indique si aucune recherche externe d'antériorité n'a été conduite.

**Incorporation** : adéquation au produit, adaptations, plan d'essais, contraintes et ressources, maturité, délais/coûts avec justification ou « non estimable », points de propriété intellectuelle à instruire, contacts. Le dialogue de suivi réutilise le dossier et le besoin, conserve les échanges et passe par le moteur configuré.

Téléchargement des dossiers en Markdown, avec provenance et mode. Une erreur d'appel n'écrase pas le dernier dossier réussi. La simulation est toujours présentée comme une illustration, jamais comme l'exécution d'un LLM.

### F06 — Programmes et décisions

Lister/créer les programmes locaux, ouvrir leur besoin, demander un rapprochement, proposer une thèse visible. Une proposition démarre « en attente ». L'acceptation crée une note reprenant les cinq points, le lien source et le laboratoire ; le refus ne produit aucune note. L'opération est idempotente : un double clic ne crée pas deux notes locales. Une erreur Oscar maintient un état permettant un nouvel essai et signale une réponse distante ambiguë plutôt que de garantir une livraison.

Mode par défaut : « Démonstration — Oscar non connecté ». Programmes fictifs livrés en JSON ; notes persistées localement et exportables. Mode connecté : appels MCP limités à oscar_projets, oscar_contexte et oscar_deposer_avis. Le chemin du serveur stdio, l'URL et le jeton sont configurables côté serveur. Les noms réels de variables du serveur Oscar sont adaptés depuis ceux du POC. Aucune modification du dépôt Oscar.

### F06bis — Travaux de recherche R1–R3

Le catalogue contient les 32 tâches décrites dans `USAGES_PASSAGE_R1_R5.md` et formalisées dans `passage/work_catalog.py` : 16 pour le doctorant, 6 pour le jeune docteur et 10 pour le directeur de thèse. Pour chacune, la définition présente les entrées, quatre étapes du parcours manuel, le livrable attendu, la contribution permise à l'agent et la décision réservée à l'humain. La page **Travaux de recherche** permet de filtrer par persona et de voir les états « à commencer », « en cours », « agent en cours », « à relire » et « validé ». Un échec de l'agent ramène la tâche en cours avec erreur lisible.

Parcours manuel : créer la tâche dans un projet privé, préciser situation et échéance, joindre notes, preuves, documents de travail, livrables et fichiers, utiliser si pertinent les contrôles déterministes CSV/TSV, JSON ou syntaxe Python, vérifier les quatre étapes avec une note motivée et une pièce facultative de la même tâche, puis accepter le livrable ou demander une révision. Chaque contrôle conserve l'auteur, la date et l'historique ; les vérifications liées à un document, un fichier ou un passage périmé doivent être renouvelées. La clôture refuse une étape cochée sans contrôle humain actuel. Les fichiers sont limités à 8 Mo et 30 par tâche ; leur empreinte SHA-256 et l'auteur du dépôt sont conservés. Les PDF/DOCX textuels peuvent fournir des extraits à l'agent ; les images, scans et XLSX ne sont pas présentés comme lus. Passage ne lance aucun code scientifique fourni par l'utilisateur.
Un document de travail est un texte éditable lié à une tâche : Markdown, LaTeX, Python, R, CSV ou texte brut. Il peut être créé vide ou à partir d'une pièce de la tâche, notamment un brouillon d'agent, ou du texte intégral extrait d'un fichier non tronqué. Chaque sauvegarde conserve une version immuable, son auteur et son empreinte SHA-256 ; un numéro de version attendu empêche d'écraser silencieusement le travail d'un autre éditeur. Le relecteur peut commenter la version courante, avec un passage cité qui doit figurer exactement dans le texte. L'éditeur ne restitue pas la mise en page des PDF/DOCX importés, ne compile pas le LaTeX et n'exécute aucun code. Limites : 20 documents par tâche, 200 000 caractères par document.
Le dépôt explicite d'une version comme livrable conserve l'identifiant, la version et l'empreinte du document. La validation refuse une version devenue ancienne ; modifier un document accepté rouvre la tâche. Le dossier est exportable en Markdown, y compris sa révision, ses étapes, entrées, texte des versions déposées, commentaires, décisions, limites et empreintes de fichiers. Les pièces binaires se téléchargent séparément. Un dossier encore à relire porte explicitement la mention qu'aucun livrable n'a été accepté.
Un brouillon d'agent peut servir de départ à un document humain ; le document et le livrable déposé conservent le lien de provenance. Le parcours manuel permet aussi un livrable direct avec une trame liée à la sortie attendue.

Parcours agent : choisir dans l'équipe un agent direct actif, généraliste ou spécialisé sur cette tâche, ajouter une consigne et lancer une exécution asynchrone. Le contexte envoyé comporte uniquement le cadrage du projet et de la tâche, les notes récentes, les notices sélectionnées accessibles, les extraits pertinents des fichiers et documents courants, et les contrôles déterministes. Le contexte des documents est borné et porte identifiant, version et empreinte ; l'agent ne voit pas nécessairement leur texte intégral. Le mandat, le skill, le contexte, la mémoire validée et les pièces du Super Skill Creator sont inclus dans le harnais de cette exécution. Les outils externes sont retirés de ce parcours. La réponse structurée sépare proposition, sources/fichiers autorisés, hypothèses, vérifications, limites et prochaines étapes. Une référence hors périmètre fait échouer l'exécution sans enregistrer de brouillon. La révision de l'agent et un snapshot du harnais restent associés à l'exécution. Une proposition ciblée peut préremplir la note de contrôle et être liée comme pièce, mais ne coche jamais l'étape elle-même.

Le coordinateur du projet reçoit le catalogue, les spécialités des agents et les tâches déjà ouvertes. Il peut créer une tâche R1–R3 ou reprendre une tâche existante depuis le dialogue, puis demander un brouillon à un agent compatible. Il conserve les identifiants de la tâche et de l'exécution ; une exécution lancée n'est jamais annoncée comme livrable terminé. Les quatre dossiers historiques gardent leur action de délégation distincte.

Collaboration : le propriétaire peut inviter un autre compte local sur une tâche, comme éditeur ou relecteur. L'invité voit uniquement cette tâche et ses fichiers. L'éditeur contribue aux étapes et au livrable ; le relecteur annote et rend un avis sur une révision précise. Une modification rend caduc cet avis pour les tâches exigeant une seconde validation : conception d'expérience, échange avec l'encadrant et décisions de divulgation. Le propriétaire reste la personne qui clôture la tâche après vérification de toutes les étapes et d'un livrable. La clôture ne vaut ni dépôt institutionnel, ni réalisation physique, ni certification scientifique ou juridique.

### F07 — Atelier des agents

Quatre agents initiaux : Lecteur, Opportunité, Rapprochement, Incorporation. La création guidée choisit un rôle puis prépare un harnais éditable ; la duplication permet d'expérimenter. Un agent actif par rôle est utilisé dans les quatre parcours historiques. Le rôle « Travaux de recherche » permet plusieurs agents actifs ; chacun déclare une ou plusieurs des 32 tâches R1–R3 qu'il couvre.

La création guidée applique une adaptation versionnée du **Super Skill Creator V4** d'OSCAR AI : six étapes visibles ; brouillon inactif ; décisions à expliciter sur déclencheur, sources consultées, limites de décision humaine, point de contrôle et livrable ; cerveau choisi séparément ; skill, contexte, mémoire et pièces facultatives de processus, workflow, expérience ; outils accordés par capacités réelles. Le contrôle peut être lancé avant la sauvegarde. L'activation est refusée tant que la définition est incomplète. Toute révision conserve le harnais et les pièces utilisés ; les agents historiques ne sont pas migrés de force. Les agents « Travaux de recherche » exigent `work.read`, une spécialité du catalogue et le moteur direct. Leurs propositions utilisent le harnais complet et un contrat structuré distinct des quatre dossiers de valorisation.

| Section | Champs / comportement |
|---|---|
| Identité et mandat | Nom, rôle, objectif, état actif/inactif |
| Cerveau | Fournisseur, identifiant de modèle, moteur direct/Dust/Pipelex ; modèle affiché dans chaque exécution |
| Skill | Instructions de travail éditables, contraintes de confiance permanentes appliquées par le serveur |
| Contexte | Contexte métier statique, documents de la tâche assemblés au lancement |
| Mémoire | Notes validées, séparées des résultats temporaires ; pas d'apprentissage automatique silencieux |
| Outils | Capacités accordées : notices, bibliothèque publiée ; connecteurs MCP enregistrables et testables. Les programmes Oscar sont lus par le parcours métier. |
| Méthode | Référence et version Pipelex, contenu exportable, contrat d'entrée/sortie |
| Gouvernance | Limites d'exécution, obligation de validation humaine, contrôle des prérequis |
| Historique et test | Révisions immuables, harnais assemblé, test sur une entrée métier, trace et erreur lisibles |

L'enregistrement crée une révision. Une exécution capture la révision exacte ; une modification ultérieure ne change pas sa provenance. Le contrôle avant exécution vérifie nom, mandat, skill, modèle, moteur et disponibilité des paramètres nécessaires. Les secrets sont uniquement côté serveur et ne sont pas inclus dans les exports.

Dust reçoit une projection de notre définition, exportable puis publiable à la demande. L'import crée un agent distant et sa référence est enregistrée. Une modification locale invalide la synchronisation ; l'interface signale qu'il faut republier. Pipelex reçoit une méthode et des entrées conformes. La mémoire de travail de Pipelex reste distincte de la mémoire durable de l'agent.

### F08 — Exécutions et journal

Afficher les exécutions en attente/en cours/réussies/échouées, leur durée, agent, révision, modèle, mode, objet, résultat et erreur utile. Un échec fournisseur n'entraîne pas une bascule silencieuse vers la simulation. Les traitements longs utilisent des tâches suivies par identifiant. Après un redémarrage, les tâches interrompues sont marquées telles quelles.

Le journal produit conserve importations, corrections, publications et décisions. WORKLOG.md conserve le travail de développement, les tests et les limitations. Les clés et entêtes d'authentification sont exclus des traces.

### F08.1 — Services de recherche doctorale

Le projet de recherche est l’espace de travail principal du doctorant : son objectif, ses contraintes, sources autorisées, données, conversations et livrables sont rassemblés et isolés des autres projets. Il peut adresser une mission au coordinateur dans le chat ou par la voix, puis retrouver les décisions, résultats et fichiers produits. Le compte ChatGPT connecté fournit le catalogue des modèles réellement disponibles ; le doctorant peut consulter le modèle courant, en choisir un par son nom exact ou revenir au modèle de l'agent depuis le même dialogue. La conversation vocale se reconnecte après le tour courant quand ce choix change. La commande « Mes validations en attente » retrouve les cartes de ses propres projets ; si une seule carte attend, le projet s'ouvre pour examen sans confirmer l'action externe. Le sélecteur de projets affiche leur nombre.

| Service | Résultat attendu | Contrôles indispensables |
|---|---|---|
| Écriture de thèse | Plan de section, synthèse de sources fournies, amélioration rédactionnelle ou relecture critique | Relier les affirmations aux sources, distinguer citation, paraphrase et interprétation, signaler les lacunes ; ne jamais fabriquer de référence ou de résultat |
| Expériences | Question expérimentale, protocole, variables, contrôles, mesures, matériel et risques à examiner | Distinguer protocole proposé d’expérience exécutée ; attacher données et conditions aux résultats ; garder l’approbation et la conduite réelle au chercheur |
| Simulations | Méthode/modèle, paramètres, hypothèses, entrées, sorties et scénario de validation ; exécution seulement via un moteur outillé disponible | Identifier données synthétiques versus réelles, version du code/modèle, graines, unités et environnement ; signaler une exécution non réalisée ou une limite de validité |
| Programmes scientifiques | Spécification ou code dédié aux données et méthodes de la recherche, avec tests et mode d’emploi | Conserver code et versions, rendre les tests et dépendances consultables, analyser les erreurs et limites ; les résultats de tests ne remplacent pas une revue scientifique |

Des exemples sélectionnables dans le chat aident à formuler les quatre types de demande sans fournir une réponse fabriquée. Dans chaque projet, le doctorant peut sélectionner jusqu'à huit notices accessibles de theses.fr. Leurs titres, identifiants, liens et résumés sont transmis comme sources autorisées au rédacteur. Le coordinateur choisit l'action `research`, un agent rédige un brouillon structuré, puis un second agent direct actif du même fournisseur dans l'équipe effectue une relecture critique si disponible. L'interface affiche les corrections demandées ; une relecture échouée est signalée comme limite sans masquer le brouillon. Les identifiants des sources et les extraits cités sont comparés aux notices sélectionnées avant enregistrement. Cela vérifie la provenance textuelle des citations, pas la vérité scientifique des affirmations. Le livrable privé est consultable et exportable en Markdown avec contenu, liens des notices, citations, hypothèses, vérifications, limites, identité et avis du relecteur, modèle et révision du rédacteur. Son statut reste « proposition à vérifier ». Sans notice sélectionnée, il ne peut déclarer aucune référence comme vérifiée. L'appel de génération ne réalise aucune expérience physique, n'exécute aucune simulation et ne compile ni ne teste le code proposé.

L'action `simulate` réalise un calcul borné pour le démonstrateur batterie, en mode réel seulement, avec un modèle thermique à capacité concentrée : `C × dT/dt = I² × R − h × (T − T_amb)`. Huit paramètres explicites sont validés, le pas et le nombre d'itérations sont limités, puis la série calculée et les paramètres sont conservés dans le projet. Son statut « calcul exécuté » distingue le calcul numérique d'une proposition de simulation. Série exportable en CSV, avec unités dans les noms de colonnes. Les paramètres sont fournis par l'utilisateur ; les prédictions ne valent pas données expérimentales et le modèle doit être validé. L’évaluation scientifique demeure sous la responsabilité du doctorant. Ces services de recherche complètent le parcours laboratoire/entreprise existant ; ils ne constituent pas une nouvelle roadmap.

### F09 — Connexions et réglages

Afficher l'état des accès OpenAI, endpoint compatible, Ollama natif, Dust, Pipelex et Oscar. Ollama permet de lister les modèles déjà installés, sans téléchargement automatique. La présence d'une clé n'est pas une preuve de connexion. Les formulaires secrets ne renvoient pas la valeur sauvegardée. Une clé saisie dans l’interface est conservée en mémoire par défaut ; une option explicite permet sa conservation chiffrée dans la base locale. Le fichier `.env` reste une alternative. Les paramètres persistants de l’interface priment sur `.env`, les valeurs de session priment sur les paramètres persistants. L'application écoute sur 127.0.0.1 par défaut.

Les connexions MCP ont nom, URL publique ou locale, liste de capacités autorisées et référence de secret. Le POC ne lance pas une commande arbitraire fournie par un modèle. Oscar utilise uniquement le script explicitement configuré par l'opérateur. Les appels MCP sont tracés et les erreurs visibles.

### F09.1 — Comptes personnels de modèles

L’utilisateur peut relier son compte ChatGPT depuis Connexions par le parcours officiel du Codex App Server, avec retour navigateur ou code d'appareil. Passage garde un profil d’authentification séparé par compte local ; il ne copie pas les jetons du compte Codex ouvert sur la machine. Un nouveau parcours annule le précédent et un lien ancien est régénéré après cinq minutes ; l'interface peut réafficher le parcours encore en attente. Une connexion terminée masque les actions de connexion et propose de vérifier ou déconnecter. Après connexion, le catalogue dynamique du compte et ses limites peuvent être consultés. À la création ou dans la fiche du projet, l'utilisateur peut choisir un modèle disponible pour son coordinateur, sans modifier l'agent partagé ni les autres projets ; ce modèle sert au chat et à la conversation vocale Gradium. Les inférences utilisent l’accès Codex du compte et ses limites d’offre. Elles ne consomment pas les crédits API OpenAI, qui relèvent d’une facturation distincte. Les modèles et limites ne sont disponibles qu’après la connexion réelle du compte ; une initialisation réussie du protocole n’est pas une recette d’inférence.

Pour Dust et Pipelex, l’accès OAuth MCP de Connexions est distinct des clés utilisées par les anciens moteurs Dust API et Pipelex API. L’interface doit rendre visible la source d’accès et le fournisseur réel d’une exécution. Un agent Dust est configuré et facturé dans le workspace Dust ; une méthode Pipelex porte son modèle et ses appels passent par la configuration propre à Pipelex. Le nom d’un agent ou d’une méthode ne doit pas être présenté comme un identifiant de modèle LLM. L’utilisateur autorise explicitement les outils MCP disponibles.

## 5. Contrats et règles communes

- Les notices importées sont des données, jamais des instructions d'exécution. Le prompt rappelle cette frontière.
- Seules les données autorisées pour le rôle et la tâche sont assemblées. Les règles de publication et de décision sont appliquées au serveur.
- Les sorties LLM sont validées par schéma ; les références de source doivent appartenir aux entrées. Les citations textuelles sont vérifiées dans les résumés fournis ; une référence invalide fait échouer le résultat.
- L'absence de résumé entraîne une confiance réduite et l'interdiction de présenter des résultats comme démontrés.
- Les estimations ne deviennent pas des faits. Les droits inconnus sont explicitement inconnus.
- Le choix du moteur et du modèle est explicite. L'interface de chat utilise les agents réels ; l'ancien mode de démonstration déterministe reste seulement dans l'API et les tests de recette. Il ne déclenche aucun fournisseur et ne prétend pas mesurer une confiance scientifique.
- Les outils externes ne sont pas appelés s'ils sont désactivés dans le harnais. Les connecteurs configurés ne donnent pas automatiquement tous leurs droits à tous les agents.
- Les pages et exports affichent les erreurs et les données comme texte ; le contenu des sources ne doit pas exécuter du HTML/JavaScript.

## 6. Données persistées

SQLite : laboratoire, notices normalisées et payload source, analyses/dossiers versionnés, corrections humaines, visibilité et décisions, consultations uniques, programmes, propositions, notes, définitions d'agents/révisions, mémoires, connecteurs, exécutions et événements. Chaque objet possède un identifiant stable et une date. Le PDF n'est pas conservé. Les sources JSON du corpus sont livrées avec provenance et date pour la reproductibilité.

Les trois familles de données sont identifiées : métadonnées réelles theses.fr ; entreprise/programmes fictifs de démonstration ; productions d'agents réels ou résultats simulés. Aucun assentiment du LRCS réel n'est revendiqué : la publication dans le POC représente une action de rôle jouée dans la démo.

## 7. Architecture de réalisation

Application locale Python/FastAPI, SQLite, interface HTML/CSS/JavaScript servie par la même application. Pas de compilation frontend nécessaire. Fournisseurs derrière des adaptateurs. Appels LLM directs via API HTTP ; mode compatible pour les serveurs locaux. Dust via API ; Pipelex via méthode hébergée ou exécution locale optionnelle selon environnement. Le transport Oscar est MCP stdio. Les données de démonstration et le moteur simulé rendent les écrans testables sans compte fournisseur, après connexion locale, tout en conservant une voie réelle distincte.

Les dépendances et un lanceur Windows sont livrés. L'API est documentée via `/docs`. Les fichiers `.env`, bases et journaux techniques sont exclus du dépôt. La documentation précise comment reproduire les tests et distinguer ce qui a été testé localement de ce qui nécessite des accès partenaires.

## 8. Intégrations et niveau attendu

| Intégration | Attendu pour le POC | Vérification |
|---|---|---|
| theses.fr | Recherche, détails, import LRCS, rafraîchissement conservateur, corpus réel | Appels publics réels + test de réimport |
| LLM direct | Quatre tâches, sortie structurée, erreurs et provenance | Tests de contrat + essai réel avec clé |
| Dust | Export/synchronisation de définition, exécution et dialogue Incorporation | OAuth MCP, catalogue et lecture de la conversation de test réels ; cette conversation est vide après refus par plafond de dépenses du workspace, donc inférence hébergée non validée |
| Pipelex | Méthode doctorale exportable et invocation configurée, état et résultats | OAuth MCP, catalogue et signature réels ; une carte de lancement est préparée, run hébergé à confirmer puis vérifier |
| Oscar | Démo complète ; adaptateur MCP des trois outils | Démo bout en bout ; connexion réelle si serveur/jeton fourni |
| Gradium | Adaptateurs STT/TTS REST et dialogue implémentés | Synthèse et transcription réelles vérifiées avec audio synthétique ; microphone humain réservé à l'essai de l'utilisateur |
| Jinko | Ville du laboratoire et préparation d'une visite | Aucun achat/réservation ; intégration avancée reportable selon cadrage |

Les accès partenaires manquants ne doivent pas être présentés comme des intégrations testées en production. Le POC doit néanmoins contenir les chemins de code et contrats des intégrations centrales demandées Dust/Pipelex.

## 9. Critères de recette

| ID | Preuve attendue |
|---|---|
| R01 | Démarrage par la commande documentée, page utilisable et base persistante |
| R02 | Au moins dix notices réelles datées, dont les trois cas du cadrage, sans affiliation inventée |
| R03 | Import réel LRCS ; réimport sans doublons ni perte de correction/visibilité |
| R04 | Notice privée absente des recherches et des dossiers entreprise ; retrait immédiat |
| R05 | Lecture réelle structurée ou erreur explicite de configuration ; démo étiquetée |
| R06 | Correction doctorant conservée après lecture/rafraîchissement et visible dans le parcours |
| R07 | Classement des trois cas expliqué ; traitement du hors-sujet et de l'absence de résultat |
| R08 | Dossiers Opportunité et Incorporation complets, exportés avec sources et incertitudes |
| R09 | Consultation unique, proposition visible côté doctorant, refus sans note, acceptation avec une seule note |
| R10 | Création/édition/duplication d'agent, activation par rôle, révision et snapshot d'exécution |
| R11 | Harnais réellement utilisé : skill/contexte/mémoire/outils et contrôles de prérequis |
| R12 | Exports/adaptateurs Dust et Pipelex cohérents avec la définition locale, aucune bascule cachée de modèle |
| R13 | Erreurs réseau/fournisseur et réponses invalides lisibles ; dossier précédent conservé |
| R14 | Aucun secret renvoyé par API/export/journal ; sources HTML malveillantes affichées comme texte |
| R15 | Vérification visuelle des vues principales et parcours au clavier, écran étroit sans débordement majeur |
| R16 | README, déclaration Oscar-AI, scénario de démo et journal de travail livrés |

Un rapport de recette indique pour chaque critère : réussi, échoué ou non vérifié, avec sa preuve. Les tests de contrat n'attestent pas l'accès réel aux services partenaires.

## 10. Sources de conception

- Pièces utilisateur : personas, roadmap et « Passage — cadrage pour construire », datés du 25/09/2026.
- OpenAI : https://developers.openai.com/api/docs/guides/structured-outputs
- Dust import : https://docs.dust.tt/api-reference/agents/import-agent-configuration
- Dust conversations : https://docs.dust.tt/api-reference/conversations/create-a-new-conversation
- Pipelex méthodes et exécution : https://docs.pipelex.com/latest/get-started/quick-start/ et https://docs.pipelex.com/latest/building-methods/pipes/executing-pipelines/
- Serveur Oscar observé en lecture seule : `../Oscar-AI/backend/passerelle/oscar_mcp.py`.

## 11. Exigence prioritaire — équipe agentique par projet

Sébastien rappelle que le hackathon doit démontrer une solution exploitant fortement l'autonomie des agents. Le lancement manuel de chaque spécialiste ne doit donc pas être le parcours principal. Cette section remplace la recommandation antérieure de missions systématiquement déclenchées une par une. Le périmètre livré est précisé en section 12.

### 11.1 Interaction avec l'utilisateur

L'utilisateur crée un projet, formule un objectif et des critères de réussite, fournit ses contraintes et accorde les sources/outils nécessaires. Il peut choisir son équipe ou accepter une équipe proposée par le coordinateur. Il lance ensuite une mission globale, suit son avancement et peut intervenir, suspendre ou préciser son objectif. Il n'a pas à déclencher chaque appel d'agent.

Une question à l'utilisateur n'est requise que lorsqu'une information manquante empêche une décision utile ou qu'une action attend une validation humaine. Les hypothèses réversibles sont explicites et permettent de poursuivre le travail indépendant.

### 11.2 Composition de l'équipe

| Fonction | Responsabilité dans le projet |
|---|---|
| Coordinateur | Comprendre l'objectif, proposer les missions, choisir les spécialistes parmi les agents autorisés, interpréter leurs retours, modifier le plan et décider quand conclure ou demander une information. |
| Rapprochement | Explorer les sources accessibles et constituer une sélection argumentée, avec rejets et inconnues. |
| Lecteur | Examiner les travaux retenus et produire leurs preuves, limites et manques documentaires. |
| Opportunité | Évaluer l'intérêt entrepreneurial lorsqu'il répond à l'objectif ; ne pas exécuter ce rôle systématiquement sur un besoin d'intégration industrielle. |
| Incorporation | Préparer les adaptations, expériences et moyens nécessaires pour les pistes pertinentes. |
| Revue critique | Vérifier la couverture du besoin et la solidité des conclusions ; demander une reprise ciblée, signaler une contradiction ou conclure que les preuves sont insuffisantes. Cette fonction peut utiliser un agent dédié ou un harnais de revue distinct. |

### 11.3 Boucle de travail

1. Le coordinateur lit l'objectif, les contraintes, les sources, les permissions et les résultats existants du projet.
2. Il produit une prochaine action structurée : déléguer une mission, consulter une source autorisée, demander une information, préparer une validation ou conclure. Il fournit une justification courte et observable.
3. Le harnais vérifie les droits, les dépendances et les budgets avant l'exécution. Une décision du modèle n'accorde jamais un nouvel accès.
4. Le résultat, ses preuves, sa provenance et ses limites rejoignent le projet. Les tâches indépendantes peuvent être exécutées en parallèle dans la limite de concurrence configurée.
5. Le coordinateur réévalue la situation à partir de ce résultat. Il peut approfondir, écarter une piste, demander une revue ou changer d'approche. Une erreur ne provoque ni boucle illimitée ni passage caché en simulation.
6. La mission s'arrête sur critères atteints, absence documentée de piste, limite de budget, demande utilisateur ou validation attendue. La synthèse indique ce qui est établi et ce qui reste ouvert.

Il ne suffit pas d'enchaîner les quatre agents dans un ordre constant. Le choix des spécialistes, les reprises et l'arrêt doivent dépendre de l'objectif et des observations.

### 11.4 Contexte, mémoire et traçabilité

Chaque projet contient son objectif, ses membres, ses sources, ses agents affectés, ses missions, ses décisions, ses livrables et sa mémoire de travail. Le harnais commun de l'agent reste versionné dans l'atelier. Son contexte d'exécution comprend uniquement les éléments autorisés du projet.

Les observations produites par les agents restent distinguées des faits vérifiés et de la mémoire validée par l'équipe. Une production ne devient pas silencieusement une vérité durable. Une modification d'objectif permet au coordinateur d'identifier les résultats à conserver ou à refaire.

L'interface montre les missions confiées, l'agent retenu, les outils réellement appelés, les résultats, les motifs brefs de changement de plan, les validations attendues et les limites consommées. Elle ne présente pas une animation scénarisée comme une exécution réelle.

### 11.5 Autonomie et validations

Recherche, lecture, comparaison, critique et préparation des dossiers peuvent avancer dans le périmètre autorisé sans clic humain à chaque étape. Publication d'une fiche, contact externe et acceptation/dépôt engageant un programme restent soumis à l'autorisation appropriée. L'utilisateur contrôle les plafonds de durée, d'appels, de dépense lorsque mesurable et de tentatives de reprise.

Dust demeure un exécuteur optionnel d'agents. Pipelex exécute les méthodes répétables et leurs contrôles. Le coordinateur choisit quand appeler un agent ou une méthode selon l'état du projet ; la définition canonique des agents et les décisions de projet restent dans Passage.

### 11.6 Preuve attendue pour le hackathon

À partir d'un seul objectif sur le pack de batteries, montrer une mission réelle où le coordinateur sélectionne les spécialistes, obtient leurs résultats, fait examiner une limite, adapte la suite et prépare une proposition à valider. Une nouvelle contrainte de masse ou de délai doit pouvoir modifier le travail demandé. Les traces doivent permettre de distinguer les décisions du coordinateur, les traitements déterministes et les décisions humaines. Les agents qui n'apportent rien à cet objectif ne sont pas appelés pour gonfler artificiellement l'équipe.

Cette recette s'ajoute à celle des parcours spécialisés. Comptes, permissions de projet et orchestration doivent avoir leurs propres tests avant d'annoncer cette expérience disponible.

## 12. Périmètre implémenté — dialogue et connexions partenaires

### 12.1 Comptes et projets

Comptes locaux avec mot de passe de douze caractères minimum, hachage PBKDF2, sessions opaques de 24 heures, cookie HttpOnly/SameSite et vérification CSRF. Administration des rôles dans l'interface. Pas de récupération de mot de passe par email, de SSO d'entreprise ou de multi-organisation. Les projets ont un propriétaire unique ; l'invitation de membres reste hors du périmètre implémenté. Les notices et programmes historiques du scénario restent partagés ; les conversations, missions, analyses et propositions nouvelles sont contrôlées par propriétaire.

### 12.2 Coordinateur et harnais

Équipe affectée à la création à partir des agents actifs. Le coordinateur utilise le cerveau d'un agent direct de cette équipe et un harnais de coordination structuré. Les spécialistes peuvent utiliser les moteurs directs, Dust ou Pipelex configurés dans leur définition. Le coordinateur peut rechercher, déléguer, interpréter les résultats, modifier nom/objectif/équipe sur instruction, consulter des outils MCP et demander une validation ou une précision.

L'exécution est séquentielle, avec huit décisions maximum par message et trois missions serveur concurrentes. La parallélisation de spécialistes et un budget monétaire configurable ne sont pas encore implémentés. L'action de recherche dispose d'un second passage de critique par un agent distinct lorsque l'équipe le permet. Arrêter empêche l'action suivante ; l'appel réseau déjà engagé peut se terminer. Une simulation utilise un parcours déterministe explicitement indiqué.

### 12.3 MCP officiels Dust et Pipelex

Connexion OAuth distincte par utilisateur, PKCE/état gérés par le SDK MCP, découverte des capacités, sélection explicite des outils autorisés. Jetons chiffrés localement ; aucune valeur secrète exposée aux écrans. Les noms et schémas des outils proviennent du serveur, sans inventer une API MCP fixe. Un outil non autorisé est refusé même s'il est demandé par le modèle.

Les outils annoncés en lecture seule peuvent être exécutés dans le périmètre accordé. Une autre action génère une carte affichant service, outil et arguments, avec Confirmer/Refuser. L'appel confirmé a un état persistant qui empêche un deuxième envoi. Un échec réseau après envoi produit « livraison à vérifier ». Déconnexion locale et révocation fournisseur sont distinguées.

### 12.4 Dialogue vocal Gradium

Capture explicite au bouton Parler, arrêt manuel ou après 60 secondes, transcription REST Gradium, texte modifiable envoyé au même coordinateur. Lecture des réponses en WAV sur option. Clé API serveur et identifiant de voix nécessaires. Micro et audio ne restent pas actifs après déconnexion. L'application ne conserve pas l'audio brut. Il s'agit d'une conversation par tours ; interruption vocale automatique et streaming duplex ne sont pas encore implémentés.

### 12.5 Critères de recette

- Un visiteur non connecté ne peut lire les données de l'application ; un rôle falsifié dans l'en-tête ne donne pas accès à l'administration.
- Deux comptes ne peuvent lire les conversations, missions ou exports de projets de l'autre.
- Le coordinateur voit le résultat du premier spécialiste avant sa décision suivante.
- Une écriture MCP attend la décision humaine et ne s'exécute qu'une fois.
- Les tests de contrat OAuth/Gradium sont distingués d'une connexion réelle aux services.
- Une mission réelle locale et les parcours du navigateur sont observés avant livraison. Les accès sponsors sont marqués « connectés » seulement après découverte réussie des outils ; une URL OAuth obtenue ne suffit pas.

Sources techniques : [Dust MCP](https://docs.dust.tt/docs/user-documentation/agents/integrations/dust-mcp-server), [Pipelex quick start](https://docs.pipelex.com/latest/get-started/quick-start/), [Gradium STT REST](https://docs.gradium.ai/guides/speech-to-text-rest), [Gradium TTS REST](https://docs.gradium.ai/guides/text-to-speech-rest).


### 12.6 Commandes de dialogue

Sans projet sélectionné, écrire ou dicter un objectif crée le projet et lance la coordination. Le même endpoint traite la saisie clavier et la transcription Gradium. Pendant une mission, « Arrête la mission » est traité immédiatement par le serveur ; il empêche l'action suivante sans prétendre annuler un appel réseau déjà engagé. Après la fin d'une mission, la même commande indique qu'aucun travail n'est en cours.

Les commandes « Crée un projet [nom] » et « Ouvre le projet [nom exact] » permettent de créer ou sélectionner un projet sans appel au modèle ; la sélection est limitée aux projets du compte connecté. « Statut de la mission » lit l'état de l'exécution du projet courant et indique si un arrêt a déjà été demandé. Les commandes qui ne lancent aucune mission reçoivent également une réponse lue par Gradium si la lecture vocale est activée.

« Liste les agents Dust » et « Liste les méthodes Pipelex » interrogent les catalogues MCP personnels en mode réel, y compris avant de sélectionner un projet. La réponse est affichée dans le dialogue ou sur l'écran sans projet et peut être lue par Gradium. La connexion et le droit de lecture du catalogue sont vérifiés côté serveur ; aucun outil d'exécution n'est appelé par ces commandes.

« Montre la méthode Pipelex [nom] » recherche d'abord le nom normalisé dans le catalogue personnel, puis appelle uniquement `pipelex_show_method` avec l'identifiant trouvé. Guillemets, accents et ponctuation ne sont pas nécessaires à la dictée. Seuls la signature et le modèle d’entrées sont extraits de la réponse et affichés dans le dialogue, éventuellement lus par Gradium. Le service doit être connecté et les deux outils de lecture accordés. Une méthode absente ou ambiguë n'est pas appelée.

Une demande peut ensuite désigner un agent Dust par son nom dans le catalogue personnel : « Demande à l’agent Dust analyst de [travail] ». Le nom prononcé est comparé après normalisation ; les guillemets sont facultatifs et une correspondance ambiguë est refusée. Passage valide ce nom et prépare `create_conversation` avec `agentName`; une carte de confirmation présente le message et l'agent avant l'appel. La demande sans nom garde l'agent Dust par défaut. Cette sélection concerne les agents Dust, dont les modèles sont gérés dans Dust ; Passage ne prétend pas modifier leur modèle sous-jacent par le MCP.

« Je confirme l'action » ou « Je refuse l'action » s'applique uniquement lorsqu'une seule carte attend une décision dans le projet courant. Un simple « oui » ne déclenche pas une autorisation. S'il existe plusieurs cartes, l'utilisateur doit désigner celle qu'il décide via son bouton. Chaque réponse du coordinateur propose une lecture explicite avec Gradium et un bouton pour couper la voix.

## 13. Demandes récentes et état constaté

### 13.1 Connexions modèles et voix

Le compte ChatGPT personnel dispose du parcours officiel d’autorisation et d’un adaptateur Codex isolé par utilisateur. Dans l’instance de recette, le CLI est installé et la route de statut est présente ; le compte n’a pas encore été autorisé et aucune inférence ni liste de modèles n’a été vérifiée. L’utilisateur doit terminer l’authentification depuis Connexions.

Dust Europe et Pipelex MCP ont des sessions OAuth utilisables. Le 26/09, les outils nécessaires aux parcours avec validation ont été accordés dans Passage : `create_conversation`, `get_conversation_messages` et `list_conversations` pour Dust Europe ; `pipelex_run` pour Pipelex, en plus des lectures déjà actives. Le coordinateur prépare une carte avant chaque écriture externe. L’unique ancien message de test Dust a atteint le plafond mensuel de dépense programmatique du workspace ; aucune inférence Dust fonctionnelle n’est donc démontrée. Pipelex donne accès en lecture au catalogue et aux signatures ; la méthode « Passage — Recherche doctorale » y est enregistrée et validée. La commande vocale ou écrite « Demande à Pipelex de… » vérifie son contrat via `pipelex_show_method` avant de préparer une carte de validation ; aucun vrai `pipelex_run` n'a encore été lancé. Les moteurs historiques directs Dust API/Pipelex API exigent leurs propres clés et méthodes publiées ; ils ne partagent pas automatiquement les sessions OAuth MCP.

Une carte Pipelex préparée conserve la signature vérifiée. À la confirmation, Passage la relit ; un contrat modifié invalide la carte avant tout `pipelex_run`. Une lecture temporairement impossible laisse la carte en attente. La réponse du dialogue distingue donc une absence d'envoi d'un résultat de livraison incertain.

Gradium accepte une clé créée pour le POC, sauvegardée dans les réglages chiffrés de l’installation, et l’identifiant de voix Noémie est configuré. La recette réelle, effectuée après avoir lancé l’instance avec accès sortant à l’API, a produit un WAV de synthèse de 115 244 octets ; la transcription REST a rendu exactement « Arrête la mission. », et le dialogue l’a reconnue comme commande `stop`. Aucun microphone physique n’a été enregistré ; sa permission et sa capture restent à vérifier dans le navigateur. L’erreur précédente venait du contexte réseau du serveur lancé dans le bac à sable ; un démarrage avec accès réseau a permis l’appel réel. Le clavier reste disponible.

### 13.2 Services demandés pour le doctorant

Demande utilisateur du 25/09 : Passage devrait aider le doctorant dans l’écriture de sa thèse, la préparation et l’analyse d’expériences, les simulations et la création de programmes informatiques dédiés. Le POC produit désormais des propositions structurées pour ces quatre usages et les conserve dans le projet ; un seul modèle de simulation batterie s'exécute réellement. L'import de documents et données propres au projet, l'exécution contrôlée de code généré ou d'autres modèles scientifiques, la connexion d'équipements expérimentaux et la vérification automatique des références restent à définir et à réaliser avant d'annoncer ces capacités comme disponibles.
