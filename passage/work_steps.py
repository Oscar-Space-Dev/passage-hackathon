"""Concrete human and agent routes for each step of every R1–R3 task."""


def step(agent_help, evidence, tool, external=False):
    return {'agent_help': agent_help, 'evidence': evidence,
            'tool': tool, 'external': external}


RECIPES = {
    'r1-literature': [
        step('Reformuler la requête et signaler les critères ambigus.', 'Question et critères consignés.', 'questions'),
        step('Préparer une fiche par texte effectivement fourni.', 'Articles joints et fiches datées.', 'file'),
        step('Comparer méthodes, résultats et limites source par source.', 'Lignes de fiches et passages vérifiés.', 'register'),
        step('Repérer les lacunes et lectures prioritaires sans inventer de référence.', 'Liste motivée des sources à approfondir.', 'document'),
    ],
    'r1-state-art': [
        step('Proposer des thèmes issus des fiches validées.', 'Plan thématique et sources retenues.', 'questions'),
        step('Mettre en parallèle convergences et contradictions.', 'Tableau comparatif avec passages sourcés.', 'register'),
        step('Rédiger une synthèse avec inconnues explicites.', 'Document de synthèse versionné.', 'document'),
        step('Contrôler la présence de sources pour les affirmations.', 'Références vérifiées et contribution située.', 'anchor'),
    ],
    'r1-hypotheses': [
        step('Rendre la question observable et relever les variables manquantes.', 'Question mesurable renseignée.', 'questions'),
        step('Proposer des hypothèses alternatives réfutables.', 'Registre des hypothèses concurrentes.', 'register'),
        step('Déduire des prédictions distinctes, sans les présenter comme mesurées.', 'Prédictions et unités dans le registre.', 'register'),
        step('Comparer les tests qui départagent les hypothèses.', 'Critères de réfutation revus avec l’encadrant.', 'share', True),
    ],
    'r1-experiment-design': [
        step('Lister facteurs, témoins et variables confondantes.', 'Tableau des variables et témoins.', 'register'),
        step('Mettre en forme les opérations et mesures du protocole.', 'Protocole ou schéma versionné.', 'diagram'),
        step('Proposer contrôles, unités, analyse et critères d’arrêt.', 'Plan de mesure et d’analyse documenté.', 'document'),
        step('Préparer les questions pour la personne responsable.', 'Avis et approbation du protocole.', 'share', True),
    ],
    'r1-experiment-run': [
        step('Préparer une liste de prérequis sans déclarer leur validation.', 'Protocole et autorisations disponibles.', 'questions'),
        step('Préparer une fiche d’essai ; la manipulation reste humaine.', 'Essai conduit et preuve datée par l’expérimentateur.', 'evidence', True),
        step('Comparer les paramètres et écarts consignés au protocole.', 'Ligne d’essai avec réglages et incidents.', 'register'),
        step('Signaler mesures ou métadonnées manquantes.', 'Données brutes et compte rendu joints.', 'file'),
    ],
    'r1-notebook': [
        step('Préparer les champs date, auteur et essai.', 'Entrée datée et attribuée.', 'register'),
        step('Rapprocher protocole, essai et fichiers déposés.', 'Versions et données liées à l’entrée.', 'file'),
        step('Repérer corrections et incidents non expliqués.', 'Historique des écarts et corrections.', 'register'),
        step('Faire une revue de complétude de l’entrée.', 'Contrôle humain de la traçabilité.', 'share'),
    ],
    'r1-code': [
        step('Formaliser interface, unités et cas limites du programme.', 'Spécification des entrées et sorties.', 'questions'),
        step('Proposer une implémentation dans un document de code.', 'Code versionné avec mode d’emploi.', 'document'),
        step('Préparer des tests ; l’exécution autorisée reste humaine.', 'Sorties de tests et environnement consignés.', 'evidence', True),
        step('Comparer les versions et interpréter les échecs connus.', 'Version retenue et résultats liés.', 'register'),
    ],
    'r1-data': [
        step('Décrire colonnes, unités, valeurs manquantes et exclusions.', 'Dictionnaire et règles d’exclusion.', 'questions'),
        step('Proposer le traitement ; calculer localement la description CSV si demandé.', 'Script ou calcul avec paramètres et source.', 'file'),
        step('Signaler unités ou incertitudes non documentées.', 'Contrôles et incertitudes consignés.', 'register'),
        step('Séparer chiffres calculés, hypothèses et interprétation.', 'Rapport d’analyse relu par le doctorant.', 'document'),
    ],
    'r1-supervision': [
        step('Résumer résultats, preuves et blocages connus.', 'Note de réunion sourcée.', 'document'),
        step('Préparer les questions à poser à l’encadrant.', 'Ordre du jour et pièces partagées.', 'share'),
        step('Structurer les réponses reçues sans inventer de décision.', 'Commentaires de l’encadrant.', 'register', True),
        step('Transformer les décisions confirmées en actions.', 'Compte rendu et responsables des suites.', 'document'),
    ],
    'r1-writing': [
        step('Proposer plan et fil de l’argument.', 'Plan des sections et contribution.', 'questions'),
        step('Rédiger une section à partir des seules pièces autorisées.', 'Document de manuscrit versionné.', 'document'),
        step('Repérer affirmations sans source ou donnée.', 'Passages sourcés et lacunes visibles.', 'anchor'),
        step('Préparer les corrections demandées par les relecteurs.', 'Commentaires et nouvelle version déposée.', 'document'),
    ],
    'r1-reviewers': [
        step('Numéroter et classer chaque remarque reçue.', 'Registre des commentaires originaux.', 'register'),
        step('Proposer action et analyse par remarque.', 'Modification ou analyse liée à chaque ligne.', 'register'),
        step('Comparer ancienne et nouvelle version du manuscrit.', 'Document révisé et passages localisés.', 'document'),
        step('Rédiger une réponse point par point à relire.', 'Lettre et accord des auteurs.', 'document'),
    ],
    'r1-conference': [
        step('Adapter le message au public et à la durée.', 'Résumé et message principal.', 'questions'),
        step('Sélectionner seulement les chiffres et figures vérifiés.', 'Résultats autorisés et fichiers de figures.', 'file'),
        step('Proposer la structure du poster ou de la présentation.', 'Support ou plan versionné.', 'document'),
        step('Signaler les contenus dont le droit de diffusion est inconnu.', 'Accord de diffusion daté.', 'evidence', True),
    ],
    'r1-committee': [
        step('Rapprocher objectifs, travaux et pièces du projet.', 'Tableau des jalons et preuves.', 'register'),
        step('Décrire écarts et progrès sans masquer les inconnues.', 'Rapport d’avancement versionné.', 'document'),
        step('Préparer risques et options de suite.', 'Questions et scénarios pour le comité.', 'questions'),
        step('Structurer les recommandations effectivement reçues.', 'Compte rendu ou avis du comité.', 'evidence', True),
    ],
    'r1-teaching': [
        step('Adapter objectifs à niveau et durée.', 'Objectifs pédagogiques renseignés.', 'questions'),
        step('Proposer supports et exercices progressifs.', 'Documents de séance et exercices.', 'document'),
        step('Repérer erreurs ou ambiguïtés des corrigés.', 'Corrigés relus et références vérifiées.', 'document'),
        step('Classer les retours après la séance.', 'Observations et adaptations du cours.', 'register', True),
    ],
    'r1-defense': [
        step('Résumer contributions, preuves et limites.', 'Arguments de soutenance sourcés.', 'register'),
        step('Proposer trame orale et questions possibles.', 'Présentation ou notes d’oral.', 'document'),
        step('Comparer options de carrière selon les critères fournis.', 'Tableau des options et inconnues.', 'register'),
        step('Transformer la préférence humaine en démarches datées.', 'Plan de transition décidé par le doctorant.', 'questions'),
    ],
    'r1-disclosure': [
        step('Inventorier les résultats envisagés pour diffusion.', 'Liste des contenus et versions.', 'register'),
        step('Relever contrats, publications et droits inconnus.', 'Pièces et inconnues juridiques signalées.', 'file'),
        step('Préparer les questions aux ayants droit sans trancher.', 'Avis des personnes habilitées.', 'share', True),
        step('Mettre en forme le périmètre autorisé.', 'Décision et accord datés.', 'evidence', True),
    ],
    'r2-manuscript': [
        step('Transformer les demandes du jury en éléments suivis.', 'Registre des corrections du jury.', 'register'),
        step('Proposer et appliquer des corrections dans un brouillon.', 'Manuscrit final versionné.', 'document'),
        step('Comparer chaque demande au passage modifié.', 'Contrôle par ligne et version.', 'register'),
        step('Préparer la liste de dépôt ; le docteur dépose.', 'Confirmation du dépôt institutionnel.', 'evidence', True),
    ],
    'r2-articles': [
        step('Repérer les analyses et limites encore ouvertes.', 'Résultats et calculs vérifiés.', 'register'),
        step('Proposer sections, figures et révisions.', 'Article versionné.', 'document'),
        step('Lister les points à soumettre aux coauteurs.', 'Accord des coauteurs sur la version.', 'share', True),
        step('Préparer les pièces et suivre les retours.', 'Accusé de soumission et état éditorial.', 'evidence', True),
    ],
    'r2-handover': [
        step('Dresser l’inventaire des ressources et versions.', 'Liste des données, codes et protocoles.', 'register'),
        step('Rédiger la procédure de reprise et les dépendances.', 'Guide de reproduction versionné.', 'document'),
        step('Signaler les accès à transférer par les responsables.', 'Accès transférés dans les systèmes autorisés.', 'evidence', True),
        step('Préparer la liste de vérification du destinataire.', 'Accusé de réception du successeur.', 'evidence', True),
    ],
    'r2-jobs': [
        step('Comparer offres et critères personnels.', 'Offre, échéance et critères consignés.', 'register'),
        step('Adapter CV et lettre aux éléments partageables.', 'Documents de candidature versionnés.', 'document'),
        step('Repérer résultats soumis à confidentialité.', 'Contenus publiables contrôlés.', 'questions'),
        step('Préparer un suivi ; le candidat envoie lui-même.', 'Preuve d’envoi et statut de candidature.', 'evidence', True),
    ],
    'r2-startup': [
        step('Formuler un problème client sans supposer sa validation.', 'Usage et hypothèses de besoin.', 'questions'),
        step('Séparer preuves techniques, marché et droits à vérifier.', 'Registre des hypothèses et preuves.', 'register'),
        step('Préparer les questions à valorisation et incubateur.', 'Échanges réellement tenus.', 'evidence', True),
        step('Assembler un dossier d’opportunité prudent.', 'Premier dossier versionné.', 'document'),
    ],
    'r2-decision': [
        step('Faire expliciter priorités et contraintes personnelles.', 'Critères de décision renseignés.', 'questions'),
        step('Comparer postdoc, emploi et startup sans choisir.', 'Tableau d’options avec inconnues.', 'register'),
        step('Signaler dates et hypothèses à confirmer.', 'Échéances et offres vérifiées.', 'file'),
        step('Transformer le choix humain en actions datées.', 'Décision personnelle et plan d’action.', 'document'),
    ],
    'r3-supervision': [
        step('Synthétiser progrès et blocages partagés par le doctorant.', 'Point d’avancement et preuves.', 'register'),
        step('Préparer ordre du jour et questions critiques.', 'Note de réunion.', 'document'),
        step('Structurer options sans décider à la place du directeur.', 'Arbitrages du directeur.', 'questions', True),
        step('Mettre en forme décisions et responsables.', 'Compte rendu et prochaines dates.', 'document'),
    ],
    'r3-protocols': [
        step('Comparer hypothèses, témoins et critères de qualité.', 'Grille de contrôle du protocole.', 'register'),
        step('Décrire calculs visibles et incohérences possibles.', 'Données, résultats et passages examinés.', 'file'),
        step('Proposer les corrections et vérifications discriminantes.', 'Demandes de correction suivies.', 'register'),
        step('Comparer la nouvelle version aux remarques.', 'Avis scientifique signé par le directeur.', 'document', True),
    ],
    'r3-manuscripts': [
        step('Reconstituer l’argument et les contributions.', 'Plan et version examinée.', 'questions'),
        step('Pointer affirmations, figures et preuves insuffisantes.', 'Passages sourcés ou à corriger.', 'anchor'),
        step('Proposer des commentaires localisés.', 'Commentaires liés à une version.', 'document'),
        step('Comparer la révision aux demandes formulées.', 'Décision de relecture du directeur.', 'share', True),
    ],
    'r3-publication': [
        step('Lister contributions et points d’accord des coauteurs.', 'Registre de contributions.', 'register'),
        step('Proposer plan et corrections de l’article.', 'Manuscrit versionné.', 'document'),
        step('Recenser les accords manquants sans les inventer.', 'Accord explicite des coauteurs.', 'evidence', True),
        step('Préparer la réponse éditoriale et son suivi.', 'Accusé de soumission et retours.', 'evidence', True),
    ],
    'r3-funding': [
        step('Extraire les critères de l’appel fourni.', 'Appel, échéance et critères conservés.', 'file'),
        step('Proposer objectifs, lots de travail et risques.', 'Programme scientifique versionné.', 'document'),
        step('Structurer postes et hypothèses sans valider le budget.', 'Budget approuvé par les services.', 'register', True),
        step('Préparer la liste des pièces puis contrôler la version.', 'Accord et preuve de dépôt.', 'evidence', True),
    ],
    'r3-funder-report': [
        step('Lister jalons, livrables et preuves convenus.', 'Tableau contractuel des jalons.', 'register'),
        step('Comparer prévu et réalisé à partir des pièces.', 'Résultats et dépenses vérifiés.', 'file'),
        step('Rédiger une explication sourcée des écarts.', 'Rapport d’avancement versionné.', 'document'),
        step('Préparer le contrôle final et la transmission.', 'Validation et accusé de transmission.', 'evidence', True),
    ],
    'r3-jury': [
        step('Préparer une grille selon les seules pièces autorisées.', 'Dossier et règles de confidentialité.', 'file'),
        step('Proposer des questions ; l’appréciation reste personnelle.', 'Questions et notes autorisées.', 'register'),
        step('Préparer un aide-mémoire ; la séance reste humaine.', 'Séance tenue et présence attestée.', 'evidence', True),
        step('Limiter le compte rendu aux éléments conservables.', 'Avis autorisé et pièce de séance.', 'document', True),
    ],
    'r3-peer-review': [
        step('Résumer les consignes de la revue et le droit d’usage de l’IA.', 'Politique de confidentialité et autorisation.', 'evidence', True),
        step('Critiquer méthode et portée sur les seuls extraits autorisés.', 'Grille méthodologique et limites.', 'register'),
        step('Proposer une structure d’avis à signer personnellement.', 'Rapport confidentiel versionné.', 'document'),
        step('Préparer la vérification finale ; le relecteur soumet.', 'Accusé de soumission de l’avis.', 'evidence', True),
    ],
    'r3-teaching': [
        step('Organiser objectifs, séances et calendrier.', 'Plan de cours par séance.', 'register'),
        step('Proposer supports et évaluations adaptés au niveau.', 'Documents de cours versionnés.', 'document'),
        step('Repérer erreurs et équité du corrigé.', 'Corrigés et barèmes vérifiés.', 'document'),
        step('Classer les retours pour adapter le cours.', 'Cours donné et retours consignés.', 'evidence', True),
    ],
    'r3-disclosure': [
        step('Inventorier contenus et partenaires concernés.', 'Registre des contenus sensibles.', 'register'),
        step('Préparer les questions aux ayants droit et à la valorisation.', 'Avis réels des parties habilitées.', 'share', True),
        step('Comparer scénarios de dates et périmètres.', 'Décision humaine sur la diffusion.', 'questions', True),
        step('Formaliser les motifs sans inventer d’accord.', 'Autorisation datée et périmètre.', 'evidence', True),
    ],
}
