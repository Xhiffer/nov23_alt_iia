import random
import requests
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import json
from pydantic import BaseModel, Field
from datetime import datetime
app = FastAPI()

class DonneesAccident(BaseModel):
    nombre_vehicules: int
    vitesse_estimee: float
    impact_detecte: bool
    conditions_meteo: str
    presence_pietons: bool
    type_route: str
    date_ajout: str = Field(default_factory=lambda: datetime.now().isoformat())

@app.post("/estimer_gravite")
async def estimer_gravite(
    video: UploadFile = File(...),
    accident_info: str = Form(...)
):
    accident = DonneesAccident.parse_raw(accident_info)
    video_bytes = await video.read()

    gravites_possibles = ['indemne', 'Tué(30j)', 'Blessé hosp. plus de 24h', 'Blessé léger']
    gravite = random.choice(gravites_possibles)

    # Prepare payload for backend_sql including gravite
    payload = accident.model_dump()
    payload['gravite_estimee'] = gravite

    # Prepare multipart/form-data for backend_sql
    files = {
        "video": (video.filename, video_bytes, video.content_type),
        "resultat_ai_data": (None, json.dumps(payload), "application/json")  # <-- matches backend parameter name
    }

    backend_url = "http://backend_sql:8000/resultat_ai/"
    response = requests.post(backend_url, files=files)
    response.raise_for_status()
    resultat_ai_response = response.json()

    return {
        "gravite_estimee": gravite,
        "backend_response": resultat_ai_response
    }
