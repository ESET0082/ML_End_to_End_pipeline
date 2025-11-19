# Advanced ML Project - Meter Units Consumption Prediction

## 📋 Project Overview
This is a complete ML pipeline for predicting electricity meter consumption (units) based on electrical parameters and temporal features using:
- **Data Pipeline**: ETL with feature engineering
- **Training Pipeline**: Linear Regression model training
- **Inference Pipeline**: Real-time predictions
- **MLflow**: Experiment tracking and model management
- **Airflow**: Workflow orchestration
- **FastAPI**: REST API for predictions
- **PostgreSQL**: Data storage
- **Superset**: Data visualization

---

## 🚀 Quick Start Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- PostgreSQL 15

### Step-1: Start PostgreSQL
```bash
cd infrastructure
docker-compose up -d postgres
docker ps  # Verify postgres is running
```

### Step-2: Initialize Airflow Database
```bash
docker-compose run --rm airflow_webserver airflow db init
```

### Step-3: Create Airflow Admin User
```bash
docker-compose run --rm airflow_webserver airflow users create \
  --username admin \
  --firstname Gopal \
  --lastname Bhammar \
  --role Admin \
  --email admin@example.com \
  --password admin
```

### Step-4: Start All Services
```bash
docker compose up --build -d

docker-compose up -d

docker ps  # Verify all services are running
```

---

## 🔗 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow UI** | http://localhost:38081 | admin / admin |
| **MLflow UI** | http://localhost:5500 | - |
| **Superset** | http://localhost:8088 | admin / admin |
| **Model API** | http://localhost:5501 | - |
| **PostgreSQL** | localhost:55432 | airflow / airflow |

---

## 📊 Pipeline Workflows

### 1. Data Ingestion DAG: `meter_data_ingestion_dag`
**Purpose**: Load meter data with engineered features into PostgreSQL

**Tasks**:
1. `check_meter_csv_exists` - Verify CSV is available
2. `load_meter_data_to_postgres` - Insert into `meter_data_raw` table
3. `run_meter_quality_checks` - Validate data quality

**Data Source**: `data/raw/final_meter_features.csv`

### 2. Training DAG: `meter_training_pipeline_dag`
**Purpose**: Train Linear Regression model to predict meter units

**Tasks**:
1. `train_logistic_regression_model` - Trains model, saves to `src/models/artifacts/models/linear_regression_model.pkl`
2. `log_model_to_mlflow` - Logs metrics (RMSE, MAE, R²) to MLflow

**Features** (12 input features):
- voltage, temperature, power_factor, load_kw, frequency_hz
- hour, day_of_week, is_weekend, voltage_flag, pf_issue, high_temp, load_intensity

**Target**: units (meter consumption in kWh)

### 3. Inference DAG: `meter_inference_pipeline_dag`
**Purpose**: Generate predictions on new meter data

**Tasks**:
1. `load_latest_model` - Load trained model with NumPy compatibility handling
2. `prepare_features_for_inference` - Prepare input features
3. `make_predictions` - Generate predictions, save to `data/raw/meter_units_predictions.csv`

---

## 🎯 MLflow Setup & Troubleshooting

### MLflow Architecture
```
┌─────────────────────┐
│   Airflow Tasks     │
│ (train_pipeline)    │
└──────────┬──────────┘
           │ HTTP requests
           ▼
┌─────────────────────┐
│  MLflow Server      │
│  (localhost:5000)   │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
PostgreSQL    Artifacts
(metadata)    (/mlflow_artifacts)
```

### Common MLflow Issues & Solutions

#### ❌ Issue: "Connection refused" to MLflow
**Symptoms**: `ConnectionError: Failed to establish a new connection to http://mlflow_server:5000`

**Causes & Solutions**:

1. **MLflow container not running**
   ```bash
   docker ps | grep mlflow  # Check if running
   docker logs mlflow_server  # View logs
   ```

2. **Wait for MLflow to initialize**
   - MLflow may need 10-15 seconds to start after postgres
   - Solution: Automatic retry in `train.py` with 5 attempts (5 second intervals)

3. **PostgreSQL not ready**
   ```bash
   docker logs postgres_db  # Check postgres health
   ```

**Fix**:
```bash
# Restart MLflow with postgres dependency
docker-compose down mlflow
docker-compose up -d mlflow
```

#### ❌ Issue: "Network host 'mlflow_server' not found"
**Symptoms**: `No address associated with hostname`

**Cause**: Docker network issue

**Fix**:
```bash
# Ensure containers are on same network
docker network ls
docker network inspect infrastructure_default
docker-compose down
docker-compose up -d
```

