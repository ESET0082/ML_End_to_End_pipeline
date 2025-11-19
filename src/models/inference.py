# src/models/inference.py

import os
import pandas as pd
import joblib
import pickle
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')
MODEL_DIR = os.path.join(ARTIFACTS_DIR, 'models')

METER_DATA_CSV = os.path.join(RAW_DATA_DIR, 'final_meter_features.csv')

def load_latest_model():
    """
    Loads the latest model from artifacts folder with NumPy compatibility fix
    """
    model_path = os.path.join(MODEL_DIR, 'linear_regression_model.pkl')
    
    try:
        # First try standard joblib load
        model = joblib.load(model_path)
        logger.info(f"✅ Model loaded from {model_path}")
        return model
    except ModuleNotFoundError as e:
        # Handle NumPy version compatibility issue
        if 'numpy._core' in str(e):
            logger.warning(f"⚠️ NumPy compatibility issue detected: {e}")
            logger.info("Attempting alternative loading method...")
            
            # Monkey-patch numpy for compatibility
            try:
                import numpy
                if not hasattr(numpy, '_core'):
                    # Redirect numpy._core to numpy.core for older NumPy versions
                    import numpy.core as core
                    sys.modules['numpy._core'] = core
                    logger.info("Applied NumPy._core compatibility patch")
            except Exception as patch_err:
                logger.error(f"Failed to apply patch: {patch_err}")
            
            # Retry loading
            try:
                model = joblib.load(model_path)
                logger.info(f"✅ Model loaded from {model_path} with compatibility patch")
                return model
            except Exception as retry_err:
                logger.error(f"Failed to load model even with patch: {retry_err}")
                raise
        else:
            raise

def prepare_features_for_inference():
    """
    Prepares features from meter data for inference
    """
    logger.info("Preparing features for inference...")
    
    df = pd.read_csv(METER_DATA_CSV)
    logger.info(f"Loaded data with shape: {df.shape}")
    
    # Select the same features used in training
    feature_cols = ['voltage', 'temperature', 'power_factor', 'load_kw', 'frequency_hz', 
                    'hour', 'day_of_week', 'is_weekend', 'voltage_flag', 'pf_issue', 
                    'high_temp', 'load_intensity']
    
    X_prepared = df[feature_cols].copy()
    
    # Fill any missing values with mean
    X_prepared = X_prepared.fillna(X_prepared.mean())

    logger.info(f"✅ Features prepared for inference. Shape: {X_prepared.shape}")
    return X_prepared, df

def make_predictions():
    """
    Loads model, prepares features, and makes predictions
    """
    logger.info("Starting inference pipeline...")
    
    try:
        model = load_latest_model()
        X_prepared, df = prepare_features_for_inference()
        predictions = model.predict(X_prepared)
        logger.info(f"✅ Predictions made. Sample: {predictions[:10]}")

        # Save predictions
        pred_path = os.path.join(RAW_DATA_DIR, 'meter_units_predictions.csv')
        results_df = pd.DataFrame({
            'id': df['id'],
            'meter_id': df['meter_id'],
            'actual_units': df['units'],
            'predicted_units': predictions
        })
        results_df.to_csv(pred_path, index=False)
        logger.info(f"✅ Predictions saved at {pred_path}")
        return results_df
    except Exception as e:
        logger.error(f"❌ Inference pipeline failed: {e}")
        raise
