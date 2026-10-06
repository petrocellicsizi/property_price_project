"""
Dinamikus ingatlanpiaci és rezsibecslő algoritmusok (Python).
A budapesti és VIII. kerületi historikus és empirikus piaci adatokra támaszkodik:
1. Bebútorozási és berendezési költség becslése (típus, m², szobaszám alapján)
2. Ekvivalens megvásárolandó lakás piaci bérleti díjának becslése
3. Havi becsült rezsiköltség energetika és alapterület alapján
"""
from typing import Optional


def calculate_suggested_furnishing(
    property_type: str,
    size_sqm: float,
    room_count: float
) -> int:
    """
    Kiszámítja az ajánlott berendezési és bútorozási összeget forintban.
    Függ az ingatlan típusától (belmagasság, konyha jellege), méretétől és szobaszámától.
    """
    size_sqm = max(10.0, float(size_sqm or 52.0))
    room_count = max(1.0, float(room_count or 2.0))
    pt = (property_type or "").strip()

    if "Újépítésű" in pt or "AA+" in pt:
        base_kitchen = 1350000  # modern beépített konyhabútor és gépek
        room_rate = 550000      # modern nappali / hálóberendezés
        sqm_rate = 12000
    elif "Korszerű tégla" in pt:
        base_kitchen = 1100000
        room_rate = 450000
        sqm_rate = 10000
    elif "Régi nagypolgári" in pt:
        base_kitchen = 1800000  # 3.8m belmagasság, egyedi beépítés, alapfestés
        room_rate = 750000      # nagyobb terek, klasszikus bútorok
        sqm_rate = 18000
    elif "Panel (felújított" in pt or "panelprogramos" in pt:
        base_kitchen = 850000   # szabvány méretezésű konyhabútor
        room_rate = 350000
        sqm_rate = 8000
    elif "Panel (eredeti" in pt:
        base_kitchen = 1400000  # elkerülhetetlen gépészeti és konyhai csere
        room_rate = 450000
        sqm_rate = 14000
    elif "Családi ház" in pt or "Ikerház" in pt:
        base_kitchen = 2100000  # nagyobb konyha, előtér, kerti kiegészítők
        room_rate = 650000
        sqm_rate = 15000
    else:
        base_kitchen = 1200000
        room_rate = 500000
        sqm_rate = 10000

    raw = base_kitchen + (room_count * room_rate) + (size_sqm * sqm_rate)
    # Kerekítés a legközelebbi 50 000 Ft-ra
    return int(round(raw / 50000.0) * 50000)


def calculate_suggested_rent(
    property_type: str,
    size_sqm: float,
    room_count: float,
    city: Optional[str] = "Budapest",
    district: Optional[str] = "VIII. kerület"
) -> int:
    """
    Kiszámítja az adott megvásárolandó ingatlannal megegyező paraméterű lakás
    becsült piaci bérleti díját (Ft/hó).
    Referencia bázis: Budapest VIII. kerület újépítésű (Corvin-negyed).
    """
    size_sqm = max(10.0, float(size_sqm or 52.0))
    room_count = max(1.0, float(room_count or 2.0))
    city_str = (city or "Budapest").strip()
    dist_str = (district or "VIII. kerület").strip().upper()
    pt = (property_type or "").strip()

    # 1. Alap m² fajlagos bérleti díj típus szerint (HUF/m²)
    if "Újépítésű" in pt or "AA+" in pt:
        base_sqm_rent = 5200.0
    elif "Korszerű tégla" in pt:
        base_sqm_rent = 4600.0
    elif "Régi nagypolgári" in pt:
        base_sqm_rent = 4200.0
    elif "Panel (felújított" in pt:
        base_sqm_rent = 3900.0
    elif "Panel (eredeti" in pt:
        base_sqm_rent = 3300.0
    elif "Családi ház" in pt:
        base_sqm_rent = 3400.0
    else:
        base_sqm_rent = 4500.0

    # 2. Méretelaszticitási szorzó (a kisebb garzonok fajlagosan drágábbak)
    if size_sqm <= 38.0:
        size_multiplier = 1.15  # Garzon prémium
    elif size_sqm <= 55.0:
        size_multiplier = 1.00  # Standard 1.5-2 szobás bázis
    elif size_sqm <= 75.0:
        size_multiplier = 0.94  # Közepes lakás diszkont
    else:
        size_multiplier = 0.88  # Nagy alapterület diszkont

    # 3. Szobaszám szorzó (több különnyíló szoba azonos m²-en magasabb bérleti értéket képvisel)
    room_multiplier = 1.00
    if room_count >= 2.0 and size_sqm <= 50.0:
        room_multiplier = 1.05
    elif room_count >= 3.0 and size_sqm <= 70.0:
        room_multiplier = 1.06

    # 4. Lokációs prémium / diszkont
    if city_str.lower() != "budapest":
        loc_multiplier = 0.82  # Vidéki egyetemi nagyvárosok átlaga
    else:
        if any(d in dist_str for d in ["V.", "VI.", "VII."]):
            loc_multiplier = 1.10  # Belső pesti prémium belváros
        elif any(d in dist_str for d in ["VIII.", "IX.", "XI.", "XIII."]):
            loc_multiplier = 1.00  # Egyetemi / Corvin folyosó referencia
        elif any(d in dist_str for d in ["I.", "II.", "XII."]):
            loc_multiplier = 1.12  # Buda prémium
        else:
            loc_multiplier = 0.88  # Külső kerületek

    raw_rent = size_sqm * base_sqm_rent * size_multiplier * room_multiplier * loc_multiplier
    # Kerekítés 5 000 Ft-ra
    return int(round(raw_rent / 5000.0) * 5000)


