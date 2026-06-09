from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from src.services.calibration_service import (
    build_calibration_report,
    calibration_readiness_rows,
    calibration_verdict_summary_rows,
)
from src.services.historical_draft_service import (
    compare_historical_rookie_replay,
    load_historical_rookie_model_replay,
    load_offline_rookie_notes,
    reconstruct_historical_rookie_drafts,
)
from src.services.historical_replay_contract_service import (
    build_historical_replay_contract_report,
    historical_replay_coverage_rows,
    historical_replay_issue_rows,
)
from src.services.historical_rookie_replay_service import (
    build_historical_rookie_replay_report,
)
from src.services.lve_stats_first_calibration_service import (
    build_stats_first_calibration_report,
    stats_first_calibration_readiness_rows,
)

DEFAULT_PREDRAFT_INPUTS = "sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv"
DEFAULT_OUTCOMES = "sample_data/historical_rookie_replay/post_draft_outcomes.csv"
DEFAULT_PLATFORM_DRAFTS = "sample_data/historical_yahoo_drafts/final_five_two_seasons.csv"
DEFAULT_OFFLINE_NOTES = "sample_data/historical_rookie_notes/offline_notes_four_seasons.csv"
DEFAULT_MODEL_REPLAY = "sample_data/historical_rookie_notes/model_replay_sample.csv"
DEFAULT_REPLAY_CONTRACT_ROOT = "templates/real_data_inputs/historical_replay"
DEFAULT_STATS_FIRST_PREVIEW_ROOT = "local_exports/nflverse_model_previews"


@st.cache_data
def _load_rookie_replay(
    predraft_path: str,
    outcome_path: str,
    predraft_fingerprint: tuple[str, int, int, int],
    outcome_fingerprint: tuple[str, int, int, int],
):
    _ = predraft_fingerprint, outcome_fingerprint
    return build_historical_rookie_replay_report(predraft_path, outcome_path)


@st.cache_data
def _load_legacy_replay(
    platform_path: str,
    notes_path: str,
    replay_path: str,
    platform_fingerprint: tuple[str, int, int, int],
    notes_fingerprint: tuple[str, int, int, int],
    replay_fingerprint: tuple[str, int, int, int],
):
    _ = platform_fingerprint, notes_fingerprint, replay_fingerprint
    platform_board = reconstruct_historical_rookie_drafts(platform_path)
    notes_board = load_offline_rookie_notes(notes_path)
    model_replay = load_historical_rookie_model_replay(replay_path)
    comparison = compare_historical_rookie_replay(notes_board, model_replay)
    return platform_board, notes_board, model_replay, comparison


@st.cache_data
def _load_contract(
    contract_root: str,
    contract_fingerprint: tuple[str, int, int, int],
):
    _ = contract_fingerprint
    return build_historical_replay_contract_report(contract_root)


@st.cache_data
def _load_calibration_report():
    return build_calibration_report()


@st.cache_data
def _load_stats_first_calibration(
    preview_root: str,
    preview_fingerprint: tuple[str, int, int, int],
):
    _ = preview_fingerprint
    return build_stats_first_calibration_report(preview_root)


st.title("Historical Rookie Replay")
st.info(
    "No-cheating backtester: this page ranks college prospects from pre-NFL/as-of-draft "
    "inputs only. Later NFL outcomes are shown only after ranks are assigned."
)

with st.sidebar:
    predraft_path = st.text_input("Pre-draft prospect inputs", DEFAULT_PREDRAFT_INPUTS)
    outcome_path = st.text_input("Post-draft outcome labels", DEFAULT_OUTCOMES)

try:
    report = _load_rookie_replay(
        predraft_path,
        outcome_path,
        path_fingerprint(predraft_path),
        path_fingerprint(outcome_path),
    )
except Exception as exc:
    st.error(f"Historical rookie replay failed to load: {exc}")
    st.stop()

if report.issues:
    st.error("Historical rookie replay has data issues.")
    st.dataframe(pd.DataFrame({"issue": report.issues}), use_container_width=True)
    st.stop()

