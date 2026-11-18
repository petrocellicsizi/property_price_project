import pytest
from app import app
from core.engine import QuantitativeSimulationEngine
from core.defaults import SCENARIOS
from utils.algorithms import calculate_suggested_furnishing


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_furnishing_full_setup():
    """Teszteli, hogy a bútorozás a teljes lakás 0-ról bebútorozását fedi le (konyha gépekkel, nappali, háló stb.)."""
    # Újépítésű 52 m2, 2 szoba: 2.4M konyha gépekkel + 2*950k (1.9M) szobák + 52*25k (1.3M) = 5.600.000 Ft
    furnish_new = calculate_suggested_furnishing("Újépítésű társasház (AA+)", 52.0, 2.0)
    assert furnish_new == 5600000

    # Panel és egyéb típusok is reálisak
    furnish_panel = calculate_suggested_furnishing("Panel (felújított / panelprogramos)", 52.0, 2.0)
    assert furnish_panel > 4000000
    assert furnish_panel % 50000 == 0

    furnish_house = calculate_suggested_furnishing("Családi ház / Ikerház", 100.0, 3.0)
    assert furnish_house >= 9000000


def test_scenario_analysis_metrics():
    """Teszteli a szcenárióelemzés és valószínűségi modell megbízhatóságát."""
    engine = QuantitativeSimulationEngine(SCENARIOS["base"]["params"])
    scenario_res = engine.compute_scenario_analysis()

    assert "scenarios" in scenario_res
    assert "metrics" in scenario_res

    scenarios = scenario_res["scenarios"]
    metrics = scenario_res["metrics"]

    # 4 fő forgatókönyv ellenőrzése
    assert len(scenarios) == 4
    scenario_ids = [s["id"] for s in scenarios]
    assert "base" in scenario_ids
    assert "bull" in scenario_ids
    assert "bear" in scenario_ids
    assert "market_surge" in scenario_ids

    # Valószínűségek összege 100%
    total_prob = sum(s["probability_pct"] for s in scenarios)
    assert total_prob == 100

    # Kockázati metrikák
    assert 0 <= metrics["buy_win_probability_pct"] <= 100
    assert 0 <= metrics["rent_win_probability_pct"] <= 100
    assert metrics["buy_win_probability_pct"] + metrics["rent_win_probability_pct"] == 100
    assert "Ft" in metrics["formatted_expected_wealth_delta_30y"]
    assert "." in metrics["formatted_expected_wealth_delta_30y"]
    assert "risk_profile" in metrics
    assert "recommendation" in metrics


def test_api_calculate_includes_scenarios_and_updated_furnishing(client):
    """Ellenőrzi, hogy a /api/calculate végpont visszaadja a szcenáriókat és az új bútorozási javaslatot."""
    payload = {
        "property": {
            "city": "Budapest",
            "district": "VIII. kerület",
            "property_type": "Újépítésű társasház (AA+)",
            "size_sqm": 52,
            "room_count": 2,
            "price_total_huf": 80600000
        },
        "loan": {
            "down_payment_pct": 25,
            "loan_amount_huf": 60450000,
            "loan_term_years": 20,
            "interest_rate_annual_pct": 6.5
        },
        "rent": {
            "monthly_rent_huf": 270000,
            "monthly_utilities_huf": 34000
        },
        "investment": {
            "expected_return_annual_pct": 7.0,
            "simulation_years": 30
        }
    }

    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    raw = data["raw"]
    assert "scenarios" in raw
    assert len(raw["scenarios"]["scenarios"]) == 4
    assert raw["suggested_furnishing_huf"] == 5600000
    assert "5.600.000 Ft" in data["formatted"]["suggested_furnishing"]


