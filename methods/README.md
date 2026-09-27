# Méthodes Passage

Les quatre méthodes historiques sont exportées depuis les profils initiaux et validées avec Pipelex 0.65.0. Chacune représente une méthode autonome ; elles déclarent le même point d'entrée `passage.analyze` et doivent être chargées séparément, pas dans une seule bibliothèque. La méthode doctorale décrite plus bas utilise le point d'entrée distinct `passage_recherche.assist`.

Pour les quatre méthodes historiques, l'entrée `request` est un texte JSON contenant le rôle, le besoin, les notices autorisées, les citations candidates et l'historique éventuel. La sortie est un rapport JSON ; Passage vérifie ensuite son schéma, les identifiants, les citations et l'exhaustivité du classement.

L'export de l'atelier reflète la révision enregistrée de l'agent choisi. Les fichiers de ce dossier sont des exemples reproductibles, pas des méthodes déjà publiées dans le service Pipelex. Après édition du harnais, réexporter et publier une référence versionnée avant utilisation hébergée.

`recherche_doctorale.mthds` est une méthode supplémentaire pour les projets de doctorat. Elle reçoit un texte `request` décrivant la tâche, les sources, les données et les contraintes ; elle prépare un livrable JSON pour rédaction, protocole expérimental, simulation ou logiciel scientifique. Elle ne lance ni expérience physique, ni simulation, ni test logiciel. Elle est exportable depuis **Connexions → Pipelex**. Une copie est enregistrée dans le catalogue privé Pipelex du compte utilisé pour la recette, validée par le service hébergé ; l’autorisation de `pipelex_run` et une première inférence réelle restent à effectuer.

Validation : `.\.venv\Scripts\python.exe scripts\validate_pipelex.py`. Ce script régénère les quatre fichiers à partir des profils initiaux et utilise un traitement à blanc, sans appel aux modèles.

Pour valider la méthode doctorale isolément, utiliser `validate_bundle` avec `Pipelex.make(needs_inference=False, config_dir='.pipelex')`. Cette validation vérifie la structure et la simulation du pipe ; elle ne prouve pas la qualité scientifique d'une réponse réelle.
