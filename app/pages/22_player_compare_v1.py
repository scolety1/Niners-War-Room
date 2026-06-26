from __future__ import annotations

# ruff: noqa: E402
import re
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
from src.services.player_compare_decision_service import (
    build_player_compare_decision_summary,
    decision_summary_rows,
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
INJURY_PER_GAME_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "draft_day_v2"
    / "injury_per_game_risk_audit_20260623.csv"
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
        "Fast on-clock read first. Review-only decision support; frozen baseline rank, "
        "Dynasty Rank, tiers, and model values are not changed."
    )
    if compare_frame.empty:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return

    records = compare_frame.to_dict("records")
    summary = build_player_compare_decision_summary(
        records[0],
        records[1],
        records[2:],
    )
    cols = st.columns(4)
    cols[0].metric("Lean", summary.lean)
    cols[1].metric("Confidence", summary.confidence)
    cols[2].metric("Best use case", summary.best_use_case)
    cols[3].metric("Data quality", summary.data_quality)

    reason_col, flag_col = st.columns(2)
    with reason_col:
        st.markdown("**Main reasons**")
        for reason in summary.reason_bullets:
            st.markdown(f"- {reason}")
    with flag_col:
        st.markdown("**Red flags / checks**")
        for flag in summary.red_flags:
            st.markdown(f"- {flag}")

    if summary.display_only_market_note:
        st.caption(summary.display_only_market_note)

    st.dataframe(
        pd.DataFrame(decision_summary_rows(records)),
        use_container_width=True,
        hide_index=True,
    )


def _player_index(players: list[str], preferred: str = "") -> int:
    if preferred and preferred in players:
        return players.index(preferred)
    return 0


def _non_duplicate_options(players: list[str], selected: set[str]) -> list[str]:
    return [player for player in players if player not in selected]


def _render_dynasty_context(compare_frame: pd.DataFrame) -> None:
    render_final_board_table(compare_frame, key="player_compare_board")


