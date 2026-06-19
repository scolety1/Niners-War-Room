from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from src.services.draft_state_service import (
    DraftBoardState,
    assert_draft_state_valid,
    available_players_after_picks,
    create_empty_draft_state,
    current_draft_pick,
    draft_pick_history,
    draft_progress_summary,
    mark_player_drafted,
    next_my_pick,
    undo_pick,
    validate_draft_state,
)
from src.services.mock_draft_input_contract import (
    MARKET_CONTEXT_COLUMNS,
    NWR_PRIVATE_VALUE_COLUMNS,
)

PRACTICE_PICK_ROWS = (
    {
        "overall_pick": 1,
        "round": 1,
        "round_pick": 1,
        "pick_label": "1.01",
        "current_owner": "Fixture Opponent A",
        "original_owner": "Fixture Opponent A",
        "is_my_pick": False,
    },
    {
        "overall_pick": 2,
        "round": 1,
        "round_pick": 2,
        "pick_label": "1.02",
        "current_owner": "NWR",
        "original_owner": "NWR",
        "is_my_pick": True,
    },
    {
        "overall_pick": 3,
        "round": 1,
        "round_pick": 3,
        "pick_label": "1.03",
        "current_owner": "Fixture Opponent B",
        "original_owner": "Fixture Opponent B",
        "is_my_pick": False,
    },
)

PRACTICE_AVAILABLE_ROWS = (
    {
        "asset_id": "fixture:rookie_a",
        "player": "Fixture Rookie A",
        "position": "WR",
        "nfl_team": "Fixture",
        "asset_type": "Rookie",
        "asset_lifecycle": "incoming_rookie",
        "why_available": "Fixture-only practice rookie.",
        "stats_model_value": 90.0,
        "market_value": 0.0,
        "market_edge": 0.0,
        "confidence": 80.0,
        "overall_rank": 1,
    },
    {
        "asset_id": "fixture:veteran_b",
        "player": "Fixture Veteran B",
        "position": "RB",
        "nfl_team": "FA",
        "asset_type": "Dropped Veteran",
        "asset_lifecycle": "dropped_veteran",
        "why_available": "Fixture-only dropped veteran.",
        "stats_model_value": 75.0,
        "market_value": 0.0,
        "market_edge": 0.0,
        "confidence": 70.0,
        "overall_rank": 2,
    },
    {
        "asset_id": "fixture:rookie_c",
        "player": "Fixture Rookie C",
        "position": "TE",
        "nfl_team": "Fixture",
        "asset_type": "Rookie",
        "asset_lifecycle": "incoming_rookie",
        "why_available": "Fixture-only practice rookie.",
        "stats_model_value": 68.0,
        "market_value": 0.0,
        "market_edge": 0.0,
        "confidence": 65.0,
        "overall_rank": 3,
    },
)

PRACTICE_PRIVATE_VALUE_ROWS = (
    {
        "asset_id": "fixture:rookie_a",
        "nwr_private_value": "fake_fixture_value_only",
        "separation_note": "fixture private value only",
    },
)

PRACTICE_MARKET_ROWS = (
    {
        "asset_id": "fixture:veteran_b",
        "market_adp_pick": "2",
        "allowed_use": "opponent_behavior_only",
        "separation_note": "fixture market behavior only",
    },
)


@dataclass(frozen=True)
class OperatorSession:
    state: DraftBoardState
    source_label: str
    fixture_only: bool
    no_real_inputs: bool
    no_simulations_run: bool
    pick_rows: tuple[dict[str, object], ...]
    available_rows: tuple[dict[str, object], ...]
    private_value_rows: tuple[dict[str, object], ...]
    market_rows: tuple[dict[str, object], ...]


def create_practice_session(
    *,
    pick_rows: tuple[dict[str, object], ...] = PRACTICE_PICK_ROWS,
    available_rows: tuple[dict[str, object], ...] = PRACTICE_AVAILABLE_ROWS,
    private_value_rows: tuple[dict[str, object], ...] = PRACTICE_PRIVATE_VALUE_ROWS,
    market_rows: tuple[dict[str, object], ...] = PRACTICE_MARKET_ROWS,
) -> OperatorSession:
    session = OperatorSession(
        state=create_empty_draft_state(pick_rows=pick_rows, available_rows=available_rows),
        source_label="fixture-only practice",
        fixture_only=True,
        no_real_inputs=True,
        no_simulations_run=True,
        pick_rows=tuple(dict(row) for row in pick_rows),
        available_rows=tuple(dict(row) for row in available_rows),
        private_value_rows=tuple(dict(row) for row in private_value_rows),
        market_rows=tuple(dict(row) for row in market_rows),
    )
    validate_operator_session(session)
    return session


def session_status(session: OperatorSession) -> dict[str, object]:
    summary = draft_progress_summary(session.state)
    current = current_draft_pick(session.state)
    return {
        "source_label": session.source_label,
        "fixture_only": session.fixture_only,
        "no_real_inputs": session.no_real_inputs,
        "no_simulations_run": session.no_simulations_run,
        "current_pick": session.state.current_pick,
        "current_pick_label": summary.current_pick_label,
        "current_owner": summary.current_owner,
        "is_my_turn": bool(current and current.is_my_pick),
        "next_my_pick_label": summary.next_my_pick_label,
        "picks_until_my_pick": summary.picks_until_my_pick,
        "drafted_count": summary.drafted_count,
        "available_count": summary.available_count,
    }


