from __future__ import annotations

from io import BytesIO
from typing import Optional, List

import pandas as pd
import streamlit as st

from constants import REQUIRED_OBRAS_ETAPAS_COLS, REQUIRED_SEQ_PROD_COLS
from io_excel import read_excel_any, coerce_dates
from ui import set_toast


ASSETS = "assets"
TEMPLATE_PATH = f"{ASSETS}/FaciliFlow_Modelo_Cadastro_Obras.xlsx"


def _export_excel(df_obras: pd.DataFrame, df_seq: pd.DataFrame) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df_obras.to_excel(writer, index=False, sheet_name="OBRAS")
        df_seq.to_excel(writer, index=False, sheet_name="SEQUENCIA DE MONTAGEM")
    return bio.getvalue()


def _try_read_sheet(content: bytes, candidates: List[str]) -> Optional[pd.DataFrame]:
    for s in candidates:
        try:
            return read_excel_any(content, sheet=s)
        except Exception:
            continue
    return None


def page_cadastro_obras() -> None:
    st.subheader("Obras")

    # ------- Importação (layout melhorado)
    with st.container(border=True):
        st.markdown("### Importação")
        c1, c2, c3 = st.columns([1.2, 2.6, 1.0], vertical_alignment="center")

        with c1:
            try:
                with open(TEMPLATE_PATH, "rb") as f:
                    st.download_button(
                        "Modelo (Excel)",
                        data=f.read(),
                        file_name="FaciliFlow_Modelo_Cadastro_Obras.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            except Exception:
                st.caption("")

        with c2:
            up = st.file_uploader("Selecione o arquivo para importar", type=["xlsx", "xls"], key="up_cadastro")

        with c3:
            do_import = st.button("Importar", type="primary", use_container_width=True, disabled=(up is None))

    # ------- Cadastro manual (nova obra)
    with st.container(border=True):
        st.markdown("### Nova obra")
        with st.form("form_nova_obra", clear_on_submit=True):
            f1, f2 = st.columns([1.1, 2.9])
            with f1:
                ct_new = st.text_input("CT", value="")
            with f2:
                nome_new = st.text_input("Nome da obra", value="")

            e1, e2, e3, e4 = st.columns([1.2, 1.0, 1.0, 1.2])
            with e1:
                etapa_new = st.text_input("Primeira etapa", value="ETAPA 1")
            with e2:
                ativa_new = st.selectbox("Ativa (S/N)", ["S", "N"], index=0)
            with e3:
                xml_new = st.selectbox("XML (S/N)", ["N", "S"], index=0)
            with e4:
                peca_new = st.selectbox("Peça x Peça (S/N)", ["N", "S"], index=0)

            gc_new = st.text_input("GC", value="")

            submitted = st.form_submit_button("Adicionar obra", type="primary", use_container_width=True)

        if submitted:
            ct_new = ct_new.strip()
            nome_new = nome_new.strip()
            etapa_new = etapa_new.strip()

            if not ct_new or not nome_new or not etapa_new:
                st.error("Preencha CT, Nome da obra e Primeira etapa.")
            else:
                df_obras_etapas = st.session_state.get("df_obras_etapas")
                if df_obras_etapas is None:
                    df_obras_etapas = pd.DataFrame(columns=REQUIRED_OBRAS_ETAPAS_COLS)

                dup = False
                if not df_obras_etapas.empty:
                    dup = (
                        (df_obras_etapas["CT"].astype(str).str.strip() == ct_new) &
                        (df_obras_etapas["ETAPA"].astype(str).str.strip().str.upper() == etapa_new.upper())
                    ).any()

                if dup:
                    st.warning("Essa obra/etapa já existe. Use a expansão da obra para editar ou adicionar novas etapas.")
                else:
                    row = {
                        "CT": ct_new,
                        "NOME OBRA": nome_new,
                        "ETAPA": etapa_new,
                        "ATIVA (S/N)": ativa_new,
                        "GC": gc_new.strip(),
                        "XML (S/N)": xml_new,
                        "PEÇA x PEÇA (S/N)": peca_new,
                    }
                    df_obras_etapas = pd.concat([df_obras_etapas, pd.DataFrame([row])], ignore_index=True)
                    st.session_state["df_obras_etapas"] = df_obras_etapas
                    set_toast("Obra adicionada com sucesso.")
                    st.rerun()

    # ------- Importação: aplica ao carregar arquivo
    if up is not None and do_import:
        content = up.getvalue()
        df_obras = _try_read_sheet(content, ["OBRAS", "OBRA", "CADASTRO_OBRAS"])
        df_seq = _try_read_sheet(content, ["SEQUENCIA DE MONTAGEM", "SEQUENCIAS_MONTAGEM", "SEQUENCIAS MONTAGEM"])

        if df_obras is None:
            st.error("Aba 'OBRAS' não encontrada.")
            return
        if df_seq is None:
            st.error("Aba 'SEQUENCIA DE MONTAGEM' não encontrada.")
            return

        for c in REQUIRED_OBRAS_ETAPAS_COLS:
            if c not in df_obras.columns:
                df_obras[c] = None
        for c in REQUIRED_SEQ_PROD_COLS:
            if c not in df_seq.columns:
                df_seq[c] = None

        df_obras = df_obras[REQUIRED_OBRAS_ETAPAS_COLS].copy()
        df_seq = df_seq[REQUIRED_SEQ_PROD_COLS].copy()
        df_seq = coerce_dates(df_seq, ["DATA_INICIO_PRODUÇÃO","DATA_FIM_PRODUÇÃO","DATA_INICIO_MONTAGEM","DATA_FIM_MONTAGEM"])

        st.session_state["df_obras_etapas"] = df_obras
        st.session_state["df_seq_montagem"] = df_seq
        set_toast("Cadastro importado com sucesso.")
        st.rerun()

    # ------- Dados atuais
    df_obras_etapas = st.session_state.get("df_obras_etapas")
    df_seq = st.session_state.get("df_seq_montagem")

    if df_obras_etapas is None:
        df_obras_etapas = pd.DataFrame(columns=REQUIRED_OBRAS_ETAPAS_COLS)
    if df_seq is None:
        df_seq = pd.DataFrame(columns=REQUIRED_SEQ_PROD_COLS)

    # base (1 linha por CT)
    base_cols = ["CT","NOME OBRA","ATIVA (S/N)","GC","XML (S/N)","PEÇA x PEÇA (S/N)"]
    obras_base = pd.DataFrame(columns=base_cols)
    if not df_obras_etapas.empty and "CT" in df_obras_etapas.columns:
        tmp = df_obras_etapas.copy()
        tmp["CT"] = tmp["CT"].astype(str).str.strip()
        tmp["NOME OBRA"] = tmp["NOME OBRA"].astype(str).str.strip()
        obras_base = (
            tmp.dropna(subset=["CT"])
               .sort_values(["CT","NOME OBRA"])
               .groupby("CT", as_index=False)
               .agg({
                   "NOME OBRA":"first",
                   "ATIVA (S/N)":"first",
                   "GC":"first",
                   "XML (S/N)":"first",
                   "PEÇA x PEÇA (S/N)":"first",
               })
        )[base_cols]

    st.divider()
    st.markdown("### Lista de obras")

    # filtros rápidos
    f1, f2, f3, f4 = st.columns([1.6, 1.2, 1.2, 1.2])
    with f1:
        q = st.text_input("Buscar", value="", placeholder="CT, nome da obra ou GC")
    with f2:
        ativa = st.selectbox("Ativa", ["(todas)", "S", "N"], index=0)
    with f3:
        xml = st.selectbox("XML", ["(todas)", "S", "N"], index=0)
    with f4:
        peca = st.selectbox("Peça x Peça", ["(todas)", "S", "N"], index=0)

    filt = obras_base.copy()
    if q.strip():
        qq = q.strip().lower()
        filt = filt[
            filt["CT"].astype(str).str.lower().str.contains(qq)
            | filt["NOME OBRA"].astype(str).str.lower().str.contains(qq)
            | filt["GC"].astype(str).str.lower().str.contains(qq)
        ]
    if ativa != "(todas)":
        filt = filt[filt["ATIVA (S/N)"].astype(str).str.upper().str.strip() == ativa]
    if xml != "(todas)":
        filt = filt[filt["XML (S/N)"].astype(str).str.upper().str.strip() == xml]
    if peca != "(todas)":
        filt = filt[filt["PEÇA x PEÇA (S/N)"].astype(str).str.upper().str.strip() == peca]

    if "obra_open" not in st.session_state:
        st.session_state["obra_open"] = {}

    if filt.empty:
        st.info("Nenhuma obra encontrada com os filtros atuais.")
        return

    # cabeçalho estilo board
    h1, h2, h3, h4, h5, h6 = st.columns([0.6, 1.2, 2.8, 1.2, 1.2, 1.4])
    h1.markdown("")
    h2.markdown("**CT**")
    h3.markdown("**Obra**")
    h4.markdown("**Ativa**")
    h5.markdown("**XML**")
    h6.markdown("**Peça x Peça**")

    def _save_seq_for_ct(ct: str, edited: pd.DataFrame) -> None:
        nonlocal df_seq
        rest = df_seq[df_seq["CT"].astype(str).str.strip() != ct].copy()
        merged = pd.concat([rest, edited], ignore_index=True)
        merged = coerce_dates(merged, ["DATA_INICIO_PRODUÇÃO","DATA_FIM_PRODUÇÃO","DATA_INICIO_MONTAGEM","DATA_FIM_MONTAGEM"])
        st.session_state["df_seq_montagem"] = merged
        set_toast("Sequências salvas com sucesso.")
        st.rerun()

    for _, row in filt.iterrows():
        ct = str(row["CT"]).strip()
        open_now = st.session_state["obra_open"].get(ct, False)
        arrow = "▼" if open_now else "▶"

        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.2, 2.8, 1.2, 1.2, 1.4])
            with c1:
                if st.button(arrow, key=f"toggle_{ct}"):
                    st.session_state["obra_open"][ct] = not open_now
                    st.rerun()
            with c2:
                st.write(ct)
            with c3:
                st.write(str(row.get("NOME OBRA","")))
            with c4:
                st.write(str(row.get("ATIVA (S/N)","")))
            with c5:
                st.write(str(row.get("XML (S/N)","")))
            with c6:
                st.write(str(row.get("PEÇA x PEÇA (S/N)","")))

            if st.session_state["obra_open"].get(ct, False):
                st.markdown("#### Etapas")
                df_et = df_obras_etapas[df_obras_etapas["CT"].astype(str).str.strip() == ct].copy()
                df_et_edit = st.data_editor(df_et, num_rows="dynamic", use_container_width=True, key=f"editor_etapas_{ct}")

                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.button("Salvar etapas", key=f"save_etapas_{ct}", type="primary", use_container_width=True):
                        rest = df_obras_etapas[df_obras_etapas["CT"].astype(str).str.strip() != ct].copy()
                        merged = pd.concat([rest, df_et_edit], ignore_index=True)
                        st.session_state["df_obras_etapas"] = merged
                        set_toast("Etapas salvas com sucesso.")
                        st.rerun()

                with b2:
                    with st.popover("Sequências de produção", use_container_width=True):
                        df_s = df_seq[df_seq["CT"].astype(str).str.strip() == ct].copy()
                        if df_s.empty:
                            df_s = pd.DataFrame(columns=REQUIRED_SEQ_PROD_COLS)

                        # Datas como date (calendário)
                        for c in ["DATA_INICIO_PRODUÇÃO","DATA_FIM_PRODUÇÃO","DATA_INICIO_MONTAGEM","DATA_FIM_MONTAGEM"]:
                            if c in df_s.columns:
                                df_s[c] = pd.to_datetime(df_s[c], errors="coerce").dt.date

                        df_s_edit = st.data_editor(df_s, num_rows="dynamic", use_container_width=True, key=f"editor_seq_{ct}")
                        if st.button("Salvar sequências", key=f"save_seq_{ct}", type="primary", use_container_width=True):
                            _save_seq_for_ct(ct, df_s_edit)

    st.divider()
    st.download_button(
        "Exportar cadastro (Excel)",
        data=_export_excel(st.session_state.get("df_obras_etapas", df_obras_etapas), st.session_state.get("df_seq_montagem", df_seq)),
        file_name="FaciliFlow_Cadastro_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
