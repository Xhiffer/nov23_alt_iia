import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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

from canary import read_canary_pct, should_route_to_canary, CHAMPION, CANARY

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
    ["predicted_class", "model_role"],
)
CANARY_REQUESTS_TOTAL = Counter(
    "gravity_canary_requests_total",
    "Nombre de requêtes servies par rôle de modèle (champion vs canary).",
    ["model_role"],
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
# Canary (challenger) served to a fraction of traffic for live comparison.
canary_model = None
canary_model_info = None


# -----------------------
# Internal helpers
# -----------------------
MODEL_NAME = "gravity_classification"


def _load_canary_internal(client, champion_version=None):
    """Charge le modèle 'challenger' comme canary, s'il existe et diffère du champion.
    Sans challenger (ou identique au champion), le canary est désactivé."""
    global canary_model, canary_model_info
    canary_model = None
    canary_model_info = None
    try:
        cv = client.get_model_version_by_alias(MODEL_NAME, "challenger")
    except Exception:
        print("ℹ️ No challenger alias; canary disabled.")
        return
    if champion_version is not None and str(cv.version) == str(champion_version):
        print("ℹ️ Challenger == champion; canary disabled.")
        return
    try:
        canary_model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@challenger")
        run = client.get_run(cv.run_id)
        canary_model_info = {
            "source": "registry:challenger",
            "model_name": MODEL_NAME,
            "version": cv.version,
            "run_id": cv.run_id,
            "f1_macro": run.data.metrics.get("f1_macro"),
            "accuracy": run.data.metrics.get("accuracy"),
        }
        print(f"🐤 Loaded canary (challenger) {MODEL_NAME} v{cv.version}")
    except Exception as e:
        print(f"⚠️ Failed to load challenger as canary ({e}); canary disabled.")
        canary_model = None
        canary_model_info = None


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
        _load_canary_internal(client, champion_version=mv.version)
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
    global model, best_model_info, canary_model, canary_model_info

    # Lazy-load model if not loaded yet
    if model is None:
        _load_best_model_internal()

    # Canary routing: send CANARY_TRAFFIC_PCT% of traffic to the challenger.
    role = CHAMPION
    active_model = model
    active_info = best_model_info
    if canary_model is not None and should_route_to_canary(read_canary_pct()):
        role = CANARY
        active_model = canary_model
        active_info = canary_model_info
    CANARY_REQUESTS_TOTAL.labels(model_role=role).inc()

    # Convert to DataFrame matching training features
    data = pd.DataFrame([accident.model_dump()])

    # No extra preprocessing here, because:
    # - your training logs show all these columns already numeric/encoded
    # - the model was trained directly on these 36 features

    # Run prediction (timed + instrumented for Prometheus)
    start = time.perf_counter()
    try:
        pred = active_model.predict(data)[0]

        # Optional: probability if the model supports predict_proba
        proba = None
        if hasattr(active_model, "predict_proba"):
            proba_arr = active_model.predict_proba(data)
            proba = float(np.max(proba_arr[0]))
    except Exception:
        PREDICT_ERRORS_TOTAL.inc()
        raise
    finally:
        PREDICT_LATENCY.observe(time.perf_counter() - start)

    # Record ML metrics
    PREDICTIONS_TOTAL.labels(predicted_class=str(int(pred)), model_role=role).inc()
    if proba is not None:
        PREDICTION_PROBABILITY.observe(proba)

    return {
        "gravite_estimee": int(pred),
        "probabilite": proba,
        "model_role": role,
        "model_info": active_info,
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
# Canary status + rollback (champion/challenger governance)
# -----------------------
@app.get("/canary_status")
def canary_status():
    """État courant du canary : modèles chargés et part de trafic configurée."""
    return {
        "canary_traffic_pct": read_canary_pct(),
        "champion": best_model_info,
        "canary": canary_model_info,
        "canary_active": canary_model is not None and read_canary_pct() > 0,
    }


@app.post("/rollback_champion")
def rollback_champion():
    """Rollback : rebascule l'alias 'champion' vers 'previous_champion'.

    L'ancien champion devient le nouveau 'previous_champion' (rollback réversible),
    puis les modèles sont rechargés. Nécessite qu'un 'previous_champion' existe
    (posé automatiquement lors d'une promotion — voir le script d'entraînement).

    Le rollback est **vérifié** : si le modèle ciblé n'est pas réellement servi
    après rechargement (artefact illisible, etc.), les alias sont restaurés et
    l'appel échoue en 500 — jamais de succès silencieux.
    """
    try:
        mlflow.set_tracking_uri("http://mlflow:5000")
        client = MlflowClient()
        try:
            previous = client.get_model_version_by_alias(MODEL_NAME, "previous_champion")
        except Exception:
            raise HTTPException(status_code=409, detail="No 'previous_champion' alias to roll back to.")

        current = None
        try:
            current = client.get_model_version_by_alias(MODEL_NAME, "champion")
        except Exception:
            current = None

        if current is not None and str(current.version) == str(previous.version):
            raise HTTPException(
                status_code=409, detail="previous_champion == champion; nothing to roll back."
            )

        client.set_registered_model_alias(MODEL_NAME, "champion", previous.version)
        if current is not None:
            client.set_registered_model_alias(MODEL_NAME, "previous_champion", current.version)

        _load_best_model_internal()

        # Vérification : le modèle réellement servi doit être la version ciblée.
        # Sinon le chargement a basculé sur un repli (fallback) et le rollback
        # n'a PAS pris effet -> on restaure l'état initial et on échoue.
        served = best_model_info or {}
        if served.get("source") != "registry:champion" or str(served.get("version")) != str(previous.version):
            if current is not None:
                client.set_registered_model_alias(MODEL_NAME, "champion", current.version)
                client.set_registered_model_alias(MODEL_NAME, "previous_champion", previous.version)
                _load_best_model_internal()
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Rollback to v{previous.version} failed: model not servable "
                    f"(serving source='{served.get('source')}', version={served.get('version')}). "
                    "Aliases restored."
                ),
            )

        return {
            "message": "↩️ Rolled back champion.",
            "new_champion_version": previous.version,
            "demoted_version": current.version if current is not None else None,
            "best_model_info": best_model_info,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e}")


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