def list_available_assets(
    session: OperatorSession,
    *,
    limit: int = 20,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "asset_id": row.asset_id,
            "player": row.player,
            "position": row.position,
            "asset_type": row.asset_type,
            "fixture_display_value": row.stats_model_value,
            "display_order": index,
        }
        for index, row in enumerate(available_players_after_picks(session.state)[:limit], start=1)
    )


def mark_asset_drafted(
    session: OperatorSession,
    asset_id: str,
    *,
    overall_pick: int | None = None,
) -> OperatorSession:
    next_state = mark_player_drafted(session.state, asset_id, overall_pick=overall_pick)
    next_session = replace(session, state=next_state)
    validate_operator_session(next_session)
    return next_session


def undo_last_pick(session: OperatorSession) -> OperatorSession:
    next_session = replace(session, state=undo_pick(session.state))
    validate_operator_session(next_session)
    return next_session


def draft_history(session: OperatorSession) -> tuple[dict[str, object], ...]:
    return tuple(row.__dict__ for row in draft_pick_history(session.state))


def upcoming_my_picks(session: OperatorSession) -> tuple[dict[str, object], ...]:
    current = session.state.current_pick or 999999
    return tuple(
        {
            "overall_pick": pick.overall_pick,
            "pick_label": pick.pick_label,
            "owner": pick.current_owner,
            "is_next": next_my_pick(session.state) == pick,
        }
        for pick in session.state.picks
        if pick.is_my_pick and pick.overall_pick >= current
    )


def validate_operator_session(session: OperatorSession) -> tuple[str, ...]:
    issues = list(validate_draft_state(session.state))
    private_columns = _columns(session.private_value_rows)
    market_columns = _columns(session.market_rows)
    if private_columns & MARKET_CONTEXT_COLUMNS:
        issues.append("Fixture private value rows contain market behavior columns.")
    if market_columns & NWR_PRIVATE_VALUE_COLUMNS:
        issues.append("Fixture market rows contain NWR private value columns.")
    if issues:
        raise ValueError("Invalid operator session: " + " ".join(issues))
    assert_draft_state_valid(session.state)
    return ()


def render_operator_status(session: OperatorSession) -> str:
    status = session_status(session)
    lines = [
        "Mock Draft operator practice",
        "Mode: fixture-only practice",
        "No real inputs read.",
        "No real simulation run.",
        f"Current pick: {status['current_pick_label']} ({status['current_owner']})",
        f"Next NWR pick: {status['next_my_pick_label']}",
        f"Drafted: {status['drafted_count']}",
        f"Available: {status['available_count']}",
    ]
    return "\n".join(lines)


def serialize_session_state(session: OperatorSession) -> str:
    payload = {
        "source_label": session.source_label,
        "fixture_only": session.fixture_only,
        "no_real_inputs": session.no_real_inputs,
        "no_simulations_run": session.no_simulations_run,
        "pick_rows": list(session.pick_rows),
        "available_rows": list(session.available_rows),
        "private_value_rows": list(session.private_value_rows),
        "market_rows": list(session.market_rows),
        "drafted_asset_ids_by_pick": [
            {"overall_pick": row.overall_pick, "asset_id": row.asset_id}
            for row in draft_pick_history(session.state)
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def deserialize_session_state(payload: str) -> OperatorSession:
    data = json.loads(payload)
    session = create_practice_session(
        pick_rows=tuple(data["pick_rows"]),
        available_rows=tuple(data["available_rows"]),
        private_value_rows=tuple(data.get("private_value_rows", ())),
        market_rows=tuple(data.get("market_rows", ())),
    )
    for row in data.get("drafted_asset_ids_by_pick", ()):
        session = mark_asset_drafted(
            session,
            str(row["asset_id"]),
            overall_pick=int(row["overall_pick"]),
        )
    return session


def save_session_state(session: OperatorSession, path: str | Path) -> None:
    safe_path = _safe_state_path(path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(serialize_session_state(session), encoding="utf-8")


def load_session_state(path: str | Path) -> OperatorSession:
    safe_path = _safe_state_path(path)
    return deserialize_session_state(safe_path.read_text(encoding="utf-8"))


def _safe_state_path(path: str | Path) -> Path:
    target = Path(path)
    normalized = target.as_posix().lower()
    temp_root = Path(tempfile.gettempdir()).resolve()
    resolved_parent = target.parent.resolve() if target.parent.exists() else target.parent
    if normalized.startswith("local_exports/mock_draft/"):
        return target
    try:
        if resolved_parent == temp_root or temp_root in resolved_parent.parents:
            return target
    except OSError:
        pass
    raise ValueError(
        "State path must be explicitly local-only under local_exports/mock_draft/ "
        "or a temp directory."
    )


def _columns(rows: tuple[dict[str, object], ...]) -> set[str]:
    columns: set[str] = set()
    for row in rows:
        columns.update(str(key).strip().lower() for key in row)
    return columns
