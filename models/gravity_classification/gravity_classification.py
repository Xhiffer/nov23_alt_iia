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

import time
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# -----------------------
# Prometheus monitoring
# -----------------------
# Standard HTTP metrics (request count, latency, in-progress...) + /metrics endpoint.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ML-specific metrics.
PREDICTIONS_TOTAL = Counter(
    "gravity_predictions_total",
    "Nombre de prédictions par classe de gravité prédite.",
    ["predicted_class"],
)
PREDICTION_PROBABILITY = Histogram(
    "gravity_prediction_probability",
    "Distribution de la probabilité (confiance) de la classe prédite.",
    buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0),
)
PREDICT_LATENCY = Histogram(
    "gravity_predict_latency_seconds",
    "Latence de l'inférence du modèle (hors overhead HTTP).",
)
PREDICT_ERRORS_TOTAL = Counter(
    "gravity_predict_errors_total",
    "Nombre d'erreurs survenues pendant l'inférence.",
)

# -----------------------
# Pydantic models
# -----------------------

class DonneesAccident(BaseModel):
    manv: int
    plan: int
    mois: int
    age: int
    n_passager: int
    motor: int
    larrout: int
    an: int
    cos_time: float
    n_pieton: int
    catr: int
    surf: int
    lum: int
    sin_time: float
    senc: int
    circ: int
    infra: int
    dep: int
    catv: int
    vosp: int
    situ: int
    agg: int
    day_of_week: int
    obs: int
    prof: int
    int_: int
    sexe: int
    obsm: int
    pr: Union[str, int]
    jour: int
    atm: int
    is_holiday: int
    choc: int
    pr1: Union[str, int]
    col: int
    vma_cat: Optional[str] = None



# -----------------------
# Global variable for model
# -----------------------
model = None
best_model_info = None


# -----------------------
# Internal helpers
# -----------------------
MODEL_NAME = "gravity_classification"


def _load_best_model_internal():
    """Load the production model: prefer the MLflow Registry 'champion' alias,
    else fall back to the best non-failed run by accuracy."""
    global model, best_model_info

    mlflow.set_tracking_uri("http://mlflow:5000")
    client = MlflowClient()

    # 1) Preferred: MLflow Model Registry champion alias
    try:
        mv = client.get_model_version_by_alias(MODEL_NAME, "champion")
        loaded_model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@champion")
        run = client.get_run(mv.run_id)
        model = loaded_model
        best_model_info = {
            "source": "registry:champion",
            "model_name": MODEL_NAME,
            "version": mv.version,
            "run_id": mv.run_id,
            "f1_macro": run.data.metrics.get("f1_macro"),
            "accuracy": run.data.metrics.get("accuracy"),
        }
        print(f"✅ Loaded champion {MODEL_NAME} v{mv.version}")
        return
    except Exception as e:
        print(f"⚠️ No champion alias available ({e}); falling back to best run by accuracy.")

    # 2) Fallback: best non-failed run by accuracy in the training experiment
    best_run = None
    best_acc = -1.0
    exp = client.get_experiment_by_name("random_forest_training")
    if exp:
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            filter_string="attributes.status != 'FAILED'",
            order_by=["metrics.accuracy DESC"],
            max_results=1,
        )
        if runs:
            best_run = runs[0]
            best_acc = best_run.data.metrics.get("accuracy", 0)

    if not best_run:
        raise RuntimeError("❌ No valid model found in MLflow (no champion alias and no run).")

    run_id = best_run.info.run_id
    loaded_model = mlflow.sklearn.load_model(f"runs:/{run_id}/model")
    model = loaded_model
    best_model_info = {
        "source": "run:best_accuracy",
        "run_id": run_id,
        "accuracy": best_acc,
        "f1_macro": best_run.data.metrics.get("f1_macro"),
    }
    print(f"✅ Loaded fallback model run {run_id} (accuracy={best_acc})")






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

    # Run prediction (timed + instrumented for Prometheus)
    start = time.perf_counter()
    try:
        pred = model.predict(data)[0]

        # Optional: probability if the model supports predict_proba
        proba = None
        if hasattr(model, "predict_proba"):
            proba_arr = model.predict_proba(data)
            proba = float(np.max(proba_arr[0]))
    except Exception:
        PREDICT_ERRORS_TOTAL.inc()
        raise
    finally:
        PREDICT_LATENCY.observe(time.perf_counter() - start)

    # Record ML metrics
    PREDICTIONS_TOTAL.labels(predicted_class=str(int(pred))).inc()
    if proba is not None:
        PREDICTION_PROBABILITY.observe(proba)

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
        "resultat_ai_data": (None, json.dumps(payload), "text/plain; charset=utf-8"),
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
