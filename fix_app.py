import re
with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"btnSaveTop\.addEventListener\('click', \(\) => \{\s*const profileName = prompt"
replacement = r"btnSaveTop.addEventListener('click', () => {\n        const payload = collectFormData();\n        if (!payload.property.price_total_huf || !payload.property.size_sqm || !payload.rent.monthly_rent_huf) {\n            showAlert('Hiányzó adatok', 'Kérjük, töltsd ki a kötelezõ mezõket (ingatlan vételára, alapterülete, havi albérlet díja) a mentéshez és szimulációhoz!', 'danger');\n            return;\n        }\n\n        const profileName = prompt"

content = re.sub(pattern, replacement, content)
with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
