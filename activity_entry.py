"""Normalización de filas ingresadas por carga directa en la app."""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Optional

import pandas as pd

# Columnas de la hoja Google Sheets «Actividades_app» (mismo orden al escribir encabezado y filas).
SHEET_ACTIVIDADES_APP_COLUMNS: tuple[str, ...] = (
    "respuesta_id",
    "fecha_carga",
    "created_at",
    "email",
    "cargado_por",
    "og",
    "oe",
    "actividad",
    "detalle",
    "resultado",
    "accion",
    "indicador",
    "anio",
    "unidad",
    "origen",
    "hoja",
    "puntuacion",
    "oe_id",
    "accion_id",
    "indicador_id",
)


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
    oe_id: str = "",
    accion_id: str = "",
    indicador_id: str = "",
) -> dict[str, Any]:
    now = dt.datetime.now()
    row: dict[str, Any] = {
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
    if oe_id.strip():
        row["oe_id"] = oe_id.strip()
    if accion_id.strip():
        row["accion_id"] = accion_id.strip()
    if indicador_id.strip():
        row["indicador_id"] = indicador_id.strip()
    return row


def entries_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def sheet_dataframe_to_entry_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convierte la hoja «Actividades_app» (DataFrame) en filas compatibles con `merge_with_forms`."""
    if df is None or df.empty:
        return []
    out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        d: dict[str, Any] = {}
        for c in SHEET_ACTIVIDADES_APP_COLUMNS:
            if c not in df.columns:
                continue
            v = r[c]
            if pd.isna(v):
                v = None
            d[c] = v
        if "og" in d and d["og"] is not None and str(d["og"]).strip() != "":
            try:
                d["og"] = int(float(str(d["og"]).replace(",", ".")))
            except (TypeError, ValueError):
                d["og"] = 0
        if "anio" in d and d["anio"] is not None and str(d["anio"]).strip() != "":
            try:
                d["anio"] = int(float(str(d["anio"]).replace(",", ".")))
            except (TypeError, ValueError):
                d["anio"] = None
        for ts in ("fecha_carga", "created_at"):
            if ts in d and d[ts] is not None and str(d[ts]).strip() != "":
                d[ts] = pd.to_datetime(d[ts], errors="coerce")
        for s in ("email", "cargado_por", "oe", "actividad", "detalle", "resultado", "accion", "indicador", "unidad", "origen", "hoja"):
            if s in d and d[s] is not None:
                d[s] = str(d[s]).strip()
        for oid in ("oe_id", "accion_id", "indicador_id"):
            if oid in d and (d[oid] is None or str(d[oid]).strip() == ""):
                d.pop(oid, None)
        if d.get("respuesta_id"):
            if not d.get("origen"):
                d["origen"] = "app_carga_directa"
            if not d.get("hoja"):
                d["hoja"] = "activity_entry"
            out.append(d)
    return out


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
