from __future__ import annotations

from typing import Optional, Dict, Any, List

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


def show_grid(
    df: pd.DataFrame,
    key: str,
    height: int = 460,
    fit_columns: bool = True,
    pinned_bottom: Optional[Dict[str, Any]] = None,
    selectable: bool = False,
    selection_mode: str = "multiple",
    hide_columns: Optional[List[str]] = None,
):
    """Tabela com filtros no cabeçalho (estilo Excel).

    - pinned_bottom: linha TOTAL travada no rodapé
    - selectable: habilita seleção de linhas (checkbox) e retorna o response do AgGrid
    - hide_columns: oculta colunas (ex.: IDs internos)
    """
    if df is None or df.empty:
        return None

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        floatingFilter=True,
    )

    if hide_columns:
        for c in hide_columns:
            if c in df.columns:
                gb.configure_column(c, hide=True)

    update_mode = GridUpdateMode.NO_UPDATE
    if selectable:
        # precisa capturar alteração de seleção
        gb.configure_selection(selection_mode=selection_mode, use_checkbox=True)
        update_mode = GridUpdateMode.SELECTION_CHANGED

    gb.configure_grid_options(domLayout="normal")
    opts = gb.build()

    if pinned_bottom is not None:
        opts["pinnedBottomRowData"] = [pinned_bottom]

    resp = AgGrid(
        df,
        gridOptions=opts,
        update_mode=update_mode,
        data_return_mode="AS_INPUT",
        allow_unsafe_jscode=True,
        height=height,
        fit_columns_on_grid_load=fit_columns,
        custom_css={
            ".ag-row-pinned": {"font-weight": "700"},
            ".ag-row-pinned .ag-cell": {"border-top": "2px solid #CBD5E1"},
        },
        key=key,
    )
    return resp
