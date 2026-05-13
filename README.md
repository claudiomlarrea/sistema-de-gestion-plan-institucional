# Sistema de gestión del PEI — UCCuyo

Aplicación **Streamlit** para cargar respuestas del **Formulario único del PEI** (formato ancho de Google Forms), transformarlas a formato largo por bloque OG/OE, y apoyar seguimiento, análisis básicos e informes exportables.

## Requisitos

- Python 3.10+

## Instalación

```bash
cd "/ruta/al/proyecto/68 Sistema de Gestión del PEI"
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Datos

Copie el Excel de respuestas como:

`data/respuestas_pei.xlsx`

(hoja por defecto: `Respuestas de formulario 1`), o use la carga desde la barra lateral de la app.

Origen de referencia en desarrollo: `~/Downloads/Formulario Único para el PEI (respuestas).xlsx`.

## Publicación (GitHub + Streamlit Cloud)

Guía paso a paso: [docs/DEPLOY_GITHUB_STREAMLIT.md](docs/DEPLOY_GITHUB_STREAMLIT.md)

Resumen: `gh auth login` → `./scripts/publicar_github_y_streamlit.sh` → en [share.streamlit.io](https://share.streamlit.io/) crear app apuntando a `app.py`.

## Ejecución local

```bash
streamlit run app.py
```

## Marca

Coloque el escudo oficial en `assets/brand/logo.png` según el Manual de marca UCCuyo. El banner no incluye textos de unidades internas.

## Configuración del plan

- `config/plan_meta.yaml` — años válidos y títulos de OG.
- `config/plan_2023_2027.yaml` — **plan canónico** (OE del formulario tabulados; acciones/indicadores listos para completar desde el PEI Word).
- `config/units.yaml` — unidades observadas y alias.
- `config/instrument.yaml` — parámetros del instrumento (p. ej. OG 6 sin columna Actividades en algunos CSV).

## Módulos principales (`pei_gestion/`)

| Módulo | Rol |
|--------|-----|
| `ingestion` | Excel/Sheets ancho → largo, `origen=google_forms`. |
| `sheets_ingestion` | Google Sheets API (`st.secrets`). |
| `snapshots` | CSV fechados en `data/snapshots/`. |
| `validation` | OE vs YAML, unidad, texto genérico. |
| `followup` | Capas A/B/C de seguimiento. |
| `analytics` / `ml_analytics` / `topics` | Filtros, series, NMF, clustering, RF baseline, polaridad léxica. |
| `activity_entry` | Filas `app_carga_directa` fusionadas al consolidado. |
| `plan_assist` | Borradores YAML exportables. |
| `reports` | Excel multi-hoja + Word. |

## Documentación

- [docs/MAPEO_SHEETS_PEI.md](docs/MAPEO_SHEETS_PEI.md) — columnas del export y mapeo al canónico.
- [docs/GOBERNANZA_PEI.md](docs/GOBERNANZA_PEI.md) — dueños de datos y ciclo anual.
- `.streamlit/secrets.toml.example` — plantilla para Sheets API.

## Páginas multipágina

En el menú lateral de Streamlit aparecen **Gobernanza** y **Fuentes y mapeo** (carpeta `pages/`), con el mismo banner institucional.

## Extracción PEI desde Word

```bash
python tools/extract_pei_docx.py "/ruta/al/PEI.docx" > tmp/pei_dump.md
```
