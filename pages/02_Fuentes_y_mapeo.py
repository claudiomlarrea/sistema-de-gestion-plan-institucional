import streamlit as st

from pei_gestion.banner import render_banner
from pei_gestion.config_loader import project_root

render_banner(title="Sistema de gestión del PEI")
st.title("Fuentes de datos y mapeo al canónico")
root = project_root()
m = root / "docs" / "MAPEO_SHEETS_PEI.md"
if m.is_file():
    st.markdown(m.read_text(encoding="utf-8"))
ex = root / ".streamlit" / "secrets.toml.example"
if ex.is_file():
    st.subheader("Ejemplo de secrets (Sheets API)")
    st.code(ex.read_text(encoding="utf-8"), language="toml")
