from __future__ import annotations
import math
from .helpers.quant_helper import map_pd_to_rating, rating_to_pd, get_bayes_alpha

def small_firm_score(data: dict,
                     sector: str,
                     cfg: dict,
                     sector_curves: dict,
                     rating_bands: list,
                     prior_lookup: dict) -> dict:
    # Weights & toggles
    W_X1 = cfg["weights"]["W_X1"]; W_X2 = cfg["weights"]["W_X2"]
    W_X3 = cfg["weights"]["W_X3"]; W_X4 = cfg["weights"]["W_X4"]; W_X5 = cfg["weights"]["W_X5"]
    ALT_WT = cfg["overlays"]["ALT_WT"]
    CF_FCF = cfg["overlays"]["CF_FCF"]; CF_IC = cfg["overlays"]["CF_IC"]; CF_RQ = cfg["overlays"]["CF_RQ"]
    AGE_PEN_LT3 = cfg["overlays"]["AGE_PEN_LT3"]; AGE_PEN_3_5 = cfg["overlays"]["AGE_PEN_3_5"]
    QUAL_WT = cfg["overlays"]["QUAL_WT"]
    SCALE_PEN = cfg["penalties"]["SCALE_PEN"]; LOW_LEV_PEN = cfg["penalties"]["LOW_LEV_PEN"]
    MV_CAP = cfg["limits"]["MV_CAP"]
    CAP_COUNTRY_RATING = cfg["toggles"]["CAP_COUNTRY_RATING"]
    USE_BAYES_PRIOR = cfg["toggles"]["USE_BAYES_PRIOR"]
    default_bayes_alpha = cfg["bayes"]["DEFAULT_BAYES_ALPHA"]
    alpha_by_country     = cfg["bayes"]["BAYES_ALPHA_BY_COUNTRY"]

    # Financial ratios
    X1 = data["working_capital"]     / data["total_assets"]
    X2 = data["retained_earnings"]   / data["total_assets"]
    X3 = data["ebit"]                / data["total_assets"]
    X4 = min(data["market_value_equity"] / data["total_liabilities"], MV_CAP)
    X5 = data["revenue"]             / data["total_assets"]

    z_raw = (W_X1*X1 + W_X2*X2 + W_X3*X3 + W_X4*X4 + W_X5*X5)

    # Alternative-data overlay
    alt_keys = ["trade_credit","utility_pay","bank_tx","tax_compliance","digital_footprint"]
    alt_mean = sum(data.get(k,0.5) for k in alt_keys)/len(alt_keys)
    alt_adj  = ALT_WT * (alt_mean - 0.5)

    # Cash-flow overlay
    cf_adj = (CF_FCF * data.get("fcf_vol_ratio",0.2) +
              CF_IC  * math.log1p(data.get("cf_int_cov",2.0)) +
              CF_RQ  * (data.get("revenue_quality",0.5)-0.5))

    # Qualitative overlay
    age = data.get("business_age_years",6)
    age_pen = AGE_PEN_LT3 if age < 3 else AGE_PEN_3_5 if age < 5 else 0
    qual_adj = (age_pen +
                QUAL_WT*(data.get("mgmt_track_record",0.5)-0.5) +
                QUAL_WT*(data.get("industry_survival_rate",0.5)-0.5) -
                QUAL_WT*data.get("geo_risk",0.5))

    # Penalties
    scale_pen = SCALE_PEN if data["revenue"] < 5_000_000 else 0
    lev_pen   = LOW_LEV_PEN if (data["total_liabilities"]/data["total_assets"] > 0.5) else 0

    z_adj = z_raw + alt_adj + cf_adj + qual_adj + scale_pen + lev_pen

    # Sector Z→PD
    curve = sector_curves.get(sector, {"slope":0.0000223,"int":0.001})
    pd_model = max(0.0, curve["slope"]*z_adj + curve["int"])

    # Bayesian blend
    country = (data.get("Country", "") or "").upper().strip()
    prior_pd = data["sector_prior_pd"]
    bayes_alpha = get_bayes_alpha(country, alpha_by_country, default_bayes_alpha)

    if USE_BAYES_PRIOR:
        pd_final = ((1 - bayes_alpha) * pd_model + bayes_alpha * prior_pd)
    else:
        pd_final = pd_model

    # Sovereign floor
    if CAP_COUNTRY_RATING:
        ctry_rating = data.get("Country Rating") or data.get("country_rating")
        if ctry_rating:
            pd_final = max(pd_final, rating_to_pd(ctry_rating, rating_bands))

    return {
        "X1":X1,"X2":X2,"X3":X3,"X4":X4,"X5":X5,
        "Z_raw":z_raw,"alt_adj":alt_adj,"cf_adj":cf_adj,
        "qual_adj":qual_adj,"scale_pen":scale_pen,"lev_pen":lev_pen,
        "Z_adj":z_adj,"PD_model":pd_model,"PD_final":pd_final,
        "Rating":map_pd_to_rating(pd_final, rating_bands)
    }
