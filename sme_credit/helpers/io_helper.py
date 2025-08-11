
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def timestamp_tag(use_utc: bool = False) -> str:
    dt = datetime.now(timezone.utc) if use_utc else datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S")

def make_output_path(base_dir: str | Path, prefix: str, ext: str = ".csv", use_utc: bool = False) -> Path:
    base = Path(base_dir)
    ensure_dir(base)
    ts = timestamp_tag(use_utc=use_utc)
    return base / f"{prefix}_{ts}{ext}"
