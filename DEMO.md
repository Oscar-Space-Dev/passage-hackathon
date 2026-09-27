# Démonstration Passage — parcours de 2 minutes

## Préparation

Lancer le serveur et ouvrir http://127.0.0.1:8088. Choisir Appels réels si les accès ont été vérifiés. Sinon annoncer explicitement une démonstration du fonctionnement avec résultats simulés ; ne pas présenter les règles de simulation comme des agents LLM.

Le premier démarrage charge les vraies notices. Le cas thermique est 2014DIJOS078 ; les cas de comparaison sont 2019PSLEC037 et s352032. Le programme Pack 2027 est fictif. Préparer les dossiers avant un enregistrement vidéo pour ne pas passer la durée de présentation à attendre les services.

L'instance livrée dispose des quatre agents Gemma locaux activés et de leurs dossiers réels. Dernier rapprochement vérifié : onze notices, scores respectifs 90 / 15 / 5 pour les trois cas ci-dessus. Les appels ont pris environ 82 à 131 secondes ; une relance peut produire d'autres formulations ou scores. Pour revoir le classement enregistré, ouvrir Exécutions et le résultat du Rapprochement réussi, sans relancer le modèle.

## Script

| Temps | À montrer | Message |
|---|---|---|
| 0–15 s | Vue d'ensemble, puis laboratoire LRCS | « Les thèses contiennent des pistes que les entreprises ne trouvent pas. Passage relie leurs deux vocabulaires. » |
| 15–35 s | Import theses.fr, fiche de Félix Bourseau | « Les notices viennent d'une source publique. L'agent distingue les objectifs d'une thèse en cours des résultats acquis. Le directeur choisit ce qui est visible. » |
| 35–65 s | Bibliothèque, cas des vélos électriques, recherche | « L'ingénieur décrit l'échauffement de ses cellules. Chaque piste est expliquée ; les matériaux d'électrode et l'impression 3D ne répondent pas au même besoin que la gestion thermique. » |
| 65–90 s | Thèse de Che Daud, dossier Incorporation | « Le dossier montre ce qui est documenté, les essais à faire, les contacts et les incertitudes. Une étude en décharge automobile ne prouve pas les performances en charge rapide sur un vélo. » |
| 90–105 s | Proposer à Pack 2027, accepter, ouvrir la note | « La note rejoint le programme seulement après une décision humaine. Sans Oscar, ce parcours fonctionne en démonstration locale. » |
| 105–120 s | Espace doctorant et atelier | « Le chercheur voit l'intérêt suscité et garde son nom sur son travail. Les agents sont configurables et leurs harnais versionnés ; Dust et Pipelex sont des moteurs possibles. » |

## Vérifications avant enregistrement

- Lire les résultats réels avant de les présenter ; ne pas promettre l'ordre exact des modèles sans l'avoir observé.
- Préparer un dossier Opportunité et montrer que « à approfondir » ou « défavorable » est une réponse possible.
- Vérifier le badge simulation/réel et la source du programme (démo/Oscar).
- Ne pas afficher de clé API ni le contenu de `.env` dans la vidéo.
- Conserver la déclaration du code préexistant Oscar-AI dans le README de candidature.

Cette fiche prépare la démonstration. Elle n'est pas une vidéo produite ni une candidature déposée.
