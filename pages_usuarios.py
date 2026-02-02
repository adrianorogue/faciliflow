from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import current_user, load_users_raw, save_users_raw, _make_password_record
from ui import set_toast
from grid import show_grid


def page_usuarios() -> None:
    u = current_user()
    if not u or u.role != "admin":
        st.error("Acesso restrito.")
        return

    st.subheader("Usuários")
    st.caption("Cadastro e manutenção de usuários planejadores.")

    raw = load_users_raw()

    # Tabela
    rows = []
    for username, rec in raw.items():
        rows.append({
            "username": username,
            "nome": rec.get("name", username),
            "perfil": rec.get("role", "planner"),
            "ativo": bool(rec.get("active", True)),
        })

    df = pd.DataFrame(rows).sort_values(["perfil", "username"]) if rows else pd.DataFrame(columns=["username","nome","perfil","ativo"])

    st.markdown("### Lista")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Novo usuário")
        with st.form("form_new_user", clear_on_submit=True):
            username = st.text_input("Usuário (login)", placeholder="ex: joao.silva")
            name = st.text_input("Nome")
            role = st.selectbox("Perfil", ["planner", "admin"], index=0)
            password = st.text_input("Senha inicial", type="password")
            active = st.checkbox("Ativo", value=True)
            ok = st.form_submit_button("Cadastrar", use_container_width=True)

        if ok:
            ukey = username.strip().lower()
            if not ukey:
                st.error("Informe o usuário (login).")
            elif ukey in raw:
                st.error("Este usuário já existe.")
            elif not password.strip():
                st.error("Informe uma senha inicial.")
            else:
                raw[ukey] = {
                    "name": name.strip() or ukey,
                    "role": role,
                    "active": bool(active),
                    "password": _make_password_record(password.strip()),
                }
                save_users_raw(raw)
                set_toast("Usuário cadastrado com sucesso.")
                st.rerun()

    with c2:
        st.markdown("### Manutenção")
        sel = st.selectbox("Selecionar usuário", ["(selecione)"] + sorted(raw.keys()), index=0)
        if sel != "(selecione)":
            rec = raw.get(sel, {})
            with st.form("form_edit_user", clear_on_submit=False):
                name2 = st.text_input("Nome", value=str(rec.get("name", sel)))
                role2 = st.selectbox("Perfil", ["planner", "admin"], index=0 if rec.get("role","planner")=="planner" else 1)
                active2 = st.checkbox("Ativo", value=bool(rec.get("active", True)))
                new_pass = st.text_input("Nova senha (opcional)", type="password", placeholder="deixe em branco para manter")
                bsave = st.form_submit_button("Salvar alterações", type="primary", use_container_width=True)

            if bsave:
                rec["name"] = name2.strip() or sel
                rec["role"] = role2
                rec["active"] = bool(active2)
                if new_pass.strip():
                    rec["password"] = _make_password_record(new_pass.strip())
                raw[sel] = rec
                save_users_raw(raw)
                set_toast("Usuário atualizado.")
                st.rerun()

            # Excluir (com trava)
            if sel == u.username:
                st.info("Você não pode excluir o usuário que está logado.")
            else:
                if st.button("Excluir usuário", type="secondary", use_container_width=True):
                    raw.pop(sel, None)
                    save_users_raw(raw)
                    set_toast("Usuário excluído.")
                    st.rerun()
