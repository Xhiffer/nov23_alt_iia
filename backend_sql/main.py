from fastapi import FastAPI
from controllers.livres import router as livre_router
from fastapi.responses import JSONResponse
import subprocess
import logging
import os

# FastAPI app setup
app = FastAPI()

# Include the router for Livre (Book) API endpoints
app.include_router(livre_router)

# Set up logging (optional)
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'app.log'),  # Log file in the 'logs' folder
    level=logging.INFO,  # Log all INFO level messages and higher
    format='%(asctime)s - %(levelname)s - %(message)s'
)