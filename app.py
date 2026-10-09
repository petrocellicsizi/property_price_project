"""
Flask alkalmazás - Dashboard Bemeneti Adatkezelő és Kvantitatív Motor.
A teljes matematikai és ingatlanpiaci modellezés a Python utils modulokban fut.
"""
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify

from core.gemini_service import gemini_service
from core.logger import logger
from utils.formatters import format_huf, format_with_dots, parse_clean_number
from utils.algorithms import (
    calculate_suggested_furnishing,
    calculate_suggested_rent,
    calculate_suggested_utilities,
    calculate_ai_adjusted_suggestions,
    calculate_suggested_price_per_sqm,
)
from utils.finance import (
    calculate_monthly_installment,
    calculate_total_initial_outlay,
    calculate_monthly_return_rate,
    calculate_property_metrics,
    calculate_lawyer_fee_metrics,
    calculate_down_payment_metrics,
)
from core.defaults import SCENARIOS

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.before_request
def log_request_info():
    if request.path.startswith('/api/'):
        logger.debug(f"API Kérés: {request.method} {request.path}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_FILE = os.path.join(DATA_DIR, "default_inputs.json")
SAVED_FILE = os.path.join(DATA_DIR, "saved_inputs.json")


def load_inputs():
    """Betölti a legutóbb elmentett adatokat, vagy a default értékeket."""
    target_file = SAVED_FILE if os.path.exists(SAVED_FILE) else DEFAULT_FILE
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_inputs(data):
    """Elmenti a beérkezett adatokat JSON fájlba."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SAVED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    """Dashboard nézet megjelenítése."""
    current_data = load_inputs()
    return render_template("index.html", initial_data=current_data)


@app.route("/api/inputs", methods=["GET"])
def get_inputs():
    """Visszaadja a jelenleg tárolt bemeneti adatokat."""
    data = load_inputs()
    is_custom = os.path.exists(SAVED_FILE)
    return jsonify({
        "status": "success",
        "is_custom": is_custom,
        "data": data
    }), 200

@app.route("/api/inputs", methods=["DELETE"])
def delete_inputs():
    """Törli a mentett adatokat, így a rendszer visszaáll az alapértékekre."""
    if os.path.exists(SAVED_FILE):
        os.remove(SAVED_FILE)
    return jsonify({"status": "success", "message": "Alapértékek visszaállítva."}), 200


@app.route("/api/calculate", methods=["POST"])
def calculate_metrics():
    """
    Kvantitatív pénzügyi és piaci számítások végrehajtása (Python backend).
    Kiszámítja a javasolt berendezési díjat, bérleti díjat, rezsit,
    a havi hiteltörlesztőt, az induló tőkét és a havi hozamrátát.
    Támogatja a Gemini AI által meghatározott felárak/diszkontok érvényesítését is.
    """
    data = request.get_json(silent=True) or {}
    
    logger.info("Szimulációs kalkuláció indítása...")
    logger.debug(f"Kalkulációs payload: {data}")
    
    prop = data.get("property", {})
    loan = data.get("loan", {})
    rent = data.get("rent", {})
    inv = data.get("investment", {})
    ai_evaluations = data.get("ai_evaluations") or {}

    # 1. Piaci és rezsi alap ajánló algoritmusok
    ptype = prop.get("property_type", "Újépítésű társasház (AA+)")
    condition = prop.get("condition", "Jó állapotú")
    size = parse_clean_number(prop.get("size_sqm", 52))
    rooms = parse_clean_number(prop.get("room_count", 2))
    city = prop.get("city", "Budapest")
    district = prop.get("district", "VIII. kerület")

    base_furnishing = calculate_suggested_furnishing(ptype, size, rooms)
    base_rent = calculate_suggested_rent(ptype, size, rooms, city, district)
    base_utilities = calculate_suggested_utilities(ptype, size)
    base_price_per_sqm = calculate_suggested_price_per_sqm(ptype, city, district, condition)
    base_price_total = int(base_price_per_sqm * size)

    # 2. AI korrekciók figyelembevétele, ha rendelkezésre állnak
    if ai_evaluations:
        base_suggestions = {
            "suggested_furnishing_huf": base_furnishing,
            "suggested_rent_huf": base_rent,
            "suggested_utilities_huf": base_utilities,
            "suggested_price_per_sqm_huf": base_price_per_sqm,
            "suggested_price_total_huf": base_price_total,
        }
        adjusted = calculate_ai_adjusted_suggestions(base_suggestions, ai_evaluations)
        suggested_furnishing = adjusted["suggested_furnishing_huf"]
        suggested_rent = adjusted["suggested_rent_huf"]
        suggested_utilities = adjusted["suggested_utilities_huf"]
        suggested_price_per_sqm = adjusted.get("suggested_price_per_sqm_huf", base_price_per_sqm)
        suggested_price_total = adjusted.get("suggested_price_total_huf", base_price_total)
        adjustments_info = adjusted.get("adjustments_applied", {})
    else:
        suggested_furnishing = base_furnishing
        suggested_rent = base_rent
        suggested_utilities = base_utilities
        suggested_price_per_sqm = base_price_per_sqm
        suggested_price_total = base_price_total
        adjustments_info = {}

    # 3. Pénzügyi és törlesztési számítások
    base_params = SCENARIOS["base"]["params"]
    price_total = parse_clean_number(prop.get("price_total_huf", suggested_price_total))
    
    # Calculate fallback loan amount based on base scenario's down payment ratio
    default_down_payment_ratio = base_params.get("down_payment_ratio", 0.25)
    default_down_payment = price_total * default_down_payment_ratio
    default_loan_amount = price_total - default_down_payment
    
    loan_amount = parse_clean_number(loan.get("loan_amount_huf", default_loan_amount))
    interest_pct = parse_clean_number(loan.get("interest_rate_annual_pct", base_params.get("loan_interest_rate_annual", 0.065) * 100))
    term_years = int(parse_clean_number(loan.get("loan_term_years", base_params.get("loan_term_years", 20))))

    # Hitel annuitásos törlesztő
    monthly_installment = calculate_monthly_installment(loan_amount, interest_pct, term_years)

    # Induló tőkeigény
    down_payment = parse_clean_number(loan.get("down_payment_huf", default_down_payment))
    
    default_lawyer_fee = price_total * base_params.get("legal_fee_rate", 0.01)
    lawyer_fee = parse_clean_number(prop.get("lawyer_fee_huf", default_lawyer_fee))
    other_fees = parse_clean_number(loan.get("other_fees_huf", 120000))
    furnishing = parse_clean_number(prop.get("furnishing_cost_huf", suggested_furnishing))

    total_initial_outlay = calculate_total_initial_outlay(
        down_payment_huf=down_payment,
        lawyer_fee_huf=lawyer_fee,
        other_fees_huf=other_fees,
        furnishing_cost_huf=furnishing,
        price_total_huf=price_total,
        transfer_tax_rate=base_params.get("transfer_tax_rate", 0.04)
    )

    # Befektetési havi ráta
    inv_return_pct = parse_clean_number(inv.get("expected_return_annual_pct", base_params.get("opportunity_cost_rate_annual", 0.07) * 100))
    monthly_return_rate = calculate_monthly_return_rate(inv_return_pct)

    # Bérlői havi összes kiadás
    rent_monthly = parse_clean_number(rent.get("monthly_rent_huf", suggested_rent))
    rent_utilities = parse_clean_number(rent.get("monthly_utilities_huf", suggested_utilities))
    total_rent_outlay = int(round(rent_monthly + rent_utilities))

    # 6. Szimulációs Motor Meghívása
    from core.engine import QuantitativeSimulationEngine
    
    # Engine paraméterek felépítése
    sim_params = {
        "simulation_years": int(parse_clean_number(inv.get("simulation_years", 30))),
        "loan_term_years": term_years,
        "property_size_sqm": size,
        "price_per_sqm": int(prop.get("price_per_sqm_huf", suggested_price_per_sqm)),
        "down_payment_ratio": parse_clean_number(loan.get("down_payment_pct", base_params.get("down_payment_ratio", 0.25) * 100)) / 100.0,
        "transfer_tax_rate": base_params.get("transfer_tax_rate", 0.04),
        "legal_fee_rate": parse_clean_number(prop.get("lawyer_fee_pct", base_params.get("legal_fee_rate", 0.01) * 100)) / 100.0,
        "renovation_cost_initial": parse_clean_number(prop.get("furnishing_cost_huf", suggested_furnishing)),
        "loan_interest_rate_annual": parse_clean_number(loan.get("interest_rate_annual_pct", base_params.get("loan_interest_rate_annual", 0.065) * 100)) / 100.0,
        "property_growth_rate_annual": parse_clean_number(inv.get("property_growth_pct", base_params.get("property_growth_rate_annual", 0.055) * 100)) / 100.0,
        "maintenance_rate_annual": base_params.get("maintenance_rate_annual", 0.01),
        "common_cost_monthly": rent_utilities,
        "rent_growth_rate_annual": parse_clean_number(inv.get("rent_inflation_pct", base_params.get("rent_growth_rate_annual", 0.045) * 100)) / 100.0,
        "initial_rent_monthly": rent_monthly,
        "opportunity_cost_rate_annual": inv_return_pct / 100.0,
        "tbsz_enabled": inv.get("tbsz_enabled", True),
        "discount_rate_annual": inv_return_pct / 100.0  # Align discount rate with opportunity cost
    }
    
    engine = QuantitativeSimulationEngine(sim_params)
    simulation_results = engine.execute()

    response_data = {
        "status": "success",
        "raw": {
            "suggested_price_per_sqm_huf": suggested_price_per_sqm,
            "suggested_price_total_huf": suggested_price_total,
            "suggested_furnishing_huf": suggested_furnishing,
            "suggested_rent_huf": suggested_rent,
            "suggested_utilities_huf": suggested_utilities,
            "estimated_monthly_payment_huf": monthly_installment,
            "total_initial_outlay_huf": total_initial_outlay,
            "total_rent_outlay_huf": total_rent_outlay,
            "monthly_return_rate_pct": monthly_return_rate,
            "adjustments_info": adjustments_info,
            "simulation": simulation_results,
            "sensitivity": engine.compute_sensitivity_matrix()
        },
        "formatted": {
            "suggested_price_per_sqm": f"{format_huf(suggested_price_per_sqm)}/m²",
            "suggested_price_total": format_huf(suggested_price_total),
            "suggested_furnishing": format_huf(suggested_furnishing),
            "suggested_rent": format_huf(suggested_rent),
            "suggested_utilities": format_huf(suggested_utilities),
            "estimated_monthly_payment": f"{format_huf(monthly_installment)}/hó",
            "total_initial_outlay": format_huf(total_initial_outlay),
            "total_rent_outlay": f"{format_huf(total_rent_outlay)}/hó",
            "monthly_return_rate": f"{monthly_return_rate:.2f}% / hó",
        }
    }
    return jsonify(response_data), 200

@app.route("/api/historical_simulation", methods=["POST"])
def historical_simulation():
    """
    Kiszámítja a historikus vagyonalakulást a megadott induló évtől napjainkig,
    visszaszámolva a jelenlegi lakásárból az induló tőkét.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "Érvénytelen vagy hiányzó JSON adat."}), 400
        
    start_year = int(payload.get("start_year", 2004))
    city = payload.get("city", "Budapest")
    district = payload.get("district", "XI. kerület")
    current_value = float(payload.get("current_property_value_huf", 60000000))
    down_payment_pct = float(payload.get("down_payment_pct", 20.0))
    loan_interest_pct = float(payload.get("loan_interest_pct", 6.5))
    loan_term_years = int(payload.get("loan_term_years", 20))
    current_rent_huf = float(payload.get("current_rent_huf", 200000))
    current_utilities_huf = float(payload.get("current_utilities_huf", 30000))
    
    from core.historical_engine import HistoricalEngine
    engine = HistoricalEngine()
    result = engine.simulate(
        start_year, city, district, current_value,
        down_payment_pct, loan_interest_pct, loan_term_years,
        current_rent_huf, current_utilities_huf
    )
    
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 400
        
    return jsonify({"status": "success", "data": result}), 200

