# SME Credit Model — Production Scaffold

An SME Probability of Default (PD) batch scorer with clean configs, timestamped outputs, and a lightweight UI.  
Your original scorer (`run_scoring.py`) stays unchanged; the UI simply executes it.

---

## Project layout

```
sme_credit_model/
├─ run_scoring.py                # ← original CLI (unchanged interface)
├─ streamlit_app.py              # ← simple UI wrapper (no code changes to scorer)
├─ sme_credit/
│  ├─ core.py
│  └─ helpers/
│     ├─ batch_helper.py
│     ├─ config_helper.py
│     ├─ io_helper.py
│     ├─ logging_helper.py
│     └─ quant_helper.py
├─ config/
│  ├─ model_config.yaml          # weights/toggles & priors path/sheet
│  ├─ rating_scale.yaml          # rating ↔ PD bands
│  └─ sector_config.yaml         # sector Z→PD curves
├─ input_data/                   # input Excel/CSV; priors xlsx
└─ output_data/                  # timestamped results (and UI log)
```

---

## Requirements

```
pandas>=1.5.0
PyYAML>=6.0
openpyxl>=3.0.10
xlrd>=2.0.1
pytest>=7.4.0
pytest-cov>=4.1.0
streamlit>=1.30.0
```

Install:

```powershell
# from the project root
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements.txt
```

(Optional for local imports / tests)
```powershell
pip install -e .
```

---

## Running the scorer (CLI)

Supported flags in `run_scoring.py`:  
`--input`, `--sheet`, `--sector-col`, `--use-utc`, `--output-prefix`

**Example (PowerShell):**
```powershell
python .\run_scoring.py `
  --input .\input_data\sample_input.xlsx `
  --sheet Sheet1 `
  --sector-col sector `
  --use-utc `
  --output-prefix sme_scores
```

**Output:**  
`output_data/sme_scores_YYYYMMDD_HHMMSS.csv`

**Create a log file without changing code (redirect stdout/stderr):**
```powershell
python .\run_scoring.py --input .\input_data\sample_input.xlsx *> .\output_data\run.log
```

### Notes
- **Priors Excel** path/sheet comes from `config/model_config.yaml`:
  - `bayes.BAYES_XLSX` (e.g., `input_data/bayes_3.xlsx`)
  - `bayes.BAYES_SHEET` (e.g., `Priors`)
- **Required columns** in input:
  - `revenue, total_assets, total_liabilities, ebit, retained_earnings, working_capital, market_value_equity, Country, sector`
- **Timestamps:** add `--use-utc` to timestamp outputs in UTC.

---

## Streamlit UI (no code changes to the scorer)

The UI saves your uploads into `input_data/` / `config/`, then calls `run_scoring.py` with the supported flags.  
It also writes a UI log and previews the result CSV.

Run the UI:
```powershell
streamlit run streamlit_app.py
```

In the app:
1. Upload your input `.xlsx`/`.csv`
2. (Optional) Upload priors `.xlsx` — saved as `input_data/bayes_3.xlsx` so it matches the config
3. (Optional) Upload custom YAMLs to overwrite config files
4. Set output prefix / sector column / sheet (sidebar)
5. Click **Run scoring**
6. Download:
   - **Scores CSV** (shown in-page)
   - **UI run log** → `output_data/ui_run.log`
   - **Run metadata JSON** (if present alongside CSV)

---

## Configs

- `config/model_config.yaml`
  - Financial ratio weights & overlays
  - Toggles: `CAP_COUNTRY_RATING`, `USE_BAYES_PRIOR`
  - Priors file & sheet
  - Bayes alpha per country/GCC + default
- `config/rating_scale.yaml`
  - Ordered rating bands with `label`, `low`, `high` (PD)
- `config/sector_config.yaml`
  - Z→PD curve `{slope, int}` per sector
  - Fallback to default curve if sector missing

---

## Tests

Run the suite:
```powershell
pytest -q
# or with coverage:
pytest --cov=sme_credit --cov-report=term-missing
```

---

## Troubleshooting

**UnicodeEncodeError** on Windows console (fancy arrows/characters):
- Quick fix for the session:
  ```powershell
  $env:PYTHONUTF8="1"
  ```
  or run with `python -X utf8 ...`
- Or change the final print in `run_scoring.py` to ASCII (`->` instead of `→`).

**Editable install error: multiple top-level packages**  
Use the provided `pyproject.toml` (limits discovery to `sme_credit*`), or avoid `-e`.

---

## Example end-to-end (PowerShell)

```powershell
. .venv\Scripts\activate
pip install -r requirements.txt

# Run CLI
python .\run_scoring.py `
  --input .\input_data\sample_input.xlsx `
  --sheet Sheet1 `
  --sector-col sector `
  --use-utc `
  --output-prefix sme_scores `
  *> .\output_data\run.log

# Or launch the UI
streamlit run streamlit_app.py
```

---

## What’s “production-ready” here

- Clear separation of **code** (package), **configs** (YAML), and **data** (input/output)
- Stable CLI for batch runs
- Timestamped outputs for traceability
- Lightweight **UI** for upload → run → preview → download — without changing your existing scorer
