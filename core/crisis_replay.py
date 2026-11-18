"""
Történelmi Válság Stresszteszt Motor (Historical Crisis Replay).
Modellezi a modern gazdaságtörténet 3 legnagyobb piaci sokkját:
1. 2008 Lehman-krízis & Globális Pénzügyi Összeomlás (10 év)
2. 2020 Covid-19 Karantén & Albérletpiaci Sokk (5 év)
3. 2022-2023 Stagflációs & Kamat / Energiakrízis (5 év)
"""
import math
from typing import Dict, Any, List, Optional
from utils.formatters import format_huf


CRISIS_DEFINITIONS = {
    "crisis_2008": {
        "id": "crisis_2008",
        "name": "2008 Lehman-krízis & Ingatlanbuborék",
        "period": "2008 - 2018 (10 év)",
        "duration_years": 10,
        "badge": "bg-danger text-white",
        "description": "Likviditási összeomlás, hitelpiaci lefagyás, lakásáresés és forintgyengülés.",
        # Éves sokk faktorok: [ingatlanár_változás, bérletidíj_változás, részvény_hozam, infláció, kamatsokk_bázispont]
        "timeline_shocks": [
            {"year": 1, "prop": -0.08, "rent": -0.05, "market": -0.38, "cpi": 0.061, "rate_jump": 3.5},
            {"year": 2, "prop": -0.07, "rent": -0.03, "market": 0.26,  "cpi": 0.042, "rate_jump": 2.0},
            {"year": 3, "prop": -0.02, "rent": 0.00,  "market": 0.15,  "cpi": 0.049, "rate_jump": 1.0},
            {"year": 4, "prop": 0.00,  "rent": 0.02,  "market": 0.02,  "cpi": 0.039, "rate_jump": 0.5},
            {"year": 5, "prop": 0.02,  "rent": 0.03,  "market": 0.16,  "cpi": 0.057, "rate_jump": 0.0},
            {"year": 6, "prop": 0.06,  "rent": 0.05,  "market": 0.32,  "cpi": 0.017, "rate_jump": -0.5},
            {"year": 7, "prop": 0.12,  "rent": 0.08,  "market": 0.13,  "cpi": -0.002, "rate_jump": -1.0},
            {"year": 8, "prop": 0.15,  "rent": 0.10,  "market": 0.01,  "cpi": 0.004, "rate_jump": -1.5},
            {"year": 9, "prop": 0.14,  "rent": 0.09,  "market": 0.12,  "cpi": 0.024, "rate_jump": -2.0},
            {"year": 10, "prop": 0.16, "rent": 0.11,  "market": -0.04, "cpi": 0.028, "rate_jump": -2.0},
        ],
        "economic_takeaway": (
            "A 2008-as krízis fő tanulsága: a tőkeáttétel negatív ársokk esetén felerősíti a tőkeveszteséget. "
            "A változó kamatozású hitellel rendelkezők havi terhei ugrásszerűen megnőttek, míg a tőkepiac "
            "az óriási kezdeti beszakadás (-38%) után a válság második felében agresszív reálhozammal kompenzált."
        )
    },
    "crisis_2020": {
        "id": "crisis_2020",
        "name": "2020 Covid-19 Karantén & Albérletpiaci Sokk",
        "period": "2020 - 2025 (5 év)",
        "duration_years": 5,
        "badge": "bg-warning text-dark",
        "description": "Lezárások, turizmus és Airbnb leállás, drasztikus belvárosi albérletáresés, V-alakú tőkepiaci felpattanás.",
        "timeline_shocks": [
            {"year": 1, "prop": -0.02, "rent": -0.18, "market": 0.18, "cpi": 0.033, "rate_jump": -0.5},
            {"year": 2, "prop": 0.12,  "rent": 0.06,  "market": 0.28, "cpi": 0.051, "rate_jump": 0.5},
            {"year": 3, "prop": 0.18,  "rent": 0.15,  "market": -0.18, "cpi": 0.145, "rate_jump": 4.0},
            {"year": 4, "prop": 0.03,  "rent": 0.12,  "market": 0.26, "cpi": 0.176, "rate_jump": 3.0},
            {"year": 5, "prop": 0.08,  "rent": 0.10,  "market": 0.24, "cpi": 0.037, "rate_jump": 0.0},
        ],
        "economic_takeaway": (
            "A Covid-válság sajátossága az albérletpiac azonnali -18%-os zuhanása volt az Airbnb leállása és a "
            "digitális oktatás miatt. Ez a bérlőknek rendkívüli készpénzmegtakarítást jelentett, amit a gyorsan "
            "felpattanó tőzsdén kamatoztathattak, miközben a lakástulajdonosok bérbeadási hozama megfeleződött."
        )
    },
    "crisis_2022": {
        "id": "crisis_2022",
        "name": "2022-2023 Stagflációs & Kamat / Energia Sokk",
        "period": "2022 - 2027 (5 év)",
        "duration_years": 5,
        "badge": "bg-primary text-white",
        "description": "25%-os inflációs csúcs, rezsi- és energiadrágulás, lakáspiaci volumenbefagyás, 16-18%-os állampapír-csúcsok.",
        "timeline_shocks": [
            {"year": 1, "prop": 0.04,  "rent": 0.14,  "market": 0.15, "cpi": 0.145, "rate_jump": 6.0, "utility_jump": 0.40},
            {"year": 2, "prop": 0.01,  "rent": 0.12,  "market": 0.18, "cpi": 0.176, "rate_jump": 5.0, "utility_jump": 0.35},
            {"year": 3, "prop": 0.06,  "rent": 0.09,  "market": 0.12, "cpi": 0.037, "rate_jump": 2.0, "utility_jump": 0.10},
            {"year": 4, "prop": 0.08,  "rent": 0.08,  "market": 0.10, "cpi": 0.035, "rate_jump": 0.0, "utility_jump": 0.05},
            {"year": 5, "prop": 0.09,  "rent": 0.07,  "market": 0.09, "cpi": 0.032, "rate_jump": -1.0, "utility_jump": 0.0},
        ],
        "economic_takeaway": (
            "A stagflációs sokk során a nominálisan enyhén emelkedő ingatlanárak reálértékben több mint 20%-ot vesztettek. "
            "Ugyanakkor az inflációkövető állampapírok (PMÁP 16-18%) rendkívüli védelmet nyújtottak a bérlői megtakarításoknak, "
            "miközben a magas hitelkamatok elriasztották az új vevőket és megdrágították a lakásfinanszírozást."
        )
    }
}


