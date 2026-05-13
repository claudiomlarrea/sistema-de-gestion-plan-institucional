"""Aplicación Streamlit — gestión y evaluación PEI UCCuyo (plan completo)."""
from __future__ import annotations

import datetime as dt
from datetime import date

import pandas as pd
import streamlit as st

from pei_gestion import analytics, followup, ingestion, ml_analytics, plan_assist, reports, snapshots, topics, validation
from pei_gestion.activity_entry import entries_to_dataframe, entry_row, merge_with_forms
from pei_gestion.banner import render_banner
from pei_gestion.canonical_plan import list_oe_for_og
from pei_gestion.config_loader import load_plan_bundle, project_root

st.set_page_config(page_title="PEI UCCuyo", layout="wide", initial_sidebar_state="expanded")

META, CANONICAL, PLAN_NAME = load_plan_bundle()
render_banner(title="Sistema de gestión del PEI", subtitle=None)

st.caption(
    "Instrumento vigente: certifica **OG/OE** y textos de actividad. **Marca temporal** = envío; **AÑO** = año declarado. "
    "Análisis automáticos son exploratorios (ver disclaimers en cada sección)."
)

if "forms_long" not in st.session_state:
    st.session_state.forms_long = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "data_label" not in st.session_state:
    st.session_state.data_label = ""
if "app_entry_rows" not in st.session_state:
    st.session_state.app_entry_rows = []


def display_long_df() -> pd.DataFrame | None:
    base = st.session_state.forms_long
    extra = entries_to_dataframe(st.session_state.app_entry_rows)
    if base is None and extra.empty:
        return None
    if base is None:
        return extra
    if extra.empty:
        return base
    return merge_with_forms(base, extra)


with st.sidebar:
    st.header("Datos")
    default_xlsx = project_root() / "data" / "respuestas_pei.xlsx"
    uploaded = st.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])
    use_default = st.checkbox(
        "Usar data/respuestas_pei.xlsx",
        value=default_xlsx.is_file(),
        disabled=not default_xlsx.is_file(),
    )
    sheet = st.text_input("Nombre de hoja", value="Respuestas de formulario 1")

    st.subheader("Google Sheets (opcional)")
    load_sheets = st.button("Cargar desde Sheets API")
    if load_sheets:
        try:
            raw = st.secrets
            from pei_gestion import sheets_ingestion

            sdf = sheets_ingestion.load_sheet_as_dataframe_from_secrets(raw)
            st.session_state.raw_df = sdf
            st.session_state.forms_long = ingestion.wide_to_long(sdf, sheet_used=str(sheet), origen="google_forms")
            st.session_state.data_label = "google_sheets_api"
            st.success(f"Sheets: {len(sdf)} filas anchas → {len(st.session_state.forms_long)} largas.")
        except Exception as e:
            st.error(f"No se pudo leer Sheets (¿secrets.toml?): {e}")

    if st.button("Cargar desde archivo"):
        try:
            if uploaded is not None:
                raw, long_df = ingestion.load_uploaded_excel(uploaded.getvalue(), uploaded.name, sheet_name=sheet)
                st.session_state.data_label = f"upload:{uploaded.name}"
            elif use_default and default_xlsx.is_file():
                raw, long_df = ingestion.load_excel_wide(default_xlsx, sheet_name=sheet)
                st.session_state.data_label = str(default_xlsx)
            else:
                st.error("Suba un .xlsx o coloque respuestas_pei.xlsx en data/.")
                st.stop()
            st.session_state.raw_df = raw
            st.session_state.forms_long = long_df
            st.success(f"Cargado: {len(raw)} × ancho → {len(long_df)} largas.")
        except Exception as e:
            st.exception(e)

    st.subheader("Carga directa (memoria de sesión)")
    st.caption("Las filas se fusionan al consolidado hasta recargar la página.")
    if st.button("Vaciar entradas manuales"):
        st.session_state.app_entry_rows = []
        st.success("Listo.")

ldf = display_long_df()
raw_df = st.session_state.raw_df

(
    tab_inicio,
    tab_seg,
    tab_ana,
    tab_sem,
    tab_entry,
    tab_assist,
    tab_inf,
    tab_inst,
) = st.tabs(
    [
        "Inicio",
        "Seguimiento",
        "Análisis",
        "Temas / ML",
        "Carga directa",
        "Planeación asistida",
        "Informes",
        "Instrumento",
    ]
)

