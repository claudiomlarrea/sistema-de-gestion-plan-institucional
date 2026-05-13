"""Normalización de filas ingresadas por carga directa en la app."""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Optional

import pandas as pd


def entry_row(
    *,
    unidad: str,
    anio: int,
    og: int,
    oe_texto: str,
    actividad: str,
    detalle: str,
    resultado: str,
    accion: str = "",
    indicador: str = "",
    email: str = "",
    cargado_por: str = "",
) -> dict[str, Any]:
    now = dt.datetime.now()
    return {
        "respuesta_id": f"app-{uuid.uuid4().hex[:12]}",
        "fecha_carga": now,
        "created_at": now,
        "email": email.strip(),
        "cargado_por": cargado_por.strip() or email.strip(),
        "og": int(og),
        "oe": oe_texto.strip(),
        "actividad": actividad.strip(),
        "detalle": detalle.strip(),
        "resultado": resultado.strip(),
        "accion": accion.strip(),
        "indicador": indicador.strip(),
        "anio": int(anio),
        "unidad": unidad.strip(),
        "origen": "app_carga_directa",
        "hoja": "activity_entry",
        "puntuacion": None,
    }


def entries_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def merge_with_forms(long_forms: pd.DataFrame, entries: pd.DataFrame) -> pd.DataFrame:
    if entries is None or entries.empty:
        return long_forms
    if long_forms is None or long_forms.empty:
        return entries
    # Alinear columnas
    all_cols = sorted(set(long_forms.columns) | set(entries.columns))
    a = long_forms.reindex(columns=all_cols)
    b = entries.reindex(columns=all_cols)
    out = pd.concat([a, b], ignore_index=True)
    if "created_at" in out.columns and "fecha_carga" in out.columns:
        fc = pd.to_datetime(out["fecha_carga"], errors="coerce")
        out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")
        out["created_at"] = out["created_at"].fillna(fc)
    return out
