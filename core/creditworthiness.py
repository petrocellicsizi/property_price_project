"""
MNB Hitelképességi & Jövedelemarányos Törlesztőrészlet (JTM) Számítási Modul.
Megfelel a 32/2014. (IX. 10.) MNB rendeletnek és a 2024. január 1-től hatályos
10%-os első lakásvásárlói önerő (HFM) szabályozásnak.
"""
import math
from typing import Dict, Any, List, Optional
from utils.formatters import format_huf


def calculate_jtm_limit(net_income: float, interest_period_years: float) -> float:
    """
    Meghatározza a jogszabályi maximális JTM plafont (%) az MNB rendelet szerint.
    - 600.000 Ft nettó jövedelemhatár
    - Kamatperiódus hossza (5 évnél rövidebb, 5-10 év közötti, vagy legalább 10 év / fix)
    """
    is_high_income = net_income >= 600_000.0

    if interest_period_years >= 10.0:
        # Végig fix vagy min. 10 éves kamatperiódus
        return 60.0 if is_high_income else 50.0
    elif interest_period_years >= 5.0:
        # 5 és 10 év közötti kamatperiódus
        return 40.0 if is_high_income else 35.0
    else:
        # 5 évnél rövidebb / változó kamatozás
        return 30.0 if is_high_income else 25.0


