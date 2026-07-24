"""Routes de monitoring ML (drift)."""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/monitoring/drift-report/")
def drift_report(reference_frac: float = 0.7, current_window: int | None = None):
    """
    Calcule un rapport de drift (Evidently) entre les données de référence et une
    fenêtre courante. Retourne un résumé (dataset_drift, drift_share, alert...) et
    sauvegarde le rapport HTML. Déclenchable manuellement ou par le DAG Airflow
    `ml_monitoring_drift`.
    """
    try:
        # Import paresseux : Evidently est lourd, on ne le charge qu'à l'appel.
        from scripts.monitoring.drift import run_drift_report

        return run_drift_report(reference_frac=reference_frac, current_window=current_window)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drift report failed: {e}")