def calculate_suggested_price_per_sqm(
    property_type: str,
    city: Optional[str] = "Budapest",
    district: Optional[str] = "VIII. kerület",
    condition: Optional[str] = "Jó állapotú"
) -> int:
    """
    Kiszámítja a becsült négyzetméterárat (Ft/m²)
    a település, kerület, ingatlan típus és állapot alapján.
    """
    city_str = (city or "Budapest").strip()
    dist_str = (district or "VIII. kerület").strip().upper()
    pt = (property_type or "").strip()
    cond = (condition or "Jó állapotú").strip()

    # Alapár típus szerint (Budapest átlag / újépítésű bázis)
    if "Újépítésű" in pt or "AA+" in pt:
        base_price = 1550000.0
    elif "Korszerű tégla" in pt:
        base_price = 1250000.0
    elif "Régi nagypolgári" in pt:
        base_price = 980000.0
    elif "Panel (felújított" in pt:
        base_price = 850000.0
    elif "Panel (eredeti" in pt:
        base_price = 720000.0
    elif "Családi ház" in pt:
        base_price = 900000.0
    else:
        base_price = 1100000.0

    # Állapot szorzók
    cond_multiplier = 1.0
    if cond == "Újszerű / Prémium":
        cond_multiplier = 1.15
    elif cond == "Jó állapotú":
        cond_multiplier = 1.00
    elif cond == "Közepes":
        cond_multiplier = 0.85
    elif cond == "Felújítandó":
        cond_multiplier = 0.70

    # Lokációs szorzók (KSH/Ingatlan.com 2024 becslések alapján)
    if city_str.lower() != "budapest":
        if city_str.lower() in ["debrecen", "győr", "szeged", "veszprém"]:
            loc_multiplier = 0.65  # Nagy egyetemi / ipari központok (pl. Debrecen ~ 950-1M Ft)
        elif city_str.lower() in ["pécs", "kecskemét", "székesfehérvár"]:
            loc_multiplier = 0.55
        else:
            loc_multiplier = 0.40  # Egyéb vidék
    else:
        if any(d in dist_str for d in ["V.", "I.", "II.", "XII."]):
            loc_multiplier = 1.35  # Prémium Buda & V. kerület
        elif any(d in dist_str for d in ["VI.", "VII.", "XI.", "XIII."]):
            loc_multiplier = 1.15  # Külső belváros & Újbuda
        elif any(d in dist_str for d in ["VIII.", "IX.", "XIV."]):
            loc_multiplier = 1.00  # Referencia / Átlag pesti
        else:
            loc_multiplier = 0.75  # Külső pesti kerületek

    raw_price = base_price * loc_multiplier * cond_multiplier
    # Kerekítés 10 000 Ft-ra
    return int(round(raw_price / 10000.0) * 10000)


