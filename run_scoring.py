
# python run_scoring.py --input input_data/sample_input.xlsx 
# python .\run_scoring.py --input .\input_data\sample_input.xlsx *> .\output_data\run.log


# From C:\ALP\sme_credit_model
"""
python .\run_scoring.py `
  --input .\input_data\sample_input.xlsx `
  --sheet Sheet1 `
  --sector-col sector `
  --use-utc `
  --output-prefix sme_scores
"""


from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from sme_credit.helpers import load_yaml
from sme_credit.helpers.quant_helper import load_priors
from sme_credit.helpers.io_helper import ensure_dir, make_output_path
from sme_credit.helpers.batch_helper import score_many

def main():
    parser = argparse.ArgumentParser(description="SME Credit PD batch scoring (production-ready).")
    parser.add_argument("--input", default="input_data/sample_input.xlsx", help="Path to input Excel file")
    parser.add_argument("--sheet", default=None, help="Excel sheet name (default: first sheet)")
    parser.add_argument("--sector-col", default="sector", help="Column name for sector")
    parser.add_argument("--use-utc", action="store_true", help="Use UTC time for output timestamp")
    parser.add_argument("--output-prefix", default="scored_output", help="Prefix for output CSV name")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    config_dir   = project_root / "config"
    input_dir    = project_root / "input_data"
    output_dir   = project_root / "output_data"

    model_cfg     = load_yaml(config_dir / "model_config.yaml")
    rating_bands  = load_yaml(config_dir / "rating_scale.yaml")["ratings"]
    sector_curves = load_yaml(config_dir / "sector_config.yaml")["sectors"]

    bayes_file = model_cfg["bayes"]["BAYES_XLSX"]
    bayes_sheet = model_cfg["bayes"]["BAYES_SHEET"]
    bayes_path = Path(bayes_file)
    if not bayes_path.is_absolute():
        bayes_path = project_root / bayes_path

    prior_lookup = load_priors(str(bayes_path), sheet=bayes_sheet)

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = project_root / input_path
    if args.sheet:
        df = pd.read_excel(input_path, sheet_name=args.sheet)
    else:
        df = pd.read_excel(input_path)

    scored_df = score_many(df, args.sector_col, model_cfg, sector_curves, rating_bands, prior_lookup)

    ensure_dir(output_dir)
    out_path = make_output_path(output_dir, args.output_prefix, ext=".csv", use_utc=args.use_utc)
    scored_df.to_csv(out_path, index=False)
    print(f"Scoring complete  {out_path}  (rows: {len(scored_df)})")

if __name__ == "__main__":
    main()
