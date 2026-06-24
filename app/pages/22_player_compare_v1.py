from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_final_board_table,
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    APPROVED_OUTCOME_DISPLAY_FIELDS,
    OUTCOME_DISPLAY_FIELD_POSITIONS,
    OUTCOME_NOT_APPLICABLE,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    display_lane_prop_frame,
    load_expanded_draftable_player_pool,
    load_frozen_board,
    load_lane_prop_file,
)

OUTCOME_PROP_LABELS = tuple(label for _source, _target, label in APPROVED_OUTCOME_DISPLAY_FIELDS)
HORIZON_CANDIDATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_8h_emergency_20260622"
    / "outcome_horizon_candidate.csv"
)


def _position_outcome_labels(position: object) -> tuple[str, ...]:
    normalized = str(position or "").strip().upper()
    return tuple(
        label
        for _source, target, label in APPROVED_OUTCOME_DISPLAY_FIELDS
        if OUTCOME_DISPLAY_FIELD_POSITIONS[target] == normalized
    )


def _outcome_display_value(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def _render_position_aware_outcome_compare(
    compare_frame: pd.DataFrame,
    prop_frame: pd.DataFrame,
    prop_path: Path,
) -> None:
    st.subheader("Outcome Context")
    st.caption(
        "Outcome probabilities are display-only. By default each player shows only the "
        "approved heads for that player's position."
    )
    show_all = st.toggle(
        "Show all Outcome columns",
        value=False,
        key="player_compare_show_all_outcomes",
        help="Wrong-position Outcome heads show N/A in this advanced view.",
    )
    st.caption(f"Outcome source: {prop_path}")

    base_columns = [column for column in ("player", "position") if column in compare_frame.columns]
    if len(base_columns) < 2:
        st.warning("Outcome comparison needs player and position context.")
        return
    merged = pd.merge(
        compare_frame[base_columns],
        prop_frame,
        on=base_columns,
        how="left",
    )
    rows: list[dict[str, str]] = []
    visible_heads: set[str] = set()
    for row in merged.to_dict("records"):
        player = str(row.get("player", ""))
        position = str(row.get("position", ""))
        labels = OUTCOME_PROP_LABELS if show_all else _position_outcome_labels(position)
        visible_heads.update(labels)
        for label in labels:
            applicable = label in _position_outcome_labels(position)
            rows.append(
                {
                    "Player": player,
                    "Pos": position,
                    "Outcome": f"{label} (Display-Only)",
                    "Probability": (
                        _outcome_display_value(row.get(label))
                        if applicable
                        else OUTCOME_NOT_APPLICABLE
                    ),
                }
            )
    if not rows:
        st.info("No applicable Outcome heads for the selected players.")
        return
    st.caption(
        "Visible Outcome heads: "
        + ", ".join(f"{head} (Display-Only)" for head in sorted(visible_heads))
    )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_horizon_candidate_compare(compare_frame: pd.DataFrame) -> None:
    if not HORIZON_CANDIDATE_PATH.exists():
        return
    try:
        horizon = pd.read_csv(HORIZON_CANDIDATE_PATH, dtype=str).fillna(
            OUTCOME_NOT_ENOUGH_INFORMATION
        )
    except Exception:
        render_yellow_hold("Outcome horizon candidate file could not be loaded.")
        return
    required = {"player", "pos", "horizon_metric", "horizon_value_or_band"}
    if not required.issubset(horizon.columns):
        render_yellow_hold("Outcome horizon candidate file is missing required columns.")
        return
    selected_keys = {
        (
            str(row.get("player", "")).strip().casefold(),
            str(row.get("position", "")).strip().upper(),
        )
        for row in compare_frame.to_dict("records")
    }
    rows = [
        row
        for row in horizon.to_dict("records")
        if (
            str(row.get("player", "")).strip().casefold(),
            str(row.get("pos", "")).strip().upper(),
        )
        in selected_keys
    ]
    if not rows:
        return
    st.subheader("Horizon Outcome Candidate")
    st.caption(
        "Candidate / Review-Only bands for 2026, 2027, and Next 5Y. These are not "
        "approved probabilities and do not replace current Outcome display."
    )
    display = pd.DataFrame(rows)
    columns = [
        "player",
        "pos",
        "horizon_metric",
        "horizon_value_or_band",
        "horizon_confidence",
        "horizon_reason",
        "display_status",
    ]
    st.dataframe(
        display.loc[:, [column for column in columns if column in display.columns]].rename(
            columns={
                "player": "Player",
                "pos": "Pos",
                "horizon_metric": "Horizon Metric",
                "horizon_value_or_band": "Band (Candidate / Review-Only)",
                "horizon_confidence": "Confidence",
                "horizon_reason": "Reason",
                "display_status": "Status",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_decision_summary(compare_frame: pd.DataFrame) -> None:
    st.subheader("Decision Summary")
    st.caption(
        "Fast on-clock read first. This is review-only decision support; Final Board Rank "
        "and Dynasty Rank are not changed."
    )
    if compare_frame.empty:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    ranked = compare_frame.copy()
    rank_column = _first_existing(
        ranked,
        ("dynasty_asset_rank", "cross_asset_candidate_rank", "final_board_rank"),
    )
    if rank_column:
        ranked["_decision_sort"] = pd.to_numeric(ranked[rank_column], errors="coerce")
        ranked = ranked.sort_values("_decision_sort", na_position="last", kind="stable")
    leader = ranked.iloc[0].to_dict()
    runner_up = ranked.iloc[1].to_dict() if len(ranked) > 1 else {}
    cols = st.columns(4)
    cols[0].metric("Lean", str(leader.get("player") or OUTCOME_NOT_ENOUGH_INFORMATION))
    cols[1].metric(
        "Confidence",
        str(
            leader.get("dynasty_asset_confidence")
            or leader.get("confidence_band")
            or OUTCOME_NOT_ENOUGH_INFORMATION
        ),
    )
    cols[2].metric(
        "Biggest risk",
        str(
            leader.get("main_risk")
            or leader.get("candidate_key_caveat")
            or OUTCOME_NOT_ENOUGH_INFORMATION
        )[:80],
    )
    cols[3].metric(
        "Compare against",
        str(runner_up.get("player") or OUTCOME_NOT_ENOUGH_INFORMATION),
    )
    summary_rows = []
    for record in ranked.to_dict("records"):
        summary_rows.append(
            {
                "Player": record.get("player", OUTCOME_NOT_ENOUGH_INFORMATION),
                "Why draft": record.get("why_draft", OUTCOME_NOT_ENOUGH_INFORMATION),
                "Why pass / risk": record.get(
                    "main_risk",
                    record.get("candidate_key_caveat", OUTCOME_NOT_ENOUGH_INFORMATION),
                ),
                "What would change decision": _decision_change_note(record),
                "Confidence": record.get(
                    "dynasty_asset_confidence",
                    record.get("confidence_band", OUTCOME_NOT_ENOUGH_INFORMATION),
                ),
            }
        )
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


def _first_existing(frame: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    return next((column for column in candidates if column in frame.columns), "")


def _decision_change_note(record: dict[str, object]) -> str:
    caveat = str(record.get("candidate_key_caveat") or record.get("main_risk") or "").strip()
    outcome = str(record.get("outcome_applicable_summary") or "").strip()
    if caveat and caveat != OUTCOME_NOT_ENOUGH_INFORMATION:
        return f"Resolve caveat: {caveat}"
    if not outcome or outcome == OUTCOME_NOT_ENOUGH_INFORMATION:
        return "More role/outcome support would raise confidence."
    return "Decision mainly changes if roster need or tier drop changes."


bundle = load_frozen_board()
compare_pool = load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame

page_header(
    "Player Compare",
    eyebrow="Draft-Day App V1",
    description=(
        "Compare 2 to 4 players using the frozen board plus verified PDF free-agent "
        "draftable overlay. Lane prop context remains secondary to final_board_rank."
    ),
    status_items=(("Frozen board comparison", "safe"), ("Missing props show hold", "review")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

players = compare_pool["player"].astype(str).tolist() if "player" in compare_pool.columns else []
selected = st.multiselect("Players to compare", players, max_selections=4)
if len(selected) < 2:
    st.info("Select 2 to 4 players from the frozen board or PDF free-agent overlay.")
    st.stop()

compare = compare_pool.loc[compare_pool["player"].astype(str).isin(selected)].copy()
_render_decision_summary(compare)
render_final_board_table(compare, key="player_compare_board")

compare_columns = [
    "cross_asset_candidate_rank",
    "final_board_rank",
    "player",
    "position",
    "nfl_team",
    "age",
    "position_rank",
    "cross_asset_candidate_value",
    "candidate_value_band",
    "confidence_band",
    "adp",
    "available_pool_adp_range",
    "current_pick_value",
    "horizon_2026_band",
    "horizon_2027_band",
    "horizon_next5y_band",
    "candidate_vs_frozen_note",
    "candidate_action_summary",
    "candidate_key_caveat",
]
available_compare_columns = [column for column in compare_columns if column in compare.columns]
if available_compare_columns:
    st.subheader("Cross-Asset Candidate Comparison")
    st.caption(
        "Tuned V2 review-only candidate and horizon metrics where available. They do "
        "not replace Final Board Rank, Dynasty Rank, or the frozen board source of "
        "truth. ADP/range is display-only price context."
    )
    candidate_display = compare.loc[:, available_compare_columns].copy().fillna(
        OUTCOME_NOT_ENOUGH_INFORMATION
    )
    st.dataframe(
        candidate_display.rename(
            columns={
                "cross_asset_candidate_rank": "Tuned V2 Candidate Rank (Review-Only)",
                "final_board_rank": "Final Board Rank",
                "player": "Player",
                "position": "Pos",
                "nfl_team": "NFL Team",
                "age": "Age",
                "position_rank": "Position Rank",
                "cross_asset_candidate_value": "Tuned V2 Candidate Value (Review-Only)",
                "candidate_value_band": "Candidate Band",
                "confidence_band": "Confidence",
                "adp": "ADP (Display-Only)",
                "available_pool_adp_range": "Available-Pool ADP Range (Display-Only)",
                "current_pick_value": "Current Pick Value (Display-Only)",
                "horizon_2026_band": "2026 Horizon Band (Review-Only)",
                "horizon_2027_band": "2027 Horizon Band (Review-Only)",
                "horizon_next5y_band": "Next-5Y Horizon Band (Review-Only)",
                "candidate_vs_frozen_note": "Candidate vs Frozen Note",
                "candidate_action_summary": "Candidate Action Summary",
                "candidate_key_caveat": "Key Caveat / Review Flag",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Lane Prop Context")
prop_files = {
    "outcome_columns": "outcome_player_context.csv",
    "trading_lab": "trade_helper_context.csv",
    "rookie_hq": "rookie_overlay_context.csv",
    "decision_board": "decision_flags_context.csv",
}
for lane, file_name in prop_files.items():
    prop_frame, prop_path = load_lane_prop_file(lane, file_name)
    if prop_path is None:
        render_yellow_hold(f"{lane} props are missing.")
        continue
    if prop_frame.empty:
        render_yellow_hold(f"{lane} props are missing: {prop_path}.")
        continue
    if lane == "outcome_columns":
        _render_position_aware_outcome_compare(compare, prop_frame, prop_path)
        _render_horizon_candidate_compare(compare)
        continue
    st.caption(f"{lane} props: {prop_path}")
    join_columns = [
        column
        for column in ("player", "position", "final_board_rank")
        if column in prop_frame.columns
    ]
    if not join_columns:
        st.dataframe(
            display_lane_prop_frame(prop_frame).head(25),
            use_container_width=True,
            hide_index=True,
        )
        continue
    base_columns = [column for column in join_columns if column in compare.columns]
    context = pd.merge(compare[base_columns], prop_frame, on=base_columns, how="left")
    st.dataframe(display_lane_prop_frame(context), use_container_width=True, hide_index=True)
