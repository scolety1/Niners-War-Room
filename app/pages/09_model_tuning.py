from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.ui_framework import page_header
from src.services.model_v4_historical_rookie_tuning_service import (
    HISTORICAL_BACKTEST_MATRIX,
    HISTORICAL_OUTCOMES,
    build_historical_rookie_tuning_report,
)


@st.cache_data
def _load_historical_tuning(
    matrix_path: str,
    outcome_path: str,
    matrix_fingerprint: tuple[str, int, int, int],
    outcome_fingerprint: tuple[str, int, int, int],
):
    _ = matrix_fingerprint, outcome_fingerprint
    return build_historical_rookie_tuning_report(matrix_path, outcome_path)


def _safe_display(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[[column for column in columns if column in frame.columns]]


page_header(
    "Model Tuning",
    eyebrow="Review-only lab",
    description=(
        "Evaluate model behavior without changing formulas, active rankings, My Team, "
        "War Board, or recommendations."
    ),
    status_items=(("Review Only", "review"), ("No Promotion", "safe")),
)

subtabs = st.tabs(["Historical Rookie Replay"])

with subtabs[0]:
    st.subheader("Historical Rookie Replay")
    st.caption(
        "Same table shape as the Draft Room prospect board, replayed across historical "
        "classes. Outcomes are display-only and never feed the score."
    )
    matrix_path = str(HISTORICAL_BACKTEST_MATRIX)
    outcome_path = str(HISTORICAL_OUTCOMES)
    try:
        report = _load_historical_tuning(
            matrix_path,
            outcome_path,
            path_fingerprint(matrix_path),
            path_fingerprint(outcome_path),
        )
    except Exception as exc:
        st.error(f"Historical rookie tuning replay failed to load: {exc}")
        st.stop()

    board = pd.DataFrame(report.board_rows)
    summary = pd.DataFrame(report.summary_rows)
    components = pd.DataFrame(report.component_rows)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Replay Years", f"{min(report.years)}-{max(report.years)}")
    metric_cols[1].metric("Historical Rows", len(board))
    metric_cols[2].metric(
        "Outcome Labels Loaded",
        int(board["Outcome Loaded"].sum()) if not board.empty else 0,
    )
    metric_cols[3].metric("Future Stats Used", "No")

    st.dataframe(summary, use_container_width=True, hide_index=True)

    filter_cols = st.columns([1.0, 1.0, 1.0, 1.0])
    with filter_cols[0]:
        selected_positions = st.multiselect(
            "Position",
            sorted(board["Pos"].dropna().unique().tolist()) if not board.empty else [],
            default=sorted(board["Pos"].dropna().unique().tolist()) if not board.empty else [],
        )
    with filter_cols[1]:
        trust_options = (
            sorted(board["Trust Level"].dropna().unique().tolist()) if not board.empty else []
        )
        selected_trust = st.multiselect(
            "Trust Level",
            trust_options,
            default=trust_options,
        )
    with filter_cols[2]:
        round_options = (
            sorted(board["Draft Round"].dropna().astype(str).unique().tolist())
            if not board.empty
            else []
        )
        selected_rounds = st.multiselect(
            "Draft Round",
            round_options,
            default=round_options,
        )
    with filter_cols[3]:
        show_only_outcomes = st.checkbox("Only rows with outcomes", value=False)

    visible = board.copy()
    if selected_positions and not visible.empty:
        visible = visible[visible["Pos"].isin(selected_positions)]
    if selected_trust and not visible.empty:
        visible = visible[visible["Trust Level"].isin(selected_trust)]
    if selected_rounds and not visible.empty:
        visible = visible[visible["Draft Round"].astype(str).isin(selected_rounds)]
    if show_only_outcomes and not visible.empty:
        visible = visible[visible["Outcome Loaded"]]

    display_columns = [
        "Rank",
        "Player",
        "Pos",
        "NFL Team",
        "College",
        "Final Score",
        "Production Score",
        "College Team Share",
        "NFL Draft Pick Signal",
        "Athletic Score",
        "Age Score",
        "Confidence Cap",
        "Evidence Available",
        "Trust Level",
        "Draft Round",
        "Overall Pick",
        "Model Edge / Source Warning",
        "Fantasy-Relevant Replay Pool",
        "Outcome Loaded",
        "Outcome Maturity",
        "Outcome Category",
        "Broad Outcome Hit?",
        "Strict Starter Hit?",
        "Difference Maker?",
        "Best LVE PPG",
        "Starter-Level Seasons",
        "Why This Rank",
    ]

    year_tabs = st.tabs([str(year) for year in report.years])
    for tab, year in zip(year_tabs, report.years, strict=False):
        with tab:
            st.caption(
                f"{year} replay. Scores use pre-draft evidence only; outcome columns are "
                "joined afterward for review."
            )
            year_frame = visible[visible["Draft Year"] == year]
            st.dataframe(
                _safe_display(year_frame, display_columns),
                use_container_width=True,
                hide_index=True,
            )

    st.divider()
    st.subheader("Player Component Drilldown")
    player_options = visible["Player"].tolist() if not visible.empty else []
    if player_options:
        selected_player = st.selectbox("Player", player_options)
        player_components = components[components["player"] == selected_player]
        st.dataframe(player_components, use_container_width=True, hide_index=True)
    else:
        st.info("No rows match the current filters.")
