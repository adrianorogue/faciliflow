from __future__ import annotations

DEFAULT_PARAMS = {
    "capacidade_m3_dia": 30.0,
}

REQUIRED_OBRAS_ETAPAS_COLS = [
    "CT",
    "NOME OBRA",
    "ETAPA",
    "ATIVA (S/N)",
    "GC",
    "XML (S/N)",
    "PEÇA x PEÇA (S/N)",
]

REQUIRED_SEQ_PROD_COLS = [
    "CT",
    "ETAPA",
    "SEQUENCIA",
    "VOLUME",
    "DATA_INICIO_PRODUÇÃO",
    "DATA_FIM_PRODUÇÃO",
    "DATA_INICIO_MONTAGEM",
    "DATA_FIM_MONTAGEM",
]

# MVP simples: colunas fixas para o Excel de peças (sem mapeamento)
REQUIRED_PECAS_COLS = [
    "CT",
    "ETAPA",
    "SEQUENCIA",
    "NOME PEÇA",
    "TIPOLOGIA",
    "TIPO ARMAÇÃO",
    "FUNDO (CM)",
    "LATERAL (CM)",
    "QTDE",
    "COMPRIMENTO (M)",   # unitário -> multiplicar por QTDE
    "VOLUME (M3)",       # total da linha (todas as peças)
]
