import pytest
from flask import Flask
from api.v1.endpoints import api_bp
from core.defaults import SCENARIOS

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    with app.test_client() as client:
        yield client

def test_get_district_8_data(client):
    rv = client.get("/api/v1/market-data/district-8")
    assert rv.status_code == 200
    assert "historical_metrics" in rv.json["data"]

def test_simulate_missing_payload(client):
    rv = client.post("/api/v1/simulate")
    assert rv.status_code == 400

def test_simulate_validation_error(client):
    rv = client.post("/api/v1/simulate", json={"loan_term_years": "nem_szam"})
    assert rv.status_code == 422

def test_simulate_success(client):
    rv = client.post("/api/v1/simulate", json=SCENARIOS["base"]["params"])
    assert rv.status_code == 200
    assert "data" in rv.json

def test_sensitivity_missing_payload(client):
    rv = client.post("/api/v1/sensitivity")
    assert rv.status_code == 400

def test_sensitivity_validation_error(client):
    rv = client.post("/api/v1/sensitivity", json={"base_params": {"loan_term_years": "nem_szam"}})
    assert rv.status_code == 422

def test_sensitivity_success(client):
    rv = client.post("/api/v1/sensitivity", json={"base_params": SCENARIOS["base"]["params"]})
    assert rv.status_code == 200
    assert "data" in rv.json
