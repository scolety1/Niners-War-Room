from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import render_source_of_truth_badge, stop_if_board_blocked
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_file
from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    event_rows,
    load_runtime_state,
    runtime_paths,
)

bundle = load_frozen_board()
live_state = load_runtime_state(mode="live")
mock_state = load_runtime_state(mode="mock")
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Your Team")
        st.caption("Local runtime view only. Source truth, ranks, and roster files are unchanged.")
        metric_cols = st.columns(2)
        metric_cols[0].metric("Live picks", len(live_state["workflow_state"]["assignments"]))
        metric_cols[1].metric("Trades", len(live_state["trade_events"]))
        st.caption(f"Last autosave: {_last_autosave(live_state)}")
        st.caption(f"Owned picks: {_owned_pick_summary(pick_frame, live_state)}")
        st.caption(f"Drafted: {_assignment_summary(live_state)}")
        st.caption(f"Future picks: {_future_pick_summary(live_state)}")

        with st.expander("Current owned picks", expanded=True):
            owned = _owned_pick_rows(pick_frame, live_state)
            if owned.empty:
                st.write("Not enough information")
            else:
                st.dataframe(owned, use_container_width=True, hide_index=True)

        with st.expander("Drafted by NWR this draft", expanded=True):
            assignments = _assignment_rows(live_state)
            if assignments.empty:
                st.write("No picks assigned yet.")
            else:
                st.dataframe(assignments, use_container_width=True, hide_index=True)

        with st.expander("Future picks from trade events", expanded=True):
            future = _future_pick_rows(live_state)
            if future.empty:
                st.write("No future pick events recorded yet.")
            else:
                st.dataframe(future, use_container_width=True, hide_index=True)

        with st.expander("Trades made during draft", expanded=False):
            trades = _trade_event_rows(live_state)
            if trades.empty:
                st.write("No trade events recorded yet.")
            else:
                st.dataframe(trades, use_container_width=True, hide_index=True)

        with st.expander("Roster source", expanded=False):
            st.write(
                "Not enough information. A current NWR roster source is not wired into this "
                "Drafting Mode sidebar, so this panel shows runtime picks/trades only."
            )
        with st.expander("Runtime status", expanded=False):
            paths = runtime_paths()
            st.caption(f"Runtime root: {paths.root}")
            st.caption(f"Pick source: {pick_path or 'Not enough information'}")
            st.caption(f"Live events: {len(event_rows(live_state))}")
            st.caption(f"Mock picks: {len(mock_state['workflow_state']['assignments'])}")