with tab_inicio:
    st.subheader(PLAN_NAME)
    st.write("Plan canónico:", CANONICAL.get("plan_id", "—"))
    ogs = META.get("objetivos_generales") or {}
    for k, v in ogs.items():
        st.markdown(f"- **OG {k}**: {v}")
    st.subheader("Estado")
    if ldf is None:
        st.info("Cargue datos con el panel lateral (archivo, Sheets o agregue carga directa).")
    else:
        st.metric("Registros consolidados (largo)", len(ldf))
        if st.session_state.forms_long is not None:
            st.metric("Solo Google Forms / archivo", len(st.session_state.forms_long))
        st.metric("Entradas app (sesión)", len(st.session_state.app_entry_rows))
    if hasattr(st, "page_link"):
        st.page_link("pages/01_Gobernanza.py", label="Gobernanza (página aparte)", icon="📘")
        st.page_link("pages/02_Fuentes_y_mapeo.py", label="Fuentes y mapeo Sheets", icon="🔗")

with tab_seg:
    if ldf is None:
        st.warning("Sin datos consolidados.")
    else:
        val = validation.validate_long_df(ldf, CANONICAL)
        st.markdown("### Capa A — Actividades")
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(followup.summary_by_unit_year(ldf), use_container_width=True)
        with c2:
            st.dataframe(followup.summary_by_og(ldf), use_container_width=True)
        st.dataframe(followup.summary_by_unit_og(ldf), use_container_width=True)
        st.dataframe(followup.completeness_flags(ldf).head(500), use_container_width=True)

        st.markdown("### Capa B — OE del plan vs evidencia")
        st.caption("Matriz por OE del YAML: conteos Forms vs app con cadena extendida.")
        st.dataframe(followup.layer_b_oe_matrix(CANONICAL, val), use_container_width=True, height=320)

        st.markdown("### Capa C — Meta-indicadores de proceso")
        st.json(followup.layer_c_meta_kpis(val, years=META.get("years_valid")))

        st.markdown("### Validación OE / unidad")
        st.dataframe(val.head(300), use_container_width=True)

with tab_ana:
    if ldf is None:
        st.warning("Sin datos consolidados.")
    else:
        unidades = sorted({str(u).strip() for u in ldf["unidad"].dropna() if str(u).strip()})
        sel_u = st.multiselect("Unidad(es)", options=unidades)
        years_meta = META.get("years_valid") or sorted(ldf["anio"].dropna().unique().tolist())
        sel_y = st.multiselect("Año(s)", options=years_meta, default=years_meta)
        sel_og = st.multiselect("OG", options=[1, 2, 3, 4, 5, 6], default=[1, 2, 3, 4, 5, 6])
        orig_opts = sorted(ldf["origen"].dropna().unique().tolist()) if "origen" in ldf.columns else []
        sel_orig = st.multiselect("Origen", options=orig_opts, default=orig_opts)
        use_ts = st.checkbox("Filtrar por Marca temporal", value=False)
        d0 = d1 = None
        if use_ts and ldf["fecha_carga"].notna().any():
            ts = pd.to_datetime(ldf["fecha_carga"], errors="coerce")
            mn, mx = ts.min(), ts.max()
            if pd.notna(mn) and pd.notna(mx):
                dr = st.date_input("Rango de envío", value=(mn.date(), mx.date()))
                if isinstance(dr, tuple) and len(dr) == 2:
                    d0, d1 = dr
                else:
                    d0 = d1 = dr

        filt = analytics.filter_long(
            ldf,
            unidades=sel_u or None,
            anios=[int(x) for x in sel_y] if sel_y else None,
            ogs=sel_og or None,
            origenes=sel_orig or None,
            fecha_desde=d0 if use_ts and d0 else None,
            fecha_hasta=d1 if use_ts and d1 else None,
        )
        st.write(analytics.describe_text_fields(filt))
        ts_eff = pd.to_datetime(filt["fecha_carga"], errors="coerce")
        st.caption(
            f"Universo filtrado: n={len(filt)} | sin marca temporal: {float(ts_eff.isna().mean()):.1%} "
            "(si filtra por fecha, esas filas pueden quedar fuera)."
        )
        if not filt.empty and filt["fecha_carga"].notna().any():
            st.subheader("Serie temporal (conteos por semana)")
            try:
                ser = ml_analytics.activities_by_period(filt, freq="W")
                st.line_chart(ser.set_index("fecha_carga"))
            except Exception as ex:
                st.warning(f"No se pudo graficar serie: {ex}")
        st.dataframe(filt, use_container_width=True, height=360)

