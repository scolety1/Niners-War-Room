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
from src.services.draft_day_app_v1_service import (
    load_expanded_draftable_player_pool,
    load_frozen_board,
    load_lane_prop_file,
)
from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    export_runtime_state,
    export_runtime_state_json,
    load_latest_runtime_state,
    load_runtime_state,
    reset_runtime_state,
    runtime_paths,
    save_runtime_state,
    update_workflow_state,
)
from src.services.draft_day_workflow_service import (
    DraftWorkflowError,
    assign_player_to_pick,
    pick_select_options,
    player_key_from_row,
)
from src.services.drafting_mode_cockpit_service import (
    DEFAULT_SORT_LABEL,
    build_cockpit_board,
    build_cockpit_summary,
    compare_decision_rows,
    current_pick_for_assignment,
    decision_panel_rows,
    display_cockpit_board,
    owned_pick_rows,
    player_options,
    recent_event_rows,
    recent_trade_rows,
    record_cockpit_trade,
    selected_player_row,
    tier_count_rows,
)

SESSION_KEY = "drafting_mode_cockpit_v1"
SESSION_TYPE_KEY = f"{SESSION_KEY}_session_type"
RESET_PENDING_KEY = f"{SESSION_KEY}_reset_pending_mode"
SESSION_LABELS = {
    "live": "Live Draft",
    "mock": "Mock Draft / Practice",
}
SESSION_BADGES = {
    "live": "LIVE DRAFT MODE",
    "mock": "MOCK PRACTICE MODE",
}


def _runtime_state_key(mode: str) -> str:
    return f"{SESSION_KEY}_{mode}_runtime_state"


def _valid_session_mode(value: object) -> str:
    token = str(value or "").strip().lower()
    return token if token in SESSION_LABELS else "live"


def _session_mode() -> str:
    return _valid_session_mode(st.session_state.get(SESSION_TYPE_KEY, "live"))


def _session_label(mode: str) -> str:
    return SESSION_LABELS[_valid_session_mode(mode)]


def _session_badge(mode: str) -> str:
    return SESSION_BADGES[_valid_session_mode(mode)]


def _render_session_selector() -> str:
    current_mode = _session_mode()
    labels = list(SESSION_LABELS.values())
    selected = st.radio(
        "Draft Session:",
        labels,
        index=labels.index(_session_label(current_mode)),
        horizontal=True,
        key=f"{SESSION_KEY}_session_selector",
    )
    next_mode = next(mode for mode, label in SESSION_LABELS.items() if label == selected)
    st.session_state[SESSION_TYPE_KEY] = next_mode
    st.markdown(f"**{_session_badge(next_mode)}**")
    if next_mode == "mock":
        st.warning("Practice state only — does not affect live draft.")
    return next_mode


def _runtime_state(mode: str | None = None) -> dict[str, object]:
    runtime_mode = _valid_session_mode(mode or _session_mode())
    key = _runtime_state_key(runtime_mode)
    if key not in st.session_state:
        st.session_state[key] = load_runtime_state(
            mode=runtime_mode,
            source_checkpoint=SOURCE_CAPTION,
        )
    return st.session_state[key]


def _set_runtime_state(state: dict[str, object]) -> None:
    mode = _valid_session_mode(state.get("mode") or _session_mode())
    st.session_state[_runtime_state_key(mode)] = state


def _action_links(mode: str) -> None:
    session_query = _valid_session_mode(mode)
    links = [
        ("Full Rankings", "/rankings"),
        ("Cheat Sheets", f"/cheat-sheets?session_type={session_query}"),
        ("Full Player Compare", "/player-compare"),
        ("Full Trading Lab", "/trading-lab"),
        ("Post-Draft Mode", "/post-draft-mode"),
        ("Settings/Data Health", "/settings-data-health"),
    ]
    for label, path in links:
        st.link_button(label, path, use_container_width=True)