def _owned_pick_rows(frame: pd.DataFrame, state: dict[str, object]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    adjusted = apply_trade_events_to_pick_frame(frame, state)
    required = {"overall_pick", "pick_label", "current_owner", "is_nwr_pick"}
    if not required.issubset(adjusted.columns):
        return pd.DataFrame()
    owner_mask = adjusted["current_owner"].astype(str).str.contains(
        "Niners|NWR", case=False, na=False
    )
    nwr_mask = adjusted["is_nwr_pick"].astype(str).str.lower().isin({"true", "1", "yes"})
    rows = adjusted.loc[owner_mask | nwr_mask].copy()
    if rows.empty:
        return pd.DataFrame()
    columns = ["overall_pick", "pick_label", "current_owner", "original_owner"]
    rows = rows.loc[:, [column for column in columns if column in rows.columns]]
    return rows.rename(
        columns={
            "overall_pick": "Overall",
            "pick_label": "Pick",
            "current_owner": "Current Owner",
            "original_owner": "Original Owner",
        }
    )


def _owned_pick_summary(frame: pd.DataFrame, state: dict[str, object]) -> str:
    rows = _owned_pick_rows(frame, state)
    if rows.empty or "Pick" not in rows.columns:
        return "Not enough information"
    picks = rows["Pick"].astype(str).head(6).tolist()
    suffix = "..." if len(rows) > 6 else ""
    return ", ".join(picks) + suffix


def _assignment_rows(state: dict[str, object]) -> pd.DataFrame:
    assignments = state.get("workflow_state", {}).get("assignments", [])  # type: ignore[union-attr]
    if not isinstance(assignments, list) or not assignments:
        return pd.DataFrame()
    rows = pd.DataFrame([row for row in assignments if isinstance(row, dict)])
    columns = [
        column
        for column in ("pick_label", "player", "position", "nfl_team")
        if column in rows.columns
    ]
    if not columns:
        return pd.DataFrame()
    return rows.loc[:, columns].rename(
        columns={
            "pick_label": "Pick",
            "player": "Player",
            "position": "Pos",
            "nfl_team": "NFL Team",
        }
    )


def _assignment_summary(state: dict[str, object]) -> str:
    rows = _assignment_rows(state)
    if rows.empty or "Player" not in rows.columns:
        return "No picks assigned yet."
    players = rows["Player"].astype(str).head(4).tolist()
    suffix = "..." if len(rows) > 4 else ""
    return ", ".join(players) + suffix


def _future_pick_rows(state: dict[str, object]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for trade in state.get("trade_events", []):
        if not isinstance(trade, dict):
            continue
        future_picks = trade.get("future_picks", [])
        if not isinstance(future_picks, list):
            continue
        for pick in future_picks:
            rows.append(
                {
                    "Future Pick": str(pick),
                    "Counterparty": str(trade.get("counterparty") or "Not enough information"),
                    "Trade": (
                        f"Send {trade.get('sends', '')}; "
                        f"Receive {trade.get('receives', '')}"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _future_pick_summary(state: dict[str, object]) -> str:
    rows = _future_pick_rows(state)
    if rows.empty or "Future Pick" not in rows.columns:
        return "No future pick events recorded yet."
    picks = rows["Future Pick"].astype(str).drop_duplicates().head(4).tolist()
    suffix = "..." if len(rows) > 4 else ""
    return ", ".join(picks) + suffix


def _trade_event_rows(state: dict[str, object]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for trade in state.get("trade_events", []):
        if not isinstance(trade, dict):
            continue
        rows.append(
            {
                "Type": str(trade.get("trade_type") or "Not enough information"),
                "Counterparty": str(trade.get("counterparty") or "Not enough information"),
                "Sends": str(trade.get("sends") or "Not enough information"),
                "Receives": str(trade.get("receives") or "Not enough information"),
            }
        )
    return pd.DataFrame(rows)


def _last_autosave(state: dict[str, object]) -> str:
    return str(state.get("updated_at_utc") or "Not enough information")


_render_sidebar()

page_header(
    "Drafting Mode",
    eyebrow="Draft-Day App V2",
    description=(
        "One on-clock shell for Live Draft, Mock Draft, cheat sheets, trade tools, player "
        "compare, search, and post-draft review. Runtime state is local-only and reload-safe."
    ),
    status_items=(
        ("Persistent runtime state", "safe"),
        ("Source truth unchanged", "safe"),
        ("Decision support only", "review"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

top_cols = st.columns([1, 1, 1, 2])
with top_cols[0]:
    st.markdown("**Enter Live Draft Room**")
    st.code("/live-draft-room")
    st.caption("Use for the real draft and reload-safe live picks.")
with top_cols[1]:
    st.markdown("**Enter Mock Draft**")
    st.code("/mock-draft")
    st.caption("Practice state remains separate from Live Draft.")
with top_cols[2]:
    st.markdown("**Open Cheat Sheets**")
    st.code("/cheat-sheets")
    st.caption("Overall-first tiered board for quick scanning.")
with top_cols[3]:
    st.caption(
        "Drafting Mode is a workflow shell. Final Board Rank and Dynasty Rank remain visible "
        "baselines; V2 runtime events do not edit source artifacts."
    )

tabs = st.tabs(
    [
        "Cheat Sheets",
        "Draft Board",
        "Trade Lab",
        "Player Compare",
        "Search",
        "Settings / Data Health",
    ]
)

with tabs[0]:
    st.subheader("Cheat Sheets")
    st.caption("Overall-first tiered view for on-clock scanning.")
    st.code("/cheat-sheets")

with tabs[1]:
    st.subheader("Draft Board")
    st.caption("Use Live Draft for real picks or Mock Draft for practice state.")
    draft_cols = st.columns(2)
    with draft_cols[0]:
        st.code("/live-draft-room")
    with draft_cols[1]:
        st.code("/mock-draft")

with tabs[2]:
    st.subheader("Trade Lab")
    st.caption("Manual package review plus V2 trade-event recording. No trade calculator logic.")
    st.code("/trading-lab")

with tabs[3]:
    st.subheader("Player Compare")
    st.caption("Decision summary first; detailed context behind expanders.")
    st.code("/player-compare")

with tabs[4]:
    st.subheader("Search")
    if bundle.loaded and "player" in bundle.frame.columns:
        query = st.text_input("Find a player on the frozen board", placeholder="Search player")
        search_frame = bundle.frame.copy()
        if query:
            search_frame = search_frame.loc[
                search_frame["player"].astype(str).str.contains(query, case=False, na=False)
            ]
        columns = [
            column
            for column in ("final_board_rank", "player", "position", "nfl_team", "final_tier")
            if column in search_frame.columns
        ]
        st.dataframe(
            search_frame.loc[:, columns].head(40).rename(
                columns={
                    "final_board_rank": "Final Board Rank",
                    "player": "Player",
                    "position": "Pos",
                    "nfl_team": "NFL Team",
                    "final_tier": "Tier",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Frozen board search is unavailable.")

with tabs[5]:
    st.subheader("Settings / Data Health")
    paths = runtime_paths()
    st.caption(f"Runtime state root: {paths.root}")
    runtime_rows = [
        {
            "Mode": "Live",
            "Picks": len(live_state["workflow_state"]["assignments"]),
            "Trades": len(live_state["trade_events"]),
            "Events": len(event_rows(live_state)),
        },
        {
            "Mode": "Mock",
            "Picks": len(mock_state["workflow_state"]["assignments"]),
            "Trades": len(mock_state["trade_events"]),
            "Events": len(event_rows(mock_state)),
        },
    ]
    st.dataframe(pd.DataFrame(runtime_rows), use_container_width=True, hide_index=True)
    st.code("/settings")
