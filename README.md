
# SME Credit Model – Production-Ready Refactor

## What changed
- Inputs now read from `input_data/` and outputs saved to `output_data/` with timestamps.
- Config split into YAML files:
  - `config/model_config.yaml` – weights, toggles, priors file path, Bayes alpha.
  - `config/rating_scale.yaml` – SME rating ↔ PD bands.
  - `config/sector_config.yaml` – sector Z→PD curves.
- Logic modularized:
  - `sme_credit/core.py` – scoring logic.
  - `sme_credit/helpers/config_helper.py` – YAML loader.
  - `sme_credit/helpers/quant_helper.py` – ratings, priors, Bayes alpha helpers.
  - `sme_credit/helpers/batch_helper.py` – batch scoring.
  - `sme_credit/helpers/io_helper.py` – paths & timestamped filenames.
- CLI runner: `python run_scoring.py --input input_data/sample_input.xlsx`

## Setup
1. Put your priors Excel (default `bayes_3.xlsx`) into `input_data/` or update `config/model_config.yaml`.
2. Install deps: `pip install pandas pyyaml openpyxl` (and `xlrd` if needed).
3. Place your input workbook in `input_data/`.
4. Run:
   ```bash
   python run_scoring.py --input input_data/sample_input.xlsx
   ```
   Output: `output_data/scored_output_YYYYMMDD_HHMMSS.csv`
