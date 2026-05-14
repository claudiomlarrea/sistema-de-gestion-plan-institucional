"""Métricas de seguimiento: Capa A (Forms), B (acciones YAML vs evidencia), C (meta-KPIs)."""
from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from pei_gestion.canonical_plan import iter_og, list_acciones, list_oe_for_og


def summary_by_unit_year(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    g = long_df.groupby(["unidad", "anio"], dropna=False).size().reset_index(name="n_actividades")
    return g.sort_values(["anio", "unidad"])


def summary_by_year(long_df: pd.DataFrame) -> pd.DataFrame:
    """Total de filas-actividad por año (suma todas las unidades)."""
    if long_df.empty or "anio" not in long_df.columns:
        return long_df
    g = long_df.groupby("anio", dropna=False).size().reset_index(name="n_actividades")
    return g.sort_values("anio")


def summary_by_og(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    g = long_df.groupby("og", dropna=False).size().reset_index(name="n_bloques")
    return g.sort_values("og")


def summary_by_unit_og(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    g = long_df.groupby(["unidad", "og"], dropna=False).size().reset_index(name="n_bloques")
    return g.sort_values(["unidad", "og"])


def completeness_flags(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame(
            columns=[
                "respuesta_id",
                "og",
                "falta_actividad",
                "falta_detalle",
                "falta_resultado",
                "falta_oe",
            ]
        )
    def flag(s: str) -> bool:
        return not (s and str(s).strip())

    tmp = long_df.copy()
    tmp["falta_oe"] = tmp["oe"].map(flag)
    tmp["falta_actividad"] = tmp["actividad"].map(flag)
    tmp["falta_detalle"] = tmp["detalle"].map(flag)
    tmp["falta_resultado"] = tmp["resultado"].map(flag)
    return tmp[
        ["respuesta_id", "og", "falta_actividad", "falta_detalle", "falta_resultado", "falta_oe"]
    ]


def layer_b_oe_matrix(plan: dict[str, Any], validated: pd.DataFrame) -> pd.DataFrame:
    """Por cada OE del YAML: conteos de actividades Forms vs carga app con cadena extendida."""
    rows: list[dict[str, Any]] = []
    if not plan or not list(iter_og(plan)):
        return pd.DataFrame(
            columns=["og", "oe_id", "resumen_oe", "acciones_en_yaml", "n_forms", "n_app", "nota"]
        )
    has_id = "oe_id_canonico" in validated.columns
    for og in iter_og(plan):
        og_n = int(og["numero"])
        for oe in list_oe_for_og(plan, og_n):
            oid = str(oe.get("id", ""))
            accs = list_acciones(oe)
            if has_id and oid:
                sub = validated[validated["oe_id_canonico"] == oid]
            else:
                txt = str(oe.get("texto", "")).strip()
                sub = validated[
                    (validated["og"] == og_n) & (validated["oe"].astype(str).str.strip() == txt)
                ]
            n_forms = int(len(sub[sub["origen"].astype(str) == "google_forms"])) if not sub.empty else 0
            n_app = int(len(sub[sub["origen"].astype(str) == "app_carga_directa"])) if not sub.empty else 0
            if accs:
                nota = "Acciones definidas en YAML: posible vinculación explícita si se cargan IDs en app."
            else:
                nota = "Sin acciones en YAML: Capa B inferida / no trazable a acción formal hasta tabular PEI."
            rows.append(
                {
                    "og": og_n,
                    "oe_id": oid,
                    "resumen_oe": str(oe.get("texto", ""))[:120],
                    "acciones_en_yaml": len(accs),
                    "n_forms": n_forms,
                    "n_app": n_app,
                    "nota": nota,
                }
            )
    return pd.DataFrame(rows)


def layer_c_meta_kpis(validated: pd.DataFrame, years: Optional[list[int]] = None) -> dict[str, Any]:
    """Indicadores de proceso (meta) derivados del registro — no sustituyen indicadores del PEI documento."""
    df = validated.copy()
    if years:
        df = df[df["anio"].isin(years)]
    if df.empty:
        return {"n_actividades": 0}
    units = df["unidad"].astype(str).str.strip().replace("", pd.NA).dropna().unique()
    n_units = int(len(units))
    by_year = df.groupby("anio")["unidad"].nunique(dropna=True).to_dict() if "anio" in df.columns else {}
    oe_cov = float(df["oe_en_catalogo"].mean()) if "oe_en_catalogo" in df.columns else None
    return {
        "n_actividades": int(len(df)),
        "unidades_distintas": n_units,
        "unidades_con_carga_por_anio": {str(k): int(v) for k, v in by_year.items()},
        "tasa_oe_en_catalogo": oe_cov,
        "definicion": "KPIs de cobertura del registro (Capa C1). Indicadores formales del PEI (Capa C2) requieren fuente adicional.",
    }
