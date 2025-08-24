import pandas as pd
from fastapi import FastAPI, HTTPException

import json

import yaml
import joblib
from pydantic import BaseModel, create_model
from typing import Dict, Any

from pathlib import Path

# Pour rendre l'api robuste contre d'éventuels changements, les artifacts seront utilisés quand nécessaire

# Chemin vers le dossier contenant les artefacts du modèle
ARTIFACTS_DIR = Path(__file__).parent

# TODO: Store this as an artifact
BUSINESS_THRESHOLD = 0.52

# Chargement de la signature des inputs
inputs_schema = json.loads(yaml.safe_load((ARTIFACTS_DIR / "MLmodel").open('r'))["signature"]["inputs"])

get_type = lambda mlflow_type: {
    "long": int,
    "string": str,
    "double": float,
}[mlflow_type]

def create_dynamic_pydantic_model(model_name: str = "ClientData") -> type[BaseModel]:
    fields: Dict[str, Any] = {}
    for col in inputs_schema:
        python_type = get_type(col["type"])
        fields[col["name"]] = (python_type, ...) if col["required"] else (python_type | None, None)
    print(f"Modèle Pydantic '{model_name}' créé dynamiquement avec {len(fields)} champs.")
    return create_model(model_name, **fields)


try:
    model_pipeline = joblib.load(ARTIFACTS_DIR / "model.pkl")
except ModuleNotFoundError:
    # TODO: Separation of the two environments
    raise ModuleNotFoundError("Please install the requirements defined in artifacts/requirements.txt")
ClientDataModel: type[BaseModel] = create_dynamic_pydantic_model()

app = FastAPI(
    title="Credit Scoring API",
    description="Accept or decline a credit based on probabilities of non payment.",
    version="1.1.0"
)

@app.get("/status", tags=["Health Check"])
@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "up" if model_pipeline else "down"}

@app.post("/predict", tags=["Prediction"])
async def predict(client_data: ClientDataModel):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Unavailable model")
    client_df = pd.DataFrame([client_data.model_dump()])
    try:
        probability = model_pipeline.predict_proba(client_df)[0][1]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error occured during prediction : {e}")
    return {
        "client_id": client_data.SK_ID_CURR,
        "probability_default": round(float(probability), 4),
        "decision": "yes" if probability < BUSINESS_THRESHOLD else "no",
        "threshold": BUSINESS_THRESHOLD
    }
