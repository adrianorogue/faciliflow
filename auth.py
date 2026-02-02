from __future__ import annotations

import hmac
import json
import os
import base64
import hashlib
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import streamlit as st


DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"


@dataclass(frozen=True)
class User:
    username: str
    name: str
    role: str = "planner"   # admin | planner
    active: bool = True


def _pbkdf2_hash(password: str, salt: bytes, iterations: int = 120_000) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def _make_password_record(password: str) -> Dict[str, str]:
    salt = secrets.token_bytes(16)
    digest = _pbkdf2_hash(password, salt)
    return {
        "salt_b64": base64.b64encode(salt).decode("utf-8"),
        "hash_b64": base64.b64encode(digest).decode("utf-8"),
        "algo": "pbkdf2_sha256",
        "iterations": 120_000,
    }


def _verify_password(password: str, rec: Dict[str, str]) -> bool:
    try:
        salt = base64.b64decode(rec.get("salt_b64", ""))
        expected = base64.b64decode(rec.get("hash_b64", ""))
        it = int(rec.get("iterations", 120_000))
    except Exception:
        return False
    got = _pbkdf2_hash(password, salt, it)
    return hmac.compare_digest(got, expected)


def _ensure_users_file() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if USERS_FILE.exists():
        return

    # usuários iniciais
    users = {
        "admin": {
            "name": "Administrador",
            "role": "admin",
            "active": True,
            "password": _make_password_record("admin123"),
        },
        "pcp": {
            "name": "PCP",
            "role": "planner",
            "active": True,
            "password": _make_password_record("pcp123"),
        },
    }
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def load_users_raw() -> Dict[str, dict]:
    _ensure_users_file()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_users_raw(data: Dict[str, dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def users() -> Dict[str, User]:
    raw = load_users_raw()
    out: Dict[str, User] = {}
    for username, rec in raw.items():
        out[username] = User(
            username=username,
            name=str(rec.get("name", username)),
            role=str(rec.get("role", "planner")),
            active=bool(rec.get("active", True)),
        )
    return out


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_user"))


def current_user() -> Optional[User]:
    return st.session_state.get("auth_user")


def logout() -> None:
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_error", None)


def login_form() -> None:
    st.markdown(
        '''
        <div style="text-align:center; margin-top: 0.25rem;">
          <h2 style="margin-bottom:0.25rem;">Acesso</h2>
          <p style="margin-top:0; color:#475569;">PCP de Pré-Fabricados • Mix de Produção</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if st.session_state.get("auth_error"):
        st.error(st.session_state["auth_error"])

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuário", placeholder="ex: pcp")
        password = st.text_input("Senha", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        ukey = username.strip().lower()
        raw = load_users_raw()
        rec = raw.get(ukey)
        if rec and bool(rec.get("active", True)) and _verify_password(password, rec.get("password", {})):
            st.session_state["auth_user"] = User(
                username=ukey,
                name=str(rec.get("name", ukey)),
                role=str(rec.get("role", "planner")),
                active=bool(rec.get("active", True)),
            )
            st.session_state.pop("auth_error", None)
            st.rerun()
        else:
            st.session_state["auth_error"] = "Usuário ou senha inválidos."
            st.rerun()
