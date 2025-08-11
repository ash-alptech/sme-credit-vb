# app.py
from __future__ import annotations
import streamlit as st
from pathlib import Path
import subprocess, sys, time
import pandas as pd
import io, yaml

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parent
INPUT_DIR  = ROOT / "input_data"
OUTPUT_DIR = ROOT / "output_data"
CONFIG_DIR = ROOT / "config"
for p in (INPUT_DIR, OUTPUT_DIR, CONFIG_DIR):
    p.mkdir(parents=True, exist_ok=True)

# Sidebar logo only (optional)
_LOGO_PATHS = [ROOT / "alp.jpg", ROOT / "assets" / "alp.jpg"]
LOGO_PATH = next((p for p in _LOGO_PATHS if p.exists()), None)

# ---------- Page setup ----------
st.set_page_config(
    page_title="SME Credit Model",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=str(LOGO_PATH) if LOGO_PATH else None,
)
if LOGO_PATH:
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)

st.sidebar.header("Run options")
output_prefix = st.sidebar.text_input("Output prefix", "sme_scores")
sheet_name    = st.sidebar.text_input("Excel sheet (optional)", "")
use_utc       = st.sidebar.checkbox("Use UTC timestamp", True)

# Show detected sector column in the sidebar if available
if "sector_col" in st.session_state and st.session_state["sector_col"]:
    st.sidebar.success(f"Sector column: {st.session_state['sector_col']}")

UI_LOG = OUTPUT_DIR / "ui_run.log"

