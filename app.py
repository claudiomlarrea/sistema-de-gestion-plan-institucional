"""Aplicación Streamlit — gestión y evaluación PEI UCCuyo (plan completo)."""
from __future__ import annotations

import datetime as dt
import re
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
    "**Dónde analizar:** usá las pestañas **Análisis cuantitativo**, **Análisis cualitativo** y **Consistencia del dato** "
    "(cada una tiene sub-secciones numeradas). **Resumen operativo** es solo tableros de volumen."
)

if "forms_long" not in st.session_state:
    st.session_state.forms_long = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "data_label" not in st.session_state:
    st.session_state.data_label = ""
if "app_entry_rows" not in st.session_state:
    st.session_state.app_entry_rows = []

CAPTION_TABLA_ACTIVIDADES = (
    "**Cada fila es una actividad cargada** (un bloque OG–OE con textos). **No** es un resumen de totales: "
    "la primera fila es solo un registro más. Para totales usá **Inicio** o **Resumen operativo**."
)


def _og_nums_en_meta(meta: dict) -> list[int]:
    ogs = meta.get("objetivos_generales") or {}
    nums: list[int] = []
    for k in ogs:
        try:
            nums.append(int(k))
        except (TypeError, ValueError):
            continue
    return sorted(nums) or [1, 2, 3, 4, 5, 6]


def _og_opciones_selectbox(meta: dict) -> list[str]:
    """Texto «N. denominación» como *valor* del selectbox (Streamlit muestra `options` literal)."""
    nums = _og_nums_en_meta(meta)
    ogs = meta.get("objetivos_generales") or {}
    labels: list[str] = []
    for n in nums:
        raw = ogs.get(n, ogs.get(str(n)))
        body = str(raw).strip() if raw is not None else ""
        labels.append(f"{n}. {body}" if body else f"{n}. (sin texto en plan_meta.yaml)")
    return labels


