"""Carga YAML de metadatos del plan."""
from __future__ import annotations

import pathlib
from typing import Any

import yaml


def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def load_plan_meta() -> dict[str, Any]:
    p = project_root() / "config" / "plan_meta.yaml"
    if not p.is_file():
        return {"display_name": "PEI", "years_valid": [], "objetivos_generales": {}}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_plan_bundle() -> tuple[dict[str, Any], dict[str, Any], str]:
    """Metadatos sueltos + plan canónico YAML; nombre para UI."""
    meta = load_plan_meta()
    from pei_gestion.canonical_plan import load_canonical_plan

    can = load_canonical_plan()
    name = str(can.get("display_name") or meta.get("display_name") or "PEI UCCuyo")
    return meta, can, name
