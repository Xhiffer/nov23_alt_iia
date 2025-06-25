import random
import requests
from fastapi import FastAPI
from pydantic import BaseModel

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
    gravites_possibles = ['indemne', 'Tué(30j)', 'Blessé hosp. plus de 24h', 'Blessé léger']
    gravite = random.choice(gravites_possibles)

    # Compose data to send to backend API
    payload = accident.model_dump()
    payload['gravite_estimee'] = gravite

    # URL of your backend API endpoint (adjust host if needed)
    backend_url = "http://backend_sql:8000/resultat_ai/"  # or use the container network IP if needed

    # Send POST request to backend
    response = requests.post(backend_url, json=payload)
    response.raise_for_status()  # Raise error if something went wrong
    resultat_ai_response = response.json()

    return {
        "gravite_estimee": gravite,
        "backend_response": resultat_ai_response
    }
