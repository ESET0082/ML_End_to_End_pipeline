# airflow_dags/data_pipeline_dag.py

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.data.ingestion import (
    check_csv_file_exists,
    load_csv_to_raw_table,
    run_meter_feature_engineering_dag,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}

with DAG(
    dag_id="meter_data_ingestion_dag",
    description=(
        "Pipeline to ingest meter data with engineered features into Postgres raw layer "
        "and prepare final dataset for training."
    ),
    default_args=default_args,
    start_date=datetime(2021, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["meter", "ingestion", "postgres"],
    max_active_runs=1,
) as dag:

    # Paths inside the container
    METER_DATA_CSV_PATH = "/opt/airflow/data/raw/final_meter_features.csv"

    # --------------------
    # Stage 1: Check Meter CSV Exists
    # --------------------
    check_meter_csv_task = PythonOperator(
        task_id="check_meter_csv_exists",
        python_callable=check_csv_file_exists,
        op_kwargs={"csv_relative_path": "raw/final_meter_features.csv"},
    )

    # --------------------
    # Stage 2: Load Meter CSV into Postgres
    # --------------------
    load_meter_csv_task = PythonOperator(
        task_id="load_meter_data_to_postgres",
        python_callable=load_csv_to_raw_table,
        op_kwargs={
            "csv_relative_path": "raw/final_meter_features.csv",
            "table_name": "meter_data_raw",
        },
    )

    # --------------------
    # Stage 3: Run Data Quality Checks
    # --------------------
    quality_check_task = PythonOperator(
        task_id="run_meter_quality_checks",
        python_callable=run_meter_feature_engineering_dag,
    )

    # Define pipeline
    check_meter_csv_task >> load_meter_csv_task >> quality_check_task