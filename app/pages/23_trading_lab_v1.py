from __future__ import annotations

# ruff: noqa: E402
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.decision_trust_strip import render_decision_trust_strips
from app.components.draft_day_v1 import (
    render_lane_status_table,
    render_source_of_truth_badge,
    render_yellow_hold,
)
from app.components.post_release_status import render_save_status, render_source_freshness
from app.components.ui_framework import page_header
from src.services.decision_trust_strip_service import build_decision_trust_strip
from src.services.draft_day_app_v1_service import (
    display_lane_prop_frame,
    load_dynasty_rankings,
    load_frozen_board,
    load_lane_prop_file,
    resolve_dynasty_rankings_path,
)
from src.services.draft_day_trade_lab_service import (
    NOT_ENOUGH_INFORMATION,
    build_registry_trade_item_lookup,
    build_trade_narrative,
    clear_trade_state,
    copy_trade_state,
    cross_side_duplicates,
    empty_trade_state,
    replace_trade_state,
    source_context_counts,
    trade_asset_ids_by_side,
    trade_item_rows,
    validate_trade_player_universe,
)
from src.services.governed_asset_registry_service import (
    finished_v1_coverage_counts,
    load_governed_asset_registry,
)
from src.services.outcome_v3_display_service import load_outcome_v3_display
from src.services.owner_asset_evidence_service import compose_owner_asset_evidence
from src.services.personal_workspace_service import (
    WorkspaceValidationError,
    load_store,
    save_scenario,
)
from src.services.post_release_usability_service import (
    governed_source_freshness,
    initial_save_status,
    perform_workspace_write,
)
from src.services.trade_brief_export_service import (
    TradeBriefValidationError,
    build_trade_brief,
)
from src.services.trading_lab_nflverse_context_service import (
    display_nflverse_context_rows,
    load_trading_lab_nflverse_context_index,
    nflverse_context_detail_rows,
    nflverse_context_summary_rows,
    nflverse_manual_row_context_rows,
    nflverse_missing_evidence_rows,
)
from src.services.unified_research_preview_service import (
    load_unified_research_preview,
)

SESSION_KEY = "draft_day_v1_trading_lab_builder"
SESSION_VERSION_KEY = "draft_day_v1_trading_lab_builder_version"
SESSION_VERSION = 2
GIVE_WIDGET_KEY = "trading_lab_current_you_give"
RECEIVE_WIDGET_KEY = "trading_lab_current_you_receive"
TRADE_AWAY_PLANNER_KEY = "draft_day_v1_trade_away_planner_rows"
TRADE_FOR_PLANNER_KEY = "draft_day_v1_trade_for_planner_rows"
TRADE_AWAY_CHECKLIST_KEY = "draft_day_v1_trade_away_checklist"
TRADE_FOR_CHECKLIST_KEY = "draft_day_v1_trade_for_checklist"
MANUAL_PLANNER_WARNING = (
    "Manual planning only. No trade valuation, market valuation, pick valuation, model "
    "score, or automatic recommendation is calculated."
)
WORKFLOW_STATUS_OPTIONS = (
    "Idea",
    "Drafted",
    "Sent",
    "Countered",
    "Rejected",
    "Accepted",
    "Archived",
    "Needs info",
)
PLANNER_COLUMNS = (
    "scenario_name",
    "counterparty_or_team",
    "send_assets",
    "receive_assets",
    "anchor_pick_or_asset",
    "nwr_player_id",
    "status",
    "open_questions",
    "manual_notes",
    "follow_up",
    "last_updated",
)

frozen_bundle = load_frozen_board()
dynasty_bundle = load_dynasty_rankings()
trade_frame, trade_path = load_lane_prop_file("trading_lab", "trade_helper_context.csv")
pick_frame, pick_path = load_lane_prop_file("trading_lab", "pick_context.csv")
tier_frame, tier_path = load_lane_prop_file("trading_lab", "trade_tier_values.csv")
mock_pick_frame, mock_pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")

