# tests/test_batch_validation.py
import pandas as pd
from sme_credit.helpers.batch_helper import score_many
from sme_credit.helpers.config_helper import load_yaml
from sme_credit.helpers.quant_helper import load_priors

def test_rejects_for_bad_rows(tmp_path):
    cfg = load_yaml("config/model_config.yaml")
    sectors = load_yaml("config/sector_config.yaml")["sectors"]
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    # tiny priors file
    xlsx = tmp_path / "p.xlsx"
    pd.DataFrame([{"Country":"*","Sector":"*","Prior_PD":0.05}]).to_excel(xlsx, index=False, sheet_name="Priors")
    lookup = load_priors(str(xlsx), "Priors")
    df = pd.DataFrame([{"revenue":"NaN", "total_assets":0}])  # invalid
    _, rejects = score_many(df, "sector", cfg, sectors, bands, lookup, validate=True)
    assert len(rejects) == 1
    assert "_error" in rejects.columns