def _render_top_bar(summary, session_mode: str) -> None:
    metric_cols = st.columns([1.1, 1.25, 0.9, 0.9, 1.35])
    metric_cols[0].metric("Current pick", summary.current_pick)
    metric_cols[1].metric("On-clock team", summary.on_clock_team)
    metric_cols[2].metric("Drafted", summary.drafted_count)
    metric_cols[3].metric("Trades", summary.trade_count)
    metric_cols[4].metric("Autosave", summary.autosave_status, help=summary.last_saved)

    action_cols = st.columns([1, 1, 1, 1, 1, 1, 1])
    if (REPO_ROOT / "src" / "services" / "data_refresh_orchestrator_service.py").exists():
        action_cols[0].link_button("Refresh Data", "/refresh-data", use_container_width=True)
    if action_cols[1].button("Save State", use_container_width=True):
        _set_runtime_state(
            save_runtime_state(
                _runtime_state(session_mode),
                event_type="manual_save",
                event_detail={
                    "source": "drafting_mode_cockpit",
                    "session_type": session_mode,
                },
            )
        )
        st.success(f"{_session_label(session_mode)} state saved.")
        st.rerun()
    if action_cols[2].button("Load Latest", use_container_width=True):
        _set_runtime_state(
            load_latest_runtime_state(mode=session_mode, source_checkpoint=SOURCE_CAPTION)
        )
        st.success(f"Latest {_session_label(session_mode)} state loaded.")
        st.rerun()
    if action_cols[3].button("Export", use_container_width=True):
        exports = export_runtime_state(_runtime_state(session_mode))
        _set_runtime_state(
            save_runtime_state(
                _runtime_state(session_mode),
                event_type="export_created",
                event_detail={label: str(path) for label, path in exports.items()},
            )
        )
        st.success("Exported local draft log.")
    action_cols[4].link_button(
        "Settings/Data Health",
        "/settings-data-health",
        use_container_width=True,
    )
    if action_cols[5].button("Reset", use_container_width=True):
        st.session_state[RESET_PENDING_KEY] = session_mode
    action_cols[6].link_button("Normal App View", "/rankings", use_container_width=True)
    _render_reset_confirmation(session_mode)


def _render_reset_confirmation(session_mode: str) -> None:
    pending_mode = st.session_state.get(RESET_PENDING_KEY)
    if pending_mode != session_mode:
        return
    if session_mode == "live":
        st.warning(
            "Resetting Live Draft state clears live picks and trades only. "
            "Mock Practice state is not changed."
        )
        confirm_label = "I understand this resets Live Draft state only."
    else:
        st.warning("Practice state only — reset affects mock draft/practice state only.")
        confirm_label = "I understand this resets Mock Draft / Practice state only."
    confirmed = st.checkbox(confirm_label, key=f"{SESSION_KEY}_{session_mode}_reset_confirmed")
    confirm_cols = st.columns([1, 1, 4])
    if confirm_cols[0].button("Confirm Reset", disabled=not confirmed, use_container_width=True):
        _set_runtime_state(
            reset_runtime_state(
                _runtime_state(session_mode),
                reason=f"manual_{session_mode}_reset_from_cockpit",
            )
        )
        st.session_state.pop(RESET_PENDING_KEY, None)
        st.success(f"{_session_label(session_mode)} state reset.")
        st.rerun()
    if confirm_cols[1].button("Cancel Reset", use_container_width=True):
        st.session_state.pop(RESET_PENDING_KEY, None)
        st.rerun()


