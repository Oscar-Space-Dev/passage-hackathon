# Utilisation de Passage pour chaque tâche de R1 à R5

Version actualisée le 26/09/2026. Base : `ANALYSE_TRAVAIL_PERSONAS.md`, les personas fournis et le POC dans ce dépôt. Ce document décrit l'action concrète dans Passage, y compris la contribution possible des agents, puis la frontière du POC. Il ne fixe ni priorité ni roadmap. Les usages proposés restent à confronter aux pratiques des personnes concernées.

**Lecture des états :** « Parcours POC » signifie qu'une tâche guidée R1–R3 peut être créée dans un projet, renseignée avec trois questions propres à ce travail et alimentée par des notes, preuves, livrables et fichiers, confiée à un agent direct de l'équipe pour une proposition, partagée avec un autre compte local pour contribution ou avis, puis clôturée par l'utilisateur après contrôle des questions et étapes. Les questions renseignées suivent la tâche et sont transmises à l'agent choisi. L'agent peut proposer des réponses à reprendre après relecture ; une trame Markdown propre à la tâche aide à rédiger le livrable. Cela ne signifie pas que Passage réalise le travail physique, une soumission externe ou une validation scientifique. « Partiel » signifie qu'une fonction existante aide à une partie de la tâche. « À construire » signifie qu'aucun parcours métier dédié n'existe.

Le détail des quatre étapes de chacune des 32 tâches R1–R3, avec action humaine, aide d'agent, outil et pièce à vérifier, figure dans `PARCOURS_R1_R3.md`. La fiche de tâche permet de cibler une étape lors de la délégation.

## R1 — Doctorant en cours de thèse

Pour les tâches impliquant une action externe, le parcours R1–R3 ajoute désormais un point de contrôle propre à la tâche : preuve ou fichier, date, déclaration du propriétaire, puis validation. Les dossiers confidentiels exigent également une attestation avant l'appel d'un agent. Les libellés exacts et leur moment d'application sont dans `passage/work_catalog.py`. Une modification du dossier rend l'attestation antérieure périmée ; le journal du dossier exporté indique son état. Cela complète les parcours décrits ci-dessous sans faire de Passage un instrument de laboratoire, un service de dépôt ou une autorité de validation.

Les livrables validés peuvent aussi être liés explicitement à une tâche suivante du même projet. Ce lien conserve la version acceptée ; l'agent de la tâche suivante reçoit un extrait borné si le partage avec le modèle est autorisé. Une modification de la source rend le lien périmé et impose une nouvelle vérification du travail aval. Les invités du travail aval doivent aussi accéder aux tâches sources.

Dans les 32 tâches R1–R3, un registre propre au métier permet de suivre chaque élément séparément : article, hypothèse, essai, commentaire, candidature, lot de budget ou décision selon le cas. Ses lignes sont versionnées, peuvent pointer vers une preuve ou un fichier et peuvent être proposées par l'agent pour reprise après vérification humaine. Les questions de cadrage et le registre ont des fonctions différentes : les premières décrivent la tâche, le second suit ses éléments répétés.

Le travail d'agent se poursuit aussi après un premier brouillon : le propriétaire peut demander une correction ciblée au même spécialiste ou à un autre agent compatible de l'équipe. Passage lui transmet le brouillon visé, le retour humain et le dossier autorisé ; la nouvelle version conserve ce lien et une différence de texte. Les passages sourcés proposés par l'agent restent à vérifier et à adopter par l'utilisateur.

