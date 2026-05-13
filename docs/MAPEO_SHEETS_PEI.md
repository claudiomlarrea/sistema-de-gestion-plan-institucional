# Mapeo: Google Sheets / Excel ancho → modelo canónico del PEI

Fuente de referencia verificada: export **Formulario Único para el PEI (respuestas).xlsx**, hoja **`Respuestas de formulario 1`**.

## Columnas de identificación y contexto

| Columna export | Campo interno | Uso |
|----------------|-----------------|-----|
| Marca temporal | `fecha_carga` | Filtro temporal “real” del envío; preferido en analítica temporal. |
| Dirección de correo electrónico | `email`, `cargado_por` | Responsable de la carga (formulario). |
| AÑO | `anio` | Año declarado de la actividad (2023–2027); no sustituye la marca temporal. |
| Unidad Académica o Administrativa (puede incluir espacios iniciales en encabezado) | `unidad` | Clave operativa; normalizar con `config/units.yaml`. |
| Puntuación | `puntuacion` | Metadato del formulario; conservado tal cual. |

## Bloques por Objetivo general (OG 1…6)

Para cada `N` en 1…6:

| Columna export (patrón) | Campo interno |
|-------------------------|---------------|
| Objetivos específicos N | `oe` (texto elegido en lista del formulario) |
| Actividades Objetivo N… | `actividad` |
| Detalle de la Actividad Objetivo N… | `detalle` |
| Resultados obtenidos Objetivo N… | `resultado` (fusionado, ver abajo) |
| Resultado obtenido (campo de Texo o Numérico) Objetivo N | `resultado` (alternativa) |

### Fusión de “resultados” duplicados

El export incluye **dos familias** de columnas de resultado por objetivo. La ingesta aplica **coalescencia**: se usa el texto de *Resultados obtenidos…* si no está vacío; si no, el de *Texo o Numérico*.

## Unpivot (ancho → largo)

- Una **fila ancha** (una respuesta del formulario) genera **hasta seis filas largas** (una por OG con contenido en al menos uno de: OE, actividad, detalle, resultado).
- `respuesta_id` = índice de fila del DataFrame leído (estable respecto del archivo).
- `origen` = `google_forms` para datos del formulario (archivo o Sheets API).

### Export CSV por unidad (Looker / carpetas)

Algunos CSV **omit** la columna “Actividades Objetivo 6”: el parser debe tolerar **ausencia de columnas** por OG según `config/instrument.yaml` (`actividades_columna_opcional_og: [6]`).

## Relación con el PEI canónico (`config/plan_2023_2027.yaml`)

| Nivel PEI | ¿En el formulario? | Validación |
|-----------|--------------------|------------|
| OG | Implícito por bloque 1…6 | Derivado del número de bloque. |
| OE | Sí (lista cerrada) | `oe_en_catalogo` vs YAML generado desde valores únicos del export / PEI. |
| Acción | No | Solo vía YAML + `activity_entry` o futuras extensiones. |
| Indicador | No | Idem. |

## Google Sheets API

- Variables / `st.secrets`: ver `.streamlit/secrets.toml.example`.
- La primera fila debe ser encabezados idénticos al export de Forms.
- TTL y cuotas: usar caché en sesión o `st.cache_data` con TTL corto en despliegue.
