"""
Kvantitatív Pénzügyi Szimulációs Motor
Diszkontált Cash-Flow (DCF), Francia annuitás, tőkeáttétel és vagyonegyenleg-alapú modellezés.
"""
from typing import Dict, Any, List, Optional
import numpy as np

from core.logger import logger

class QuantitativeSimulationEngine:
    """
    Saját lakás vs. Bérlés pénzügyi szimulációs motor Budapest VIII. kerületi
    újépítésű lakáspiaci paraméterekre kalibrálva.
    """

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        
        # Alapméretek és futamidők (hónapokban)
        self.sim_years = int(params.get("simulation_years", 30))
        self.total_months = self.sim_years * 12
        self.loan_term_years = int(params.get("loan_term_years", 20))
        self.loan_months = min(self.loan_term_years * 12, self.total_months)
        
        self.t = np.arange(1, self.total_months + 1)

    def execute(self) -> Dict[str, Any]:
        """
        Lefuttatja a teljes 30 éves havi szimulációt vektorizált NumPy műveletekkel.
        """
        logger.debug(f"Szimulációs motor indítása: {self.sim_years} év, {self.params.get('property_size_sqm', 0)} m2, Vételár/m2: {self.params.get('price_per_sqm', 0)}")
        # 1. Ingatlan alapadatok és kezdeti tőkeszükséglet (t = 0)
        size = float(self.params["property_size_sqm"])
        price_sqm = float(self.params["price_per_sqm"])
        property_val_0 = size * price_sqm
        
        down_payment_ratio = float(self.params["down_payment_ratio"])
        down_payment = property_val_0 * down_payment_ratio
        
        tax_rate = float(self.params.get("transfer_tax_rate", 0.04))
        legal_rate = float(self.params.get("legal_fee_rate", 0.01))
        renovation_initial = float(self.params.get("renovation_cost_initial", 2_500_000.0))
        
        initial_upfront_fees = (property_val_0 * (tax_rate + legal_rate)) + renovation_initial
        initial_equity_needed = down_payment + initial_upfront_fees
        loan_principal_0 = max(0.0, property_val_0 - down_payment)

        # 2. Hitel amortizációs pálya (Francia annuitás)
        loan_annual_rate = float(self.params["loan_interest_rate_annual"])
        r_loan_m = loan_annual_rate / 12.0
        
        pmt_monthly = 0.0
        loan_balance = np.zeros(self.total_months)
        loan_interest_paid = np.zeros(self.total_months)
        loan_principal_paid = np.zeros(self.total_months)
        
        if loan_principal_0 > 0 and self.loan_months > 0:
            if r_loan_m > 0:
                pmt_monthly = loan_principal_0 * (r_loan_m * (1.0 + r_loan_m)**self.loan_months) / ((1.0 + r_loan_m)**self.loan_months - 1.0)
                
                # Hitel futamideje alatti hónapok (1 .. loan_months)
                t_loan = np.arange(1, self.loan_months + 1)
                balance_during_loan = loan_principal_0 * (((1.0 + r_loan_m)**self.loan_months - (1.0 + r_loan_m)**t_loan) 
                                                          / ((1.0 + r_loan_m)**self.loan_months - 1.0))
                balance_during_loan = np.maximum(balance_during_loan, 0.0)
                loan_balance[:self.loan_months] = balance_during_loan
                
                # Kamat és tőkerész bontás
                prev_balance = np.empty(self.loan_months)
                prev_balance[0] = loan_principal_0
                prev_balance[1:] = balance_during_loan[:-1]
                
                interest_during_loan = prev_balance * r_loan_m
                principal_during_loan = pmt_monthly - interest_during_loan
                
                loan_interest_paid[:self.loan_months] = interest_during_loan
                loan_principal_paid[:self.loan_months] = principal_during_loan
            else:
                # 0%-os kamat kedvezmény / támogatás esete
                pmt_monthly = loan_principal_0 / self.loan_months
                principal_during_loan = np.full(self.loan_months, pmt_monthly)
                loan_principal_paid[:self.loan_months] = principal_during_loan
                loan_balance[:self.loan_months] = np.maximum(loan_principal_0 - np.cumsum(principal_during_loan), 0.0)

        # 3. Ingatlan piaci értékének időbeli növekedése
        prop_growth_annual = float(self.params["property_growth_rate_annual"])
        g_prop_m = (1.0 + prop_growth_annual)**(1.0 / 12.0) - 1.0
        property_value_traj = property_val_0 * (1.0 + g_prop_m)**self.t

        # 4. Tulajdonosi fenntartási költségek és havi összkiadás
        maint_rate_annual = float(self.params.get("maintenance_rate_annual", 0.01))
        common_cost_base = float(self.params.get("common_cost_monthly", 23_400.0))
        # Közös költség és karbantartás inflálódása a bérleti díj növekedési ütemével arányosan (általános infláció proxy)
        rent_growth_annual = float(self.params["rent_growth_rate_annual"])
        g_rent_m = (1.0 + rent_growth_annual)**(1.0 / 12.0) - 1.0
        common_cost_traj = common_cost_base * (1.0 + g_rent_m)**self.t
        
        # JAVÍTOTT KARBANTARTÁS: Az induló érték 1%-a, ami a sima inflációval nő, nem pedig az ingatlanbuborékkal!
        maintenance_traj = (property_val_0 * (maint_rate_annual / 12.0)) * (1.0 + g_rent_m)**self.t
        
        # Havi tulajdonosi készpénzkiadás
        monthly_buy_pmt = np.zeros(self.total_months)
        monthly_buy_pmt[:self.loan_months] = pmt_monthly
        monthly_buy_outflow = monthly_buy_pmt + maintenance_traj + common_cost_traj

        # Tulajdonosi Nettó Vagyon (Net Worth) - 1.5% eladási tranzakciós költséggel diszkontálva
        sale_fee_rate = float(self.params.get("sale_transaction_fee_rate", 0.015))
        buy_net_worth = (property_value_traj * (1.0 - sale_fee_rate)) - loan_balance

        # 5. Bérlői pálya és Alternatív Tőkepiaci Portfólió
        rent_initial_monthly = float(self.params["initial_rent_monthly"])
        rent_traj = rent_initial_monthly * (1.0 + g_rent_m)**self.t
        
        # A bérlő havi kiadása: Bérleti díj + Rezsi (ugyanaz a rezsi, mint a tulajdonosnál)
        monthly_rent_outflow = rent_traj + common_cost_traj
        
        # Bérlő kezdeti vagyona = a vásárláshoz szükséges teljes önerő és induló díjak
        r_opp_annual = float(self.params["opportunity_cost_rate_annual"])
        
        # ETF Adózás kezelése (TBSZ)
        # Ha a TBSZ ki van kapcsolva, akkor 15% SZJA terheli a hozamot (a nettó hozamot vesszük)
        is_tbsz = self.params.get("tbsz_enabled", True)
        if not is_tbsz:
            r_opp_annual = r_opp_annual * 0.85
            
        r_opp_m = (1.0 + r_opp_annual)**(1.0 / 12.0) - 1.0
        
        # Közös költségvetés: A havi maximális kiadás a kettő közül
        budget_m = np.maximum(monthly_buy_outflow, monthly_rent_outflow)
        
        # Befektetésre szánt havi összegek az alapesetekben:
        rent_investment_monthly = budget_m - monthly_rent_outflow
        buy_investment_monthly = budget_m - monthly_buy_outflow
        
        # 3. Szcenárió: Befektetési célú lakásvásárlás (Buy-to-Let / BTL)
        # Felhasználói kérés: nem számoljuk bele a saját lakhatás (albérlet) költségét, tisztán befektetésként nézzük.
        # Adózás a bérleti díj után: 15% SZJA a bevétel 90%-a után (10% költséghányad) -> effektív 13.5% adó
        tax_on_rent_rate = 0.135 
        rent_traj_net = rent_traj * (1.0 - tax_on_rent_rate)
        
        # BTL befektetési egyenleg = Rendelkezésre álló büdzsé - Saját lakhatás költsége (albérlet) + Nettó bérleti díj - Hitel - Karbantartás
        btl_investment_monthly = budget_m - monthly_rent_outflow + rent_traj_net - monthly_buy_pmt - maintenance_traj
        
        rent_portfolio = np.zeros(self.total_months)
        buy_portfolio = np.zeros(self.total_months)
        btl_portfolio = np.zeros(self.total_months)
        
        rent_wealth = initial_equity_needed
        buy_wealth = 0.0
        btl_wealth = 0.0
        
        for m in range(self.total_months):
            rent_wealth = rent_wealth * (1.0 + r_opp_m) + rent_investment_monthly[m]
            rent_portfolio[m] = rent_wealth
            
            buy_wealth = buy_wealth * (1.0 + r_opp_m) + buy_investment_monthly[m]
            buy_portfolio[m] = buy_wealth
            
            btl_wealth = btl_wealth * (1.0 + r_opp_m) + btl_investment_monthly[m]
            btl_portfolio[m] = btl_wealth

        # Ingatlan tőkeértéke (eladási költséggel és hitellel csökkentve)
        property_equity = buy_net_worth # Ezt korábban így neveztük el
        
        # Hozzáadjuk a felhalmozott értékpapír portfóliókat a lakásvagyonhoz
        buy_net_worth = property_equity + buy_portfolio
        btl_net_worth = property_equity + btl_portfolio

        # 6. Break-Even Point (Fordulópont) keresése
        wealth_delta = buy_net_worth - rent_portfolio
        
        # Keressük az első olyan hónapot, ahol a saját lakás vagyona tartósan meghaladja a bérlőjét
        bep_indices = np.where(wealth_delta >= 0)[0]
        
        bep_month: Optional[int] = None
        bep_year: Optional[float] = None
        if len(bep_indices) > 0:
            bep_idx = int(bep_indices[0])
            bep_month = bep_idx + 1
            bep_year = round(bep_month / 12.0, 2)

        # 7. Diszkontált Cash-Flow (DCF) és Jelenérték (NPV)
        # A diszkontrátát logikusan az alternatív költséghez (opportunity cost = ETF hozam) kötjük!
        discount_annual = r_opp_annual
        r_disc_m = (1.0 + discount_annual)**(1.0 / 12.0) - 1.0
        discount_factors = 1.0 / ((1.0 + r_disc_m)**self.t)
        
        # DCF-hez a teljes havi cash-outflow-t vesszük figyelembe (kiadás + befektetett összeg)
        total_outflow_buy = monthly_buy_outflow + buy_investment_monthly
        total_outflow_rent = monthly_rent_outflow + rent_investment_monthly
        
        # NPV profilok
        dcf_buy = np.cumsum(-total_outflow_buy * discount_factors) - initial_equity_needed + (buy_net_worth * discount_factors)
        dcf_rent = np.cumsum(-total_outflow_rent * discount_factors) - 0.0 + (rent_portfolio * discount_factors)

        # Összegző metrikák
        total_interest = float(np.sum(loan_interest_paid))
        total_rent_paid = float(np.sum(rent_traj))
        total_maintenance_paid = float(np.sum(maintenance_traj + common_cost_traj))

        # 8. Új kimutatások: Dead Money, LTV, Real Wealth, ROE, Price-to-Rent
        # Halott pénz (Dead Money)
        total_buy_dead_money = float(initial_upfront_fees) + float(total_interest) + float(total_maintenance_paid)
        total_rent_dead_money = float(total_rent_paid) + float(np.sum(common_cost_traj))
        
        # Tőkearányos megtérülés (ROE / CAGR of Equity)
        cagr_equity = 0.0
        if initial_equity_needed > 0:
            if buy_net_worth[-1] <= 0:
                cagr_equity = -1.0
            else:
                cagr_equity = (buy_net_worth[-1] / initial_equity_needed) ** (1.0 / self.sim_years) - 1.0
            
        # LTV (Loan-to-Value) pálya
        ltv_traj = loan_balance / property_value_traj
        
        # Infláció-korrigált reálvagyon pálya (bérletidíj-növekedést használva inflációs proxy-ként)
        real_buy_net_worth = buy_net_worth / ((1.0 + g_rent_m)**self.t)
        real_rent_net_worth = rent_portfolio / ((1.0 + g_rent_m)**self.t)
        
        # Price-to-Rent Ratio és Bruttó Hozam
        annual_rent = rent_initial_monthly * 12.0
        price_to_rent = property_val_0 / annual_rent if annual_rent > 0 else 0.0
        gross_yield = annual_rent / property_val_0 if property_val_0 > 0 else 0.0

        # Éves mintavételezés a grafikonokhoz (hogy a JSON válasz kompakt és gyors maradjon)
        sample_step = 1  # 360 adatpont havi felbontásban teljesen jól kezelhető a kliensen
        sampled_indices = np.arange(0, self.total_months, sample_step)
        
        logger.debug(f"Szimuláció véget ért. Break-Even év: {bep_year}, NPV(Buy): {dcf_buy[-1]:.0f}, NPV(Rent): {dcf_rent[-1]:.0f}")
        
        return {
            "summary": {
                "break_even_month": bep_month,
                "break_even_year": bep_year,
                "break_even_status": "Elérve" if bep_year is not None else "Nem térül meg a vizsgált időtávon",
                "initial_equity_needed": round(float(initial_equity_needed), 0),
                "property_initial_value": round(float(property_val_0), 0),
                "loan_principal_initial": round(float(loan_principal_0), 0),
                "monthly_loan_pmt": round(float(pmt_monthly), 0),
                "total_interest_paid": round(total_interest, 0),
                "total_rent_paid_30y": round(total_rent_paid, 0),
                "total_maintenance_30y": round(total_maintenance_paid, 0),
                "terminal_buy_net_worth": round(float(buy_net_worth[-1]), 0),
                "terminal_rent_net_worth": round(float(rent_portfolio[-1]), 0),
                "wealth_delta_10y": round(float(wealth_delta[min(119, self.total_months - 1)]), 0),
                "wealth_delta_20y": round(float(wealth_delta[min(239, self.total_months - 1)]), 0),
                "wealth_delta_30y": round(float(wealth_delta[-1]), 0),
                # Új metrikák:
                "total_buy_dead_money": round(total_buy_dead_money, 0),
                "total_rent_dead_money": round(total_rent_dead_money, 0),
                "cagr_equity_pct": round(cagr_equity * 100.0, 2),
                "price_to_rent_ratio": round(price_to_rent, 2),
                "gross_yield_pct": round(gross_yield * 100.0, 2),
                "terminal_real_buy_net_worth": round(float(real_buy_net_worth[-1]), 0),
                "terminal_real_rent_net_worth": round(float(real_rent_net_worth[-1]), 0),
            },
            "trajectories": {
                "month": self.t[sampled_indices].tolist(),
                "year": (self.t[sampled_indices] / 12.0).round(2).tolist(),
                "buy_net_worth": buy_net_worth[sampled_indices].round(0).tolist(),
                "rent_net_worth": rent_portfolio[sampled_indices].round(0).tolist(),
                "btl_net_worth": btl_net_worth[sampled_indices].round(0).tolist(),
                "wealth_delta": wealth_delta[sampled_indices].round(0).tolist(),
                "property_market_value": property_value_traj[sampled_indices].round(0).tolist(),
                "remaining_loan_balance": loan_balance[sampled_indices].round(0).tolist(),
                "monthly_buy_outflow": monthly_buy_outflow[sampled_indices].round(0).tolist(),
                "monthly_rent_outflow": monthly_rent_outflow[sampled_indices].round(0).tolist(),
                "dcf_buy": dcf_buy[sampled_indices].round(0).tolist(),
                "dcf_rent": dcf_rent[sampled_indices].round(0).tolist(),
                # Új pályák:
                "ltv": ltv_traj[sampled_indices].round(4).tolist(),
                "real_buy_net_worth": real_buy_net_worth[sampled_indices].round(0).tolist(),
                "real_rent_net_worth": real_rent_net_worth[sampled_indices].round(0).tolist(),
            }
        }

    def compute_sensitivity_matrix(
        self,
        etf_return_range: Optional[List[float]] = None,
        property_growth_range: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Kétváltozós érzékenységi mátrixot generál az ETF hozam és az ingatlanáremelkedés rácsán.
        Eredménye a 30. év végi Nettó Vagyon Különbség (Saját Lakás - Bérlés).
        Ha pozitív, a saját lakás nyert. Ha negatív, a bérlés nyert.
        """
        if etf_return_range is None:
            etf_return_range = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12]
        if property_growth_range is None:
            property_growth_range = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]

        matrix = []
        base_params = dict(self.params)

        for growth in property_growth_range:
            row = []
            for etf in etf_return_range:
                sim_params = dict(base_params)
                sim_params["opportunity_cost_rate_annual"] = etf
                sim_params["property_growth_rate_annual"] = growth
                
                sub_engine = QuantitativeSimulationEngine(sim_params)
                res = sub_engine.execute()
                diff = res["summary"]["terminal_buy_net_worth"] - res["summary"]["terminal_rent_net_worth"]
                row.append(diff)
            matrix.append(row)

        return {
            "etf_rates_pct": [round(e * 100.0, 2) for e in etf_return_range],
            "property_growth_rates_pct": [round(g * 100.0, 2) for g in property_growth_range],
            "wealth_difference_matrix": matrix
        }