| Tâche | Utilisation de Passage par le doctorant et ses agents | État et frontière |
|---|---|---|
| Lire et classer la littérature | Créer une tâche de lecture, déposer les articles autorisés, ancrer une affirmation à un passage exact, noter critères et annotations ; l'agent propose des fiches, classements et passages à vérifier. | **Parcours POC.** Passage vérifie le texte et sa version, pas la validité de l'interprétation ; pas de bibliothèque bibliographique complète. |
| Construire l'état de l'art | Regrouper les fiches par thème, consigner convergences et contradictions ; l'agent prépare un plan et des passages sourcés que le doctorant reprend dans un document versionné. | **Parcours POC.** La vérification scientifique des références reste humaine ; l'agent reçoit des extraits bornés des fichiers et documents. |
| Formuler question et hypothèses | Inscrire question, hypothèses concurrentes, prédictions et tests discriminants dans une tâche ; l'agent cherche les alternatives et les lacunes. | **Parcours POC.** Le doctorant et l'encadrant choisissent les hypothèses scientifiques. |
| Concevoir une expérience | Fournir hypothèse, contraintes et matériel ; l'agent propose protocole, témoins, mesures et critères d'arrêt. Partager la version avec l'encadrant pour avis. | **Parcours POC.** Accord d'un compte laboratoire ou administrateur requis pour clôturer ; Passage ne vérifie ni sécurité ni faisabilité instrumentale. |
| Réaliser une expérience | Ouvrir la tâche avec le protocole, consigner paramètres, incidents et résultats, joindre les fichiers ; l'agent vérifie la complétude du compte rendu. | **Parcours POC de traçabilité.** L'essai se fait hors de Passage ; aucun instrument n'est piloté et l'agent ne peut attester qu'il a eu lieu. |
| Tenir le cahier de laboratoire | Créer une entrée datée, relier protocole, observations et fichiers ; l'agent structure les notes et signale les champs manquants. | **Parcours POC.** Historique de pièces et empreintes des fichiers ; ce n'est pas un cahier de laboratoire certifié ou signé. |
| Écrire ou adapter du code scientifique | Déposer la spécification, écrire ou reprendre le code dans un document versionné, demander à l'agent une implémentation ou revue, puis conserver les sorties fournies par le chercheur. | **Parcours POC.** Contrôle syntaxique des fichiers Python disponible ; aucun code utilisateur n'est exécuté ou testé par Passage. |
| Nettoyer et analyser des données | Déposer CSV/TSV, dictionnaire et règles d'exclusion ; choisir une variable numérique et un groupe pour une analyse descriptive locale, ou demander à l'agent de déclencher ce calcul puis relire son interprétation. | **Parcours POC.** Effectifs, valeurs exclues, moyenne, médiane, extrêmes et écart-type calculés avec empreinte du fichier ; pas de pipeline scientifique général ni d'inférence statistique validée. |
| Discuter les résultats avec l'encadrant | Préparer une note résultat–preuve–incertitude–décision, inviter l'encadrant sur la tâche, recueillir son avis et consigner la suite. | **Parcours POC.** Relecture sur compte local ; pas de synchronisation avec les outils du laboratoire. |
| Rédiger thèse et articles | Importer une section textuelle ou reprendre un brouillon d'agent, ancrer les affirmations à des passages source, rédiger des versions, demander des commentaires, puis déposer une version comme livrable. | **Parcours POC.** Éditeur de texte, registre de passages et commentaires sur version, sans mise en page collaborative ni dépôt à une revue. |
| Répondre aux relecteurs | Importer remarques et manuscrit, relier chaque remarque à une action et une preuve ; l'agent propose la matrice et une réponse point par point. | **Parcours POC.** Le suivi est dans la tâche, sans liaison au système éditorial. |
| Préparer conférences et posters | Déposer résultats validés et contraintes de format ; l'agent prépare résumé, récit, plan du poster et questions probables. | **Parcours POC.** Passage ne fabrique pas un poster/diaporama final ni ne décide ce qui est publiable. |
| Rendre compte au comité de suivi | Rassembler objectifs, essais, résultats et écarts ; l'agent prépare une synthèse et les points de décision ; conserver le compte rendu. | **Parcours POC.** Pas de collecte automatique de toutes les activités du projet ou du laboratoire. |
| Préparer enseignement | Définir niveau et objectifs, joindre les supports existants ; l'agent propose séance, exercices et corrigé à vérifier. | **Parcours POC.** Pas de gestion de cours, d'étudiants ou d'évaluation. |
| Préparer soutenance et suite de carrière | Déposer contributions et limites ; demander à l'agent un plan oral, des questions possibles et une comparaison postdoc–emploi–startup. | **Parcours POC.** La présentation finale, les candidatures et les choix personnels restent hors de l'outil. |
| Décider ce qui peut être divulgué | Lister les contenus, publications et engagements connus ; l'agent prépare une fiche d'inconnues, puis inviter un relecteur habilité avant de consigner une décision. | **Parcours POC.** Accord local de relecture requis pour clôturer ; aucune analyse juridique fiable ni autorisation institutionnelle automatique. |

## R2 — Docteur venant de soutenir

