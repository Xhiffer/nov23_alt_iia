"""DAG de monitoring ML : calcule un rapport de drift quotidien via l'API backend."""
from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from datetime import datetime

BASE_CONN_ID = "backend_sql"  # Must exist in Airflow Connections

with DAG(
    dag_id="ml_monitoring_drift",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["monitoring", "drift", "ml"],
) as dag:

    drift_report = SimpleHttpOperator(
        task_id="compute_drift_report",
        http_conn_id=BASE_CONN_ID,
        endpoint="/monitoring/drift-report/",
        method="POST",
        log_response=True,  # Le résumé de drift apparaît dans les logs de la tâche
    )
