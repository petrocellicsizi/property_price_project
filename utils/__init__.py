"""
Kvantitatív Pénzügyi és Ingatlanpiaci Segédmodulok (Utils)
"""
from utils.formatters import format_huf, format_with_dots, parse_clean_number
from utils.algorithms import (
    calculate_suggested_furnishing,
    calculate_suggested_rent,
    calculate_suggested_utilities,
    calculate_ai_adjusted_suggestions,
)
from utils.finance import (
    calculate_monthly_installment,
    calculate_total_initial_outlay,
    calculate_monthly_return_rate,
    calculate_property_metrics,
    calculate_lawyer_fee_metrics,
    calculate_down_payment_metrics,
)

__all__ = [
    "format_huf",
    "format_with_dots",
    "parse_clean_number",
    "calculate_suggested_furnishing",
    "calculate_suggested_rent",
    "calculate_suggested_utilities",
    "calculate_ai_adjusted_suggestions",
    "calculate_monthly_installment",
    "calculate_total_initial_outlay",
    "calculate_monthly_return_rate",
    "calculate_property_metrics",
    "calculate_lawyer_fee_metrics",
    "calculate_down_payment_metrics",
]
