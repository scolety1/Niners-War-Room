from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.services.draft_day_runtime_state_service import (
    RuntimeState,
    apply_trade_events_to_pick_frame,
    event_rows,
    normalize_runtime_state,
    record_trade_event,
)
from src.services.draft_day_workflow_service import (
    NOT_ENOUGH_INFORMATION,
    available_board_frame,
    current_pick_number,
    player_key_from_row,
    sort_workflow_frame,
    workflow_summary,
)
from src.services.player_compare_decision_service import (
    MARKET_DISPLAY_ONLY_NOTE,
    build_player_compare_decision_summary,
)

DEFAULT_SORT_LABEL = "Dynasty Asset Tier/Rank"
MARKET_SORT_LABELS = {
    "Available-Pool ADP Rank",
    "ADP / Price Context",
    "Market Rank",
    "Market Gap",
}

COCKPIT_BOARD_COLUMNS = (
    "dynasty_asset_tier",
    "dynasty_asset_rank",
    "player",
    "position",
    "nfl_team",
    "age",
    "final_board_rank",
    "why_draft",
    "main_risk",
    "on_clock_confidence",
    "draft_timing_note",
    "source_label_display_only",
)


@dataclass(frozen=True)
class CockpitSummary:
    current_pick: str
    on_clock_team: str
    drafted_count: int
    available_count: int
    trade_count: int
    event_count: int
    last_saved: str
    autosave_status: str


def build_cockpit_summary(
    *,
    board_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    runtime_state: RuntimeState,
) -> CockpitSummary:
    state = normalize_runtime_state(
        runtime_state,
        mode=str(runtime_state.get("mode") or "live"),
        draft_id=str(runtime_state.get("draft_id") or "draft_day_v2"),
    )
    adjusted_picks = apply_trade_events_to_pick_frame(pick_frame, state)
    summary = workflow_summary(board_frame, adjusted_picks, state["workflow_state"])
    return CockpitSummary(
        current_pick=summary.current_pick_label,
        on_clock_team=summary.current_pick_owner or NOT_ENOUGH_INFORMATION,
        drafted_count=summary.drafted_count,
        available_count=summary.available_count,
        trade_count=len(state["trade_events"]),
        event_count=len(event_rows(state)),
        last_saved=str(state.get("updated_at_utc") or state.get("updated_at") or ""),
        autosave_status="Autosave ready" if state.get("updated_at_utc") else "Not saved yet",
    )


def build_cockpit_board(
    board_frame: pd.DataFrame,
    runtime_state: RuntimeState,
    *,
    search: str = "",
    position: str = "All",
    tier: str = "All",
    show_pdf_free_agents: bool = True,
    show_k_dst: bool = False,
    sort_label: str = DEFAULT_SORT_LABEL,
) -> pd.DataFrame:
    state = normalize_runtime_state(
        runtime_state,
        mode=str(runtime_state.get("mode") or "live"),
        draft_id=str(runtime_state.get("draft_id") or "draft_day_v2"),
    )
    frame = available_board_frame(board_frame, state["workflow_state"])
    if not show_k_dst and "position" in frame.columns:
        frame = frame.loc[~frame["position"].astype(str).str.upper().isin({"K", "DST"})].copy()
    if not show_pdf_free_agents and "source_group" in frame.columns:
        frame = frame.loc[~frame["source_group"].astype(str).eq("LVE PDF Free Agent")].copy()
    if position != "All" and "position" in frame.columns:
        frame = frame.loc[frame["position"].astype(str).eq(position)].copy()
    if tier != "All" and "dynasty_asset_tier" in frame.columns:
        frame = frame.loc[frame["dynasty_asset_tier"].astype(str).eq(tier)].copy()
    if search and "player" in frame.columns:
        frame = frame.loc[
            frame["player"].astype(str).str.contains(search, case=False, na=False)
        ].copy()
    if sort_label in MARKET_SORT_LABELS:
        sort_label = DEFAULT_SORT_LABEL
    return sort_workflow_frame(frame, sort_label, ascending=True)


