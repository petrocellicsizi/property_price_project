"""
Budapesti VIII. kerületi (Józsefváros) újépítésű lakáspiaci historikus adatok
és referencia szcenáriók (2014-2024 tényadatok és előrejelzések alapján).
"""

# VIII. kerületi historikus adatok (Corvin-negyed, Orczy-kert, Középső-Józsefváros)
DISTRICT_8_HISTORICAL_DATA = {
    "location": "Budapest VIII. kerület (Józsefváros) - Újépítésű szegmens",
    "historical_timeframe": "2014-2024",
    "historical_sqm_price_2014": 420_000,       # HUF / m2
    "historical_sqm_price_2024": 1_550_000,     # HUF / m2
    "cagr_property_price_historical": 0.138,     # 13.8% p.a.
    "historical_rent_sqm_2014": 1_900,          # HUF / m2 / hó
    "historical_rent_sqm_2024": 5_200,          # HUF / m2 / hó
    "cagr_rent_historical": 0.106,              # 10.6% p.a.
    "average_gross_yield_historical": 0.048,    # 4.8% átlagos bruttó bérleti hozam
    "typical_common_cost_sqm": 450,             # HUF / m2 / hó (újépítésű AA+ üzemeltetés)
    "transfer_tax_rate": 0.04                   # 4% vagyonszerzési illeték
}

# Előre definiált piaci szcenáriók a szimulációhoz
SCENARIOS = {
    "base": {
        "name": "Alap forgatókönyv (Base Case)",
        "probability_pct": 55,
        "description": "Kiegyensúlyozott piaci konvergencia, mérsékelt gazdasági növekedés és konszolidált infláció.",
        "params": {
            "property_size_sqm": 52.0,
            "price_per_sqm": 1_550_000.0,
            "renovation_cost_initial": 2_500_000.0,
            "transfer_tax_rate": 0.04,
            "legal_fee_rate": 0.01,
            "down_payment_ratio": 0.25,
            "loan_term_years": 20,
            "loan_interest_rate_annual": 0.065,
            "property_growth_rate_annual": 0.055,
            "initial_rent_monthly": 270_000.0,
            "rent_growth_rate_annual": 0.045,
            "opportunity_cost_rate_annual": 0.070,
            "maintenance_rate_annual": 0.010,
            "common_cost_monthly": 23_400.0
        }
    },
    "bear": {
        "name": "Pesszimista / Magas kamatkörnyezet (Bear Case)",
        "probability_pct": 25,
        "description": "Tartósan magas kamatszintek, stagnáló reálbérek és visszafogott ingatlanár-növekedés.",
        "params": {
            "property_size_sqm": 52.0,
            "price_per_sqm": 1_600_000.0,
            "renovation_cost_initial": 3_000_000.0,
            "transfer_tax_rate": 0.04,
            "legal_fee_rate": 0.01,
            "down_payment_ratio": 0.30,
            "loan_term_years": 20,
            "loan_interest_rate_annual": 0.085,
            "property_growth_rate_annual": 0.020,
            "initial_rent_monthly": 250_000.0,
            "rent_growth_rate_annual": 0.025,
            "opportunity_cost_rate_annual": 0.085,
            "maintenance_rate_annual": 0.015,
            "common_cost_monthly": 28_000.0
        }
    },
    "bull": {
        "name": "Ingatlanpiaci konjunktúra (Bull Case)",
        "probability_pct": 20,
        "description": "Erőteljes gazdasági expanzió, olcsó hitelezés és gyorsuló bérleti díj növekedés a Corvin-negyedben.",
        "params": {
            "property_size_sqm": 52.0,
            "price_per_sqm": 1_500_000.0,
            "renovation_cost_initial": 2_000_000.0,
            "transfer_tax_rate": 0.04,
            "legal_fee_rate": 0.01,
            "down_payment_ratio": 0.20,
            "loan_term_years": 20,
            "loan_interest_rate_annual": 0.050,
            "property_growth_rate_annual": 0.090,
            "initial_rent_monthly": 290_000.0,
            "rent_growth_rate_annual": 0.070,
            "opportunity_cost_rate_annual": 0.060,
            "maintenance_rate_annual": 0.008,
            "common_cost_monthly": 22_000.0
        }
    }
}
