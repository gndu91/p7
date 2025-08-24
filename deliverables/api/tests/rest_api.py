from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur l'API de Scoring de Crédit !"}

def test_predict_valid_input():
    # Données valides basées sur l'exemple dans le modèle Pydantic
    valid_data = {
        "AMT_INCOME_TOTAL": 202500.0,
        "AMT_CREDIT": 406597.5,
        "AMT_ANNUITY": 24700.5,
        "DAYS_BIRTH": -9461,
        "DAYS_EMPLOYED": -637,
        "EXT_SOURCE_2": 0.262949,
        "EXT_SOURCE_3": 0.139376,
    }
    response = client.post("/predict", json=valid_data)
    assert response.status_code == 200
    json_response = response.json()
    assert "probabilite_defaut" in json_response
    assert "decision" in json_response
    assert 0 <= json_response["probabilite_defaut"] <= 1

def test_predict_invalid_input():
    # Données invalides (champ manquant)
    invalid_data = {
        "AMT_INCOME_TOTAL": 202500.0,
        # AMT_CREDIT est manquant
        "AMT_ANNUITY": 24700.5,
        "DAYS_BIRTH": -9461,
        "DAYS_EMPLOYED": -637,
        "EXT_SOURCE_2": 0.262949,
        "EXT_SOURCE_3": 0.139376,
    }
    response = client.post("/predict", json=invalid_data)
    # FastAPI retourne un 422 pour les erreurs de validation Pydantic
    assert response.status_code == 422
