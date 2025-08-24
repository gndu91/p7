import json

import yaml
import joblib
from pydantic import BaseModel, create_model
from typing import Dict, Any

from pathlib import Path

# Pour rendre l'api robuste contre d'éventuels changements, les artifacts seront utilisés quand nécessaire

# Chemin de base du dossier de l'API.
# Path(__file__) -> /api/model.py
# .parent -> /api
BASE_DIR = Path(__file__).parent

# Chemin vers le dossier contenant les artefacts du modèle
ARTIFACTS_DIR = BASE_DIR / "artifacts"

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
