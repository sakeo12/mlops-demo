import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("http://172.16.0.200:5555")

client = MlflowClient()

models = client.search_registered_models()

for model in models:
    print(model.name)
