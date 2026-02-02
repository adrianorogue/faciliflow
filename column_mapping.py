from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd


SYNONYMS = {
    "CT": ["CT", "CONTRATO", "NUMERO CONTRATO", "Nº CONTRATO", "CONTRATO Nº", "NR CONTRATO"],
    "ETAPA": ["ETAPA", "FASE"],
    "SEQUENCIA": ["SEQUENCIA", "SEQUÊNCIA", "SEQ", "SEQ MONTAGEM", "SEQUENCIA MONTAGEM", "SEQ. MONTAGEM", "SEQ MONTAGEM", "SEQ MONTAGEM ", "SEQ MONTAGEM	", "SEQ MONTAGEM", "SEQ MONTAGEM", "SEQ MONTAGEM", "SEQ MONTAGEM"],
    "NOME_PECA": ["PEÇA", "PECA", "NOME PEÇA", "NOME PECA", "DESCRIÇÃO", "DESCRICAO"],
    "TIPOLOGIA": ["TIPOLOGIA", "TIPO", "ELEMENTO", "PRODUTO"],
    "ARMACAO": ["ARMACAO", "ARMAÇÃO", "ARMADURA", "TIPO ARMACAO", "TIPO ARMAÇÃO", "ARMAÇÃO"],
    "QTDE": ["QTDE", "QTD", "QUANTIDADE", "QTY"],
    "COMPRIMENTO_M": ["COMPRIMENTO_M", "COMPRIMENTO", "COMPRIMENTO (M)", "COMP (M)", "COMPRIMENTO (m)", "L (M)", "LENGTH"],
    "VOLUME_M3_TOTAL": ["VOLUME_M3", "VOLUME", "VOLUME (M3)", "VOLUME (M³)", "VOLUME TOTAL", "M3", "M³"],
    "FUNDO_CM": ["FUNDO_CM", "FUNDO (CM)", "FUNDO", "ALTURA", "ALTURA (CM)", "H (CM)", "FUNDO (cm)"],
    "LATERAL_CM": ["LATERAL_CM", "LATERAL (CM)", "LATERAL", "LARGURA", "LARGURA (CM)", "B (CM)", "LATERAL (cm)"],
}


def guess_mapping(cols: List[str]) -> Dict[str, Optional[str]]:
    cols_upper = [str(c).upper() for c in cols]
    mapping: Dict[str, Optional[str]] = {k: None for k in SYNONYMS.keys()}
    for internal, synonyms in SYNONYMS.items():
        for s in synonyms:
            if s.upper() in cols_upper:
                mapping[internal] = cols[cols_upper.index(s.upper())]
                break
    return mapping


def apply_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    out = pd.DataFrame()
    for internal, src in mapping.items():
        if src and src in df.columns:
            out[internal] = df[src]
        else:
            out[internal] = None
    return out
