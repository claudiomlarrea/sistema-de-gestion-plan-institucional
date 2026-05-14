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


# --- Etiquetas de columnas para la UI (Streamlit); nombres internos no cambian. ---

DISPLAY_COLUMN_LABELS_ES: dict[str, str] = {
    "respuesta_id": "ID del envío (respuesta)",
    "email": "Correo del respondiente",
    "cargado_por": "Usuario que cargó el dato",
    "og": "Objetivo general del PEI (número 1 a 6)",
    "oe": "Objetivo específico (texto del formulario)",
    "actividad": "Actividad",
    "detalle": "Detalle",
    "resultado": "Resultado",
    "accion": "Acción (plan PEI)",
    "indicador": "Indicador (plan PEI)",
    "puntuacion": "Puntuación (formulario)",
    "anio": "Año",
    "unidad": "Unidad Académica",
    "origen": "Origen (formulario o app)",
    "hoja": "Hoja de Excel de origen",
    "fecha_carga": "Fecha y hora de envío (Forms)",
    "created_at": "Fecha de registro en la app",
    "unidad_norm": "Unidad Académica (normalizada)",
    "oe_en_catalogo": "OE reconocido en plan oficial",
    "oe_id_canonico": "Código OE en plan oficial",
    "unidad_catalogada": "Unidad Académica en listado institucional",
    "texto_generico": "Texto genérico o muy breve (alerta)",
    "polaridad_lexica": "Polaridad léxica (exploratorio)",
    "falta_actividad": "Falta actividad",
    "falta_detalle": "Falta detalle",
    "falta_resultado": "Falta resultado",
    "falta_oe": "Falta objetivo específico",
    "n_actividades": "Cantidad de actividades",
    "n_bloques": "Cantidad de actividades registradas",
    "oe_id": "Código OE",
    "resumen_oe": "Resumen del OE (plan)",
    "acciones_en_yaml": "Acciones definidas en plan (YAML)",
    "n_forms": "Actividades desde formulario",
    "n_app": "Actividades desde app",
    "nota": "Nota",
    "oe_id": "Código OE (plan)",
    "accion_id": "Código acción (plan)",
    "indicador_id": "Código indicador (plan)",
}


def dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Copia del DataFrame con encabezados renombrados solo para visualización."""
    if df is None or df.empty:
        return df
    ren = {c: DISPLAY_COLUMN_LABELS_ES[c] for c in df.columns if c in DISPLAY_COLUMN_LABELS_ES}
    return df.rename(columns=ren)
