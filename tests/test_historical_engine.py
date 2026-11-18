import pytest
from unittest.mock import patch
from core.historical_engine import HistoricalEngine, calculate_irr

MOCK_FINANCIAL_DATA = {
    "2004": {"sp500": 1000.0, "usdhuf": 200.0, "bux": 10000.0, "allampapir_yield": 8.0, "mortgage_rate_avg": 9.0},
    "2024": {"sp500": 5000.0, "usdhuf": 360.0, "bux": 50000.0, "allampapir_yield": 10.0, "mortgage_rate_avg": 7.0}
}

MOCK_REAL_ESTATE_DATA = {
    "XI. kerület": {
        "2004": 150.0,
        "2024": 800.0
    },
    "Budapest átlag": {
        "2004": 140.0,
        "2024": 700.0
    },
    "Debrecen": {
        "2004": 120.0,
        "2024": 650.0
    }
}

@patch('core.historical_engine.HistoricalEngine._load_json')
def test_historical_engine_simulate(mock_load_json):
    def side_effect(filename):
        if filename == 'financial_market_data.json':
            return MOCK_FINANCIAL_DATA
        if filename == 'macro_index.json':
            return {"rent_index": {"2004": 0.25, "2024": 1.0}, "cpi_index": {"2004": 0.40, "2024": 1.0}}
        return MOCK_REAL_ESTATE_DATA

    mock_load_json.side_effect = side_effect
    
    engine = HistoricalEngine()
    
    result = engine.simulate(2004, "Budapest", "XI. kerület", 60000000, 
                             down_payment_pct=20.0, loan_interest_pct=0.0, 
                             loan_term_years=20, current_rent_huf=200000, current_utilities_huf=0)
    
    assert "error" not in result
    assert result["start_year"] == 2004
    assert result["end_year"] == 2024
    assert result["location_used"] == "XI. kerület"
    assert result["initial_capital_huf"] == 2250000
    assert result["kpi"]["final_re_value"] == 60000000
    assert "allampapir_values" in result
    assert "bux_values" in result
    assert "re_irr_pct" in result["kpi"]
    assert "sp_irr_pct" in result["kpi"]

def test_historical_engine_real_data():
    """Valós fájlokkal történő szimuláció tesztelése."""
    engine = HistoricalEngine()
    res = engine.simulate(2004, "Budapest", "VIII. kerület", 60000000,
                          down_payment_pct=20.0, loan_interest_pct=6.5, loan_term_years=20)
    assert "error" not in res
    assert res["start_year"] == 2004
    assert res["end_year"] == 2024
    assert res["location_used"] == "VIII. kerület"
    assert len(res["timeline"]) == 21
    assert len(res["real_estate_values"]) == 21
    assert len(res["sp500_values"]) == 21
    assert len(res["allampapir_values"]) == 21
    assert res["loan_balances"][-1] == 0
    assert res["kpi"]["final_re_value"] == 60000000
    assert res["kpi"]["re_irr_pct"] > 0
    assert res["kpi"]["sp_irr_pct"] > 0

def test_location_normalization():
    """Helyszínek rugalmas felismerésének tesztje."""
    engine = HistoricalEngine()
    assert engine.normalize_location("Budapest", "8") == "VIII. kerület"
    assert engine.normalize_location("Budapest", "VIII") == "VIII. kerület"
    assert engine.normalize_location("Budapest", "Józsefváros") == "VIII. kerület"
    assert engine.normalize_location("Budapest", "11.") == "XI. kerület"
    assert engine.normalize_location("Budapest", "Újbuda") == "XI. kerület"
    assert engine.normalize_location("Debrecen", "") == "Debrecen"
    assert engine.normalize_location("gyor", "") == "Győr"
    assert engine.normalize_location("Dunakeszi", "") == "Dunakeszi"
    assert engine.normalize_location("IsmeretlenVáros", "") == "Budapest átlag"

def test_calculate_irr():
    """IRR numerikus számítási tesztek."""
    assert calculate_irr([]) == 0.0
    assert calculate_irr([-100, -50]) == 0.0
    assert calculate_irr([100, 200]) == 0.0
    irr = calculate_irr([-1000, 200, 300, 400, 500])
    assert 12.0 < irr < 13.5

