from sme_credit.helpers.config_helper import load_yaml
from sme_credit.helpers.quant_helper import rating_to_pd, map_pd_to_rating

def test_rating_roundtrip():
    bands = load_yaml("config/rating_scale.yaml")["ratings"]
    pd_mid = rating_to_pd("BBB", bands)
    assert map_pd_to_rating(pd_mid, bands) == "BBB"