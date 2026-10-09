"""
API v1 végpontok a »Saját lakás vs. Bérlés« kvantitatív kalkulátorhoz.
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from schemas.simulation import SimulationInputSchema, SensitivityInputSchema
from core.engine import QuantitativeSimulationEngine
from core.defaults import DISTRICT_8_HISTORICAL_DATA, SCENARIOS

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_bp.route("/market-data/district-8", methods=["GET"])
def get_district_8_data():
    """
    Visszaadja a VIII. kerületi (Józsefváros) újépítésű piac kalibrációs adatait,
    valamint az előre definiált piaci forgatókönyveket (Base, Bear, Bull).
    """
    return jsonify({
        "status": "success",
        "data": {
            "historical_metrics": DISTRICT_8_HISTORICAL_DATA,
            "scenarios": SCENARIOS
        }
    }), 200


@api_bp.route("/simulate", methods=["POST"])
def simulate():
    """
    Fő szimulációs végpont: bemeneti paraméterek Pydantic validációja,
    majd 30 éves havi diszkontált cash-flow és nettó vagyonegyenleg szimuláció.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({
            "status": "error",
            "message": "Hiányzó vagy érvénytelen JSON kérés."
        }), 400

    try:
        validated = SimulationInputSchema(**payload)
    except ValidationError as err:
        return jsonify({
            "status": "validation_error",
            "message": "Paraméter validációs hiba.",
            "errors": err.errors()
        }), 422

    try:
        engine = QuantitativeSimulationEngine(validated.model_dump())
        results = engine.execute()
        return jsonify({
            "status": "success",
            "data": results
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "computation_error",
            "message": f"Számítási hiba lépett fel: {str(exc)}"
        }), 500


@api_bp.route("/sensitivity", methods=["POST"])
def sensitivity_analysis():
    """
    Érzékenységvizsgálat: kamatláb vs. ingatlanáremelkedés 2D rács generálása.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({
            "status": "error",
            "message": "Hiányzó vagy érvénytelen JSON kérés."
        }), 400

    # Ha közvetlenül a base_params-ot küldték vagy beágyazva:
    base_dict = payload.get("base_params", payload)
    try:
        validated_base = SimulationInputSchema(**base_dict)
    except ValidationError as err:
        return jsonify({
            "status": "validation_error",
            "message": "Alapparaméter validációs hiba.",
            "errors": err.errors()
        }), 422

    etf_return_range = payload.get("etf_return_range", None)
    property_growth_rates = payload.get("property_growth_rates", None)

    try:
        engine = QuantitativeSimulationEngine(validated_base.model_dump())
        matrix_data = engine.compute_sensitivity_matrix(
            etf_return_range=etf_return_range,
            property_growth_range=property_growth_rates
        )
        return jsonify({
            "status": "success",
            "data": matrix_data
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "computation_error",
            "message": f"Hiba az érzékenységvizsgálat futtatásakor: {str(exc)}"
        }), 500
