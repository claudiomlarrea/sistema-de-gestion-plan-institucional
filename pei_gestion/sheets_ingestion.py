"""Lectura de Google Sheets vía API (credenciales en st.secrets o JSON en variable de entorno)."""
from __future__ import annotations

import io
import json
import os
import pathlib
from typing import Any, Optional

import pandas as pd

try:
    import gspread
    from google.oauth2.service_account import Credentials

    _HAS_GSPREAD = True
except ImportError:
    _HAS_GSPREAD = False


def _service_account_info() -> Optional[dict[str, Any]]:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        return json.loads(raw)
    p = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if p and pathlib.Path(p).is_file():
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    return None


def load_sheet_as_dataframe_from_secrets(streamlit_secrets: Any) -> pd.DataFrame:
    """Usa bloque [google_service_account] + sheets.spreadsheet_id + sheets.worksheet en secrets."""
    if not _HAS_GSPREAD:
        raise RuntimeError("Instale gspread y google-auth: pip install gspread google-auth")
    raw_sa = streamlit_secrets["google_service_account"]
    info = dict(raw_sa) if not isinstance(raw_sa, dict) else raw_sa
    sid = dict(streamlit_secrets["sheets"])["spreadsheet_id"]
    wname = dict(streamlit_secrets["sheets"]).get("worksheet", "Respuestas de formulario 1")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sid)
    ws = sh.worksheet(wname) if not str(wname).isdigit() else sh.get_worksheet(int(wname))
    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame()
    header, body = rows[0], rows[1:]
    return pd.DataFrame(body, columns=header)


def load_sheet_as_dataframe_optional() -> Optional[pd.DataFrame]:
    """Fuera de Streamlit: usa variables de entorno."""
    info = _service_account_info()
    if not info or not _HAS_GSPREAD:
        return None
    sid = os.environ.get("SHEETS_SPREADSHEET_ID")
    wname = os.environ.get("SHEETS_WORKSHEET", "Respuestas de formulario 1")
    if not sid:
        return None
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(sid).worksheet(wname)
    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows[1:], columns=rows[0])


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
