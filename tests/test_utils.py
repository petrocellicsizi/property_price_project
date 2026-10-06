"""
Tesztek a kvantitatív pénzügyi és piaci algoritmusokhoz (utils modulok).
"""
import pytest
from utils.formatters import format_huf, format_with_dots, parse_clean_number
from utils.algorithms import (
    calculate_suggested_furnishing,
    calculate_suggested_rent,
    calculate_suggested_utilities,
    calculate_ai_adjusted_suggestions,
)
from utils.finance import (
    calculate_monthly_installment,
    calculate_total_initial_outlay,
    calculate_monthly_return_rate,
    calculate_property_metrics,
    calculate_lawyer_fee_metrics,
    calculate_down_payment_metrics,
)


def test_formatters():
    assert format_with_dots(80600000) == "80.600.000"
    assert format_huf(80600000) == "80.600.000 Ft"
    assert format_huf(120000) == "120.000 Ft"
    assert parse_clean_number("80.600.000 Ft") == 80600000.0
    assert parse_clean_number(" 120.000 ") == 120000.0
    assert parse_clean_number(2500000) == 2500000.0


def test_suggested_furnishing():
    # Újépítésű AA+, 52 m2, 2 szoba
    furnish = calculate_suggested_furnishing("Újépítésű társasház (AA+)", 52.0, 2.0)
    # base 1.35M + 2*550k (1.1M) + 52*12k (624k) = 3.074M -> round to 50k = 3.05M or 3.1M
    assert furnish > 2000000
    assert furnish % 50000 == 0


def test_suggested_rent():
    # Újépítésű AA+, 52 m2, 2 szoba, Budapest VIII. kerület
    rent = calculate_suggested_rent("Újépítésű társasház (AA+)", 52.0, 2.0, "Budapest", "VIII. kerület")
    assert rent > 200000
    assert rent % 5000 == 0


def test_suggested_utilities():
    utils = calculate_suggested_utilities("Újépítésű társasház (AA+)", 52.0)
    assert utils >= 15000
    assert utils % 1000 == 0


def test_monthly_installment():
    # 60.450.000 Ft hitel, 6.5% kamat, 20 év
    pmt = calculate_monthly_installment(60450000, 6.5, 20)
    assert 440000 < pmt < 460000

    # 0% kamat ellenőrzése
    pmt_zero = calculate_monthly_installment(12000000, 0.0, 10)
    assert pmt_zero == 100000


def test_total_initial_outlay():
    # 20.15M önerő + 806k ügyvéd + 120k egyéb + 2.8M bútor + 4% illeték (3.224M a 80.6M-ból) = 27.1M
    total = calculate_total_initial_outlay(
        down_payment_huf=20150000,
        lawyer_fee_huf=806000,
        other_fees_huf=120000,
        furnishing_cost_huf=2800000,
        price_total_huf=80600000,
        transfer_tax_rate=0.04
    )
    assert total == 20150000 + 806000 + 120000 + 2800000 + int(80600000 * 0.04)


def test_monthly_return_rate():
    # 7% éves hozam havi megfelelője: (1.07)^(1/12) - 1 ~ 0.565% -> 0.57%
    rate = calculate_monthly_return_rate(7.0)
    assert rate == 0.57


def test_metrics_helpers():
    prop = calculate_property_metrics(52.0, price_total_huf=80600000)
    assert prop["price_per_sqm_huf"] == round(80600000 / 52.0)

    lawyer = calculate_lawyer_fee_metrics(80600000, lawyer_pct=1.0)
    assert lawyer["lawyer_fee_huf"] == 806000

    down = calculate_down_payment_metrics(80600000, down_payment_pct=25.0)
    assert down["down_payment_huf"] == 20150000
    assert down["loan_amount_huf"] == 60450000


def test_calculate_ai_adjusted_suggestions():
    """AI által korrigált javaslatok tesztelése (pl. Dunamenti felár +15%, felújítás +300k Ft)."""
    base = {
        "suggested_furnishing_huf": 2800000,
        "suggested_rent_huf": 270000,
        "suggested_utilities_huf": 34000,
    }

    # 1. Pozitív korrekció: +15% Dunamenti bérlet, +300.000 Ft felújítás
    ai_eval = {
        "property": {
            "furnishing_adjustment_huf": 300000
        },
        "rent": {
            "rent_adjustment_pct": 15.0,
            "utilities_adjustment_pct": 5.0
        }
    }
    adjusted = calculate_ai_adjusted_suggestions(base, ai_eval)

    # 2.8M + 300k = 3.1M
    assert adjusted["suggested_furnishing_huf"] == 3100000
    assert adjusted["formatted"]["suggested_furnishing"] == "3.100.000 Ft"

    # 270k * 1.15 = 310.5k -> kerekítve 5k-ra = 310.000 Ft
    assert adjusted["suggested_rent_huf"] == 310000
    assert adjusted["formatted"]["suggested_rent"] == "310.000 Ft"

    # 34k * 1.05 = 35.7k -> kerekítve 1k-ra = 36.000 Ft
    assert adjusted["suggested_utilities_huf"] == 36000
    assert adjusted["formatted"]["suggested_utilities"] == "36.000 Ft"

    assert adjusted["adjustments_applied"]["rent_adjustment_pct"] == 15.0
    assert adjusted["adjustments_applied"]["furnishing_adjustment_huf"] == 300000

    # 2. Negatív korrekció (diszkont): -10% bérleti díj
    ai_eval_discount = {
        "rent": {
            "rent_adjustment_pct": -10.0,
            "utilities_adjustment_pct": 0.0
        }
    }
    adj_discount = calculate_ai_adjusted_suggestions(base, ai_eval_discount)
    # 270k * 0.90 = 243k -> kerekítve 5k-ra = 245.000 Ft
    assert adj_discount["suggested_rent_huf"] == 245000
    assert adj_discount["formatted"]["suggested_rent"] == "245.000 Ft"
