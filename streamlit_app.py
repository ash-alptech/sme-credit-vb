# streamlit_app.py
from __future__ import annotations
import streamlit as st
from pathlib import Path
import subprocess, sys, time, glob
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR  = PROJECT_ROOT / "input_data"
OUTPUT_DIR = PROJECT_ROOT / "output_data"
CONFIG_DIR = PROJECT_ROOT / "config"
for p in (INPUT_DIR, OUTPUT_DIR, CONFIG_DIR):
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="SME Credit Model", layout="centered")
st.title("SME Credit Model — Batch Scoring UI")

with st.sidebar:
    st.header("Options")
    output_prefix = st.text_input("Output prefix", "sme_scores")
    sector_col    = st.text_input("Sector column name", "sector")
    sheet_name    = st.text_input("Excel sheet name (optional)", "")
    use_utc       = st.checkbox("Use UTC timestamp", True)

st.subheader("1) Upload input data")
input_file = st.file_uploader("Input file (.xlsx or .csv)", type=["xlsx","xlsm","xls","csv"])

st.subheader("2) (Optional) Upload Priors Excel")
priors_file = st.file_uploader("Priors (.xlsx)", type=["xlsx","xlsm","xls"])
st.caption("If uploaded, it's saved as input_data/bayes_3.xlsx (matching your config).")

st.subheader("3) (Optional) Overwrite configs")
c1, c2, c3 = st.columns(3)
with c1: model_cfg_up  = st.file_uploader("model_config.yaml",  ["yaml","yml"])
with c2: rating_cfg_up = st.file_uploader("rating_scale.yaml",  ["yaml","yml"])
with c3: sector_cfg_up = st.file_uploader("sector_config.yaml", ["yaml","yml"])

run_btn = st.button("Run scoring", type="primary")
log_box = st.empty()
out_box = st.container()

def save_uploaded(uploader, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(uploader.getbuffer())
    return dst

def find_latest_csv(prefix: str) -> Path | None:
    files = sorted(OUTPUT_DIR.glob(f"{prefix}_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

if run_btn:
    if not input_file:
        st.error("Please upload an input file first.")
        st.stop()

    # Save input
    ext = Path(input_file.name).suffix.lower() or ".xlsx"
    input_path = INPUT_DIR / f"ui_input_{int(time.time())}{ext}"
    save_uploaded(input_file, input_path)

    # Priors (optional) — save to expected path in your config
    if priors_file:
        save_uploaded(priors_file, INPUT_DIR / "bayes_3.xlsx")

    # Optional config overrides — overwrite existing YAMLs
    if model_cfg_up:  save_uploaded(model_cfg_up,  CONFIG_DIR / "model_config.yaml")
    if rating_cfg_up: save_uploaded(rating_cfg_up, CONFIG_DIR / "rating_scale.yaml")
    if sector_cfg_up: save_uploaded(sector_cfg_up, CONFIG_DIR / "sector_config.yaml")

    # Build command using ONLY flags your current run_scoring.py supports
    cmd = [sys.executable, str(PROJECT_ROOT / "run_scoring.py"),
           "--input", str(input_path),
           "--sector-col", sector_col,
           "--output-prefix", output_prefix]
    if use_utc:
        cmd.append("--use-utc")
    if sheet_name.strip():
        cmd += ["--sheet", sheet_name.strip()]

    log_box.info("Running scoring…")
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)

    # Write a UI log file (since run_scoring.py doesn't create one)
    log_path = OUTPUT_DIR / "ui_run.log"
    with open(log_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write("COMMAND:\n" + " ".join(cmd) + "\n\n")
        f.write("STDOUT:\n" + (proc.stdout or "") + "\n\n")
        f.write("STDERR:\n" + (proc.stderr or "") + "\n")

    with st.expander("stdout"):
        st.code(proc.stdout or "(empty)")
    with st.expander("stderr"):
        st.code(proc.stderr or "(empty)")

    if proc.returncode != 0:
        log_box.error("Scoring failed. See logs above.")
        st.download_button("Download run log", log_path.read_bytes(), file_name="ui_run.log")
        st.stop()

    log_box.success("Scoring complete.")
    scored_csv = find_latest_csv(output_prefix)

    with out_box:
        st.subheader("Results")
        if scored_csv and scored_csv.exists():
            st.write(f"**Scores file:** `{scored_csv.name}`")
            # Preview the CSV
            try:
                df_preview = pd.read_csv(scored_csv)
                st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.warning(f"Preview failed: {e}")
            # Download button
            st.download_button("Download scores CSV", scored_csv.read_bytes(),
                               file_name=scored_csv.name, mime="text/csv")
        else:
            st.warning("Couldn't locate the scores CSV. Check stdout/stderr above.")

        st.download_button("Download run log", log_path.read_bytes(),
                           file_name="ui_run.log", mime="text/plain")
