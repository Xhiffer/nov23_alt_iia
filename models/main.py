"""
Objectif du model :
--> valeurs en entrée :
- json variables de l'accident
  -> variables d'accident qu'on peut s'attendre de trouver sur une videéo de sécurité routière
--> retourne gravité estimé de l'accident 


Pour l'instant il nous faut juste :
la fonction qui prend les valeurs en entrée et qui lance une fonction qui renvoie une valeurs randome 

"""


from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI()

class DonneesAccident(BaseModel):
    nombre_vehicules: int
    vitesse_estimee: float
    impact_detecte: bool
    conditions_meteo: str
    presence_pietons: bool
    type_route: str

@app.post("/estimer_gravite")
def estimer_gravite(accident: DonneesAccident):
    """
    Retourne une gravité d'accident estimée de manière aléatoire.
    à voir mais surement possible d'avoir plusieurs personnes // plusieurs états
    """
    gravites_possibles = ['indemne', 'Tué(30j)', 'Blessé hosp. plus de 24h', 'Blessé léger']
    gravite = random.choice(gravites_possibles)
    return {"gravite_estimee": gravite}