| Tâche | Utilisation de Passage par le docteur et ses agents | État et frontière |
|---|---|---|
| Corriger et déposer le manuscrit final | Joindre les demandes du jury, reprendre les sections textuelles en documents versionnés, faire relire les corrections par l'agent et conserver la preuve de dépôt. | **Parcours POC.** Le dépôt institutionnel et la mise en page finale se font hors de Passage. |
| Finaliser les derniers articles | Reprendre résultats, versions et consignes ; l'agent propose sections, liste de contrôles et réponses aux retours ; faire valider les coauteurs. | **Parcours POC.** Pas de soumission ni de suivi éditorial connecté. |
| Transmettre données, code et protocoles | Inventorier les fichiers, versions, accès et points ouverts ; l'agent rédige un mode d'emploi ; inviter le successeur sur la tâche et noter sa réception. | **Parcours POC.** Partage entre comptes locaux sur la tâche ; transfert réel des accès, dépôts et gros volumes hors de Passage. |
| Chercher un poste et candidater | Joindre CV et offre, comparer les compétences aux critères, faire proposer CV/lettre et suivre chaque candidature dans une tâche. | **Parcours POC.** Passage n'interroge pas les sites d'emploi et n'envoie aucune candidature. |
| Explorer une startup | Partir du résultat et d'un besoin supposé ; demander un dossier d'opportunité, les preuves manquantes et des questions pour valorisation/incubateur. | **Parcours POC**, complété par la fiche Opportunité existante. Marché, droits et modèle économique exigent une enquête réelle. |
| Choisir sa prochaine voie | Renseigner préférences, échéances et offres ; l'agent met en regard postdoc, emploi et startup, puis propose des vérifications. | **Parcours POC.** Le tableau aide la décision ; il ne choisit pas pour la personne. |

## R3 — Directeur de thèse

| Tâche | Utilisation de Passage par le directeur et ses agents | État et frontière |
|---|---|---|
| Préparer les réunions d'encadrement | Recevoir les tâches partagées par les doctorants, demander une synthèse à son agent sur les éléments autorisés, commenter les blocages et consigner les décisions. | **Parcours POC.** Boîte de réception des tâches partagées, sans tableau de bord consolidé de tous les doctorants. |
| Relire protocoles et résultats | Ouvrir la tâche partagée, consulter protocole, fichiers et contrôles, demander une critique d'agent, puis donner un avis humain ou une demande de révision. | **Parcours POC.** L'agent ne vérifie ni mesure brute ni sûreté expérimentale. |
| Relire manuscrits et articles | Ouvrir le document de la tâche partagée, lire sa version et citer un passage exact dans un commentaire ou un ancrage ; demander aussi une critique d'agent sur les extraits autorisés. | **Parcours POC.** Commentaires et passages liés à une version, sans édition collaborative avec suivi des modifications. |
| Publier avec les doctorants | Suivre plan, versions, retours et accord des coauteurs dans la tâche ; l'agent prépare sections ou matrice de réponses. | **Parcours POC.** Pas de signature des coauteurs ni de connexion à la revue. |
| Monter des dossiers de financement | Joindre appel et pièces, répartir les étapes, faire proposer argumentaire, plan de travail et risques par un agent. | **Parcours POC.** Budget, éligibilité et dépôt exigent les services habilités. |
| Rendre des rapports aux financeurs | Rassembler convention, jalons et preuves, faire proposer une synthèse des écarts par l'agent, valider puis transmettre le rapport. | **Parcours POC.** Les dépenses et jalons ne sont pas synchronisés avec un système de gestion. |
| Participer aux comités et jurys | Déposer uniquement les pièces autorisées, préparer une grille et des questions avec l'agent, consigner l'avis permis. | **Parcours POC.** Le responsable doit vérifier les règles de confidentialité avant tout recours à un fournisseur externe. |
| Relire pour une revue scientifique | Vérifier la politique de la revue ; si l'usage d'IA est autorisé, joindre les seuls extraits permis et demander une grille critique, puis rédiger son avis. | **Parcours POC technique.** L'autorisation de la revue et la confidentialité restent entièrement à la charge du relecteur. |
| Donner des cours | Organiser séances, supports et évaluations dans une tâche ; l'agent propose explications et exercices ; l'enseignant vérifie corrigés et niveau. | **Parcours POC.** Aucun LMS ou suivi des étudiants. |
| Arbitrer publication et confidentialité | Réunir résultat, calendrier et engagements connus ; demander une note factuelle à l'agent, puis un avis de relecture et consigner le périmètre retenu. | **Parcours POC.** Accord local requis pour clôturer ; ne couvre pas la décision des ayants droit ni les formalités de propriété intellectuelle. |

## R4 — Directeur de laboratoire