if not report.years:
    st.warning("No historical rookie replay years are loaded.")
    st.stop()

selected_year = st.selectbox(
    "Draft year",
    report.years,
    index=len(report.years) - 1,
    help="Ranks are rebuilt from the pre-draft input file for this year only.",
)
selected_positions = st.multiselect(
    "Position filter",
    report.positions,
    default=report.positions,
    help="Filters visible prospect rows. Overall hit-rate metrics still use the full year.",
)

year_rows = [
    row
    for row in report.top20_rows
    if row["draft_year"] == selected_year and row["position"] in selected_positions
]
year_features = [
    row
    for row in report.feature_rows
    if row["draft_year"] == selected_year and row["position"] in selected_positions
]
year_outcomes = [
    row
    for row in report.outcome_rows
    if row["draft_year"] == selected_year and row["position"] in selected_positions
]
year_hit_rates = [
    row
    for row in report.hit_rate_rows
    if row["draft_year"] == selected_year and row["scope"] == "overall"
]
year_position_hit_rates = [
    row for row in report.position_hit_rate_rows if row["draft_year"] == selected_year
]
year_wins = [
    row
    for row in report.model_win_rows
    if row["draft_year"] == selected_year and row["position"] in selected_positions
]
year_misses = [
    row
    for row in report.model_miss_rows
    if row["draft_year"] == selected_year and row["position"] in selected_positions
]


def _rate_text(hit_rates: list[dict[str, object]], rank_window: str) -> str:
    row = next((item for item in hit_rates if item["rank_window"] == rank_window), None)
    if not row or row["hit_rate"] is None:
        return "n/a"
    return f"{float(row['hit_rate']) * 100:.0f}%"


left, middle, right, fourth = st.columns(4)
left.metric("Top-5 Hit Rate", _rate_text(year_hit_rates, "top_5"))
middle.metric("Top-10 Hit Rate", _rate_text(year_hit_rates, "top_10"))
right.metric("Top-20 Hit Rate", _rate_text(year_hit_rates, "top_20"))
fourth.metric("Future Stats Used", "No")

st.success(
    "Ranking metadata: future NFL production fields are excluded from the model score. "
    "Outcome labels are review-only."
)

top20_tab, hit_rate_tab, wins_tab, features_tab, outcomes_tab, metadata_tab, legacy_tab = st.tabs(
    [
        "Top 20 Prospects",
        "Hit Rates",
        "Wins / Misses",
        "Pre-Draft Feature Inputs",
        "Outcome Labels",
        "No-Cheat Metadata",
        "Legacy Reference",
    ]
)

