# deliverables/api/tests/test_api.py

import pytest
from fastapi.testclient import TestClient
import json
from pathlib import Path
import sys

api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from app import app

# Créer un client de test pour l'API
client = TestClient(app)


@pytest.fixture(scope="module")
def valid_client_data():
    """
    Fixture Pytest qui charge les données de test depuis le fichier JSON.
    'scope="module"' signifie que le fichier n'est lu qu'une seule fois pour tous les tests.
    """
    json_path = Path(__file__).parent / "test_api.json"
    if not json_path.exists():
        pytest.fail(f"Le fichier de données de test n'a pas été trouvé : {json_path}. "
                    "Veuillez l'exécuter depuis le notebook de modélisation.")
    with open(json_path, 'r') as f:
        return json.load(f)


def test_health_check():
    """Teste le endpoint de statut '/'."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert response.json() == {"status": "up"}, "Le statut de l'API devrait être 'up'"


def test_predict_success(valid_client_data):
    """Teste une prédiction réussie avec des données valides chargées depuis le JSON."""
    response = client.post("/predict", json=valid_client_data)

    assert response.status_code == 200, f"La prédiction a échoué: {response.text}"

    data = response.json()
    assert "client_id" in data
    assert "probability_default" in data
    assert "decision" in data
    assert "threshold" in data
    assert data["decision"] in ["yes", "no"]
    assert isinstance(data["probability_default"], float)
    assert 0 <= data["probability_default"] <= 1


def test_predict_missing_feature(valid_client_data):
    """Teste le comportement de l'API avec une feature manquante."""
    invalid_data = valid_client_data.copy()
    # On retire une feature clé pour le test
    del invalid_data["AMT_CREDIT"]

    response = client.post("/predict", json=invalid_data)

    # FastAPI gère la validation Pydantic et doit retourner une erreur 422
    assert response.status_code == 422, "Une feature manquante devrait déclencher une erreur 422"


def test_predict_incorrect_type(valid_client_data):
    """Teste le comportement de l'API avec un type de donnée incorrect."""
    invalid_data = valid_client_data.copy()
    # On met une chaîne de caractères là où un nombre est attendu
    invalid_data["AMT_INCOME_TOTAL"] = "beaucoup d'argent"

    response = client.post("/predict", json=invalid_data)

    assert response.status_code == 422, "Un type incorrect devrait déclencher une erreur 422"