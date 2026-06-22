from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import pandas as pd

Assignment = dict[str, object]
WorkflowState = dict[str, list[Assignment]]

VISIBLE_RANKING_COLUMNS = (
    "draft_status",
    "assigned_pick",
    "final_board_rank",
    "player",
    "position",
    "nfl_team",
    "asset_type",
    "availability_status",
    "draft_action_display_only",
    "final_board_score_visible",
    "final_tier",
    "position_rank",
    "warning_severity_display_only",
    "risk_notes",
    "needs_manual_review",
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
    "player": "Player",
    "position": "Pos",
    "nfl_team": "NFL Team",
    "asset_type": "Asset Type",
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
    "Player": "player",
    "Position": "position",
    "Tier": "final_tier",
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


def display_ranking_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in VISIBLE_RANKING_COLUMNS if column in frame.columns]
    display = frame.loc[:, columns].copy()
    return display.rename(columns=RANKING_LABELS)


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
    if column in {"final_board_rank", "position_rank", "final_board_score_visible"}:
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
        raise DraftWorkflowError("Selected player is not on the frozen board.")
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
