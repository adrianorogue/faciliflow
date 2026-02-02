from __future__ import annotations

import streamlit as st


def page_d5() -> None:
    st.subheader("Programação de Projeto (D-5)")
    st.write("Toda peça precisa estar detalhada **D-5 dias úteis** antes da data de fabricação.")

    params = st.session_state.get("params", {})
    st.metric("Regra atual", f"D-{params.get('d5_dias_uteis', 5)} dias úteis")

    df_d5 = st.session_state.get("df_d5")
    if df_d5 is None or df_d5.empty:
        st.info("Gere a programação na aba **Programação** para criar a lista D-5.")
        return

    st.markdown("### Entregas da Engenharia (D-5)")
    st.dataframe(df_d5, use_container_width=True)
