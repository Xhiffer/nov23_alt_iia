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


import json
import requests
from fastapi import FastAPI, File, UploadFile
import random
from pydantic import BaseModel
from typing import Optional, Union
app = FastAPI()


class DonneesAccident(BaseModel):
    sexe: int
    obsm: int
    pr: Union[str, int]
    jour: int
    col: int
    vma_cat: Optional[str] = None
    choc: int
    pr1: Union[str, int]
    mois: int
    age: int
    manv: int
    plan: int
    an: int
    cos_time: float
    n_passager: int
    motor: int
    larrout: int
    lum: int
    sin_time: float
    n_pieton: int
    catr: int
    surf: int
    dep: int
    senc: int
    circ: int
    infra: int
    agg: int
    day_of_week: int
    catv: int
    vosp: int
    situ: int
    int_: int
    obs: int
    prof: int
    atm: int
    is_holiday: int

def dummy_labelisation_model(video_bytes: bytes) -> DonneesAccident:
    """Generate a fake set of accident features (for testing pipeline)."""
    import random
    import math

    return DonneesAccident(
        sexe=random.choice([1, 2]),
        obsm=random.choice([1, 2, 0, 9, 5]),
        pr=str(random.choice(['-1', '18', '0', '7', '2', '6'])),
        jour=random.randint(1, 31),
        col=random.choice([1, 2, 3, 4, 5, 6, 7, -1]),
        vma_cat=random.choice(['0', '1', '2', '3', '4', '5', None]),
        choc=random.choice(range(10)),
        pr1=str(random.choice(['-1', '0', '100', '300', '950'])),
        mois=random.randint(1, 12),
        age=random.randint(18, 90),
        manv=random.choice(range(0, 25)),
        plan=random.choice([1, 2, 3, 4]),
        an=2023,
        cos_time=round(math.cos(random.uniform(0, 2*math.pi)), 3),
        n_passager=random.randint(0, 5),
        motor=random.choice([1, 4, 0, 2, 3, 5, -1, 6]),
        larrout=random.choice([-1, 12, 3, 5, 7, 6, 10, 13]),
        lum=random.choice([1, 2, 3, 4, 5]),
        sin_time=round(math.sin(random.uniform(0, 2*math.pi)), 3),
        n_pieton=random.choice([0, 1]),
        catr=random.choice([1, 2, 3, 4, 6, 7, 9]),
        surf=random.choice([1, 2, 3, 6, 9]),
        dep=random.choice(range(1, 96)),
        senc=random.choice([0, 1, 2, 3]),
        circ=random.choice([1, 2, 3, -1]),
        infra=random.choice([0, 1, 2, 3, 5, 6, 8, 9]),
        agg=random.choice([1, 2]),
        day_of_week=random.choice(range(7)),
        catv=random.choice(list(range(1, 44)) + [50, 60, 80, 99]),
        vosp=random.choice([-1, 0, 1, 2, 3]),
        situ=random.choice([1, 2, 3, 4, 5, 6, 8]),
        int_=random.choice([1, 2, 3, 6, 7, 9]),
        obs=random.choice(range(0, 17)),
        prof=random.choice([1, 2, 4]),
        atm=random.choice([1, 2, 3, 5, 8]),
        is_holiday=random.choice([0, 1]),
    )



@app.post("/labelise_and_estime/")
async def labelise_and_estime(video: UploadFile = File(...)):
    contents = await video.read()

    accident_info = dummy_labelisation_model(contents)

    # Prepare multipart/form-data with JSON as a string + video bytes
    files = {
        "video": (video.filename, contents, video.content_type),
        "accident_info": (None, json.dumps(accident_info.model_dump()), "application/json")
    }

    try:
        response = requests.post(
            "http://ai_model_gravity_classification:81/estimer_gravite",
            files=files
        )
        response.raise_for_status()
        gravite_estimee = response.json().get("gravite_estimee")
    except Exception as e:
        return {"error": f"Failed to contact gravity classification model: {e}"}

    return {"accident_info": accident_info.model_dump(), "gravite_estimee": gravite_estimee}

