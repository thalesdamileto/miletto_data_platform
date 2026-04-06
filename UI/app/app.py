"""Streamlit home shell for the Miletto Data Platform (navigation placeholders)."""

from __future__ import annotations

from typing import Final

import streamlit as st

_TILES: Final[tuple[tuple[str, str], ...]] = (
    ("Databases", "Catalogs, connections, and data stores (coming soon)."),
    ("Data Contracts", "Contract definitions and lineage vs. `contracts/` and silver metadata."),
    ("Pipelines", "DLT jobs and Databricks assets under `databricks/`."),
    ("Monitor", "Health, runs, and SLAs (coming soon)."),
    ("Requests", "Self-service change requests (coming soon)."),
    (
        "About",
        (
            "Agent context: see `AGENTS.md` at the repository root. "
            "UI context: `UI/instructions/.cursorrules`."
        ),
    ),
)


def _render_tile(title: str, body: str, *, tile_key: str) -> None:
    st.subheader(title)
    st.caption(body)
    st.button("Open", key=tile_key, disabled=True, help="Coming in a later iteration.")


def main() -> None:
    st.set_page_config(
        page_title="Miletto Data Platform",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.title("Miletto Data Platform")
    st.markdown("Choose an area below. Detailed pages will be added in future iterations.")

    keys_top = ("tile_0", "tile_1", "tile_2")
    keys_bottom = ("tile_3", "tile_4", "tile_5")
    row1 = st.columns(3)
    for col, (title, body), key in zip(row1, _TILES[:3], keys_top, strict=True):
        with col:
            _render_tile(title, body, tile_key=key)

    row2 = st.columns(3)
    for col, (title, body), key in zip(row2, _TILES[3:], keys_bottom, strict=True):
        with col:
            _render_tile(title, body, tile_key=key)


main()
