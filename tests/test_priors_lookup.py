# tests/test_priors_lookup.py
from sme_credit.helpers.quant_helper import get_prior_pd

def test_priors_wildcards():
    lookup = {
        ("*", "*"): 0.05,
        ("*", "Industrials"): 0.03,
        ("UAE", "Banks"): 0.02,
    }
    assert get_prior_pd("UAE", "Banks", lookup) == 0.02
    assert get_prior_pd("INDIA", "Industrials", lookup) == 0.03
    assert get_prior_pd("FRANCE", "Tech", lookup) == 0.05
