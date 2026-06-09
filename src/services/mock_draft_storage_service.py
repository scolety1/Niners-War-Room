from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.services.draft_state_service import (
    DraftBoardState,
    DraftedPlayer,
    DraftPick,
    mark_player_drafted,
    reset_mock,
)

MOCK_DRAFT_SCHEMA_VERSION = 1
DEFAULT_MOCK_DRAFT_DIR = Path("local_exports/mock_drafts")


@dataclass(frozen=True)
class MockDraftSummary:
    mock_name: str
    path: Path
    created_at: str
    active_data_pack: str
    drafted_count: int


class MockDraftValidationError(ValueError):
    pass


def save_mock_draft(
    state: DraftBoardState,
    *,
    mock_name: str,
    active_data_pack: str,
    root: str | Path = DEFAULT_MOCK_DRAFT_DIR,
) -> Path:
    if not mock_name.strip():
        raise MockDraftValidationError("Mock name is required.")
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    path = root_path / f"{_slugify(mock_name)}.json"
    payload = _state_to_payload(
        state,
        mock_name=mock_name.strip(),
        active_data_pack=active_data_pack,
        created_at=_now_timestamp(),
    )
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_mock_draft(
    path: str | Path,
    *,
    base_state: DraftBoardState,
) -> DraftBoardState:
    payload = _load_payload(path)
    state = reset_mock(base_state)
    drafted_rows = _required_list(payload, "drafted_players")
    for row in drafted_rows:
        if not isinstance(row, dict):
            raise MockDraftValidationError("Every drafted player row must be an object.")
        asset_id = _required_str(row, "asset_id")
        overall_pick = _required_int(row, "overall_pick")
        try:
            state = mark_player_drafted(state, asset_id, overall_pick=overall_pick)
        except ValueError as exc:
            raise MockDraftValidationError(str(exc)) from exc
    return state


def duplicate_mock_draft(
    source_path: str | Path,
    *,
    new_mock_name: str,
    root: str | Path = DEFAULT_MOCK_DRAFT_DIR,
) -> Path:
    payload = _load_payload(source_path)
    payload["mock_name"] = new_mock_name.strip()
    payload["created_at"] = _now_timestamp()
    if not payload["mock_name"]:
        raise MockDraftValidationError("Mock name is required.")
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    path = root_path / f"{_slugify(str(payload['mock_name']))}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def list_mock_drafts(root: str | Path = DEFAULT_MOCK_DRAFT_DIR) -> list[MockDraftSummary]:
    root_path = Path(root)
    if not root_path.exists():
        return []
    summaries: list[MockDraftSummary] = []
    for path in sorted(root_path.glob("*.json")):
        try:
            payload = _load_payload(path)
        except MockDraftValidationError:
            continue
        summaries.append(
            MockDraftSummary(
                mock_name=str(payload["mock_name"]),
                path=path,
                created_at=str(payload["created_at"]),
                active_data_pack=str(payload["active_data_pack"]),
                drafted_count=len(_required_list(payload, "drafted_players")),
            )
        )
    return sorted(summaries, key=lambda row: (row.mock_name.lower(), str(row.path)))


def clear_mock_draft(path: str | Path) -> None:
    candidate = Path(path)
    if candidate.exists():
        candidate.unlink()


def _state_to_payload(
    state: DraftBoardState,
    *,
    mock_name: str,
    active_data_pack: str,
    created_at: str,
) -> dict[str, object]:
    return {
        "schema_version": MOCK_DRAFT_SCHEMA_VERSION,
        "mock_name": mock_name,
        "created_at": created_at,
        "active_data_pack": active_data_pack,
        "picks": [_pick_payload(row) for row in state.picks],
        "drafted_players": [_drafted_payload(row) for row in state.drafted_players],
    }


def _pick_payload(pick: DraftPick) -> dict[str, object]:
    return {
        "overall_pick": pick.overall_pick,
        "round": pick.round,
        "round_pick": pick.round_pick,
        "pick_label": pick.pick_label,
        "current_owner": pick.current_owner,
        "original_owner": pick.original_owner,
        "is_my_pick": pick.is_my_pick,
    }


def _drafted_payload(player: DraftedPlayer) -> dict[str, object]:
    return {
        "overall_pick": player.pick.overall_pick,
        "asset_id": player.asset_id,
        "player": player.player,
        "position": player.position,
        "nfl_team": player.nfl_team,
        "asset_type": player.asset_type,
        "stats_model_value": player.stats_model_value,
        "market_edge": player.market_edge,
        "confidence": player.confidence,
    }


def _load_payload(path: str | Path) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MockDraftValidationError("Mock draft file is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise MockDraftValidationError("Mock draft file must contain a JSON object.")
    if payload.get("schema_version") != MOCK_DRAFT_SCHEMA_VERSION:
        raise MockDraftValidationError("Unsupported mock draft schema version.")
    _required_str(payload, "mock_name")
    _required_str(payload, "created_at")
    _required_str(payload, "active_data_pack")
    _required_list(payload, "picks")
    _required_list(payload, "drafted_players")
    return payload


def _required_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MockDraftValidationError(f"Mock draft is missing required field: {key}.")
    return value


def _required_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        raise MockDraftValidationError(f"Mock draft field must be an integer: {key}.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise MockDraftValidationError(
            f"Mock draft field must be an integer: {key}."
        ) from exc


def _required_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise MockDraftValidationError(f"Mock draft is missing list field: {key}.")
    return value


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "mock_draft"


def _now_timestamp() -> str:
    return datetime.now(ZoneInfo("America/Denver")).isoformat(timespec="seconds")
