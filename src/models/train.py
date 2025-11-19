# src/models/train.py

import os
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import mlflow


# -------------------------------
# Paths
# -------------------------------

# Data directory (shared with Airflow)
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw")

# Artifacts directory INSIDE src/models (and mounted into containers)
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_DIR = os.path.join(ARTIFACTS_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

METER_DATA_CSV = os.path.join(RAW_DATA_DIR, "final_meter_features.csv")

print("🔧 [MODULE LOAD] train.py loaded")
print(f"🔧 [MODULE LOAD] RAW_DATA_DIR   = {RAW_DATA_DIR}")
print(f"🔧 [MODULE LOAD] ARTIFACTS_DIR  = {ARTIFACTS_DIR}")
print(f"🔧 [MODULE LOAD] MODEL_DIR      = {MODEL_DIR}")
print(f"🔧 [MODULE LOAD] METER_DATA_CSV = {METER_DATA_CSV}")


def train_logistic_regression(**kwargs):
    """
    Train Linear Regression model to predict meter units consumption
    """
    print("\n==================== TRAIN LINEAR REGRESSION ====================")
    print(f"📂 [TRAIN] CWD inside task: {os.getcwd()}")
    print(f"📂 [TRAIN] RAW_DATA_DIR: {RAW_DATA_DIR}")
    print(f"📂 [TRAIN] MODEL_DIR: {MODEL_DIR}")
    print(f"📄 [TRAIN] METER_DATA_CSV: {METER_DATA_CSV} (exists={os.path.exists(METER_DATA_CSV)})")

    # Load meter data
    df = pd.read_csv(METER_DATA_CSV)
    print(f"🧮 [TRAIN] Loaded data shape: {df.shape}")
    print(f"🧮 [TRAIN] Columns: {df.columns.tolist()}")

    # Select features and target
    # Features: numeric and engineered features (exclude id, meter_id, units, date, voltage_status)
    feature_cols = ['voltage', 'temperature', 'power_factor', 'load_kw', 'frequency_hz', 
                    'hour', 'day_of_week', 'is_weekend', 'voltage_flag', 'pf_issue', 
                    'high_temp', 'load_intensity']
    
    X = df[feature_cols].copy()
    y = df['units'].copy()
    
    print(f"🧮 [TRAIN] Feature matrix shape: {X.shape}, target shape: {y.shape}")
    print(f"🧮 [TRAIN] Features: {feature_cols}")

    # Fill any missing values
    X = X.fillna(X.mean())
    y = y.fillna(y.mean())
    print(f"🧮 [TRAIN] Handled missing values")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"🧪 [TRAIN] Train shapes: {X_train.shape}, {y_train.shape}")
    print(f"🧪 [TRAIN] Test shapes: {X_test.shape}, {y_test.shape}")

    # Train model
    print("🤖 [TRAIN] Training LinearRegression...")
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"✅ [TRAIN] Model trained.")
    print(f"✅ [TRAIN] MSE: {mse:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")

    # Save model to local artifacts dir
    model_path = os.path.join(MODEL_DIR, "linear_regression_model.pkl")

    print(f"💾 [TRAIN] Saving model to:   {model_path}")
    joblib.dump(model, model_path)

    print(f"📁 [TRAIN] MODEL_DIR listing: {os.listdir(MODEL_DIR)}")

    # Push metrics to XCom for MLflow logging
    print("📤 [TRAIN] Pushing metrics to XCom")
    kwargs["ti"].xcom_push(key="rmse", value=float(rmse))
    kwargs["ti"].xcom_push(key="mae", value=float(mae))
    kwargs["ti"].xcom_push(key="r2", value=float(r2))
    print("==================== END TRAIN LINEAR REGRESSION ====================\n")


def log_model_to_mlflow(**kwargs):
    """
    Pulls metrics from XCom and logs model + metrics to MLflow.
    Handles network timeouts and connection issues gracefully.
    """
    from mlflow.tracking import MlflowClient
    import time

    print("\n==================== LOG MODEL TO MLFLOW ====================")
    print(f"📂 [LOG] CWD inside task: {os.getcwd()}")
    print(f"📂 [LOG] MODEL_DIR: {MODEL_DIR}")

    ti = kwargs["ti"]
    rmse = ti.xcom_pull(task_ids="train_logistic_regression_model", key="rmse")
    mae = ti.xcom_pull(task_ids="train_logistic_regression_model", key="mae")
    r2 = ti.xcom_pull(task_ids="train_logistic_regression_model", key="r2")
    
    print(f"📥 [LOG] Pulled metrics from XCom: RMSE={rmse}, MAE={mae}, R²={r2}")

    if rmse is None or mae is None or r2 is None:
        raise ValueError("❌ Metrics not found in XCom. Did the training task succeed?")

    tracking_uri = "http://mlflow_server:5000"
    print(f"🔗 [LOG] Setting MLflow tracking URI to: {tracking_uri}")
    
    # Wait for MLflow to be ready
    max_retries = 5
    for attempt in range(max_retries):
        try:
            mlflow.set_tracking_uri(tracking_uri)
            print(f"✅ [LOG] Connected to MLflow at attempt {attempt + 1}/{max_retries}")
            break
        except Exception as e:
            print(f"⚠️ [LOG] Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise

    experiment_name = "meter_units_regression"
    print(f"🧪 [LOG] Setting MLflow experiment: {experiment_name}")
    
    try:
        mlflow.set_experiment(experiment_name)
    except Exception as e:
        print(f"⚠️ [LOG] Warning setting experiment: {e}")

    # Confirm what tracking URI MLflow sees
    effective_uri = mlflow.get_tracking_uri()
    print(f"🔍 [LOG] Effective MLflow tracking URI: {effective_uri}")

    model_path = os.path.join(MODEL_DIR, "linear_regression_model.pkl")

    print(f"📄 [LOG] Expecting model at: {model_path} (exists={os.path.exists(model_path)})")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"❌ Model file not found at {model_path}")

    # Use explicit MlflowClient so we know it's bound to HTTP URI
    print("🧑‍💻 [LOG] Creating MlflowClient with tracking URI...")
    try:
        client = MlflowClient(tracking_uri=tracking_uri)

        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            print("🧪 [LOG] Experiment does not exist yet. Creating...")
            exp_id = client.create_experiment(experiment_name)
        else:
            exp_id = experiment.experiment_id
            print(f"🧪 [LOG] Found existing experiment id: {exp_id}")

        print("🏃 [LOG] Creating new MLflow run...")
        run = client.create_run(experiment_id=exp_id)
        run_id = run.info.run_id
        print(f"🏃 [LOG] Run created with run_id: {run_id}")

        # Log params and metrics
        print("📊 [LOG] Logging params and metrics...")
        client.log_param(run_id, "model_type", "LinearRegression")
        client.log_param(run_id, "target", "units")
        client.log_metric(run_id, "rmse", float(rmse))
        client.log_metric(run_id, "mae", float(mae))
        client.log_metric(run_id, "r2", float(r2))

        # Log artifacts
        print("📦 [LOG] Logging artifacts (model) to run...")
        client.log_artifact(run_id, model_path, artifact_path="model")

        print(f"✅ [LOG] Model and metrics logged to MLflow at: {tracking_uri}")
        print(f"🔗 [LOG] Run URL: {tracking_uri}/#/experiments/{exp_id}/runs/{run_id}")
        
    except Exception as e:
        print(f"❌ [LOG] Error logging to MLflow: {e}")
        print("⚠️ [LOG] Continuing despite MLflow error - training artifacts were saved locally")

    print("==================== END LOG MODEL TO MLFLOW ====================\n")
