
from __future__ import annotations
from typing import Dict, Tuple, List
import math
import pandas as pd

def map_pd_to_rating(pd_val: float, rating_bands: List[dict]) -> str:
    for band in rating_bands:
        low = float(band["low"])
        high_raw = band.get("high", None)
        if high_raw is None:
            high = float("inf")
        else:
            try:
                high = float(high_raw)
            except (ValueError, TypeError):
                high = float("inf")
        if low <= pd_val < high:
            return band["label"]
    return "NR"

def rating_to_pd(rating: str, rating_bands: List[dict]) -> float:
    rating = (rating or "").upper().strip()
    for band in rating_bands:
        if band["label"].upper().strip() == rating:
            low = float(band["low"])
            high_raw = band.get("high", None)
            if high_raw is None:
                return low
            try:
                high = float(high_raw)
            except (ValueError, TypeError):
                high = float("inf")
            return (low + high)/2 if math.isfinite(high) else low
    return 1.0

def load_priors(path: str, sheet: str) -> Dict[Tuple[str, str], float]:
    df = pd.read_excel(path, sheet_name=sheet)
    required = {"Country", "Sector", "Prior_PD"}
    if not required.issubset(df.columns):
        raise ValueError(f"Bayes prior file must have columns {required}")
    df["Country"] = df["Country"].str.upper().str.strip()
    df["Sector"]  = df["Sector"].str.strip()
    return { (row.Country, row.Sector): float(row.Prior_PD)
             for row in df.itertuples(index=False) }

def get_prior_pd(country: str, sector: str, lookup: Dict[Tuple[str, str], float], fallback: float = 0.05) -> float:
    country = (country or "").upper().strip()
    sector  = (sector or "").strip()
    return lookup.get((country, sector),
           lookup.get(("*", sector),
           lookup.get(("*", "*"), fallback)))

def get_bayes_alpha(country: str, alpha_by_country: dict, default_alpha: float) -> float:
    country = (country or "").upper().strip()
    gcc_countries = {"UAE", "SAUDI ARABIA", "OMAN", "QATAR", "KUWAIT", "BAHRAIN"}
    if country in gcc_countries and "GCC" in alpha_by_country:
        return float(alpha_by_country["GCC"])
    return float(alpha_by_country.get(country, default_alpha))