page_header(
    "Analyze Trade",
    eyebrow="Draft-Day App V1",
    description=(
        "Build the two sides, understand what each side offers, then save or export the exact "
        "current trade."
    ),
    status_items=(
        ("Manual descriptive analysis", "review"),
        ("Exact governed assets", "safe"),
    ),
)
render_source_freshness(governed_source_freshness())
st.info(
    "NWR compares the evidence on each side but does not automatically accept or reject trades."
)
player_universe_errors = (
    validate_trade_player_universe(dynasty_bundle.frame) if dynasty_bundle.loaded else ()
)
if dynasty_bundle.loaded and not player_universe_errors:
    _coverage = finished_v1_coverage_counts(dynasty_bundle.frame)
    st.caption(
        f"{_coverage['ranked_skill_players']} production-ranked players · "
        f"{_coverage['unranked_kickers']} structural kickers outside ranking coverage"
    )
else:
    st.error(
        "Trading Lab requires the approved hash-validated 240-player production universe. "
        "The frozen draft-board checkpoint will not be substituted as the player selector."
    )
    for warning in dynasty_bundle.warnings:
        st.warning(warning)
    for error in dynasty_bundle.errors:
        st.error(error)
    for error in player_universe_errors:
        st.error(error)
    st.stop()

for warning in dynasty_bundle.warnings:
    st.warning(warning)

if st.session_state.get(SESSION_VERSION_KEY) != SESSION_VERSION:
    st.session_state[SESSION_KEY] = empty_trade_state()
    st.session_state[SESSION_VERSION_KEY] = SESSION_VERSION
    st.session_state.pop(GIVE_WIDGET_KEY, None)
    st.session_state.pop(RECEIVE_WIDGET_KEY, None)
elif SESSION_KEY not in st.session_state:
    st.session_state[SESSION_KEY] = empty_trade_state()
st.session_state[SESSION_KEY] = copy_trade_state(st.session_state[SESSION_KEY])

current_board_path, _current_label, _current_warnings = resolve_dynasty_rankings_path()
governed = load_governed_asset_registry(
    repo_root=REPO_ROOT,
    current_board_path=current_board_path,
    expected_current_hash=dynasty_bundle.source_hash or "",
)
if governed.errors:
    for registry_error in governed.errors:
        st.error(f"Governed asset registry: {registry_error}")
    st.stop()
try:
    _research_bundle = load_unified_research_preview()
    _research_frame = _research_bundle.board
except (OSError, ValueError):
    _research_bundle = None
    _research_frame = pd.DataFrame()
_outcome_bundle = load_outcome_v3_display()
owner_evidence = compose_owner_asset_evidence(
    governed.rows,
    dynasty_frame=dynasty_bundle.frame,
    research_frame=_research_frame,
    outcome_frame=_outcome_bundle.frame,
)
governed_by_id = owner_evidence.by_id
lookup = build_registry_trade_item_lookup(owner_evidence.rows)
counts = source_context_counts(dynasty_bundle.frame, trade_frame, pick_frame, tier_frame)
nflverse_context = load_trading_lab_nflverse_context_index()

if trade_path is None or trade_frame.empty:
    render_yellow_hold(
        "Trading Lab helper context is missing; review is current-player context only."
    )


def _render_source_metrics(counts: dict[str, int]) -> None:
    cols = st.columns(4)
    cols[0].metric("Governed selector assets", len(governed.rows))
    cols[1].metric("Trade helper rows", counts["trade_helper_rows"])
    cols[2].metric("Legacy pick helper rows", counts["pick_context_rows"])
    cols[3].metric("Tier context rows", counts["tier_context_rows"])
    st.caption(
        "Selectors come from the governed registry. Finished V1, Rookie Review, blocked assets, "
        "2026 picks, and future picks keep separate authority labels and cannot override "
        "`nwr_rank`, `final_board_rank`, create hidden sort fields, or produce package values."
    )


def _asset_option_label(item_key: str) -> str:
    row = lookup[item_key]
    return (
        f"{row.get('player')} · {row.get('registry_asset_type')} · "
        f"{str(row.get('data_status', '')).split(';', maxsplit=1)[0]}"
    )