# ---------- Helpers ----------
def save_uploaded(uploader, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(uploader.getbuffer())
    return dst

def latest_outputs(prefix: str | None = None) -> list[Path]:
    files = sorted(OUTPUT_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [f for f in files if (not prefix or f.name.startswith(prefix))]

def build_cmd(input_path: Path, sector_col: str) -> list[str]:
    cmd = [sys.executable, str(ROOT / "run_scoring.py"),
           "--input", str(input_path),
           "--sector-col", sector_col,
           "--output-prefix", output_prefix]
    if use_utc:
        cmd.append("--use-utc")
    if sheet_name.strip():
        cmd += ["--sheet", sheet_name.strip()]
    return cmd

def read_uploaded_df(uploaded, sheet_name: str | None):
    """Read a small preview DataFrame from the uploaded file buffer (no saving)."""
    name = uploaded.name.lower()
    uploaded.seek(0)
    if name.endswith(".csv") or name.endswith(".txt"):
        return pd.read_csv(uploaded)
    # Excel
    return pd.read_excel(uploaded, sheet_name=(sheet_name or 0))

def detect_sector_column(df: pd.DataFrame, sector_names: set[str]) -> tuple[str | None, list[str]]:
    """Return (best_guess, candidate_columns)."""
    candidates = [c for c in df.columns if df[c].dtype == "object" or pd.api.types.is_string_dtype(df[c])]
    if not candidates:
        return None, []
    # score by % of values that match known sector names
    best, best_score = None, -1.0
    for c in candidates:
        s = df[c].dropna().astype(str).str.strip()
        match_ratio = (s.isin(sector_names)).mean() if len(s) else 0.0
        if match_ratio > best_score:
            best, best_score = c, match_ratio
    return best, candidates

# Load known sector names from config (for better detection)
try:
    with open(CONFIG_DIR / "sector_config.yaml", "r", encoding="utf-8") as f:
        sectors_yaml = yaml.safe_load(f) or {}
    KNOWN_SECTORS = set((sectors_yaml.get("sectors") or {}).keys())
except Exception:
    KNOWN_SECTORS = set()

# ---------- Tabs ----------
tabs = st.tabs(["Run Scoring", "Results", "Logs"])
tab_run, tab_results, tab_logs = tabs

# ---------- RUN SCORING ----------
with tab_run:
    st.subheader("Upload & Detect Sector Column")

    colA, colB = st.columns([2, 1], gap="large")
    with colA:
        input_file  = st.file_uploader("Input file (.xlsx / .csv)", type=["xlsx","xlsm","xls","csv"])
        priors_file = st.file_uploader("Priors (.xlsx) — saved as input_data/bayes_3.xlsx", type=["xlsx","xlsm","xls"])
    with colB:
        st.caption("Optional: overwrite configs")
        model_cfg_up  = st.file_uploader("model_config.yaml",  ["yaml","yml"], key="m1")
        rating_cfg_up = st.file_uploader("rating_scale.yaml",  ["yaml","yml"], key="m2")
        sector_cfg_up = st.file_uploader("sector_config.yaml", ["yaml","yml"], key="m3")

    sector_col_selected = st.session_state.get("sector_col", "")

    # If file uploaded, detect sector column and show dropdowns
    if input_file is not None:
        try:
            df_preview = read_uploaded_df(input_file, sheet_name if sheet_name.strip() else None)
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")
            df_preview = None

        if df_preview is not None and len(df_preview.columns) > 0:
            best, candidates = detect_sector_column(df_preview, KNOWN_SECTORS)
            # If we already chose one in this session, keep it; else use best guess
            if not sector_col_selected:
                sector_col_selected = best or (candidates[0] if candidates else "")

            st.markdown("**Select sector column (auto-detected):**")
            sector_col_selected = st.selectbox(
                "Sector column",
                options=candidates or list(df_preview.columns),
                index=(candidates or list(df_preview.columns)).index(sector_col_selected)
                if sector_col_selected in (candidates or list(df_preview.columns)) else 0,
                key="sector_col_select",
            )

            # Show distinct sector values (from the chosen column)
            try:
                distinct_vals = (
                    df_preview[sector_col_selected]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .value_counts()
                    .reset_index()
                )
                distinct_vals.columns = [sector_col_selected, "count"]
                st.caption("Distinct sector values found (top 50):")
                st.dataframe(distinct_vals.head(50), use_container_width=True)
                # Also a dropdown to inspect a single sector value if you want to confirm
                _ = st.selectbox(
                    "Preview a sector value",
                    options=list(distinct_vals[sector_col_selected].head(50)),
                    help="Selection is for preview only; scoring uses each row's sector value.",
                )
            except Exception as e:
                st.warning(f"Could not summarize sector values: {e}")

    # Small run button
    go = st.button("Run scoring", type="primary")
    status = st.empty()

    if go:
        if not input_file:
            st.error("Please upload an input file first.")
        elif not sector_col_selected:
            st.error("Please select the sector column.")
        else:
            # Save to disk with timestamped name
            ext = Path(input_file.name).suffix.lower() or ".xlsx"
            input_path = INPUT_DIR / f"ui_input_{int(time.time())}{ext}"
            save_uploaded(input_file, input_path)

            if priors_file:
                save_uploaded(priors_file, INPUT_DIR / "bayes_3.xlsx")
            if model_cfg_up:  save_uploaded(model_cfg_up,  CONFIG_DIR / "model_config.yaml")
            if rating_cfg_up: save_uploaded(rating_cfg_up, CONFIG_DIR / "rating_scale.yaml")
            if sector_cfg_up: save_uploaded(sector_cfg_up, CONFIG_DIR / "sector_config.yaml")

            # Remember selection for later tabs + sidebar
            st.session_state["sector_col"] = sector_col_selected

            # Run scorer
            cmd = build_cmd(input_path, sector_col_selected)
            status.info("Running scoring…")
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)

            with open(UI_LOG, "w", encoding="utf-8", errors="ignore") as f:
                f.write("COMMAND:\n" + " ".join(cmd) + "\n\n")
                f.write("STDOUT:\n" + (proc.stdout or "") + "\n\n")
                f.write("STDERR:\n" + (proc.stderr or "") + "\n")

            if proc.returncode != 0:
                status.error("Scoring failed. See Logs tab for details.")
            else:
                status.success("Scoring complete. See the Results tab.")
                st.session_state["last_prefix"] = output_prefix

# ---------- RESULTS ----------
with tab_results:
    st.subheader("Results")
    default_prefix = st.session_state.get("last_prefix", output_prefix)
    cols = st.columns([2,1,1])
    with cols[0]:
        prefix_filter = st.text_input("Filter by output prefix", default_prefix)
    with cols[1]:
        max_rows = st.number_input("Rows to show", 10, 200000, 200, step=50)
    with cols[2]:
        show_index = st.checkbox("Show index", False)

    files = latest_outputs(prefix_filter.strip() or None)
    if not files:
        st.info("No output CSVs found yet. Run a job in the Run Scoring tab.")
    else:
        names = [f.name for f in files]
        selected_name = st.selectbox("Choose an output file", names, index=0)
        selected = next(f for f in files if f.name == selected_name)

        try:
            df = pd.read_csv(selected)
            rows = min(len(df), int(max_rows))
            view = df.head(rows)
            if not show_index:
                view = view.reset_index(drop=True)

            st.caption(f"Showing {rows} of {len(df)} rows · {df.shape[1]} columns · file: `{selected.name}`")
            st.dataframe(view, use_container_width=True, height=min(900, 40 + 28 * min(rows, 25)))
        except Exception as e:
            st.error(f"Could not load CSV: {e}")

# ---------- LOGS ----------
with tab_logs:
    st.subheader("UI run log")
    if UI_LOG.exists():
        st.code(UI_LOG.read_text(encoding="utf-8", errors="ignore"), language="bash")
        st.download_button("Download log", UI_LOG.read_bytes(), file_name="ui_run.log", mime="text/plain")
    else:
        st.caption("No UI log yet. Run a job in the Run Scoring tab.")
