import logging
import os
import subprocess
from fastapi import APIRouter, HTTPException


router = APIRouter()
@router.post("/ai-models/train/{model_name}")
async def train_model(model_name: str):
    """Run an AI model training script synchronously and surface failures.

    Blocking on purpose: the caller (Airflow SimpleHttpOperator) must fail if
    training fails, instead of the previous fire-and-forget that always reported
    success even when no model was produced.
    """
    script_path = os.path.join("scripts", "ai_models", f"{model_name}.py")
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Model script not found: {model_name}.py")

    logging.info(f"Starting {model_name} training...")
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except subprocess.TimeoutExpired:
        logging.error(f"{model_name} training timed out")
        raise HTTPException(status_code=504, detail=f"{model_name} training timed out")

    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "")[-1000:]
        logging.error(f"{model_name} training failed (exit {result.returncode}): {tail}")
        raise HTTPException(status_code=500, detail=f"{model_name} training failed: {tail}")

    logging.info(f"{model_name} training finished successfully.")
    return {"message": f"{model_name} training completed successfully!"}