"""
prend la vidéo de 30 secondes en entrée : 
de cette vidéo il va devoir extraire multiples informations + metadonnées

va devoir renvoyer un json avec les informations suivantes :
- nombre de véhicules impliqués
- vitesse estimée des véhicules
- impact détecté (booléen)
- conditions météo (pluie, brouillard, etc.)
- présence de piétons (booléen)
- type de route (autoroute, route nationale, etc.)
- timestamp de l'accident
- localisation GPS (si disponible)

enfin j'ai listé au hasard, on verras plus tard si on en ajoute ou supprime des variables.

puis envoie toute les informations au modele gravity_data_labelisation
pour que celui-ci puisse estimer la gravité de l'accident.
"""