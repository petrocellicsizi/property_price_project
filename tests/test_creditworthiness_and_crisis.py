"""
Unit és integrációs tesztek a Hitelképességi & JTM modulhoz és a Történelmi Válság Stresszteszthez.
"""
import pytest
from app import app
from core.creditworthiness import calculate_jtm_limit, calculate_creditworthiness
from core.crisis_replay import run_crisis_replay, CRISIS_DEFINITIONS


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_jtm_limit_rules():
    """MNB 32/2014 rendelet (800.000 Ft-os jövedelemhatár) szerinti JTM limitek ellenőrzése."""
    # < 800.000 Ft nettó jövedelem
    assert calculate_jtm_limit(500_000, 10.0) == 50.0
    assert calculate_jtm_limit(700_000, 10.0) == 50.0
    assert calculate_jtm_limit(500_000, 5.0) == 35.0
    assert calculate_jtm_limit(500_000, 3.0) == 25.0
    assert calculate_jtm_limit(500_000, 0.0) == 25.0

    # >= 800.000 Ft nettó jövedelem
    assert calculate_jtm_limit(800_000, 10.0) == 60.0
    assert calculate_jtm_limit(900_000, 10.0) == 60.0
    assert calculate_jtm_limit(800_000, 5.0) == 40.0
    assert calculate_jtm_limit(1_000_000, 3.0) == 30.0
    assert calculate_jtm_limit(1_000_000, 0.0) == 30.0


def test_calculate_creditworthiness_approved():
    """Hitelképes igénylő tesztelése (magas jövedelem, kényelmes JTM)."""
    res = calculate_creditworthiness(
        net_monthly_income_huf=1_000_000,
        loan_principal_huf=40_000_000,
        annual_interest_rate_pct=6.5,
        loan_term_years=20,
        interest_period_years=10.0,
        property_price_huf=60_000_000
    )
    assert res["status_code"] == "approved"
    assert res["metrics"]["is_jtm_compliant"] is True
    assert res["metrics"]["is_ltv_compliant"] is True
    assert res["metrics"]["calculated_jtm_pct"] < 50.0
    assert res["metrics"]["max_loan_amount_huf"] > 40_000_000
    assert "distribution" in res["charts"]
    assert "income_sensitivity" in res["charts"]


def test_calculate_creditworthiness_rejected_jtm():
    """Elutasított igénylő túllépett JTM miatt."""
    res = calculate_creditworthiness(
        net_monthly_income_huf=300_000,
        loan_principal_huf=60_000_000,
        annual_interest_rate_pct=7.0,
        loan_term_years=20,
        interest_period_years=10.0,
        property_price_huf=80_000_000
    )
    assert res["status_code"] == "rejected_jtm"
    assert res["metrics"]["is_jtm_compliant"] is False
    assert res["metrics"]["calculated_jtm_pct"] > 50.0


def test_calculate_creditworthiness_rejected_ltv_and_first_buyer():
    """HFM/LTV korlát tesztelése normál (80%) és első lakásvásárló (90%) esetén."""
    # 85% hitel (15% önerő) normál vevőnél elutasítva
    res_normal = calculate_creditworthiness(
        net_monthly_income_huf=1_500_000,
        loan_principal_huf=85_000_000,
        annual_interest_rate_pct=6.0,
        loan_term_years=20,
        property_price_huf=100_000_000,
        is_first_home_buyer=False
    )
    assert res_normal["status_code"] == "rejected_ltv"
    assert res_normal["metrics"]["is_ltv_compliant"] is False

    # Ugyanez első lakásvásárlóként jóváhagyva (90% LTV megengedett)
    res_first_buyer = calculate_creditworthiness(
        net_monthly_income_huf=1_500_000,
        loan_principal_huf=85_000_000,
        annual_interest_rate_pct=6.0,
        loan_term_years=20,
        property_price_huf=100_000_000,
        is_first_home_buyer=True
    )
    assert res_first_buyer["status_code"] in ["approved", "warning"]
    assert res_first_buyer["metrics"]["is_ltv_compliant"] is True


def test_creditworthiness_api_endpoint(client):
    """A /api/creditworthiness végpont integrációs tesztje."""
    payload = {
        "net_monthly_income_huf": 800_000,
        "loan_principal_huf": 45_000_000,
        "annual_interest_rate_pct": 6.5,
        "loan_term_years": 20,
        "interest_period_years": 10.0,
        "property_price_huf": 65_000_000,
        "is_first_home_buyer": True,
        "is_green_certified": True
    }
    response = client.post("/api/creditworthiness", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "metrics" in data["data"]
    assert "charts" in data["data"]


def test_crisis_replay_models():
    """Mindhárom történelmi válság stresszteszt lefutása és mutatói."""
    for cid in ["crisis_2008", "crisis_2020", "crisis_2022"]:
        res = run_crisis_replay(
            crisis_id=cid,
            property_val_0=70_000_000,
            down_payment_ratio=0.20,
            loan_annual_rate=0.065,
            loan_term_years=20,
            initial_rent_monthly=220_000,
            is_loan_fixed=True
        )
        assert res["crisis_id"] == cid
        assert "metrics" in res
        assert "trajectories" in res
        assert len(res["trajectories"]["timeline"]) == res["duration_years"] + 1
        assert res["metrics"]["final_buy_wealth"] is not None
        assert res["metrics"]["final_rent_wealth"] is not None
        assert res["metrics"]["max_buy_drawdown_pct"] >= 0.0


def test_crisis_replay_api_endpoint(client):
    """A /api/crisis_replay végpont integrációs tesztje."""
    payload = {
        "crisis_id": "crisis_2008",
        "property_val_0": 80_000_000,
        "down_payment_ratio": 0.25,
        "loan_annual_rate": 0.065,
        "loan_term_years": 20,
        "initial_rent_monthly": 260_000,
        "is_loan_fixed": False
    }
    response = client.post("/api/crisis_replay", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "metrics" in data["data"]
    assert "trajectories" in data["data"]


def test_zero_fixation_and_first_buyer_age():
    """0 év kamatfixálás (változó) és 41 év feletti első vásárló MNB korlátainak ellenőrzése."""
    res_var = calculate_creditworthiness(
        net_monthly_income_huf=700_000,
        loan_principal_huf=40_000_000,
        annual_interest_rate_pct=6.5,
        loan_term_years=20,
        interest_period_years=0.0,
        property_price_huf=60_000_000
    )
    assert res_var["metrics"]["mnb_limit_pct"] == 25.0

    res_older = calculate_creditworthiness(
        net_monthly_income_huf=1_500_000,
        loan_principal_huf=85_000_000,
        annual_interest_rate_pct=6.0,
        loan_term_years=20,
        property_price_huf=100_000_000,
        is_first_home_buyer=True,
        applicant_age=42
    )
    assert res_older["status_code"] == "rejected_ltv"
    assert res_older["metrics"]["is_ltv_compliant"] is False