| Tâche | Utilisation envisagée ou existante de Passage | État et frontière |
|---|---|---|
| Gérer budget, personnel, équipements et locaux | Relier à chaque projet les ressources engagées, disponibilités et arbitrages pour voir la charge et les échéances. | **À construire.** Aucun module budgétaire, RH ou de réservation. |
| Suivre l'activité du laboratoire | Consulter les notices du corpus, les publications et les indicateurs locaux ; exporter les compteurs. | **Partiel.** Vue du corpus de démonstration, pas de mesure exhaustive de l'activité ni de l'impact réel. |
| Coordonner équipes et résoudre les blocages | Agréger les décisions en attente, besoins et dépendances des projets et confier une synthèse à un agent. | **À construire.** Les tâches R1–R3 se partagent une à une, sans espace multi-équipe. |
| Définir priorités et projet scientifique | Comparer axes, compétences, résultats, coûts et scénarios ; faire préparer des options par des agents. | **À construire.** Les notices seules ne suffisent pas à cet arbitrage. |
| Préparer le rapport annuel | Réutiliser indicateurs et pièces validées pour produire un rapport sourcé par équipe et obtenir leur accord. | **Partiel.** Export CSV de certains indicateurs ; pas de collecte ni de rapport consolidé. |
| Préparer l'évaluation HCERES | Constituer un dossier pluriannuel avec preuves, contrats, thèses, résultats et validation des responsables. | **Partiel.** Quelques indicateurs exportables ; dossier d'évaluation non géré. |
| Négocier conventions et représenter le laboratoire | Préparer une fiche factuelle sur un résultat et ses inconnues avant rendez-vous, puis conserver décision et convention. | **Partiel.** Fiches et sources disponibles ; pas de négociation ni de signature. |
| Contrôler la diffusion des travaux | Examiner, corriger, publier ou retirer les notices du laboratoire avec traçabilité locale. | **Présent pour les notices du POC.** Ne vaut pas autorisation de l'établissement pour tous les documents. |

## R5 — Chargé de valorisation

| Tâche | Utilisation envisagée ou existante de Passage | État et frontière |
|---|---|---|
| Détecter des résultats valorisables | Parcourir les notices, produire des fiches Lecture/Opportunité et repérer applications, maturité et preuves manquantes. | **Partiel.** Présélection sur les notices disponibles ; pas de classement fiable de tous les dossiers. |
| Rencontrer les chercheurs | Préparer les questions de nouveauté, preuves, divulgation et droits, puis conserver les réponses confirmées. | **À construire** comme entretien partagé et suivi de réponses. |
| Recevoir et instruire une déclaration d'invention | Collecter inventeurs, employeurs, financeurs, dates, preuves et pièces, puis suivre les validations. | **À construire.** Aucun formulaire ou circuit institutionnel. |
| Faire une recherche d'antériorité | Comparer les revendications aux publications et brevets externes, garder requêtes, dates et différences. | **À construire.** La fiche Opportunité n'effectue pas cette recherche. |
| Décider et suivre un dépôt de brevet | Constituer le dossier de décision, solliciter les ayants droit et suivre le conseil en propriété intellectuelle et les échéances. | **À construire.** Pas de dépôt, analyse juridique ou suivi de familles. |
| Monter un programme de maturation | Partir des lacunes de la fiche Opportunité, définir essais, jalons, budget, responsables et preuves à obtenir. | **Partiel.** Les fiches suggèrent des vérifications ; le programme et ses moyens ne sont pas suivis. |
| Prospecter des entreprises | Rapprocher une technologie d'un besoin explicite, préparer une proposition et enregistrer contact et suite donnée. | **Partiel.** Rapprochement et signaux locaux ; pas de prospection externe ni de CRM. |
| Rédiger une fiche technologie | Transformer une lecture vérifiée en page factuelle sur problème, résultat, maturité, limites, accès et contact. | **Partiel.** Dossiers Markdown exportables, sans gabarit et approbation de fiche institutionnelle. |
| Négocier confidentialité, licences et contrats | Rassembler faits, titulaires, versions et demandes pour le juriste, puis suivre négociation et décisions. | **À construire.** Aucun cycle contractuel ni signature. |
| Accompagner une création de startup | Relier résultat, besoin, équipe, preuves et interlocuteurs, puis suivre maturation et accès aux droits. | **Partiel.** Dossier Opportunité initial, sans parcours incubateur, financement ou licence. |
| Rendre compte et prioriser le portefeuille | Regrouper dossiers, étapes, preuves, ressources et motifs des priorités pour la direction. | **Partiel.** Compteurs locaux, sans portefeuille de valorisation complet. |

## Lecture transversale

Passage sert déjà de **lieu de travail par projet et par tâche** pour R1–R3 : l'utilisateur cadre, apporte des preuves, demande une proposition à un agent de son équipe, partage une tâche, puis décide. L'agent prépare et critique ; l'utilisateur ou le professionnel habilité reste responsable des faits, des expériences, des soumissions et des décisions. Pour R4–R5, le POC offre surtout le corpus, des fiches et des indicateurs : les circuits de direction et de valorisation restent à concevoir avec leurs utilisateurs.
