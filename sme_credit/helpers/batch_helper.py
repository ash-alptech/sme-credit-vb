from __future__ import annotations
import pandas as pd
from typing import Union, Tuple

# keep relative imports (works when package is run with -m or installed in editable mode)
from ..core import small_firm_score
from .quant_helper import get_prior_pd


def score_many(
    df_or_list: Union[pd.DataFrame, list],
    sector_col: str,
    cfg: dict,
    sector_curves: dict,
    rating_bands: list,
    prior_lookup: dict,
    validate: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Batch-score rows. If validate=True, returns (scored_df, rejects_df),
    otherwise returns scored_df only.
    """
    df = pd.DataFrame(df_or_list) if isinstance(df_or_list, list) else df_or_list.copy()

    # lightweight schema for validation (no extra deps)
    required_numeric = [
        "revenue",
        "total_assets",
        "total_liabilities",
        "ebit",
        "retained_earnings",
        "working_capital",
        "market_value_equity",
    ]

    def _is_number(x) -> bool:
        try:
            return pd.notna(x) and float(x) == float(x)
        except Exception:
            return False

    defaults = {
        "trade_credit": 0.5,
        "utility_pay": 0.5,
        "bank_tx": 0.5,
        "tax_compliance": 0.5,
        "digital_footprint": 0.5,
        "fcf_vol_ratio": 0.2,
        "cf_int_cov": 2.0,
        "revenue_quality": 0.5,
        "business_age_years": 6,
        "mgmt_track_record": 0.5,
        "industry_survival_rate": 0.5,
        "geo_risk": 0.5,
    }

    records = []
    rejects = []

    for _, row in df.iterrows():
        # --- optional validation ---
        if validate:
            missing_or_bad = [c for c in required_numeric if not _is_number(row.get(c))]
            errs = []
            if missing_or_bad:
                errs.append(f"non-numeric/NaN: {missing_or_bad}")
            ta = row.get("total_assets", 0)
            try:
                if float(ta) == 0:
                    errs.append("total_assets==0")
            except Exception:
                errs.append("total_assets not numeric")
            if errs:
                reject = row.to_dict()
                reject["_error"] = "; ".join(errs)
                rejects.append(reject)
                continue

        # --- scoring path ---
        sector = row.get(sector_col, "Industrials")
        country = (row.get("Country", "") or "").upper().strip()
        prior = get_prior_pd(country, sector, prior_lookup)
        data = {**defaults, **row.to_dict(), "sector_prior_pd": prior}
        rec = {
            **row,
            **small_firm_score(data, sector, cfg, sector_curves, rating_bands, prior_lookup),
        }
        records.append(rec)

    scored_df = pd.DataFrame(records)
    if validate:
        rejects_df = pd.DataFrame(rejects)
        return scored_df, rejects_df
    return scored_df
