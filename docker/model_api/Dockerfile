FROM python:3.10-slim

# Install dependencies from requirements.txt
COPY docker/model_api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY src/ /app/src

# Point to Linear Regression model
ENV MODEL_PATH=/app/src/models/artifacts/models/linear_regression_model.pkl

# Run FastAPI server on port 8000
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
