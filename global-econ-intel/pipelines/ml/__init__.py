"""
ML pipelines (Day 2, Steps 3-4).

- `mlflow_utils`  : thin MLflow tracking/registry wrapper
- `features`      : pulls training features from the warehouse repository layer
- `models/`       : one trainer per forecast domain (gdp, inflation,
                    exchange_rate, crypto), each producing a `TrainingResult`
"""
