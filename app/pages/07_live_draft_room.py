from __future__ import annotations

# ruff: noqa: E402
import html
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.demo_source_labels import demo_source_label
from app.components.draft_session import (
    dirty_key,
    draft_state_key,
    reset_confirm_key,
    selected_pick_key,
    selected_pick_number,
    state_from_session,
)
from app.components.player_detail_card import render_player_detail_card
from src.config.settings import get_settings
from src.services.draft_state_service import (
    DraftBoardState,
    available_players_after_picks,
    best_remaining_by_position,
    current_draft_pick,
    draft_board_export_rows,
    draft_pick_grid_rows,
    drafted_player_at_pick,
    is_my_turn,
    mark_player_drafted,
    pick_guardrail_status,
    recent_drafted_players,
    remaining_pool_export_rows,
    replace_drafted_player_at_pick,
    reset_mock,
    search_available_players,
    undo_pick,
)
from src.services.draft_ux_service import (
    DRAFT_ROUNDS,
    DRAFT_TEAMS,
    DRAFT_TOTAL_PICKS,
    build_draft_ux_contract,
)
from src.services.mock_draft_storage_service import (
    MockDraftValidationError,
    clear_mock_draft,
    duplicate_mock_draft,
    list_mock_drafts,
    load_mock_draft,
    save_mock_draft,
)
from src.services.player_detail_card_service import build_player_detail_card_payload

DRAFT_PREP_ROOT = REPO_ROOT / "local_exports/model_v4/draft_prep/latest"
SCOUTING_PREP_POOL_ROWS = DRAFT_PREP_ROOT / "scouting_prep_pool_review_rows.csv"
OWNED_PICK_LABELS = ("1.03", "1.04", "2.04", "2.08", "5.04")
SOURCE_TYPE_OPTIONS = ("All", "Rookie", "Free Agent / Veteran Preview")
POSITION_OPTIONS = ("All", "QB", "RB", "WR", "TE", "FLEX")
FLEX_POSITIONS = {"RB", "WR", "TE"}
MISSING = "—"


@st.cache_data
def _load_contract(active_data_pack: str, fingerprint: tuple[str, int, int, int]):
    _ = fingerprint
    return build_draft_ux_contract(active_data_pack)


@st.cache_data
def _load_scouting_pool(path_text: str, fingerprint: tuple[str, int, int, int]) -> pd.DataFrame:
    _ = fingerprint
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