def _clear_trade_builder() -> None:
    st.session_state[SESSION_KEY] = clear_trade_state()
    st.session_state[GIVE_WIDGET_KEY] = []
    st.session_state[RECEIVE_WIDGET_KEY] = []


def _render_builder(lookup: dict[str, dict[str, object]]) -> None:
    st.markdown("## Build the trade")
    options = sorted(lookup, key=lambda key: (str(lookup[key].get("player")), key))
    analyzed = copy_trade_state(st.session_state[SESSION_KEY])
    give_defaults = (
        {}
        if GIVE_WIDGET_KEY in st.session_state
        else {"default": [key for key in analyzed["give"] if key in lookup]}
    )
    receive_defaults = (
        {}
        if RECEIVE_WIDGET_KEY in st.session_state
        else {"default": [key for key in analyzed["get"] if key in lookup]}
    )
    with st.form("current-trade-builder"):
        give_col, receive_col = st.columns(2)
        give = give_col.multiselect(
            "You give",
            options,
            format_func=_asset_option_label,
            key=GIVE_WIDGET_KEY,
            placeholder="Search and add players or picks",
            **give_defaults,
        )
        receive = receive_col.multiselect(
            "You receive",
            options,
            format_func=_asset_option_label,
            key=RECEIVE_WIDGET_KEY,
            placeholder="Search and add players or picks",
            **receive_defaults,
        )
        analyze = st.form_submit_button("Analyze Trade", type="primary")
    if analyze:
        duplicates = cross_side_duplicates(give, receive)
        if duplicates:
            names = ", ".join(str(lookup[key].get("player")) for key in duplicates)
            st.error(f"An asset cannot appear on both sides: {names}.")
        else:
            st.session_state[SESSION_KEY] = replace_trade_state(give, receive)
            st.rerun()
    st.button(
        "Clear Trade",
        key="trading_lab_clear_trade",
        on_click=_clear_trade_builder,
    )


def _render_asset_card(row: dict[str, object], personal: dict[str, dict[str, object]]) -> None:
    asset_id = str(row.get("asset_id", ""))
    with st.container(border=True):
        st.markdown(f"**{row.get('player')}** · {row.get('registry_asset_type')}")
        details: list[str] = []
        if str(row.get("dynasty_rank", "")).strip():
            details.append(f"Dynasty Rank {row.get('dynasty_rank')}")
            if str(row.get("position_rank", "")).strip():
                details.append(str(row.get("position_rank")))
            if str(row.get("final_tier", "")).strip():
                details.append(str(row.get("final_tier")))
            if str(row.get("age", "")).strip():
                details.append(f"Age {row.get('age')}")
        elif str(row.get("final_board_rank", "")).strip():
            details.append(f"Rookie Review Rank {row.get('final_board_rank')}")
            if str(row.get("research_rank", "")).strip():
                details.append(f"Research Rank {row.get('research_rank')}")
            details.append(str(row.get("research_status") or "Review-only evidence"))
        elif str(row.get("asset_type")) == "Pick context":
            details.append(str(row.get("pick_window_note") or "Governed pick context"))
        st.write(" · ".join(details) if details else "Source-separated context only")
        if row.get("market_dp_value") or row.get("market_dp_rank"):
            st.caption(
                f"Market: DP Value {row.get('market_dp_value') or '—'} · "
                f"DP Rank {row.get('market_dp_rank') or '—'} · {row.get('market_status')}"
            )
        for signal in tuple(row.get("outcome_signals", ()))[:2]:
            st.caption(f"Outcome: {signal}")
        caveats = tuple(row.get("owner_caveats", ()))
        if caveats:
            major_caveat = next(
                (
                    caveat
                    for caveat in caveats
                    if "age-related" in caveat.casefold() or "age-window" in caveat.casefold()
                ),
                caveats[0],
            )
            st.caption(f"Caveat: {major_caveat}")
        overlay = personal.get(asset_id, {})
        owner_bits = [
            str(overlay.get("my_tier") or ""),
            ", ".join(overlay.get("tags", [])),
            str(overlay.get("notes") or ""),
        ]
        owner_bits = [value for value in owner_bits if value]
        if owner_bits:
            st.caption("Personal: " + " · ".join(owner_bits))


