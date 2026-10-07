"""
Pydantic validációs sémák a pénzügyi szimulációs végpontokhoz.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class SimulationInputSchema(BaseModel):
    # Ingatlan fizikai és vásárlási paraméterei
    property_size_sqm: float = Field(
        default=52.0, 
        ge=15.0, 
        le=300.0, 
        description="Lakás hasznos alapterülete négyzetméterben"
    )
    price_per_sqm: float = Field(
        default=1_550_000.0, 
        ge=300_000.0, 
        le=5_000_000.0, 
        description="Újépítésű négyzetméterár HUF-ban"
    )
    renovation_cost_initial: float = Field(
        default=2_500_000.0, 
        ge=0.0, 
        le=50_000_000.0, 
        description="Kezdeti berendezés, bútorozás, konyhagépek"
    )
    transfer_tax_rate: float = Field(
        default=0.04, 
        ge=0.0, 
        le=0.10, 
        description="Vagyonszerzési illeték mértéke (alapesetben 4%, CSOK Plusznál 0%)"
    )
    legal_fee_rate: float = Field(
        default=0.01, 
        ge=0.0, 
        le=0.05, 
        description="Ügyvédi és földhivatali bejegyzési díj aránya"
    )

    # Finanszírozás (Hitel)
    down_payment_ratio: float = Field(
        default=0.25, 
        ge=0.10, 
        le=1.00, 
        description="Önerő aránya a vételárhoz képest (MNB szabályozás min. 10-20%)"
    )
    loan_term_years: int = Field(
        default=20, 
        ge=5, 
        le=35, 
        description="Hitel futamideje években"
    )
    loan_interest_rate_annual: float = Field(
        default=0.065, 
        ge=0.0, 
        le=0.25, 
        description="Hitel éves ügyleti kamatlába vagy THM-je (tizedestörtként, pl. 0.065)"
    )

    # Piaci dinamika és növekedési ráták
    property_growth_rate_annual: float = Field(
        default=0.055, 
        ge=-0.10, 
        le=0.30, 
        description="Ingatlan éves várható piaci áremelkedése"
    )
    initial_rent_monthly: float = Field(
        default=270_000.0, 
        ge=30_000.0, 
        le=2_000_000.0, 
        description="Kezdeti havi bérleti díj egy hasonló újépítésű lakásért"
    )
    rent_growth_rate_annual: float = Field(
        default=0.045, 
        ge=-0.05, 
        le=0.25, 
        description="Bérleti díjak éves várható növekedési üteme"
    )

    # Alternatív költség és fenntartás
    opportunity_cost_rate_annual: float = Field(
        default=0.070, 
        ge=0.0, 
        le=0.30, 
        description="Alternatív tőkepiaci befektetés várható éves hozama (pl. PMÁP, ETF)"
    )
    discount_rate_annual: float = Field(
        default=0.060, 
        ge=0.0, 
        le=0.25, 
        description="DCF diszkontráta a nettó jelenérték számításhoz"
    )
    maintenance_rate_annual: float = Field(
        default=0.010, 
        ge=0.0, 
        le=0.06, 
        description="Éves amortizáció és karbantartás az ingatlanérték arányában"
    )
    common_cost_monthly: float = Field(
        default=23_400.0, 
        ge=0.0, 
        le=300_000.0, 
        description="Közös költség és felújítási alap havi összege"
    )
    sale_transaction_fee_rate: float = Field(
        default=0.015, 
        ge=0.0, 
        le=0.08, 
        description="Likvidációs / közvetítői díj az ingatlan későbbi értékesítésekor"
    )
    simulation_years: int = Field(
        default=30, 
        ge=5, 
        le=50, 
        description="A szimulációs horizont hossza években"
    )

    @field_validator("down_payment_ratio")
    @classmethod
    def check_down_payment(cls, v: float) -> float:
        if v < 0.10:
            raise ValueError("Az önerő aránya nem lehet alacsonyabb 10%-nál (MNB HFD rendelet).")
        return v


class SensitivityInputSchema(BaseModel):
    base_params: SimulationInputSchema
    interest_rates: Optional[List[float]] = Field(
        default=[0.045, 0.055, 0.065, 0.075, 0.085, 0.095],
        description="Tesztelendő hitelkamatok listája"
    )
    property_growth_rates: Optional[List[float]] = Field(
        default=[0.020, 0.035, 0.050, 0.065, 0.080, 0.095],
        description="Tesztelendő ingatlan árnövekedési ütemek listája"
    )
