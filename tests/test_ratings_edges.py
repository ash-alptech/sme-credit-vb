# tests/test_ratings_edges.py
from sme_credit.helpers.config_helper import load_yaml
from sme_credit.helpers.quant_helper import rating_to_pd, map_pd_to_rating

def test_rating_edges_roundtrip():
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    mid = rating_to_pd("BBB-", bands)
    assert map_pd_to_rating(mid, bands) == "BBB-"

def test_rating_upper_infinite_band():
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    assert map_pd_to_rating(2.0, bands) == "D"
