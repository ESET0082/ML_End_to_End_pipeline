# src/data/ingestion.py

import os
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

# Base directory for CSV inside container
BASE_DATA_DIR = "/opt/airflow/data"   # Adjust ONLY if your docker-compose uses a different mount


def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "postgres"),
        port=os.getenv("PG_PORT", "5432"),
        dbname=os.getenv("PG_DB", "airflow"),
        user=os.getenv("PG_USER", "airflow"),
        password=os.getenv("PG_PASSWORD", "airflow"),
    )


def resolve_csv_path(relative_path: str) -> str:
    """
    Ensures paths work inside Linux-based Airflow Docker.
    Converts: data/raw/file.csv → /opt/airflow/data/raw/file.csv
    """
    return os.path.join(BASE_DATA_DIR, *relative_path.split("/"))


def check_csv_file_exists(csv_relative_path: str):
    """
    Ensures the CSV exists inside container and is readable.
    Expects a relative path like: 'raw/meter_for_regression.csv'
    """
    csv_path = resolve_csv_path(csv_relative_path)

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found inside container: {csv_path}")

    # Test-read first few rows
    pd.read_csv(csv_path, nrows=5)
    logger.info(f"✅ CSV exists and readable: {csv_path}")

    return csv_path


def run_basic_quality_checks_dag():
    """
    Ensures meter tables exist and contain data.
    """
    tables_to_check = ["meter_data_raw"]
    conn = get_pg_connection()

    try:
        with conn.cursor() as cur:
            for table_name in tables_to_check:
                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cur.fetchone()[0]

                if count == 0:
                    raise ValueError(f"❌ Data quality check failed: {table_name} is empty.")
                else:
                    logger.info(f"✅ Table {table_name} contains {count} rows.")

    finally:
        conn.close()


def run_meter_feature_engineering_dag():
    """
    Wrapper for feature engineering pipeline.
    Checks meter_data_raw table and confirms data quality.
    """
    try:
        # Verify meter_data_raw table exists and has data
        run_basic_quality_checks_dag()
        logger.info("✅ Meter data quality checks passed. Ready for training.")
    except Exception as e:
        logger.error(f"❌ Quality check failed: {e}")
        raise


def load_csv_to_raw_table(csv_relative_path: str, table_name: str):
    """
    Loads a CSV into a Postgres RAW table.
    Schema is created automatically.
    Expects relative path like: 'raw/meter_data.csv'
    """

    csv_path = resolve_csv_path(csv_relative_path)

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"{csv_path} is empty!")

    # Convert numeric columns safely
    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        df[col] = df[col].apply(lambda x: int(x) if pd.notnull(x) else None)

    rows = [tuple(row) for row in df.to_numpy()]
    cols = list(df.columns)

    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join([f"{col} TEXT" for col in cols])}
        );
    """

    insert_query = f"""
        INSERT INTO {table_name} ({', '.join(cols)})
        VALUES %s
    """

    conn = get_pg_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(create_table_query)
                execute_values(cur, insert_query, rows)

        logger.info(f"📥 Loaded {len(rows)} rows into {table_name}.")

    finally:
        conn.close()
