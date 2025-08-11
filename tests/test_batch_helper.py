import pandas as pd
from sme_credit.helpers.config_helper import load_yaml
from sme_credit.helpers.quant_helper import load_priors
from sme_credit.helpers.batch_helper import score_many

def test_batch_helper_smoke(tmp_path):
    cfg = load_yaml("config/model_config.yaml")
    sectors = load_yaml("config/sector_config.yaml")["sectors"]
    bands = load_yaml("config/rating_scale.yaml")["ratings"]

    priors_df = pd.DataFrame([{"Country":"UAE","Sector":"Industrials","Prior_PD":0.02}])
    xlsx = tmp_path/"priors.xlsx"
    priors_df.to_excel(xlsx, index=False, sheet_name="Priors")
    lookup = load_priors(str(xlsx), sheet="Priors")

    df = pd.DataFrame([{
        "revenue":10_000_000, "total_assets":20_000_000, "total_liabilities":8_000_000,
        "ebit":1_500_000, "retained_earnings":2_000_000, "working_capital":1_000_000,
        "market_value_equity":12_000_000, "Country":"UAE", "sector":"Industrials"
    }])
    scored, rejects = score_many(df, "sector", cfg, sectors, bands, lookup, validate=True)
    assert len(scored)==1
    assert rejects.empty