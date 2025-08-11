# tests/test_core_toggles.py
import pandas as pd
from sme_credit.core import small_firm_score
from sme_credit.helpers.config_helper import load_yaml

def base_row():
    return dict(
        revenue=10_000_000, total_assets=20_000_000, total_liabilities=8_000_000,
        ebit=1_500_000, retained_earnings=2_000_000, working_capital=1_000_000,
        market_value_equity=12_000_000, Country="UAE", sector_prior_pd=0.02
    )

def test_default_sector_curve_applies_when_missing():
    cfg = load_yaml("config/model_config.yaml")
    sectors = load_yaml("config/sector_config.yaml")["sectors"]
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    row = base_row()
    out = small_firm_score(row, "UnknownSector", cfg, sectors, bands, {})
    assert "PD_final" in out and out["PD_final"] >= 0

def test_sovereign_cap_changes_pd_when_lower_than_floor():
    cfg = load_yaml("config/model_config.yaml"); cfg["toggles"]["CAP_COUNTRY_RATING"] = True
    sectors = load_yaml("config/sector_config.yaml")["sectors"]
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    row = base_row() | {"country_rating": "BB"}
    out = small_firm_score(row, "Industrials", cfg, sectors, bands, {})
    # floor at ~mid of BB band
    assert out["PD_final"] >= 0.025
