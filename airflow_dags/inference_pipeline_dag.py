# airflow_dags/inference_pipeline_dag.py

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import mlflow

from src.models.inference import (
    load_latest_model,
    prepare_features_for_inference,
    make_predictions,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}

with DAG(
    dag_id="meter_inference_pipeline_dag",
    description="Inference pipeline for meter units consumption prediction",
    default_args=default_args,
    start_date=datetime(2021, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["meter", "inference", "mlflow"],
    max_active_runs=1,
) as dag:

    # Stage 1: Load latest trained model from MLflow
    load_model_task = PythonOperator(
        task_id="load_latest_model",
        python_callable=load_latest_model,
    )

    # Stage 2: Prepare features for inference
    prepare_features_task = PythonOperator(
        task_id="prepare_features_for_inference",
        python_callable=prepare_features_for_inference,
    )

    # Stage 3: Make predictions
    prediction_task = PythonOperator(
        task_id="make_predictions",
        python_callable=make_predictions,
    )

    # Define pipeline order
    load_model_task >> prepare_features_task >> prediction_task
