"""Filtros y tablas descriptivas simples."""
from __future__ import annotations

from datetime import date

import pandas as pd


def filter_long(
    long_df: pd.DataFrame,
    *,
    unidades: list[str] | None = None,
    anios: list[int] | None = None,
    ogs: list[int] | None = None,
    origenes: list[str] | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> pd.DataFrame:
    df = long_df.copy()
    if unidades:
        df = df[df["unidad"].isin(unidades)]
    if anios:
        df = df[df["anio"].isin(anios)]
    if ogs:
        df = df[df["og"].isin(ogs)]
    if origenes and "origen" in df.columns:
        df = df[df["origen"].isin(origenes)]
    if fecha_desde is not None and "fecha_carga" in df.columns:
        ts = pd.to_datetime(df["fecha_carga"], errors="coerce")
        df = df[ts.dt.date >= fecha_desde]
    if fecha_hasta is not None and "fecha_carga" in df.columns:
        ts = pd.to_datetime(df["fecha_carga"], errors="coerce")
        df = df[ts.dt.date <= fecha_hasta]
    return df


def describe_text_fields(df: pd.DataFrame) -> dict[str, int]:
    if df.empty:
        return {"n_filas": 0, "n_emails_distintos": 0, "n_unidades_distintas": 0}
    return {
        "n_filas": int(len(df)),
        "n_emails_distintos": int(df["email"].nunique()) if "email" in df.columns else 0,
        "n_unidades_distintas": int(df["unidad"].nunique()) if "unidad" in df.columns else 0,
    }