def display_cockpit_board(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=[_label(column) for column in COCKPIT_BOARD_COLUMNS])
    display = frame.loc[:, [column for column in COCKPIT_BOARD_COLUMNS if column in frame.columns]]
    return display.fillna(NOT_ENOUGH_INFORMATION).rename(
        columns={column: _label(column) for column in display.columns}
    )


def tier_count_rows(frame: pd.DataFrame) -> list[dict[str, str]]:
    if frame.empty:
        return []
    tier_column = "dynasty_asset_tier" if "dynasty_asset_tier" in frame.columns else "final_tier"
    if tier_column not in frame.columns:
        return []
    counts = frame[tier_column].replace("", NOT_ENOUGH_INFORMATION).astype(str).value_counts()
    return [
        {"tier": tier, "available_count": str(count)}
        for tier, count in counts.sort_index().items()
    ]


def player_options(frame: pd.DataFrame) -> dict[str, str]:
    options: dict[str, str] = {}
    for _index, row in frame.iterrows():
        key = player_key_from_row(row)
        label = (
            f"#{_field(row, 'dynasty_asset_rank') or _field(row, 'final_board_rank')} - "
            f"{_field(row, 'player')} ({_field(row, 'position')}, {_field(row, 'nfl_team')})"
        )
        options[label] = key
    return options


def selected_player_row(frame: pd.DataFrame, player_key: str) -> dict[str, Any] | None:
    for _index, row in frame.iterrows():
        if player_key_from_row(row) == player_key:
            return row.to_dict()
    return None


def decision_panel_rows(player: dict[str, Any] | None) -> list[dict[str, str]]:
    if not player:
        return [
            {
                "field": "Selected player",
                "value": "Select a player from the board to see decision summary.",
            }
        ]
    flags = red_flags_for_player(player)
    rows = [
        {"field": "Player", "value": _value(player, "player")},
        {"field": "Position / Team / Age", "value": _position_team_age(player)},
        {"field": "NWR rank / tier", "value": _rank_tier(player)},
        {"field": "Why draft", "value": _value(player, "why_draft")},
        {"field": "Main caveat", "value": _value(player, "main_risk")},
        {"field": "Market sanity", "value": _market_note(player)},
        {"field": "Display-only guardrail", "value": MARKET_DISPLAY_ONLY_NOTE},
        {"field": "Red flags", "value": "; ".join(flags) if flags else "None in current context."},
    ]
    return rows


def compare_decision_rows(
    player: dict[str, Any] | None,
    comparison_player: dict[str, Any] | None,
) -> list[dict[str, str]]:
    if not player or not comparison_player:
        return [
            {
                "field": "Compare summary",
                "value": "Select a second player to compare against the selected player.",
            }
        ]
    summary = build_player_compare_decision_summary(player, comparison_player)
    return [
        {"field": "Lean", "value": summary.lean},
        {"field": "Confidence", "value": summary.confidence},
        {"field": "Best use", "value": summary.best_use_case},
        {"field": "Reasons", "value": " ".join(summary.reason_bullets)},
        {"field": "Red flags", "value": "; ".join(summary.red_flags)},
        {"field": "Market note", "value": summary.display_only_market_note},
    ]


