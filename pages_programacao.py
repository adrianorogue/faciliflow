from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from scheduler import build_mix_diario_simple
from ui import set_toast
from grid import show_grid


def _to_excel_bytes(df: pd.DataFrame, sheet_name: str = "MIX") -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return bio.getvalue()


def _pinned_totals_row(df: pd.DataFrame, label_col: str) -> dict:
    tot_comp = pd.to_numeric(df.get("Comprimento Total de Fundo (m)", pd.Series(dtype=float)), errors="coerce").sum() if "Comprimento Total de Fundo (m)" in df.columns else 0.0
    tot_vol = pd.to_numeric(df.get("Volume", pd.Series(dtype=float)), errors="coerce").sum() if "Volume" in df.columns else 0.0
    row = {c: "" for c in df.columns}
    if label_col in row:
        row[label_col] = "TOTAL"
    if "Comprimento Total de Fundo (m)" in row:
        row["Comprimento Total de Fundo (m)"] = float(tot_comp)
    if "Volume" in row:
        row["Volume"] = float(tot_vol)
    return row


def _aggregate(df_daily: pd.DataFrame, mode: str, capacidade_m3_dia: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (df_view, df_chart)"""
    if df_daily is None or df_daily.empty:
        return df_daily, pd.DataFrame()

    d = df_daily.copy()
    d["Data"] = pd.to_datetime(d["Data"], errors="coerce")

    if mode == "Diária":
        d["Periodo"] = d["Data"].dt.date.astype(str)
    elif mode == "Semanal":
        iso = d["Data"].dt.isocalendar()
        d["Periodo"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
    else:
        d["Periodo"] = d["Data"].dt.to_period("M").astype(str)

    gcols = ["Periodo", "Tipologia", "Tipo Armação", "Fundo (cm)", "Lateral (cm)", "Setup"]
    df_view = (
        d.groupby(gcols, dropna=False)
         .agg({
             "Comprimento Total de Fundo (m)": "sum",
             "Volume": "sum",
             "Seq de Montagem": lambda s: ";".join(sorted({str(x) for x in s.dropna().astype(str)})),
             "Nome Peças": lambda s: ";".join(sorted({p.strip() for x in s.dropna().astype(str) for p in str(x).split(";") if p.strip()})),
         })
         .reset_index()
         .rename(columns={"Periodo": "Data"})
    )

    # Chart (demanda x capacidade)
    chart = d.groupby("Periodo", dropna=False).agg({"Volume": "sum"}).reset_index().rename(columns={"Periodo": "Data", "Volume": "Demanda (m³)"})
    # capacidade por período:
    # diária -> 1 dia; semanal/mensal -> nº de dias únicos (do daily)
    days_per_period = d.groupby("Periodo")["Data"].nunique().reset_index().rename(columns={"Periodo":"Data","Data":"Dias"})
    chart = chart.merge(days_per_period, on="Data", how="left")
    chart["Capacidade (m³)"] = chart["Dias"].fillna(0).astype(float) * float(capacidade_m3_dia)
    chart = chart.drop(columns=["Dias"])
    chart = chart.set_index("Data")

    return df_view, chart


def page_programacao() -> None:
    st.subheader("Mix de Produção")

    df_seq = st.session_state.get("df_seq_montagem")
    df_pecas = st.session_state.get("df_pecas")
    params = st.session_state.get("params", {})
    capacidade = float(params.get("capacidade_m3_dia", 30.0))

    issues = []
    if df_seq is None or df_seq.empty:
        issues.append("Sequências de produção não cadastradas.")
    if df_pecas is None or df_pecas.empty:
        issues.append("Peças não cadastradas.")
    if capacidade <= 0:
        issues.append("Capacidade (m³/dia) inválida. Ajuste na tela **Peças**.")

    if issues:
        for it in issues:
            st.warning(it)
        return

    # valida datas
    tmp = df_seq.copy()
    tmp["DATA_INICIO_PRODUÇÃO"] = pd.to_datetime(tmp.get("DATA_INICIO_PRODUÇÃO"), errors="coerce", dayfirst=True)
    tmp["DATA_FIM_PRODUÇÃO"] = pd.to_datetime(tmp.get("DATA_FIM_PRODUÇÃO"), errors="coerce", dayfirst=True)
    missing_dates = tmp["DATA_INICIO_PRODUÇÃO"].isna() | tmp["DATA_FIM_PRODUÇÃO"].isna()
    if missing_dates.any():
        st.warning(f"Existem {int(missing_dates.sum())} linhas de sequências sem DATA_INICIO_PRODUÇÃO ou DATA_FIM_PRODUÇÃO. Elas serão ignoradas no mix.")

    st.divider()

    mode = st.selectbox("Visualização", ["Diária", "Semanal", "Mensal"], index=0)

    if st.button("Gerar Mix", type="primary", use_container_width=True):
        out = build_mix_diario_simple(
            pecas=df_pecas,
            seq_producao=df_seq,
            capacidade_m3_dia=capacidade,
            use_business_days=True,
        )
        st.session_state["mix_diario_raw"] = out.mix_diario
        st.session_state["mix_pendencias"] = out.pendencias
        set_toast("Mix gerado com sucesso.")
        st.rerun()

    df_raw = st.session_state.get("mix_diario_raw")
    df_pend = st.session_state.get("mix_pendencias")

    if df_raw is None:
        st.info("Clique em **Gerar Mix** para visualizar.")
        return

    if df_pend is not None and not df_pend.empty:
        st.markdown("### Avisos / Pendências")
        show_grid(df_pend, key="grid_pend", height=260)

    # tabela
    df_view, df_chart = _aggregate(df_raw, mode, capacidade_m3_dia=capacidade)

    if df_view is None or df_view.empty:
        st.warning("Mix ficou vazio para esta visualização. Veja pendências acima.")
        return

    st.divider()
    st.markdown(f"### Mix ({mode})")

    # ordena
    sort_cols = ["Data", "Setup", "Tipologia", "Tipo Armação"]
    for c in sort_cols:
        if c not in df_view.columns:
            sort_cols.remove(c)
    if sort_cols:
        df_view = df_view.sort_values(sort_cols, kind="mergesort")

    pinned = _pinned_totals_row(df_view, label_col="Data")
    show_grid(df_view, key=f"grid_mix_{mode}", height=560, pinned_bottom=pinned)

    st.download_button(
        "Baixar Mix (Excel)",
        data=_to_excel_bytes(df_view, sheet_name="MIX"),
        file_name=f"FaciliFlow_MIX_{mode}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # gráfico
    st.divider()
    st.markdown("### Demanda x Capacidade")
    if df_chart is not None and not df_chart.empty:
        st.line_chart(df_chart)
    else:
        st.info("Sem dados para gráfico.")
