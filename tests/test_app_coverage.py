import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_delete_inputs(client):
    response = client.delete('/api/inputs')
    assert response.status_code == 200
    assert response.json["status"] == "success"

def test_historical_endpoint(client):
    payload = {
        "start_year": 2004,
        "city": "Budapest",
        "district": "XI. kerület",
        "current_property_value_huf": 60000000,
        "down_payment_pct": 20.0,
        "loan_interest_pct": 6.5,
        "loan_term_years": 20,
        "current_rent_huf": 200000,
        "current_utilities_huf": 30000,
        "tbsz_enabled": True
    }
    response = client.post('/api/historical_simulation', json=payload)
    assert response.status_code == 200
    assert "data" in response.json
    
    # Missing payload
    response_fail = client.post('/api/historical_simulation')
    assert response_fail.status_code == 400

def test_store_inputs_missing(client):
    response = client.post('/api/inputs')
    assert response.status_code == 400

def test_generate_summary(client, mocker):
    mocker.patch('google.genai.Client')
    payload = {
        "model_results": {"net_wealth_re": 100, "net_wealth_sp500": 120}
    }
    response = client.post('/api/generate_summary', json=payload)
    # the endpoint catches exception and returns dummy data if API fails or is mocked poorly
    assert response.status_code == 200
    
    response_fail = client.post('/api/generate_summary')
    assert response_fail.status_code == 400

def test_chat_endpoint(client, mocker):
    mocker.patch('google.genai.Client')
    payload = {
        "message": "hello",
        "history": []
    }
    response = client.post('/api/chat', json=payload)
    assert response.status_code == 200
    
    response_fail = client.post('/api/chat')
    assert response_fail.status_code == 400
