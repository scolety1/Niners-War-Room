from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
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
from src.services.draft_day_trade_lab_service import (
    NOT_ENOUGH_INFORMATION,
    add_trade_item,
    build_trade_item_lookup,
    clear_trade_state,
    copy_trade_state,
    display_market_package_rows,
    display_market_totals,
    display_package_summary,
    display_trade_item_rows,
    empty_trade_state,
    package_summary_rows,
    pick_context_options,
    player_options,
    remove_trade_item,
    review_trade_package,
    source_context_counts,
    summarize_trade_package_market,
    trade_item_rows,
)

SESSION_KEY = "draft_day_v1_trading_lab_builder"
MANUAL_PLANNER_WARNING = (
    "Manual planning only. Not a trade calculator. Not model input. Not market valuation."
)

bundle = load_frozen_board()
trade_frame, trade_path = load_lane_prop_file("trading_lab", "trade_helper_context.csv")
pick_frame, pick_path = load_lane_prop_file("trading_lab", "pick_context.csv")
tier_frame, tier_path = load_lane_prop_file("trading_lab", "trade_tier_values.csv")
mock_pick_frame, mock_pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")

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
st.caption(
    "Deep tool: manual trade review. Market context is display-only and not a trade model, "
    "rank input, or source of truth."
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

if SESSION_KEY not in st.session_state:
    st.session_state[SESSION_KEY] = empty_trade_state()
st.session_state[SESSION_KEY] = copy_trade_state(st.session_state[SESSION_KEY])

lookup = build_trade_item_lookup(bundle.frame, trade_frame, pick_frame)
player_select = player_options(lookup)
pick_select = pick_context_options(lookup)
counts = source_context_counts(bundle.frame, trade_frame, pick_frame, tier_frame)

if trade_path is None or trade_frame.empty:
    render_yellow_hold("Trading Lab helper context is missing; review is board-context only.")


def _render_source_metrics(counts: dict[str, int]) -> None:
    cols = st.columns(4)
    cols[0].metric("Frozen baseline rows", counts["frozen_board_rows"])
    cols[1].metric("Trade helper rows", counts["trade_helper_rows"])
    cols[2].metric("Draft pick rows", int(mock_pick_frame.shape[0]))
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


def _render_market_sanity_panel(lookup: dict[str, dict[str, object]]) -> None:
    with st.expander("Market Baseline / Display-Only sanity check", expanded=True):
        st.caption(
            "DynastyProcess market baseline is sanity context only. It is not NWR source "
            "truth, not a trade calculator, and not used for NWR rank/model logic."
        )
        text_cols = st.columns(2)
        give_text = text_cols[0].text_area(
            "Give market assets",
            value="",
            placeholder="Example: 2026 1.04",
            key="trading_lab_market_give_assets",
        )
        get_text = text_cols[1].text_area(
            "Get market assets",
            value="",
            placeholder="Example: 2026 2.03, 2028 1st",
            key="trading_lab_market_get_assets",
        )
        market_summary = summarize_trade_package_market(
            st.session_state[SESSION_KEY],
            lookup,
            give_assets_text=give_text,
            get_assets_text=get_text,
        )
        fresh = market_summary.freshness
        fresh_cols = st.columns(4)
        fresh_cols[0].metric("Market sanity", market_summary.status)
        fresh_cols[1].metric("Difference", market_summary.difference_display)
        fresh_cols[2].metric("Freshness", fresh.get("freshness_status", "Not enough information"))
        fresh_cols[3].metric(
            "Scrape date",
            fresh.get("upstream_scrape_date", "Not enough information"),
        )
        st.caption(market_summary.display_only_warning)
        stale_warning = fresh.get("market_baseline_stale_warning")
        if stale_warning:
            st.warning(stale_warning)
        if market_summary.rows.empty:
            st.info("Add selected package items or type pick/player assets for market sanity.")
        else:
            st.dataframe(
                display_market_package_rows(market_summary.rows).astype(str),
                use_container_width=True,
                hide_index=True,
                key="trading_lab_market_rows",
            )
            st.dataframe(
                display_market_totals(market_summary.totals).astype(str),
                use_container_width=True,
                hide_index=True,
                key="trading_lab_market_totals",
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
        if mock_pick_path and not mock_pick_frame.empty:
            st.caption(f"Draft pick-order context: {mock_pick_path}")
            st.dataframe(
                display_lane_prop_frame(mock_pick_frame.head(20)),
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


def _render_trade_away_pick_planner() -> None:
    st.subheader("Trade Away Pick Planner")
    st.warning(MANUAL_PLANNER_WARNING)
    st.caption(
        "Use this when a pick like 1.05 feels uncomfortable. The page helps you write down "
        "offers and questions; it does not find offers, value picks, or update draft state."
    )
    pick_labels = _pick_labels(mock_pick_frame)
    selected_pick = st.selectbox(
        "Pick you may trade away",
        pick_labels or [NOT_ENOUGH_INFORMATION],
        index=_default_index(pick_labels, "1.05") if pick_labels else 0,
        key="trade_away_pick_planner_pick",
    )
    st.text_input(
        "Why are you considering moving it?",
        value="I do not like the options at this pick.",
        key="trade_away_pick_planner_reason",
    )
    st.text_area(
        "Manual get-side notes",
        value="",
        placeholder="Example: 2028 1st + 2.03 from Team X; confirm owner and exact terms.",
        key="trade_away_pick_planner_get_notes",
    )
    offer_text = st.text_area(
        "Manual offer comparison rows",
        value="",
        placeholder="Partner, receive assets, send assets, open questions, status",
        key="trade_away_pick_planner_offer_rows",
    )
    rows = _manual_planner_rows(
        offer_text,
        ("partner", "receive_assets", "send_assets", "open_questions", "status"),
        selected_pick,
    )
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        _download_rows(
            "Download trade-away planning notes CSV",
            rows,
            "nwr_trade_away_pick_planner_manual_notes.csv",
        )
    else:
        st.info("Enter manual offer rows to compare options without valuation.")
    st.dataframe(
        pd.DataFrame(_trade_away_checklist(selected_pick)),
        use_container_width=True,
        hide_index=True,
    )


def _render_trade_for_pick_planner() -> None:
    st.subheader("Trade For Pick Planner")
    st.warning(MANUAL_PLANNER_WARNING)
    st.caption(
        "Use this when a player is falling and you want to plan a conversation for a pick like "
        "1.08. This is a workspace, not an offer generator."
    )
    pick_labels = _pick_labels(mock_pick_frame)
    target_pick = st.selectbox(
        "Target pick to acquire",
        pick_labels or [NOT_ENOUGH_INFORMATION],
        index=_default_index(pick_labels, "1.08") if pick_labels else 0,
        key="trade_for_pick_planner_target_pick",
    )
    st.text_input(
        "Falling player or board pocket you are watching",
        value="",
        placeholder="Player name or tier pocket",
        key="trade_for_pick_planner_target_player",
    )
    st.text_area(
        "Manual assets to consider offering",
        value="",
        placeholder="Example: later current pick, future pick, player name; manual notes only.",
        key="trade_for_pick_planner_asset_notes",
    )
    scenario_text = st.text_area(
        "Manual offer-building scenarios",
        value="",
        placeholder="Scenario, possible send assets, reason to consider, open questions, status",
        key="trade_for_pick_planner_scenario_rows",
    )
    rows = _manual_planner_rows(
        scenario_text,
        ("scenario", "possible_send_assets", "reason_to_consider", "open_questions", "status"),
        target_pick,
    )
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        _download_rows(
            "Download trade-for planning notes CSV",
            rows,
            "nwr_trade_for_pick_planner_manual_notes.csv",
        )
    else:
        st.info("Enter manual scenarios to compare possible conversations without valuation.")
    st.dataframe(
        pd.DataFrame(_trade_for_checklist(target_pick)),
        use_container_width=True,
        hide_index=True,
    )


def _remove_options(
    side_keys: list[str],
    lookup: dict[str, dict[str, object]],
) -> dict[str, str]:
    options: dict[str, str] = {}
    for key in side_keys:
        label = str(lookup.get(key, {}).get("label", key))
        options[label] = key
    return options


def _pick_labels(frame: pd.DataFrame) -> list[str]:
    if frame.empty or "pick_label" not in frame.columns:
        return []
    return frame["pick_label"].astype(str).dropna().tolist()


def _default_index(options: list[str], preferred: str) -> int:
    try:
        return options.index(preferred)
    except ValueError:
        return 0


def _manual_planner_rows(
    text: str,
    columns: tuple[str, ...],
    anchor_pick: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        values = [part.strip() for part in cleaned.split(",")]
        row = {
            column: values[index] if index < len(values) and values[index] else "Manual review"
            for index, column in enumerate(columns)
        }
        row["anchor_pick"] = anchor_pick
        row["guardrail"] = MANUAL_PLANNER_WARNING
        rows.append(row)
    return rows


def _trade_away_checklist(selected_pick: str) -> list[dict[str, str]]:
    return [
        _checklist_row(
            selected_pick,
            "Confirm exact pick owner and timing before discussing terms.",
        ),
        _checklist_row(
            selected_pick,
            "Write down every asset on both sides; do not rely on memory.",
        ),
        _checklist_row(
            selected_pick,
            "Check whether this is a current-pick move, future-pick move, or player package.",
        ),
        _checklist_row(
            selected_pick,
            "After a real deal is agreed, record it in the Draft Cockpit trade event workflow.",
        ),
    ]


def _trade_for_checklist(target_pick: str) -> list[dict[str, str]]:
    return [
        _checklist_row(
            target_pick,
            "Confirm the pick owner and whether the pick is actually available.",
        ),
        _checklist_row(
            target_pick,
            "List assets you would consider sending before making an offer.",
        ),
        _checklist_row(
            target_pick,
            "Use Player Compare and Rankings as separate context, not as an automatic offer.",
        ),
        _checklist_row(
            target_pick,
            "If a real deal happens, use the Draft Cockpit trade event workflow to record it.",
        ),
    ]


def _checklist_row(anchor_pick: str, question: str) -> dict[str, str]:
    return {
        "anchor_pick": anchor_pick,
        "manual_check": question,
        "status": "Not Started",
        "guardrail": MANUAL_PLANNER_WARNING,
    }


def _download_rows(label: str, rows: list[dict[str, str]], filename: str) -> None:
    data = pd.DataFrame(rows).to_csv(index=False)
    st.download_button(label, data=data, file_name=filename, mime="text/csv")


_render_source_metrics(counts)
builder_tab, trade_away_tab, trade_for_tab = st.tabs(
    ["Package Builder", "Trade Away Pick Planner", "Trade For Pick Planner"]
)
with builder_tab:
    _render_builder(player_select, pick_select)
    _render_summary(lookup)
    _render_selected_items(lookup)
    _render_market_sanity_panel(lookup)
with trade_away_tab:
    _render_trade_away_pick_planner()
with trade_for_tab:
    _render_trade_for_pick_planner()
_render_diagnostics()
