from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]
    warnings: List[str]


def require_columns(df: pd.DataFrame, required: List[str], label: str) -> ValidationResult:
    errors = []
    for c in required:
        if c not in df.columns:
            errors.append(f"{label}: coluna obrigatória ausente: {c}")
    return ValidationResult(ok=(len(errors) == 0), errors=errors, warnings=[])


def validate_pecas_internal(pecas_internal: pd.DataFrame) -> ValidationResult:
    errors, warnings = [], []

    required = ["CT", "SEQUENCIA", "NOME_PECA", "TIPOLOGIA", "ARMACAO", "FUNDO_CM", "LATERAL_CM", "QTDE", "COMPRIMENTO_M", "VOLUME_M3_TOTAL"]
    for c in required:
        if c not in pecas_internal.columns:
            errors.append(f"Peças: coluna {c} ausente.")
    if errors:
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    for c in ["CT", "SEQUENCIA", "NOME_PECA", "TIPOLOGIA"]:
        if pecas_internal[c].isna().all():
            errors.append(f"Peças: coluna {c} está vazia (verifique o mapeamento).")

    for c in ["QTDE","COMPRIMENTO_M","VOLUME_M3_TOTAL","FUNDO_CM","LATERAL_CM"]:
        if not pecas_internal[c].notna().any():
            warnings.append(f"Peças: coluna {c} parece toda vazia (verifique o mapeamento).")

    return ValidationResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)
