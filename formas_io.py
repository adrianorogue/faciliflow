from __future__ import annotations

import pandas as pd


def normalize_formas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o Excel de mapa de formas para o padrão interno do FaciliFlow."""
    d = df.copy()
    # normaliza nomes
    d.columns = [str(c).strip().upper() for c in d.columns]

    rename = {
        "VÃO": "VAO",
        "VAO": "VAO",
        "FORMA": "FORMA",
        "TIPO": "TIPO",
        "ARMAÇÃO": "ARMACAO_FORMA",
        "ARMACAO": "ARMACAO_FORMA",
        "QUANTIDADE": "QUANTIDADE",
        "COMPRIMENTO ÚTIL (M)": "COMPRIMENTO_UTIL_M",
        "COMPRIMENTO UTIL (M)": "COMPRIMENTO_UTIL_M",
        "COMPRIMENTO UTIL": "COMPRIMENTO_UTIL_M",
        "FUNDO (CM)": "FUNDO_CM",
        "FUNDO_CM": "FUNDO_CM",
        "LATERAL (CM)": "LATERAL_CM",
        "LATERAL_CM": "LATERAL_CM",
        "STATUS": "STATUS",
    }
    for k, v in rename.items():
        if k in d.columns:
            d = d.rename(columns={k: v})

    # tipos
    if "ARMACAO_FORMA" in d.columns:
        d["ARMACAO_FORMA"] = d["ARMACAO_FORMA"].astype(str).str.strip().str.upper()

    if "TIPO" in d.columns:
        d["TIPO"] = d["TIPO"].astype(str).str.strip().str.upper()

    if "STATUS" in d.columns:
        d["STATUS"] = d["STATUS"].astype(str).str.strip().str.upper()

    # numéricos
    for c in ["QUANTIDADE", "COMPRIMENTO_UTIL_M", "FUNDO_CM", "LATERAL_CM", "VAO"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    return d
