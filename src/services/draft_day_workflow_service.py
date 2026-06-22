from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

Assignment = dict[str, object]
WorkflowState = dict[str, list[Assignment]]
NOT_ENOUGH_INFORMATION = "Not enough information"
SLEEPER_ADP_POINTER_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context"
    r"\latest_candidate.json"
)

CORE_RANKING_COLUMNS = (
    "cross_asset_candidate_rank",
    "final_board_rank",
    "player",
    "position",
    "nfl_team",
    "age",
    "position_rank",
    "candidate_value_band",
    "cross_asset_candidate_value",
    "confidence_band",
    "adp_display_only",
    "available_pool_adp_range",
    "current_pick_value_display_only",
    "source_label_display_only",
    "final_tier",
    "candidate_key_caveat",
    "risk_notes",
    "needs_manual_review",
)

DRAFTED_CONTEXT_COLUMNS = (
    "draft_status",
    "assigned_pick",
)

DRAFT_BOARD_COLUMNS = (
    "overall_pick",
    "pick_label",
    "round",
    "round_pick",
    "current_owner",
    "is_nwr_pick",
    "pick_status",
    "player",
    "position",
    "nfl_team",
    "final_board_rank",
    "final_tier",
)

RANKING_LABELS = {
    "draft_status": "Draft Status",
    "assigned_pick": "Assigned Pick",
    "final_board_rank": "Final Board Rank",
    "final_tier": "Final Tier",
    "position_rank": "Position Rank",
    "cross_asset_candidate_rank": "Tuned V2 Candidate Rank (Review-Only)",
    "cross_asset_candidate_value": "Tuned V2 Candidate Value (Review-Only)",
    "candidate_value_band": "Candidate Band",
    "confidence_band": "Confidence",
    "available_pool_adp_rank": "Available-Pool ADP Rank (Display-Only)",
    "available_pool_adp_range": "Available-Pool ADP Range (Display-Only)",
    "candidate_key_caveat": "Key Caveat / Review Flag",
    "player": "Player",
    "position": "Pos",
    "nfl_team": "NFL Team",
    "age": "Age",
    "asset_type": "Asset Type",
    "adp_display_only": "ADP (Display-Only)",
    "adp_range_display_only": "ADP Range (Display-Only)",
    "current_pick_value_display_only": "Current Pick Value (Display-Only)",
    "source_label_display_only": "Source",
    "availability_status": "Board Availability",
    "final_board_score_visible": "Visible Score (Mixed Basis)",
    "draft_action_display_only": "Draft Action (Display-Only)",
    "warning_severity_display_only": "Warning (Display-Only)",
    "risk_notes": "Risk Notes",
    "needs_manual_review": "Manual Review",
}

DRAFT_BOARD_LABELS = {
    "overall_pick": "Overall",
    "pick_label": "Pick",
    "round": "Round",
    "round_pick": "Round Pick",
    "current_owner": "Owner",
    "is_nwr_pick": "NWR Pick",
    "pick_status": "Status",
    "player": "Player",
    "position": "Pos",
    "nfl_team": "NFL Team",
    "final_board_rank": "Board Rank",
    "final_tier": "Tier",
}

VISIBLE_SORT_COLUMNS = {
    "Final Board Rank": "final_board_rank",
    "Candidate Rank": "cross_asset_candidate_rank",
    "Candidate Value": "cross_asset_candidate_value",
    "Available-Pool ADP Rank": "available_pool_adp_rank",
    "Player": "player",
    "Position": "position",
    "Tier": "final_tier",
    "Position Rank": "position_rank",
    "Visible Board Score": "final_board_score_visible",
    "Draft Status": "draft_status",
}


class DraftWorkflowError(ValueError):
    """User-facing draft workflow validation error."""


@dataclass(frozen=True)
class DraftWorkflowSummary:
    drafted_count: int
    available_count: int
    current_pick_label: str
    current_pick_owner: str


def empty_workflow_state() -> WorkflowState:
    return {"assignments": []}


