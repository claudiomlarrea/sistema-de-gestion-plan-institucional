"""Carga y normalización del formulario ancho → tabla larga por bloque OG/OE."""
from __future__ import annotations

import pathlib
from typing import Any, Optional

import pandas as pd


def _norm(s: Any) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def _pick_col(columns: list[Any], startswith: str) -> Optional[str]:
    for c in columns:
        if isinstance(c, str) and c.strip().startswith(startswith):
            return c
    return None


def _pick_col_contains(columns: list[Any], needle: str) -> Optional[str]:
    for c in columns:
        if needle in str(c):
            return c
    return None


def _merge_resultado(row: pd.Series, col_obtenidos: Optional[str], col_texo: Optional[str]) -> str:
    a = _norm(row[col_obtenidos]) if col_obtenidos and col_obtenidos in row.index else ""
    b = _norm(row[col_texo]) if col_texo and col_texo in row.index else ""
    return a or b


def wide_to_long(
    df: pd.DataFrame,
    *,
    sheet_used: str = "default",
    origen: str = "google_forms",
) -> pd.DataFrame:
    """Convierte una fila de respuesta ancha en hasta 6 filas (una por bloque OG declarado en el formulario)."""
    cols = list(df.columns)
    email_col = _pick_col(cols, "Dirección de correo") or _pick_col_contains(cols, "correo electrónico")
    ts_col = _pick_col(cols, "Marca temporal")
    year_col = _pick_col(cols, "AÑO") or _pick_col_contains(cols, "AÑO")
    unit_col = _pick_col_contains(cols, "Unidad Académica") or _pick_col_contains(cols, "Unidad")
    punt_col = _pick_col_contains(cols, "Puntuación")

    rows: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        fecha = row[ts_col] if ts_col else pd.NaT
        email = _norm(row[email_col]) if email_col else ""
        try:
            anio = int(row[year_col]) if year_col and pd.notna(row.get(year_col)) else None
        except (TypeError, ValueError):
            anio = None
        unidad = _norm(row[unit_col]) if unit_col else ""
        puntuacion = row[punt_col] if punt_col and punt_col in row.index else None

        for og in range(1, 7):
            oe_c = _pick_col(cols, f"Objetivos específicos {og}")
            act_c = _pick_col(cols, f"Actividades Objetivo {og}")
            det_c = _pick_col_contains(cols, f"Detalle de la Actividad Objetivo {og}")
            res_obt = _pick_col_contains(cols, f"Resultados obtenidos Objetivo {og}")
            res_texo = _pick_col_contains(cols, f"Resultado obtenido (campo de Texo o Numérico) Objetivo {og}")

            if not oe_c:
                continue
            oe = _norm(row[oe_c])
            act = _norm(row[act_c]) if act_c else ""
            det = _norm(row[det_c]) if det_c else ""
            res = _merge_resultado(row, res_obt, res_texo)

            if not (oe or act or det or res):
                continue

            rows.append(
                {
                    "respuesta_id": int(idx) if isinstance(idx, (int, float)) else str(idx),
                    "fecha_carga": fecha,
                    "email": email,
                    "cargado_por": email,
                    "og": og,
                    "oe": oe,
                    "actividad": act,
                    "detalle": det,
                    "resultado": res,
                    "accion": "",
                    "indicador": "",
                    "puntuacion": puntuacion,
                    "anio": anio,
                    "unidad": unidad,
                    "origen": origen,
                    "hoja": sheet_used,
                    "created_at": pd.NaT,
                }
            )

    out = pd.DataFrame(rows)
    if not out.empty and "fecha_carga" in out.columns:
        out["fecha_carga"] = pd.to_datetime(out["fecha_carga"], errors="coerce")
    return out


def load_excel_wide(path: str | pathlib.Path, sheet_name: str = "Respuestas de formulario 1") -> tuple[pd.DataFrame, pd.DataFrame]:
    path = pathlib.Path(path)
    raw = pd.read_excel(path, sheet_name=sheet_name, header=0)
    long_df = wide_to_long(raw, sheet_used=sheet_name, origen="google_forms")
    return raw, long_df


def load_uploaded_excel(file_bytes: bytes, filename: str, sheet_name: str = "Respuestas de formulario 1") -> tuple[pd.DataFrame, pd.DataFrame]:
    import io

    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=0)
    long_df = wide_to_long(raw, sheet_used=sheet_name, origen="google_forms")
    return raw, long_df
