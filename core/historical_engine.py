import json
import os
import unicodedata
from typing import Dict, Any, List

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
    Newton-Raphson numerikus módszerrel, bisection fallback-kel.
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
        hogy a felhasználó által begépelt tetszőleges formátum (pl. '8', 'VIII', '8. kerület')
        pontosan a megfelelő historikus indexhez kapcsolódjon.
        """
        def strip_accents(s: str) -> str:
            return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

        c_clean = (city or "").strip()
        d_clean = (district or "").strip()
        c_unaccent = strip_accents(c_clean)
        d_unaccent = strip_accents(d_clean)

        # Ha Budapest
        if not c_clean or c_unaccent == "budapest" or "pest" in c_unaccent:
            # Alias keresés (pl. Józsefváros, Újbuda)
            for alias, target in BUDAPEST_DISTRICT_ALIASES.items():
                if strip_accents(alias) in d_unaccent:
                    if target in self.real_estate_data:
                        return target

            # Tisztítás: szedjük le a 'kerület', 'ker.', '.', 'th' szavakat
            d_num = d_unaccent.replace("kerulet", "").replace("ker.", "").replace(".", "").strip()
            
            # Római szám vizsgálat (pl. 'viii', 'xi')
            if d_num in ROMAN_TO_INT:
                target = f"{INT_TO_ROMAN[ROMAN_TO_INT[d_num]]}. kerület"
                if target in self.real_estate_data:
                    return target

            # Arab szám vizsgálat (pl. '8', '11')
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
                 use_historical_rates: bool = False) -> Dict[str, Any]:
        
        end_year = max([int(y) for y in self.financial_data.keys()]) if self.financial_data else 2024
        start_year_str = str(start_year)
        end_year_str = str(end_year)
        
        location_key = self.normalize_location(city, district)
        if location_key not in self.real_estate_data:
            return {"error": f"Nem található historikus adat a megadott helyszínre: {city} {district}"}
            
        location_index_data = self.real_estate_data[location_key]
        
        if start_year_str not in location_index_data or end_year_str not in location_index_data:
            return {"error": f"Hiányzó ingatlanárindex a(z) {start_year}-{end_year} évekre."}
            
        if start_year_str not in self.financial_data or end_year_str not in self.financial_data:
            return {"error": f"Hiányzó pénzügyi piaci adat a(z) {start_year}-{end_year} évekre."}
            
        end_index = location_index_data[end_year_str]
        start_index = location_index_data[start_year_str]
        
        # 1. Induló ingatlanár visszaszámítása a kiválasztott évre
        initial_property_price = current_property_value_huf / (end_index / start_index)
        down_payment_huf = initial_property_price * (down_payment_pct / 100.0)
        loan_amount_huf = initial_property_price - down_payment_huf
        
        # 2. Hitel amortizáció alapjai
        monthly_rate = (loan_interest_pct / 100.0) / 12.0
        n_payments = loan_term_years * 12
        if monthly_rate > 0:
            monthly_mortgage = loan_amount_huf * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        else:
            monthly_mortgage = loan_amount_huf / n_payments
            
        # 3. Portfóliók indulása (t = 0 / start_year)
        start_fin = self.financial_data[start_year_str]
        sp500_shares = (down_payment_huf / start_fin['usdhuf']) / start_fin['sp500']
        allampapir_balance = down_payment_huf
        bux_balance = down_payment_huf
        
        rent_index = self.macro_data.get('rent_index', {})
        cpi_index = self.macro_data.get('cpi_index', {})
        latest_cpi_idx = cpi_index.get(end_year_str, 1.0)
        start_cpi_idx = cpi_index.get(start_year_str, latest_cpi_idx)
        start_rent_idx = rent_index.get(start_year_str, 1.0)
        
        # Kezdeti havi költségek t = 0-nál
        initial_monthly_buy = monthly_mortgage + (initial_property_price * 0.01 / 12.0) + (current_utilities_huf * (start_cpi_idx / latest_cpi_idx))
        initial_monthly_rent = (current_rent_huf * start_rent_idx) + (current_utilities_huf * (start_cpi_idx / latest_cpi_idx))
        initial_ltv = (loan_amount_huf / initial_property_price * 100.0) if initial_property_price > 0 else 0.0

        # Adattömbök inicializálása a t = 0 (start_year) kezdőállapottal
        years = [start_year]
        real_estate_net_worth = [int(down_payment_huf)]
        property_market_values = [int(initial_property_price)]
        loan_balances = [int(loan_amount_huf)]
        sp500_net_worth = [int(down_payment_huf)]
        allampapir_net_worth = [int(down_payment_huf)]
        bux_net_worth = [int(down_payment_huf)]
        
        buy_cashflows = [int(initial_monthly_buy)]
        rent_cashflows = [int(initial_monthly_rent)]
        dead_money_buy = [0]
        dead_money_rent = [0]
        ltv_values = [round(min(100.0, max(0.0, initial_ltv)), 1)]
        
        # IRR számításhoz készpénzáramlások
        cf_re = [-down_payment_huf]
        cf_sp = [-down_payment_huf]
        cf_bond = [-down_payment_huf]

        current_loan_balance = loan_amount_huf
        cum_dead_buy = 0.0
        cum_dead_rent = 0.0
        total_invested_sp500_huf = down_payment_huf
        total_rent_paid = 0.0
        total_interest_paid = 0.0
        total_maintenance_paid = 0.0
        
        # 4. Éves szimulációs ciklus (t = 1..N, azaz start_year + 1-től end_year-ig)
        for year in range(start_year + 1, end_year + 1):
            y_str = str(year)
            prev_y_str = str(year - 1)
            years.append(year)
            
            fin_year = self.financial_data.get(y_str, self.financial_data[start_year_str])
            y_usdhuf = fin_year.get('usdhuf', self.financial_data[start_year_str]['usdhuf'])
            y_sp500 = fin_year.get('sp500', self.financial_data[start_year_str]['sp500'])
            current_index = location_index_data.get(y_str, start_index)
            
            # Ingatlan piaci érték és fenntartás
            current_prop_val = initial_property_price * (current_index / start_index)
            annual_maintenance = current_prop_val * 0.01
            total_maintenance_paid += annual_maintenance
            
            # Hitel törlesztés az év során (12 hónap)
            interest_paid = 0.0
            actual_mortgage_paid = 0.0
            
            # Dinamikus piaci kamatláb opció (kamatfordulókor a törlesztőrészlet újrakalkulálódik a hátralévő futamidőre)
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
            
            # Bérleti díj és Rezsi
            y_cpi_idx = cpi_index.get(y_str, latest_cpi_idx)
            y_rent_idx = rent_index.get(y_str, 1.0)
            
            annual_rent = (current_rent_huf * 12) * y_rent_idx
            total_rent_paid += annual_rent
            annual_utils = (current_utilities_huf * 12) * (y_cpi_idx / latest_cpi_idx)
            
            buy_costs = actual_mortgage_paid + annual_maintenance + annual_utils
            rent_costs = annual_rent + annual_utils
            
            # Megtakarítási különbség (amennyivel a vétel többe vagy kevesebbe került a bérlésnél)
            cash_difference_huf = buy_costs - rent_costs
            total_invested_sp500_huf += cash_difference_huf
            
            # Halott pénz felhalmozódás (tiszta lakhatási költségveszteség rezsi nélkül, a UI-nak megfelelően)
            cum_dead_buy += (interest_paid + annual_maintenance)
            cum_dead_rent += annual_rent
            
            # S&P 500 portfólió frissítése
            # 1. Osztalék újrabefektetés (~1.5% éves osztalékhozam)
            dividend_yield = 0.015
            dividend_value_usd = sp500_shares * y_sp500 * dividend_yield
            sp500_shares += (dividend_value_usd / y_sp500)
            
            # 2. Havi cash-flow különbség befektetése (vagy részvényeladás bérleti hiány fedezésére)
            new_shares = (cash_difference_huf / y_usdhuf) / y_sp500
            sp500_shares += new_shares
            rent_nw = sp500_shares * y_sp500 * y_usdhuf
            
            # Magyar Állampapír portfólió frissítése (PMÁP / DKJ)
            bond_yield = fin_year.get('allampapir_yield', 5.0) / 100.0
            allampapir_balance = (allampapir_balance * (1.0 + bond_yield)) + cash_difference_huf
            
            # BUX index portfólió frissítése
            prev_bux = self.financial_data.get(prev_y_str, {}).get('bux', 10000.0)
            curr_bux = fin_year.get('bux', prev_bux)
            bux_growth = (curr_bux / prev_bux) if prev_bux > 0 else 1.0
            bux_balance = (bux_balance * bux_growth) + cash_difference_huf
            
            # Saját lakás nettó vagyon az év végén
            buy_nw = current_prop_val - current_loan_balance
            ltv = (current_loan_balance / current_prop_val * 100.0) if current_prop_val > 0 else 0.0
            
            # Értékek rögzítése
            real_estate_net_worth.append(int(buy_nw))
            property_market_values.append(int(current_prop_val))
            loan_balances.append(int(max(0, current_loan_balance)))
            sp500_net_worth.append(int(rent_nw))
            allampapir_net_worth.append(int(allampapir_balance))
            bux_net_worth.append(int(bux_balance))
            
            buy_cashflows.append(int(buy_costs / 12))
            rent_cashflows.append(int(rent_costs / 12))
            dead_money_buy.append(int(cum_dead_buy))
            dead_money_rent.append(int(cum_dead_rent))
            ltv_values.append(round(min(100.0, max(0.0, ltv)), 1))
            
            # Készpénzáramlás az IRR-hez
            cf_re.append(-buy_costs)
            cf_sp.append(-buy_costs)
            cf_bond.append(-buy_costs)

        final_re_val = real_estate_net_worth[-1]
        final_sp_val = sp500_net_worth[-1]
        final_bond_val = allampapir_net_worth[-1]
        
        # Adózás (ha TBSZ nincs bekapcsolva):
        # Magyarországon a lakossági állampapírok (PMÁP) 2019 óta kamatadó-mentesek.
        # Az S&P 500 esetén TBSZ hiányában 15% SZJA terheli a realizált tőkenyereséget.
        if not tbsz_enabled:
            sp500_profit = max(0, final_sp_val - total_invested_sp500_huf)
            tax_amount = sp500_profit * 0.15
            final_sp_val -= tax_amount
            sp500_net_worth[-1] = int(final_sp_val)
        
        # IRR végérték hozzáadása a készpénzáramlásokhoz
        if len(cf_re) > 1:
            cf_re[-1] += final_re_val
            cf_sp[-1] += final_sp_val
            cf_bond[-1] += final_bond_val
            
        re_irr = calculate_irr(cf_re)
        sp_irr = calculate_irr(cf_sp)
        bond_irr = calculate_irr(cf_bond)
        
        base_capital = down_payment_huf
        years_diff = end_year - start_year
        
        # Tőkemultiplikátor alapú teljes növekedés
        re_total_growth_pct = ((final_re_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        sp_total_growth_pct = ((final_sp_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        bond_total_growth_pct = ((final_bond_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        
        # Évesített saját tőke hozam (CAGR)
        re_cagr = ((final_re_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_re_val > 0 else 0
        sp_cagr = ((final_sp_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_sp_val > 0 else 0
        bond_cagr = ((final_bond_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and final_bond_val > 0 else 0
        
        # Tiszta eszközár index növekedés tőkeáttétel nélkül
        prop_growth_unleveraged = ((end_index / start_index) - 1) * 100 if start_index > 0 else 0
        start_sp_huf = self.financial_data[start_year_str]['sp500'] * self.financial_data[start_year_str]['usdhuf']
        end_sp_huf = self.financial_data[end_year_str]['sp500'] * self.financial_data[end_year_str]['usdhuf']
        sp_huf_growth_unleveraged = ((end_sp_huf / start_sp_huf) - 1) * 100 if start_sp_huf > 0 else 0

        return {
            "start_year": start_year,
            "end_year": end_year,
            "initial_capital_huf": int(base_capital),
            "location_used": location_key,
            "timeline": years,
            "real_estate_values": real_estate_net_worth,
            "property_market_values": property_market_values,
            "loan_balances": loan_balances,
            "sp500_values": sp500_net_worth,
            "allampapir_values": allampapir_net_worth,
            "bux_values": bux_net_worth,
            "buy_cashflows": buy_cashflows,
            "rent_cashflows": rent_cashflows,
            "dead_money_buy": dead_money_buy,
            "dead_money_rent": dead_money_rent,
            "ltv_values": ltv_values,
            "kpi": {
                "re_total_growth_pct": re_total_growth_pct,
                "sp_total_growth_pct": sp_total_growth_pct,
                "allampapir_total_growth_pct": bond_total_growth_pct,
                "re_cagr_pct": re_cagr,
                "sp_cagr_pct": sp_cagr,
                "allampapir_cagr_pct": bond_cagr,
                "re_irr_pct": re_irr,
                "sp_irr_pct": sp_irr,
                "allampapir_irr_pct": bond_irr,
                "final_re_value": final_re_val,
                "final_sp_value": final_sp_val,
                "final_allampapir_value": final_bond_val,
                "property_price_growth_pct": round(prop_growth_unleveraged, 1),
                "sp500_huf_growth_pct": round(sp_huf_growth_unleveraged, 1),
                "total_rent_paid": int(total_rent_paid),
                "total_interest_paid": int(total_interest_paid),
                "total_maintenance_paid": int(total_maintenance_paid)
            }
        }