def normalize_workflow_state(state: Any) -> WorkflowState:
    if not isinstance(state, dict):
        return empty_workflow_state()
    assignments = state.get("assignments", [])
    if not isinstance(assignments, list):
        return empty_workflow_state()
    clean: list[Assignment] = []
    seen_picks: set[int] = set()
    seen_players: set[str] = set()
    for assignment in assignments:
        if not isinstance(assignment, dict):
            continue
        player_key = str(assignment.get("player_key", "")).strip()
        overall_pick = _int_or_none(assignment.get("overall_pick"))
        if not player_key or overall_pick is None:
            continue
        if overall_pick in seen_picks or player_key in seen_players:
            continue
        clean.append(dict(assignment))
        seen_picks.add(overall_pick)
        seen_players.add(player_key)
    return {"assignments": clean}


def player_key_from_row(row: pd.Series | dict[str, object]) -> str:
    getter = row.get
    return _visible_key(
        getter("final_board_rank", ""),
        getter("player", ""),
        getter("position", ""),
        getter("nfl_team", ""),
    )


def pick_key_from_row(row: pd.Series | dict[str, object]) -> int:
    value = _int_or_none(row.get("overall_pick", ""))
    if value is None:
        raise DraftWorkflowError("Selected pick does not have a valid overall pick number.")
    return value


def with_workflow_columns(board: pd.DataFrame, state: WorkflowState) -> pd.DataFrame:
    normalized = normalize_workflow_state(state)
    by_player = {str(row["player_key"]): row for row in normalized["assignments"]}
    rows: list[dict[str, object]] = []
    for _index, row in board.iterrows():
        record = row.to_dict()
        player_key = player_key_from_row(row)
        assignment = by_player.get(player_key)
        record["draft_status"] = "Drafted" if assignment else "Available"
        record["assigned_pick"] = assignment.get("pick_label", "") if assignment else ""
        rows.append(record)
    return pd.DataFrame(rows)


def available_board_frame(board: pd.DataFrame, state: WorkflowState) -> pd.DataFrame:
    frame = with_workflow_columns(board, state)
    if "draft_status" not in frame.columns:
        return frame
    return frame.loc[frame["draft_status"] == "Available"].copy()


def display_ranking_frame(
    frame: pd.DataFrame,
    *,
    show_drafted_context: bool = False,
    current_pick: int | None = None,
) -> pd.DataFrame:
    contextual = with_display_context(frame, current_pick=current_pick)
    visible_columns = list(CORE_RANKING_COLUMNS)
    if show_drafted_context:
        visible_columns = [*DRAFTED_CONTEXT_COLUMNS, *visible_columns]
    columns = [column for column in visible_columns if column in contextual.columns]
    display = contextual.loc[:, columns].copy()
    return display.rename(columns=RANKING_LABELS)


def with_display_context(
    frame: pd.DataFrame,
    *,
    current_pick: int | None = None,
) -> pd.DataFrame:
    contextual = frame.copy()
    adp_lookup = sleeper_adp_display_lookup()
    adp_values: list[str] = []
    range_values: list[str] = []
    current_pick_values: list[str] = []
    source_values: list[str] = []
    for row in contextual.to_dict("records"):
        key = _adp_key(row.get("player"), row.get("position"))
        adp_row = adp_lookup.get(key, {})
        adp_text = str(
            row.get("adp") or adp_row.get("adp") or row.get("adp_display_only") or ""
        ).strip()
        range_text = str(
            row.get("available_pool_adp_range")
            or adp_row.get("range")
            or row.get("adp_range_display_only")
            or ""
        ).strip()
        adp_values.append(adp_text or NOT_ENOUGH_INFORMATION)
        range_values.append(range_text or NOT_ENOUGH_INFORMATION)
        current_pick_values.append(
            current_pick_value_label(
                current_pick,
                str(row.get("available_pool_adp_rank") or "").strip(),
                candidate_rank=str(row.get("cross_asset_candidate_rank") or "").strip(),
                confidence=str(row.get("confidence_band") or "").strip(),
            )
        )
        source_values.append(source_label_for_row(row, adp_row))
    contextual["adp_display_only"] = adp_values
    contextual["adp_range_display_only"] = range_values
    contextual["available_pool_adp_range"] = range_values
    contextual["current_pick_value_display_only"] = current_pick_values
    contextual["source_label_display_only"] = source_values
    return contextual