def _render_trade_at_a_glance(
    lookup: dict[str, dict[str, object]],
    personal: dict[str, dict[str, object]],
) -> None:
    rows = trade_item_rows(st.session_state[SESSION_KEY], lookup)
    st.markdown("## Trade at a glance")
    if rows.empty:
        st.info("Choose the assets on both sides, then select Analyze Trade.")
        return
    give_col, receive_col = st.columns(2)
    for container, side in ((give_col, "You give"), (receive_col, "You receive")):
        with container:
            st.markdown(f"### {side}")
            side_rows = rows.loc[rows["side"].eq(side)].to_dict("records")
            if not side_rows:
                st.warning("No assets selected.")
            for row in side_rows:
                _render_asset_card(row, personal)


def _render_trade_interpretation(lookup: dict[str, dict[str, object]]) -> None:
    narrative = build_trade_narrative(st.session_state[SESSION_KEY], lookup)
    st.markdown("## How the sides differ")
    if narrative.differences:
        for difference in narrative.differences:
            st.write(f"- {difference}")
    else:
        st.caption("Add at least one asset to each side.")
    st.markdown("## Bottom line")
    for sentence in narrative.bottom_line:
        st.write(sentence)


def _render_nflverse_context_panel(lookup: dict[str, dict[str, object]]) -> None:
    with st.expander("NFLVerse player context", expanded=False):
        metric_cols = st.columns(3)
        metric_cols[0].metric("Player context artifact rows", nflverse_context.artifact_row_count)
        metric_cols[1].metric("Safe display rows", nflverse_context.safe_row_count)
        metric_cols[2].metric(
            "Identity review rows",
            nflverse_context.identity_review_row_count,
        )

        rows = trade_item_rows(st.session_state[SESSION_KEY], lookup)
        if rows.empty:
            st.info("Select player assets to view display-only NFLVerse context.")
            return

        summary = display_nflverse_context_rows(
            nflverse_context_summary_rows(rows, nflverse_context)
        )
        st.markdown("**Selected asset context status**")
        st.dataframe(summary, width="stretch", hide_index=True)

        details = display_nflverse_context_rows(
            nflverse_context_detail_rows(rows, nflverse_context)
        )
        st.markdown("**Approved player context details**")
        if details.empty:
            st.info("No approved player-context details are available for the selected assets.")
        else:
            st.dataframe(details, width="stretch", hide_index=True)

        missing = display_nflverse_context_rows(
            nflverse_missing_evidence_rows(rows, nflverse_context)
        )
        st.markdown("**Missing evidence / deferred context**")
        st.caption(
            "Missing is not zero, neutral, safe, clean, healthy, no-role, no-usage, "
            "or favorable. Schedule context appears only for approved safe rows; missing or "
            "gated schedule data remains Not enough information."
        )
        st.dataframe(missing, width="stretch", hide_index=True)


def _render_diagnostics() -> None:
    with st.expander("Source diagnostics (Advanced)", expanded=False):
        _render_source_metrics(counts)
        render_source_of_truth_badge(frozen_bundle)
        render_lane_status_table()
        if trade_path and not trade_frame.empty:
            st.caption(f"Display-only trade helper context: {trade_path}")
            st.dataframe(
                display_lane_prop_frame(trade_frame.head(20)),
                width="stretch",
                hide_index=True,
            )
        if pick_path and not pick_frame.empty:
            st.caption(f"Display-only pick context: {pick_path}")
            st.dataframe(
                display_lane_prop_frame(pick_frame.head(20)),
                width="stretch",
                hide_index=True,
            )
        if mock_pick_path and not mock_pick_frame.empty:
            st.caption(f"Draft pick-order context: {mock_pick_path}")
            st.dataframe(
                display_lane_prop_frame(mock_pick_frame.head(20)),
                width="stretch",
                hide_index=True,
            )
        if tier_path and not tier_frame.empty:
            st.caption(f"Display-only tier context: {tier_path}")
            st.dataframe(
                display_lane_prop_frame(tier_frame),
                width="stretch",
                hide_index=True,
            )


