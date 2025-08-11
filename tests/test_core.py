from sme_credit.helpers.config_helper import load_yaml
from sme_credit.core import small_firm_score

def test_small_firm_score_smoke():
    cfg = load_yaml("config/model_config.yaml")
    sectors = load_yaml("config/sector_config.yaml")["sectors"]
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    data = dict(
        revenue=10_000_000, total_assets=20_000_000, total_liabilities=8_000_000,
        ebit=1_500_000, retained_earnings=2_000_000, working_capital=1_000_000,
        market_value_equity=12_000_000, Country="UAE", sector_prior_pd=0.02
    )
    out = small_firm_score(data, "Industrials", cfg, sectors, bands, {})
    assert 0.0 <= out["PD_final"] <= 1.0
    assert "Rating" in out