from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_lane_status_table,
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    display_lane_prop_frame,
    load_frozen_board,
    load_lane_prop_file,
)
from src.services.draft_day_runtime_state_service import load_runtime_state, record_trade_event
from src.services.draft_day_trade_lab_service import (
    NOT_ENOUGH_INFORMATION,
    add_trade_item,
    build_trade_item_lookup,
    clear_trade_state,
    copy_trade_state,
    display_package_summary,
    display_trade_item_rows,
    empty_trade_state,
    package_summary_rows,
    pick_context_options,
    player_options,
    remove_trade_item,
    review_trade_package,
    source_context_counts,
    trade_item_rows,
)

SESSION_KEY = "draft_day_v1_trading_lab_builder"
RUNTIME_STATE_KEY = "draft_day_v2_trade_lab_runtime_state"

bundle = load_frozen_board()
trade_frame, trade_path = load_lane_prop_file("trading_lab", "trade_helper_context.csv")
pick_frame, pick_path = load_lane_prop_file("trading_lab", "pick_context.csv")
tier_frame, tier_path = load_lane_prop_file("trading_lab", "trade_tier_values.csv")

page_header(
    "Trading Lab",
    eyebrow="Draft-Day App V1",
    description=(
        "Manual give/get package workspace using frozen-board rank, tier, and visible score "
        "context. No trade calculator, simulation, private value, or final trade advice runs here."
    ),
    status_items=(
        ("Manual review only", "review"),
        ("Frozen board source", "safe"),
        ("No trade model added", "safe"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

if SESSION_KEY not in st.session_state:
    st.session_state[SESSION_KEY] = empty_trade_state()
st.session_state[SESSION_KEY] = copy_trade_state(st.session_state[SESSION_KEY])
if RUNTIME_STATE_KEY not in st.session_state:
    st.session_state[RUNTIME_STATE_KEY] = load_runtime_state(mode="live")

lookup = build_trade_item_lookup(bundle.frame, trade_frame, pick_frame)
player_select = player_options(lookup)
pick_select = pick_context_options(lookup)
counts = source_context_counts(bundle.frame, trade_frame, pick_frame, tier_frame)

if trade_path is None or trade_frame.empty:
    render_yellow_hold("Trading Lab helper context is missing; review is board-context only.")


def _render_source_metrics(counts: dict[str, int]) -> None:
    cols = st.columns(4)
    cols[0].metric("Frozen board rows", counts["frozen_board_rows"])
    cols[1].metric("Trade helper rows", counts["trade_helper_rows"])
    cols[2].metric("Pick context rows", counts["pick_context_rows"])
    cols[3].metric("Tier context rows", counts["tier_context_rows"])
    st.caption(
        "Trade helper, pick, tier, and any market-like fields are display-only context. "
        "They cannot override `final_board_rank` or create hidden trade value."
    )


def _render_builder(player_select: dict[str, str], pick_select: dict[str, str]) -> None:
    st.subheader("Trade Builder")
    st.caption(
        "Build both sides manually. Status bands are conservative review labels, not final trade "
        "advice."
    )
    give_col, get_col = st.columns(2)
    _render_side_controls("NWR gives", "give", give_col, player_select, pick_select)
    _render_side_controls("NWR gets", "get", get_col, player_select, pick_select)
    clear_col, _spacer = st.columns([1, 3])
    if clear_col.button("Clear Trade", key="trading_lab_clear_trade", use_container_width=True):
        st.session_state[SESSION_KEY] = clear_trade_state()
        st.rerun()


def _render_side_controls(
    title: str,
    side: str,
    container,
    player_select: dict[str, str],
    pick_select: dict[str, str],
) -> None:
    with container:
        st.markdown(f"**{title}**")
        if player_select:
            player_label = st.selectbox(
                "Add player",
                list(player_select),
                key=f"trading_lab_{side}_player",
            )
            if st.button(
                "Add Player",
                key=f"trading_lab_{side}_add_player",
                use_container_width=True,
            ):
                st.session_state[SESSION_KEY] = add_trade_item(
                    st.session_state[SESSION_KEY],
                    side,  # type: ignore[arg-type]
                    player_select[player_label],
                )
                st.rerun()
        else:
            st.warning(NOT_ENOUGH_INFORMATION)

        if pick_select:
            pick_label = st.selectbox(
                "Add pick/context",
                list(pick_select),
                key=f"trading_lab_{side}_pick",
            )
            if st.button(
                "Add Pick Context",
                key=f"trading_lab_{side}_add_pick",
                use_container_width=True,
            ):
                st.session_state[SESSION_KEY] = add_trade_item(
                    st.session_state[SESSION_KEY],
                    side,  # type: ignore[arg-type]
                    pick_select[pick_label],
                )
                st.rerun()
        else:
            st.caption(f"Pick/context add: {NOT_ENOUGH_INFORMATION}")

        side_keys = st.session_state[SESSION_KEY][side]
        remove_options = _remove_options(side_keys, lookup)
        if remove_options:
            remove_label = st.selectbox(
                "Remove item",
                list(remove_options),
                key=f"trading_lab_{side}_remove_select",
            )
            if st.button(
                "Remove Item",
                key=f"trading_lab_{side}_remove",
                use_container_width=True,
            ):
                st.session_state[SESSION_KEY] = remove_trade_item(
                    st.session_state[SESSION_KEY],
                    side,  # type: ignore[arg-type]
                    remove_options[remove_label],
                )
                st.rerun()
        else:
            st.caption("No items on this side yet.")


def _render_summary(lookup: dict[str, dict[str, object]]) -> None:
    st.subheader("Package Summary")
    review = review_trade_package(st.session_state[SESSION_KEY], lookup)
    cols = st.columns(4)
    cols[0].metric("Review status", review.status)
    cols[1].metric("Visible score gap", review.score_gap_display)
    cols[2].metric("Rank context", review.rank_context)
    cols[3].metric("Human review", "Required")
    st.info(review.explanation)
    st.dataframe(
        display_package_summary(package_summary_rows(st.session_state[SESSION_KEY], lookup)),
        use_container_width=True,
        hide_index=True,
        key="trading_lab_package_summary",
    )


def _render_selected_items(lookup: dict[str, dict[str, object]]) -> None:
    st.subheader("Selected Package Items")
    rows = trade_item_rows(st.session_state[SESSION_KEY], lookup)
    if rows.empty:
        st.warning(NOT_ENOUGH_INFORMATION)
        return
    st.dataframe(
        display_trade_item_rows(rows),
        use_container_width=True,
        hide_index=True,
        key="trading_lab_selected_items",
    )


def _render_diagnostics() -> None:
    with st.expander("Source diagnostics", expanded=False):
        render_lane_status_table()
        if trade_path and not trade_frame.empty:
            st.caption(f"Display-only trade helper context: {trade_path}")
            st.dataframe(
                display_lane_prop_frame(trade_frame.head(20)),
                use_container_width=True,
                hide_index=True,
            )
        if pick_path and not pick_frame.empty:
            st.caption(f"Display-only pick context: {pick_path}")
            st.dataframe(
                display_lane_prop_frame(pick_frame.head(20)),
                use_container_width=True,
                hide_index=True,
            )
        if tier_path and not tier_frame.empty:
            st.caption(f"Display-only tier context: {tier_path}")
            st.dataframe(
                display_lane_prop_frame(tier_frame),
                use_container_width=True,
                hide_index=True,
            )


def _render_trade_finder() -> None:
    st.subheader("Trade Finder")
    st.caption(
        "Use when the current pick feels bad: find conservative trade-back structures from "
        "existing pick context. Decision support only; no trade calculator."
    )
    if pick_frame.empty:
        st.warning(NOT_ENOUGH_INFORMATION)
        return
    pick_labels = pick_frame.get("pick_label", pick_frame.index.to_series()).astype(str).tolist()
    current_pick = st.selectbox("Current pick to shop", pick_labels, key="trade_finder_pick")
    later_picks = [label for label in pick_labels if label != current_pick]
    target_pick = st.selectbox(
        "Candidate later pick received",
        later_picks or pick_labels,
        key="trade_finder_later_pick",
    )
    future_pick = st.text_input(
        "Future pick / extra context",
        value="2028 1st",
        key="trade_finder_future_pick",
    )
    counterparty = st.text_input(
        "Counterparty",
        value="Trade partner",
        key="trade_finder_counterparty",
    )
    st.info(
        f"Conservative structure: NWR sends {current_pick}; NWR receives "
        f"{future_pick} + {target_pick}. Human judgment required."
    )
    if st.button("Record Accepted Trade-Back Event", key="trade_finder_accept"):
        st.session_state[RUNTIME_STATE_KEY] = record_trade_event(
            st.session_state[RUNTIME_STATE_KEY],
            trade_type="Trade Finder accepted trade-back",
            counterparty=counterparty,
            sends=current_pick,
            receives=f"{future_pick} + {target_pick}",
            notes="Recorded from Trade Finder V2 decision-support tab.",
        )
        st.success("Accepted trade-back event recorded in local draft runtime log.")


def _render_trade_for() -> None:
    st.subheader("Trade For")
    st.caption(
        "Use when a player is falling: estimate a conservative pick-acquisition structure "
        "from available pick context. No trade calculator or final advice."
    )
    if not player_select:
        st.warning(NOT_ENOUGH_INFORMATION)
        return
    player_label = st.selectbox("Falling player", list(player_select), key="trade_for_player")
    pick_labels = pick_frame.get("pick_label", pick_frame.index.to_series()).astype(str).tolist()
    target_pick = st.selectbox("Pick to acquire", pick_labels, key="trade_for_pick")
    offer = st.text_input(
        "Possible offer",
        value="Future pick or later current pick",
        key="trade_for_offer",
    )
    counterparty = st.text_input(
        "Pick owner / counterparty",
        value="Pick owner",
        key="trade_for_counterparty",
    )
    st.info(
        f"Review structure: acquire {target_pick} for {player_label}; possible send: {offer}. "
        "Compare manually against roster need and tiers."
    )
    if st.button("Record Accepted Trade-For Event", key="trade_for_accept"):
        st.session_state[RUNTIME_STATE_KEY] = record_trade_event(
            st.session_state[RUNTIME_STATE_KEY],
            trade_type="Trade For accepted pick acquisition",
            counterparty=counterparty,
            sends=offer,
            receives=target_pick,
            notes=f"Target player context: {player_label}",
        )
        st.success("Accepted trade-for event recorded in local draft runtime log.")


def _remove_options(
    side_keys: list[str],
    lookup: dict[str, dict[str, object]],
) -> dict[str, str]:
    options: dict[str, str] = {}
    for key in side_keys:
        label = str(lookup.get(key, {}).get("label", key))
        options[label] = key
    return options


_render_source_metrics(counts)
builder_tab, finder_tab, trade_for_tab = st.tabs(
    ["Package Builder", "Trade Finder", "Trade For"]
)
with builder_tab:
    _render_builder(player_select, pick_select)
    _render_summary(lookup)
    _render_selected_items(lookup)
with finder_tab:
    _render_trade_finder()
with trade_for_tab:
    _render_trade_for()
_render_diagnostics()