def sort_workflow_frame(
    frame: pd.DataFrame,
    sort_label: str,
    *,
    ascending: bool = True,
) -> pd.DataFrame:
    column = VISIBLE_SORT_COLUMNS.get(sort_label, "final_board_rank")
    if column not in frame.columns:
        return frame.copy()
    sorted_frame = frame.copy()
    if column in {
        "final_board_rank",
        "position_rank",
        "final_board_score_visible",
        "cross_asset_candidate_rank",
        "cross_asset_candidate_value",
        "available_pool_adp_rank",
    }:
        sorted_frame["_visible_sort"] = pd.to_numeric(sorted_frame[column], errors="coerce")
        sorted_frame = sorted_frame.sort_values(
            by=["_visible_sort", "player"],
            ascending=[ascending, True],
            na_position="last",
            kind="stable",
        ).drop(columns=["_visible_sort"])
    else:
        sorted_frame = sorted_frame.sort_values(
            by=[column, "final_board_rank" if "final_board_rank" in frame.columns else column],
            ascending=[ascending, True],
            kind="stable",
        )
    return sorted_frame.reset_index(drop=True)


@lru_cache(maxsize=1)
def sleeper_adp_display_lookup() -> dict[str, dict[str, str]]:
    if not SLEEPER_ADP_POINTER_PATH.exists():
        return {}
    try:
        pointer = json.loads(SLEEPER_ADP_POINTER_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    allowed = {str(value) for value in pointer.get("allowed_use", [])}
    blocked = {str(value) for value in pointer.get("blocked_use", [])}
    if "display_only" not in allowed or "rankings" not in blocked:
        return {}
    snapshot_path = Path(str(pointer.get("snapshot_path", "")))
    data_file = str(pointer.get("data_file", ""))
    source_path = snapshot_path / data_file
    if not source_path.exists():
        return {}
    try:
        frame = pd.read_csv(source_path, dtype=str).fillna("")
    except Exception:
        return {}
    lookup: dict[str, dict[str, str]] = {}
    for row in frame.to_dict("records"):
        key = _adp_key(row.get("player_name"), row.get("position"))
        if not key:
            continue
        preferred = _display_adp(row.get("preferred_adp_for_nwr"))
        adp_range = _adp_source_field_range(row)
        lookup[key] = {
            "adp": preferred,
            "range": adp_range,
            "source_risk": str(row.get("source_risk", "")),
        }
    return lookup


def source_label_for_row(row: dict[str, object], adp_row: dict[str, str]) -> str:
    source = str(row.get("source_label_display_only") or "Frozen Board")
    if adp_row:
        risk = adp_row.get("source_risk") or "display-only"
        risk_label = "YELLOW" if "YELLOW" in risk else risk
        source = f"{source} + ADP ({risk_label})"
    return source


def current_pick_value_label(
    current_pick: int | None,
    available_pool_adp_rank: str,
    *,
    candidate_rank: str = "",
    confidence: str = "",
) -> str:
    if current_pick is None:
        return NOT_ENOUGH_INFORMATION
    try:
        pool_rank = float(str(available_pool_adp_rank).strip())
    except ValueError:
        return NOT_ENOUGH_INFORMATION
    try:
        candidate = float(str(candidate_rank).strip())
    except ValueError:
        candidate = pool_rank
    price_delta = float(current_pick) - pool_rank
    value_delta = float(current_pick) - candidate
    low_confidence = str(confidence).strip().lower() in {"low", "very low"}
    if low_confidence and value_delta < 6:
        return NOT_ENOUGH_INFORMATION
    if price_delta <= -8 and value_delta <= -4:
        return "Too early"
    if price_delta <= -4:
        return "Reach"
    if price_delta <= -2:
        return "Slight reach"
    if value_delta >= 10 and price_delta >= 3:
        return "Steal"
    if value_delta >= 4 or price_delta >= 2:
        return "Value"
    return "Fair"


def _adp_source_field_range(row: dict[str, object]) -> str:
    values = [
        _meaningful_adp(row.get(column))
        for column in ("adp_dynasty_std", "adp_dynasty", "adp_std")
    ]
    numeric_values = [value for value in values if value is not None]
    if len(numeric_values) < 2:
        return NOT_ENOUGH_INFORMATION
    minimum = min(numeric_values)
    maximum = max(numeric_values)
    if minimum == maximum:
        return f"{minimum:.1f}"
    return f"{minimum:.1f}-{maximum:.1f}"


def _display_adp(value: object) -> str:
    numeric = _meaningful_adp(value)
    if numeric is None:
        return NOT_ENOUGH_INFORMATION
    return f"{numeric:.1f}"


def _meaningful_adp(value: object) -> float | None:
    try:
        numeric = float(str(value).strip())
    except ValueError:
        return None
    if numeric <= 0 or numeric >= 900:
        return None
    return numeric


def _adp_key(name: object, position: object) -> str:
    normalized_name = re.sub(r"[^a-z0-9]+", "", str(name or "").casefold())
    normalized_position = str(position or "").strip().upper()
    if not normalized_name or not normalized_position:
        return ""
    return f"{normalized_name}|{normalized_position}"


def player_select_options(frame: pd.DataFrame) -> dict[str, str]:
    options: dict[str, str] = {}
    for _index, row in frame.iterrows():
        label = (
            f"#{row.get('final_board_rank', '')} - {row.get('player', '')} "
            f"({row.get('position', '')}, {row.get('nfl_team', '')})"
        )
        options[label] = player_key_from_row(row)
    return options


def pick_select_options(pick_frame: pd.DataFrame) -> dict[str, int]:
    options: dict[str, int] = {}
    for _index, row in pick_frame.iterrows():
        overall = pick_key_from_row(row)
        label = (
            f"{row.get('pick_label', overall)} - {row.get('current_owner', '')} "
            f"(overall {overall})"
        )
        options[label] = overall
    return options


def current_pick_number(pick_frame: pd.DataFrame, state: WorkflowState) -> int | None:
    normalized = normalize_workflow_state(state)
    assigned = {int(row["overall_pick"]) for row in normalized["assignments"]}
    for _index, row in pick_frame.iterrows():
        overall = pick_key_from_row(row)
        if overall not in assigned:
            return overall
    return None


def current_pick_label(pick_frame: pd.DataFrame, state: WorkflowState) -> str:
    current = current_pick_number(pick_frame, state)
    if current is None:
        return "Draft complete"
    row = _pick_row(pick_frame, current)
    return str(row.get("pick_label", current)) if row is not None else str(current)


def assign_player_to_pick(
    state: WorkflowState,
    *,
    board: pd.DataFrame,
    pick_frame: pd.DataFrame,
    player_key: str,
    overall_pick: int,
) -> WorkflowState:
    normalized = normalize_workflow_state(state)
    player_row = _player_row(board, player_key)
    if player_row is None:
        raise DraftWorkflowError("Selected player is not in the draftable player pool.")
    pick_row = _pick_row(pick_frame, overall_pick)
    if pick_row is None:
        raise DraftWorkflowError("Selected pick slot is not in the draft board.")
    for assignment in normalized["assignments"]:
        if (
            assignment.get("player_key") == player_key
            and assignment.get("overall_pick") != overall_pick
        ):
            raise DraftWorkflowError(
                f"{player_row.get('player', 'Selected player')} is already assigned to "
                f"{assignment.get('pick_label', 'another pick')}."
            )
    next_assignments = [
        assignment
        for assignment in normalized["assignments"]
        if int(assignment["overall_pick"]) != overall_pick
    ]
    next_assignments.append(_assignment_from_rows(player_row, pick_row, player_key))
    return {"assignments": next_assignments}


def undo_last_pick(state: WorkflowState) -> tuple[WorkflowState, str]:
    normalized = normalize_workflow_state(state)
    if not normalized["assignments"]:
        return normalized, "No drafted pick to undo."
    undone = normalized["assignments"][-1]
    return {"assignments": normalized["assignments"][:-1]}, (
        f"Undid {undone.get('player', 'selected player')} from "
        f"{undone.get('pick_label', 'the last pick')}."
    )


def remove_pick_assignment(state: WorkflowState, overall_pick: int) -> tuple[WorkflowState, str]:
    normalized = normalize_workflow_state(state)
    kept = [
        assignment
        for assignment in normalized["assignments"]
        if int(assignment["overall_pick"]) != overall_pick
    ]
    if len(kept) == len(normalized["assignments"]):
        return normalized, "No player was assigned to that pick."
    return {"assignments": kept}, "Removed the selected pick assignment."


def draft_board_frame(
    pick_frame: pd.DataFrame,
    nwr_picks_frame: pd.DataFrame,
    state: WorkflowState,
) -> pd.DataFrame:
    normalized = normalize_workflow_state(state)
    by_pick = {int(row["overall_pick"]): row for row in normalized["assignments"]}
    nwr_pick_numbers = {
        int(value)
        for value in nwr_picks_frame.get("overall_pick", pd.Series(dtype=object)).tolist()
        if _int_or_none(value) is not None
    }
    current = current_pick_number(pick_frame, normalized)
    rows: list[dict[str, object]] = []
    for _index, row in pick_frame.iterrows():
        overall = pick_key_from_row(row)
        assignment = by_pick.get(overall, {})
        status = "Current" if overall == current else "Open"
        if assignment:
            status = "Drafted"
        rows.append(
            {
                "overall_pick": overall,
                "pick_label": row.get("pick_label", overall),
                "round": row.get("round", ""),
                "round_pick": row.get("round_pick", ""),
                "current_owner": row.get("current_owner", ""),
                "is_nwr_pick": "Yes" if overall in nwr_pick_numbers else "",
                "pick_status": status,
                "player": assignment.get("player", ""),
                "position": assignment.get("position", ""),
                "nfl_team": assignment.get("nfl_team", ""),
                "final_board_rank": assignment.get("final_board_rank", ""),
                "final_tier": assignment.get("final_tier", ""),
            }
        )
    return pd.DataFrame(rows)


def display_draft_board_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in DRAFT_BOARD_COLUMNS if column in frame.columns]
    display = frame.loc[:, columns].copy()
    for column in display.columns:
        display[column] = display[column].astype(str)
    return display.rename(columns=DRAFT_BOARD_LABELS)


