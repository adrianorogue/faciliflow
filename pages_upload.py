from __future__ import annotations

import re
import streamlit as st
import pandas as pd

from constants import DEFAULT_PARAMS, REQUIRED_PECAS_INTERNAL
from io_excel import read_excel_any
from validators import require_columns, validate_pecas_internal
from column_mapping import guess_mapping, apply_mapping
from ui import set_toast


def _extract_seq_number(val) -> str:
    s = str(val) if val is not None else ""
    m = re.match(r"\s*(\d+)", s)
    return m.group(1) if m else s.strip()


def page_upload() -> None:
    st.subheader("Uploads (Lista de Peças)")
    st.write(
        "Envie a **Lista de Peças**. O app fará um **mapeamento de colunas** para o padrão interno "
        "e tentará extrair o número da sequência a partir do campo 'Seq Montagem' (ex.: '3 - SETOR A2' → 3)."
    )

    f_pecas = st.file_uploader("Lista de Peças (Excel)", type=["xlsx", "xls"], key="up_pecas")

    st.divider()
    st.markdown("### Parâmetros da Fábrica")
    params = st.session_state.get("params", DEFAULT_PARAMS.copy())

    params["capacidade_m3_dia"] = st.number_input(
        "Média de produção (m³/dia)",
        min_value=1.0,
        value=float(params.get("capacidade_m3_dia", 30.043275490634)),
        step=0.5,
        help="Usado para montar o MIX diário (e agregações semanal/mensal).",
    )
    st.session_state["params"] = params

    st.divider()
    st.markdown("### Mapeamento de colunas (Peças → padrão interno)")

    if not f_pecas:
        st.info("Envie um Excel para liberar o mapeamento.")
        return

    df_raw = read_excel_any(f_pecas.getvalue())
    st.session_state["df_pecas_raw"] = df_raw

    csave1, csave2 = st.columns([1, 1])
    with csave1:
        if st.button("Salvar upload", use_container_width=True):
            st.session_state["df_pecas_raw_saved"] = df_raw
            st.session_state["pecas_upload_name"] = getattr(f_pecas, "name", "Lista_de_pecas")
            set_toast("Upload salvo com sucesso.")
            st.rerun()
    with csave2:
        st.caption('Use "Salvar upload" para guardar a carga na sessão mesmo antes do mapeamento.')

    guess = guess_mapping(list(df_raw.columns))
    mapping = {}
    cols = ["(vazio)"] + list(df_raw.columns)

    cA, cB = st.columns(2)
    with cA:
        mapping["CT"] = st.selectbox("CT", cols, index=cols.index(guess["CT"]) if guess.get("CT") in cols else 0)
        mapping["ETAPA"] = st.selectbox("ETAPA (se existir)", cols, index=cols.index(guess["ETAPA"]) if guess.get("ETAPA") in cols else 0)
        mapping["SEQUENCIA"] = st.selectbox("SEQUENCIA / Seq Montagem", cols, index=cols.index(guess["SEQUENCIA"]) if guess.get("SEQUENCIA") in cols else 0)
        mapping["NOME_PECA"] = st.selectbox("NOME_PECA", cols, index=cols.index(guess["NOME_PECA"]) if guess.get("NOME_PECA") in cols else 0)
        mapping["TIPOLOGIA"] = st.selectbox("TIPOLOGIA (Produto)", cols, index=cols.index(guess["TIPOLOGIA"]) if guess.get("TIPOLOGIA") in cols else 0)
    with cB:
        mapping["ARMACAO"] = st.selectbox("ARMACAO", cols, index=cols.index(guess["ARMACAO"]) if guess.get("ARMACAO") in cols else 0)
        mapping["QTDE"] = st.selectbox("QTDE", cols, index=cols.index(guess["QTDE"]) if guess.get("QTDE") in cols else 0)
        mapping["VOLUME_M3_TOTAL"] = st.selectbox("VOLUME_M3_TOTAL", cols, index=cols.index(guess["VOLUME_M3_TOTAL"]) if guess.get("VOLUME_M3_TOTAL") in cols else 0)
        mapping["COMPRIMENTO_M"] = st.selectbox("COMPRIMENTO_M", cols, index=cols.index(guess["COMPRIMENTO_M"]) if guess.get("COMPRIMENTO_M") in cols else 0)
        mapping["FUNDO_CM"] = st.selectbox("FUNDO_CM", cols, index=cols.index(guess["FUNDO_CM"]) if guess.get("FUNDO_CM") in cols else 0)
        mapping["LATERAL_CM"] = st.selectbox("LATERAL_CM", cols, index=cols.index(guess["LATERAL_CM"]) if guess.get("LATERAL_CM") in cols else 0)

    mapping_clean = {k: (None if v == "(vazio)" else v) for k, v in mapping.items()}
    st.session_state["pecas_mapping"] = mapping_clean

    if st.button("Aplicar mapeamento", type="primary", use_container_width=True):
        df_internal = apply_mapping(df_raw, mapping_clean)

        # Normalizações
        for col in ["CT", "ETAPA", "SEQUENCIA", "NOME_PECA", "TIPOLOGIA", "ARMACAO"]:
            if col in df_internal.columns:
                df_internal[col] = df_internal[col].astype(str).str.strip()

        # Extrai número da sequência quando vier como "3 - SETOR"
        df_internal["SEQUENCIA"] = df_internal["SEQUENCIA"].apply(_extract_seq_number)

        for col in ["QTDE", "COMPRIMENTO_M", "VOLUME_M3_TOTAL", "FUNDO_CM", "LATERAL_CM"]:
            if col in df_internal.columns:
                df_internal[col] = pd.to_numeric(df_internal[col], errors="coerce")

        st.session_state["df_pecas"] = df_internal

        vr = require_columns(df_internal, REQUIRED_PECAS_INTERNAL, "Peças (padrão interno)")
        if not vr.ok:
            st.error("\n".join(vr.errors))
        else:
            set_toast("Mapeamento aplicado com sucesso.")

        v2 = validate_pecas_internal(df_internal)
        if not v2.ok:
            st.error("\n".join(v2.errors))
        for w in v2.warnings:
            st.warning(w)

        st.rerun()

    st.markdown("#### Preview (raw)")
    st.dataframe(df_raw.head(30), use_container_width=True)

    st.divider()
    st.markdown("### Peças já mapeadas (sessão)")
    df_m = st.session_state.get("df_pecas")
    if df_m is None or df_m.empty:
        st.caption("Nenhuma peça mapeada ainda.")
    else:
        c1, _ = st.columns([1, 3])
        with c1:
            cts = sorted([c for c in df_m["CT"].dropna().astype(str).str.strip().unique().tolist() if c])
            ct = st.selectbox("Filtrar por CT", ["(todos)"] + cts, index=0, key="up_ct_filter")
        view = df_m.copy()
        if ct != "(todos)":
            view = view[view["CT"].astype(str).str.strip() == ct].copy()
        st.caption(f"{view.shape[0]} linhas (mostrando até 200)")
        st.dataframe(view.head(200), use_container_width=True)