def test_historical_rates_option():
    """Történelmi MNB hitelkamatok opció tesztelése."""
    engine = HistoricalEngine()
    res_fixed = engine.simulate(2014, "Budapest", "XI. kerület", 60000000,
                                down_payment_pct=20.0, loan_interest_pct=3.0, use_historical_rates=False)
    res_hist = engine.simulate(2014, "Budapest", "XI. kerület", 60000000,
                               down_payment_pct=20.0, loan_interest_pct=3.0, use_historical_rates=True)
    assert res_fixed["kpi"]["total_interest_paid"] != res_hist["kpi"]["total_interest_paid"]

def test_tbsz_toggle_effect():
    """TBSZ ki/be kapcsolásának hatása a végértékre."""
    engine = HistoricalEngine()
    res_tbsz = engine.simulate(2010, "Budapest", "XI. kerület", 60000000, tbsz_enabled=True)
    res_no_tbsz = engine.simulate(2010, "Budapest", "XI. kerület", 60000000, tbsz_enabled=False)
    assert res_tbsz["kpi"]["final_sp_value"] >= res_no_tbsz["kpi"]["final_sp_value"]

def test_acquisition_costs_option():
    """Idea 2: Tranzakciós költségek (4% illeték + 1% ügyvéd) beszámítása."""
    engine = HistoricalEngine()
    res_no_fees = engine.simulate(2004, "Budapest", "XI. kerület", 60000000, include_acquisition_costs=False)
    res_with_fees = engine.simulate(2004, "Budapest", "XI. kerület", 60000000, include_acquisition_costs=True, acquisition_cost_pct=5.0)
    
    assert res_with_fees["upfront_fees_huf"] > 0
    assert res_with_fees["initial_capital_huf"] > res_no_fees["initial_capital_huf"]
    assert res_with_fees["dead_money_buy"][0] == res_with_fees["upfront_fees_huf"]
    assert res_no_fees["dead_money_buy"][0] == 0

def test_currency_attribution_and_fx_hedging():
    """Idea 4: Devizahatás forrásbontás és FX-hedging tesztelése."""
    engine = HistoricalEngine()
    res = engine.simulate(2004, "Budapest", "XI. kerület", 60000000, fx_hedged=False)
    ca = res["kpi"]["currency_attribution"]
    assert "usd_price_gain_pct" in ca
    assert "fx_gain_pct" in ca
    assert "dividend_est_gain_pct" in ca
    assert "total_unhedged_market_growth_pct" in ca
    assert ca["usd_price_gain_pct"] > 0
    assert ca["fx_gain_pct"] > 0

    res_hedged = engine.simulate(2004, "Budapest", "XI. kerület", 60000000, fx_hedged=True)
    assert res_hedged["fx_hedged"] is True
    assert res_hedged["kpi"]["final_sp_value"] == res_hedged["kpi"]["final_sp_hedged_value"]
    # A forintgyengülés miatt a fedezett végérték alacsonyabb, mint az unhedged végérték
    assert res_hedged["kpi"]["final_sp_hedged_value"] < res["kpi"]["final_sp_unhedged_value"]

def test_calculate_rolling_windows():
    """Idea 3: Historikus Rolling Windows ciklus-elemzés tesztelése."""
    engine = HistoricalEngine()
    rolling = engine.calculate_rolling_windows(
        city="Budapest",
        district="XI. kerület",
        current_property_value_huf=60000000,
        holding_years=10
    )
    assert rolling["holding_years"] == 10
    assert rolling["total_windows"] == 15
    assert len(rolling["windows"]) == 15
    stats = rolling["stats"]
    assert stats["re_wins"] + stats["sp_wins"] + stats["bond_wins"] == 15
    assert round(stats["re_win_rate_pct"] + stats["sp_win_rate_pct"] + stats["bond_win_rate_pct"], 0) == 100.0

def test_sanity_and_edge_cases():
    """Szélsőérték és sanity ellenőrzések."""
    engine = HistoricalEngine()
    # 1. Start year == End year
    res_zero = engine.simulate(2024, "Budapest", "XI. kerület", 60000000, end_year=2024)
    assert "error" not in res_zero
    assert res_zero["kpi"]["re_cagr_pct"] == 0.0

    # 2. 100% önrész (készpénzes vásárlás, 0 hitel)
    res_cash = engine.simulate(2014, "Budapest", "XI. kerület", 60000000, down_payment_pct=100.0)
    assert res_cash["loan_balances"][0] == 0
    assert res_cash["kpi"]["total_interest_paid"] == 0

    # 3. 0% kamat
    res_zero_intr = engine.simulate(2014, "Budapest", "XI. kerület", 60000000, loan_interest_pct=0.0)
    assert res_zero_intr["kpi"]["total_interest_paid"] == 0
