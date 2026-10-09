"""
Pénzügyi motor (QuantitativeSimulationEngine) egységtesztek.
"""
import pytest
from core.engine import QuantitativeSimulationEngine
from core.defaults import SCENARIOS


def test_base_scenario_execution():
    """Alap forgatókönyv lefutása és alapvető pénzügyi összefüggések ellenőrzése."""
    base_params = SCENARIOS["base"]["params"]
    engine = QuantitativeSimulationEngine(base_params)
    result = engine.execute()
    
    assert "summary" in result
    assert "trajectories" in result
    
    summary = result["summary"]
    # Induló önerő és költségek léteznek
    assert summary["initial_equity_needed"] > 0
    # Havi törlesztő pozitív
    assert summary["monthly_loan_pmt"] > 0
    # Break-even pont létezik az alap esetben (jellemzően 5-10 év között a VIII. kerületben)
    assert summary["break_even_year"] is not None
    assert 1.0 <= summary["break_even_year"] <= 20.0
    
    trajectories = result["trajectories"]
    assert len(trajectories["month"]) == 360
    assert len(trajectories["buy_net_worth"]) == 360
    assert len(trajectories["rent_net_worth"]) == 360
    
    # A hiteltartozás a futamidő végére (240. hónap) 0-ra csökken
    loan_term_months = base_params["loan_term_years"] * 12
    assert trajectories["remaining_loan_balance"][loan_term_months - 1] == pytest.approx(0.0, abs=10.0)
    assert trajectories["remaining_loan_balance"][-1] == 0.0


def test_zero_loan_all_cash():
    """100% önerős (készpénzes) vásárlás esete: hiteltörlesztő 0, hiteltartozás 0."""
    params = dict(SCENARIOS["base"]["params"])
    params["down_payment_ratio"] = 1.0  # 100% önerő
    
    engine = QuantitativeSimulationEngine(params)
    result = engine.execute()
    
    summary = result["summary"]
    assert summary["loan_principal_initial"] == 0.0
    assert summary["monthly_loan_pmt"] == 0.0
    assert summary["total_interest_paid"] == 0.0


def test_zero_interest_rate():
    """0% kamatláb kezelése (nincs 0-val való osztási hiba a francia annuitásban)."""
    params = dict(SCENARIOS["base"]["params"])
    params["loan_interest_rate_annual"] = 0.0
    
    engine = QuantitativeSimulationEngine(params)
    result = engine.execute()
    
    summary = result["summary"]
    loan_principal = summary["loan_principal_initial"]
    expected_pmt = loan_principal / (params["loan_term_years"] * 12)
    assert summary["monthly_loan_pmt"] == pytest.approx(expected_pmt, rel=1e-3)
    assert summary["total_interest_paid"] == 0.0


def test_sensitivity_matrix_computation():
    """Érzékenységi mátrix generálásának tesztje."""
    base_params = SCENARIOS["base"]["params"]
    engine = QuantitativeSimulationEngine(base_params)
    
    rates = [0.05, 0.07]
    growths = [0.03, 0.06]
    matrix = engine.compute_sensitivity_matrix(
        etf_return_range=rates,
        property_growth_range=growths
    )
    
    assert matrix["etf_rates_pct"] == [5.0, 7.0]
    assert matrix["property_growth_rates_pct"] == [3.0, 6.0]
    assert len(matrix["wealth_difference_matrix"]) == 2
    assert len(matrix["wealth_difference_matrix"][0]) == 2
