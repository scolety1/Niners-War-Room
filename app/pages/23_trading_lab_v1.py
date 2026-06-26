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
from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    load_runtime_state,
    record_trade_event,
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
RUNTIME_STATE_KEY = "draft_day_v2_trade_lab_runtime_state"

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
st.markdown(
    '<a href="/live-draft-room" target="_self">Back to Live Draft</a>',
    unsafe_allow_html=True,
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


def _render_trade_finder() -> None:
    st.subheader("Trade Finder")
    st.caption(
        "Use when the current pick feels bad: find conservative trade-back structures from "
        "existing pick context. Decision support only; no trade calculator."
    )
    effective_pick_frame = _effective_pick_frame()
    if effective_pick_frame.empty:
        st.warning(NOT_ENOUGH_INFORMATION)
        return
    pick_labels = _pick_labels(effective_pick_frame)
    current_pick = st.selectbox(
        "Current pick to shop",
        pick_labels,
        index=_default_index(pick_labels, "1.04"),
        key="trade_finder_pick",
    )
    later_picks = _later_pick_labels(effective_pick_frame, current_pick)
    target_pick = st.selectbox(
        "Candidate later pick received",
        later_picks or pick_labels,
        index=_default_index(later_picks or pick_labels, "2.03"),
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
    st.caption(
        "Recommendation table fields: Target Owner, What To Ask For, Tier-Drop Risk, "
        "Who May Still Be Available, Confidence, and Caveat."
    )
    st.dataframe(
        _trade_back_rows(current_pick, effective_pick_frame, bundle.frame),
        use_container_width=True,
        hide_index=True,
        key="trade_finder_recommendations",
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
    effective_pick_frame = _effective_pick_frame()
    pick_labels = _pick_labels(effective_pick_frame)
    if not pick_labels:
        st.warning(NOT_ENOUGH_INFORMATION)
        return
    target_pick = st.selectbox(
        "Pick to acquire",
        pick_labels,
        index=_default_index(pick_labels, "1.04"),
        key="trade_for_pick",
    )
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
    st.caption(
        "Recommendation table fields: Cheapest Plausible Internal Package, Overpay Warning, "
        "Worth Pursuing?, Confidence, and Caveat. Decision support only."
    )
    st.dataframe(
        _trade_for_rows(player_label, target_pick, effective_pick_frame, lookup),
        use_container_width=True,
        hide_index=True,
        key="trade_for_recommendations",
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


def _effective_pick_frame() -> pd.DataFrame:
    state = st.session_state.get(RUNTIME_STATE_KEY, load_runtime_state(mode="live"))
    return apply_trade_events_to_pick_frame(mock_pick_frame, state)


def _pick_labels(frame: pd.DataFrame) -> list[str]:
    if frame.empty or "pick_label" not in frame.columns:
        return []
    return frame["pick_label"].astype(str).dropna().tolist()


def _later_pick_labels(frame: pd.DataFrame, current_pick: str) -> list[str]:
    if frame.empty or "pick_label" not in frame.columns or "overall_pick" not in frame.columns:
        return [label for label in _pick_labels(frame) if label != current_pick]
    current_rows = frame.loc[frame["pick_label"].astype(str).eq(str(current_pick))]
    if current_rows.empty:
        return [label for label in _pick_labels(frame) if label != current_pick]
    current_overall = _maybe_int(current_rows.iloc[0].get("overall_pick"))
    if current_overall is None:
        return [label for label in _pick_labels(frame) if label != current_pick]
    later = frame.loc[pd.to_numeric(frame["overall_pick"], errors="coerce") > current_overall]
    return later["pick_label"].astype(str).tolist()


def _default_index(options: list[str], preferred: str) -> int:
    try:
        return options.index(preferred)
    except ValueError:
        return 0


def _trade_back_rows(
    current_pick: str,
    frame: pd.DataFrame,
    board_frame: pd.DataFrame,
) -> pd.DataFrame:
    current = _pick_row(frame, current_pick)
    if current is None:
        return pd.DataFrame([_not_enough_row("Trade-back target")])
    current_overall = _maybe_int(current.get("overall_pick"))
    if current_overall is None:
        return pd.DataFrame([_not_enough_row("Trade-back target")])
    candidates = frame.loc[
        (pd.to_numeric(frame["overall_pick"], errors="coerce") > current_overall)
        & (pd.to_numeric(frame["overall_pick"], errors="coerce") <= current_overall + 18)
    ].head(8)
    rows: list[dict[str, str]] = []
    for _index, row in candidates.iterrows():
        target_pick = str(row.get("pick_label") or NOT_ENOUGH_INFORMATION)
        rows.append(
            {
                "Current Pick": current_pick,
                "Trade-Back Target": target_pick,
                "Target Owner": _text(row.get("current_owner")),
                "What To Ask For": _ask_for_note(current_pick, target_pick),
                "Tier-Drop Risk": _tier_drop_risk(
                    current_overall,
                    _maybe_int(row.get("overall_pick")),
                    board_frame,
                ),
                "Who May Still Be Available": _players_near_pick(
                    _maybe_int(row.get("overall_pick")),
                    board_frame,
                ),
                "Confidence": "Medium" if _text(row.get("current_owner")) else "Low",
                "Caveat": "Decision support only; no final trade advice or trade calculator.",
            }
        )
    return pd.DataFrame(rows) if rows else pd.DataFrame([_not_enough_row("Trade-back target")])


def _trade_for_rows(
    player_label: str,
    target_pick: str,
    frame: pd.DataFrame,
    lookup: dict[str, dict[str, object]],
) -> pd.DataFrame:
    target = _pick_row(frame, target_pick)
    selected = _lookup_by_label(player_label, lookup)
    if target is None or selected is None:
        return pd.DataFrame([_not_enough_row("Trade-for package")])
    target_overall = _maybe_int(target.get("overall_pick"))
    selected_rank = _maybe_int(selected.get("final_board_rank"))
    owned_later = _owned_later_picks(frame, target_overall)
    package = (
        f"Start with {owned_later[0]} plus a future pick sweetener"
        if owned_later
        else "Future pick package only"
    )
    return pd.DataFrame(
        [
            {
                "Target Player": player_label,
                "Pick To Acquire": target_pick,
                "Current Owner": _text(target.get("current_owner")),
                "Cheapest Plausible Internal Package": package,
                "Overpay Warning": _overpay_warning(target_overall, selected_rank),
                "Worth Pursuing?": _worth_pursuing(target_overall, selected_rank),
                "Confidence": "Medium" if selected_rank is not None else "Low",
                "Caveat": "Decision support only; accepted trade writes local event log.",
            }
        ]
    )


def _pick_row(frame: pd.DataFrame, pick_label: str) -> pd.Series | None:
    if frame.empty or "pick_label" not in frame.columns:
        return None
    matches = frame.loc[frame["pick_label"].astype(str).eq(str(pick_label))]
    if matches.empty:
        return None
    return matches.iloc[0]


def _lookup_by_label(
    label: str,
    lookup: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    for item in lookup.values():
        if str(item.get("label")) == label:
            return item
    return None


def _ask_for_note(current_pick: str, target_pick: str) -> str:
    current_round = _round_from_pick(current_pick)
    target_round = _round_from_pick(target_pick)
    if current_round is not None and target_round is not None and target_round > current_round:
        return f"{target_pick} plus a future 1st/2nd or equivalent make-up asset"
    return f"{target_pick} plus a meaningful future pick if tier drops"


def _tier_drop_risk(
    current_overall: int | None,
    target_overall: int | None,
    board_frame: pd.DataFrame,
) -> str:
    if current_overall is None or target_overall is None:
        return NOT_ENOUGH_INFORMATION
    current_tier = _tier_at_rank(current_overall, board_frame)
    target_tier = _tier_at_rank(target_overall, board_frame)
    if current_tier == NOT_ENOUGH_INFORMATION or target_tier == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    if current_tier == target_tier:
        return f"Low: still around {target_tier}"
    return f"High: moves from {current_tier} to {target_tier}"


def _players_near_pick(overall_pick: int | None, board_frame: pd.DataFrame) -> str:
    if overall_pick is None or board_frame.empty or "final_board_rank" not in board_frame.columns:
        return NOT_ENOUGH_INFORMATION
    ranks = pd.to_numeric(board_frame["final_board_rank"], errors="coerce")
    window = board_frame.loc[(ranks >= overall_pick - 2) & (ranks <= overall_pick + 2)]
    names = [
        f"{row.get('player')} ({row.get('position')})"
        for _index, row in window.head(5).iterrows()
    ]
    return ", ".join(names) if names else NOT_ENOUGH_INFORMATION


def _owned_later_picks(frame: pd.DataFrame, target_overall: int | None) -> list[str]:
    if target_overall is None or frame.empty:
        return []
    if not {"overall_pick", "pick_label", "current_owner"}.issubset(frame.columns):
        return []
    later = frame.loc[
        (pd.to_numeric(frame["overall_pick"], errors="coerce") > target_overall)
        & frame["current_owner"].astype(str).str.contains("Niners|NWR", case=False, na=False)
    ]
    return later["pick_label"].astype(str).head(3).tolist()


def _overpay_warning(target_overall: int | None, selected_rank: int | None) -> str:
    if target_overall is None or selected_rank is None:
        return NOT_ENOUGH_INFORMATION
    if target_overall < selected_rank - 6:
        return "High: acquiring this pick is earlier than the player's board neighborhood."
    if target_overall > selected_rank + 6:
        return "Lower: target player is past the board neighborhood."
    return "Moderate: price and player rank are in the same neighborhood."


def _worth_pursuing(target_overall: int | None, selected_rank: int | None) -> str:
    if target_overall is None or selected_rank is None:
        return NOT_ENOUGH_INFORMATION
    if target_overall >= selected_rank + 6:
        return "Looks favorable"
    if target_overall >= selected_rank - 3:
        return "Close / needs human judgment"
    return "Risky"


def _tier_at_rank(rank: int, board_frame: pd.DataFrame) -> str:
    if board_frame.empty or "final_board_rank" not in board_frame.columns:
        return NOT_ENOUGH_INFORMATION
    ranks = pd.to_numeric(board_frame["final_board_rank"], errors="coerce")
    rows = board_frame.loc[ranks.eq(rank)]
    if rows.empty:
        return NOT_ENOUGH_INFORMATION
    return _text(rows.iloc[0].get("final_tier")) or NOT_ENOUGH_INFORMATION


def _round_from_pick(pick_label: str) -> int | None:
    try:
        return int(str(pick_label).split(".")[0])
    except (ValueError, IndexError):
        return None


def _maybe_int(value: object) -> int | None:
    try:
        if str(value or "").strip() == "":
            return None
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str:
    text = str(value or "").strip()
    if text.lower() in {"", "nan", "none", "null"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _not_enough_row(label: str) -> dict[str, str]:
    return {
        label: NOT_ENOUGH_INFORMATION,
        "Confidence": "Low",
        "Caveat": "Decision support only; no final trade advice or trade calculator.",
    }


_render_source_metrics(counts)
builder_tab, finder_tab, trade_for_tab = st.tabs(
    ["Package Builder", "Trade Finder", "Trade For"]
)
with builder_tab:
    _render_builder(player_select, pick_select)
    _render_summary(lookup)
    _render_selected_items(lookup)
    _render_market_sanity_panel(lookup)
with finder_tab:
    _render_trade_finder()
with trade_for_tab:
    _render_trade_for()
_render_diagnostics()