def _og_num_desde_etiqueta_select(label: str) -> int:
    m = re.match(r"^\s*(\d+)\.", str(label).strip())
    return int(m.group(1)) if m else 1


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
            if st.session_state.forms_long.empty:
                st.warning(
                    "**0 filas en formato largo:** el ancho se leyó, pero no se detectaron bloques OG/OE con datos "
                    "(revisá que los encabezados coincidan con el export del Google Forms: "
                    "«Objetivos específicos 1»…6, «Actividades Objetivo 1»…, etc.). "
                    "**No renombrar columnas en el Excel** antes de cargar."
                )
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
            if long_df.empty:
                st.warning(
                    "**0 filas en formato largo:** el archivo tiene filas anchas, pero no se extrajo ninguna actividad. "
                    "Causas frecuentes: **hoja incorrecta**, encabezados **renombrados** respecto del formulario, "
                    "o columnas de OG/OE que no coinciden con los textos esperados "
                    "(p. ej. «Objetivos específicos 1», «Actividades Objetivo 1»). "
                    "Descargá de nuevo **Respuestas de formulario** desde Google Forms y cargá sin editar títulos de columnas."
                )
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
    tab_res,
    tab_cuanti,
    tab_cuali,
    tab_consist,
    tab_entry,
    tab_assist,
    tab_inf,
    tab_guia,
) = st.tabs(
    [
        "Inicio",
        "Resumen operativo",
        "Análisis cuantitativo",
        "Análisis cualitativo",
        "Consistencia del dato",
        "Carga directa",
        "Planeación asistida",
        "Informes",
        "Guía metodológica",
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

with tab_res:
    if ldf is None:
        st.warning("Sin datos consolidados.")
    else:
        st.markdown("### Resumen operativo")
        st.caption(
            "Igual que «Resumen de ítems» en encuestas: **cuánto** hay por unidad, año y OG, y si faltan campos. "
            "Para números con filtros → **Análisis cuantitativo**. Para % frente al plan → **Consistencia del dato**."
        )
        st.markdown("#### Capa A — Actividades")
        st.caption(
            "Cada **actividad** es una fila del consolidado (texto declarado por unidad en un objetivo general y específico). "
            "Los números **no** son usuarios ni envíos únicos del formulario: son actividades cargadas."
        )
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Por **unidad** y **año**: cuántas actividades se registraron.")
            st.dataframe(analytics.dataframe_for_display(followup.summary_by_unit_year(ldf)), use_container_width=True)
        with c2:
            st.caption(
                "Por **objetivo general** (1–6): cuántas actividades se declararon en cada OG (suma todas las unidades)."
            )
            st.dataframe(analytics.dataframe_for_display(followup.summary_by_og(ldf)), use_container_width=True)
        st.caption("Por **unidad** y **objetivo general** a la vez (misma actividad cuenta en una sola celda).")
        st.dataframe(analytics.dataframe_for_display(followup.summary_by_unit_og(ldf)), use_container_width=True)
        st.markdown("#### Completitud de campos (por bloque)")
        st.caption("Cada fila: un bloque OG; columnas «Falta…» indican si falta texto en ese campo.")
        st.dataframe(analytics.dataframe_for_display(followup.completeness_flags(ldf).head(500)), use_container_width=True)

with tab_consist:
    if ldf is None:
        st.warning("Sin datos consolidados.")
    else:
        val = validation.validate_long_df(ldf, CANONICAL)
        st.markdown("## Consistencia del dato")
        st.caption(
            "Igual que un apartado de «consistencia / calidad» en encuestas: qué tan alineado está lo cargado "
            "con el **plan YAML** y el **listado de unidades**."
        )
        s1, s2, s3, s4 = st.tabs(
            [
                "1. Porcentajes de consistencia",
                "2. Plan vs evidencia (matriz)",
                "3. JSON técnico",
                "4. Filas validadas (muestra)",
            ]
        )
        with s1:
            with st.expander(
                "Aclaración — Consistencia de la actividad cargada con el objetivo",
                expanded=False,
            ):
                st.markdown(
                    "El indicador **«OE en catálogo oficial»** (y en el JSON, `tasa_oe_en_catalogo`) mide si, **en cada fila**, "
                    "el texto del **objetivo específico (OE)** cargado puede reconocerse en el catálogo oficial del PEI "
                    "**bajo el objetivo general (OG)** que figura en esa misma fila. "
                    "**No** indica «dónde» se cargó la actividad (unidad u origen), ni si el respondiente eligió el OG "
                    "que vos considerarías correcto: si el OG declarado no corresponde al OE escrito, el match puede fallar "
                    "aunque ese OE exista en el plan bajo otro OG."
                )
            c1, c2, c3, c4 = st.columns(4)
            if "oe_en_catalogo" in val.columns:
                c1.metric("OE en catálogo oficial", f"{100.0 * float(val['oe_en_catalogo'].mean()):.1f}%")
            if "unidad_catalogada" in val.columns:
                c2.metric("Unidad en lista institucional", f"{100.0 * float(val['unidad_catalogada'].mean()):.1f}%")
            fl = followup.completeness_flags(ldf)
            if not fl.empty:
                c3.metric("Con actividad informada", f"{100.0 * (1 - fl['falta_actividad'].mean()):.1f}%")
                c4.metric("Con resultado informado", f"{100.0 * (1 - fl['falta_resultado'].mean()):.1f}%")
            st.caption(
                f"Texto genérico o vacío (proxy de baja evidencia): {100.0 * float(val['texto_generico'].mean()):.1f}%"
            )
        with s2:
            st.dataframe(
                analytics.dataframe_for_display(followup.layer_b_oe_matrix(CANONICAL, val)),
                use_container_width=True,
                height=380,
            )
        with s3:
            kpi = followup.layer_c_meta_kpis(val, years=META.get("years_valid"))
            st.caption(
                "**Aclaración:** `tasa_oe_en_catalogo` = consistencia de la actividad cargada con el **objetivo**: "
                "OE reconocible en el catálogo para el **OG de esa fila** (ver desplegable en «1. Porcentajes…»)."
            )
            st.json(kpi)
        with s4:
            st.caption(CAPTION_TABLA_ACTIVIDADES)
            st.dataframe(
                analytics.dataframe_for_display(val.head(400)),
                use_container_width=True,
                hide_index=True,
            )

with tab_cuanti:
    if ldf is None:
        st.warning("Sin datos consolidados.")
    else:
        st.markdown("## Análisis cuantitativo")
        st.caption(
            "Como la pestaña homónima en encuestas: **números**, filtros y tendencias en el tiempo. "
            "Sub-secciones numeradas abajo."
        )
        unidades = sorted({str(u).strip() for u in ldf["unidad"].dropna() if str(u).strip()})
        years_meta = META.get("years_valid") or sorted(ldf["anio"].dropna().unique().tolist())
        sel_y = st.multiselect("Año(s)", options=years_meta, default=years_meta, key="cuanti_anios")
        sel_og = st.multiselect(
            "Objetivo general del PEI (1 a 6)",
            options=[1, 2, 3, 4, 5, 6],
            default=[1, 2, 3, 4, 5, 6],
            key="cuanti_og",
        )
        orig_opts = sorted(ldf["origen"].dropna().unique().tolist()) if "origen" in ldf.columns else []
        sel_orig = st.multiselect("Origen", options=orig_opts, default=orig_opts, key="cuanti_orig")
        use_ts = st.checkbox("Filtrar por Marca temporal", value=False, key="cuanti_ts")
        d0 = d1 = None
        if use_ts and ldf["fecha_carga"].notna().any():
            ts = pd.to_datetime(ldf["fecha_carga"], errors="coerce")
            mn, mx = ts.min(), ts.max()
            if pd.notna(mn) and pd.notna(mx):
                dr = st.date_input("Rango de envío", value=(mn.date(), mx.date()), key="cuanti_dr")
                if isinstance(dr, tuple) and len(dr) == 2:
                    d0, d1 = dr
                else:
                    d0 = d1 = dr

        q1, q2, q3 = st.tabs(
            [
                "1. Filtros y universo",
                "2. Tablas y conteos",
                "3. Serie temporal",
            ]
        )
        with q1:
            sel_u = st.multiselect("Unidad Académica", options=unidades, key="cuanti_uni")
            filt = analytics.filter_long(
                ldf,
                unidades=sel_u or None,
                anios=[int(x) for x in sel_y] if sel_y else None,
                ogs=sel_og or None,
                origenes=sel_orig or None,
                fecha_desde=d0 if use_ts and d0 else None,
                fecha_hasta=d1 if use_ts and d1 else None,
            )
            st.session_state["_cuanti_filt"] = filt
            st.write(analytics.describe_text_fields(filt))
            ts_eff = pd.to_datetime(filt["fecha_carga"], errors="coerce")
            st.caption(
                f"Universo filtrado: n={len(filt)} | sin marca temporal: {float(ts_eff.isna().mean()):.1%} "
                "(si filtrás por fecha, esas filas pueden quedar fuera)."
            )
        filt = st.session_state.get("_cuanti_filt", ldf)
        with q2:
            st.caption(CAPTION_TABLA_ACTIVIDADES)
            st.dataframe(
                analytics.dataframe_for_display(filt),
                use_container_width=True,
                height=420,
                hide_index=True,
            )
        with q3:
            if not filt.empty and filt["fecha_carga"].notna().any():
                try:
                    ser = ml_analytics.activities_by_period(filt, freq="W")
                    st.line_chart(ser.set_index("fecha_carga"))
                except Exception as ex:
                    st.warning(f"No se pudo graficar serie: {ex}")
            else:
                st.info("No hay fechas de envío válidas para armar la serie (revisá filtros o datos).")

with tab_cuali:
    st.markdown("## Análisis cualitativo")
    st.caption(
        "Como la pestaña homónima en encuestas: **texto**, temas y patrones. Cada bloque está numerado abajo. "
        "No sustituye lectura humana ni decisiones institucionales."
    )
    st.warning(
        "**Advertencia:** modelos automáticos pueden equivocarse (ironía, jerga, español académico). "
        "Usá semilla fija para reproducibilidad donde la app lo permite."
    )
    if ldf is None or len(ldf) < 30:
        st.info("Se requieren al menos ~30 filas consolidadas.")
    else:
        n_top = st.slider("Cantidad de temas (NMF)", 3, 16, 8, key="cuali_nmf_n")
        seed = st.number_input("Semilla aleatoria", value=42, key="cuali_seed")
        c1, c2, c3, c4, c5 = st.tabs(
            [
                "1. Temas (NMF)",
                "2. Clusters (k-means)",
                "3. Polaridad léxica",
                "4. Modelo exploratorio (RF)",
                "5. Embeddings (opcional)",
            ]
        )
        with c1:
            if st.button("Ejecutar extracción de temas (NMF)", key="cuali_btn_nmf"):
                try:
                    tr = topics.run_nmf_topics(ldf, n_topics=int(n_top), random_state=int(seed))
                    st.write("Modelo:", tr.model_version)
                    for i, top in enumerate(tr.topics):
                        st.markdown(f"**Tema {i+1}:** " + ", ".join(f"{w} ({s:.2f})" for w, s in top[:8]))
                except Exception as e:
                    st.exception(e)
        with c2:
            if st.button("Ejecutar clusters en textos (TF-IDF)", key="cuali_btn_km"):
                try:
                    labels, _ = topics.run_kmeans_on_tfidf(ldf, n_clusters=6, random_state=int(seed))
                    st.subheader("Distribución de clusters (k=6)")
                    st.bar_chart(pd.Series(labels).value_counts().sort_index())
                except Exception as e:
                    st.exception(e)
        with c3:
            pol = ml_analytics.add_polarity_column(ldf)
            st.caption("Léxico reducido en español; no es un modelo de lenguaje completo.")
            st.dataframe(
                analytics.dataframe_for_display(
                    pol[["unidad", "anio", "polaridad_lexica", "actividad", "resultado"]].head(200)
                ),
                use_container_width=True,
                hide_index=True,
            )
        with c4:
            st.caption(ml_analytics.rf_og_from_text_baseline(ldf).get("disclaimer", ""))
            if st.button("Entrenar baseline (OG desde texto)", key="cuali_btn_rf"):
                rep = ml_analytics.rf_og_from_text_baseline(ldf)
                if "error" in rep:
                    st.warning(rep["error"])
                else:
                    st.metric("Accuracy hold-out", f"{rep['accuracy_holdout']:.3f}")
                    st.text(rep.get("classification_report", ""))
        with c5:
            emb = st.checkbox("Requiere paquete sentence-transformers en el servidor", value=False, key="cuali_emb_ck")
            if emb and st.button("Cluster con embeddings multilingües", key="cuali_btn_emb"):
                r = topics.try_sentence_embedding_cluster(ldf, n_clusters=6)
                if r is None:
                    st.info("Instale `sentence-transformers` en requirements para esta opción.")
                else:
                    labels, desc = r
                    st.success(desc)
                    st.bar_chart(pd.Series(labels).value_counts().sort_index())

with tab_entry:
    st.markdown("### Registro alternativo al Google Forms")
    st.caption("Vinculación OG → OE según `config/plan_2023_2027.yaml`. Acción/indicador: texto libre si aún no hay catálogo.")
    unidades_cfg = validation.load_units_config().get("unidades_observadas") or []
    if unidades_cfg:
        u_pick = st.selectbox("Unidad Académica", options=unidades_cfg, key="entry_unidad")
    else:
        u_pick = st.text_input("Unidad Académica (texto libre)", value="", key="entry_unidad_txt")

    anio = st.selectbox(
        "Año",
        options=META.get("years_valid", [2023, 2024, 2025, 2026, 2027]),
        key="entry_anio",
    )
    st.caption("Objetivos generales según **config/plan_meta.yaml** (Plan estratégico institucional).")
    og_etiquetas = _og_opciones_selectbox(META)
    og_sel = st.selectbox(
        "Objetivo general",
        options=og_etiquetas,
        key="entry_og_label",
    )
    og_n = _og_num_desde_etiqueta_select(og_sel)
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
        st.caption(CAPTION_TABLA_ACTIVIDADES)
        st.dataframe(analytics.dataframe_for_display(edf), use_container_width=True, hide_index=True)
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
            referencia_clusters="Ver pestaña «Análisis cualitativo» (temas / clusters).",
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

with tab_guia:
    st.subheader("Guía metodológica")
    st.markdown(
        """
### Alcance del instrumento (Google Forms)

El formulario certifica actividades hasta **objetivo específico (OE)**. **Acciones** e **indicadores** del documento
matriz **no** están en el formulario: no interpretar su ausencia como “falta de cumplimiento” sin otra fuente.

### Dónde está cada tipo de análisis (mapa rápido)

| Pestaña principal | Qué encontrás |
|-------------------|----------------|
| **Resumen operativo** | Tableros de volumen (unidad / año / OG) y completitud de campos |
| **Análisis cuantitativo** | Filtros, tabla de datos, serie temporal (sub-pestañas 1–3) |
| **Análisis cualitativo** | Temas NMF, clusters, polaridad, modelo exploratorio (sub-pestañas 1–5) |
| **Consistencia del dato** | Porcentajes vs plan YAML y unidades; matriz plan vs evidencia |
| **Informes** | Excel, Word, snapshot |
"""
    )
    if hasattr(st, "page_link"):
        st.page_link("pages/01_Gobernanza.py", label="Gobernanza (página aparte)", icon="📘")
        st.page_link("pages/02_Fuentes_y_mapeo.py", label="Fuentes y mapeo Sheets", icon="🔗")
    if raw_df is not None:
        st.markdown("#### Columnas del archivo ancho cargado")
        st.code("\n".join(str(c) for c in raw_df.columns))
