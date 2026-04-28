from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.keeper_scores import KeeperDecision, KeeperScoreInputs
from src.services.team_service import build_team_keeper_board


@dataclass(frozen=True)
class LeagueIntelBoard:
    snapshot_date: str | None
    pressure_rows: list[dict[str, object]]
    default_release_rows: list[dict[str, object]]
    shield_rows: list[dict[str, object]]
    pressure_levels: list[str]


def build_league_intel(
    data_pack_path: str | Path,
    *,
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> LeagueIntelBoard:
    validated = validate_data_pack(data_pack_path)
    rows_by_team = _rows_by_team(_joined_player_rows(validated.rows_by_table))
    pressure_rows: list[dict[str, object]] = []
    default_release_rows: list[dict[str, object]] = []
    shield_rows: list[dict[str, object]] = []

    for team_id, rows in rows_by_team.items():
        team_name = _team_name(rows, team_id)
        board = build_team_keeper_board(
            [_keeper_input(row) for row in rows],
            team_id=team_id,
            team_name=team_name,
            protect_limit=protect_limit,
            official_top_five_keep_limit=official_top_five_keep_limit,
        )
        pressure_rows.append(
            {
                "team": team_name,
                "pressure_level": board.pressure.pressure_level.title(),
                "pressure_count": board.pressure.pressure_count,
                "forced_release_count": board.pressure.forced_release_count,
                "official_top_five_count": board.pressure.official_top_five_count,
                "roster_count": board.pressure.roster_count,
                "protect_limit": board.pressure.protect_limit,
            }
        )
        decisions = {decision.player_id: decision for decision in board.decisions}
        default_release_rows.extend(
            _candidate_row(team_name, player.player_id, decisions, "Default Release")
            for player in board.forced_release_candidates
        )
        shield_rows.extend(
            _candidate_row(team_name, decision.player_id, decisions, "Shield")
            for decision in board.decisions
            if decision.top_five_shield_eligible
        )

    pressure_rows = sorted(
        pressure_rows,
        key=lambda row: (
            -int(row["pressure_count"]),
            str(row["team"]),
        ),
    )
    default_release_rows = sorted(
        default_release_rows,
        key=lambda row: (-float(row["drop_score"] or 0.0), str(row["team"])),
    )
    shield_rows = sorted(
        shield_rows,
        key=lambda row: (-float(row["keeper_score"] or 0.0), str(row["team"])),
    )
    return LeagueIntelBoard(
        snapshot_date=validated.snapshot_date,
        pressure_rows=pressure_rows,
        default_release_rows=default_release_rows,
        shield_rows=shield_rows,
        pressure_levels=_ordered_pressure_levels(
            {str(row["pressure_level"]) for row in pressure_rows}
        ),
    )


def _joined_player_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(rows_by_table.get("model_outputs", []))
    rows: list[dict[str, object]] = []
    for roster_row in rows_by_table.get("rosters", []):
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        output_row = outputs.get(player_id, {})
        row = dict(roster_row)
        row["official_rank"] = _first_present(
            roster_row.get("official_rank"),
            ranking_row.get("official_rank"),
        )
        for column in (
            "private_score",
            "market_score",
            "confidence_score",
        ):
            row[column] = output_row.get(column)
        rows.append(row)
    return rows


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _rows_by_team(
    rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    rows_by_team: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        team_id = str(row.get("team_id") or "")
        rows_by_team[team_id].append(row)
    return dict(rows_by_team)


def _keeper_input(row: dict[str, object]) -> KeeperScoreInputs:
    return KeeperScoreInputs(
        player_id=str(row.get("player_id") or ""),
        player_name=str(row.get("player_name") or row.get("player_id") or ""),
        position=str(row.get("position") or ""),
        official_rank=_optional_int(row.get("official_rank")),
        private_score=_optional_float(row.get("private_score"), 50.0),
        market_score=_optional_float(row.get("market_score")),
        confidence_score=_optional_float(row.get("confidence_score"), 0.6),
        roster_status=str(row.get("roster_status") or "rostered"),
    )


def _team_name(rows: list[dict[str, object]], fallback: str) -> str:
    if not rows:
        return fallback
    return str(rows[0].get("team_name") or fallback)


def _candidate_row(
    team_name: str,
    player_id: str,
    decisions: dict[str, KeeperDecision],
    signal: str,
) -> dict[str, object]:
    decision = decisions[player_id]
    return {
        "team": team_name,
        "player": decision.player_name,
        "pos": decision.position,
        "signal": signal,
        "official_rank": decision.official_rank,
        "keeper_score": decision.keeper_score,
        "drop_score": decision.drop_candidate_score,
        "confidence": decision.confidence_score,
    }


def _ordered_pressure_levels(levels: set[str]) -> list[str]:
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(levels, key=lambda level: (order.get(level, 99), level))


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_float(value: object, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)