def workflow_summary(
    board: pd.DataFrame,
    pick_frame: pd.DataFrame,
    state: WorkflowState,
) -> DraftWorkflowSummary:
    normalized = normalize_workflow_state(state)
    drafted_count = len(normalized["assignments"])
    current = current_pick_number(pick_frame, normalized)
    current_label = "Draft complete"
    current_owner = ""
    if current is not None:
        row = _pick_row(pick_frame, current)
        if row is not None:
            current_label = str(row.get("pick_label", current))
            current_owner = str(row.get("current_owner", ""))
    return DraftWorkflowSummary(
        drafted_count=drafted_count,
        available_count=max(int(board.shape[0]) - drafted_count, 0),
        current_pick_label=current_label,
        current_pick_owner=current_owner,
    )


def validate_no_duplicate_assignments(state: WorkflowState) -> tuple[str, ...]:
    normalized = normalize_workflow_state(state)
    player_keys = [str(row.get("player_key", "")) for row in normalized["assignments"]]
    pick_numbers = [int(row["overall_pick"]) for row in normalized["assignments"]]
    issues: list[str] = []
    if len(player_keys) != len(set(player_keys)):
        issues.append("A player appears on more than one pick.")
    if len(pick_numbers) != len(set(pick_numbers)):
        issues.append("A pick slot has more than one player.")
    return tuple(issues)


def _assignment_from_rows(
    player_row: pd.Series,
    pick_row: pd.Series,
    player_key: str,
) -> Assignment:
    return {
        "player_key": player_key,
        "overall_pick": pick_key_from_row(pick_row),
        "pick_label": pick_row.get("pick_label", ""),
        "pick_owner": pick_row.get("current_owner", ""),
        "player": player_row.get("player", ""),
        "position": player_row.get("position", ""),
        "nfl_team": player_row.get("nfl_team", ""),
        "final_board_rank": player_row.get("final_board_rank", ""),
        "final_tier": player_row.get("final_tier", ""),
    }


def _player_row(board: pd.DataFrame, player_key: str) -> pd.Series | None:
    for _index, row in board.iterrows():
        if player_key_from_row(row) == player_key:
            return row
    return None


def _pick_row(pick_frame: pd.DataFrame, overall_pick: int) -> pd.Series | None:
    for _index, row in pick_frame.iterrows():
        if pick_key_from_row(row) == overall_pick:
            return row
    return None


def _visible_key(*parts: object) -> str:
    return "|".join(str(part or "").strip() for part in parts)


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def copy_state(state: WorkflowState) -> WorkflowState:
    return deepcopy(normalize_workflow_state(state))
