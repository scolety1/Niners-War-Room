from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.mock_draft_input_contract import READINESS_GREEN, READINESS_RED, READINESS_YELLOW


@dataclass(frozen=True)
class RosterReport:
    readiness: str
    roster_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    no_simulations_run: bool = True


def validate_roster_contract(
    roster_rows: Sequence[Mapping[str, object]] | None,
    available_rows: Sequence[Mapping[str, object]] = (),
) -> RosterReport:
    if roster_rows is None:
        return RosterReport(
            readiness=READINESS_YELLOW,
            roster_count=0,
            errors=(),
            warnings=("Roster input is missing.",),
        )
    errors: list[str] = []
    warnings: list[str] = []
    player_to_team: dict[str, str] = {}
    available_players = {_text(row.get("player")) for row in available_rows}
    for index, row in enumerate(roster_rows, start=1):
        if _is_blank_row(row):
            warnings.append(f"Roster row {index} is blank and was ignored.")
            continue
        for column in ("team_id", "team_name", "player", "position", "keeper_status"):
            if not _text(row.get(column)):
                errors.append(f"Roster row {index} missing {column}.")
        player = _text(row.get("player"))
        team = _text(row.get("team_id"))
        if player in player_to_team and player_to_team[player] != team:
            errors.append(f"Kept player appears on multiple teams: {player}.")
        player_to_team[player] = team
        if player in available_players:
            errors.append(f"Kept player is also listed as available: {player}.")
    return RosterReport(
        readiness=READINESS_RED if errors else READINESS_GREEN,
        roster_count=len(roster_rows),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _is_blank_row(row: Mapping[str, object]) -> bool:
    return not any(_text(value) for value in row.values())
