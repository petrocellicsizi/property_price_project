import re
import os

filepath = os.path.join('static', 'js', 'app.js')
with open(filepath, 'r', encoding='utf-8') as f:
    js = f.read()

# Keresünk olyan sorokat a populateForm-ban, ahol "??" vagy "||" van.
# Kicsit óvatosan, regex-szel cseréljük a hardcode-olt fallbackeket `?? ''`-re.

js = re.sub(r'data\.property\.price_total_huf \?\? \d+', "data.property.price_total_huf ?? ''", js)
js = re.sub(r'data\.property\.price_per_sqm_huf \?\? \d+', "data.property.price_per_sqm_huf ?? ''", js)
js = re.sub(r'data\.property\.lawyer_fee_pct \?\? [\d\.]+', "data.property.lawyer_fee_pct ?? ''", js)
js = re.sub(r'data\.property\.lawyer_fee_huf \?\? \d+', "data.property.lawyer_fee_huf ?? ''", js)

js = re.sub(r'data\.loan\.down_payment_pct \?\? \d+', "data.loan.down_payment_pct ?? ''", js)
js = re.sub(r'data\.loan\.down_payment_huf \?\? \d+', "data.loan.down_payment_huf ?? ''", js)
js = re.sub(r'data\.loan\.loan_amount_huf \?\? \d+', "data.loan.loan_amount_huf ?? ''", js)
js = re.sub(r'data\.loan\.loan_term_years \?\? \d+', "data.loan.loan_term_years ?? ''", js)
js = re.sub(r'data\.loan\.interest_rate_annual_pct \?\? [\d\.]+', "data.loan.interest_rate_annual_pct ?? ''", js)
js = re.sub(r'data\.loan\.other_fees_huf \?\? \d+', "data.loan.other_fees_huf ?? ''", js)

js = re.sub(r'data\.investment\.expected_return_annual_pct \?\? [\d\.]+', "data.investment.expected_return_annual_pct ?? ''", js)

# Nézzük meg a data.rent objektumot is
js = re.sub(r'data\.rent\.monthly_rent_huf \?\? \d+', "data.rent.monthly_rent_huf ?? ''", js)
js = re.sub(r'data\.rent\.utilities_monthly_huf \?\? \d+', "data.rent.utilities_monthly_huf ?? ''", js)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(js)
print("JS fallbacks replaced.")
