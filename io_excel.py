from __future__ import annotations

from io import BytesIO
from typing import Optional

import pandas as pd


def normalize_columns(cols: list[str]) -> list[str]:
    """Normaliza nomes de colunas vindos de Excel.
    Regras (MVP):
    - strip + UPPER
    - remove '*' (muito comum para marcar obrigatória)
    - substitui quebras de linha por espaço
    - colapsa múltiplos espaços
    """
    out: list[str] = []
    for c in cols:
        s = str(c).replace("\n", " ").strip().upper()
        s = s.replace("*", "")
        s = " ".join(s.split())
        out.append(s)
    return out


def read_excel_any(content: bytes, sheet: Optional[str] = None) -> pd.DataFrame:
    """Lê Excel a partir de bytes e retorna DataFrame.
    - Tenta a primeira aba por padrão.
    - Normaliza nomes de colunas.
    """
    bio = BytesIO(content)
    df = pd.read_excel(bio, sheet_name=sheet or 0, engine="openpyxl")
    df.columns = normalize_columns(list(df.columns))
    return df


def coerce_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce", dayfirst=True)
    return out
