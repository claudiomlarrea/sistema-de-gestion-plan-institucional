"""Snapshots fechados del consolidado (CSV/Parquet) para auditoría y reproducibilidad."""
from __future__ import annotations

import datetime as dt
import pathlib

import pandas as pd

from pei_gestion.config_loader import project_root


def snapshot_dir() -> pathlib.Path:
    d = project_root() / "data" / "snapshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_snapshot(long_df: pd.DataFrame, label: str = "long", fmt: str = "csv") -> pathlib.Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = snapshot_dir() / f"{label}_{ts}"
    path = base.with_suffix(".csv")
    long_df.to_csv(path, index=False)
    return path


def list_snapshots() -> list[pathlib.Path]:
    d = snapshot_dir()
    if not d.is_dir():
        return []
    return sorted(d.glob("*.csv"))
