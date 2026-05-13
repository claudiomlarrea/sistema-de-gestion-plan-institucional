"""Validación de actividades contra catálogo canónico de OE y unidades."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd
import yaml

from pei_gestion.canonical_plan import find_oe_by_text, load_canonical_plan
from pei_gestion.config_loader import project_root


def load_units_config() -> dict[str, Any]:
    p = project_root() / "config" / "units.yaml"
    if not p.is_file():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def normalize_unidad(s: str, alias: dict[str, str]) -> str:
    s = (s or "").strip()
    return alias.get(s, s)


def validate_long_df(long_df: pd.DataFrame, plan: dict[str, Any] | None = None) -> pd.DataFrame:
    plan = plan or load_canonical_plan()
    units_cfg = load_units_config()
    alias = dict(units_cfg.get("alias") or {})
    known_units = set(units_cfg.get("unidades_observadas") or [])

    out = long_df.copy()
    out["unidad_norm"] = out["unidad"].map(lambda x: normalize_unidad(str(x), alias))

    def _oe_row(row: pd.Series) -> pd.Series:
        og = int(row["og"])
        oe_txt = str(row.get("oe", "")).strip()
        hit = find_oe_by_text(plan, og, oe_txt) if plan else None
        return pd.Series(
            {"oe_en_catalogo": bool(hit), "oe_id_canonico": str(hit.get("id", "")) if hit else ""}
        )

    flags = out.apply(_oe_row, axis=1)
    out["oe_en_catalogo"] = flags["oe_en_catalogo"]
    out["oe_id_canonico"] = flags["oe_id_canonico"]

    out["unidad_catalogada"] = out["unidad_norm"].map(lambda u: u in known_units if known_units else True)
    out["texto_generico"] = out.apply(
        lambda r: _generic_text(r.get("actividad", ""), r.get("detalle", ""), r.get("resultado", "")),
        axis=1,
    )
    return out


def _generic_text(a: Any, d: Any, res: Any) -> bool:
    blob = f"{a} {d} {res}".lower().strip()
    if len(blob) < 2:
        return True
    if blob in {"-", ".", "n/a", "na", "sin datos", "s/d"}:
        return True
    return False


def word_count_es(s: str) -> int:
    return len(re.findall(r"\S+", str(s)))