def _render_candidate_context(compare_frame: pd.DataFrame) -> None:
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
        "candidate_vs_frozen_note",
        "candidate_action_summary",
        "candidate_key_caveat",
    ]
    available_compare_columns = [
        column for column in compare_columns if column in compare_frame.columns
    ]
    if not available_compare_columns:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.caption(
        "Tuned V2 review-only candidate metrics. They do not replace Final Board Rank, "
        "Dynasty Rank, or the frozen baseline checkpoint."
    )
    candidate_display = compare_frame.loc[:, available_compare_columns].copy().fillna(
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
                "candidate_vs_frozen_note": "Candidate vs Frozen Note",
                "candidate_action_summary": "Candidate Action Summary",
                "candidate_key_caveat": "Key Caveat / Review Flag",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_market_context(compare_frame: pd.DataFrame) -> None:
    market_columns = [
        "player",
        "position",
        "adp",
        "startup_adp_display",
        "available_pool_adp_rank",
        "available_pool_adp_range",
        "current_pick_value",
    ]
    columns = [column for column in market_columns if column in compare_frame.columns]
    if len(columns) <= 2:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.caption(
        "Market/ADP context is display-only timing sanity. It is not a model input and "
        "does not override NWR ranks."
    )
    st.dataframe(
        compare_frame.loc[:, columns].fillna(OUTCOME_NOT_ENOUGH_INFORMATION).rename(
            columns={
                "player": "Player",
                "position": "Pos",
                "adp": "ADP (Display-Only)",
                "startup_adp_display": "Startup ADP (Display-Only)",
                "available_pool_adp_rank": "Available-Pool ADP Rank (Display-Only)",
                "available_pool_adp_range": "Available-Pool ADP Range (Display-Only)",
                "current_pick_value": "Current Pick Value (Display-Only)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_age_risk_context(compare_frame: pd.DataFrame) -> None:
    risk_columns = [
        "player",
        "position",
        "age",
        "main_risk",
        "risk_notes",
        "candidate_key_caveat",
        "needs_manual_review",
        "human_review_flag",
    ]
    columns = [column for column in risk_columns if column in compare_frame.columns]
    if len(columns) <= 2:
        st.warning(OUTCOME_NOT_ENOUGH_INFORMATION)
        return
    st.caption(
        "Age/injury/risk fields are shown only where the current approved data supports them."
    )
    st.dataframe(
        compare_frame.loc[:, columns].fillna(OUTCOME_NOT_ENOUGH_INFORMATION).rename(
            columns={
                "player": "Player",
                "position": "Pos",
                "age": "Age",
                "main_risk": "Main Risk",
                "risk_notes": "Risk Notes",
                "candidate_key_caveat": "Candidate Caveat",
                "needs_manual_review": "Needs Manual Review",
                "human_review_flag": "Human Review Flag",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_injury_per_game_context(compare_frame: pd.DataFrame) -> None:
    st.subheader("Injury / Per-Game Context")
    st.caption(
        "Display-only context. Not used to change rank or model value. Missing injury "
        f"coverage shows exactly `{OUTCOME_NOT_ENOUGH_INFORMATION}` and does not mean clean health."
    )
    audit = _load_injury_per_game_audit()
    rows = [_injury_display_row(record, audit) for record in compare_frame.to_dict("records")]
    display = pd.DataFrame(rows)
    warning_players = [
        row["Player"]
        for row in rows
        if str(row.get("Annual Totals Warning", "")).startswith("YES")
    ]
    if warning_players:
        st.warning(
            "Annual totals may be misleading for: "
            + ", ".join(warning_players)
            + ". Use per-game talent and availability risk as separate questions."
        )
    st.table(display)


def _load_injury_per_game_audit() -> pd.DataFrame:
    if not INJURY_PER_GAME_AUDIT_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(INJURY_PER_GAME_AUDIT_PATH, dtype=str).fillna(
            OUTCOME_NOT_ENOUGH_INFORMATION
        )
    except Exception:
        return pd.DataFrame()


def _injury_display_row(
    record: dict[str, object],
    audit: pd.DataFrame,
) -> dict[str, str]:
    player = str(record.get("player") or OUTCOME_NOT_ENOUGH_INFORMATION)
    position = str(record.get("position") or OUTCOME_NOT_ENOUGH_INFORMATION)
    audit_row = _audit_row_for_player(player, position, audit)
    current_available = _audit_value(
        audit_row,
        "current_injury_status_available",
    ).lower()
    return {
        "Player": player,
        "Pos": position,
        "Per-Game Signal Available": _audit_value(
            audit_row,
            "per_game_signal_available",
        ),
        "Annual Total Signal Available": _audit_value(
            audit_row,
            "annual_total_signal_available",
        ),
        "Injury Data Available": (
            "Verified current injury data"
            if current_available in {"yes", "true", "verified"}
            else OUTCOME_NOT_ENOUGH_INFORMATION
        ),
        "Current Injury Status": (
            _audit_value(audit_row, "current_injury_status")
            if current_available in {"yes", "true", "verified"}
            else OUTCOME_NOT_ENOUGH_INFORMATION
        ),
        "Recovery Risk Band": _supported_band(audit_row, "recovery_risk_band"),
        "Chronic Injury Risk Band": _supported_band(audit_row, "chronic_injury_risk_band"),
        "Human Review Warning": _audit_value(audit_row, "human_review_warning"),
        "Model Treatment Summary": _audit_value(audit_row, "model_treatment_summary"),
        "Annual Totals Warning": _audit_value(
            audit_row,
            "current_display_likely_misleading",
        ),
    }


def _audit_row_for_player(
    player: str,
    position: str,
    audit: pd.DataFrame,
) -> dict[str, object]:
    if audit.empty or "player" not in audit.columns:
        return {}
    player_key = _player_key(player)
    rows = audit.loc[audit["player"].map(_player_key).eq(player_key)]
    if rows.empty and player_key == "brianthomas":
        rows = audit.loc[audit["player"].map(_player_key).isin({"brianthomas", "brianthomasjr"})]
    if rows.empty and "pos" in audit.columns:
        rows = audit.loc[
            audit["player"].map(_player_key).eq(player_key)
            & audit["pos"].astype(str).str.upper().eq(str(position).upper())
        ]
    if rows.empty:
        return {}
    return rows.iloc[0].to_dict()


def _audit_value(row: dict[str, object], column: str) -> str:
    text = str(row.get(column, "") if row else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return OUTCOME_NOT_ENOUGH_INFORMATION
    return text


def _supported_band(row: dict[str, object], column: str) -> str:
    value = _audit_value(row, column)
    return value if value != OUTCOME_NOT_ENOUGH_INFORMATION else OUTCOME_NOT_ENOUGH_INFORMATION


def _player_key(value: object) -> str:
    text = str(value or "").lower().replace("jr.", "jr")
    text = text.replace("brian thomas jr", "brian thomas")
    return re.sub(r"[^a-z0-9]+", "", text)


bundle = load_frozen_board()
compare_pool = load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame

page_header(
    "Player Compare",
    eyebrow="Draft-Day App V1",
    description=(
        "Compare 2 to 4 players using the active draftable pool, frozen baseline checkpoint, "
        "and verified PDF free-agent overlay."
    ),
    status_items=(("Frozen board comparison", "safe"), ("Missing props show hold", "review")),
)
st.markdown(
    '<a href="/live-draft-room" target="_self">Back to Live Draft</a>',
    unsafe_allow_html=True,
)
st.caption(
    "Deep tool: decision aid only. Comparison output does not mutate ranks, tiers, model "
    "values, or source-truth files."
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

players = compare_pool["player"].astype(str).tolist() if "player" in compare_pool.columns else []
query_players = [
    player
    for player in st.query_params.get_all("player")
    if player in set(players)
]
if len(players) < 2:
    st.warning("Not enough information: player pool has fewer than two players.")
else:
    selector_cols = st.columns(2)
    player_a_default = query_players[0] if query_players else ""
    player_b_default = query_players[1] if len(query_players) > 1 else ""
    player_a = selector_cols[0].selectbox(
        "Player A",
        players,
        index=_player_index(players, player_a_default),
        key="player_compare_a",
    )
    player_b_options = _non_duplicate_options(players, {player_a})
    player_b = selector_cols[1].selectbox(
        "Player B",
        player_b_options,
        index=_player_index(player_b_options, player_b_default),
        key="player_compare_b",
    )
    extra_options = _non_duplicate_options(players, {player_a, player_b})
    extra_players = st.multiselect(
        "Optional extra players",
        extra_options,
        default=[player for player in query_players[2:4] if player in extra_options],
        max_selections=2,
        help="Use this only when you want a 3- or 4-player decision check.",
    )
    selected = [player_a, player_b, *extra_players]
    compare = compare_pool.loc[compare_pool["player"].astype(str).isin(selected)].copy()
    compare["_selection_order"] = compare["player"].astype(str).map(
        {player: index for index, player in enumerate(selected)}
    )
    compare = compare.sort_values("_selection_order", kind="stable").drop(
        columns=["_selection_order"]
    )
    _render_decision_summary(compare)

    detail_tabs = st.tabs(
        [
            "Dynasty / NWR Context",
            "Market Baseline / Display-Only",
            "Injury / Per-Game Context",
            "Outcome / Horizon",
            "Age / Injury / Risk",
            "Raw Details / Diagnostics",
        ]
    )
    with detail_tabs[0]:
        _render_candidate_context(compare)
        with st.expander("Frozen board detail", expanded=False):
            _render_dynasty_context(compare)
    with detail_tabs[1]:
        _render_market_context(compare)
    with detail_tabs[2]:
        _render_injury_per_game_context(compare)
    with detail_tabs[4]:
        _render_age_risk_context(compare)

    prop_files = {
        "outcome_columns": "outcome_player_context.csv",
        "trading_lab": "trade_helper_context.csv",
        "rookie_hq": "rookie_overlay_context.csv",
        "decision_board": "decision_flags_context.csv",
    }
    with detail_tabs[3]:
        outcome_frame, outcome_path = load_lane_prop_file(
            "outcome_columns",
            "outcome_player_context.csv",
        )
        if outcome_path is None or outcome_frame.empty:
            render_yellow_hold("Outcome props are missing.")
        else:
            _render_position_aware_outcome_compare(compare, outcome_frame, outcome_path)
            _render_horizon_candidate_compare(compare)

    with detail_tabs[5]:
        st.caption("Raw context is diagnostic-only and intentionally below the decision summary.")
        for lane, file_name in prop_files.items():
            prop_frame, prop_path = load_lane_prop_file(lane, file_name)
            if prop_path is None:
                render_yellow_hold(f"{lane} props are missing.")
                continue
            if prop_frame.empty:
                render_yellow_hold(f"{lane} props are missing: {prop_path}.")
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
            st.dataframe(
                display_lane_prop_frame(context),
                use_container_width=True,
                hide_index=True,
            )
