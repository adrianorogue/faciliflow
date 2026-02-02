from __future__ import annotations

import streamlit as st
import pandas as pd

from constants import REQUIRED_PECAS_INTERNAL, REQUIRED_SEQ_PROD_COLS, REQUIRED_FORMAS_COLS
from validators import require_columns, validate_pecas_internal


def page_validacao() -> None:
    st.subheader("Validação")
    st.write("Checagens: estrutura mínima e consistência entre peças, sequência de produção e mapa de formas.")

    df_pecas = st.session_state.get("df_pecas")
    df_seq = st.session_state.get("df_seq_montagem")
    df_formas = st.session_state.get("df_formas")

    if df_pecas is None or df_seq is None or df_formas is None:
        st.warning("Complete **Cadastro de Obras**, **Formas** e **Uploads (Peças)** para habilitar as validações.")
        return

    vr_p = require_columns(df_pecas, REQUIRED_PECAS_INTERNAL, "Peças (padrão interno)")
    vr_s = require_columns(df_seq, REQUIRED_SEQ_PROD_COLS, "Sequência de montagem (produção)")
    vr_f = require_columns(df_formas, REQUIRED_FORMAS_COLS, "Formas (Mapa)")

    errs = vr_p.errors + vr_s.errors + vr_f.errors
    if errs:
        st.error("\n".join(errs))
        return

    vpi = validate_pecas_internal(df_pecas)
    if not vpi.ok:
        st.error("\n".join(vpi.errors))
        return
    for w in vpi.warnings:
        st.warning(w)

    # checar se CT/SEQUENCIA das peças existe no cadastro de sequência (CT/ETAPA/SEQUENCIA)
    pkey = df_pecas[["CT", "SEQUENCIA"]].astype(str).apply(lambda s: s.str.strip())
    skey = df_seq[["CT", "SEQUENCIA"]].astype(str).apply(lambda s: s.str.strip())
    pset = set(map(tuple, pkey.dropna().values.tolist()))
    sset = set(map(tuple, skey.dropna().values.tolist()))

    missing = sorted(list(pset - sset))[:100]
    if missing:
        st.warning("Existem combinações **CT/SEQUENCIA** nas peças que não estão na aba SEQUENCIA DE MONTAGEM (mostrando até 100):")
        st.dataframe(pd.DataFrame(missing, columns=["CT", "SEQUENCIA"]), use_container_width=True)
    else:
        st.success("CT/SEQUENCIA das peças estão presentes na SEQUENCIA DE MONTAGEM.")

    # checa datas válidas
    df_seq2 = df_seq.copy()
    df_seq2["DATA_INICIO_PRODUÇÃO"] = pd.to_datetime(df_seq2["DATA_INICIO_PRODUÇÃO"], errors="coerce", dayfirst=True)
    df_seq2["DATA_FIM_PRODUÇÃO"] = pd.to_datetime(df_seq2["DATA_FIM_PRODUÇÃO"], errors="coerce", dayfirst=True)
    bad_dates = df_seq2[df_seq2["DATA_INICIO_PRODUÇÃO"].isna() | df_seq2["DATA_FIM_PRODUÇÃO"].isna()]
    if not bad_dates.empty:
        st.warning("Há sequências com datas de produção inválidas/vazias:")
        st.dataframe(bad_dates[["CT","ETAPA","SEQUENCIA","DATA_INICIO_PRODUÇÃO","DATA_FIM_PRODUÇÃO"]], use_container_width=True)
    else:
        st.success("Datas de produção estão preenchidas para as sequências.")

    st.info("A compatibilidade com formas (TIPO/ARMAÇÃO/FUNDO/LATERAL) é aplicada na geração do MIX.")
