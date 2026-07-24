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

    # 🔍 Look for best finished run
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
        raise RuntimeError("❌ No valid model found in MLflow.")

    run_id = best_run.info.run_id
    artifact_uri = best_run.info.artifact_uri

    print(f"🔍 MLflow reports artifact_uri: {artifact_uri}")

    # -------------------------
    # Try to load the model dynamically from MLflow
    # -------------------------
    try:
        print(f"📦 Trying to load model directly from MLflow (run_id={run_id})...")
        loaded_model = mlflow.sklearn.load_model(f"runs:/{run_id}/model")
        print(f"✅ Model successfully loaded from MLflow run {run_id}")
    except Exception as e:
        print(f"⚠️ Could not load model via run_id ({run_id}). Trying manual MinIO path...")
        print(f"Original MLflow error: {e}")

        # 🔧 Force path to your known valid artifact location in MinIO
        fallback_path = "s3://mlflow/1/models/m-d1d3d692694e415ea5b106f9bf190f53/artifacts/model.pkl"
        try:
            print(f"📦 Forcing load from fallback path: {fallback_path}")
            loaded_model = mlflow.sklearn.load_model(fallback_path)
            print(f"✅ Model successfully loaded from fallback path.")
        except Exception as e2:
            raise RuntimeError(
                f"❌ Failed to load MLflow model even from fallback path.\n"
                f"Run ID: {run_id}\n"
                f"Experiment: {best_experiment}\n"
                f"Original error: {e}\n"
                f"Fallback error: {e2}"
            ) from e2

    # Save info globally
    model = loaded_model
    best_model_info = {
        "experiment": best_experiment,
        "experiment_id": best_exp_id,
        "run_id": run_id,
        "accuracy": best_acc,
        "artifact_uri": artifact_uri,
    }

    print(f"✅ Model ready to use (accuracy={best_acc}, experiment={best_experiment})")






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
