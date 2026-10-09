import re

with open('core/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"raw_text = \(response\.text or \"\"\)\.strip\(\)\n\s*parsed = self\._clean_and_parse_json\(raw_text\)"
replacement = r"""raw_text = (response.text or "").strip()
                parsed = self._clean_and_parse_json(raw_text)

                # BUG FIX: Force empty fields to be truly empty in AI evaluations
                evals = parsed.get("evaluations", {})
                if not prop_notes and "property" in evals:
                    evals["property"].update({
                        "provided": False,
                        "relevance_score": 0,
                        "furnishing_adjustment_huf": 0,
                        "market_value_adjustment_pct": 0.0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    })
                if not loan_notes and "loan" in evals:
                    evals["loan"].update({
                        "provided": False,
                        "relevance_score": 0,
                        "furnishing_adjustment_huf": 0,
                        "market_value_adjustment_pct": 0.0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    })
                if not rent_notes and "rent" in evals:
                    evals["rent"].update({
                        "provided": False,
                        "relevance_score": 0,
                        "furnishing_adjustment_huf": 0,
                        "market_value_adjustment_pct": 0.0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    })
                if not inv_notes and "investment" in evals:
                    evals["investment"].update({
                        "provided": False,
                        "relevance_score": 0,
                        "furnishing_adjustment_huf": 0,
                        "market_value_adjustment_pct": 0.0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    })
"""

content = re.sub(pattern, replacement, content)

with open('core/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("gemini_service.py patched")
