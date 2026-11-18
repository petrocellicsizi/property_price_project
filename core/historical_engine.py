import json
import os
import unicodedata
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

ROMAN_TO_INT = {
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
    'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
    'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20,
    'xxi': 21, 'xxii': 22, 'xxiii': 23
}
INT_TO_ROMAN = {v: k.upper() for k, v in ROMAN_TO_INT.items()}

BUDAPEST_DISTRICT_ALIASES = {
    "belváros": "V. kerület",
    "lipótváros": "V. kerület",
    "terézváros": "VI. kerület",
    "erzsébetváros": "VII. kerület",
    "józsefváros": "VIII. kerület",
    "ferencváros": "IX. kerület",
    "kőbánya": "X. kerület",
    "újbuda": "XI. kerület",
    "hegyvidék": "XII. kerület",
    "angyalföld": "XIII. kerület",
    "zugló": "XIV. kerület",
    "újpest": "IV. kerület",
    "óbuda": "III. kerület",
    "várkerület": "I. kerület",
    "budafok": "XXII. kerület",
    "tétény": "XXII. kerület",
    "csepel": "XXI. kerület",
    "kispest": "XIX. kerület",
    "pesterzsébet": "XX. kerület",
    "soroksár": "XXIII. kerület",
    "rákosmente": "XVII. kerület",
    "pestlőrinc": "XVIII. kerület",
    "mátyásföld": "XVI. kerület",
    "rákospalota": "XV. kerület"
}

def calculate_irr(cash_flows: List[float], iterations: int = 100, tolerance: float = 1e-5) -> float:
    """
    Kiszámítja a belső megtérülési rátát (IRR - Internal Rate of Return) 
    Newton-Raphson numerikus módszerrel, robusztus bisection fallback-kel.
    """
    if not cash_flows or len(cash_flows) < 2:
        return 0.0
    if all(cf >= 0 for cf in cash_flows) or all(cf <= 0 for cf in cash_flows):
        return 0.0

    rate = 0.08
    for _ in range(iterations):
        npv = 0.0
        d_npv = 0.0
        for t, cf in enumerate(cash_flows):
            denom = (1.0 + rate) ** t
            npv += cf / denom
            if t > 0:
                d_npv -= t * cf / (denom * (1.0 + rate))
        if abs(d_npv) < 1e-12:
            break
        new_rate = rate - npv / d_npv
        if abs(new_rate - rate) < tolerance:
            return round(new_rate * 100.0, 2)
        rate = new_rate
        if rate <= -0.99 or rate > 10.0:
            break

    # Robusztus bisection fallback
    low, high = -0.99, 5.0
    for _ in range(80):
        mid = (low + high) / 2.0
        npv = sum(cf / ((1.0 + mid) ** t) for t, cf in enumerate(cash_flows))
        if abs(npv) < 1e-4:
            return round(mid * 100.0, 2)
        if npv > 0:
            low = mid
        else:
            high = mid
    return round(mid * 100.0, 2)


