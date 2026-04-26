from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.services.command_board_service import build_import_review_board


@st.cache_data
def _load_board(active_data_pack: str):
    return build_import_review_board(active_data_pack)


settings = get_settings()
board = _load_board(str(settings.active_data_pack))

st.title("Import Review")
st.caption(f"`{settings.active_data_pack}`")

left, middle, right = st.columns(3)
left.metric("Errors", board.issue_counts.get("error", 0))
middle.metric("Warnings", board.issue_counts.get("warning", 0))
right.metric("Snapshot", board.snapshot_date or "unknown")

if board.has_errors:
    st.error("Open import errors need review before trusting model boards.")
else:
    st.success("No blocking import errors found.")

st.subheader("Validation")
issue_frame = pd.DataFrame(board.issue_rows)
if issue_frame.empty:
    st.dataframe(pd.DataFrame(columns=["severity", "file", "row", "entity", "issue", "fix"]))
else:
    severity_filter = st.multiselect(
        "Severity",
        sorted(issue_frame["severity"].dropna().unique()),
        default=sorted(issue_frame["severity"].dropna().unique()),
    )
    filtered_issues = issue_frame[issue_frame["severity"].isin(severity_filter)]
    st.dataframe(filtered_issues, use_container_width=True, hide_index=True)

st.subheader("Loaded Rows")
st.dataframe(pd.DataFrame(board.row_counts), use_container_width=True, hide_index=True)

with st.expander("Source Review"):
    source_frame = pd.DataFrame(board.source_rows)
    st.dataframe(source_frame, use_container_width=True, hide_index=True)