def red_flags_for_player(player: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if not _value(player, "player_id") and not _value(player, "sleeper_id"):
        flags.append("missing player_id")
    if _value(player, "age") == NOT_ENOUGH_INFORMATION:
        flags.append("missing age")
    if _value(player, "market_sanity_label") == "No market match":
        flags.append("no market match")
    if _value(player, "outcome_applicable_summary") == NOT_ENOUGH_INFORMATION:
        flags.append("unsupported outcome")
    role_text = " ".join(
        _value(player, key)
        for key in ("main_risk", "candidate_key_caveat", "risk_notes", "on_clock_warning")
    ).lower()
    if any(term in role_text for term in ("role", "depth", "manual", "review")):
        flags.append("role/depth caveat")
    return flags


def owned_pick_rows(pick_frame: pd.DataFrame, runtime_state: RuntimeState) -> pd.DataFrame:
    if pick_frame.empty:
        return pd.DataFrame()
    adjusted = apply_trade_events_to_pick_frame(pick_frame, runtime_state)
    if "current_owner" not in adjusted.columns:
        return pd.DataFrame()
    owner = adjusted["current_owner"].astype(str)
    nwr_mask = owner.str.contains("NWR|Niners", case=False, na=False)
    if "is_nwr_pick" in adjusted.columns:
        nwr_mask = nwr_mask | adjusted["is_nwr_pick"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    columns = [
        column
        for column in ("overall_pick", "pick_label", "current_owner", "original_owner")
        if column in adjusted.columns
    ]
    return adjusted.loc[nwr_mask, columns].copy()


def recent_event_rows(runtime_state: RuntimeState, *, limit: int = 6) -> pd.DataFrame:
    rows = event_rows(runtime_state)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows[-limit:]).iloc[::-1].reset_index(drop=True)


def recent_trade_rows(runtime_state: RuntimeState, *, limit: int = 4) -> pd.DataFrame:
    state = normalize_runtime_state(
        runtime_state,
        mode=str(runtime_state.get("mode") or "live"),
        draft_id=str(runtime_state.get("draft_id") or "draft_day_v2"),
    )
    rows: list[dict[str, str]] = []
    for trade in state["trade_events"][-limit:]:
        rows.append(
            {
                "team_a": str(trade.get("team_a") or ""),
                "team_a_sends": str(trade.get("team_a_sends") or ""),
                "team_b": str(trade.get("team_b") or ""),
                "team_b_sends": str(trade.get("team_b_sends") or ""),
                "status": str(trade.get("status") or ""),
            }
        )
    return pd.DataFrame(rows[::-1])


def record_cockpit_trade(
    runtime_state: RuntimeState,
    *,
    team_a: str,
    team_a_sends: str,
    team_b: str,
    team_b_sends: str,
    notes: str,
    root: Any = None,
) -> RuntimeState:
    return record_trade_event(
        runtime_state,
        team_a=team_a,
        team_a_sends=team_a_sends,
        team_b=team_b,
        team_b_sends=team_b_sends,
        notes=notes,
        root=root,
    )


def current_pick_for_assignment(
    pick_frame: pd.DataFrame,
    runtime_state: RuntimeState,
) -> int | None:
    adjusted = apply_trade_events_to_pick_frame(pick_frame, runtime_state)
    state = normalize_runtime_state(
        runtime_state,
        mode=str(runtime_state.get("mode") or "live"),
        draft_id=str(runtime_state.get("draft_id") or "draft_day_v2"),
    )
    return current_pick_number(adjusted, state["workflow_state"])


def _position_team_age(player: dict[str, Any]) -> str:
    return " / ".join(
        (
            _value(player, "position"),
            _value(player, "nfl_team"),
            _value(player, "age"),
        )
    )


def _rank_tier(player: dict[str, Any]) -> str:
    return (
        f"Rank {_value(player, 'dynasty_asset_rank')} | "
        f"Tier {_value(player, 'dynasty_asset_tier')} | "
        f"Frozen baseline {_value(player, 'final_board_rank')}"
    )


def _market_note(player: dict[str, Any]) -> str:
    for key in ("market_sanity_label", "draft_timing_note", "source_label_display_only"):
        value = _value(player, key)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _value(player: dict[str, Any], key: str) -> str:
    return _field(player, key) or NOT_ENOUGH_INFORMATION


def _field(row: pd.Series | dict[str, Any], key: str) -> str:
    value = row.get(key, "")  # type: ignore[call-arg]
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return ""
    return text


def _label(column: str) -> str:
    return {
        "dynasty_asset_tier": "Tier Section",
        "dynasty_asset_rank": "NWR Draft Rank",
        "player": "Player",
        "position": "Pos",
        "nfl_team": "NFL",
        "age": "Age",
        "final_board_rank": "Frozen Baseline Rank",
        "why_draft": "Why Draft",
        "main_risk": "Main Caveat",
        "on_clock_confidence": "Confidence",
        "draft_timing_note": "Timing Note",
        "source_label_display_only": "Source / Display-Only",
    }.get(column, column.replace("_", " ").title())
