from __future__ import annotations

import streamlit as st

from app.components.demo_source_labels import demo_source_label


def active_pack_sidebar(active_data_pack: str) -> None:
    st.sidebar.write(demo_source_label(active_data_pack))