def _render_trade_away_pick_planner() -> None:
    st.subheader("Trade Away Pick Planner")
    st.warning(MANUAL_PLANNER_WARNING)
    st.caption(
        "Use this when a pick like 1.05 feels uncomfortable. The page helps you write down "
        "manual scenarios and questions; it does not find offers, appraise picks, or update "
        "draft state."
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
    rows = _render_manual_planner_editor(
        key=TRADE_AWAY_PLANNER_KEY,
        anchor=selected_pick,
        default_scenario="Trade away pick idea",
        default_send=selected_pick,
        default_receive="Manual entry",
    )
    _render_manual_planner_nflverse_context(rows)
    checklist = _render_manual_checklist(
        key=TRADE_AWAY_CHECKLIST_KEY,
        anchor=selected_pick,
    )
    memo = _manual_memo_text(
        "Trade Away Pick Planner",
        selected_pick,
        rows,
        checklist,
    )
    _download_text(
        "Download manual trade-away memo",
        memo,
        "nwr_trade_away_pick_planner_manual_memo.md",
    )


def _render_trade_for_pick_planner() -> None:
    st.subheader("Trade For Pick Planner")
    st.warning(MANUAL_PLANNER_WARNING)
    st.caption(
        "Use this when a player is falling and you want to plan a conversation for a pick like "
        "1.08. This is a manual workspace, not an offer generator."
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
    rows = _render_manual_planner_editor(
        key=TRADE_FOR_PLANNER_KEY,
        anchor=target_pick,
        default_scenario="Trade for pick idea",
        default_send="Manual entry",
        default_receive=target_pick,
    )
    _render_manual_planner_nflverse_context(rows)
    checklist = _render_manual_checklist(
        key=TRADE_FOR_CHECKLIST_KEY,
        anchor=target_pick,
    )
    memo = _manual_memo_text(
        "Trade For Pick Planner",
        target_pick,
        rows,
        checklist,
    )
    _download_text(
        "Download manual trade-for memo",
        memo,
        "nwr_trade_for_pick_planner_manual_memo.md",
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


def _render_manual_planner_editor(
    *,
    key: str,
    anchor: str,
    default_scenario: str,
    default_send: str,
    default_receive: str,
) -> list[dict[str, str]]:
    st.caption(
        "Structured manual planner rows. Add or edit rows by hand; rows are not generated, "
        "ranked, priced, or sorted by the app."
    )
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(
            [
                {
                    "scenario_name": default_scenario,
                    "counterparty_or_team": "Manual entry",
                    "send_assets": default_send,
                    "receive_assets": default_receive,
                    "anchor_pick_or_asset": anchor,
                    "nwr_player_id": "",
                    "status": "Idea",
                    "open_questions": "What information is missing?",
                    "manual_notes": "",
                    "follow_up": "",
                    "last_updated": "",
                }
            ],
            columns=list(PLANNER_COLUMNS),
        )
    frame = _planner_frame(st.session_state[key], anchor)
    edited = st.data_editor(
        frame,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key=f"{key}_editor",
        column_config={
            "status": st.column_config.SelectboxColumn(
                "status",
                options=list(WORKFLOW_STATUS_OPTIONS),
                required=True,
            )
        },
    )
    st.session_state[key] = _planner_frame(edited, anchor)
    rows = _manual_planner_rows_from_frame(st.session_state[key])
    if rows:
        _download_rows(
            "Download manual planner rows CSV",
            rows,
            f"{key}.csv",
        )
    else:
        st.info("Add manual rows to organize options without scoring or pricing.")
    return rows


def _render_manual_planner_nflverse_context(rows: list[dict[str, str]]) -> None:
    with st.expander("Manual row NFLVerse context / display-only", expanded=False):
        st.caption(
            "Enter an approved NWR Player ID on a manual row to show factual player context. "
            "Display-only context | Manual review only | No valuation calculated | "
            "No automatic recommendation."
        )
        context_rows = display_nflverse_context_rows(
            nflverse_manual_row_context_rows(rows, nflverse_context)
        )
        if context_rows.empty:
            st.info(
                "No approved NWR Player ID is present on these manual rows. Pick assets remain "
                "raw labels only."
            )
        else:
            st.dataframe(context_rows, width="stretch", hide_index=True)


def _render_manual_checklist(*, key: str, anchor: str) -> list[dict[str, str]]:
    st.caption(
        "Editable manual checklist. Completion changes only your notes; it does not change "
        "status into advice, sorting, or a package outcome."
    )
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(_default_checklist_rows(anchor))
    frame = _checklist_frame(st.session_state[key], anchor)
    edited = st.data_editor(
        frame,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key=f"{key}_editor",
        column_config={
            "status": st.column_config.SelectboxColumn(
                "status",
                options=["Not started", "In progress", "Done", "Needs info"],
                required=True,
            )
        },
    )
    st.session_state[key] = _checklist_frame(edited, anchor)
    rows = _manual_planner_rows_from_frame(st.session_state[key])
    _download_rows("Download manual checklist CSV", rows, f"{key}.csv")
    return rows


def _planner_frame(value: object, anchor: str) -> pd.DataFrame:
    frame = value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    for column in PLANNER_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame.loc[:, list(PLANNER_COLUMNS)].fillna("").astype(str)
    frame["anchor_pick_or_asset"] = frame["anchor_pick_or_asset"].replace("", anchor)
    frame["status"] = frame["status"].where(
        frame["status"].isin(WORKFLOW_STATUS_OPTIONS),
        "Idea",
    )
    return frame


def _checklist_frame(value: object, anchor: str) -> pd.DataFrame:
    columns = ("anchor_pick_or_asset", "manual_check", "status", "manual_notes")
    frame = value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame.loc[:, list(columns)].fillna("").astype(str)
    frame["anchor_pick_or_asset"] = frame["anchor_pick_or_asset"].replace("", anchor)
    return frame


def _default_checklist_rows(anchor: str) -> list[dict[str, str]]:
    prompts = [
        "What roster problem does this trade idea solve?",
        "What roster problem does this trade idea create?",
        "Which roster slots change?",
        "Which assets are picks versus players?",
        "What information is missing?",
        "What follow-up move would be required?",
        "Is this an idea, sent offer, counter, rejected, or accepted?",
        "Did the actual deal get recorded later in Draft Cockpit, if applicable?",
    ]
    return [
        {
            "anchor_pick_or_asset": anchor,
            "manual_check": prompt,
            "status": "Not started",
            "manual_notes": "",
        }
        for prompt in prompts
    ]


def _manual_planner_rows_from_frame(frame: pd.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in frame.fillna("").astype(str).to_dict("records"):
        if any(str(value).strip() for value in row.values()):
            clean = {str(key): str(value) for key, value in row.items()}
            clean["guardrail"] = MANUAL_PLANNER_WARNING
            rows.append(clean)
    return rows


def _manual_memo_text(
    planner_name: str,
    anchor: str,
    rows: list[dict[str, str]],
    checklist: list[dict[str, str]],
) -> str:
    lines = [
        f"# {planner_name}",
        "",
        MANUAL_PLANNER_WARNING,
        "",
        f"Anchor: {anchor}",
        "",
        "## Manual Planner Rows",
    ]
    if rows:
        for index, row in enumerate(rows, start=1):
            lines.extend(
                [
                    f"{index}. Scenario: {row.get('scenario_name', NOT_ENOUGH_INFORMATION)}",
                    "   - Counterparty/team: "
                    f"{row.get('counterparty_or_team', NOT_ENOUGH_INFORMATION)}",
                    f"   - Send assets: {row.get('send_assets', NOT_ENOUGH_INFORMATION)}",
                    f"   - Receive assets: {row.get('receive_assets', NOT_ENOUGH_INFORMATION)}",
                    f"   - NWR player ID: {row.get('nwr_player_id', NOT_ENOUGH_INFORMATION)}",
                    f"   - Status: {row.get('status', NOT_ENOUGH_INFORMATION)}",
                    f"   - Open questions: {row.get('open_questions', NOT_ENOUGH_INFORMATION)}",
                    f"   - Manual notes: {row.get('manual_notes', NOT_ENOUGH_INFORMATION)}",
                    f"   - Follow-up: {row.get('follow_up', NOT_ENOUGH_INFORMATION)}",
                ]
            )
    else:
        lines.append(NOT_ENOUGH_INFORMATION)
    lines.extend(["", "## Manual Checklist"])
    for row in checklist:
        lines.append(
            f"- [{row.get('status', 'Not started')}] "
            f"{row.get('manual_check', NOT_ENOUGH_INFORMATION)} "
            f"Notes: {row.get('manual_notes', '')}"
        )
    lines.extend(
        [
            "",
            "## Gated context",
            "NFLVerse player context is display-only and manual-review-only when an approved "
            "NWR Player ID is present. Missing values remain Not enough information. No "
            "valuation, automatic recommendation, pick pricing, trade pricing, side totals, "
            "grades, scores, or hidden sort fields are calculated.",
        ]
    )
    return "\n".join(lines)


def _download_rows(label: str, rows: list[dict[str, str]], filename: str) -> None:
    data = pd.DataFrame(rows).to_csv(index=False)
    st.download_button(label, data=data, file_name=filename, mime="text/csv")


def _download_text(label: str, text: str, filename: str) -> None:
    st.download_button(label, data=text, file_name=filename, mime="text/markdown")


personal_store = load_store("personal_board")
scenario_store = load_store("saved_scenarios")
personal = {row["asset_id"]: row for row in personal_store.records}
render_save_status(initial_save_status(scenario_store.status, scenario_store.updated_at_utc))

saved_trade_scenarios = [
    row for row in scenario_store.records if row.get("scenario_type") == "trading_lab"
]
if saved_trade_scenarios:
    scenario_by_label = {
        f"{row.get('title', 'Saved trade')} · {row.get('updated_at_utc', '')}": row
        for row in saved_trade_scenarios
    }
    reopen_col, action_col = st.columns([3, 1])
    reopen_label = reopen_col.selectbox("Reopen saved trade", list(scenario_by_label))
    if action_col.button("Reopen", key="trading_lab_reopen_scenario"):
        reopened = scenario_by_label[reopen_label]
        restored = empty_trade_state()
        for item in reopened.get("payload", {}).get("selected_sides", []):
            asset_id = str(item.get("asset_id", "")).strip()
            item_key = f"registry:{asset_id}"
            if item_key not in lookup:
                continue
            side = "give" if item.get("side") in {"You give", "NWR gives"} else "get"
            restored[side].append(item_key)
        restored = copy_trade_state(restored)
        st.session_state[SESSION_KEY] = restored
        st.session_state[GIVE_WIDGET_KEY] = restored["give"]
        st.session_state[RECEIVE_WIDGET_KEY] = restored["get"]
_render_builder(lookup)
selected_rows = trade_item_rows(st.session_state[SESSION_KEY], lookup)
trade_ids = trade_asset_ids_by_side(st.session_state[SESSION_KEY], lookup)
exact_ids = [*trade_ids["give"], *trade_ids["get"]]
_render_trade_at_a_glance(lookup, personal)
if not selected_rows.empty:
    _render_trade_interpretation(lookup)

with st.form("save-trading-lab-scenario"):
    scenario_title = st.text_input("Trade scenario title")
    scenario_notes = st.text_area("Your scenario notes", max_chars=20_000)
    team_window = st.selectbox(
        "Your team-window context",
        ("Contending", "Balanced", "Rebuilding", "Custom/Unspecified"),
    )
    save_trade_scenario = st.form_submit_button("Save Current Trade")
if save_trade_scenario and (not trade_ids["give"] or not trade_ids["get"]):
    st.error("Add at least one asset to each side before saving.")
elif save_trade_scenario:
    snapshot_rows = selected_rows[
        [
            column
            for column in (
                "side",
                "asset_type",
                "asset_id",
                "nwr_player_id",
                "player",
                "rank_source",
                "dynasty_rank",
                "position_rank",
                "final_board_rank",
                "data_status",
            )
            if column in selected_rows.columns
        ]
    ].to_dict("records")
    try:
        write_status = perform_workspace_write(
            lambda: save_scenario(
                {
                    "scenario_id": f"trade-{uuid4()}",
                    "scenario_type": "trading_lab",
                    "title": scenario_title or "Saved Trading Lab scenario",
                    "assets": exact_ids,
                    "source_versions": governed.source_hashes,
                    "payload": {
                        "selected_sides": snapshot_rows,
                        "notes": scenario_notes,
                        "team_window": team_window,
                        "unresolved_pick_context_visible": 0,
                    },
                },
                asset_registry={key: row["asset_type"] for key, row in governed_by_id.items()},
            ),
            observer=render_save_status,
        )
        if write_status.state == "Save failed":
            st.error("The scenario was not saved. The current trade remains available.")
    except WorkspaceValidationError as exc:
        st.error(f"Scenario blocked: {exc}")

st.markdown("## Export Current Trade")
st.caption("Markdown and JSON use the exact analyzed assets and sides shown above.")
with st.form("trade-brief-export"):
    brief_title = st.text_input("Brief title", value=scenario_title or "Trade brief")
    brief_rationale = st.text_area("Your rationale (optional)", max_chars=20_000)
    include_personal = st.checkbox("Include my tiers, tags, and notes")
    build_brief = st.form_submit_button("Prepare Current Trade Exports")
if build_brief and (not trade_ids["give"] or not trade_ids["get"]):
    st.error("Add at least one asset to each side before exporting.")
elif build_brief:
    try:
        brief = build_trade_brief(
            {
                "title": brief_title,
                "created_at_utc": datetime.now(UTC).isoformat(),
                "side_a": trade_ids["give"],
                "side_b": trade_ids["get"],
                "team_window": team_window,
                "rationale": brief_rationale,
            },
            assets=governed_by_id,
            personal=personal,
            include_personal=include_personal,
        )
        st.download_button(
            "Download Current Trade · Markdown",
            data=brief.markdown,
            file_name="nwr-current-trade.md",
            mime="text/markdown",
        )
        st.download_button(
            "Download Current Trade · JSON",
            data=brief.structured_json,
            file_name="nwr-current-trade.json",
            mime="application/json",
        )
        if brief.missing_data:
            st.warning(f"Missing data remains visible: {len(brief.missing_data)} item(s).")
    except TradeBriefValidationError as exc:
        st.error(f"Brief blocked: {exc}")

with st.expander("Advanced Data Details", expanded=False):
    st.caption("Raw receipt codes and technical source details are kept here.")
    if not selected_rows.empty:
        advanced_columns = [
            column
            for column in ("side", "asset_id", "player", "raw_caveat_codes", "data_status")
            if column in selected_rows.columns
        ]
        st.dataframe(selected_rows[advanced_columns], hide_index=True, width="stretch")
        render_decision_trust_strips(
            [
                build_decision_trust_strip(
                    row,
                    surface="Trading Lab",
                    entity_label=str(row.get("player") or "Selected asset"),
                    receipt_label="Governed selected-asset evidence",
                    receipt_available=bool(str(row.get("asset_id") or "").strip()),
                )
                for row in selected_rows.to_dict("records")
            ],
            heading="Selected-asset evidence trust",
        )

_render_nflverse_context_panel(lookup)
_render_diagnostics()

planner_tabs = st.tabs(["Trade Away Pick Planner", "Trade For Pick Planner"])
with planner_tabs[0]:
    _render_trade_away_pick_planner()
with planner_tabs[1]:
    _render_trade_for_pick_planner()

trade_workspace_links = st.columns(2)
trade_workspace_links[0].link_button("Open saved scenarios", "/saved-scenarios")
trade_workspace_links[1].link_button("Journal this scenario", "/decision-journal")
