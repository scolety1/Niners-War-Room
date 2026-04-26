from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from src.models.keeper_scores import (
    KeeperPressure,
    KeeperScoreInputs,
    forced_release_candidates,
    keeper_pressure,
    official_top_five,
)


def keeper_inputs_from_rows(rows: Iterable[Mapping[str, object]]) -> list[KeeperScoreInputs]:
    players: list[KeeperScoreInputs] = []
    for row in rows:
        players.append(
            KeeperScoreInputs(
                player_id=str(row.get("player_id") or ""),
                player_name=str(row.get("player_name") or row.get("player_id") or ""),
                position=str(row.get("position") or ""),
                official_rank=_optional_int(row.get("official_rank")),
                private_score=_optional_float(row.get("private_score"), default=50.0),
                market_score=_optional_float(row.get("market_score")),
                my_rank_score=_optional_float(row.get("my_rank_score")),
                confidence_score=_optional_float(row.get("confidence_score"), default=0.6),
                roster_status=str(row.get("roster_status") or "rostered"),
            )
        )
    return players


def official_top_five_names(rows: Iterable[Mapping[str, object]]) -> list[str]:
    return [player.player_name for player in official_top_five(keeper_inputs_from_rows(rows))]


def forced_release_candidate_names(rows: Iterable[Mapping[str, object]]) -> list[str]:
    return [
        player.player_name
        for player in forced_release_candidates(keeper_inputs_from_rows(rows))
    ]


def keeper_pressure_by_team(
    rows: Iterable[Mapping[str, object]],
    *,
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> list[KeeperPressure]:
    rows_by_team: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    team_names: dict[str, str] = {}
    for row in rows:
        team_id = str(row.get("team_id") or "")
        rows_by_team[team_id].append(row)
        team_names[team_id] = str(row.get("team_name") or team_id)

    pressures = []
    for team_id, team_rows in rows_by_team.items():
        top_five_count = len(official_top_five(keeper_inputs_from_rows(team_rows)))
        pressures.append(
            keeper_pressure(
                team_id,
                team_names[team_id],
                len(team_rows),
                top_five_count,
                protect_limit=protect_limit,
                official_top_five_keep_limit=official_top_five_keep_limit,
            )
        )
    return pressures


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_float(value: object, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)