def test_probability_distribution_and_mathematical_expectation():
    """Részletes teszt a szcenáriók valószínűségi mutatóinak matematikai helyességére."""
    engine = QuantitativeSimulationEngine(SCENARIOS["base"]["params"])
    analysis = engine.compute_scenario_analysis()
    scenarios = analysis["scenarios"]
    metrics = analysis["metrics"]

    # 1. Teljes valószínűség tétele: az elemi események összege pontosan 100%
    prob_sum = sum(s["probability_pct"] for s in scenarios)
    assert prob_sum == 100

    # 2. Partíció: Buy Win + Rent Win = 100%
    buy_win = metrics["buy_win_probability_pct"]
    rent_win = metrics["rent_win_probability_pct"]
    assert round(buy_win + rent_win, 5) == 100.0

    # 3. Kiszámított várható érték (Expected Value - EV) szigorú matematikai egyezése:
    # E[ΔW] = sum(p_i * ΔW_i)
    manual_ev = sum((s["probability_pct"] / 100.0) * s["wealth_delta_30y"] for s in scenarios)
    assert metrics["expected_wealth_delta_30y"] == round(manual_ev, 0)

    # 4. Győztes megjelölés konzisztenciája
    for s in scenarios:
        if s["wealth_delta_30y"] > 0:
            assert s["winner"] == "Saját lakás"
            assert "bg-success" in s["winner_class"]
        else:
            assert s["winner"] == "Bérlés & Befektetés"
            assert "bg-danger" in s["winner_class"]

    # 5. Várható megtérülési idő súlyozott átlagának ellenőrzése
    valid_beps = [(s["probability_pct"] / 100.0, s["break_even_year"]) for s in scenarios if s["break_even_year"] is not None]
    if valid_beps:
        expected_bep_manual = sum(p * yr for p, yr in valid_beps) / sum(p for p, _ in valid_beps)
        assert metrics["expected_break_even_year"] == round(expected_bep_manual, 1)


def test_scenarios_sensitivity_expensive_vs_cheap_market():
    """Teszteli a valószínűségi mutatók reális piaci viselkedését drága vs. olcsó lakás esetén."""
    base_params = dict(SCENARIOS["base"]["params"])

    # A) Extrém drága lakás alacsony bérleti díjjal (bérlésnek kell dominálnia)
    expensive_params = {
        **base_params,
        "price_per_sqm": 3270000.0,  # ~170M Ft vételár 52 m2-re
        "monthly_rent": 200000.0,
        "opportunity_cost_rate_annual": 0.08
    }
    engine_exp = QuantitativeSimulationEngine(expensive_params)
    exp_res = engine_exp.compute_scenario_analysis()
    exp_metrics = exp_res["metrics"]

    # Bérlés győzelmi esélyének nagynak kell lennie (>= 70%)
    assert exp_metrics["rent_win_probability_pct"] >= 70.0
    assert exp_metrics["risk_profile"] == "Magas alternatív költség kockázat"

    # B) Kifejezetten jó vétel / olcsó lakás magas bérleti díjjal (saját lakásnak kell nyernie)
    cheap_params = {
        **base_params,
        "price_per_sqm": 730000.0,  # ~38M Ft vételár 52 m2-re
        "monthly_rent": 320000.0,
        "opportunity_cost_rate_annual": 0.06
    }
    engine_cheap = QuantitativeSimulationEngine(cheap_params)
    cheap_res = engine_cheap.compute_scenario_analysis()
    cheap_metrics = cheap_res["metrics"]

    # Saját lakás győzelmi esélye 100%
    assert cheap_metrics["buy_win_probability_pct"] == 100.0
    assert cheap_metrics["risk_profile"] == "Alacsony kockázat / Magas saját lakás valószínűség"
    assert cheap_metrics["expected_wealth_delta_30y"] > 50000000
    assert cheap_metrics["expected_break_even_year"] is not None
    assert cheap_metrics["expected_break_even_year"] < 7.0


def test_scenario_annual_trajectories_and_dynamic_years():
    params_15y = {
        **SCENARIOS["base"]["params"],
        "simulation_years": 15
    }
    engine = QuantitativeSimulationEngine(params_15y)
    res = engine.compute_scenario_analysis()
    metrics = res["metrics"]
    scenarios = res["scenarios"]

    assert metrics["simulation_years"] == 15
    assert len(metrics["timeline_years"]) == 16  # 0 to 15
    assert len(metrics["expected_annual_wealth_delta"]) == 16

    for s in scenarios:
        assert len(s["annual_wealth_delta"]) == 16
        assert len(s["annual_buy_net_worth"]) == 16
        assert len(s["annual_rent_net_worth"]) == 16
        assert "wealth_delta_terminal" in s
        assert "formatted_delta_terminal" in s