with top20_tab:
    st.subheader(f"{selected_year} Top 20 Model Prospects")
    st.caption(
        "Sorted by pre-NFL model score, then confidence. NFL outcome columns are joined "
        "after ranking and are not inputs."
    )
    if year_rows:
        st.dataframe(
            pd.DataFrame(year_rows)[
                [
                    "model_rank",
                    "player_name",
                    "position",
                    "school",
                    "pre_nfl_model_score",
                    "confidence_score",
                    "as_of_date",
                    "future_nfl_stats_used",
                    "outcome_label",
                    "outcome_category",
                    "outcome_is_hit",
                    "best_lve_ppg_after_draft",
                    "top24_seasons_after_draft",
                    "source_notes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "model_rank": st.column_config.NumberColumn("Rank"),
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "pre_nfl_model_score": st.column_config.NumberColumn(
                    "Pre-NFL Model",
                    format="%.2f",
                ),
                "confidence_score": st.column_config.NumberColumn(
                    "Confidence",
                    format="%.1f",
                ),
                "future_nfl_stats_used": st.column_config.CheckboxColumn(
                    "Future Stats Used"
                ),
                "outcome_is_hit": st.column_config.CheckboxColumn("Hit"),
                "best_lve_ppg_after_draft": st.column_config.NumberColumn(
                    "Best Later LVE PPG",
                    format="%.1f",
                ),
            },
        )
    else:
        st.warning(f"No top-20 rows found for {selected_year}.")

with hit_rate_tab:
    st.subheader(f"{selected_year} Prospect Hit Rates")
    st.caption(
        "Hit rates are calculated after ranking from the separate outcome file. "
        "Positive outcomes are hit, starter, and fantasy_difference_maker."
    )
    if year_hit_rates:
        st.dataframe(
            pd.DataFrame(year_hit_rates),
            use_container_width=True,
            hide_index=True,
            column_config={
                "hit_rate": st.column_config.NumberColumn("Hit Rate", format="%.3f"),
                "ranking_input": st.column_config.CheckboxColumn("Ranking Input"),
            },
        )
    st.subheader("Position Breakout")
    if year_position_hit_rates:
        position_rate_frame = pd.DataFrame(year_position_hit_rates)
        st.dataframe(
            position_rate_frame[
                [
                    "position",
                    "rank_window",
                    "ranked_count",
                    "labeled_count",
                    "hit_count",
                    "hit_rate",
                    "fantasy_difference_maker_count",
                    "starter_count",
                    "hit_only_count",
                    "miss_count",
                    "bust_count",
                    "ranking_input",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "hit_rate": st.column_config.NumberColumn("Hit Rate", format="%.3f"),
                "ranking_input": st.column_config.CheckboxColumn("Ranking Input"),
            },
        )

with wins_tab:
    st.subheader(f"{selected_year} Biggest Model Wins")
    st.caption("Model wins are high-ranked prospects whose later outcomes supported the rank.")
    if year_wins:
        st.dataframe(
            pd.DataFrame(year_wins),
            use_container_width=True,
            hide_index=True,
            column_config={
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "ranking_input": st.column_config.CheckboxColumn("Ranking Input"),
            },
        )
    else:
        st.info("No model wins found for this filter.")

    st.subheader(f"{selected_year} Biggest Model Misses")
    st.caption(
        "Misses include highly ranked misses/busts and later-ranked players who became "
        "starters or difference-makers."
    )
    if year_misses:
        st.dataframe(
            pd.DataFrame(year_misses),
            use_container_width=True,
            hide_index=True,
            column_config={
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "ranking_input": st.column_config.CheckboxColumn("Ranking Input"),
            },
        )
    else:
        st.info("No model misses found for this filter.")

with features_tab:
    st.subheader("Pre-Draft Feature Receipts")
    st.caption(
        "These are the only feature rows that feed the replay ranking. Outcome fields "
        "do not appear here."
    )
    if year_features:
        player_options = ["All"] + sorted({str(row["player_name"]) for row in year_features})
        selected_player = st.selectbox("Player", player_options)
        feature_frame = pd.DataFrame(year_features)
        if selected_player != "All":
            feature_frame = feature_frame[feature_frame["player_name"] == selected_player]
        st.dataframe(
            feature_frame[
                [
                    "model_rank",
                    "player_name",
                    "position",
                    "feature_name",
                    "normalized_score",
                    "feature_weight",
                    "model_score_contribution",
                    "source",
                    "as_of_date",
                    "future_nfl_stats_used",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "model_rank": st.column_config.NumberColumn("Rank"),
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "normalized_score": st.column_config.NumberColumn("Score", format="%.1f"),
                "feature_weight": st.column_config.NumberColumn("Weight", format="%.1f"),
                "model_score_contribution": st.column_config.NumberColumn(
                    "Contribution",
                    format="%.3f",
                ),
                "future_nfl_stats_used": st.column_config.CheckboxColumn(
                    "Future Stats Used"
                ),
            },
        )

with outcomes_tab:
    st.subheader("Post-Draft Outcome Labels")
    st.warning(
        "Outcome labels are for hit-rate review after the ranks are produced. They are "
        "not ranking inputs and cannot change the top-20 order."
    )
    if year_outcomes:
        st.dataframe(
            pd.DataFrame(year_outcomes),
            use_container_width=True,
            hide_index=True,
            column_config={
                "model_rank": st.column_config.NumberColumn("Rank"),
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "ranking_input": st.column_config.CheckboxColumn("Ranking Input"),
            },
        )

with metadata_tab:
    st.subheader("No-Cheat Replay Metadata")
    st.dataframe(
        pd.DataFrame(report.metadata_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Year Coverage")
    st.dataframe(
        pd.DataFrame(report.summary_rows),
        use_container_width=True,
        hide_index=True,
    )

with legacy_tab:
    st.subheader("Legacy Reference Tools")
    st.caption(
        "The older draft-note comparison and veteran calibration checks have been moved "
        "out of the main flow. They remain here as read-only references."
    )
    legacy_comparison = None
    with st.expander("Legacy Draft Notes And Replay Comparison"):
        platform_path = st.text_input("Platform final-pick export", DEFAULT_PLATFORM_DRAFTS)
        notes_path = st.text_input("Offline rookie notes", DEFAULT_OFFLINE_NOTES)
        replay_path = st.text_input("Legacy model replay rows", DEFAULT_MODEL_REPLAY)
        try:
            platform_board, notes_board, model_replay, comparison = _load_legacy_replay(
                platform_path,
                notes_path,
                replay_path,
                path_fingerprint(platform_path),
                path_fingerprint(notes_path),
                path_fingerprint(replay_path),
            )
        except Exception as exc:
            st.error(f"Legacy replay failed to load: {exc}")
        else:
            legacy_actual_tab, legacy_replay_tab, legacy_compare_tab = st.tabs(
                ["Actual Drafts", "Model Replay", "Comparison"]
            )
            with legacy_actual_tab:
                actual_frame = pd.DataFrame([entry.__dict__ for entry in notes_board.entries])
                st.dataframe(actual_frame, use_container_width=True, hide_index=True)
                with st.expander("Platform Final-Pick Reconstruction"):
                    platform_frame = pd.DataFrame(
                        [entry.__dict__ for entry in platform_board.entries]
                    )
                    st.caption(platform_board.review_warning)
                    st.dataframe(platform_frame, use_container_width=True, hide_index=True)
            with legacy_replay_tab:
                replay_frame = pd.DataFrame([row.__dict__ for row in model_replay])
                st.dataframe(replay_frame, use_container_width=True, hide_index=True)
            with legacy_compare_tab:
                comparison_frame = pd.DataFrame([row.__dict__ for row in comparison.rows])
                st.caption(comparison.review_warning)
                st.dataframe(comparison_frame, use_container_width=True, hide_index=True)
            legacy_comparison = comparison

    with st.expander("Legacy Decision-Safety Calibration"):
        if legacy_comparison is None:
            st.warning("Load the legacy draft comparison before viewing this calibration.")
        else:
            calibration = _load_calibration_report()
            readiness_rows = calibration_readiness_rows(calibration, legacy_comparison)
            st.dataframe(
                pd.DataFrame(readiness_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.dataframe(
                pd.DataFrame(calibration_verdict_summary_rows(legacy_comparison)),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Legacy Stats-First Veteran Calibration"):
        stats_first_preview_root = st.text_input(
            "Stats-first preview root",
            DEFAULT_STATS_FIRST_PREVIEW_ROOT,
        )
        stats_first = _load_stats_first_calibration(
            stats_first_preview_root,
            path_fingerprint(stats_first_preview_root),
        )
        st.dataframe(
            pd.DataFrame(stats_first_calibration_readiness_rows(stats_first)),
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(
            pd.DataFrame(stats_first.summary_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Legacy Replay File Contract"):
        contract_root = st.text_input("Replay contract root", DEFAULT_REPLAY_CONTRACT_ROOT)
        contract = _load_contract(contract_root, path_fingerprint(contract_root))
        left_schema, right_schema, third_schema = st.columns(3)
        left_schema.metric("Contract", contract.status.upper())
        right_schema.metric("Errors", contract.error_count)
        third_schema.metric("Warnings", contract.warning_count)
        st.dataframe(
            pd.DataFrame(historical_replay_coverage_rows(contract)),
            use_container_width=True,
            hide_index=True,
        )
        issue_rows = historical_replay_issue_rows(contract)
        if issue_rows:
            st.subheader("Contract Issues")
            st.dataframe(pd.DataFrame(issue_rows), use_container_width=True, hide_index=True)
