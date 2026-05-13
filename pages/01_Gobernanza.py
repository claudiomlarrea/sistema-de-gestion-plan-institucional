import streamlit as st

from pei_gestion.banner import render_banner
from pei_gestion.config_loader import project_root

render_banner(title="Sistema de gestión del PEI")
st.title("Gobernanza de datos del PEI")
p = project_root() / "docs" / "GOBERNANZA_PEI.md"
if p.is_file():
    st.markdown(p.read_text(encoding="utf-8"))
else:
    st.warning("No se encontró docs/GOBERNANZA_PEI.md")