with tab_sem:
    st.warning(
        "**Advertencia:** temas, clustering y polaridad léxica son hipótesis exploratorias; no miden calidad "
        "ni desempeño individual. Versionado: sklearn + semilla fija donde aplica."
    )
    if ldf is None or len(ldf) < 30:
        st.info("Se requieren al menos ~30 filas consolidadas.")
    else:
        n_top = st.slider("Temas NMF", 3, 16, 8)
        seed = st.number_input("Semilla", value=42)
        if st.button("Ejecutar NMF + k-means (TF-IDF)"):
            try:
                tr = topics.run_nmf_topics(ldf, n_topics=int(n_top), random_state=int(seed))
                st.write("Modelo:", tr.model_version)
                for i, top in enumerate(tr.topics):
                    st.markdown(f"**Tema {i+1}:** " + ", ".join(f"{w} ({s:.2f})" for w, s in top[:8]))
                labels, _ = topics.run_kmeans_on_tfidf(ldf, n_clusters=6, random_state=int(seed))
                st.subheader("Distribución de clusters (k=6)")
                st.bar_chart(pd.Series(labels).value_counts().sort_index())
            except Exception as e:
                st.exception(e)
        emb = st.checkbox("Intentar embeddings multilingües (opcional, requiere sentence-transformers)", value=False)
        if emb and st.button("Cluster con embeddings"):
            r = topics.try_sentence_embedding_cluster(ldf, n_clusters=6)
            if r is None:
                st.info("Instale `sentence-transformers` para esta opción.")
            else:
                labels, desc = r
                st.success(desc)
                st.bar_chart(pd.Series(labels).value_counts().sort_index())

        st.subheader("Polaridad léxica simple (español reducido)")
        pol = ml_analytics.add_polarity_column(ldf)
        st.caption("Léxico mínimo embebido; no es modelo de lenguaje completo.")
        st.dataframe(pol[["unidad", "anio", "polaridad_lexica", "actividad", "resultado"]].head(200))

        st.subheader("Random Forest: baseline OG ← texto (hold-out)")
        st.caption(ml_analytics.rf_og_from_text_baseline(ldf).get("disclaimer", ""))
        if st.button("Entrenar baseline RF"):
            rep = ml_analytics.rf_og_from_text_baseline(ldf)
            if "error" in rep:
                st.warning(rep["error"])
            else:
                st.metric("Accuracy hold-out", f"{rep['accuracy_holdout']:.3f}")
                st.text(rep.get("classification_report", ""))

with tab_entry:
    st.markdown("### Registro alternativo al Google Forms")
    st.caption("Vinculación OG → OE según `config/plan_2023_2027.yaml`. Acción/indicador: texto libre si aún no hay catálogo.")
    unidades_cfg = validation.load_units_config().get("unidades_observadas") or []
    if unidades_cfg:
        u_pick = st.selectbox("Unidad", options=unidades_cfg)
    else:
        u_pick = st.text_input("Unidad (texto libre)", value="")

    anio = st.selectbox("Año", options=META.get("years_valid", [2023, 2024, 2025, 2026, 2027]))
    og_n = st.selectbox("Objetivo general", options=[1, 2, 3, 4, 5, 6])
    oes = list_oe_for_og(CANONICAL, int(og_n)) if CANONICAL else []
    if oes:
        oe_labels = [f"{o.get('id', '')} — {str(o.get('texto', ''))[:90]}" for o in oes]
        oe_i = st.selectbox("Objetivo específico", list(range(len(oes))), format_func=lambda i: oe_labels[i])
        oe_txt = str(oes[oe_i].get("texto", ""))
    else:
        oe_txt = st.text_input("Texto OE (sin catálogo YAML)", value="")
    acc_txt = st.text_input("Acción (opcional / libre)", value="")
    ind_txt = st.text_input("Indicador (opcional / libre)", value="")
    act = st.text_input("Actividad (≤10 palabras recomendado)", value="")
    det = st.text_input("Detalle (≤20 palabras recomendado)", value="")
    res = st.text_input("Resultado", value="")
    email = st.text_input("Correo institucional", value="")

    if st.button("Agregar a la sesión"):
        row = entry_row(
            unidad=u_pick,
            anio=int(anio),
            og=int(og_n),
            oe_texto=str(oe_txt),
            actividad=act,
            detalle=det,
            resultado=res,
            accion=acc_txt,
            indicador=ind_txt,
            email=email,
            cargado_por=email,
        )
        st.session_state.app_entry_rows.append(row)
        st.success(f"Filas en sesión: {len(st.session_state.app_entry_rows)}")

    edf = entries_to_dataframe(st.session_state.app_entry_rows)
    if not edf.empty:
        st.dataframe(edf, use_container_width=True)
        st.download_button(
            "Descargar entradas sesión (CSV)",
            edf.to_csv(index=False).encode("utf-8"),
            file_name=f"activity_entry_{date.today().isoformat()}.csv",
            mime="text/csv",
        )

