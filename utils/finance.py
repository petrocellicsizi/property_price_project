"""
Kvantitatív pénzügyi és hitelszámítási modul (Python).
Tartalmazza az annuitásos törlesztőrészletet, az induló saját tőkeigényt,
az implikált havi hozamrátát, valamint a kétirányú szinkronizációs számításokat.
"""
import math
from typing import Dict, Any, Optional


def calculate_monthly_installment(
    principal: float,
    annual_interest_pct: float,
    term_years: int
) -> int:
    """
    Kiszámítja a havi annuitásos hiteltörlesztőt a standard pénzügyi képlet alapján:
    PMT = P * [ r*(1+r)^n ] / [ (1+r)^n - 1 ]
    ahol:
      P = tőkeösszeg (principal)
      r = havi kamatláb (éves kamat / 12 / 100)
      n = futamidő hónapokban (évek száma * 12)
    """
    principal = float(principal or 0.0)
    annual_pct = float(annual_interest_pct or 0.0)
    term_years = int(term_years or 20)

    if principal <= 0 or term_years <= 0:
        return 0

    total_months = term_years * 12
    monthly_rate = (annual_pct / 100.0) / 12.0

    if monthly_rate <= 0:
        return int(round(principal / total_months))

    try:
        factor = math.pow(1.0 + monthly_rate, total_months)
        pmt = principal * (monthly_rate * factor) / (factor - 1.0)
        return int(round(pmt))
    except (OverflowError, ZeroDivisionError):
        return int(round(principal / total_months))


def calculate_total_initial_outlay(
    down_payment_huf: float,
    lawyer_fee_huf: float,
    other_fees_huf: float,
    furnishing_cost_huf: float,
    price_total_huf: float,
    transfer_tax_rate: float = 0.04
) -> int:
    """
    Kiszámítja az összes induló saját tőkeszükségletet a vásárlás pillanatában:
    Összes induló = Önerő + Ügyvédi munkadíj + Egyéb hiteldíjak + Bútorozás/berendezés + 4% Vagyonszerzési illeték
    """
    down = float(down_payment_huf or 0.0)
    lawyer = float(lawyer_fee_huf or 0.0)
    other = float(other_fees_huf or 0.0)
    furnish = float(furnishing_cost_huf or 0.0)
    price = float(price_total_huf or 0.0)
    tax = price * float(transfer_tax_rate)

    return int(round(down + lawyer + other + furnish + tax))


def calculate_monthly_return_rate(annual_return_pct: float) -> float:
    """
    Kiszámítja a kamatos kamatozású effektív havi hozamrátát az éves elvárt hozamból:
    r_havi = (1 + r_éves)^(1/12) - 1
    Visszatérési érték: százalékban (pl. 0.57) 2 tizedesjegyre kerekítve.
    """
    annual_rate = float(annual_return_pct or 0.0) / 100.0
    if annual_rate <= -1.0:
        return 0.0
    try:
        monthly_rate = math.pow(1.0 + annual_rate, 1.0 / 12.0) - 1.0
        return round(monthly_rate * 100.0, 2)
    except (ValueError, OverflowError):
        return 0.0


def calculate_property_metrics(
    size_sqm: float,
    price_total_huf: Optional[float] = None,
    price_per_sqm_huf: Optional[float] = None
) -> Dict[str, Any]:
    """
    Kétirányú szinkronizáció az alapterület, vételár és m² ár között.
    """
    size = max(1.0, float(size_sqm or 1.0))
    if price_total_huf is not None and price_total_huf > 0:
        total = float(price_total_huf)
        sqm_price = round(total / size)
        return {
            "size_sqm": size,
            "price_total_huf": int(round(total)),
            "price_per_sqm_huf": int(sqm_price)
        }
    elif price_per_sqm_huf is not None and price_per_sqm_huf > 0:
        sqm_price = float(price_per_sqm_huf)
        total = round(size * sqm_price)
        return {
            "size_sqm": size,
            "price_total_huf": int(total),
            "price_per_sqm_huf": int(round(sqm_price))
        }
    return {
        "size_sqm": size,
        "price_total_huf": 0,
        "price_per_sqm_huf": 0
    }


def calculate_lawyer_fee_metrics(
    price_total_huf: float,
    lawyer_pct: Optional[float] = None,
    lawyer_huf: Optional[float] = None
) -> Dict[str, Any]:
    """
    Kétirányú szinkronizáció az ügyvédi munkadíj százaléka és forint összege között.
    """
    total = max(1.0, float(price_total_huf or 1.0))
    if lawyer_pct is not None:
        pct = float(lawyer_pct)
        huf = int(round(total * (pct / 100.0)))
        return {"lawyer_fee_pct": round(pct, 2), "lawyer_fee_huf": huf}
    elif lawyer_huf is not None:
        huf = float(lawyer_huf)
        pct = round((huf / total) * 100.0, 2)
        return {"lawyer_fee_pct": pct, "lawyer_fee_huf": int(round(huf))}
    return {"lawyer_fee_pct": 1.0, "lawyer_fee_huf": int(round(total * 0.01))}


def calculate_down_payment_metrics(
    price_total_huf: float,
    down_payment_pct: Optional[float] = None,
    down_payment_huf: Optional[float] = None
) -> Dict[str, Any]:
    """
    Kétirányú szinkronizáció az önerő százalék, forint összeg és hitelösszeg között.
    """
    total = max(0.0, float(price_total_huf or 0.0))
    if down_payment_pct is not None:
        pct = min(100.0, max(0.0, float(down_payment_pct)))
        down_huf = int(round(total * (pct / 100.0)))
        loan_huf = max(0, int(round(total - down_huf)))
        return {
            "down_payment_pct": round(pct, 1),
            "down_payment_huf": down_huf,
            "loan_amount_huf": loan_huf
        }
    elif down_payment_huf is not None:
        down_huf = min(total, max(0.0, float(down_payment_huf)))
        pct = (down_huf / total * 100.0) if total > 0 else 0.0
        loan_huf = max(0, int(round(total - down_huf)))
        return {
            "down_payment_pct": round(pct, 1),
            "down_payment_huf": int(round(down_huf)),
            "loan_amount_huf": loan_huf
        }
    return {
        "down_payment_pct": 25.0,
        "down_payment_huf": int(round(total * 0.25)),
        "loan_amount_huf": int(round(total * 0.75))
    }
