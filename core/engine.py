"""
Kvantitatív Pénzügyi Szimulációs Motor
Diszkontált Cash-Flow (DCF), Francia annuitás, tőkeáttétel és vagyonegyenleg-alapú modellezés.
"""
from typing import Dict, Any, List, Optional
import numpy as np


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
        # Közös költség inflálódása a bérleti díj növekedési ütemével arányosan
        rent_growth_annual = float(self.params["rent_growth_rate_annual"])
        g_rent_m = (1.0 + rent_growth_annual)**(1.0 / 12.0) - 1.0
        common_cost_traj = common_cost_base * (1.0 + g_rent_m)**self.t
        
        maintenance_traj = property_value_traj * (maint_rate_annual / 12.0)
        
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
        
        # Bérlő kezdeti vagyona = a vásárláshoz szükséges teljes önerő és induló díjak
        r_opp_annual = float(self.params["opportunity_cost_rate_annual"])
        r_opp_m = (1.0 + r_opp_annual)**(1.0 / 12.0) - 1.0
        
        # Havi cash flow különbség: (Vásárló havi kiadása) - (Bérlő havi kiadása)
        # Ha a vásárló többet fizet (jellemzően az első 10-15 évben a törlesztő miatt),
        # a bérlő ezt a többletet havonta befekteti a portfóliójába.
        # Ha a bérleti díj felülmúlja a törlesztőt (vagy a hitel lejárta után), a differencia negatív,
        # tehát a bérlő a portfóliójából fedezi a hiányt.
        cf_diff = monthly_buy_outflow - rent_traj
        
        rent_portfolio = np.zeros(self.total_months)
        wealth_acc = initial_equity_needed
        for m in range(self.total_months):
            wealth_acc = wealth_acc * (1.0 + r_opp_m) + cf_diff[m]
            rent_portfolio[m] = wealth_acc

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
        discount_annual = float(self.params.get("discount_rate_annual", 0.06))
        r_disc_m = (1.0 + discount_annual)**(1.0 / 12.0) - 1.0
        discount_factors = 1.0 / ((1.0 + r_disc_m)**self.t)
        
        # NPV profilok
        dcf_buy = np.cumsum(-monthly_buy_outflow * discount_factors) - initial_equity_needed + (buy_net_worth * discount_factors)
        dcf_rent = np.cumsum(-rent_traj * discount_factors) - 0.0 + (rent_portfolio * discount_factors)

        # Összegző metrikák
        total_interest = float(np.sum(loan_interest_paid))
        total_rent_paid = float(np.sum(rent_traj))
        total_maintenance_paid = float(np.sum(maintenance_traj + common_cost_traj))

        # Éves mintavételezés a grafikonokhoz (hogy a JSON válasz kompakt és gyors maradjon)
        sample_step = 1  # 360 adatpont havi felbontásban teljesen jól kezelhető a kliensen
        sampled_indices = np.arange(0, self.total_months, sample_step)
        
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
            },
            "trajectories": {
                "month": self.t[sampled_indices].tolist(),
                "year": (self.t[sampled_indices] / 12.0).round(2).tolist(),
                "buy_net_worth": buy_net_worth[sampled_indices].round(0).tolist(),
                "rent_net_worth": rent_portfolio[sampled_indices].round(0).tolist(),
                "wealth_delta": wealth_delta[sampled_indices].round(0).tolist(),
                "property_market_value": property_value_traj[sampled_indices].round(0).tolist(),
                "remaining_loan_balance": loan_balance[sampled_indices].round(0).tolist(),
                "monthly_buy_outflow": monthly_buy_outflow[sampled_indices].round(0).tolist(),
                "monthly_rent_outflow": rent_traj[sampled_indices].round(0).tolist(),
                "dcf_buy": dcf_buy[sampled_indices].round(0).tolist(),
                "dcf_rent": dcf_rent[sampled_indices].round(0).tolist()
            }
        }

    def compute_sensitivity_matrix(
        self,
        interest_rate_range: Optional[List[float]] = None,
        property_growth_range: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Kétváltozós érzékenységi mátrixot generál a hitelkamat és az ingatlanáremelkedés rácsán.
        Eredménye egy BEP (években) hőtérkép.
        """
        if interest_rate_range is None:
            interest_rate_range = [0.045, 0.055, 0.065, 0.075, 0.085, 0.095]
        if property_growth_range is None:
            property_growth_range = [0.020, 0.035, 0.050, 0.065, 0.080, 0.095]

        matrix = []
        base_params = dict(self.params)

        for rate in interest_rate_range:
            row = []
            for growth in property_growth_range:
                sim_params = dict(base_params)
                sim_params["loan_interest_rate_annual"] = rate
                sim_params["property_growth_rate_annual"] = growth
                
                sub_engine = QuantitativeSimulationEngine(sim_params)
                res = sub_engine.execute()
                bep_yr = res["summary"]["break_even_year"]
                row.append(bep_yr if bep_yr is not None else 31.0)  # 31 jelöli, ha 30 év alatt sem fordul át
            matrix.append(row)

        return {
            "interest_rates_pct": [round(r * 100.0, 2) for r in interest_rate_range],
            "property_growth_rates_pct": [round(g * 100.0, 2) for g in property_growth_range],
            "bep_years_matrix": matrix
        }