class HistoricalEngine:
    def __init__(self):
        self.financial_data = self._load_json('financial_market_data.json')
        self.real_estate_data = self._load_json('real_estate_index.json')
        self.macro_data = self._load_json('macro_index.json')
        
    def _load_json(self, filename: str) -> Dict:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def normalize_location(self, city: str, district: str) -> str:
        """
        Rugalmasan és intelligensen feloldja a város és kerület megnevezéseket,
        ékezetfüggetlenül és szám/szöveges formátumok kezelésével.
        """
        def strip_accents(s: str) -> str:
            return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

        c_clean = (city or "").strip()
        d_clean = (district or "").strip()
        c_unaccent = strip_accents(c_clean)
        d_unaccent = strip_accents(d_clean)

        # Ha Budapest
        if not c_clean or c_unaccent == "budapest" or "pest" in c_unaccent:
            for alias, target in BUDAPEST_DISTRICT_ALIASES.items():
                if strip_accents(alias) in d_unaccent:
                    if target in self.real_estate_data:
                        return target

            d_num = d_unaccent.replace("kerulet", "").replace("ker.", "").replace(".", "").strip()
            
            if d_num in ROMAN_TO_INT:
                target = f"{INT_TO_ROMAN[ROMAN_TO_INT[d_num]]}. kerület"
                if target in self.real_estate_data:
                    return target

            if d_num.isdigit() and int(d_num) in INT_TO_ROMAN:
                target = f"{INT_TO_ROMAN[int(d_num)]}. kerület"
                if target in self.real_estate_data:
                    return target

            return "Budapest átlag" if "Budapest átlag" in self.real_estate_data else "Budapest"

        # Egyéb város / megyeszékhely keresése ékezetfüggetlenül
        for loc_key in self.real_estate_data.keys():
            if strip_accents(loc_key) == c_unaccent:
                return loc_key

        # Agglomeráció keresése
        agglo_cities = ["erd", "dunakeszi", "budaors", "szentendre", "godollo", "agglomeracio"]
        if any(agg in c_unaccent for agg in agglo_cities):
            for loc_key in self.real_estate_data.keys():
                if strip_accents(loc_key) in c_unaccent:
                    return loc_key
            if "Agglomeráció" in self.real_estate_data:
                return "Agglomeráció"

        # Fallback Budapest átlagra
        return "Budapest átlag" if "Budapest átlag" in self.real_estate_data else list(self.real_estate_data.keys())[0]

    def simulate(self, 
                 start_year: int, 
                 city: str, 
                 district: str, 
                 current_property_value_huf: float,
                 down_payment_pct: float = 20.0,
                 loan_interest_pct: float = 6.5,
                 loan_term_years: int = 20,
                 current_rent_huf: float = 200000,
                 current_utilities_huf: float = 30000,
                 tbsz_enabled: bool = True,
                 use_historical_rates: bool = False,
                 include_acquisition_costs: bool = False,
                 acquisition_cost_pct: float = 5.0,
                 fx_hedged: bool = False,
                 end_year: Optional[int] = None) -> Dict[str, Any]:
        
        max_available_year = max([int(y) for y in self.financial_data.keys()]) if self.financial_data else 2024
        if end_year is None or end_year > max_available_year:
            end_year = max_available_year
        if start_year > end_year:
            start_year = end_year
            
        start_year_str = str(start_year)
        end_year_str = str(end_year)
        latest_year_str = str(max_available_year)
        
        location_key = self.normalize_location(city, district)
        if location_key not in self.real_estate_data:
            return {"error": f"Nem található historikus adat a megadott helyszínre: {city} {district}"}
            
        location_index_data = self.real_estate_data[location_key]
        
        if start_year_str not in location_index_data or end_year_str not in location_index_data:
            return {"error": f"Hiányzó ingatlanárindex a(z) {start_year}-{end_year} évekre."}
            
        if start_year_str not in self.financial_data or end_year_str not in self.financial_data:
            return {"error": f"Hiányzó pénzügyi piaci adat a(z) {start_year}-{end_year} évekre."}
            
        latest_index = location_index_data.get(latest_year_str, location_index_data[end_year_str])
        start_index = location_index_data[start_year_str]
        end_index = location_index_data[end_year_str]
        
        # 1. Induló ingatlanár és tranzakciós költségek (Idea 2)
        initial_property_price = current_property_value_huf / (latest_index / start_index) if latest_index > 0 else current_property_value_huf
        down_payment_huf = initial_property_price * (down_payment_pct / 100.0)
        loan_amount_huf = max(0.0, initial_property_price - down_payment_huf)
        
        if include_acquisition_costs:
            upfront_fees_huf = initial_property_price * (acquisition_cost_pct / 100.0)
        else:
            upfront_fees_huf = 0.0
            
        # A vevő által ténylegesen letett készpénz (önrész + illeték/ügyvéd)
        base_capital = down_payment_huf + upfront_fees_huf
        
        # 2. Hitel amortizáció alapjai
        monthly_rate = (loan_interest_pct / 100.0) / 12.0
        n_payments = loan_term_years * 12
        if monthly_rate > 0:
            monthly_mortgage = loan_amount_huf * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        else:
            monthly_mortgage = loan_amount_huf / n_payments if n_payments > 0 else 0.0
            
        # 3. Portfóliók indulása (t = 0 / start_year)
        start_fin = self.financial_data[start_year_str]
        start_usdhuf = start_fin['usdhuf']
        start_sp500 = start_fin['sp500']
        
        # A bérlő a megspórolt teljes tőkét (önrész + illeték) befekteti
        sp500_shares = (base_capital / start_usdhuf) / start_sp500
        sp500_shares_hedged = (base_capital / start_usdhuf) / start_sp500
        allampapir_balance = base_capital
        bux_balance = base_capital
        
        rent_index = self.macro_data.get('rent_index', {})
        cpi_index = self.macro_data.get('cpi_index', {})
        latest_cpi_idx = cpi_index.get(latest_year_str, 1.0)
        start_cpi_idx = cpi_index.get(start_year_str, latest_cpi_idx)
        start_rent_idx = rent_index.get(start_year_str, 1.0)
        
        initial_monthly_buy = monthly_mortgage + (initial_property_price * 0.01 / 12.0) + (current_utilities_huf * (start_cpi_idx / latest_cpi_idx))
        initial_monthly_rent = (current_rent_huf * start_rent_idx) + (current_utilities_huf * (start_cpi_idx / latest_cpi_idx))
        initial_ltv = (loan_amount_huf / initial_property_price * 100.0) if initial_property_price > 0 else 0.0

        # Adattömbök inicializálása
        years = [start_year]
        # Vevő vagyona Day 0-n: Ingatlan piaci érték - hitel = down_payment_huf (az illeték nem épít ingatlanvagyont)
        real_estate_net_worth = [int(down_payment_huf)]
        property_market_values = [int(initial_property_price)]
        loan_balances = [int(loan_amount_huf)]
        sp500_net_worth = [int(base_capital)]
        sp500_hedged_net_worth = [int(base_capital)]
        allampapir_net_worth = [int(base_capital)]
        bux_net_worth = [int(base_capital)]
        
        buy_cashflows = [int(initial_monthly_buy)]
        rent_cashflows = [int(initial_monthly_rent)]
        dead_money_buy = [int(upfront_fees_huf)]
        dead_money_rent = [0]
        ltv_values = [round(min(100.0, max(0.0, initial_ltv)), 1)]
        
        cf_re = [-base_capital]
        cf_sp = [-base_capital]
        cf_bond = [-base_capital]
        cf_sp_hedged = [-base_capital]

        current_loan_balance = loan_amount_huf
        cum_dead_buy = float(upfront_fees_huf)
        cum_dead_rent = 0.0
        total_invested_sp500_huf = base_capital
        total_rent_paid = 0.0
        total_interest_paid = 0.0
        total_maintenance_paid = 0.0
        
        # 4. Éves szimulációs ciklus (t = 1..N, start_year + 1-től end_year-ig)
        for year in range(start_year + 1, end_year + 1):
            y_str = str(year)
            prev_y_str = str(year - 1)
            years.append(year)
            
            fin_year = self.financial_data.get(y_str, self.financial_data[start_year_str])
            y_usdhuf = fin_year.get('usdhuf', start_usdhuf)
            y_sp500 = fin_year.get('sp500', start_sp500)
            current_index = location_index_data.get(y_str, start_index)
            
            current_prop_val = initial_property_price * (current_index / start_index)
            annual_maintenance = current_prop_val * 0.01
            total_maintenance_paid += annual_maintenance
            
            interest_paid = 0.0
            actual_mortgage_paid = 0.0
            
            # Dinamikus piaci kamatláb opció
            if use_historical_rates:
                year_rate = fin_year.get('mortgage_rate_avg', loan_interest_pct)
                cur_monthly_rate = (year_rate / 100.0) / 12.0
                remaining_months = max(1, (loan_term_years - (year - start_year - 1)) * 12)
                if cur_monthly_rate > 0 and current_loan_balance > 0:
                    cur_monthly_mortgage = current_loan_balance * (cur_monthly_rate * (1 + cur_monthly_rate)**remaining_months) / ((1 + cur_monthly_rate)**remaining_months - 1)
                elif current_loan_balance > 0:
                    cur_monthly_mortgage = current_loan_balance / remaining_months
                else:
                    cur_monthly_mortgage = 0.0
            else:
                cur_monthly_rate = monthly_rate
                cur_monthly_mortgage = monthly_mortgage

            if current_loan_balance > 0:
                for _ in range(12):
                    if current_loan_balance <= 0:
                        break
                    m_interest = current_loan_balance * cur_monthly_rate
                    m_payment = min(cur_monthly_mortgage, current_loan_balance + m_interest)
                    m_principal = m_payment - m_interest
                    
                    interest_paid += m_interest
                    actual_mortgage_paid += m_payment
                    current_loan_balance -= m_principal
                    
            total_interest_paid += interest_paid
            
            y_cpi_idx = cpi_index.get(y_str, latest_cpi_idx)
            y_rent_idx = rent_index.get(y_str, 1.0)
            
            annual_rent = (current_rent_huf * 12) * y_rent_idx
            total_rent_paid += annual_rent
            annual_utils = (current_utilities_huf * 12) * (y_cpi_idx / latest_cpi_idx)
            
            buy_costs = actual_mortgage_paid + annual_maintenance + annual_utils
            rent_costs = annual_rent + annual_utils
            
            cash_difference_huf = buy_costs - rent_costs
            total_invested_sp500_huf += cash_difference_huf
            
            # Halott pénz felhalmozódás (tiszta lakhatási költség rezsi nélkül + induló illeték)
            cum_dead_buy += (interest_paid + annual_maintenance)
            cum_dead_rent += annual_rent
            
            # S&P 500 Unhedged (természetes devizás)
            dividend_yield = 0.015
            dividend_value_usd = sp500_shares * y_sp500 * dividend_yield
            sp500_shares += (dividend_value_usd / y_sp500)
            sp500_shares += (cash_difference_huf / y_usdhuf) / y_sp500
            sp500_shares = max(0.0, sp500_shares)
            rent_nw = sp500_shares * y_sp500 * y_usdhuf
            
            # S&P 500 FX-Hedged (devizafedezett, fix induló USD/HUF árfolyamon) [Idea 4]
            sp500_shares_hedged += (sp500_shares_hedged * y_sp500 * dividend_yield) / y_sp500
            sp500_shares_hedged += (cash_difference_huf / start_usdhuf) / y_sp500
            sp500_shares_hedged = max(0.0, sp500_shares_hedged)
            rent_nw_hedged = sp500_shares_hedged * y_sp500 * start_usdhuf
            
            # Magyar Állampapír (PMÁP / DKJ)
            bond_yield = fin_year.get('allampapir_yield', 5.0) / 100.0
            allampapir_balance = max(0.0, (allampapir_balance * (1.0 + bond_yield)) + cash_difference_huf)
            
            # BUX Index
            prev_bux = self.financial_data.get(prev_y_str, {}).get('bux', 10000.0)
            curr_bux = fin_year.get('bux', prev_bux)
            bux_growth = (curr_bux / prev_bux) if prev_bux > 0 else 1.0
            bux_balance = max(0.0, (bux_balance * bux_growth) + cash_difference_huf)
            
            buy_nw = current_prop_val - current_loan_balance
            ltv = (current_loan_balance / current_prop_val * 100.0) if current_prop_val > 0 else 0.0
            
            real_estate_net_worth.append(int(buy_nw))
            property_market_values.append(int(current_prop_val))
            loan_balances.append(int(max(0, current_loan_balance)))
            sp500_net_worth.append(int(rent_nw))
            sp500_hedged_net_worth.append(int(rent_nw_hedged))
            allampapir_net_worth.append(int(allampapir_balance))
            bux_net_worth.append(int(bux_balance))
            
            buy_cashflows.append(int(buy_costs / 12))
            rent_cashflows.append(int(rent_costs / 12))
            dead_money_buy.append(int(cum_dead_buy))
            dead_money_rent.append(int(cum_dead_rent))
            ltv_values.append(round(min(100.0, max(0.0, ltv)), 1))
            
            cf_re.append(-buy_costs)
            cf_sp.append(-buy_costs)
            cf_sp_hedged.append(-buy_costs)
            cf_bond.append(-buy_costs)

        final_re_val = real_estate_net_worth[-1]
        final_sp_val = sp500_net_worth[-1]
        final_sp_hedged_val = sp500_hedged_net_worth[-1]
        final_bond_val = allampapir_net_worth[-1]
        
        # Adózás (ha TBSZ nincs bekapcsolva):
        if not tbsz_enabled:
            sp500_profit = max(0, final_sp_val - total_invested_sp500_huf)
            final_sp_val -= int(sp500_profit * 0.15)
            sp500_net_worth[-1] = int(final_sp_val)

            sp500_h_profit = max(0, final_sp_hedged_val - total_invested_sp500_huf)
            final_sp_hedged_val -= int(sp500_h_profit * 0.15)
            sp500_hedged_net_worth[-1] = int(final_sp_hedged_val)
        
        # Ha a felhasználó a fedezett módot választotta fő S&P 500-ként
        display_sp_values = sp500_hedged_net_worth if fx_hedged else sp500_net_worth
        active_final_sp = final_sp_hedged_val if fx_hedged else final_sp_val
        
        if len(cf_re) > 1:
            cf_re[-1] += final_re_val
            cf_sp[-1] += final_sp_val
            cf_sp_hedged[-1] += final_sp_hedged_val
            cf_bond[-1] += final_bond_val
            
        re_irr = calculate_irr(cf_re)
        sp_irr = calculate_irr(cf_sp)
        sp_hedged_irr = calculate_irr(cf_sp_hedged)
        bond_irr = calculate_irr(cf_bond)
        
        years_diff = end_year - start_year
        
        re_total_growth_pct = ((final_re_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        sp_total_growth_pct = ((final_sp_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        sp_hedged_total_growth_pct = ((final_sp_hedged_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        bond_total_growth_pct = ((final_bond_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        
        re_cagr = ((final_re_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_re_val > 0 and base_capital > 0 else 0
        sp_cagr = ((final_sp_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_sp_val > 0 and base_capital > 0 else 0
        sp_hedged_cagr = ((final_sp_hedged_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_sp_hedged_val > 0 and base_capital > 0 else 0
        bond_cagr = ((final_bond_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_bond_val > 0 and base_capital > 0 else 0
        
        # Tiszta index növekedések
        prop_growth_unleveraged = ((end_index / start_index) - 1) * 100 if start_index > 0 else 0
        start_sp_usd = self.financial_data[start_year_str]['sp500']
        end_sp_usd = self.financial_data[end_year_str]['sp500']
        start_usdhuf = self.financial_data[start_year_str]['usdhuf']
        end_usdhuf = self.financial_data[end_year_str]['usdhuf']
        
        start_sp_huf = start_sp_usd * start_usdhuf
        end_sp_huf = end_sp_usd * end_usdhuf
        
        sp_usd_growth = ((end_sp_usd / start_sp_usd) - 1) * 100 if start_sp_usd > 0 else 0
        usdhuf_growth = ((end_usdhuf / start_usdhuf) - 1) * 100 if start_usdhuf > 0 else 0
        sp_huf_growth_unleveraged = ((end_sp_huf / start_sp_huf) - 1) * 100 if start_sp_huf > 0 else 0

        # Devizahatás forrásbontása (Currency Attribution Breakdown - Idea 4)
        dividend_compound_est_pct = ((1.015 ** years_diff) - 1.0) * 100.0 if years_diff > 0 else 0.0
        currency_attribution = {
            "usd_price_gain_pct": round(sp_usd_growth, 1),
            "fx_gain_pct": round(usdhuf_growth, 1),
            "dividend_est_gain_pct": round(dividend_compound_est_pct, 1),
            "total_unhedged_market_growth_pct": round(sp_huf_growth_unleveraged, 1)
        }

        return {
            "start_year": start_year,
            "end_year": end_year,
            "initial_capital_huf": int(base_capital),
            "down_payment_huf": int(down_payment_huf),
            "upfront_fees_huf": int(upfront_fees_huf),
            "include_acquisition_costs": include_acquisition_costs,
            "fx_hedged": fx_hedged,
            "location_used": location_key,
            "timeline": years,
            "real_estate_values": real_estate_net_worth,
            "property_market_values": property_market_values,
            "loan_balances": loan_balances,
            "sp500_values": display_sp_values,
            "sp500_unhedged_values": sp500_net_worth,
            "sp500_hedged_values": sp500_hedged_net_worth,
            "allampapir_values": allampapir_net_worth,
            "bux_values": bux_net_worth,
            "buy_cashflows": buy_cashflows,
            "rent_cashflows": rent_cashflows,
            "dead_money_buy": dead_money_buy,
            "dead_money_rent": dead_money_rent,
            "ltv_values": ltv_values,
            "kpi": {
                "re_total_growth_pct": re_total_growth_pct,
                "sp_total_growth_pct": sp_hedged_total_growth_pct if fx_hedged else sp_total_growth_pct,
                "sp_unhedged_total_growth_pct": sp_total_growth_pct,
                "sp_hedged_total_growth_pct": sp_hedged_total_growth_pct,
                "allampapir_total_growth_pct": bond_total_growth_pct,
                "re_cagr_pct": re_cagr,
                "sp_cagr_pct": sp_hedged_cagr if fx_hedged else sp_cagr,
                "sp_unhedged_cagr_pct": sp_cagr,
                "sp_hedged_cagr_pct": sp_hedged_cagr,
                "allampapir_cagr_pct": bond_cagr,
                "re_irr_pct": re_irr,
                "sp_irr_pct": sp_hedged_irr if fx_hedged else sp_irr,
                "sp_unhedged_irr_pct": sp_irr,
                "sp_hedged_irr_pct": sp_hedged_irr,
                "allampapir_irr_pct": bond_irr,
                "final_re_value": final_re_val,
                "final_sp_value": active_final_sp,
                "final_sp_unhedged_value": final_sp_val,
                "final_sp_hedged_value": final_sp_hedged_val,
                "final_allampapir_value": final_bond_val,
                "property_price_growth_pct": round(prop_growth_unleveraged, 1),
                "sp500_huf_growth_pct": round(sp_huf_growth_unleveraged, 1),
                "sp500_usd_growth_pct": round(sp_usd_growth, 1),
                "usdhuf_growth_pct": round(usdhuf_growth, 1),
                "currency_attribution": currency_attribution,
                "total_rent_paid": int(total_rent_paid),
                "total_interest_paid": int(total_interest_paid),
                "total_maintenance_paid": int(total_maintenance_paid),
                "total_upfront_fees": int(upfront_fees_huf)
            }
        }

    def calculate_rolling_windows(self,
                                  city: str,
                                  district: str,
                                  current_property_value_huf: float,
                                  holding_years: int = 10,
                                  down_payment_pct: float = 20.0,
                                  loan_interest_pct: float = 6.5,
                                  loan_term_years: int = 20,
                                  current_rent_huf: float = 200000,
                                  current_utilities_huf: float = 30000,
                                  tbsz_enabled: bool = True,
                                  use_historical_rates: bool = False,
                                  include_acquisition_costs: bool = False,
                                  acquisition_cost_pct: float = 5.0,
                                  fx_hedged: bool = False) -> Dict[str, Any]:
        """
        Historikus Ciklus- és Időtáv-elemzés (Idea 3):
        Végigfuttatja az összes lehetséges holding_years hosszúságú befektetési periódust
        2000 és a legfrissebb év között, és statisztikai győzelmi arányt (Win Rate),
        átlagos IRR-t és periódustáblázatot készít.
        """
        max_available_year = max([int(y) for y in self.financial_data.keys()]) if self.financial_data else 2024
        min_available_year = min([int(y) for y in self.financial_data.keys()]) if self.financial_data else 2000
        
        valid_holding_years = max(1, min(holding_years, max_available_year - min_available_year))
        
        windows = []
        re_wins = 0
        sp_wins = 0
        bond_wins = 0
        
        re_irrs = []
        sp_irrs = []
        bond_irrs = []

        start_years_range = range(min_available_year, max_available_year - valid_holding_years + 1)
        
        for s_year in start_years_range:
            e_year = s_year + valid_holding_years
            res = self.simulate(
                start_year=s_year,
                city=city,
                district=district,
                current_property_value_huf=current_property_value_huf,
                down_payment_pct=down_payment_pct,
                loan_interest_pct=loan_interest_pct,
                loan_term_years=loan_term_years,
                current_rent_huf=current_rent_huf,
                current_utilities_huf=current_utilities_huf,
                tbsz_enabled=tbsz_enabled,
                use_historical_rates=use_historical_rates,
                include_acquisition_costs=include_acquisition_costs,
                acquisition_cost_pct=acquisition_cost_pct,
                fx_hedged=fx_hedged,
                end_year=e_year
            )
            
            if "error" in res:
                continue
                
            kpi = res["kpi"]
            re_final = kpi["final_re_value"]
            sp_final = kpi["final_sp_value"]
            bond_final = kpi["final_allampapir_value"]
            
            re_irr = kpi["re_irr_pct"]
            sp_irr = kpi["sp_irr_pct"]
            bond_irr = kpi["allampapir_irr_pct"]
            
            re_irrs.append(re_irr)
            sp_irrs.append(sp_irr)
            bond_irrs.append(bond_irr)
            
            # Győztes megállapítása
            if re_final >= sp_final and re_final >= bond_final:
                winner = "Ingatlan"
                winner_color = "primary"
                re_wins += 1
            elif sp_final >= re_final and sp_final >= bond_final:
                winner = "S&P 500"
                winner_color = "success"
                sp_wins += 1
            else:
                winner = "Állampapír"
                winner_color = "purple"
                bond_wins += 1
                
            windows.append({
                "start_year": s_year,
                "end_year": e_year,
                "label": f"{s_year} - {e_year}",
                "winner": winner,
                "winner_color": winner_color,
                "re_final": re_final,
                "sp_final": sp_final,
                "bond_final": bond_final,
                "re_irr": re_irr,
                "sp_irr": sp_irr,
                "bond_irr": bond_irr,
                "re_sp_delta": re_final - sp_final
            })

        total_windows = len(windows)
        re_win_rate = round((re_wins / total_windows * 100.0), 1) if total_windows > 0 else 0.0
        sp_win_rate = round((sp_wins / total_windows * 100.0), 1) if total_windows > 0 else 0.0
        bond_win_rate = round((bond_wins / total_windows * 100.0), 1) if total_windows > 0 else 0.0
        
        avg_re_irr = round(sum(re_irrs) / len(re_irrs), 2) if re_irrs else 0.0
        avg_sp_irr = round(sum(sp_irrs) / len(sp_irrs), 2) if sp_irrs else 0.0
        avg_bond_irr = round(sum(bond_irrs) / len(bond_irrs), 2) if bond_irrs else 0.0

        return {
            "holding_years": valid_holding_years,
            "total_windows": total_windows,
            "stats": {
                "re_wins": re_wins,
                "re_win_rate_pct": re_win_rate,
                "sp_wins": sp_wins,
                "sp_win_rate_pct": sp_win_rate,
                "bond_wins": bond_wins,
                "bond_win_rate_pct": bond_win_rate,
                "avg_re_irr_pct": avg_re_irr,
                "avg_sp_irr_pct": avg_sp_irr,
                "avg_bond_irr_pct": avg_bond_irr
            },
            "windows": windows
        }
