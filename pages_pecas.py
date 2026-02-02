from __future__ import annotations

from io import BytesIO
import re
import unicodedata
import uuid

import pandas as pd
import streamlit as st

from constants import REQUIRED_PECAS_COLS, DEFAULT_PARAMS
from io_excel import read_excel_any
from ui import set_toast
from grid import show_grid


ASSETS = "assets"
TEMPLATE_PATH = f"{ASSETS}/FaciliFlow_Modelo_Pecas.xlsx"


def _norm(s: str) -> str:
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.upper()
    s = re.sub(r"\s+", " ", s)
    return s


def _guess_mapping(columns: list[str]) -> dict[str, str | None]:
    norm_cols = {_norm(c): c for c in columns}

    syn = {
        "CT": ["CT", "CONTRATO", "NUMERO CONTRATO", "N CONTRATO"],
        "ETAPA": ["ETAPA", "FASE"],
        "SEQUENCIA": ["SEQUENCIA", "SEQ", "SEQ MONTAGEM", "SEQUENCIA MONTAGEM", "SEQ. MONTAGEM"],
        "NOME PEÇA": ["NOME PECA", "NOME PEÇA", "PECA", "PEÇA", "DESCRICAO", "DESCRIÇÃO", "NOME"],
        "TIPOLOGIA": ["TIPOLOGIA", "TIPO", "PRODUTO"],
        "TIPO ARMAÇÃO": ["TIPO ARMACAO", "TIPO ARMAÇÃO", "ARMACAO", "ARMAÇÃO"],
        "FUNDO (CM)": ["FUNDO (CM)", "FUNDO", "BASE", "B (CM)", "B"],
        "LATERAL (CM)": ["LATERAL (CM)", "LATERAL", "ALTURA", "H (CM)", "H"],
        "QTDE": ["QTDE", "QTD", "QUANTIDADE", "QTDADE"],
        "COMPRIMENTO (M)": ["COMPRIMENTO (M)", "COMPRIMENTO", "COMP", "C (M)", "C"],
        "VOLUME (M3)": ["VOLUME (M3)", "VOLUME (M³)", "VOLUME", "VOL", "VOLUME TOTAL"],
    }

    out: dict[str, str | None] = {}
    for target in REQUIRED_PECAS_COLS:
        tnorm = _norm(target)
        if tnorm in norm_cols:
            out[target] = norm_cols[tnorm]
            continue

        found = None
        for s in syn.get(target, []):
            sn = _norm(s)
            if sn in norm_cols:
                found = norm_cols[sn]
                break
        out[target] = found

    return out


def _apply_mapping(df_raw: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    out = pd.DataFrame()
    for target in REQUIRED_PECAS_COLS:
        src = mapping.get(target)
        if src and src in df_raw.columns:
            out[target] = df_raw[src]
        else:
            out[target] = None
    return out


def _to_excel(df: pd.DataFrame) -> bytes:
    bio = BytesIO()
    df_out = df.copy()
    if "_id" in df_out.columns:
        df_out = df_out.drop(columns=["_id"])
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name="PECAS")
    return bio.getvalue()


