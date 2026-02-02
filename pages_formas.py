from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from io_excel import read_excel_any
from validators import require_columns
from constants import REQUIRED_FORMAS_COLS
from formas_io import normalize_formas
from ui import set_toast


def _empty_formas() -> pd.DataFrame:
    return pd.DataFrame(columns=REQUIRED_FORMAS_COLS)


def _export_excel(df_formas: pd.DataFrame) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df_formas.to_excel(writer, index=False, sheet_name="FORMAS")
    return bio.getvalue()


def page_formas() -> None:
    st.subheader("Formas (Mapa de Formas)")
    st.write(
        "Aqui você gerencia o **mapa de formas**. "
        "Pode importar do Excel, editar, incluir novas formas e exportar novamente."
    )

    st.info(
        "Regras de compatibilidade que o app já considera:\n"
        "- **Forma PROTENDIDA** pode fabricar **PROTENDIDA e ARMADA**\n"
        "- **Forma ARMADA** só pode fabricar **ARMADA**\n"
        "- Se a forma estiver como **'VIGA; PILAR'**, o app **não mistura VIGA e PILAR no mesmo dia** (setup inclui tipologia)."
    )

    st.divider()
    up = st.file_uploader("Importar mapa de formas (Excel)", type=["xlsx", "xls"], key="up_formas")

    if up is not None and st.button("Importar agora", type="primary", use_container_width=True):
        raw = read_excel_any(up.getvalue())
        df = normalize_formas(raw)

        vr = require_columns(df, REQUIRED_FORMAS_COLS, "FORMAS")
        if vr.ok:
            st.session_state["df_formas"] = df[REQUIRED_FORMAS_COLS].copy()
            set_toast("Formas importadas com sucesso.")
            st.rerun()
        else:
            st.error("\n".join(vr.errors))

    st.divider()
    st.markdown("### Editar no app")

    df_formas = st.session_state.get("df_formas")
    if df_formas is None:
        df_formas = _empty_formas()

    st.caption("Dica: use STATUS = INSTALADO para formas disponíveis (o app considera somente instaladas).")
    df_edit = st.data_editor(df_formas, num_rows="dynamic", use_container_width=True, key="editor_formas")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar alterações", type="primary", use_container_width=True):
            df_clean = df_edit.copy()
            # normalização rápida
            df_clean.columns = [str(c).strip().upper() for c in df_clean.columns]
            for c in ["TIPO", "ARMACAO_FORMA", "STATUS", "FORMA"]:
                if c in df_clean.columns:
                    df_clean[c] = df_clean[c].astype(str).str.strip().str.upper()
            for c in ["QUANTIDADE", "COMPRIMENTO_UTIL_M", "FUNDO_CM", "LATERAL_CM", "VAO"]:
                if c in df_clean.columns:
                    df_clean[c] = pd.to_numeric(df_clean[c], errors="coerce")

            vr = require_columns(df_clean, REQUIRED_FORMAS_COLS, "FORMAS")
            if not vr.ok:
                st.error("\n".join(vr.errors))
                return

            st.session_state["df_formas"] = df_clean[REQUIRED_FORMAS_COLS].reset_index(drop=True)
            set_toast("Formas salvas com sucesso.")
            st.rerun()

    with c2:
        data = _export_excel(df_edit)
        st.download_button(
            "Exportar formas (Excel)",
            data=data,
            file_name="FaciliFlow_Formas_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
