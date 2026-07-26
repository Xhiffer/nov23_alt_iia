"""
Monitoring ML — détection de drift (data & target) avec Evidently.

Compare un jeu de **référence** (données d'entraînement) à un jeu **courant**
(fenêtre récente) et renvoie un résumé de drift + un rapport HTML.

NOTE : tant qu'un journal des features des prédictions en production n'existe pas,
le jeu « courant » est approximé par les lignes les plus récentes de la table
d'entraînement. Remplacer `_build_feature_frame` / la fenêtre courante par le vrai
log de prédiction dès qu'il est disponible.
"""
import os
import logging
from datetime import datetime

import pandas as pd

from database import SessionLocal
from routers.ai_training_model_data_router import get_all_ai_training_data
from scripts.general_tain_setup import (
    remove_excluded_columns,
    remove_lat_long_columns,
    remove_vma_column,
    remove_an_nais_column,
    delete_hrmn_scaled_column,
    delete_date_column,
    group_grav_values,
)

REPORT_DIR = os.environ.get("DRIFT_REPORT_DIR", "monitoring_reports")
TARGET = "grav"
DRIFT_SHARE_THRESHOLD = float(os.environ.get("DRIFT_SHARE_THRESHOLD", "0.3"))


def _build_feature_frame() -> pd.DataFrame:
    """Reconstruit le DataFrame de features avec le même preprocessing qu'à l'entraînement."""
    db = SessionLocal()
    try:
        data = get_all_ai_training_data(db)
    finally:
        db.close()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame([obj.__dict__ for obj in data])
    df = df.drop(columns=[c for c in ["_sa_instance_state"] if c in df.columns], errors="ignore")

    df = remove_excluded_columns(df)
    df = remove_lat_long_columns(df)
    df = remove_vma_column(df)
    df = remove_an_nais_column(df)
    df = delete_hrmn_scaled_column(df)
    df = delete_date_column(df)
    df = group_grav_values(df)

    for col in ["locp", "is_weekend"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    return df


def run_drift_report(reference_frac: float = 0.7, current_window: int | None = None) -> dict:
    """Calcule le drift et sauvegarde un rapport HTML. Retourne un résumé JSON-sérialisable."""
    # Import Evidently ici (lourd) pour ne pas ralentir le démarrage de l'API.
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
    from evidently import ColumnMapping

    df = _build_feature_frame()
    if df.empty or len(df) < 20:
        raise ValueError("Pas assez de données pour calculer le drift (minimum 20 lignes).")

    n = len(df)
    split = int(n * reference_frac)
    reference = df.iloc[:split]
    current = df.iloc[split:] if current_window is None else df.iloc[-current_window:]

    column_mapping = ColumnMapping()
    metrics = [DataDriftPreset()]
    if TARGET in df.columns:
        column_mapping.target = TARGET
        metrics.append(TargetDriftPreset())

    report = Report(metrics=metrics)
    report.run(reference_data=reference, current_data=current, column_mapping=column_mapping)

    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(REPORT_DIR, f"drift_report_{ts}.html")
    report.save_html(html_path)

    drift = report.as_dict()["metrics"][0]["result"]
    drift_share = float(drift.get("share_of_drifted_columns", 0.0))
    summary = {
        "dataset_drift": bool(drift.get("dataset_drift", False)),
        "n_features": int(drift.get("number_of_columns", 0)),
        "n_drifted_features": int(drift.get("number_of_drifted_columns", 0)),
        "drift_share": drift_share,
        "threshold": DRIFT_SHARE_THRESHOLD,
        "alert": drift_share > DRIFT_SHARE_THRESHOLD,
        "reference_rows": int(len(reference)),
        "current_rows": int(len(current)),
        "report_html": html_path,
        "generated_at": ts,
    }
    logging.info("Drift summary: %s", summary)
    if summary["alert"]:
        logging.warning(
            "⚠️ DRIFT ALERT: %.1f%% des features ont drifté (seuil %.0f%%).",
            drift_share * 100,
            DRIFT_SHARE_THRESHOLD * 100,
        )
        # Alerting effectif : notifie le webhook configuré (no-op si ALERT_WEBHOOK_URL absent).
        from scripts.monitoring.notify import send_drift_alert

        summary["alert_sent"] = send_drift_alert(summary)
    return summary