def _render_left_rail(
    state: dict[str, object],
    pick_frame: pd.DataFrame,
    session_mode: str,
) -> None:
    st.markdown("#### Your Draft Rail")
    owned = owned_pick_rows(pick_frame, state)
    st.caption("Owned picks")
    if owned.empty:
        st.info("Not enough information")
    else:
        st.dataframe(owned.head(10), use_container_width=True, hide_index=True)

    st.caption("Recent pick/trade events")
    events = recent_event_rows(state)
    if events.empty:
        st.write("No runtime events yet.")
    else:
        st.dataframe(events, use_container_width=True, hide_index=True)

    trades = recent_trade_rows(state)
    st.caption("Recent trades")
    if trades.empty:
        st.write("No trade events recorded.")
    else:
        st.dataframe(trades, use_container_width=True, hide_index=True)

    with st.expander("Pick ownership overrides", expanded=False):
        overrides = state.get("pick_ownership_overrides", {})
        if isinstance(overrides, dict) and overrides:
            st.dataframe(
                pd.DataFrame(
                    [
                        {"pick": pick, **value}
                        for pick, value in overrides.items()
                        if isinstance(value, dict)
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("No ownership overrides recorded.")

    with st.expander("Deep tools", expanded=True):
        _action_links(session_mode)


def _render_board_controls(board_frame: pd.DataFrame) -> tuple[str, str, str, bool, bool]:
    controls = st.columns([1.3, 0.8, 1, 0.9, 0.7])
    search = controls[0].text_input(
        "Search",
        placeholder="Player name",
        key=f"{SESSION_KEY}_search",
    )
    positions = ["All"]
    if "position" in board_frame.columns:
        positions.extend(
            sorted(
                value
                for value in board_frame["position"].astype(str).dropna().unique().tolist()
                if value
            )
        )
    position = controls[1].selectbox("Position", positions, key=f"{SESSION_KEY}_position")
    tiers = ["All"]
    if "dynasty_asset_tier" in board_frame.columns:
        tiers.extend(
            sorted(
                value
                for value in (
                    board_frame["dynasty_asset_tier"].astype(str).dropna().unique().tolist()
                )
                if value
            )
        )
    tier = controls[2].selectbox("Tier", tiers, key=f"{SESSION_KEY}_tier")
    show_pdf = controls[3].toggle("PDF FAs", value=True, key=f"{SESSION_KEY}_show_pdf")
    show_k_dst = controls[4].toggle("K/DST", value=False, key=f"{SESSION_KEY}_show_k_dst")
    return search, position, tier, show_pdf, show_k_dst


def _render_center_board(
    *,
    board_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    state: dict[str, object],
    session_mode: str,
) -> tuple[pd.DataFrame, dict[str, object] | None, dict[str, object] | None]:
    st.markdown("#### Best Available Board")
    search, position, tier, show_pdf, show_k_dst = _render_board_controls(board_frame)
    filtered = build_cockpit_board(
        board_frame,
        state,
        search=search,
        position=position,
        tier=tier,
        show_pdf_free_agents=show_pdf,
        show_k_dst=show_k_dst,
        sort_label=DEFAULT_SORT_LABEL,
    )
    counts = tier_count_rows(filtered)
    if counts:
        st.dataframe(pd.DataFrame(counts), use_container_width=True, hide_index=True)
    st.dataframe(
        display_cockpit_board(filtered).head(80),
        use_container_width=True,
        hide_index=True,
        key=f"{SESSION_KEY}_main_board",
    )

    options = player_options(filtered)
    if not options:
        st.warning("No available players match the current filters.")
        return filtered, None, None
    selected_label = st.selectbox("Select player", list(options), key=f"{SESSION_KEY}_selected")
    selected = selected_player_row(filtered, options[selected_label])

    comparison_options = {"None": ""}
    comparison_options.update(options)
    comparison_label = st.selectbox(
        "Compare against",
        list(comparison_options),
        key=f"{SESSION_KEY}_compare_against",
    )
    comparison = (
        selected_player_row(filtered, comparison_options[comparison_label])
        if comparison_options[comparison_label]
        else None
    )

    action_cols = st.columns([1, 1, 1, 1])
    if action_cols[0].button("Mark Drafted", use_container_width=True):
        _mark_player_drafted(
            selected=selected,
            board_frame=board_frame,
            pick_frame=pick_frame,
            state=state,
        )
    action_cols[1].link_button("Open Full Compare", "/player-compare", use_container_width=True)
    action_cols[2].link_button("Open Trade Lab", "/trading-lab", use_container_width=True)
    note = st.text_input("Flag/note", key=f"{SESSION_KEY}_note", placeholder="Optional note")
    if action_cols[3].button("Add Note", use_container_width=True):
        if selected and note.strip():
            next_state = dict(_runtime_state(session_mode))
            notes = list(next_state.get("notes", []))
            notes.append(f"{selected.get('player', 'Player')}: {note.strip()}")
            next_state["notes"] = notes
            _set_runtime_state(
                save_runtime_state(
                    next_state,
                    event_type="note_added",
                    event_detail={"player": selected.get("player", ""), "note": note.strip()},
                )
            )
            st.success("Note added to local runtime state.")
            st.rerun()
        else:
            st.warning("Select a player and enter a note first.")
    return filtered, selected, comparison


def _mark_player_drafted(
    *,
    selected: dict[str, object] | None,
    board_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    state: dict[str, object],
) -> None:
    if selected is None:
        st.warning("Select a player first.")
        return
    current_pick = current_pick_for_assignment(pick_frame, state)
    if current_pick is None:
        st.warning("No current pick is available.")
        return
    adjusted_picks = apply_trade_events_to_pick_frame(pick_frame, state)
    try:
        next_workflow = assign_player_to_pick(
            state["workflow_state"],  # type: ignore[index]
            board=board_frame,
            pick_frame=adjusted_picks,
            player_key=player_key_from_row(selected),
            overall_pick=current_pick,
        )
    except DraftWorkflowError as exc:
        st.error(str(exc))
        return
    pick_options = pick_select_options(adjusted_picks)
    pick_label = next(
        (label for label, pick in pick_options.items() if pick == current_pick),
        str(current_pick),
    )
    _set_runtime_state(
        update_workflow_state(
            state,
            next_workflow,
            event_type="pick_assigned",
            event_detail={
                "player": selected.get("player", ""),
                "player_id": player_key_from_row(selected),
                "position": selected.get("position", ""),
                "pick_label": pick_label.split(" - ", maxsplit=1)[0],
                "overall_pick": current_pick,
            },
        )
    )
    st.success(f"Marked {selected.get('player', 'player')} drafted.")
    st.rerun()


def _render_right_panel(
    selected: dict[str, object] | None,
    comparison: dict[str, object] | None,
) -> None:
    st.markdown("#### Decision Panel")
    st.dataframe(
        pd.DataFrame(decision_panel_rows(selected)),
        use_container_width=True,
        hide_index=True,
    )
    with st.expander("Compare decision summary", expanded=bool(comparison)):
        st.dataframe(
            pd.DataFrame(compare_decision_rows(selected, comparison)),
            use_container_width=True,
            hide_index=True,
        )


def _render_trade_recorder(state: dict[str, object]) -> None:
    with st.expander("Record Trade", expanded=False):
        st.caption(
            "Local runtime trade event only. Updates parseable current-year pick ownership "
            "overrides; future picks are logged; unparseable assets require review."
        )
        cols = st.columns(2)
        team_a = cols[0].text_input("Team A", value="NWR", key=f"{SESSION_KEY}_trade_team_a")
        team_b = cols[1].text_input("Team B", value="Team B", key=f"{SESSION_KEY}_trade_team_b")
        asset_cols = st.columns(2)
        team_a_sends = asset_cols[0].text_area(
            "Team A sends",
            value="2026 1.04",
            key=f"{SESSION_KEY}_team_a_sends",
        )
        team_b_sends = asset_cols[1].text_area(
            "Team B sends",
            value="2026 2.03, 2028 1st",
            key=f"{SESSION_KEY}_team_b_sends",
        )
        notes = st.text_area("Notes", key=f"{SESSION_KEY}_trade_notes")
        if st.button("Record trade", key=f"{SESSION_KEY}_record_trade"):
            _set_runtime_state(
                record_cockpit_trade(
                    state,
                    team_a=team_a,
                    team_a_sends=team_a_sends,
                    team_b=team_b,
                    team_b_sends=team_b_sends,
                    notes=notes,
                )
            )
            st.success("Trade event recorded.")
            st.rerun()


bundle = load_frozen_board()
draftable_board = (
    load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame
)
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
SOURCE_CAPTION = (
    f"Frozen baseline checkpoint: {bundle.source_path}. Pick order: {pick_path}. "
    "Draftable overlay: LVE Rosters 061326.pdf page 3 Free Agents. "
    "K/DST hidden by default. Market/ADP context is display-only and never drives default sort."
)

page_header(
    "Drafting Mode",
    eyebrow="On-Clock Cockpit",
    description=(
        "Draft session workspace: board first, runtime state always local, "
        "source truth unchanged."
    ),
    status_items=(
        ("Cockpit active", "safe"),
        ("Autosave local", "safe"),
        ("Market display-only", "review"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)
session_mode = _render_session_selector()
state = _runtime_state(session_mode)
summary = build_cockpit_summary(
    board_frame=draftable_board,
    pick_frame=pick_frame,
    runtime_state=state,
)
_render_top_bar(summary, session_mode)

left, center, right = st.columns([1.1, 2.35, 1.15])
with left:
    _render_left_rail(state, pick_frame, session_mode)
with center:
    _filtered, selected_player, comparison_player = _render_center_board(
        board_frame=draftable_board,
        pick_frame=pick_frame,
        state=state,
        session_mode=session_mode,
    )
    _render_trade_recorder(_runtime_state(session_mode))
with right:
    _render_right_panel(selected_player, comparison_player)

with st.expander("Source / guardrails", expanded=False):
    st.caption(SOURCE_CAPTION)
    st.caption(
        "Default cockpit sort is Dynasty Asset Tier/Rank. Frozen Final Board Rank is a "
        "baseline/checkpoint display, not source truth for the full available pool."
    )
    st.caption(
        "DynastyProcess, ADP, and market fields are display-only timing/sanity context and "
        "do not drive default sort, model inputs, ranks, tiers, or hidden sort."
    )
    st.download_button(
        "Download current runtime JSON",
        data=export_runtime_state_json(_runtime_state(session_mode)),
        file_name=f"drafting_mode_{session_mode}_runtime_state.json",
        mime="application/json",
    )
    paths = runtime_paths()
    st.caption(f"Runtime root: {paths.root}")