def run_crisis_replay(
    crisis_id: str,
    property_val_0: float,
    down_payment_ratio: float,
    loan_annual_rate: float,
    loan_term_years: int,
    initial_rent_monthly: float,
    common_cost_monthly: float = 25_000.0,
    renovation_initial: float = 2_500_000.0,
    is_loan_fixed: bool = True
) -> Dict[str, Any]:
    """
    Végrehajtja a kiválasztott történelmi válság stressztesztet a felhasználó konkrét ingatlan és bérleti paramétereire.
    """
    crisis = CRISIS_DEFINITIONS.get(crisis_id, CRISIS_DEFINITIONS["crisis_2008"])
    shocks = crisis["timeline_shocks"]
    n_years = len(shocks)

    prop_price = max(1_000_000.0, float(property_val_0 or 80_000_000.0))
    down_ratio = max(0.05, min(1.0, float(down_payment_ratio or 0.20)))
    down_payment = prop_price * down_ratio
    loan_0 = max(0.0, prop_price - down_payment)

    # Induló illeték + ügyvéd (5%) + berendezés
    upfront_fees = (prop_price * 0.05) + float(renovation_initial or 0.0)
    initial_equity = down_payment + upfront_fees

    # Hitel annuitás számítás
    term_months = int(loan_term_years or 20) * 12
    base_rate_m = (float(loan_annual_rate or 0.065)) / 12.0
    if loan_0 > 0 and base_rate_m > 0:
        base_pmt = loan_0 * (base_rate_m * (1.0 + base_rate_m)**term_months) / ((1.0 + base_rate_m)**term_months - 1.0)
    else:
        base_pmt = loan_0 / term_months if term_months > 0 else 0.0

    # Idősorok inicializálása
    timeline = [0]
    crisis_buy_wealth = [initial_equity - upfront_fees]  # Day 0: Ingatlan piaci érték - hitel = önerő
    crisis_rent_wealth = [initial_equity]                # Bérlő kezdeti tőkéje = önrész + induló díjak

    baseline_buy_wealth = [initial_equity - upfront_fees]
    baseline_rent_wealth = [initial_equity]

    # Változók nyomon követése
    current_prop_val = prop_price
    current_baseline_prop_val = prop_price
    current_loan_bal = loan_0
    current_baseline_loan_bal = loan_0
    
    current_rent_val = initial_rent_monthly
    current_baseline_rent_val = initial_rent_monthly

    cur_rent_wealth = initial_equity
    cur_baseline_rent_wealth = initial_equity

    cum_cpi = 1.0
    max_buy_wealth = initial_equity - upfront_fees
    max_rent_wealth = initial_equity
    max_buy_drawdown_pct = 0.0
    max_rent_drawdown_pct = 0.0

    cashflow_shock_diff_sum = 0.0

    for idx, shock in enumerate(shocks):
        yr = shock["year"]
        timeline.append(yr)

        prop_growth = shock["prop"]
        rent_growth = shock["rent"]
        market_ret = shock["market"]
        cpi = shock["cpi"]
        rate_jump_bp = shock.get("rate_jump", 0.0)
        util_jump = shock.get("utility_jump", 0.0)

        cum_cpi *= (1.0 + cpi)

        # 1. Ingatlan értékének alakulása
        current_prop_val *= (1.0 + prop_growth)
        current_baseline_prop_val *= 1.055  # Alappályán évi 5.5% növekedés

        # 2. Hitel törlesztése ebben az évben
        # Ha a hitel NEM fix, akkor a kamatsokk megemeli a törlesztőt!
        cur_rate_annual = float(loan_annual_rate) + (0.0 if is_loan_fixed else (rate_jump_bp / 100.0))
        cur_rate_m = max(0.01, cur_rate_annual) / 12.0
        rem_months = max(1, term_months - (idx * 12))
        
        if current_loan_bal > 0:
            if cur_rate_m > 0:
                cur_annual_pmt = current_loan_bal * (cur_rate_m * (1.0 + cur_rate_m)**rem_months) / ((1.0 + cur_rate_m)**rem_months - 1.0) * 12.0
            else:
                cur_annual_pmt = current_loan_bal / rem_months * 12.0
            
            # Tőketörlesztés becslése
            approx_interest = current_loan_bal * cur_rate_annual
            approx_principal = max(0.0, cur_annual_pmt - approx_interest)
            current_loan_bal = max(0.0, current_loan_bal - approx_principal)
        else:
            cur_annual_pmt = 0.0

        # Baseline hiteltörlesztés
        if current_baseline_loan_bal > 0:
            base_annual_pmt = base_pmt * 12.0
            b_interest = current_baseline_loan_bal * float(loan_annual_rate)
            b_principal = max(0.0, base_annual_pmt - b_interest)
            current_baseline_loan_bal = max(0.0, current_baseline_loan_bal - b_principal)
        else:
            base_annual_pmt = 0.0

        # Saját lakás nettó vagyona (ingatlan - hitel - 1.5% eladási díj)
        net_buy = (current_prop_val * 0.985) - current_loan_bal
        net_baseline_buy = (current_baseline_prop_val * 0.985) - current_baseline_loan_bal

        crisis_buy_wealth.append(round(net_buy, 0))
        baseline_buy_wealth.append(round(net_baseline_buy, 0))

        # 3. Bérlői portfólió alakulása
        current_rent_val *= (1.0 + rent_growth)
        current_baseline_rent_val *= 1.045  # Alappályán évi 4.5% bérletidíj-infláció

        annual_rent_paid = current_rent_val * 12.0
        annual_maintenance = current_prop_val * 0.01

        # Havi büdzsé különbség megtakarítása
        buy_outflow = cur_annual_pmt + annual_maintenance + (common_cost_monthly * 12.0 * (1.0 + util_jump))
        rent_outflow = annual_rent_paid + (common_cost_monthly * 12.0)
        
        diff_savings = max(0.0, buy_outflow - rent_outflow)
        cashflow_shock_diff_sum += (buy_outflow - (base_pmt * 12.0 + annual_maintenance + common_cost_monthly * 12.0))

        # Bérlő befektetési hozama a válságban vs alappályán (alapon 8%)
        cur_rent_wealth = (cur_rent_wealth * (1.0 + market_ret)) + diff_savings
        cur_baseline_rent_wealth = (cur_baseline_rent_wealth * 1.08) + max(0.0, (base_pmt * 12.0 + prop_price * 0.01) - (current_baseline_rent_val * 12.0))

        crisis_rent_wealth.append(round(cur_rent_wealth, 0))
        baseline_rent_wealth.append(round(cur_baseline_rent_wealth, 0))

        # Drawdown mérés
        if net_buy > max_buy_wealth:
            max_buy_wealth = net_buy
        else:
            dd = (max_buy_wealth - net_buy) / max_buy_wealth * 100.0 if max_buy_wealth > 0 else 0.0
            if dd > max_buy_drawdown_pct:
                max_buy_drawdown_pct = dd

        if cur_rent_wealth > max_rent_wealth:
            max_rent_wealth = cur_rent_wealth
        else:
            dd = (max_rent_wealth - cur_rent_wealth) / max_rent_wealth * 100.0 if max_rent_wealth > 0 else 0.0
            if dd > max_rent_drawdown_pct:
                max_rent_drawdown_pct = dd

    final_buy_wealth = crisis_buy_wealth[-1]
    final_rent_wealth = crisis_rent_wealth[-1]
    wealth_delta = final_buy_wealth - final_rent_wealth

    # Reálvagyon (inflációval deflálva)
    real_buy_wealth = final_buy_wealth / cum_cpi
    real_rent_wealth = final_rent_wealth / cum_cpi

    # Győztes megállapítása
    if wealth_delta >= 0:
        winner = "Saját lakás vásárlása"
        winner_badge = "badge bg-success text-white"
        resilience_verdict = "A lakásvásárlás még a válság közepette is magasabb nettó vagyont eredményezett."
    else:
        winner = "Bérlés & Befektetés"
        winner_badge = "badge bg-danger text-white"
        resilience_verdict = "A bérlés és likvid tőkepiaci allokáció nagyobb ellenállóképességet nyújtott ezen sokk alatt."

    return {
        "crisis_id": crisis_id,
        "name": crisis["name"],
        "period": crisis["period"],
        "badge": crisis["badge"],
        "description": crisis["description"],
        "duration_years": n_years,
        "economic_takeaway": crisis["economic_takeaway"],
        "is_loan_fixed": is_loan_fixed,
        "metrics": {
            "final_buy_wealth": round(final_buy_wealth, 0),
            "formatted_final_buy_wealth": format_huf(final_buy_wealth),
            "final_rent_wealth": round(final_rent_wealth, 0),
            "formatted_final_rent_wealth": format_huf(final_rent_wealth),
            "wealth_delta": round(wealth_delta, 0),
            "formatted_wealth_delta": format_huf(wealth_delta),
            "max_buy_drawdown_pct": round(max_buy_drawdown_pct, 1),
            "max_rent_drawdown_pct": round(max_rent_drawdown_pct, 1),
            "real_buy_wealth": round(real_buy_wealth, 0),
            "formatted_real_buy_wealth": format_huf(real_buy_wealth),
            "real_rent_wealth": round(real_rent_wealth, 0),
            "formatted_real_rent_wealth": format_huf(real_rent_wealth),
            "cumulative_inflation_pct": round((cum_cpi - 1.0) * 100.0, 1),
            "winner": winner,
            "winner_badge": winner_badge,
            "resilience_verdict": resilience_verdict
        },
        "trajectories": {
            "timeline": timeline,
            "crisis_buy_wealth": crisis_buy_wealth,
            "crisis_rent_wealth": crisis_rent_wealth,
            "baseline_buy_wealth": baseline_buy_wealth,
            "baseline_rent_wealth": baseline_rent_wealth
        }
    }