@app.route("/api/inputs", methods=["POST"])
def store_inputs():
    """
    Fogadja a dashboardról érkező adatokat és letárolja.
    Meghívja a Gemini AI szolgáltatást az egyéb releváns információk
    szakmai kiértékelésére és a javaslatok számszerű AI korrekciójára (pl. Dunamenti felár).
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({
            "status": "error",
            "message": "Érvénytelen vagy hiányzó JSON adat."
        }), 400

    # 1. Gemini AI elemzés futtatása a kiegészítő megjegyzésekre
    gemini_analysis = gemini_service.evaluate_all_notes(payload)

    # 2. Alap piaci javaslatok kiszámítása az aktuális lakásadatok alapján
    prop = payload.get("property", {})
    ptype = prop.get("property_type", "Újépítésű társasház (AA+)")
    size = parse_clean_number(prop.get("size_sqm", 52))
    rooms = parse_clean_number(prop.get("room_count", 2))
    city = prop.get("city", "Budapest")
    district = prop.get("district", "VIII. kerület")

    base_suggestions = {
        "suggested_furnishing_huf": calculate_suggested_furnishing(ptype, size, rooms),
        "suggested_rent_huf": calculate_suggested_rent(ptype, size, rooms, city, district),
        "suggested_utilities_huf": calculate_suggested_utilities(ptype, size),
    }

    # 3. AI korrekciók hozzáadása a javaslatokhoz
    ai_evaluations = gemini_analysis.get("evaluations", {})
    ai_adjusted_suggestions = calculate_ai_adjusted_suggestions(base_suggestions, ai_evaluations)

    # Időbélyeg és elemzés hozzáadása az adatrekordhoz
    stored_payload = {
        "updated_at": datetime.now().isoformat(),
        "inputs": payload,
        "gemini_analysis": gemini_analysis,
        "ai_adjusted_suggestions": ai_adjusted_suggestions
    }

    try:
        save_inputs(stored_payload)
        return jsonify({
            "status": "saved",
            "message": "A bemeneti paraméterek és a Gemini AI elemzés sikeresen elmentve!",
            "data": stored_payload,
            "gemini_analysis": gemini_analysis,
            "ai_adjusted_suggestions": ai_adjusted_suggestions
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Nem sikerült elmenteni az adatokat: {str(exc)}"
        }), 500
@app.route("/api/generate_summary", methods=["POST"])
def generate_summary():
    """
    Készít egy végső szöveges összefoglalót a szimuláció kimenetéről.
    """
    payload = request.get_json(silent=True)
    if not payload:
        logger.warning("generate_summary hívás hiányzó payload-dal.")
        return jsonify({"status": "error", "message": "Hiányzó adatok"}), 400

    logger.info("AI Összefoglaló generálása indult...")
    sim_results = payload.get("simulation", {})
    inputs = payload.get("inputs", {})

    summary_text = gemini_service.generate_simulation_summary(sim_results, inputs)
    logger.info("AI Összefoglaló generálása kész.")
    return jsonify({"summary_text": summary_text}), 200

@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """
    Kezeli az AI Chat Asszisztens kéréseit.
    Várja a felhasználó üzenetét, a chat előzményeket és az aktuális bemeneteket.
    """
    payload = request.get_json(silent=True)
    if not payload:
        logger.warning("chat_endpoint hívás hiányzó payload-dal.")
        return jsonify({"status": "error", "message": "Hiányzó adatok"}), 400

    user_message = payload.get("message", "")
    history = payload.get("history", [])
    current_params = payload.get("current_params", {})

    if not user_message:
        logger.warning("chat_endpoint hívás üres üzenettel.")
        return jsonify({"status": "error", "message": "Üres üzenet"}), 400

    logger.info(f"AI Chat kérés érkezett. Üzenet: '{user_message[:50]}...' (Előzmények hossza: {len(history)})")
    ai_response = gemini_service.chat_with_assistant(user_message, current_params, history)
    
    if ai_response.get("updates"):
        logger.info(f"AI módosította a csúszkákat: {ai_response['updates']}")
        
    return jsonify(ai_response), 200

@app.route("/api/analyze_location", methods=["POST"])
def analyze_location():
    """
    AI mikrolokációs elemzés a megadott pontos cím alapján.
    """
    payload = request.get_json(silent=True)
    if not payload or not payload.get("address"):
        logger.warning("analyze_location hívás hiányzó címmel.")
        return jsonify({"status": "error", "message": "Hiányzó cím"}), 400

    address = payload.get("address")
    logger.info(f"AI Lokáció elemzés indul: {address}")
    
    result = gemini_service.analyze_location(address)
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 500

    return jsonify(result), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)