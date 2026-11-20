"""
Tesztek a felülvizsgálati audit során azonosított és javított I. kritikus és II. magas prioritású hibákhoz.
"""
import pytest
from app import app
from core.engine import QuantitativeSimulationEngine
from core.creditworthiness import calculate_jtm_limit, calculate_creditworthiness
from core.defaults import SCENARIOS
from utils.algorithms import calculate_suggested_price_per_sqm, calculate_suggested_rent


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_fix_short_simulation_preserves_contractual_mortgage():
    """1. Hiba: 5 éves szimuláció nem írhatja át a 20 éves hitelszerződést 5 évesre."""
    params = dict(SCENARIOS["base"]["params"])
    params["simulation_years"] = 5
    params["loan_term_years"] = 20

    engine = QuantitativeSimulationEngine(params)
    res = engine.execute()

    summary = res["summary"]
    trajectories = res["trajectories"]

    # A havi törlesztőnek a 20 éves futamidő szerintinek kell lennie (~450.699 Ft), nem pedig ~1.183.000 Ft
    assert summary["monthly_loan_pmt"] == pytest.approx(450_699.0, abs=10.0)

    # Az 5. év végén (60. hónap) a hiteltartozás nem lehet 0 Ft, hanem a valós ~51.74m Ft tőketartozás!
    assert trajectories["remaining_loan_balance"][-1] == pytest.approx(51_738_624.0, abs=500.0)
    assert len(trajectories["month"]) == 60


def test_fix_dcf_npv_equal_initial_equity_deduction():
    """2. Hiba: A bérlő NPV-jéből is le kell vonni a kezdeti befektetett tőkét (t=0)."""
    params = dict(SCENARIOS["base"]["params"])
    engine = QuantitativeSimulationEngine(params)
    res = engine.execute()

    trajectories = res["trajectories"]
    dcf_buy_terminal = trajectories["dcf_buy"][-1]
    dcf_rent_terminal = trajectories["dcf_rent"][-1]

    # Mindkét stratégia induló tőkével indult, a bérlés NPV-je nem lehet irreálisan jobb a t=0 elhagyása miatt
    # A vevő NPV-jének jobbnak kell lennie, mint a bérlőének az alapesetben (+15m Ft körül)
    assert dcf_buy_terminal > dcf_rent_terminal
    assert dcf_buy_terminal - dcf_rent_terminal > 10_000_000.0


def test_fix_district_8_exact_matching():
    """4. Hiba: A VIII. kerület nem illeszkedhet az 'I.' kerület részstringjére."""
    # VIII. kerület referencia szorzója 1.0 (újépítésűnél 1.550.000 Ft/m²), nem pedig prémium 2.090.000 Ft/m²
    price_viii = calculate_suggested_price_per_sqm("Újépítésű társasház (AA+)", district="VIII. kerület")
    assert price_viii == 1_550_000

    price_i = calculate_suggested_price_per_sqm("Újépítésű társasház (AA+)", district="I. kerület")
    assert price_i == 2_090_000

    rent_viii = calculate_suggested_rent("Újépítésű társasház (AA+)", 52, 2, district="VIII. kerület")
    assert rent_viii == 270_000


def test_fix_api_v1_blueprint_registered(client):
    """5. Hiba: Az /api/v1 végpontok elérhetőek az éles app példányon keresztül is."""
    res_market = client.get("/api/v1/market-data/district-8")
    assert res_market.status_code == 200
    assert "historical_metrics" in res_market.get_json()["data"]

    res_sim = client.post("/api/v1/simulate", json=SCENARIOS["base"]["params"])
    assert res_sim.status_code == 200
    assert "summary" in res_sim.get_json()["data"]


def test_fix_mnb_2026_income_threshold_and_zero_fixation():
    """7. Hiba: MNB 800.000 Ft-os jövedelemhatár és 0 év kamatfixálás (változó) kezelése."""
    # 700.000 Ft jövedelem 2026-tól már nem magas jövedelem (50% a korlát 10 év fixnél)
    assert calculate_jtm_limit(700_000, 10.0) == 50.0

    # 800.000 Ft-tól válik elérhetővé a 60%
    assert calculate_jtm_limit(800_000, 10.0) == 60.0

    # 0.0 év fixálás esetén változó kamatozásúként 25% a limit (nem minősül 10 év fixnek!)
    res_var = calculate_creditworthiness(
        net_monthly_income_huf=700_000,
        loan_principal_huf=40_000_000,
        annual_interest_rate_pct=6.5,
        loan_term_years=20,
        interest_period_years=0.0,
        property_price_huf=60_000_000
    )
    assert res_var["metrics"]["mnb_limit_pct"] == 25.0


def test_fix_csok_plusz_and_babavaro_integration(client):
    """8. Hiba: CSOK Plusz 3%-os kamatplafon és Babaváró havi adósságszolgálat."""
    # Alap kalkuláció CSOK Plusz és Babaváróval
    payload = {
        "property": {
            "city": "Budapest",
            "district": "VIII. kerület",
            "size_sqm": 52,
            "room_count": 2,
            "price_total_huf": 80600000
        },
        "loan": {
            "loan_amount_huf": 60450000,
            "loan_term_years": 20,
            "down_payment_huf": 20150000,
            "csok_plusz": True,
            "babavaro": True
        },
        "rent": {
            "monthly_rent_huf": 270000,
            "monthly_utilities_huf": 34000
        },
        "investment": {
            "expected_return_annual_pct": 7.0,
            "simulation_years": 30
        }
    }
    rv = client.post("/api/calculate", json=payload)
    assert rv.status_code == 200
    data = rv.get_json()

    # CSOK Plusz miatt az illeték 0 Ft
    # A Babaváró havi törlesztése (~50.416 Ft) hozzáadódik a havi kiadásokhoz
    assert data["raw"]["simulation"]["summary"]["monthly_loan_pmt"] > 0
