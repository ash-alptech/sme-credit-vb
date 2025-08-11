
from __future__ import annotations
from pathlib import Path
import yaml

def load_yaml(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = (Path(__file__).resolve().parents[2] / p).resolve()
    if not p.exists():
        raise FileNotFoundError(f"YAML not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data
