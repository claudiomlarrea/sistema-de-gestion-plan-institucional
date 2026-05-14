"""Carga del plan canónico (OG → OE → acciones → indicadores) desde YAML versionado."""
from __future__ import annotations

import copy
import pathlib
from typing import Any, Optional

import yaml

from pei_gestion.config_loader import project_root


def default_plan_path() -> pathlib.Path:
    return project_root() / "config" / "plan_2023_2027.yaml"


def load_canonical_plan(path: Optional[pathlib.Path] = None) -> dict[str, Any]:
    p = path or default_plan_path()
    if not p.is_file():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def iter_og(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return list(plan.get("objetivos") or [])


def find_og(plan: dict[str, Any], numero: int) -> Optional[dict[str, Any]]:
    for o in iter_og(plan):
        if int(o.get("numero", -1)) == int(numero):
            return o
    return None


def list_oe_for_og(plan: dict[str, Any], og_num: int) -> list[dict[str, Any]]:
    og = find_og(plan, og_num)
    if not og:
        return []
    return list(og.get("objetivos_especificos") or [])


def find_oe_by_text(plan: dict[str, Any], og_num: int, texto: str) -> Optional[dict[str, Any]]:
    t = (texto or "").strip()
    for oe in list_oe_for_og(plan, og_num):
        if (oe.get("texto") or "").strip() == t:
            return oe
    return None


def find_oe_by_id(plan: dict[str, Any], og_num: int, oe_id: str) -> Optional[dict[str, Any]]:
    oid = (oe_id or "").strip()
    for oe in list_oe_for_og(plan, og_num):
        if str(oe.get("id", "")).strip() == oid:
            return oe
    return None


def acciones_overrides_path() -> pathlib.Path:
    return project_root() / "config" / "plan_acciones_overrides.yaml"


def load_acciones_overrides(path: Optional[pathlib.Path] = None) -> dict[str, Any]:
    """YAML opcional con clave `por_oe`: { OE_ID: [ { id, texto, indicadores: [...] }, ... ] }."""
    p = path or acciones_overrides_path()
    if not p.is_file():
        return {}
    with p.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return raw if isinstance(raw, dict) else {}


def plan_with_merged_acciones(plan: dict[str, Any], overrides: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Copia profunda del plan; sustituye `acciones` de cada OE si hay entrada en overrides."""
    out = copy.deepcopy(plan)
    ov = overrides if overrides is not None else load_acciones_overrides()
    if not ov:
        return out
    por_oe = ov.get("por_oe") if isinstance(ov.get("por_oe"), dict) else ov
    for og in iter_og(out):
        for oe in og.get("objetivos_especificos") or []:
            oid = str(oe.get("id", ""))
            block = por_oe.get(oid)
            if isinstance(block, list) and len(block) > 0:
                oe["acciones"] = copy.deepcopy(block)
    return out


def list_acciones(oe: dict[str, Any]) -> list[dict[str, Any]]:
    return list(oe.get("acciones") or [])


def list_indicadores(accion: dict[str, Any]) -> list[dict[str, Any]]:
    return list(accion.get("indicadores") or [])


def flatten_acciones_indicadores(plan: dict[str, Any]) -> list[tuple[str, str, str, str, str]]:
    """Tuplas (og_id, oe_id, oe_texto, accion_id, indicador_id) para matrices Capa B/C."""
    rows: list[tuple[str, str, str, str, str]] = []
    for og in iter_og(plan):
        og_n = int(og["numero"])
        for oe in list_oe_for_og(plan, og_n):
            oe_id = str(oe.get("id", ""))
            accs = list_acciones(oe)
            if not accs:
                rows.append((f"OG{og_n}", oe_id, str(oe.get("texto", "")), "", ""))
                continue
            for ac in accs:
                aid = str(ac.get("id", ""))
                inds = list_indicadores(ac)
                if not inds:
                    rows.append((f"OG{og_n}", oe_id, str(oe.get("texto", "")), aid, ""))
                    continue
                for ind in inds:
                    rows.append(
                        (f"OG{og_n}", oe_id, str(oe.get("texto", "")), aid, str(ind.get("id", "")))
                    )
    return rows
