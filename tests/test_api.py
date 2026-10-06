"""
Flask API integrációs tesztek a jelenlegi Dashboardhoz.
"""
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Főoldal (Dashboard) elérhetőségének ellenőrzése."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Saj\xc3\xa1t lak\xc3\xa1s vs. B\xc3\xa9rl\xc3\xa9s" in response.data or b"Dashboard" in response.data


def test_get_inputs(client):
    """Bemeneti adatok lekérése a REST API-ról."""
    response = client.get("/api/inputs")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "data" in data


def test_calculate_endpoint(client):
    """A kvantitatív Python számítási motor (/api/calculate) tesztelése."""
    payload = {
        "property": {
            "property_type": "Újépítésű társasház (AA+)",
            "size_sqm": 52,
            "room_count": 2,
            "price_total_huf": 80600000,
            "lawyer_fee_huf": 806000,
            "furnishing_cost_huf": 2800000
        },
        "loan": {
            "loan_amount_huf": 60450000,
            "interest_rate_annual_pct": 6.5,
            "loan_term_years": 20,
            "down_payment_huf": 20150000,
            "other_fees_huf": 120000
        },
        "rent": {
            "monthly_rent_huf": 270000,
            "monthly_utilities_huf": 34000
        },
        "investment": {
            "expected_return_annual_pct": 7.0
        }
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    res = response.get_json()
    assert res["status"] == "success"
    assert "raw" in res
    assert "formatted" in res
    assert res["raw"]["suggested_furnishing_huf"] > 0
    assert res["raw"]["suggested_rent_huf"] > 0
    assert res["raw"]["suggested_utilities_huf"] > 0
    assert res["raw"]["estimated_monthly_payment_huf"] > 0
    assert res["raw"]["total_initial_outlay_huf"] > 0


def test_store_inputs_empty(client):
    """Üres megjegyzésekkel történő mentés tesztelése."""
    payload = {
        "property": {"other_info": ""},
        "loan": {"other_info": ""},
        "rent": {"other_info": ""},
        "investment": {"other_info": ""}
    }
    response = client.post("/api/inputs", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "saved"
    assert data["gemini_analysis"]["status"] == "empty"


def test_calculate_endpoint_with_ai_evaluations(client):
    """A kvantitatív Python számítási motor tesztelése AI felülbírálatokkal (pl. +15% albérlet)."""
    payload = {
        "property": {
            "property_type": "Újépítésű társasház (AA+)",
            "size_sqm": 52,
            "room_count": 2,
            "price_total_huf": 80600000,
        },
        "loan": {
            "loan_amount_huf": 60450000,
            "interest_rate_annual_pct": 6.5,
            "loan_term_years": 20,
            "down_payment_huf": 20150000,
        },
        "rent": {},
        "investment": {},
        "ai_evaluations": {
            "rent": {
                "rent_adjustment_pct": 15.0,
                "utilities_adjustment_pct": 5.0
            },
            "property": {
                "furnishing_adjustment_huf": 300000
            }
        }
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    res = response.get_json()
    assert res["status"] == "success"
    # Alapértelmezett 270.000 Ft helyett 310.000 Ft javaslat
    assert res["raw"]["suggested_rent_huf"] == 310000
    assert res["formatted"]["suggested_rent"] == "310.000 Ft"
    assert res["raw"]["adjustments_info"]["rent_adjustment_pct"] == 15.0


def test_store_inputs_with_dunamenti_note(client):
    """Mentés Dunamenti megjegyzéssel: ellenőrzi az AI korrekciós javaslat integrációját."""
    payload = {
        "property": {
            "city": "Budapest",
            "district": "VIII. kerület",
            "property_type": "Újépítésű társasház (AA+)",
            "size_sqm": 52,
            "room_count": 2,
            "price_total_huf": 80600000,
            "other_info": "Prémium felújított belső tér"
        },
        "loan": {"other_info": ""},
        "rent": {
            "other_info": "Csak Dunamenti lakásban vagyok hajlandó lakni"
        },
        "investment": {"other_info": ""}
    }
    response = client.post("/api/inputs", json=payload)
    assert response.status_code == 200
    res = response.get_json()
    assert res["status"] == "saved"
    assert "ai_adjusted_suggestions" in res
    adj = res["ai_adjusted_suggestions"]
    # A Dunamenti igény miatt a javasolt albérlet felülbírálódik (+15% vagy AI által meghatározott)
    assert adj["suggested_rent_huf"] >= 270000
    assert "adjustments_applied" in adj
    assert "." in adj["formatted"]["suggested_rent"]

