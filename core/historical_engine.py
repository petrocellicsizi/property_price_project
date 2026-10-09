import json
import os
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

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

    def simulate(self, 
                 start_year: int, 
                 city: str, 
                 district: str, 
                 current_property_value_huf: float,
                 down_payment_pct: float = 20.0,
                 loan_interest_pct: float = 6.5,
                 loan_term_years: int = 20,
                 current_rent_huf: float = 200000,
                 current_utilities_huf: float = 30000) -> Dict[str, Any]:
        
        end_year = max([int(y) for y in self.financial_data.keys()]) if self.financial_data else 2024
        start_year_str = str(start_year)
        end_year_str = str(end_year)
        
        location_key = district if city.lower() == "budapest" else city
        if location_key not in self.real_estate_data:
            location_key = "Budapest átlag" if city.lower() == "budapest" else "Budapest"
        if location_key not in self.real_estate_data:
            return {"error": "Location data not found."}
            
        location_index_data = self.real_estate_data[location_key]
        
        if start_year_str not in location_index_data or end_year_str not in location_index_data:
            return {"error": f"Missing real estate index data for years {start_year}-{end_year}."}
            
        if start_year_str not in self.financial_data or end_year_str not in self.financial_data:
            return {"error": f"Missing financial data for years {start_year}-{end_year}."}
            
        end_index = location_index_data[end_year_str]
        start_index = location_index_data[start_year_str]
        
        initial_property_price = current_property_value_huf / (end_index / start_index)
        
        rent_index = self.macro_data.get('rent_index', {})
        cpi_index = self.macro_data.get('cpi_index', {})
        
        annual_rent_yield = (current_rent_huf * 12) / current_property_value_huf
        annual_utils_2024 = current_utilities_huf * 12
        latest_cpi_idx = cpi_index.get('2024', 1.0)
        
        down_payment_huf = initial_property_price * (down_payment_pct / 100.0)
        loan_amount_huf = initial_property_price - down_payment_huf
        
        monthly_rate = (loan_interest_pct / 100.0) / 12.0
        n_payments = loan_term_years * 12
        if monthly_rate > 0:
            monthly_mortgage = loan_amount_huf * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        else:
            monthly_mortgage = loan_amount_huf / n_payments
            
        annual_mortgage = monthly_mortgage * 12
        
        sp500_shares = (down_payment_huf / self.financial_data[start_year_str]['usdhuf']) / self.financial_data[start_year_str]['sp500']
        
        years = []
        real_estate_net_worth = []
        sp500_net_worth = []
        
        # New arrays for additional charts
        buy_cashflows = []
        rent_cashflows = []
        dead_money_buy = []
        dead_money_rent = []
        ltv_values = []
        property_market_values = []
        loan_balances = []
        
        current_loan_balance = loan_amount_huf
        cum_dead_buy = 0
        cum_dead_rent = 0
        
        for year in range(start_year, end_year + 1):
            y_str = str(year)
            years.append(year)
            
            y_usdhuf = self.financial_data.get(y_str, {}).get('usdhuf', self.financial_data[start_year_str]['usdhuf'])
            y_sp500 = self.financial_data.get(y_str, {}).get('sp500', self.financial_data[start_year_str]['sp500'])
            current_index = location_index_data.get(y_str, start_index)
            
            # Buy
            current_prop_val = initial_property_price * (current_index / start_index)
            annual_maintenance = current_prop_val * 0.01
            
            buy_nw = current_prop_val - current_loan_balance
            real_estate_net_worth.append(int(max(0, buy_nw)))
            
            property_market_values.append(int(current_prop_val))
            loan_balances.append(int(current_loan_balance))
            
            interest_paid = 0
            if current_loan_balance > 0:
                interest_paid = current_loan_balance * (loan_interest_pct / 100.0)
                principal_paid = annual_mortgage - interest_paid
                current_loan_balance = max(0, current_loan_balance - principal_paid)
                
            ltv = (current_loan_balance / current_prop_val * 100) if current_prop_val > 0 else 0
            ltv_values.append(min(100, max(0, ltv)))
            
            # Rent
            y_cpi_idx = cpi_index.get(y_str, latest_cpi_idx)
            
            annual_rent = current_prop_val * annual_rent_yield
            annual_utils = annual_utils_2024 * (y_cpi_idx / latest_cpi_idx)
            
            buy_costs = annual_mortgage + annual_maintenance if current_loan_balance > 0 else annual_maintenance
            rent_costs = annual_rent + annual_utils
            
            # Cash flows
            buy_cashflows.append(int(buy_costs / 12))  # store monthly averages for the chart
            rent_cashflows.append(int(rent_costs / 12))
            
            # Dead money
            cum_dead_buy += (interest_paid + annual_maintenance)
            cum_dead_rent += rent_costs
            dead_money_buy.append(int(cum_dead_buy))
            dead_money_rent.append(int(cum_dead_rent))
            
            cash_difference_huf = buy_costs - rent_costs
            new_shares = (cash_difference_huf / y_usdhuf) / y_sp500
            sp500_shares += new_shares
            
            rent_nw = sp500_shares * y_sp500 * y_usdhuf
            sp500_net_worth.append(int(rent_nw))
            
        final_re_val = real_estate_net_worth[-1]
        final_sp_val = sp500_net_worth[-1]
        
        base_capital = down_payment_huf
        re_total_growth_pct = ((final_re_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        sp_total_growth_pct = ((final_sp_val / base_capital) - 1) * 100 if base_capital > 0 else 0
        
        years_diff = end_year - start_year
        re_cagr = ((final_re_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and base_capital > 0 and final_re_val > 0 else 0
        if final_sp_val <= 0:
            sp_cagr = -100.0
        else:
            sp_cagr = ((final_sp_val / base_capital) ** (1/years_diff) - 1) * 100 if years_diff > 0 and base_capital > 0 else 0

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
            "buy_cashflows": buy_cashflows,
            "rent_cashflows": rent_cashflows,
            "dead_money_buy": dead_money_buy,
            "dead_money_rent": dead_money_rent,
            "ltv_values": ltv_values,
            "kpi": {
                "re_total_growth_pct": re_total_growth_pct,
                "sp_total_growth_pct": sp_total_growth_pct,
                "re_cagr_pct": re_cagr,
                "sp_cagr_pct": sp_cagr,
                "final_re_value": final_re_val,
                "final_sp_value": final_sp_val
            }
        }
