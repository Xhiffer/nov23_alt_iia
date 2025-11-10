import requests
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import json
from datetime import datetime

# --- MLflow imports ---
import mlflow
import mlflow.sklearn
import mlflow
from mlflow.tracking import MlflowClient

import numpy as np
import pandas as pd
from typing import Optional, Union

app = FastAPI()

# -----------------------
# Pydantic models
# -----------------------

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


# -----------------------
# Global variable for model
# -----------------------
model = None
best_model_info = None


# -----------------------
# Internal helpers
# -----------------------
def _load_best_model_internal():
    """Internal: load best MLflow model across experiments."""
    global model, best_model_info

    mlflow.set_tracking_uri("http://mlflow:5000")
    client = MlflowClient()
    experiment_names = ["random_forest_training"]

    best_run = None
    best_acc = -1.0
    best_experiment = None
    best_exp_id = None

    for exp_name in experiment_names:
        exp = client.get_experiment_by_name(exp_name)
        if not exp:
            continue

        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            filter_string="attributes.status != 'FAILED'",
            order_by=["metrics.accuracy DESC"],
            max_results=1,
        )

        if runs:
            run = runs[0]
            acc = run.data.metrics.get("accuracy", 0)
            if acc > best_acc:
                best_acc = acc
                best_run = run
                best_experiment = exp_name
                best_exp_id = exp.experiment_id

    if not best_run:
        raise RuntimeError("No valid model found in MLflow.")

    run_id = best_run.info.run_id
    artifact_uri = best_run.info.artifact_uri

    print(f"🔍 Base artifact_uri reported by MLflow: {artifact_uri}")

    # 🔧 Patch the path if needed (add '/models/')
    # Because your real models are stored under mlflow/1/models/<run_id>/artifacts
    if "/models/" not in artifact_uri:
        parts = artifact_uri.split("/")
        if parts[3].isdigit():  # experiment id
            parts.insert(4, "models")
            artifact_uri = "/".join(parts)
            print(f"🔧 Adjusted artifact_uri to: {artifact_uri}")

    try:
        loaded_model = mlflow.sklearn.load_model(artifact_uri)
        print(f"✅ Model successfully loaded from {artifact_uri}")
    except Exception as e:
        raise RuntimeError(
            f"❌ Failed to load MLflow model from {artifact_uri} "
            f"(run_id={run_id}, experiment={best_experiment})\nOriginal error: {e}"
        ) from e

    model = loaded_model
    best_model_info = {
        "experiment": best_experiment,
        "experiment_id": best_exp_id,
        "run_id": run_id,
        "accuracy": best_acc,
        "artifact_uri": artifact_uri,
    }





def _predict_from_donnees(accident: DonneesAccident) -> dict:
    """Core prediction logic using the loaded model and a DonneesAccident instance."""
    global model, best_model_info

    # Lazy-load model if not loaded yet
    if model is None:
        _load_best_model_internal()

    # Convert to DataFrame matching training features
    data = pd.DataFrame([accident.model_dump()])

    # No extra preprocessing here, because:
    # - your training logs show all these columns already numeric/encoded
    # - the model was trained directly on these 36 features

    # Run prediction
    pred = model.predict(data)[0]

    # Optional: probability if the model supports predict_proba
    proba = None
    if hasattr(model, "predict_proba"):
        proba_arr = model.predict_proba(data)
        proba = float(np.max(proba_arr[0]))

    return {
        "gravite_estimee": int(pred),
        "probabilite": proba,
        "model_info": best_model_info,
    }


# -----------------------
# 1️⃣ Load best model from MLflow (explicit)
# -----------------------
@app.post("/load_best_model")
def load_best_model():
    try:
        _load_best_model_internal()
        return {"message": "✅ Model loaded successfully", "best_model_info": best_model_info}
    except Exception as e:
        return {"error": str(e)}


# -----------------------
# 2️⃣ Predict endpoint using the loaded model
# -----------------------
@app.post("/predict_gravite")
def predict_gravite(accident: DonneesAccident):
    result = _predict_from_donnees(accident)
    return result


# -----------------------
# 3️⃣ Endpoint that takes video + JSON, calls model, sends to backend_sql
# -----------------------
@app.post("/estimer_gravite")
async def estimer_gravite(
    video: UploadFile = File(...),
    accident_info: str = Form(...)
):
    # Parse accident features from JSON string
    accident = DonneesAccident.parse_raw(accident_info)
    video_bytes = await video.read()

    # Use the ML model to estimate gravity
    prediction_result = _predict_from_donnees(accident)
    gravite = prediction_result["gravite_estimee"]

    # Prepare payload for backend_sql including gravite
    payload = accident.model_dump()
    payload["gravite_estimee"] = gravite

    files = {
        "video": (video.filename, video_bytes, video.content_type),
        "resultat_ai_data": (None, json.dumps(payload), "application/json"),
    }

    backend_url = "http://backend_sql:8000/resultat_ai/"
    response = requests.post(backend_url, files=files)
    response.raise_for_status()
    resultat_ai_response = response.json()

    return {
        "gravite_estimee": gravite,
        "prediction_details": prediction_result,
        "backend_response": resultat_ai_response,
    }
