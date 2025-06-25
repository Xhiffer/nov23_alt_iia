

from fastapi import FastAPI
from routers.vehicules_router import router as vehicules_router
from routers.usagers_router import router as usagers_router
from routers.lieux_router import router as lieux_router
from routers.caract_router import router as caract_router

from routers.resultat_ai_router import router as ai_results_router


from fastapi.responses import JSONResponse
import subprocess
import logging
import os

tags_metadata = [
    {
        "name": "Usagers",
        "description": "Opérations liées aux participants d’un accident (usagers)."
    },
    {
        "name": "Véhicules",
        "description": "Gestion des données des véhicules impliqués dans chaque accident."
    },
    {
        "name": "Lieux",
        "description": "Données géographiques et d’infrastructure liées aux lieux des accidents."
    },
    {
        "name": "Caractéristiques",
        "description": "Informations descriptives liées aux circonstances ou types d’accidents."
    },
    {
        "name": "AiResults",
        "description": "résultat des différents mondel d'ia."
    }
]

# FastAPI app setup
app = FastAPI(openapi_tags=tags_metadata)

# Include the router for Vehicules API endpoints
app.include_router(vehicules_router, tags=["Véhicules"])
app.include_router(usagers_router, tags=["Usagers"])
app.include_router(lieux_router, tags=["Lieux"])
app.include_router(caract_router, tags=["Caractéristiques"])
app.include_router(ai_results_router, tags=["AiResults"])







# Set up logging (optional)
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'app.log'),  # Log file in the 'logs' folder
    level=logging.INFO,  # Log all INFO level messages and higher
    format='%(asctime)s - %(levelname)s - %(message)s'
)
