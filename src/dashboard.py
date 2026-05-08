"""Streamlit dashboard for the Pokemon GO PvP ETL."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import REGION_LABELS
from src.database import connect_db, get_metadata
from src.etl import run_etl
from src.transform import build_transfer_string


def render_dashboard(df: pd.DataFrame) -> None:
    st.title("Pokemon GO PvP ETL")
    st.caption("Rankings PvPoke + dimensao gamemaster + SQLite")

    search_col, count_col = st.columns([2, 1])
    with search_col:
        name_query = st.text_input("Buscar por nome").strip().lower()
    with count_col:
        selected_counts = st.multiselect(
            "Quantidade de Listas",
            options=[0, 1, 2, 3],
            default=[0, 1, 2, 3],
        )

    view_df = df.copy()
    if name_query:
        view_df = view_df[view_df["nome"].str.lower().str.contains(name_query, na=False)]
    view_df = view_df[view_df["quantidade_listas"].isin(selected_counts)]

    display_df = view_df.rename(
        columns={
            "pokedex_id": "Pokedex ID",
            "nome": "Nome",
            "forma_regional": "Forma Regional",
            "quantidade_listas": "Quantidade de Listas",
        }
    )
    display_df["Forma Regional"] = display_df["Forma Regional"].map(REGION_LABELS)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.subheader("Lixeira Segura")
    st.code(build_transfer_string(df), language="text")


def main() -> None:
    st.set_page_config(page_title="Pokemon GO PvP ETL", layout="wide")

    refresh = st.sidebar.button("Atualizar ETL agora")
    with st.spinner("Executando ETL com PvPoke, pandas e SQLite..."):
        data = run_etl(force_refresh=refresh)

    conn = connect_db()
    last_refresh = get_metadata(conn, "last_refresh_utc")
    if last_refresh:
        st.sidebar.caption(f"Ultima atualizacao UTC: {last_refresh}")

    render_dashboard(data)
