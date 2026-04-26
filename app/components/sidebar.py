from __future__ import annotations

import streamlit as st


def active_pack_sidebar(active_data_pack: str) -> None:
    st.sidebar.write(f"Active data pack: `{active_data_pack}`")
