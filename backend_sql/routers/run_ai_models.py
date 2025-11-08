import logging
import os
import subprocess
from fastapi import APIRouter, HTTPException


router = APIRouter()
@router.post("/ai-models/train/{model_name}")
async def train_model(model_name: str):
    """Generic endpoint to run any AI model script"""
    try:
        logging.info(f"Starting {model_name} training...")
        script_path = os.path.join("scripts", "ai_models", f"{model_name}.py")
        
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=404,
                detail=f"Model script not found: {model_name}.py"
            )
        subprocess.Popen(
            ["python", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logging.info(f"{model_name} training started successfully.")
        return {"message": f"{model_name} training started successfully!"}
        
    except Exception as e:
        logging.error(f"Error starting {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))