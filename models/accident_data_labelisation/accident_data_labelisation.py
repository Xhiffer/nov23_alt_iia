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

accident_data_labelisation.py :
fonctione avec fastapi
il attend une video de 30 secondes en entrée,
et renvoie un json avec les informations de l'accident.
--> le json pour l'instant est aléatoire, mais il faut que la fonction soit prête à recevoir les données de la vidéo et à les traiter.


les données qu'on va envoyer au modèle gravity_data_labelisation sont les suivantes :

class DonneesAccident(BaseModel):
    nombre_vehicules: int
    vitesse_estimee: float
    impact_detecte: bool
    conditions_meteo: str
    presence_pietons: bool
    type_route: str
"""


import random
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Modèle de données pour un accident
class DonneesAccident(BaseModel):
    nombre_vehicules: int
    vitesse_estimee: float
    impact_detecte: bool
    conditions_meteo: str
    presence_pietons: bool
    type_route: str

def dummy_labelisation_model(video_bytes: bytes) -> DonneesAccident:
    """
    Simule le traitement d'une vidéo pour en extraire des données d'accident.
    (Version fictive pour test)
    """
    return DonneesAccident(
        nombre_vehicules=random.randint(1, 5),
        vitesse_estimee=round(random.uniform(10, 130), 2),
        impact_detecte=random.choice([True, False]),
        conditions_meteo=random.choice(["ensoleillé", "pluie", "neige", "brouillard"]),
        presence_pietons=random.choice([True, False]),
        type_route=random.choice(["autoroute", "route nationale", "zone urbaine"])
    )

@app.post("/labelise_and_estime/")
async def labelise_and_estime(video: UploadFile = File(...)):
    contents = await video.read()
    # Step 1: Labelise accident (dummy)
    accident_info = dummy_labelisation_model(contents)

    # Step 2: Estimate severity
    response = client.post("/estimer_gravite", json=accident_info.dict())
    severity = response.json()

    return {
        "infos_accident": accident_info.dict(),
        "gravite_estimee": severity["gravite_estimee"]
    }
