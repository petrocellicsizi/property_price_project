import pytest
from utils.finance import (
    calculate_monthly_installment,
    calculate_monthly_return_rate,
    calculate_property_metrics,
    calculate_lawyer_fee_metrics,
    calculate_down_payment_metrics
)
from utils.formatters import parse_clean_number, format_with_dots, format_huf
from core.gemini_service import GeminiEvaluationService

def test_finance_edge_cases():
    assert calculate_monthly_installment(0, 0, 0) == 0
    # Zero interest fallback
    assert calculate_monthly_installment(1200, 0, 1) == 100
    
    assert calculate_monthly_return_rate(-2.0) == -0.17
    
    prop_no_price = calculate_property_metrics(52.0, price_per_sqm_huf=100000)
    assert prop_no_price['price_total_huf'] == 5200000
    
    prop_empty = calculate_property_metrics(52.0)
    assert prop_empty['price_total_huf'] == 0
    assert prop_empty['price_per_sqm_huf'] == 0
    
    lawyer_no_pct = calculate_lawyer_fee_metrics(1000000, lawyer_huf=20000)
    assert lawyer_no_pct['lawyer_fee_pct'] == 2.0
    
    lawyer_empty = calculate_lawyer_fee_metrics(1000000)
    assert lawyer_empty['lawyer_fee_pct'] == 1.0
    assert lawyer_empty['lawyer_fee_huf'] == 10000
    
    down_no_pct = calculate_down_payment_metrics(1000000, down_payment_huf=250000)
    assert down_no_pct['down_payment_pct'] == 25.0
    
    down_empty = calculate_down_payment_metrics(1000000)
    assert down_empty['down_payment_pct'] == 25.0
    assert down_empty['down_payment_huf'] == 250000

def test_formatters_edge_cases():
    assert parse_clean_number(None) == 0.0
    assert parse_clean_number('') == 0.0
    assert parse_clean_number('1.250,50') == 1250.50
    assert parse_clean_number('1,25') == 1.25
    assert parse_clean_number('abc') == 0.0
    
    assert format_with_dots(None) == ''
    assert format_with_dots('') == ''
    assert format_huf(None) == '0 Ft'
    assert format_huf('') == '0 Ft'

def test_gemini_service_robustness(mocker):
    service = GeminiEvaluationService()
    
    with pytest.raises(ValueError):
        service._clean_and_parse_json(None)
    with pytest.raises(ValueError):
        service._clean_and_parse_json('')
        
    valid_json = '{"evaluations": {"property": {"relevance_score": 5}}}'
    text_md = f'Here is your json:\n```json\n{valid_json}\n```'
    res = service._clean_and_parse_json(text_md)
    assert 'evaluations' in res
    
    text_md2 = f'```\n{valid_json}\n```'
    res2 = service._clean_and_parse_json(text_md2)
    assert 'evaluations' in res2
    
    text_trailing = '{"evaluations": {"property": {"relevance_score": 5}},}'
    res3 = service._clean_and_parse_json(text_trailing)
    assert 'evaluations' in res3
    
    # Test fallback heuristics
    payload = {
        "property": {"other_info": "nagyon lerobbant, felújítást igényel"},
        "rent": {"other_info": "kutya"}
    }
    # Mock client generate_content to throw error
    if service.client:
        mocker.patch.object(service.client.models, 'generate_content', side_effect=Exception("API Error"))
    
    evals = service.evaluate_all_notes(payload)
    assert evals["status"] == "fallback"
    assert evals["evaluations"]["property"]["furnishing_adjustment_huf"] == 300000
    assert evals["evaluations"]["rent"]["rent_adjustment_pct"] == 10.0
