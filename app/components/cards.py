from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: str) -> None:
    st.metric(label, value)
