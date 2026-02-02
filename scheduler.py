from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple

import pandas as pd


@dataclass
class MixOutputs:
    mix_diario: pd.DataFrame
    pendencias: pd.DataFrame


def _extract_seq_number(val) -> str:
    s = str(val) if val is not None else ""
    m = re.match(r"\s*(\d+)", s)
    return m.group(1) if m else s.strip()


def _seqnum(x: str) -> int:
    m = re.match(r"\d+", str(x))
    return int(m.group(0)) if m else 999999


def build_mix_diario_simple(
    pecas: pd.DataFrame,
    seq_producao: pd.DataFrame,
    capacidade_m3_dia: float,
    use_business_days: bool = True,
) -> MixOutputs:
    """MVP simples (sem mapa de formas).

    Regras:
    - Volume (M3) na lista de peças é total da linha
    - Comprimento (M) é unitário -> Comprimento Total de Fundo = QTDE x COMPRIMENTO (M)
    - Distribuição sequencial por SETUP respeitando capacidade diária.
    - Prioridade **estrita** por CT/ETAPA: executa SEQ 1, depois SEQ 2, etc.
      Só avança para a próxima sequência quando a anterior estiver concluída.
    """
    p = pecas.copy()
    s = seq_producao.copy()

    # ---- Normalização de colunas (peças)
    for c in ["CT", "ETAPA", "SEQUENCIA", "NOME PEÇA", "TIPOLOGIA", "TIPO ARMAÇÃO"]:
        if c in p.columns:
            p[c] = p[c].astype(str).str.strip()

    if "SEQUENCIA" in p.columns:
        p["SEQUENCIA"] = p["SEQUENCIA"].apply(_extract_seq_number)

    for c in ["QTDE", "COMPRIMENTO (M)", "VOLUME (M3)", "FUNDO (CM)", "LATERAL (CM)"]:
        if c in p.columns:
            p[c] = pd.to_numeric(p[c], errors="coerce")

    p["COMP_TOTAL_FUNDO_M"] = (p.get("QTDE", 0).fillna(0) * p.get("COMPRIMENTO (M)", 0).fillna(0)).astype(float)
    p["VOL_TOTAL_M3"] = p.get("VOLUME (M3)", 0).fillna(0).astype(float)

    # ---- Normalização de colunas (sequências)
    for c in ["CT", "ETAPA", "SEQUENCIA"]:
        if c in s.columns:
            s[c] = s[c].astype(str).str.strip()
    if "SEQUENCIA" in s.columns:
        s["SEQUENCIA"] = s["SEQUENCIA"].apply(_extract_seq_number)

    s["DATA_INICIO_PRODUÇÃO"] = pd.to_datetime(s.get("DATA_INICIO_PRODUÇÃO"), errors="coerce", dayfirst=True)
    s["DATA_FIM_PRODUÇÃO"] = pd.to_datetime(s.get("DATA_FIM_PRODUÇÃO"), errors="coerce", dayfirst=True)

    seq_keys = s.dropna(subset=["CT", "ETAPA", "SEQUENCIA", "DATA_INICIO_PRODUÇÃO", "DATA_FIM_PRODUÇÃO"]).copy()
    pend: List[dict] = []

    if seq_keys.empty:
        return MixOutputs(mix_diario=pd.DataFrame(), pendencias=pd.DataFrame([{"MOTIVO": "Sequências sem datas válidas."}]))

    if p.empty:
        return MixOutputs(mix_diario=pd.DataFrame(), pendencias=pd.DataFrame([{"MOTIVO": "Lista de peças vazia."}]))

    # validação: peças sem chave
    missing_key = (
        p["CT"].isna() | (p["CT"].astype(str).str.strip() == "") |
        p["ETAPA"].isna() | (p["ETAPA"].astype(str).str.strip() == "") |
        p["SEQUENCIA"].isna() | (p["SEQUENCIA"].astype(str).str.strip() == "")
    )
    if missing_key.any():
        for _, r in p[missing_key].head(200).iterrows():
            pend.append({
                "CT": r.get("CT", ""),
                "ETAPA": r.get("ETAPA", ""),
                "SEQUENCIA": r.get("SEQUENCIA", ""),
                "NOME PEÇA": r.get("NOME PEÇA", ""),
                "MOTIVO": "Peça sem CT/ETAPA/SEQUENCIA (não programada)",
            })
        p = p[~missing_key].copy()

    if p.empty:
        return MixOutputs(mix_diario=pd.DataFrame(), pendencias=pd.DataFrame(pend))

    # cria lotes por SETUP (dentro de CT/ETAPA/SEQUENCIA)
    p["TIPOLOGIA"] = p.get("TIPOLOGIA", "").astype(str).str.strip().str.upper()
    p["TIPO ARMAÇÃO"] = p.get("TIPO ARMAÇÃO", "").astype(str).str.strip().str.upper()

    p["FUNDO (CM)"] = p.get("FUNDO (CM)", 0).fillna(0)
    p["LATERAL (CM)"] = p.get("LATERAL (CM)", 0).fillna(0)
    p["SETUP"] = p["FUNDO (CM)"].astype(int).astype(str) + "x" + p["LATERAL (CM)"].astype(int).astype(str)

    lot_cols = ["CT", "ETAPA", "SEQUENCIA", "TIPOLOGIA", "TIPO ARMAÇÃO", "FUNDO (CM)", "LATERAL (CM)", "SETUP"]
    lots = (
        p.groupby(lot_cols, dropna=False)
         .agg({
             "COMP_TOTAL_FUNDO_M": "sum",
             "VOL_TOTAL_M3": "sum",
             "NOME PEÇA": lambda x: ";".join(sorted({str(v).strip() for v in x.dropna().astype(str) if str(v).strip()})),
         })
         .reset_index()
    )
    lots = lots[lots["VOL_TOTAL_M3"] > 0].copy()
    if lots.empty:
        pend.append({"MOTIVO": "Peças sem volume > 0."})
        return MixOutputs(mix_diario=pd.DataFrame(), pendencias=pd.DataFrame(pend))

    # filas por sequência
    by_seq: Dict[Tuple[str, str, str], List[dict]] = {}
    for _, r in lots.iterrows():
        key = (str(r["CT"]).strip(), str(r["ETAPA"]).strip(), str(r["SEQUENCIA"]).strip())
        by_seq.setdefault(key, []).append({
            "CT": key[0],
            "ETAPA": key[1],
            "SEQUENCIA": key[2],
            "SEQNUM": _seqnum(key[2]),
            "TIPOLOGIA": r["TIPOLOGIA"],
            "TIPO_ARMAÇÃO": r["TIPO ARMAÇÃO"],
            "FUNDO (CM)": float(r["FUNDO (CM)"]) if pd.notna(r["FUNDO (CM)"]) else 0.0,
            "LATERAL (CM)": float(r["LATERAL (CM)"]) if pd.notna(r["LATERAL (CM)"]) else 0.0,
            "SETUP": r["SETUP"],
            "NOME PEÇAS": r["NOME PEÇA"],
            "vol_total": float(r["VOL_TOTAL_M3"]),
            "comp_total": float(r["COMP_TOTAL_FUNDO_M"]),
            "vol_rem": float(r["VOL_TOTAL_M3"]),
        })

    # ordena setups dentro de cada sequência (por setup)
    for k in list(by_seq.keys()):
        by_seq[k].sort(key=lambda x: (str(x["SETUP"]), str(x["TIPOLOGIA"]), str(x["TIPO_ARMAÇÃO"])))

    # prepara calendário global
    start = seq_keys["DATA_INICIO_PRODUÇÃO"].min().normalize()
    end = seq_keys["DATA_FIM_PRODUÇÃO"].max().normalize()
    days = pd.bdate_range(start=start, end=end, freq="B") if use_business_days else pd.date_range(start=start, end=end, freq="D")

    # índice de janelas por CT/ETAPA/SEQ
    win: Dict[Tuple[str, str, str], Tuple[pd.Timestamp, pd.Timestamp]] = {}
    for _, r in seq_keys.iterrows():
        key = (str(r["CT"]).strip(), str(r["ETAPA"]).strip(), str(r["SEQUENCIA"]).strip())
        win[key] = (r["DATA_INICIO_PRODUÇÃO"].normalize(), r["DATA_FIM_PRODUÇÃO"].normalize())

    # lista de sequências por CT/ETAPA (ordenadas)
    seq_list_by_stage: Dict[Tuple[str, str], List[Tuple[str, str, str]]] = {}
    for key in win.keys():
        ct, etapa, seq = key
        seq_list_by_stage.setdefault((ct, etapa), []).append(key)
    for stage, keys in list(seq_list_by_stage.items()):
        seq_list_by_stage[stage] = sorted(keys, key=lambda k: _seqnum(k[2]))

    # ponteiro de sequência corrente por CT/ETAPA
    current_idx: Dict[Tuple[str, str], int] = {stage: 0 for stage in seq_list_by_stage.keys()}

    mix_rows: List[dict] = []

    for day in days:
        cap_rest = float(capacidade_m3_dia)

        # percorre CT/ETAPA em ordem estável
        for stage in sorted(seq_list_by_stage.keys(), key=lambda x: (x[0], x[1])):
            if cap_rest <= 1e-9:
                break

            keys = seq_list_by_stage[stage]
            idx = current_idx.get(stage, 0)

            # avança idx se sequência anterior já acabou
            while idx < len(keys):
                k = keys[idx]
                queue = by_seq.get(k, [])
                if queue and sum(x["vol_rem"] for x in queue) > 1e-9:
                    break
                idx += 1
            current_idx[stage] = idx

            if idx >= len(keys):
                continue

            k = keys[idx]
            # só produz se o dia estiver dentro da janela dessa sequência
            w = win.get(k)
            if not w:
                continue
            w_start, w_end = w
            if not (w_start <= day.normalize() <= w_end):
                continue

            queue = by_seq.get(k, [])
            if not queue:
                continue

            # consome fila de setups sequencialmente
            i = 0
            while i < len(queue) and cap_rest > 1e-9:
                lot = queue[i]
                if lot["vol_rem"] <= 1e-9:
                    i += 1
                    continue

                take = min(lot["vol_rem"], cap_rest)
                cap_rest -= take
                lot["vol_rem"] -= take

                comp_take = lot["comp_total"] * (take / lot["vol_total"]) if lot["vol_total"] > 1e-9 else 0.0

                mix_rows.append({
                    "Data": day.date(),
                    "Tipologia": lot["TIPOLOGIA"],
                    "Tipo Armação": lot["TIPO_ARMAÇÃO"],
                    "Fundo (cm)": lot["FUNDO (CM)"],
                    "Lateral (cm)": lot["LATERAL (CM)"],
                    "Setup": lot["SETUP"],
                    "Comprimento Total de Fundo (m)": float(comp_take),
                    "Volume": float(take),
                    "Seq de Montagem": lot["SEQUENCIA"],
                    "Nome Peças": lot["NOME PEÇAS"],
                })

                if lot["vol_rem"] <= 1e-9:
                    i += 1

            # remove lotes finalizados
            by_seq[k] = [x for x in queue if x["vol_rem"] > 1e-9]

    # pendências: sobrou volume não programado dentro da janela
    for (ct, etapa, seq), queue in by_seq.items():
        vol_left = sum(x["vol_rem"] for x in queue)
        if vol_left > 1e-6:
            pend.append({
                "CT": ct,
                "ETAPA": etapa,
                "SEQUENCIA": seq,
                "MOTIVO": "Não coube nas datas de produção (capacidade média)",
                "VOLUME_RESTANTE_M3": float(vol_left),
            })

    mix_df = pd.DataFrame(mix_rows)

    # agrega por dia e setup
    if not mix_df.empty:
        gcols = ["Data", "Tipologia", "Tipo Armação", "Fundo (cm)", "Lateral (cm)", "Setup"]
        mix_df = (
            mix_df.groupby(gcols, dropna=False)
                  .agg({
                      "Comprimento Total de Fundo (m)": "sum",
                      "Volume": "sum",
                      "Seq de Montagem": lambda s: ";".join(sorted({str(x) for x in s.dropna().astype(str)})),
                      "Nome Peças": lambda s: ";".join(sorted({p.strip() for x in s.dropna().astype(str) for p in str(x).split(";") if p.strip()})),
                  })
                  .reset_index()
        )

    return MixOutputs(mix_diario=mix_df, pendencias=pd.DataFrame(pend))
