"""
idée -->


faire un modèle dummy (la fonction qui prend les valeurs en entrée et qui lance une fonction qui renvoie une valeur)

ne pas la finir mais juste la faire fonctionner

comment elle marche  :

il doit avoir en actif autant de docker que de rtsp://<ip>:<port>/... de la caméra

il va lire en live les flux rtsp des caméras
et pour chaque flux il va faire une détection d'accident
quand un accident est détecté il va envoyer la video -30sc avant l'accident au modele gravity_data_labelisation
AVEC les metadonnées si elles sont disponibles (conditions météo, localisation, etc.)
"""