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
from src.services.trading_lab_nflverse_context_service import (
    display_nflverse_context_rows,
    load_trading_lab_nflverse_context_index,
    nflverse_context_detail_rows,
    nflverse_context_summary_rows,
    nflverse_manual_row_context_rows,
    nflverse_missing_evidence_rows,
)

SESSION_KEY = "draft_day_v1_trading_lab_builder"
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

bundle = load_frozen_board()
trade_frame, trade_path = load_lane_prop_file("trading_lab", "trade_helper_context.csv")
pick_frame, pick_path = load_lane_prop_file("trading_lab", "pick_context.csv")
tier_frame, tier_path = load_lane_prop_file("trading_lab", "trade_tier_values.csv")
mock_pick_frame, mock_pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")

page_header(
    "Trading Lab",
    eyebrow="Draft-Day App V1",
    description=(
        "Manual trade planning workspace using frozen-board rank, tier, pick-window, and "
        "risk-note context only. No package value, offer generation, simulation, private value, "
        "or final trade advice runs here."
    ),
    status_items=(
        ("Manual review only", "review"),
        ("Frozen board source", "safe"),
        ("No trade model added", "safe"),
    ),
)
st.caption(
    "Deep tool: manual trade review. Display-only context is not a trade model, rank input, "
    "or source of truth. No trade calculator or automatic offer generator runs here."
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
nflverse_context = load_trading_lab_nflverse_context_index()

if trade_path is None or trade_frame.empty:
    render_yellow_hold("Trading Lab helper context is missing; review is board-context only.")


def _render_source_metrics(counts: dict[str, int]) -> None:
    cols = st.columns(4)
    cols[0].metric("Frozen baseline rows", counts["frozen_board_rows"])
    cols[1].metric("Trade helper rows", counts["trade_helper_rows"])
    cols[2].metric("Pick context rows", counts["pick_context_rows"])
    cols[3].metric("Tier context rows", counts["tier_context_rows"])
    st.caption(
        "Source badge: Frozen Final Draft Board V1 plus approved lane props. Row counts are "
        "visible. Context is display-only/manual planning and cannot override "
        "`final_board_rank`, create hidden sort fields, or produce package values."
    )


def _render_builder(player_select: dict[str, str], pick_select: dict[str, str]) -> None:
    st.subheader("Trade Builder")
    st.caption(
        "Build both sides manually. The review label is a completeness check, not a verdict, "
        "grade, price, or recommendation."
    )
    give_col, get_col = st.columns(2)
    _render_side_controls("NWR gives", "give", give_col, player_select, pick_select)
    _render_side_controls("NWR gets", "get", get_col, player_select, pick_select)
    clear_col, _spacer = st.columns([1, 3])
    if clear_col.button("Clear Trade", key="trading_lab_clear_trade", width="stretch"):
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
                width="stretch",
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
                width="stretch",
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
                width="stretch",
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
    st.subheader("Manual Package Context")
    review = review_trade_package(st.session_state[SESSION_KEY], lookup)
    cols = st.columns(3)
    cols[0].metric("Manual context status", review.status)
    cols[1].metric("Missing evidence", review.missing_context_display)
    cols[2].metric("Human review", "Required")
    st.caption(f"Rank/tier context: {review.rank_context}")
    st.info(review.explanation)
    st.dataframe(
        display_package_summary(
            package_summary_rows(st.session_state[SESSION_KEY], lookup)
        ).astype(str),
        width="stretch",
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
        display_trade_item_rows(rows).astype(str),
        width="stretch",
        hide_index=True,
        key="trading_lab_selected_items",
    )


def _render_nflverse_context_panel(lookup: dict[str, dict[str, object]]) -> None:
    with st.expander("NFLVerse player context / display-only", expanded=True):
        st.caption(
            "Display-only context | Manual review only | No valuation calculated | "
            "No automatic recommendation. Missing values display as: Not enough information."
        )
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
            st.info(
                "No approved player-context details are available for the selected assets."
            )
        else:
            st.dataframe(details, width="stretch", hide_index=True)

        missing = display_nflverse_context_rows(
            nflverse_missing_evidence_rows(rows, nflverse_context)
        )
        st.markdown("**Missing evidence / deferred context**")
        st.caption(
            "Missing is not zero, neutral, safe, clean, healthy, no-role, no-usage, "
            "or favorable. Next game, opponent, and bye context remain unavailable."
        )
        st.dataframe(missing, width="stretch", hide_index=True)


def _render_diagnostics() -> None:
    with st.expander("Source diagnostics", expanded=False):
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


_render_source_metrics(counts)
builder_tab, trade_away_tab, trade_for_tab = st.tabs(
    ["Package Builder", "Trade Away Pick Planner", "Trade For Pick Planner"]
)
with builder_tab:
    _render_builder(player_select, pick_select)
    _render_summary(lookup)
    _render_selected_items(lookup)
    _render_nflverse_context_panel(lookup)
with trade_away_tab:
    _render_trade_away_pick_planner()
with trade_for_tab:
    _render_trade_for_pick_planner()
_render_diagnostics()
