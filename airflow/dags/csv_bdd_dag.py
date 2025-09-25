from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from datetime import datetime

BASE_CONN_ID = "backend_sql"  # Must exist in Airflow Connections

with DAG(
    dag_id="import_csv_to_sql",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["backend_sql", "csv-import"],
) as dag:

    caracts = SimpleHttpOperator(
        task_id="import_caracts",
        http_conn_id=BASE_CONN_ID,
        endpoint="/caracts/csv-to-sql/",
        method="POST",
        log_response=True,  # Logs backend response in task logs
    )

    lieux = SimpleHttpOperator(
        task_id="import_lieux",
        http_conn_id=BASE_CONN_ID,
        endpoint="/lieux/csv-to-sql/",
        method="POST",
        log_response=True,
    )

    usagers = SimpleHttpOperator(
        task_id="import_usagers",
        http_conn_id=BASE_CONN_ID,
        endpoint="/usagers/csv-to-sql/",
        method="POST",
        log_response=True,
    )

    vehicules = SimpleHttpOperator(
        task_id="import_vehicules",
        http_conn_id=BASE_CONN_ID,
        endpoint="/vehicules/csv-to-sql/",
        method="POST",
        log_response=True,
    )
    ai_training_data = SimpleHttpOperator(
        task_id="import_ai_training_data",
        http_conn_id=BASE_CONN_ID,
        endpoint="/ai-training-data/csv-to-sql/",
        method="POST",
        log_response=True,
    )

    caracts >> lieux >> usagers >> vehicules >> ai_training_data