with tab_assist:
    st.markdown("### Planeación asistida (borrador)")
    st.caption("Exporta propuestas en YAML; **no** modifica `config/plan_2023_2027.yaml` oficial.")
    sug = st.text_area("Sugerencias de cambio (texto libre)", height=120)
    nuevo = st.text_area("Objetivos nuevos / contexto (uno por línea)", height=100)
    autor = st.text_input("Autor", value="")
    if st.button("Generar YAML de propuesta"):
        doc = plan_assist.build_proposals_document(
            str(CANONICAL.get("plan_id", "pei-uccuyo-2023-2027")),
            sugerencias=[sug] if sug.strip() else [],
            objetivos_nuevos=[{"texto": line} for line in nuevo.splitlines() if line.strip()],
            referencia_clusters="Ver módulo Temas/ML si aplica.",
            autor=autor or "anonimo",
        )
        yaml_out = plan_assist.proposals_to_yaml(doc)
        fn = f"plan_proposals_{doc['plan_id']}_{dt.date.today().isoformat()}.yaml"
        st.download_button("Descargar borrador", yaml_out.encode("utf-8"), file_name=fn, mime="text/yaml")

with tab_inf:
    if ldf is None:
        st.warning("Sin datos consolidados.")
    else:
        val = validation.validate_long_df(ldf, CANONICAL)
        lb = followup.layer_b_oe_matrix(CANONICAL, val)
        kpi = followup.layer_c_meta_kpis(val, years=META.get("years_valid"))
        st.markdown("Exporta Excel (varias hojas) y Word con metadatos y pivots.")
        out_dir = project_root() / "data" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
        xlsx_path = out_dir / f"informe_pei_{stamp}.xlsx"
        docx_path = out_dir / f"informe_pei_{stamp}.docx"
        c1, c2, c3 = st.columns(3)
        if c1.button("Excel completo"):
            reports.write_excel_report(
                xlsx_path,
                long_df=ldf,
                by_unit_year=followup.summary_by_unit_year(ldf),
                by_og=followup.summary_by_og(ldf),
                completeness=followup.completeness_flags(ldf),
                plan_name=PLAN_NAME,
                source=st.session_state.data_label,
                validated=val,
                layer_b=lb,
                meta_kpis=kpi,
            )
            st.success(str(xlsx_path))
        if c2.button("Word resumen"):
            reports.write_word_summary(
                docx_path,
                long_df=ldf,
                plan_name=PLAN_NAME,
                source=st.session_state.data_label,
            )
            st.success(str(docx_path))
        if c3.button("Snapshot CSV consolidado"):
            p = snapshots.save_snapshot(ldf, label="consolidado")
            st.success(str(p))

with tab_inst:
    st.subheader("Alcance del instrumento vs PEI")
    st.markdown(
        """
El **Google Forms** certifica actividades hasta **objetivo específico (OE)**. **Acciones** e **indicadores** del documento
matriz **no** están en el formulario: no interpretar su ausencia como “falta de cumplimiento” sin otra fuente.

- **Capa B/C** del seguimiento se alimenta del YAML y de la **carga directa** con texto/IDs cuando existan.
- Coherencia fuerte OE ↔ catálogo: ver columnas `oe_en_catalogo` tras validación.
"""
    )
    if raw_df is not None:
        st.code("\n".join(str(c) for c in raw_df.columns))