def _render_css() -> None:
    st.markdown(
        """
        <style>
        .live-draft-banner {
            border: 1px solid #f2c76e;
            background: #fff8e6;
            color: #4f3600;
            padding: 0.85rem 1rem;
            border-radius: 8px;
            margin: 0.75rem 0 1rem;
        }
        .pick-grid table td {
            white-space: normal;
        }
        .source-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
            gap: 0.55rem;
            margin: 0.75rem 0 0.35rem;
        }
        .source-card {
            border: 1px solid #d7dde8;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.7rem 0.75rem;
            min-height: 82px;
        }
        .source-card-label {
            color: #536276;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        .source-card-value {
            color: #1d2633;
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.28rem;
            overflow-wrap: anywhere;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none"} else text


def _slug(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return slug or "unknown"


def _score_value(row: pd.Series) -> float:
    for column in ("nwr_draft_value", "nwr_rookie_score", "nwr_dynasty_score"):
        value = pd.to_numeric(row.get(column, ""), errors="coerce")
        if pd.notna(value):
            return float(value)
    return 0.0


def _warning_summary(value: object) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    count = len([part for part in re.split(r"[|;]", text) if part.strip()])
    return f"{count} warning" if count == 1 else f"{count} warnings"


def _scouting_rows_for_state(pool_frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, row in pool_frame.iterrows():
        player = _clean_text(row.get("player", ""))
        position = _clean_text(row.get("position", ""))
        source_type = _clean_text(row.get("source_type", "scouting"))
        if not player or not position:
            continue
        rows.append(
            {
                "overall_rank": index + 1,
                "asset_id": f"scouting:{_slug(source_type)}:{_slug(player)}:{_slug(position)}",
                "player": player,
                "position": position,
                "nfl_team": _clean_text(row.get("nfl_team", "")),
                "asset_type": source_type,
                "asset_lifecycle": _clean_text(row.get("draftable_status", "scouting_pool")),
                "why_available": _clean_text(row.get("draftable_status", "scouting pool")),
                "draft_status": "available",
                "stats_model_value": _score_value(row),
                "model_value": _score_value(row),
                "market_value": 0.0,
                "market_edge": 0.0,
                "confidence": 75.0,
                "warning": _warning_summary(row.get("warning_flags", "")),
                "recommended_range": "Scouting Only",
            }
        )
    return rows


def _mock_options() -> dict[str, str]:
    return {
        f"{row.mock_name} ({row.drafted_count} picks, {row.created_at})": str(row.path)
        for row in list_mock_drafts()
    }


def _mark_dirty(dirty_key_value: str) -> None:
    st.session_state[dirty_key_value] = True


def _mark_clean(dirty_key_value: str) -> None:
    st.session_state[dirty_key_value] = False


def _render_status_cards(
    *,
    contract,
    state: DraftBoardState,
    scouting_rows: int,
) -> None:
    card_rows = (
        ("Draft Shape", f"{DRAFT_ROUNDS} rounds x {DRAFT_TEAMS} teams"),
        ("Total Picks", str(DRAFT_TOTAL_PICKS)),
        ("My Picks", ", ".join(OWNED_PICK_LABELS)),
        ("Scouting Pool", f"{scouting_rows} rows" if scouting_rows else "Missing"),
        ("Legal Pool", "Pending"),
        ("Draft State", "Session/local mock"),
    )
    st.markdown(_source_card_grid(card_rows), unsafe_allow_html=True)
    if contract.available_pool_warnings:
        st.caption(
            "Active legal pool is still pending required source files; scouting rows "
            "below are mock/scouting mode only."
        )
        with st.expander("Legal pool source warnings", expanded=False):
            for warning in contract.available_pool_warnings:
                st.write(warning)
    progress = state_progress(state)
    st.caption(
        f"Current: {progress['current']} | Drafted: {progress['drafted']} of "
        f"{progress['total']} | Available scouting rows: {progress['available']}"
    )


def _source_card_grid(rows: tuple[tuple[str, str], ...]) -> str:
    cards = "".join(
        (
            '<div class="source-card">'
            f'<div class="source-card-label">{html.escape(label)}</div>'
            f'<div class="source-card-value">{html.escape(value)}</div>'
            "</div>"
        )
        for label, value in rows
    )
    return f'<div class="source-card-grid">{cards}</div>'


def state_progress(state: DraftBoardState) -> dict[str, object]:
    current = current_draft_pick(state)
    return {
        "current": current.pick_label if current else "Done",
        "drafted": len(state.drafted_players),
        "available": len(available_players_after_picks(state)),
        "total": len(state.picks),
    }


def _render_save_load_controls(
    *,
    state: DraftBoardState,
    session_key: str,
    selected_key: str,
    dirty_key_value: str,
    active_data_pack: str,
) -> None:
    with st.expander("Save / Load Mock", expanded=False):
        save_cols = st.columns([2, 1])
        with save_cols[0]:
            mock_name = st.text_input("Mock Name", value="Untitled Mock")
        with save_cols[1]:
            if st.button("Save Mock", use_container_width=True):
                try:
                    path = save_mock_draft(
                        state,
                        mock_name=mock_name,
                        active_data_pack=active_data_pack,
                    )
                    _mark_clean(dirty_key_value)
                    st.success(f"Saved mock: {path}")
                except MockDraftValidationError as exc:
                    st.error(str(exc))

        mock_options = _mock_options()
        selected_mock_label = st.selectbox(
            "Saved Mock",
            list(mock_options),
            index=0 if mock_options else None,
            placeholder="No saved mocks",
        )
        selected_mock_path = mock_options.get(str(selected_mock_label))
        action_cols = st.columns(4)
        with action_cols[0]:
            if st.button("Load Mock", disabled=not selected_mock_path, use_container_width=True):
                try:
                    st.session_state[session_key] = load_mock_draft(
                        selected_mock_path or "",
                        base_state=state,
                    )
                    _mark_clean(dirty_key_value)
                    st.session_state[selected_key] = st.session_state[session_key].current_pick
                    st.rerun()
                except MockDraftValidationError as exc:
                    st.error(str(exc))
        with action_cols[1]:
            duplicate_name = f"{mock_name} Copy"
            if st.button(
                "Duplicate Mock",
                disabled=not selected_mock_path,
                use_container_width=True,
            ):
                try:
                    duplicate_mock_draft(
                        selected_mock_path or "",
                        new_mock_name=duplicate_name,
                    )
                    st.rerun()
                except MockDraftValidationError as exc:
                    st.error(str(exc))
        with action_cols[2]:
            if st.button("Clear Mock", disabled=not selected_mock_path, use_container_width=True):
                clear_mock_draft(selected_mock_path or "")
                st.rerun()
        with action_cols[3]:
            st.caption("Saved mocks are local JSON files. Active data packs are not modified.")


def _render_draft_grid(
    *,
    state: DraftBoardState,
    selected_pick: int | None,
    selected_key: str,
) -> None:
    st.subheader("Draft Grid")
    rows = draft_pick_grid_rows(state, selected_pick=selected_pick)
    grid_frame = pd.DataFrame(rows)
    if not grid_frame.empty:
        st.dataframe(
            grid_frame[
                ["pick", "overall_pick", "owner", "my_pick", "current", "player", "pos", "status"]
            ],
            use_container_width=True,
            hide_index=True,
        )

    pick_choices = {
        f"{row['pick']} | {row['owner']} | {row['status']}": int(row["overall_pick"])
        for row in rows
    }
    if pick_choices:
        current_index = 0
        if selected_pick in pick_choices.values():
            current_index = list(pick_choices.values()).index(selected_pick)
        selected_label = st.selectbox(
            "Selected Pick",
            list(pick_choices),
            index=current_index,
        )
        st.session_state[selected_key] = pick_choices[str(selected_label)]


def _render_pick_assignment(
    *,
    state: DraftBoardState,
    session_key: str,
    selected_key: str,
    dirty_key_value: str,
) -> DraftBoardState:
    selected_pick = selected_pick_number(state, selected_key)
    guardrail = pick_guardrail_status(state, selected_pick)
    current = current_draft_pick(state)
    selected_drafted_player = drafted_player_at_pick(state, selected_pick)

    st.subheader("Pick Controls")
    status_cols = st.columns(3)
    status_cols[0].metric("Current Pick", current.pick_label if current else "Done")
    status_cols[1].metric("Current Owner", current.current_owner if current else MISSING)
    status_cols[2].metric("My Turn", "Yes" if is_my_turn(state) else "No")
    if guardrail.warning:
        st.warning(guardrail.warning)
    if selected_drafted_player is not None:
        st.caption(
            "Current selection: "
            f"{selected_drafted_player.player} ({selected_drafted_player.position}). "
            "Choose another available player to replace this pick."
        )
    else:
        st.caption("Replace Pick appears after selecting a pick that already has a drafted player.")

    search = st.text_input(
        "Player Search",
        placeholder="Type player, position, source type, or team",
    )
    matched_players = search_available_players(state, search, limit=35)
    choices = {
        (
            f"{row.player} ({row.position}, {row.asset_type}, {row.asset_lifecycle}) "
            f"- Score {row.stats_model_value:.1f}"
        ): row.asset_id
        for row in matched_players
    }
    selected_label = st.selectbox(
        "Available Player",
        list(choices),
        index=0 if choices else None,
        placeholder="No matching players",
    )
    action_label = "Replace Pick" if guardrail.edit_mode else "Mark Drafted"
    if st.button(
        action_label,
        disabled=not choices or selected_pick is None,
        use_container_width=True,
    ):
        selected_asset = choices[str(selected_label)]
        try:
            if guardrail.edit_mode and selected_pick is not None:
                next_state = replace_drafted_player_at_pick(
                    state,
                    selected_asset,
                    overall_pick=selected_pick,
                )
            else:
                next_state = mark_player_drafted(
                    state,
                    selected_asset,
                    overall_pick=selected_pick,
                )
            st.session_state[session_key] = next_state
            st.session_state[selected_key] = next_state.current_pick
            _mark_dirty(dirty_key_value)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    undo_cols = st.columns(3)
    with undo_cols[0]:
        if st.button("Undo Last", disabled=not state.drafted_players, use_container_width=True):
            next_state = undo_pick(state)
            st.session_state[session_key] = next_state
            st.session_state[selected_key] = next_state.current_pick
            _mark_dirty(dirty_key_value)
            st.rerun()
    with undo_cols[1]:
        confirm = st.checkbox(
            "Confirm reset",
            key=reset_confirm_key("live-draft-room", (0, 0, 0, 0)),
            disabled=not state.drafted_players,
        )
        if st.button(
            "Reset Mock",
            disabled=not state.drafted_players or not confirm,
            use_container_width=True,
        ):
            next_state = reset_mock(state)
            st.session_state[session_key] = next_state
            st.session_state[selected_key] = next_state.current_pick
            _mark_dirty(dirty_key_value)
            st.rerun()
    with undo_cols[2]:
        st.caption(
            "Undo and reset unlock after a pick is marked. Draft state is "
            "session/local mock state only."
        )
    return state


def _pick_label_for_overall(state: DraftBoardState, overall_pick: int | None) -> str:
    if overall_pick is None:
        return MISSING
    for pick in state.picks:
        if pick.overall_pick == overall_pick:
            return pick.pick_label
    return MISSING


def _render_live_player_detail(
    frame: pd.DataFrame,
    *,
    state: DraftBoardState,
    selected_pick: int | None,
    hide_drafted: bool,
) -> None:
    if frame.empty:
        return
    detail_frame = frame.head(250).copy()
    choices = {
        (
            f"{row.player} | {row.position} | {row.asset_type} | "
            f"{row.draft_status}"
        ): index
        for index, row in detail_frame.iterrows()
    }
    selected_label = st.selectbox(
        "Selected player detail",
        list(choices),
        index=0 if choices else None,
        help=(
            "Read-only player context from the mock/scouting board. Viewing this card "
            "does not mark or replace picks."
        ),
    )
    if not choices:
        return
    detail_row = detail_frame.loc[choices[str(selected_label)]].to_dict()
    current = current_draft_pick(state)
    warning_text = _clean_text(detail_row.get("warning"))
    if warning_text:
        detail_row["data_needed"] = f"Review scouting warning summary: {warning_text}"
    detail_row.update(
        {
            "source_type": detail_row.get("asset_type", ""),
            "draftable_status": detail_row.get("asset_lifecycle", ""),
            "drafted_status": detail_row.get("draft_status", ""),
            "current_pick_context": current.pick_label if current else "Done",
            "selected_pick_context": _pick_label_for_overall(state, selected_pick),
            "legal_pool_status": "Legal Pool Pending",
            "scouting_pool_status": "Mock/scouting mode",
            "hide_drafted_status": (
                "Drafted rows hidden" if hide_drafted else "Drafted rows visible"
            ),
            "mock_state_context": "Session/local mock state only; source data is not mutated.",
            "best_remaining_context": "Selected from Best Remaining / Scouting Pool.",
            "trust_status": "Source/context only",
            "source_path": demo_source_label(SCOUTING_PREP_POOL_ROWS),
            "source_column": "stats_model_value",
            "allowed_use": "mock_live_tracking_and_scouting_context_only",
            "blocked_use": "do_not_use_as_private_value_or_final_draft_recommendation",
        }
    )
    payload = build_player_detail_card_payload(detail_row, context="live_draft_room")
    with st.expander(f"Selected Player Detail: {payload.player}", expanded=False):
        render_player_detail_card(payload)


def _render_best_remaining(state: DraftBoardState, *, selected_pick: int | None) -> None:
    st.subheader("Best Remaining / Scouting Pool")
    filter_cols = st.columns(3)
    with filter_cols[0]:
        source_filter = st.selectbox("Source Type", SOURCE_TYPE_OPTIONS)
    with filter_cols[1]:
        position_filter = st.selectbox("Position Filter", POSITION_OPTIONS)
    with filter_cols[2]:
        hide_drafted = st.toggle("Hide Drafted", value=True)

    rows = _all_player_rows(state)
    if not rows:
        st.info("No scouting rows are loaded for mock/live tracking.")
        return
    frame = pd.DataFrame(rows)
    if hide_drafted:
        frame = frame[frame["draft_status"] != "drafted"]
    if source_filter == "Rookie":
        frame = frame[frame["asset_type"].astype(str).str.lower() == "rookie"]
    elif source_filter == "Free Agent / Veteran Preview":
        frame = frame[frame["asset_type"].astype(str).str.lower() == "free_agent"]
    if position_filter == "FLEX":
        frame = frame[frame["position"].astype(str).str.upper().isin(FLEX_POSITIONS)]
        st.caption("FLEX means RB + WR + TE only. QB is excluded.")
    elif position_filter != "All":
        frame = frame[frame["position"].astype(str).str.upper() == position_filter]
    st.dataframe(
        frame[
            [
                "player",
                "position",
                "nfl_team",
                "asset_type",
                "asset_lifecycle",
                "stats_model_value",
                "draft_status",
                "drafted_pick",
                "warning",
            ]
        ].head(200),
        use_container_width=True,
        hide_index=True,
    )
    _render_live_player_detail(
        frame,
        state=state,
        selected_pick=selected_pick,
        hide_drafted=hide_drafted,
    )

    position_rows = best_remaining_by_position(state, limit_per_position=3)
    if position_rows:
        st.caption("Best remaining by position")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "position": row.position,
                        "player": row.player,
                        "source_type": row.asset_type,
                        "score": row.stats_model_value,
                        "confidence": row.confidence,
                    }
                    for row in position_rows
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def _all_player_rows(state: DraftBoardState) -> list[dict[str, object]]:
    rows = [
        {
            "asset_id": row.asset_id,
            "player": row.player,
            "position": row.position,
            "nfl_team": row.nfl_team,
            "asset_type": row.asset_type,
            "asset_lifecycle": row.asset_lifecycle,
            "stats_model_value": row.stats_model_value,
            "confidence": row.confidence,
            "warning": row.warning,
            "draft_status": "available",
            "drafted_pick": "",
        }
        for row in state.available_players
    ]
    rows.extend(
        {
            "asset_id": row.asset_id,
            "player": row.player,
            "position": row.position,
            "nfl_team": row.nfl_team,
            "asset_type": row.asset_type,
            "asset_lifecycle": row.asset_lifecycle,
            "stats_model_value": row.stats_model_value,
            "confidence": row.confidence,
            "warning": "",
            "draft_status": "drafted",
            "drafted_pick": row.pick.pick_label,
        }
        for row in state.drafted_players
    )
    return sorted(
        rows,
        key=lambda row: (
            str(row["draft_status"]) == "drafted",
            -float(row["stats_model_value"] or 0),
            str(row["player"]),
        ),
    )


def _render_my_picks_and_recent(state: DraftBoardState) -> None:
    cols = st.columns(2)
    with cols[0]:
        st.subheader("My Upcoming Picks")
        my_rows = [
            {
                "pick": pick.pick_label,
                "overall": pick.overall_pick,
                "owner": pick.current_owner,
                "status": "current"
                if pick.overall_pick == state.current_pick
                else "open"
                if drafted_player_at_pick(state, pick.overall_pick) is None
                else "filled",
            }
            for pick in state.picks
            if pick.is_my_pick
        ]
        st.dataframe(pd.DataFrame(my_rows), use_container_width=True, hide_index=True)
    with cols[1]:
        st.subheader("Recent Picks")
        recent = recent_drafted_players(state, limit=8)
        if not recent:
            st.info("No picks marked yet.")
        else:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "pick": row.pick_label,
                            "owner": row.owner,
                            "player": row.player,
                            "pos": row.position,
                            "source": row.asset_type,
                        }
                        for row in recent
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )


def _render_downloads_and_details(state: DraftBoardState, session_key: str) -> None:
    with st.expander("Advanced Session Details", expanded=False):
        st.caption("Session/local mock state only. These exports do not change source data packs.")
        export_cols = st.columns(2)
        with export_cols[0]:
            st.download_button(
                "Download Draft State CSV",
                data=pd.DataFrame(draft_board_export_rows(state)).to_csv(index=False),
                file_name="live_draft_room_state.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with export_cols[1]:
            st.download_button(
                "Download Remaining Pool CSV",
                data=pd.DataFrame(remaining_pool_export_rows(state)).to_csv(index=False),
                file_name="live_draft_room_remaining_pool.csv",
                mime="text/csv",
                use_container_width=True,
            )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "context": "local mock state",
                        "value": "Session key hidden for demo",
                        "safety": "Never writes to active data packs.",
                    },
                    {
                        "context": "scouting pool",
                        "value": demo_source_label(SCOUTING_PREP_POOL_ROWS),
                        "safety": "Read-only input for session state.",
                    },
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def main() -> None:
    settings = get_settings()
    active_data_pack = render_data_pack_selector(settings)
    active_fingerprint = path_fingerprint(active_data_pack)
    _render_css()

    contract = _load_contract(str(active_data_pack), active_fingerprint)
    scouting_frame = _load_scouting_pool(
        str(SCOUTING_PREP_POOL_ROWS),
        path_fingerprint(SCOUTING_PREP_POOL_ROWS),
    )
    scouting_rows = _scouting_rows_for_state(scouting_frame)

    live_state_scope = f"live-draft-room::{active_data_pack}"
    session_key = draft_state_key(live_state_scope, active_fingerprint)
    selected_key = selected_pick_key(live_state_scope, active_fingerprint)
    dirty_key_value = dirty_key(live_state_scope, active_fingerprint)
    state = state_from_session(
        session_key,
        contract_rows=contract.pick_grid_rows,
        ranking_rows=scouting_rows,
    )
    selected_pick = selected_pick_number(state, selected_key)

    st.title("Live Draft Room")
    st.caption("Mock/live draft tracking. Draft state is separate from source data.")
    st.markdown(
        """
        <div class="live-draft-banner">
          <strong>Legal draft pool pending:</strong> dropped/released veteran data has
          not been supplied yet. Use this as mock/scouting draft mode until the final
          legal pool is loaded.
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_status_cards(contract=contract, state=state, scouting_rows=len(scouting_rows))
    if st.session_state.get(dirty_key_value):
        st.warning("Unsaved mock changes. Save this mock before leaving or refreshing.")

    _render_save_load_controls(
        state=state,
        session_key=session_key,
        selected_key=selected_key,
        dirty_key_value=dirty_key_value,
        active_data_pack=str(active_data_pack),
    )

    top_cols = st.columns([1.25, 1])
    with top_cols[0]:
        _render_draft_grid(state=state, selected_pick=selected_pick, selected_key=selected_key)
    with top_cols[1]:
        _render_pick_assignment(
            state=state,
            session_key=session_key,
            selected_key=selected_key,
            dirty_key_value=dirty_key_value,
        )

    _render_best_remaining(st.session_state[session_key], selected_pick=selected_pick)
    _render_my_picks_and_recent(st.session_state[session_key])
    _render_downloads_and_details(st.session_state[session_key], session_key)


main()
