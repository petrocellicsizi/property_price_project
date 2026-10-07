"""
Gemini AI Szolgáltatás a felhasználói kiegészítő információk elemzésére.
A google-genai SDK-t és a hivatalos Google Gemini modelleket használja (gemini-3.5-flash-lite és gemini-3.8-flash).
Beépített szigorú JSON sémával és robusztus hibajavító parserrel rendelkezik.
Közvetlen számszerű javaslat-korrekciókat (rent_adjustment_pct, furnishing_adjustment_huf stb.) generál.
"""
import os
import re
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai

# Környezeti változók (.env) betöltése
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiEvaluationService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.primary_model = "gemini-3.5-flash-lite"
        self.secondary_model = "gemini-3.8-flash"
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Hiba a Gemini Client inicializálásakor: {e}")

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Robusztus JSON kinyerő és szintaktikai hibajavító függvény.
        Kezeli a markdown kódblokkokat, a bevezető szövegeket,
        a lebegő idézőjeleket és a trailing vesszőket.
        """
        if not raw_text:
            raise ValueError("Üres válasz érkezett az AI modelltől.")

        text = raw_text.strip()

        # 1. Markdown blokkok kibontása
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        elif "```" in text:
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        # 2. Legkülső kapcsos zárójelek megkeresése
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1].strip()

        # 3. Első próbálkozás: natív json.loads strict=False mellett
        res = None
        try:
            res = json.loads(text, strict=False)
        except json.JSONDecodeError:
            pass

        # 4. Trailing vesszők eltávolítása objektumok és listák végéről
        if not res:
            cleaned = re.sub(r",\s*([\]}])", r"\1", text)
            try:
                res = json.loads(cleaned, strict=False)
            except json.JSONDecodeError:
                pass

        # 5. Nem engedélyezett ASCII vezérlőkarakterek cseréje
        if not res:
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
            cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
            try:
                res = json.loads(cleaned, strict=False)
            except json.JSONDecodeError:
                pass

        # Ha sikerült a JSON parse, biztosítjuk a számszerű korrekciós mezők meglétét
        if res and isinstance(res, dict) and "evaluations" in res:
            for sec in ["property", "loan", "rent", "investment"]:
                if sec in res["evaluations"]:
                    item = res["evaluations"][sec]
                    item["furnishing_adjustment_huf"] = int(item.get("furnishing_adjustment_huf") or 0)
                    item["rent_adjustment_pct"] = float(item.get("rent_adjustment_pct") or 0.0)
                    item["utilities_adjustment_pct"] = float(item.get("utilities_adjustment_pct") or 0.0)
            return res

        # 6. Végső heurisztika: Regex alapú kinyerés a 4 szekcióra, ha a JSON szintaxis sérült
        logger.warning("A modell JSON szintaxisa sérült, regex alapú kinyerés indul...")
        overall_match = re.search(r'"overall_summary"\s*:\s*"([^"]+)"', text)
        overall_summary = overall_match.group(1) if overall_match else "A kiegészítő megjegyzések feldolgozásra kerültek."

        evaluations = {}
        for section in ["property", "loan", "rent", "investment"]:
            sec_pattern = re.compile(rf'"{section}"\s*:\s*\{{([^}}]+)\}}', re.DOTALL)
            sec_match = sec_pattern.search(text)
            if sec_match:
                block = sec_match.group(1)
                score_match = re.search(r'"relevance_score"\s*:\s*(\d+)', block)
                cat_match = re.search(r'"category"\s*:\s*"([^"]+)"', block)
                impact_match = re.search(r'"impact_analysis"\s*:\s*"([^"]+)"', block)
                rec_match = re.search(r'"quantitative_recommendation"\s*:\s*"([^"]+)"', block)
                furnish_match = re.search(r'"furnishing_adjustment_huf"\s*:\s*(-?\d+)', block)
                market_match = re.search(r'"market_value_adjustment_pct"\s*:\s*(-?\d+(?:\.\d+)?)', block)
                rent_match = re.search(r'"rent_adjustment_pct"\s*:\s*(-?\d+(?:\.\d+)?)', block)
                utils_match = re.search(r'"utilities_adjustment_pct"\s*:\s*(-?\d+(?:\.\d+)?)', block)

                evaluations[section] = {
                    "provided": True,
                    "relevance_score": int(score_match.group(1)) if score_match else 7,
                    "category": cat_match.group(1) if cat_match else "Szakmai tényező",
                    "impact_analysis": impact_match.group(1) if impact_match else "A megadott tényező befolyásolja a számítást.",
                    "quantitative_recommendation": rec_match.group(1) if rec_match else "Kvantitatív korrekció szükséges.",
                    "furnishing_adjustment_huf": int(furnish_match.group(1)) if furnish_match else 0,
                    "market_value_adjustment_pct": float(market_match.group(1)) if market_match else 0.0,
                    "rent_adjustment_pct": float(rent_match.group(1)) if rent_match else 0.0,
                    "utilities_adjustment_pct": float(utils_match.group(1)) if utils_match else 0.0
                }
            else:
                evaluations[section] = {
                    "provided": False,
                    "relevance_score": 0,
                    "category": "Alapértelmezett",
                    "impact_analysis": "Nem sikerült értelmezni.",
                    "quantitative_recommendation": "Nincs korrekció.",
                    "furnishing_adjustment_huf": 0,
                    "market_value_adjustment_pct": 0.0,
                    "rent_adjustment_pct": 0.0,
                    "utilities_adjustment_pct": 0.0
                }

        if evaluations:
            return {
                "overall_summary": overall_summary,
                "evaluations": evaluations
            }

        raise ValueError(f"Nem sikerült érvényes adatokat kinyerni a szövegből: {text[:200]}")

    def evaluate_all_notes(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiértékeli a 4 szekcióban megadott 'egyéb releváns információkat'.
        Minden megadott mezőhöz 1-10-es relevancia pontszámot, pénzügyi kihatás-elemzést,
        kvantitatív korrekciós javaslatot és konkrét számszerű felárat/diszkontot határoz meg.
        """
        prop_data = payload.get("property", {})
        loan_data = payload.get("loan", {})
        rent_data = payload.get("rent", {})
        inv_data = payload.get("investment", {})

        prop_notes = (prop_data.get("other_info") or "").strip()
        loan_notes = (loan_data.get("other_info") or "").strip()
        rent_notes = (rent_data.get("other_info") or "").strip()
        inv_notes = (inv_data.get("other_info") or "").strip()

        # Ha egyik mező sincs kitöltve, azonnali strukturált választ adunk
        if not any([prop_notes, loan_notes, rent_notes, inv_notes]):
            return {
                "status": "empty",
                "model_used": "N/A (üres bemenet)",
                "overall_summary": "Nem lett megadva egyéni kiegészítő információ. A pénzügyi modell a standard piaci átlagok és törlesztési szabályok alapján kalkulál.",
                "evaluations": {
                    "property": {
                        "provided": False,
                        "relevance_score": 0,
                        "category": "Alapértelmezett piaci modell",
                        "impact_analysis": "Nincs egyedi ingatlantulajdonság rögzítve. Standard amortizációs és felértékelődési ráta érvényesül.",
                        "quantitative_recommendation": "Nincs szükség korrekcióra.",
                        "furnishing_adjustment_huf": 0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    },
                    "loan": {
                        "provided": False,
                        "relevance_score": 0,
                        "category": "Standard banki hiteltermék",
                        "impact_analysis": "Standard annuitásos törlesztőrészlet és kamatfelár kerül modellezésre.",
                        "quantitative_recommendation": "Nincs szükség korrekcióra.",
                        "furnishing_adjustment_huf": 0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    },
                    "rent": {
                        "provided": False,
                        "relevance_score": 0,
                        "category": "Piaci átlagos bérleti feltételek",
                        "impact_analysis": "Átlagos bérleti indexálás és üresedési ráta (vacancy rate) feltételezett.",
                        "quantitative_recommendation": "Nincs szükség korrekcióra.",
                        "furnishing_adjustment_huf": 0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    },
                    "investment": {
                        "provided": False,
                        "relevance_score": 0,
                        "category": "Standard alternatív hozam",
                        "impact_analysis": "Standard elvárt piaci hozam, egyedi adózási vagy likviditási prémium nélkül.",
                        "quantitative_recommendation": "Nincs szükség korrekcióra.",
                        "furnishing_adjustment_huf": 0,
                        "rent_adjustment_pct": 0.0,
                        "utilities_adjustment_pct": 0.0
                    }
                }
            }

        if not self.client:
            return {
                "status": "error",
                "message": "A Gemini API kliens nem elérhető (hiányzó API kulcs a .env fájlban).",
                "evaluations": {}
            }

        city = prop_data.get("city") or "Budapest"
        district = prop_data.get("district") or "VIII. kerület"
        prop_type = prop_data.get("property_type") or "Újépítésű társasház (AA+)"
        size_sqm = prop_data.get("size_sqm") or 52
        price = prop_data.get("price_total_huf") or 80600000

        loan_amount = loan_data.get("loan_amount_huf") or 60450000
        loan_term = loan_data.get("loan_term_years") or 20
        interest_pct = loan_data.get("interest_rate_annual_pct") or 6.5

        rent_huf = rent_data.get("monthly_rent_huf") or 270000
        utils_huf = rent_data.get("monthly_utilities_huf") or 34000

        inv_pct = inv_data.get("expected_return_annual_pct") or 7.0

        prompt = f"""Te egy szeniör kvantitatív pénzügyi elemző és magyar ingatlanpiaci modellező szakértő vagy.
A felhasználó egy 'Saját lakás vs. Bérlés' megtérülési kalkulátorhoz (Break-Even modell) adott meg bemeneti adatokat.
A modell 4 területén a felhasználó az alábbi kiegészítő megjegyzéseket rögzítette:

--- ALAPADATOK ---
- Ingatlan: {city}, {district}, Típus: {prop_type}, Méret: {size_sqm} m2, Vételár: {price:,} Ft
- Hitel: {loan_amount:,} Ft, Futamidő: {loan_term} év, Kamat/THM: {interest_pct}%
- Bérlés alapjavaslat: {rent_huf:,} Ft/hó, Rezsi alapjavaslat: {utils_huf:,} Ft/hó
- Alternatív befektetési hozam: {inv_pct}%/év

--- FELHASZNÁLÓI KIEGÉSZÍTŐ MEGJEGYZÉSEK ---
1. LAKÁS & INGATLAN EGYÉB INFÓ: "{prop_notes if prop_notes else 'Nincs megadva'}"
2. HITEL & FINANSZÍROZÁS EGYÉB INFÓ: "{loan_notes if loan_notes else 'Nincs megadva'}"
3. ALBÉRLET & REZSI EGYÉB INFÓ: "{rent_notes if rent_notes else 'Nincs megadva'}"
4. BEFEKTETÉS & MEGTAKARÍTÁS EGYÉB INFÓ: "{inv_notes if inv_notes else 'Nincs megadva'}"

FELADAT:
Értékeld ki a fenti megjegyzéseket a 'Saját lakás vs. Bérlés' DCF és NPV számítás szempontjából!
Kifejezetten határozz meg konkrét számszerű módosító értékeket is, amelyek közvetlenül beépülnek a kalkulátor megbecsült javaslataiba:
- property szekciónál:
  * "furnishing_adjustment_huf": egész szám (Ft), amennyivel az információ növeli vagy csökkenti a berendezési/bútorozási igényt (pl. 300000 vagy -150000, ha nincs: 0)
  * "market_value_adjustment_pct": százalékos lebegőpontos érték, amennyivel a becsült piaci értéket (vételárat) módosítja az egyedi tényező (pl. +5.0 ha luxus panorámás, -10.0 ha sötét földszinti, 0.0 ha nincs érdemi hatás)
- rent szekciónál:
  * "rent_adjustment_pct": százalékos lebegőpontos érték, amennyivel a bérleti díj javaslat módosuljon a bérlői igények/lokáció miatt (pl. +15.0 ha Dunamenti vagy prémium lokáció, +10.0 ha kutya felár, -5.0 ha kompromisszumos, 0.0 ha nincs)
  * "utilities_adjustment_pct": százalékos lebegőpontos érték a rezsire (pl. +10.0 ha tetőtéri hűtési többlet, 0.0 ha nincs)

SZIGORÚ FORMÁTUMI KÖVETELMÉNYEK:
1. Válaszolj KIZÁRÓLAG érvényes JSON formátumban!
2. A szöveges mezők értékeiben SOHA NE használj idézőjelet (\"), helyette szimpla idézőjelet (') vagy kötőjelet használj!
3. Ne tegyél felesleges vesszőt az utolsó elemek után!

MINTA JSON:
{{
  "overall_summary": "Szakértői összefoglaló...",
  "evaluations": {{
    "property": {{
      "provided": {str(bool(prop_notes)).lower()},
      "relevance_score": 8,
      "category": "Likviditás és Értékmegőrzés",
      "impact_analysis": "A felújítási igény többletköltséget jelent...",
      "quantitative_recommendation": "300.000 Ft bútorozási többlet indokolt.",
      "furnishing_adjustment_huf": 300000,
      "market_value_adjustment_pct": 5.0
    }},
    "loan": {{
      "provided": {str(bool(loan_notes)).lower()},
      "relevance_score": 7,
      "category": "Kamatkockázat és Tőkeáttétel",
      "impact_analysis": "A kamattámogatott forrás csökkenti a havi terhet...",
      "quantitative_recommendation": "A súlyozott tőkeköltség 4.8%-ra csökken."
    }},
    "rent": {{
      "provided": {str(bool(rent_notes)).lower()},
      "relevance_score": 9,
      "category": "Lokációs Prémium",
      "impact_analysis": "A Dunamenti elhelyezkedés vagy speciális igény jelentős bérleti felárat képvisel...",
      "quantitative_recommendation": "+15% bérleti díj felár indokolt a Dunamenti prémium miatt.",
      "rent_adjustment_pct": 15.0,
      "utilities_adjustment_pct": 0.0
    }},
    "investment": {{
      "provided": {str(bool(inv_notes)).lower()},
      "relevance_score": 9,
      "category": "Adóoptimalizáció",
      "impact_analysis": "A TBSZ 0% kamatadója miatt a teljes hozam felhalmozódik...",
      "quantitative_recommendation": "15% SZJA és 13% SZOCHO megtakarítás érvényesül."
    }}
  }}
}}"""

        # Próbálkozás a modellekkel kényszerített JSON mime-típussal
        models_to_try = [self.primary_model, self.secondary_model]
        last_error = None

        for model in models_to_try:
            try:
                interaction = self.client.interactions.create(
                    model=model,
                    input=prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                raw_text = (interaction.output_text or "").strip()
                parsed = self._clean_and_parse_json(raw_text)
                parsed["status"] = "success"
                parsed["model_used"] = model
                return parsed
            except Exception as exc:
                logger.warning(f"Modell hiba ({model}): {exc}")
                last_error = exc

        # Ha egyik Gemini hívás sem sikerült, intelligens heurisztikus tartalék
        logger.error(f"Minden Gemini modell kérése sikertelen volt: {last_error}")
        prop_furnish_adj = 300000 if ("felújít" in prop_notes.lower() or "bútor" in prop_notes.lower()) else 0
        rent_adj_pct = 15.0 if ("duna" in rent_notes.lower() or "panoráma" in rent_notes.lower()) else (10.0 if ("kutya" in rent_notes.lower() or "állat" in rent_notes.lower()) else 0.0)

        return {
            "status": "fallback",
            "model_used": "Heurisztikus Offline Elemző",
            "message": f"Gemini API hiba ({str(last_error)}) - Intelligens offline heurisztika alkalmazva.",
            "overall_summary": "A megadott egyedi paraméterek rögzítésre kerültek az adatbázisban, és a kvantitatív modell közvetlen korrekcióként kezeli őket.",
            "evaluations": {
                "property": {
                    "provided": bool(prop_notes),
                    "relevance_score": 8 if prop_notes else 0,
                    "category": "Ingatlanállapot és Fizikai Jellemzők",
                    "impact_analysis": prop_notes if prop_notes else "Nincs megadva egyéb információ.",
                    "quantitative_recommendation": f"Alkalmazzon {prop_furnish_adj:,} Ft berendezési korrekciót." if prop_notes else "Nincs szükség korrekcióra.",
                    "furnishing_adjustment_huf": prop_furnish_adj,
                    "rent_adjustment_pct": 0.0,
                    "utilities_adjustment_pct": 0.0
                },
                "loan": {
                    "provided": bool(loan_notes),
                    "relevance_score": 8 if loan_notes else 0,
                    "category": "Finanszírozási Struktúra és Tőkeáttétel",
                    "impact_analysis": loan_notes if loan_notes else "Nincs megadva egyéb információ.",
                    "quantitative_recommendation": "Számoljon a kamattámogatott források tőkemegtérülési hatásával." if loan_notes else "Nincs szükség korrekcióra.",
                    "furnishing_adjustment_huf": 0,
                    "rent_adjustment_pct": 0.0,
                    "utilities_adjustment_pct": 0.0
                },
                "rent": {
                    "provided": bool(rent_notes),
                    "relevance_score": 8 if rent_notes else 0,
                    "category": "Bérleti Piaci Költségek és Lokáció",
                    "impact_analysis": rent_notes if rent_notes else "Nincs megadva egyéb információ.",
                    "quantitative_recommendation": f"Alkalmazzon +{rent_adj_pct}% bérleti felárat a megadott igények miatt." if rent_notes else "Nincs szükség korrekcióra.",
                    "furnishing_adjustment_huf": 0,
                    "rent_adjustment_pct": rent_adj_pct,
                    "utilities_adjustment_pct": 0.0
                },
                "investment": {
                    "provided": bool(inv_notes),
                    "relevance_score": 9 if inv_notes else 0,
                    "category": "Adózás és Kamatos Kamat Hatás",
                    "impact_analysis": inv_notes if inv_notes else "Nincs megadva egyéb információ.",
                    "quantitative_recommendation": "TBSZ esetén adómentesség növeli az alternatív vagyontömeget." if inv_notes else "Nincs szükség korrekcióra.",
                    "furnishing_adjustment_huf": 0,
                    "rent_adjustment_pct": 0.0,
                    "utilities_adjustment_pct": 0.0
                }
            }
        }

    def generate_simulation_summary(self, simulation_results: dict, payload: dict) -> str:
        """
        Készít egy rövid, szöveges összefoglalót a szimuláció eredményeiről.
        """
        if not self.client:
            return "A Gemini API nem elérhető, az összefoglaló nem generálható."

        try:
            summary_data = simulation_results.get("summary", {})
            bep_status = summary_data.get("break_even_status", "Ismeretlen")
            bep_year = summary_data.get("break_even_year", "N/A")
            wealth_buy = summary_data.get("terminal_buy_net_worth", 0)
            wealth_rent = summary_data.get("terminal_rent_net_worth", 0)
            
            rent_pct = payload.get("investment", {}).get("expected_return_annual_pct", 7.0)
            prop_pct = payload.get("investment", {}).get("property_growth_pct", 5.0)

            prompt = f"""Te egy pénzügyi tanácsadó vagy. Kérlek írj egy RÖVID, 3-4 mondatos összefoglalót a felhasználónak a következő szimuláció eredményéről, érthetően elmagyarázva, hogy miért ez az eredmény jött ki. Ne használj bonyolult formázást (csak sima szöveg, esetleg vastagítás).

SZIMULÁCIÓS EREDMÉNYEK (30 ÉV):
- Saját lakás (hitelre vett) nettó vagyon 30 év múlva: {wealth_buy:,} Ft
- Bérlés + ETF (megtakarított pénz befektetése) vagyon 30 év múlva: {wealth_rent:,} Ft
- Befektetési hozam (ETF): {rent_pct}%/év
- Ingatlan drágulása: {prop_pct}%/év
- Megtérülési (Break-Even) pont (mikortól éri meg jobban a saját lakás): {bep_status} (Év: {bep_year})

MAGYARÁZAT:
Magyarázd el, hogy az ETF magasabb kamatos kamata, vagy az ingatlan tőkeáttétele (hitel) dominált-e, és röviden fűzd hozzá, hogy a futamidő lejárta után hogyan alakult a bérlő vs. tulajdonos havi készpénzárama (törlesztő kiesése vs. egyre növekvő bérleti díj). Légy barátságos!
"""
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Gemini API hiba a szimuláció összefoglalása közben: {str(e)}")
            return "Nem sikerült az AI összefoglalót generálni hálózati hiba miatt."

    def chat_with_assistant(self, user_message: str, current_params: dict, history_dicts: list) -> dict:
        """
        Dinamikus chat asszisztens function calling támogatással.
        """
        if not self.client:
            return {"text": "A Gemini API nem elérhető.", "updates": {}}

        from google.genai import types
        
        captured_args = {}

        def update_simulation_params(
            price_total_huf: int = None,
            down_payment_pct: float = None,
            loan_term_years: int = None,
            interest_rate_annual_pct: float = None,
            monthly_rent_huf: int = None,
            expected_return_annual_pct: float = None,
            property_growth_pct: float = None
        ) -> str:
            """
            Frissíti a szimuláció csúszkáit és bemeneti paramétereit a megadott értékekkel.
            Csak azokat a paramétereket add meg, amiket a felhasználó kifejezetten meg akar változtatni!
            A többi maradjon None.
            """
            nonlocal captured_args
            captured_args = {
                k: v for k, v in locals().items() 
                if k != 'captured_args' and v is not None
            }
            return f"Paraméterek frissítve: {captured_args}"

        # Konvertáljuk a dictionary history-t a GenAI types.Content objektumokká
        converted_history = []
        for msg in history_dicts:
            role = 'user' if msg['role'] == 'user' else 'model'
            converted_history.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg['content'])])
            )

        sys_prompt = f"""Te egy pénzügyi AI asszisztens vagy egy 'Saját lakás vs Bérlés' szimulátor weboldalon.
A felhasználó a chaten keresztül kérdezhet, vagy megkérhet, hogy állítsd át a kalkulátor csúszkáit (pl. 'Mi lenne ha 30% lenne az önerő?').
Ilyenkor HÍVD MEG az `update_simulation_params` függvényt az új értékekkel! Fontos: A vételárat Ft-ban add meg, a %-okat számként (pl. 30).

Jelenlegi beállított paraméterek:
{json.dumps(current_params, indent=2, ensure_ascii=False)}

Válaszolj röviden, barátságosan, magyarul! Ha módosítottad a paramétereket, említsd meg a válaszban!
"""

        try:
            chat = self.client.chats.create(
                model=self.primary_model,
                config={
                    "tools": [update_simulation_params],
                    "system_instruction": sys_prompt,
                    "temperature": 0.7
                },
                history=converted_history
            )
            
            response = chat.send_message(user_message)
            
            return {
                "text": response.text.strip(),
                "updates": captured_args
            }
        except Exception as e:
            logger.error(f"Chat API hiba: {str(e)}")
            return {"text": "Hiba történt az üzenet feldolgozása közben.", "updates": {}}



# Egyke (Singleton) példány
gemini_service = GeminiEvaluationService()
