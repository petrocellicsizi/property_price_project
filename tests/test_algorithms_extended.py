import pytest
from utils.algorithms import (
    calculate_suggested_furnishing,
    calculate_suggested_rent,
    calculate_suggested_price_per_sqm,
    calculate_suggested_utilities,
    calculate_ai_adjusted_suggestions
)

def test_suggested_furnishing_branches():
    assert calculate_suggested_furnishing("Újépítésű", 50, 2) > 0
    assert calculate_suggested_furnishing("Korszerű tégla", 50, 2) > 0
    assert calculate_suggested_furnishing("Régi nagypolgári", 50, 2) > 0
    assert calculate_suggested_furnishing("Panel (felújított", 50, 2) > 0
    assert calculate_suggested_furnishing("Panel (eredeti", 50, 2) > 0
    assert calculate_suggested_furnishing("Családi ház", 50, 2) > 0
    assert calculate_suggested_furnishing("Egyéb", 50, 2) > 0

def test_suggested_rent_branches():
    assert calculate_suggested_rent("Újépítésű", 50, 2) > 0
    assert calculate_suggested_rent("Korszerű tégla", 50, 2) > 0
    assert calculate_suggested_rent("Régi nagypolgári", 50, 2) > 0
    assert calculate_suggested_rent("Panel (felújított", 50, 2) > 0
    assert calculate_suggested_rent("Panel (eredeti", 50, 2) > 0
    assert calculate_suggested_rent("Családi ház", 50, 2) > 0
    assert calculate_suggested_rent("Egyéb", 50, 2) > 0

    assert calculate_suggested_rent("Újépítésű", 30, 1) > 0
    assert calculate_suggested_rent("Újépítésű", 60, 3) > 0
    assert calculate_suggested_rent("Újépítésű", 80, 3) > 0

    assert calculate_suggested_rent("Újépítésű", 50, 2, city="Szeged") > 0
    assert calculate_suggested_rent("Újépítésű", 50, 2, district="V. kerület") > 0
    assert calculate_suggested_rent("Újépítésű", 50, 2, district="II. kerület") > 0
    assert calculate_suggested_rent("Újépítésű", 50, 2, district="XVII. kerület") > 0

def test_suggested_price_per_sqm_branches():
    assert calculate_suggested_price_per_sqm("Újépítésű") > 0
    assert calculate_suggested_price_per_sqm("Korszerű tégla") > 0
    assert calculate_suggested_price_per_sqm("Régi nagypolgári") > 0
    assert calculate_suggested_price_per_sqm("Panel (felújított") > 0
    assert calculate_suggested_price_per_sqm("Panel (eredeti") > 0
    assert calculate_suggested_price_per_sqm("Családi ház") > 0
    assert calculate_suggested_price_per_sqm("Egyéb") > 0

    assert calculate_suggested_price_per_sqm("Újépítésű", condition="Kiváló") > 0
    assert calculate_suggested_price_per_sqm("Újépítésű", condition="Felújítandó") > 0

    assert calculate_suggested_price_per_sqm("Újépítésű", city="Debrecen") > 0
    assert calculate_suggested_price_per_sqm("Újépítésű", district="V. kerület") > 0
    assert calculate_suggested_price_per_sqm("Újépítésű", district="II. kerület") > 0
    assert calculate_suggested_price_per_sqm("Újépítésű", district="XVIII. kerület") > 0

def test_suggested_utilities_branches():
    assert calculate_suggested_utilities("Újépítésű", 50) > 0
    assert calculate_suggested_utilities("Korszerű tégla", 50) > 0
    assert calculate_suggested_utilities("Régi nagypolgári", 50) > 0
    assert calculate_suggested_utilities("Panel", 50) > 0
    assert calculate_suggested_utilities("Családi ház", 50) > 0
    assert calculate_suggested_utilities("Egyéb", 50) > 0

def test_ai_adjusted_suggestions():
    base = {
        "suggested_furnishing_huf": 1000000,
        "suggested_rent_huf": 200000,
        "suggested_utilities_huf": 30000,
        "suggested_price_per_sqm_huf": 1000000,
        "suggested_price_total_huf": 50000000,
    }
    ai = {
        "adjustments": {
            "furnishing": {"factor": 1.1},
            "rent": {"factor": 1.2},
            "utilities": {"factor": 0.9},
            "price_per_sqm": {"factor": 1.05},
        }
    }
    adj = calculate_ai_adjusted_suggestions(base, ai)
    assert adj["suggested_furnishing_huf"] == 1100000
    assert adj["suggested_rent_huf"] == 240000
    assert adj["suggested_utilities_huf"] == 27000