def calculate_creditworthiness(
    net_monthly_income_huf: float,
    loan_principal_huf: float,
    annual_interest_rate_pct: float,
    loan_term_years: int = 20,
    interest_period_years: float = 10.0,
    existing_monthly_loans_huf: float = 0.0,
    credit_card_limits_huf: float = 0.0,
    property_price_huf: float = 0.0,
    is_first_home_buyer: bool = False,
    is_green_certified: bool = False,
) -> Dict[str, Any]:
    """
    Részletes hitelbírálati és JTM vizsgálatot végez az MNB szabályok szerint.
    """
    income = max(1.0, float(net_monthly_income_huf or 0.0))
    principal = max(0.0, float(loan_principal_huf or 0.0))
    rate_annual = max(0.0, float(annual_interest_rate_pct or 0.0))
    term_years = max(1, int(loan_term_years or 20))
    int_period = float(interest_period_years or 10.0)
    existing_loans = max(0.0, float(existing_monthly_loans_huf or 0.0))
    cc_limits = max(0.0, float(credit_card_limits_huf or 0.0))
    prop_price = max(0.0, float(property_price_huf or 0.0))

    # Zöld hitel esetén 0.5% kamatkedvezmény
    effective_rate = max(0.0, rate_annual - (0.5 if is_green_certified else 0.0))

    # 1. Havi hiteltörlesztő kiszámítása (Francia annuitás)
    total_months = term_years * 12
    monthly_rate = (effective_rate / 100.0) / 12.0
    if principal <= 0:
        new_monthly_pmt = 0.0
    elif monthly_rate <= 0:
        new_monthly_pmt = principal / total_months
    else:
        factor = math.pow(1.0 + monthly_rate, total_months)
        new_monthly_pmt = principal * (monthly_rate * factor) / (factor - 1.0)

    # 2. Hitelkártya & folyószámlakeret 5%-os havi terhelése az MNB szerint
    cc_monthly_burden = cc_limits * 0.05

    # 3. Teljes havi adósságszolgálat
    total_debt_service = new_monthly_pmt + existing_loans + cc_monthly_burden

    # 4. Kalkulált JTM és jogszabályi plafon
    calculated_jtm_pct = (total_debt_service / income) * 100.0
    mnb_limit_pct = calculate_jtm_limit(income, int_period)

    # 5. Maximális megengedett havi törlesztési kapacitás
    max_allowed_debt_service = income * (mnb_limit_pct / 100.0)
    available_pmt_capacity = max(0.0, max_allowed_debt_service - existing_loans - cc_monthly_burden)

    # 6. Maximálisan felvehető hitelösszeg a jövedelem alapján
    if monthly_rate > 0:
        factor = math.pow(1.0 + monthly_rate, total_months)
        max_loan_amount = available_pmt_capacity * (factor - 1.0) / (monthly_rate * factor)
    else:
        max_loan_amount = available_pmt_capacity * total_months

    # 7. Szükséges minimális nettó jövedelem az adott hitelhez
    # Ha 600k alatt van a jövedelem, az 50%/35%/25% szabály érvényes, ha felette, a 60%/40%/30%
    rate_low = calculate_jtm_limit(500_000.0, int_period) / 100.0
    rate_high = calculate_jtm_limit(700_000.0, int_period) / 100.0

    req_income_at_high = total_debt_service / rate_high
    if req_income_at_high >= 600_000.0:
        min_required_income = req_income_at_high
    else:
        min_required_income = total_debt_service / rate_low

    # 8. Hitelfedezeti arány (HFM / LTV) vizsgálata
    max_allowed_ltv = 90.0 if is_first_home_buyer else 80.0
    current_ltv_pct = (principal / prop_price * 100.0) if prop_price > 0 else 0.0
    is_ltv_compliant = current_ltv_pct <= max_allowed_ltv if prop_price > 0 else True
    is_jtm_compliant = calculated_jtm_pct <= mnb_limit_pct

    # 9. Szabad jövedelem a törlesztés után
    disposable_income = income - total_debt_service

    # 10. Banki Minősítés / Döntési kategória
    if not is_jtm_compliant:
        status_code = "rejected_jtm"
        verdict = "ELUTASÍTVA (MNB JTM Limit Túllépés)"
        verdict_badge = "bg-danger text-white"
        verdict_icon = "bi-x-octagon-fill"
        summary_text = (
            f"A számított havi adósságszolgálat ({format_huf(total_debt_service)}) "
            f"meghaladja az MNB által előírt maximális {mnb_limit_pct:.0f}%-os jövedelemterhelhetőségi plafont. "
            f"A jelenlegi {format_huf(income)} nettó jövedelemmel ez a hitelösszeg jogszabályilag nem hitelezhető."
        )
    elif not is_ltv_compliant:
        status_code = "rejected_ltv"
        verdict = "ELUTASÍTVA (Nem elegendő önerő / HFM túllépés)"
        verdict_badge = "bg-danger text-white"
        verdict_icon = "bi-x-octagon-fill"
        min_down_pct = 10.0 if is_first_home_buyer else 20.0
        summary_text = (
            f"A kért hitelösszeg ({format_huf(principal)}) eléri az ingatlan {current_ltv_pct:.1f}%-át, "
            f"amely meghaladja a megengedett maximális {max_allowed_ltv:.0f}%-os HFM korlátot. "
            f"Legalább {min_down_pct:.0f}% önerő ({format_huf(prop_price * min_down_pct / 100.0)}) igazolása szükséges."
        )
    elif calculated_jtm_pct > (mnb_limit_pct - 7.0):
        status_code = "warning"
        verdict = "HATÁRESET (Magas Kockázat / Kifeszített Büdzsé)"
        verdict_badge = "bg-warning text-dark"
        verdict_icon = "bi-exclamation-triangle-fill"
        summary_text = (
            f"A hitel jogilag megfelel az MNB rendeletnek ({calculated_jtm_pct:.1f}% / {mnb_limit_pct:.0f}%), "
            f"azonban a háztartás jövedelmének jelentős részét felemészti a havi törlesztés. "
            f"A bankok szigorított bírálat esetén adóstárs bevonását kérhetik."
        )
    else:
        status_code = "approved"
        verdict = "HITELKÉPES (Biztonságos Zóna)"
        verdict_badge = "bg-success text-white"
        verdict_icon = "bi-check-circle-fill"
        summary_text = (
            f"Kiváló hitelbírálati mutatók! A havi törlesztőrészlet ({format_huf(new_monthly_pmt)}) "
            f"kényelmesen belefér a jogszabályi keretekbe ({calculated_jtm_pct:.1f}% a megengedett {mnb_limit_pct:.0f}%-hoz képest), "
            f"és a törlesztés után még {format_huf(disposable_income)} szabad jövedelem marad havonta."
        )

    # 11. Banki tanácsok és optimalizációs javaslatok
    recommendations: List[str] = []
    if cc_limits > 0:
        recommendations.append(
            f"Meglévő hitelkártyák / folyószámlakeretek: A {format_huf(cc_limits)} keret automatikusan {format_huf(cc_monthly_burden)} "
            "havi törlesztésnek számít. Ezen keretek lezárásával azonnal növelhető a felvehető hitelösszeg!"
        )
    if not is_jtm_compliant:
        diff_pmt = total_debt_service - max_allowed_debt_service
        recommendations.append(
            f"A hitelképesség eléréséhez a havi törlesztőt legalább {format_huf(diff_pmt)}-al kell csökkenteni "
            f"(pl. a futamidő kitolásával, önrész növelésével), vagy adóstársat kell bevonni a jövedelem emeléséhez."
        )
    if not is_first_home_buyer and prop_price > 0 and current_ltv_pct > 80.0:
        recommendations.append(
            "Amennyiben 35 év alatti első lakásvásárló vagy, a jogszabály 10% minimális önerőt enged meg (90% HFM), "
            "amely azonnal jóváhagyhatóvá teheti az igénylést!"
        )
    if is_green_certified:
        recommendations.append(
            "Zöld hitel kedvezmény: A fenntartható energetika (AA+) miatt ~0.5% kamatkedvezmény került alkalmazásra."
        )
    if int_period < 10.0:
        recommendations.append(
            f"A választott rövidebb kamatperiódus miatt az MNB JTM plafon szigorúbb ({mnb_limit_pct:.0f}%). "
            "10 éves vagy végig fix kamatperiódussal a megengedett terhelhetőség magasabb lenne!"
        )

    # 12. Grafikon A adatok: Havi Jövedelem Felosztás (Doughnut)
    chart_distribution = {
        "labels": [
            "Tervezett lakáshitel törlesztő",
            "Meglévő hitelek & hitelkeretek",
            "További szabad hitelkapacitás",
            "Szabad megélhetési jövedelem"
        ],
        "values": [
            round(new_monthly_pmt, 0),
            round(existing_loans + cc_monthly_burden, 0),
            round(max(0.0, max_allowed_debt_service - total_debt_service), 0),
            round(max(0.0, income - max_allowed_debt_service), 0)
        ]
    }

    # 13. Grafikon B adatok: Jövedelemérzékenységi Görbe (Max hitelösszeg jövedelem szerint)
    income_steps = [400_000, 600_000, 800_000, 1_000_000, 1_200_000, 1_500_000, 2_000_000]
    max_loans_fix = []
    max_loans_var = []

    for inc in income_steps:
        # Fix (10+ év)
        lim_fix = calculate_jtm_limit(inc, 10.0) / 100.0
        cap_fix = max(0.0, inc * lim_fix - existing_loans - cc_monthly_burden)
        if monthly_rate > 0:
            factor = math.pow(1.0 + monthly_rate, total_months)
            amt_fix = cap_fix * (factor - 1.0) / (monthly_rate * factor)
        else:
            amt_fix = cap_fix * total_months
        max_loans_fix.append(round(amt_fix, 0))

        # Változó / Rövid (3 év)
        lim_var = calculate_jtm_limit(inc, 3.0) / 100.0
        cap_var = max(0.0, inc * lim_var - existing_loans - cc_monthly_burden)
        if monthly_rate > 0:
            amt_var = cap_var * (factor - 1.0) / (monthly_rate * factor)
        else:
            amt_var = cap_var * total_months
        max_loans_var.append(round(amt_var, 0))

    chart_income_sensitivity = {
        "income_levels": income_steps,
        "income_labels": [format_huf(inc) for inc in income_steps],
        "max_loans_fix": max_loans_fix,
        "max_loans_var": max_loans_var
    }

    return {
        "status_code": status_code,
        "verdict": verdict,
        "verdict_badge": verdict_badge,
        "verdict_icon": verdict_icon,
        "summary_text": summary_text,
        "recommendations": recommendations,
        "metrics": {
            "net_monthly_income_huf": round(income, 0),
            "formatted_net_monthly_income": format_huf(income),
            "new_monthly_payment_huf": round(new_monthly_pmt, 0),
            "formatted_new_monthly_payment": format_huf(new_monthly_pmt),
            "existing_debt_service_huf": round(existing_loans + cc_monthly_burden, 0),
            "formatted_existing_debt_service": format_huf(existing_loans + cc_monthly_burden),
            "total_monthly_debt_service_huf": round(total_debt_service, 0),
            "formatted_total_monthly_debt_service": format_huf(total_debt_service),
            "calculated_jtm_pct": round(calculated_jtm_pct, 1),
            "mnb_limit_pct": round(mnb_limit_pct, 1),
            "is_jtm_compliant": is_jtm_compliant,
            "disposable_income_huf": round(disposable_income, 0),
            "formatted_disposable_income": format_huf(disposable_income),
            "max_loan_amount_huf": round(max_loan_amount, 0),
            "formatted_max_loan_amount": format_huf(max_loan_amount),
            "min_required_income_huf": round(min_required_income, 0),
            "formatted_min_required_income": format_huf(min_required_income),
            "current_ltv_pct": round(current_ltv_pct, 1),
            "max_allowed_ltv_pct": round(max_allowed_ltv, 1),
            "is_ltv_compliant": is_ltv_compliant,
            "effective_interest_rate_pct": round(effective_rate, 2),
        },
        "charts": {
            "distribution": chart_distribution,
            "income_sensitivity": chart_income_sensitivity
        }
    }
