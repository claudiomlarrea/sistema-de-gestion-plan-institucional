"""Encabezado institucional UCCuyo (sin subtítulos de secretarías)."""
from __future__ import annotations

import json
import pathlib
from typing import Optional

import streamlit as st


def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _brand_colors() -> dict[str, str]:
    p = project_root() / "assets" / "brand" / "colors.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"primary_green": "#1a5c3a", "primary_green_dark": "#0d3d24", "accent": "#c5a059"}


def render_banner(title: str = "Sistema de gestión del PEI", subtitle: Optional[str] = None) -> None:
    root = project_root()
    logo = root / "assets" / "brand" / "logo.png"
    logo_html = ""
    if logo.is_file():
        import base64

        b64 = base64.b64encode(logo.read_bytes()).decode("ascii")
        logo_html = f'<img src="data:image/png;base64,{b64}" style="height:52px;margin-right:16px;" alt="UCCuyo"/>'

    sub = f'<div style="font-size:0.95rem;opacity:0.9;margin-top:4px;">{subtitle}</div>' if subtitle else ""
    c = _brand_colors()
    g0, g1 = c.get("primary_green", "#1a5c3a"), c.get("primary_green_dark", "#0d3d24")

    st.markdown(
        f"""
<div style="background:linear-gradient(90deg,{g0} 0%,{g1} 100%);color:#fff;padding:16px 20px;border-radius:8px;margin-bottom:16px;display:flex;align-items:center;">
  {logo_html}
  <div>
    <div style="font-size:1.35rem;font-weight:700;letter-spacing:0.02em;">Universidad Católica de Cuyo</div>
    <div style="font-size:1.05rem;font-weight:500;opacity:0.95;">{title}</div>
    {sub}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
