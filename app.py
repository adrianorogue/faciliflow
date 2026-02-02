from __future__ import annotations

import streamlit as st

from auth import is_authenticated, login_form, logout, current_user
from ui import inject_global_css, header, render_toast

from pages_cadastro_obras import page_cadastro_obras
from pages_pecas import page_pecas
from pages_programacao import page_programacao
from pages_usuarios import page_usuarios


ASSETS = "assets"
LOGO = f"{ASSETS}/logo_transparente.png"

BASE_PAGES = {
    "Obras": page_cadastro_obras,
    "Peças": page_pecas,
    "Mix de Produção": page_programacao,
}



def page_login() -> None:
    inject_global_css()
    render_toast()
    st.image(LOGO, width=180)
    login_form()
    st.caption("Acesso ao sistema")


def page_shell() -> None:
    inject_global_css()
    render_toast()
    header(LOGO, subtitle="PCP de Pré-Fabricados • Mix de Produção", badge_text="Tema claro")

    u = current_user()

    pages = dict(BASE_PAGES)
    if u.role == "admin":
        pages["Usuários"] = page_usuarios

    # Barra superior (sempre visível) — fallback caso a sidebar esteja recolhida
    top1, top2, top3 = st.columns([2.2, 1.2, 0.6], vertical_alignment="center")
    with top1:
        st.caption(f"Usuário: {u.name} • Perfil: {u.role}")
    with top2:
        st.session_state.setdefault("nav_page", list(pages.keys())[0])
        page_name = st.selectbox(
            "Navegação",
            list(pages.keys()),
            index=list(pages.keys()).index(st.session_state["nav_page"]) if st.session_state["nav_page"] in pages else 0,
            label_visibility="collapsed",
            key="nav_page_select",
        )
        st.session_state["nav_page"] = page_name
    with top3:
        if st.button("Sair", use_container_width=True):
            logout()
            st.rerun()

    # Menu lateral (quando visível)
    with st.sidebar:
        st.image(LOGO, width=140)
        st.markdown(f"**Usuário:** {u.name}  ")
        st.markdown(f"**Perfil:** {u.role}")
        st.divider()
        page_side = st.radio("Navegação", list(pages.keys()), index=list(pages.keys()).index(page_name), label_visibility="collapsed")
        st.session_state["nav_page"] = page_side

    pages[st.session_state["nav_page"]]()


def main() -> None:
    st.set_page_config(
        page_title="FaciliFlow",
        page_icon="assets/favicon.ico",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if not is_authenticated():
        page_login()
    else:
        page_shell()


if __name__ == "__main__":
    main()
