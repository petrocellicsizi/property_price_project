"""
Pénzügyi és numerikus formázó segédfüggvények.
A magyar pénzügyi sztenderdeknek megfelelően pontozott ezres elválasztást alkalmaz (pl. 80.600.000 Ft).
"""
import re
from typing import Union, Any


def parse_clean_number(val: Any) -> float:
    """
    Kitisztítja a szöveges vagy numerikus bemenetet és lebegőpontos számot ad vissza.
    Kiszűri a pontokat, szóközöket, 'Ft' és egyéb nem numerikus karaktereket.
    """
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    # Szöveges tisztítás: csak számjegyek és tizedesvessző/pont
    val_str = str(val).strip().replace(" ", "").replace("Ft", "").replace("ft", "")
    # Ha van benne vessző tizedesként, de pont ezresként: pl. 1.250,50 vagy 1250.50
    if "," in val_str and "." in val_str:
        # feltételezzük a pont az ezres elválasztó, vessző a tizedes
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
    elif "." in val_str:
        # Ha a pont után 3 számjegy van és nincs több tizedes, lehet ezres elválasztó
        # pl. "80.600.000"
        parts = val_str.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) >= 1):
            val_str = val_str.replace(".", "")

    # Nem numerikus karakterek eltávolítása (kivéve pont és mínusz)
    clean_digits = re.sub(r"[^\d.-]", "", val_str)
    try:
        return float(clean_digits) if clean_digits else 0.0
    except ValueError:
        return 0.0


def format_with_dots(val: Union[int, float, str, None]) -> str:
    """
    Pontozott ezres tagolású formátumra alakítja az egész számot (pl. 80600000 -> '80.600.000').
    """
    if val is None or val == "":
        return ""
    num = round(parse_clean_number(val))
    sign = "-" if num < 0 else ""
    abs_num = abs(num)
    s = str(abs_num)
    # Hátulról 3-as csoportosítás
    reversed_s = s[::-1]
    grouped = ".".join(reversed_s[i:i+3] for i in range(0, len(reversed_s), 3))
    return sign + grouped[::-1]


def format_huf(val: Union[int, float, str, None]) -> str:
    """
    Pontozott formátum Ft utótaggal (pl. 80600000 -> '80.600.000 Ft').
    """
    if val is None or val == "":
        return "0 Ft"
    formatted = format_with_dots(val)
    return f"{formatted} Ft" if formatted else "0 Ft"
