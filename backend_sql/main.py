from fastapi import FastAPI
from routers.vehicules_router import router as vehicules_router  # import your router here
from fastapi.responses import JSONResponse
import subprocess
import logging
import os

# FastAPI app setup
app = FastAPI()

# Include the router for Vehicules API endpoints
app.include_router(vehicules_router)

# Set up logging (optional)
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'app.log'),  # Log file in the 'logs' folder
    level=logging.INFO,  # Log all INFO level messages and higher
    format='%(asctime)s - %(levelname)s - %(message)s'
)