def page_pecas() -> None:
    st.subheader("Peças")

    # Capacidade
    params = st.session_state.get("params", DEFAULT_PARAMS.copy())
    params["capacidade_m3_dia"] = st.number_input(
        "Capacidade média (m³/dia)",
        min_value=1.0,
        value=float(params.get("capacidade_m3_dia", 30.0)),
        step=0.5,
    )
    st.session_state["params"] = params

    st.divider()

    # Importação (layout melhorado)
    with st.container(border=True):
        st.markdown("### Importação")
        h1, h2, h3 = st.columns([1.2, 2.6, 1.0], vertical_alignment="center")
        with h1:
            try:
                with open(TEMPLATE_PATH, "rb") as f:
                    st.download_button(
                        "Modelo (Excel)",
                        data=f.read(),
                        file_name="FaciliFlow_Modelo_Pecas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            except Exception:
                st.caption("")
        with h2:
            f = st.file_uploader("Selecione o arquivo para importar", type=["xlsx", "xls"], key="up_pecas_file")
        with h3:
            st.caption("")

    # Importação com mapeamento
    if f is not None:
        df_raw = read_excel_any(f.getvalue())
        if df_raw is None or df_raw.empty:
            st.error("Arquivo sem dados.")
            return

        st.markdown("### Mapeamento de colunas")
        cols = ["(vazio)"] + list(df_raw.columns)
        guess = _guess_mapping(list(df_raw.columns))
        mapping: dict[str, str | None] = {}

        left, right = st.columns(2)
        for i, target in enumerate(REQUIRED_PECAS_COLS):
            box = left if i % 2 == 0 else right
            with box:
                g = guess.get(target)
                idx = cols.index(g) if (g in cols) else 0
                sel = st.selectbox(target, cols, index=idx, key=f"map_{target}")
                mapping[target] = None if sel == "(vazio)" else sel

        missing = [t for t, s in mapping.items() if s is None]
        if missing:
            st.warning("Colunas não mapeadas: " + ", ".join(missing))

        df_prev = _apply_mapping(df_raw, mapping)

        st.markdown("### Pré-visualização")
        st.dataframe(df_prev.head(50), use_container_width=True)

        b1, b2 = st.columns([1, 1], vertical_alignment="center")
        with b1:
            if st.button("Salvar peças", type="primary", use_container_width=True):
                df = df_prev.copy()

                for c in ["QTDE", "FUNDO (CM)", "LATERAL (CM)", "COMPRIMENTO (M)", "VOLUME (M3)"]:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

                for c in ["CT", "ETAPA", "SEQUENCIA", "NOME PEÇA", "TIPOLOGIA", "TIPO ARMAÇÃO"]:
                    df[c] = df[c].astype(str).str.strip()

                df["_id"] = [uuid.uuid4().hex for _ in range(len(df))]

                st.session_state["df_pecas"] = df
                set_toast("Peças salvas com sucesso.")
                st.rerun()
        with b2:
            st.caption("Volume (M3) é total da linha; Comprimento (M) é unitário (QTDE × COMP).")

    # Consulta
    df = st.session_state.get("df_pecas")
    if df is not None and not df.empty and "_id" not in df.columns:
        df = df.copy()
        df["_id"] = [uuid.uuid4().hex for _ in range(len(df))]
        st.session_state["df_pecas"] = df

    st.divider()
    st.markdown("### Consulta")

    if df is None or df.empty:
        st.info("Nenhuma peça cadastrada.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        cts = sorted([x for x in df["CT"].dropna().astype(str).unique().tolist() if x])
        ct = st.selectbox("CT", ["(todos)"] + cts, index=0)
    with c2:
        df2 = df if ct == "(todos)" else df[df["CT"].astype(str) == ct]
        etapas = sorted([x for x in df2["ETAPA"].dropna().astype(str).unique().tolist() if x])
        etapa = st.selectbox("Etapa", ["(todas)"] + etapas, index=0)
    with c3:
        df3 = df2 if etapa == "(todas)" else df2[df2["ETAPA"].astype(str) == etapa]
        seqs = sorted([x for x in df3["SEQUENCIA"].dropna().astype(str).unique().tolist() if x])
        seq = st.selectbox("Sequência", ["(todas)"] + seqs, index=0)

    out = df.copy()
    if ct != "(todos)":
        out = out[out["CT"].astype(str) == ct]
    if etapa != "(todas)":
        out = out[out["ETAPA"].astype(str) == etapa]
    if seq != "(todas)":
        out = out[out["SEQUENCIA"].astype(str) == seq]

    # Seleção para exclusão (opcional)
    sel_mode = st.checkbox("Selecionar linhas para excluir", value=False)

    resp = show_grid(
        out,
        key="grid_pecas",
        height=520,
        selectable=sel_mode,
        hide_columns=["_id"],
    )

    if sel_mode:
        selected = []
        try:
            selected = (resp.get("selected_rows") if resp else [])
            if selected is None:
                selected = []
        except Exception:
            selected = []
        if not isinstance(selected, list):
            selected = []
        selected_ids = [r.get("_id") for r in selected if isinstance(r, dict) and r.get("_id")]
        st.caption(f"Selecionadas: {len(selected_ids)}")

        cdel1, cdel2 = st.columns([1.2, 2.8], vertical_alignment="center")
        with cdel1:
            confirm_sel = st.text_input("Confirmação", value="", placeholder="digite EXCLUIR", key="confirm_delete_selected")
        with cdel2:
            if st.button(
                "Excluir selecionadas",
                type="secondary",
                disabled=(len(selected_ids) == 0 or confirm_sel.strip().upper() != "EXCLUIR"),
            ):
                df_all = st.session_state.get("df_pecas")
                if df_all is not None and not df_all.empty and "_id" in df_all.columns:
                    st.session_state["df_pecas"] = df_all[~df_all["_id"].isin(selected_ids)].reset_index(drop=True)
                    set_toast("Linhas selecionadas excluídas.")
                    st.rerun()

    st.divider()
    st.markdown("### Exclusão")

    with st.expander("Excluir peças", expanded=False):
        st.caption("Você pode excluir as peças filtradas (CT/Etapa/Sequência) ou limpar tudo.")
        col_a, col_b = st.columns([1, 1], vertical_alignment="center")

        with col_a:
            confirm = st.text_input("Para confirmar, digite EXCLUIR", value="", key="confirm_delete_pecas")
            if st.button("Excluir peças filtradas", type="secondary", disabled=(confirm.strip().upper() != "EXCLUIR")):
                df_all = st.session_state.get("df_pecas")
                if df_all is not None and not df_all.empty:
                    df_all2 = df_all.copy()
                    out2 = out.copy()
                    if "_id" in df_all2.columns and "_id" in out2.columns:
                        st.session_state["df_pecas"] = df_all2[~df_all2["_id"].isin(out2["_id"].tolist())].reset_index(drop=True)
                    else:
                        key_cols = ["CT", "ETAPA", "SEQUENCIA", "NOME PEÇA", "TIPOLOGIA", "TIPO ARMAÇÃO", "FUNDO (CM)", "LATERAL (CM)", "QTDE", "COMPRIMENTO (M)", "VOLUME (M3)"]
                        for c in key_cols:
                            if c not in df_all2.columns:
                                df_all2[c] = None
                            if c not in out2.columns:
                                out2[c] = None
                        sig_all = df_all2[key_cols].astype(str).agg("|".join, axis=1)
                        sig_out = set(out2[key_cols].astype(str).agg("|".join, axis=1).tolist())
                        keep = ~sig_all.isin(sig_out)
                        st.session_state["df_pecas"] = df_all2.loc[keep].reset_index(drop=True)

                    set_toast("Peças filtradas excluídas.")
                    st.rerun()

        with col_b:
            confirm_all = st.text_input("Para limpar tudo, digite LIMPAR", value="", key="confirm_delete_all_pecas")
            if st.button("Limpar todas as peças", type="secondary", disabled=(confirm_all.strip().upper() != "LIMPAR")):
                st.session_state["df_pecas"] = pd.DataFrame(columns=[c for c in df.columns if c != "_id"])
                set_toast("Todas as peças foram removidas.")
                st.rerun()

    st.download_button(
        "Baixar (Excel)",
        data=_to_excel(out),
        file_name="FaciliFlow_Pecas_Filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