def calculate_suggested_utilities(
    property_type: str,
    size_sqm: float
) -> int:
    """
    Kiszámítja a becsült havi rezsiköltséget (Ft/hó)
    az ingatlan energetikai jellege és alapterülete alapján (fűtés, víz, villany, közös költség).
    """
    size_sqm = max(10.0, float(size_sqm or 52.0))
    pt = (property_type or "").strip()

    if "Újépítésű" in pt or "AA+" in pt:
        rate_per_sqm = 650.0   # Alacsony hőszükséglet, de magasabb közös költség
    elif "Korszerű tégla" in pt:
        rate_per_sqm = 750.0
    elif "Régi nagypolgári" in pt:
        rate_per_sqm = 1050.0  # Magas belmagasság miatti hőveszteség, felújítási alap
    elif "Panel (felújított" in pt:
        rate_per_sqm = 800.0   # Egyedi méréses távhő
    elif "Panel (eredeti" in pt:
        rate_per_sqm = 950.0   # Általánydíjas távhő
    elif "Családi ház" in pt:
        rate_per_sqm = 700.0
    else:
        rate_per_sqm = 750.0

    raw = size_sqm * rate_per_sqm
    # Minimum 15 000 Ft, kerekítve 1 000 Ft-ra
    return int(max(15000, round(raw / 1000.0) * 1000))


def calculate_ai_adjusted_suggestions(
    base_suggestions: dict,
    ai_evaluations: dict
) -> dict:
    """
    Összehangolja a piaci alapalgoritmusok által adott javaslatokat
    a Gemini AI által meghatározott egyedi szempontokkal (pl. Dunamenti felár, kisállat felár, felújítás).
    """
    from utils.formatters import format_huf

    furnish_base = int(base_suggestions.get("suggested_furnishing_huf", 2800000))
    rent_base = int(base_suggestions.get("suggested_rent_huf", 270000))
    utils_base = int(base_suggestions.get("suggested_utilities_huf", 34000))
    market_price_base = int(base_suggestions.get("suggested_price_total_huf", 0))
    market_sqm_base = int(base_suggestions.get("suggested_price_per_sqm_huf", 0))

    prop_eval = ai_evaluations.get("property", {}) if isinstance(ai_evaluations, dict) else {}
    rent_eval = ai_evaluations.get("rent", {}) if isinstance(ai_evaluations, dict) else {}

    furnish_adj = float(prop_eval.get("furnishing_adjustment_huf", 0) or 0)
    market_adj_pct = float(prop_eval.get("market_value_adjustment_pct", 0.0) or 0.0)
    rent_adj_pct = float(rent_eval.get("rent_adjustment_pct", 0.0) or 0.0)
    utils_adj_pct = float(rent_eval.get("utilities_adjustment_pct", 0.0) or 0.0)

    # Korrigált értékek kerekítése a standard piaci osztásokra
    adj_furnish = int(round((furnish_base + furnish_adj) / 50000.0) * 50000)
    adj_rent = int(round((rent_base * (1.0 + rent_adj_pct / 100.0)) / 5000.0) * 5000)
    adj_utils = int(max(15000, round((utils_base * (1.0 + utils_adj_pct / 100.0)) / 1000.0) * 1000))
    
    # Piaci érték korrekciója az AI alapján
    adj_market_total = int(round((market_price_base * (1.0 + market_adj_pct / 100.0)) / 100000.0) * 100000) if market_price_base else 0
    adj_market_sqm = int(round((market_sqm_base * (1.0 + market_adj_pct / 100.0)) / 10000.0) * 10000) if market_sqm_base else 0

    return {
        "suggested_furnishing_huf": adj_furnish,
        "suggested_rent_huf": adj_rent,
        "suggested_utilities_huf": adj_utils,
        "suggested_price_total_huf": adj_market_total,
        "suggested_price_per_sqm_huf": adj_market_sqm,
        "adjustments_applied": {
            "furnishing_adjustment_huf": int(furnish_adj),
            "market_value_adjustment_pct": market_adj_pct,
            "rent_adjustment_pct": rent_adj_pct,
            "utilities_adjustment_pct": utils_adj_pct,
        },
        "formatted": {
            "suggested_furnishing": format_huf(adj_furnish),
            "suggested_rent": format_huf(adj_rent),
            "suggested_utilities": format_huf(adj_utils),
            "suggested_price_total": format_huf(adj_market_total),
            "suggested_price_per_sqm": f"{format_huf(adj_market_sqm)}/m²"
        }
    }

