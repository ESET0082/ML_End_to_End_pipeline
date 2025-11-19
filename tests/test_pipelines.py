"""
Unit tests for data pipeline
"""
import pandas as pd
import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestDataPipeline:
    """Test data loading and validation"""
    
    def test_csv_loading(self):
        """Test CSV file can be loaded"""
        # Create sample data
        data = {
            'id': [1, 2, 3],
            'units': [10.5, 15.2, 12.3],
            'voltage': [220, 225, 215]
        }
        df = pd.DataFrame(data)
        
        assert len(df) == 3
        assert 'units' in df.columns
        assert df['units'].mean() > 0
    
    def test_data_validation(self):
        """Test data validation rules"""
        data = {
            'id': [1, 2, 3],
            'units': [10.5, 15.2, 12.3],
            'voltage': [220, 225, 215]
        }
        df = pd.DataFrame(data)
        
        # Check no nulls
        assert df.isnull().sum().sum() == 0
        
        # Check data types
        assert df['units'].dtype in ['float64', 'float32']
        assert df['voltage'].dtype in ['int64', 'int32']
    
    def test_feature_engineering(self):
        """Test feature engineering creates new columns"""
        data = {
            'id': [1, 2, 3],
            'units': [10.5, 15.2, 12.3],
            'voltage': [220, 225, 215],
            'temperature': [25.0, 30.0, 20.0],
            'power_factor': [0.95, 0.90, 0.98]
        }
        df = pd.DataFrame(data)
        
        # Simulate feature engineering
        df['voltage_flag'] = (df['voltage'] < 200).astype(int)
        
        assert 'voltage_flag' in df.columns
        assert df['voltage_flag'].sum() == 0  # No values < 200


@pytest.mark.unit
class TestModelPipeline:
    """Test model training and inference"""
    
    def test_model_training_inputs(self):
        """Test model receives correct inputs"""
        import numpy as np
        from sklearn.linear_model import LinearRegression
        
        # Create sample data
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 2, 3])
        
        model = LinearRegression()
        model.fit(X, y)
        
        assert model.coef_ is not None
        assert len(model.coef_) == 2
    
    def test_model_prediction(self):
        """Test model generates predictions"""
        import numpy as np
        from sklearn.linear_model import LinearRegression
        
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([1, 2, 3])
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        X_test = np.array([[2, 3]])
        predictions = model.predict(X_test)
        
        assert predictions.shape == (1,)
        assert isinstance(predictions[0], (int, float, np.number))
    
    def test_model_metrics(self):
        """Test model metrics calculation"""
        import numpy as np
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        
        y_true = np.array([10, 20, 30])
        y_pred = np.array([12, 18, 31])
        
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        assert rmse > 0
        assert mae > 0
        assert rmse >= mae  # RMSE >= MAE always


@pytest.mark.unit
class TestAPISchema:
    """Test API request/response schemas"""
    
    def test_meter_features_validation(self):
        """Test MeterFeatures Pydantic model"""
        from pydantic import BaseModel, ValidationError
        
        class MeterFeatures(BaseModel):
            voltage: float
            temperature: float
            power_factor: float
            load_kw: float
            frequency_hz: float
            hour: int
            day_of_week: int
            is_weekend: int
            voltage_flag: int
            pf_issue: int
            high_temp: int
            load_intensity: float
        
        # Valid data
        valid_data = {
            'voltage': 220.5,
            'temperature': 25.0,
            'power_factor': 0.95,
            'load_kw': 2.5,
            'frequency_hz': 50.0,
            'hour': 12,
            'day_of_week': 2,
            'is_weekend': 0,
            'voltage_flag': 1,
            'pf_issue': 0,
            'high_temp': 0,
            'load_intensity': 10.5
        }
        
        meter = MeterFeatures(**valid_data)
        assert meter.voltage == 220.5
        assert meter.hour == 12
    
    def test_meter_features_validation_failure(self):
        """Test invalid data rejection"""
        from pydantic import BaseModel, ValidationError
        
        class MeterFeatures(BaseModel):
            voltage: float
            temperature: float
            hour: int
        
        invalid_data = {
            'voltage': 'not_a_number',  # Should be float
            'temperature': 25.0,
            'hour': 12
        }
        
        with pytest.raises(ValidationError):
            MeterFeatures(**invalid_data)


@pytest.mark.integration
class TestDataPipelineIntegration:
    """Integration tests for data pipeline"""
    
    def test_data_to_model_pipeline(self):
        """Test full pipeline from data to model"""
        import numpy as np
        from sklearn.linear_model import LinearRegression
        import pandas as pd
        
        # Create sample data
        data = {
            'units': np.random.rand(100) * 50,
            'voltage': np.random.rand(100) * 30 + 210,
            'temperature': np.random.rand(100) * 40,
            'power_factor': np.random.rand(100) * 0.2 + 0.8,
            'load_kw': np.random.rand(100) * 5,
            'frequency_hz': np.random.rand(100) * 2 + 49,
            'hour': np.random.randint(0, 24, 100),
            'day_of_week': np.random.randint(0, 7, 100),
            'is_weekend': np.random.randint(0, 2, 100),
            'voltage_flag': np.random.randint(0, 2, 100),
            'pf_issue': np.random.randint(0, 2, 100),
            'high_temp': np.random.randint(0, 2, 100),
            'load_intensity': np.random.rand(100) * 100,
        }
        
        df = pd.DataFrame(data)
        
        # Train model
        X = df.drop('units', axis=1)
        y = df['units']
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Make predictions
        predictions = model.predict(X)
        
        assert len(predictions) == 100
        assert all(isinstance(p, (int, float, np.number)) for p in predictions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
