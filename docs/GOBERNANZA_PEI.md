# Gobernanza de datos del PEI — UCCuyo

Este documento resume roles, versionado y ciclo operativo alineado al plan de sistema GitHub + Streamlit.

## Dueños de datos

| Activo | Dueño sugerido | Notas |
|--------|----------------|-------|
| Diccionario canónico del PEI (`config/plan_*.yaml`) | Comisión / Secretaría académica con mandato del Consejo | Versionado en Git; cambios solo vía PR o proceso institucional explícito. |
| Catálogo de unidades (`config/units.yaml`) | Secretaría que administra el Google Forms | Refleja lista cerrada del formulario + alias acordados. |
| Respuestas del formulario (Sheets) | Unidades (carga) + Secretaría (validación) | Fuente operativa; credenciales de lectura en `st.secrets` o entorno seguro. |
| Snapshots (`data/snapshots/`) | Secretaría PEI | Archivos fechados para auditoría y cierres de memoria; política de retención institucional. |
| Borradores `plan_proposals_*` | Autor de la carga en app + revisión política | No sustituyen el PEI aprobado hasta resolución formal. |

## Versionado del formulario y del plan

- Cada cambio de redacción de OE/indicadores en el **Google Forms** debe registrar **changelog** (fecha, responsable, motivo) y alinearse con una **versión** del paquete YAML en repositorio (`pei-2023-2027-vN`).
- Si el formulario y el YAML divergen, el sistema marcará **OE fuera de catálogo** hasta actualizar el YAML o corregir el formulario.

## Ciclo anual sugerido

1. **Ventana de carga** por unidades (fechas publicadas).
2. **Validación central** (coherencia OE/unidad/año, textos genéricos, duplicados).
3. **Devolución** a unidades con observaciones.
4. **Snapshot de cierre** para memoria / rendición de cuentas.
5. **Revisión** de propuestas de `plan_assist` (si se usan) en órgano competente.

## Privacidad

Los exports contienen **correos** y textos libres. Para demos públicas: anonimizar o usar `data/sample_*.csv` acotado.

## Aprobación de borradores

El paso de archivos `plan_proposals_*.yaml` (planeación asistida) a paquete oficial debe estar **nombrado** (p. ej. Consejo Superior, comisión PEI) y documentado; la app **no** sobrescribe `config/plan_*.yaml` oficial.
