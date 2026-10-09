import json
import os
from datetime import datetime

# Path to data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_financial_data():
    print("Generating S&P 500 and USD/HUF mock data...")
    # S&P 500 yearly returns (approximate)
    # USD/HUF historical rates (approximate year end)
    
    historical_usdhuf = {
        2000: 284, 2001: 279, 2002: 225, 2003: 207, 2004: 180, 2005: 213,
        2006: 191, 2007: 172, 2008: 187, 2009: 188, 2010: 208, 2011: 240,
        2012: 220, 2013: 215, 2014: 259, 2015: 286, 2016: 293, 2017: 258,
        2018: 280, 2019: 294, 2020: 297, 2021: 325, 2022: 373, 2023: 347, 2024: 360
    }
    
    historical_sp500_close = {
        2000: 1320, 2001: 1148, 2002: 879, 2003: 1111, 2004: 1211, 2005: 1248,
        2006: 1418, 2007: 1468, 2008: 903, 2009: 1115, 2010: 1257, 2011: 1257,
        2012: 1426, 2013: 1848, 2014: 2058, 2015: 2043, 2016: 2238, 2017: 2673,
        2018: 2506, 2019: 3230, 2020: 3756, 2021: 4766, 2022: 3839, 2023: 4769, 2024: 5700
    }
    
    final_data = {}
    for year in range(2000, 2025):
        final_data[str(year)] = {
            "sp500": float(historical_sp500_close[year]),
            "usdhuf": float(historical_usdhuf[year])
        }

    with open(os.path.join(DATA_DIR, 'financial_market_data.json'), 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4)
    print("Saved financial_market_data.json")

def generate_real_estate_index():
    print("Generating simulated real estate index data...")
    # Base year: 2000 = 100
    
    # Generic Budapest growth rates (simulated based on historical trends)
    base_rates = {
        2000: 1.0, 2001: 1.15, 2002: 1.10, 2003: 1.08, 2004: 1.05, 2005: 1.04,
        2006: 1.03, 2007: 1.02, 2008: 0.98, 2009: 0.90, 2010: 0.95, 2011: 0.97,
        2012: 0.96, 2013: 0.98, 2014: 1.12, 2015: 1.18, 2016: 1.22, 2017: 1.15,
        2018: 1.14, 2019: 1.20, 2020: 1.08, 2021: 1.15, 2022: 1.20, 2023: 1.02, 2024: 1.04
    }
    
    district_multipliers = {
        "I. kerület": 1.02, "II. kerület": 1.01, "III. kerület": 0.99,
        "V. kerület": 1.03, "VI. kerület": 1.02, "VII. kerület": 1.04,
        "VIII. kerület": 1.06, # gentrification
        "IX. kerület": 1.05, "XI. kerület": 1.03, "XIII. kerület": 1.04,
        "XIV. kerület": 1.00, "Budapest átlag": 1.00
    }
    
    # Fill in the rest with 1.00
    for i in range(1, 24):
        dist_name = ["I.", "II.", "III.", "IV.", "V.", "VI.", "VII.", "VIII.", "IX.", "X.", "XI.", "XII.", "XIII.", "XIV.", "XV.", "XVI.", "XVII.", "XVIII.", "XIX.", "XX.", "XXI.", "XXII.", "XXIII."][i-1] + " kerület"
        if dist_name not in district_multipliers:
            district_multipliers[dist_name] = 1.00
            
    # Also add generic cities
    district_multipliers["Budapest"] = 1.00
    district_multipliers["Debrecen"] = 1.02
    district_multipliers["Győr"] = 1.01
    district_multipliers["Szeged"] = 1.01
    district_multipliers["Pécs"] = 0.98
    
    indices = {}
    
    for district, mult in district_multipliers.items():
        district_data = {}
        current_index = 100.0
        for year in range(2000, 2025):
            rate = base_rates[year]
            if year >= 2014: # gentrification effect boom
                rate = 1.0 + ((rate - 1.0) * mult)
            
            if year == 2000:
                current_index = 100.0
            else:
                current_index *= rate
                
            district_data[str(year)] = current_index
        indices[district] = district_data
        
    with open(os.path.join(DATA_DIR, 'real_estate_index.json'), 'w', encoding='utf-8') as f:
        json.dump(indices, f, indent=4, ensure_ascii=False)
    print("Saved real_estate_index.json")

if __name__ == "__main__":
    fetch_financial_data()
    generate_real_estate_index()