#### ❌ Issue: "Artifact storage not writable"
**Symptoms**: `PermissionError: [Errno 13] Permission denied: '/mlflow_artifacts'`

**Fix**:
```bash
# Fix volume permissions
cd infrastructure
mkdir -p ../mlflow_artifacts
chmod 777 ../mlflow_artifacts
docker-compose restart mlflow
```

#### ❌ Issue: "mlflow_db database does not exist"
**Symptoms**: `psycopg2.OperationalError: FATAL: database "mlflow_db" does not exist`

**Fix**:
```bash
# Create mlflow database in postgres
docker exec postgres_db psql -U airflow -c "CREATE DATABASE mlflow_db;"
docker-compose restart mlflow
```

---

## 🧪 Testing & Verification

### Test Data Pipeline
```bash
# Generate meter data with engineered features
cd src/data
python create_datasets.py
# Outputs: data/raw/final_meter_features.csv
```

### Test Training Pipeline
```bash
# Train model locally (without Airflow)
cd src/models
python -c "
from train import train_logistic_regression
class MockTI:
    def xcom_push(self, key, value):
        print(f'[XCom] {key} = {value}')
train_logistic_regression(ti=MockTI())
"
# Model saved to: src/models/artifacts/models/linear_regression_model.pkl
```

### Test Inference Pipeline
```bash
# Generate predictions locally
cd src/models
python -c "from inference import make_predictions; make_predictions()"
# Outputs: data/raw/meter_units_predictions.csv
```

### Test API Server
```bash
# Locally
cd src/api
uvicorn server:app --reload --port 8000

# Via Docker
curl -X GET http://localhost:5501/
curl -X POST http://localhost:5501/predict \
  -H "Content-Type: application/json" \
  -d '{
    "voltage": 220.5,
    "temperature": 25.0,
    "power_factor": 0.95,
    "load_kw": 2.5,
    "frequency_hz": 50.0,
    "hour": 12,
    "day_of_week": 2,
    "is_weekend": 0,
    "voltage_flag": 1,
    "pf_issue": 0,
    "high_temp": 0,
    "load_intensity": 10.5
  }'
```

---

## 📁 Project Structure

```
├── airflow_dags/                    # Airflow DAG definitions
│   ├── data_pipeline_dag.py         # Data ingestion workflow
│   ├── training_pipeline_dag.py     # Model training workflow
│   └── inference_pipeline_dag.py    # Prediction workflow
├── src/
│   ├── data/
│   │   ├── create_datasets.py       # Feature engineering
│   │   ├── features.py              # Feature definitions
│   │   ├── ingestion.py             # Data loading functions
│   │   └── __init__.py
│   ├── models/
│   │   ├── train.py                 # Training script (with MLflow logging)
│   │   ├── inference.py             # Inference script (with NumPy fix)
│   │   └── artifacts/               # Saved models
│   ├── api/
│   │   ├── server.py                # FastAPI application
│   │   └── templates/index.html     # Web UI
│   └── monitoring/
│       └── drift_detector.py        # Data drift detection
├── docker/
│   ├── airflow/Dockerfile           # Airflow image (with NumPy 1.24.0+)
│   ├── mlflow/Dockerfile            # MLflow image
│   └── model_api/Dockerfile         # FastAPI image
├── infrastructure/
│   ├── docker-compose.yml           # Service orchestration
│   ├── postgres/init.sql            # Database initialization
│   └── superset/config.py           # Superset configuration
├── data/
│   └── raw/
│       ├── final_meter_features.csv # Generated features
│       └── meter_units_predictions.csv # Predictions
└── mlflow_artifacts/                # MLflow experiment tracking
```

---

## 🛠️ Troubleshooting Commands

```bash
# View logs
docker logs airflow_webserver
docker logs mlflow_server
docker logs postgres_db

# Check service health
docker ps -a
docker stats

# Restart services
docker-compose restart airflow_webserver airflow_scheduler
docker-compose restart mlflow

# Clean up (WARNING: deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache
```

---

## 📈 Model Performance

**Linear Regression on Meter Units**:
- RMSE: 14.20 kWh
- MAE: 12.26 kWh
- R²: -0.0065

*Note: Negative R² indicates the model performs worse than a baseline. Consider feature engineering or different algorithms.*

---

## 🔐 Security Notes

- ⚠️ Default credentials are for development only
- 🔑 Change postgres password in docker-compose.yml
- 🔐 Use environment variables for secrets in production
- 🚨 Enable MLflow authentication in production

---

## 📝 License & Credits

Advanced ML Project - Final Year Project | 2025


