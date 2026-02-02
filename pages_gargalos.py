from __future__ import annotations

import streamlit as st
import pandas as pd


def page_gargalos() -> None:
    st.subheader("Gargalos / Alertas")
    params = st.session_state.get("params", {})
    cap = float(params.get("capacidade_m3_dia", 30.0))

    df_raw = st.session_state.get("mix_diario_raw")
    df_pend = st.session_state.get("mix_pendencias")

    if df_raw is None or df_raw.empty:
        st.info("Gere o MIX na aba **Produção — MIX** para ver gargalos e alertas.")
        return

    d = df_raw.copy()
    d["DATA"] = pd.to_datetime(d["DATA"], errors="coerce")

    resumo = (d.groupby(d["DATA"].dt.date)
                .agg(VOLUME_M3=("VOLUME (M3)", "sum"),
                     PISTAS=("QTD PISTAS", "sum"),
                     SETUPS=("SETUP", "nunique"))
                .reset_index()
                .rename(columns={"DATA":"DATA"}))
    resumo["CAP_M3_DIA"] = cap
    resumo["UTIL_CAP"] = resumo["VOLUME_M3"] / resumo["CAP_M3_DIA"]

    st.markdown("### Utilização diária (Volume x Capacidade)")
    st.dataframe(resumo.sort_values("DATA"), use_container_width=True)
    st.line_chart(resumo.set_index("DATA")[["VOLUME_M3", "CAP_M3_DIA"]])

    st.markdown("### Dias com maior carga")
    st.dataframe(resumo.sort_values("UTIL_CAP", ascending=False).head(20), use_container_width=True)

    if df_pend is not None and not df_pend.empty:
        st.markdown("### Pendências (principal gargalo)")
        st.warning("Pendências indicam que **não coube nas datas** informadas ou **não existe forma compatível**.")
        st.dataframe(df_pend, use_container_width=True)
