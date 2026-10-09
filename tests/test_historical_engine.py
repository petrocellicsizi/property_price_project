import pytest
from unittest.mock import patch
from core.historical_engine import HistoricalEngine

MOCK_FINANCIAL_DATA = {
    "2004": {"sp500": 1000.0, "usdhuf": 200.0},
    "2024": {"sp500": 5000.0, "usdhuf": 360.0}
}

MOCK_REAL_ESTATE_DATA = {
    "XI. kerület": {
        "2004": 150.0,
        "2024": 800.0
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
