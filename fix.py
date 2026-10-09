import re
import os

filepath = os.path.join('templates', 'index.html')
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

def replace_value(match):
    tag = match.group(0)
    if 'type="range"' in tag or 'type="checkbox"' in tag or 'type="radio"' in tag or 'type="hidden"' in tag:
        return tag
    new_tag = re.sub(r'\s+value="[^"]*"', '', tag)
    return new_tag

new_html = re.sub(r'<input[^>]*>', replace_value, html)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_html)
print("HTML values removed.")
