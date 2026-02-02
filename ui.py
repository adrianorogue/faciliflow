from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal, Optional

import streamlit as st


ToastKind = Literal["success", "info", "warning", "error"]


def inject_global_css(primary: str = "#5271FF", accent: str = "#38B6FF") -> None:
    st.markdown(
        f"""
    <style>
      /* Layout */
      .block-container {{ padding-top: 1.0rem; padding-bottom: 2.5rem; }}
      header, footer {{ visibility: hidden; }}

      /* App header */
      .ff-header {{
        display:flex;
        align-items:center;
        gap: 14px;
        padding: 10px 14px;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        border-radius: 14px;
        box-shadow: 0 1px 10px rgba(2,6,23,0.04);
        margin-bottom: 14px;
      }}
      .ff-title {{
        font-size: 1.35rem;
        font-weight: 750;
        color: #0F172A;
        line-height: 1.1;
        margin: 0;
      }}
      .ff-subtitle {{
        font-size: 0.92rem;
        color: #475569;
        margin: 2px 0 0 0;
      }}
      .ff-badge {{
        margin-left:auto;
        font-size: 0.82rem;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(56,182,255,0.12);
        border: 1px solid rgba(56,182,255,0.35);
        color: #0F172A;
      }}

      /* Buttons (geral) */
      div.stButton > button {{
        border-radius: 12px !important;
        border: 1px solid rgba(82,113,255,0.35) !important;
      }}
      div.stButton > button[kind="primary"] {{
        background: {primary} !important;
        border: 1px solid {primary} !important;
      }}

      /* Inputs */
      input, textarea {{
        border-radius: 10px !important;
      }}

      /* Sidebar */
      [data-testid="stSidebar"] {{
        background: #FFFFFF;
        border-right: 1px solid #E2E8F0;
      }}
      [data-testid="stSidebar"] .stMarkdown p {{
        color: #475569;
      }}

      /* Navegação em "caixas" (pills) - estiliza o radio */
      [data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 8px;
      }}
      [data-testid="stSidebar"] div[role="radiogroup"] label {{
        width: 100%;
        border: 1px solid #E2E8F0;
        border-radius: 999px;
        padding: 8px 10px;
        margin: 0 !important;
        background: #FFFFFF;
        box-shadow: 0 1px 10px rgba(2,6,23,0.02);
      }}
      /* some com o circulozinho padrão */
      [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
        display: none !important;
      }}
      /* texto da opção */
      [data-testid="stSidebar"] div[role="radiogroup"] label p {{
        margin: 0 !important;
        font-weight: 600;
        color: #0F172A;
      }}
      /* opção selecionada: borda + fundo suave */
      [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        border: 1px solid rgba(82,113,255,0.55);
        background: rgba(82,113,255,0.06);
      }}

      /* deixa o botão Sair discreto */
      [data-testid="stSidebar"] div.stButton > button {{
        border-radius: 999px !important;
      }}

      /* File uploader: esconde instrução padrão (em inglês) e usamos nossos próprios rótulos */
[data-testid="stFileUploaderDropzoneInstructions"] {{ display: none !important; }}
[data-testid="stFileUploaderDropzone"] {{ padding-top: 0.6rem; padding-bottom: 0.6rem; }}

/* Responsividade */
@media (max-width: 860px) {{
  .block-container {{ padding-left: 0.8rem; padding-right: 0.8rem; }}
  .ff-header {{ flex-wrap: wrap; gap: 10px; }}
  .ff-badge {{ margin-left: 0; width: 100%; text-align: center; }}
}}
@media (max-width: 520px) {{
  .ff-title {{ font-size: 1.15rem; }}
  .ff-subtitle {{ font-size: 0.85rem; }}
  .ff-header img {{ width: 38px; height: 38px; }}
  .ff-toast {{ right: 10px; left: 10px; max-width: none; }}
}}

/* Toast (top-right), auto-hide 3s via CSS animation */

      @keyframes ffToastFade {{
        0%   {{ opacity: 0; transform: translateY(-8px); }}
        10%  {{ opacity: 1; transform: translateY(0px); }}
        85%  {{ opacity: 1; transform: translateY(0px); }}
        100% {{ opacity: 0; transform: translateY(-8px); }}
      }}
      .ff-toast {{
        position: fixed;
        top: 14px;
        right: 18px;
        z-index: 100000;
        padding: 10px 12px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(2,6,23,0.18);
        font-weight: 650;
        font-size: 0.92rem;
        max-width: 360px;
        animation: ffToastFade 3s ease-in-out forwards;
      }}
      .ff-toast.success {{
        background: rgba(34,197,94,0.14);
        border: 1px solid rgba(34,197,94,0.35);
        color: #065F46;
      }}
      .ff-toast.info {{
        background: rgba(56,182,255,0.14);
        border: 1px solid rgba(56,182,255,0.35);
        color: #0F172A;
      }}
      .ff-toast.warning {{
        background: rgba(245,158,11,0.16);
        border: 1px solid rgba(245,158,11,0.35);
        color: #7C2D12;
      }}
      .ff-toast.error {{
        background: rgba(239,68,68,0.14);
        border: 1px solid rgba(239,68,68,0.35);
        color: #7F1D1D;
      }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def header(logo_path: str, subtitle: str, badge_text: str = "MVP") -> None:
    logo_b64 = _img_to_base64(logo_path)
    st.markdown(
        f"""
      <div class="ff-header">
        <img src="data:image/png;base64,{logo_b64}" width="44" height="44" style="border-radius:10px;" />
        <div>
          <p class="ff-title">FaciliFlow</p>
          <p class="ff-subtitle">{subtitle}</p>
        </div>
        <div class="ff-badge">{badge_text}</div>
      </div>
    """,
        unsafe_allow_html=True,
    )


def set_toast(message: str, kind: ToastKind = "success") -> None:
    """Agenda um toast para aparecer no próximo rerun."""
    st.session_state["ff_toast"] = {"message": message, "kind": kind}


def render_toast() -> None:
    """Renderiza o toast (se existir) e limpa do session_state."""
    data = st.session_state.pop("ff_toast", None)
    if not data:
        return
    msg = str(data.get("message", "")).strip()
    kind = str(data.get("kind", "success")).strip().lower()
    if not msg:
        return
    if kind not in ["success", "info", "warning", "error"]:
        kind = "success"

    st.markdown(f'<div class="ff-toast {kind}">{msg}</div>', unsafe_allow_html=True)


def _img_to_base64(path: str) -> str:
    p = Path(path)
    data = p.read_bytes()
    return base64.b64encode(data).decode("utf-8")
