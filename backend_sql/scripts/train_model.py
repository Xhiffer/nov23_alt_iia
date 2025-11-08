""""
1) on predit la column grav
3) je pene tout utilisé pour le reste mais peut être des test à faire 

5) on va skip pour l'instant je pense j'ai déjà un peut flitré ca 
6) Quelles métriques on utilise ? accuracy ? f1 score ?
7) Très probable que :
Beaucoup d’accidents peu graves,

Peu d’accidents mortels/graves.

Donc, niveau réflexion :

Est-ce que tu gardes toutes les classes de grav ou tu en fusionnes ?

ex. grav_léger, grav_moyen, grav_grave+mortel.

+ de faux positifs sur les classes peu graves, ça passe.

Tu peux envisager :
pondérer les classes dans le modèle,
ou sur-échantillonner les cas graves ?


8) faut qu'on utilisé MLflow pour géré les différents résultats
9) vérifié les bias ?
10) remettre en question
"""




"""1) set up le script pour se lancé dans le dag """



"""
now let's think what model to use :

no first we need to do general trainning setup ?

what do we need ?

1) 
"""



"""
filtres de données des choses à faire encore mais on skip pour l'instant.

donc mtn :

1) lister des models à tester : 
    LogisticRegression ---> rapide, interprétable, bonne baseline globale, capte mal les interactions non linéaires
    DecisionTreeClassifier ---> donne une intuition sur quelles features sont importantes, vite overfit, surtout si pas bien réglé

2) setup le script de trainning model :
    a) load data filtré
    b) séparer features / target
    c) split train/test --> same for all data ? (on skip pas le temps)
    d) entrainé model
    e) évalué model
    f) sauvegardé model + métriques (mlflow ?)
3) le mettre dans airflow dag
"""


import sys
import os
import traceback
import logging
import numpy as np
# Logging setup
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'train_model.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
try:
    sys.path.append("/app")
    from routers.ai_training_model_data_router import get_all_ai_training_data
    import pandas as pd
    from database import SessionLocal
    from general_tain_setup import remove_excluded_columns, remove_lat_long_columns
    db = SessionLocal()



    data = get_all_ai_training_data(db)
    if data:
        rows = [obj.__dict__ for obj in data]
        df = pd.DataFrame(rows)
    else:
        logging.info("No data found.")
    df = remove_excluded_columns(df)
    df = remove_lat_long_columns(df)

    if __name__ == "__main__":  
        print("train_model script started")
except Exception as e:
    logging.error(f"train_model import An error occurred: {e}\n{traceback.format_exc()}")



