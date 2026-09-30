"""Deterministic multi-week Redraft streamer aggregation.

The ranking authority is NWR's admitted weekly-projection provider scored
with the connected league settings.  Schedule facts only describe the
window; they do not add a hidden matchup weight.  External expert consensus
is intentionally absent from the score and may be shown separately as QA.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamerHorizonRow:
    sleeper_player_id: str
    player_name: str
    position: str
    team: str
    availability: str
    values: tuple[float | None, float | None, float | None, float | None]
    selected_horizon_value: float | None
    schedule: tuple[str, ...]
    why: str
    action: str


@dataclass(frozen=True)
class StreamerHorizonResult:
    horizon_weeks: int
    start_week: int
    requested_weeks: tuple[int, ...]
    projection_weeks_available: tuple[int, ...]
    schedule_weeks_available: tuple[int, ...]
    rows: tuple[StreamerHorizonRow, ...]
    limitations: tuple[str, ...]


def _cumulative(points: Sequence[float], coverage: Sequence[bool], weeks: int) -> float | None:
    if weeks <= 0 or len(points) < weeks or not all(coverage[:weeks]):
        return None
    return round(sum(points[:weeks]), 2)


def build_streamer_horizon(
    *,
    start_week: int,
    horizon_weeks: int,
    weekly_rows: Mapping[int, Sequence[Mapping[str, object]]],
    schedule_opponents: Mapping[int, Mapping[str, str]],
    own_player_ids: Sequence[str],
    owned_player_ids: Sequence[str],
    relevant_positions: Sequence[str],
    max_rows_per_position: int = 10,
) -> StreamerHorizonResult:
    if not 1 <= horizon_weeks <= 4:
        raise ValueError("horizon_weeks must be between 1 and 4.")
    requested = tuple(range(start_week, min(18, start_week + 3) + 1))
    projection_weeks = tuple(week for week in requested if week in weekly_rows)
    schedule_weeks = tuple(week for week in requested if week in schedule_opponents)
    own = set(own_player_ids)
    owned = set(owned_player_ids)
    positions = {str(value).upper() for value in relevant_positions}

    identities: dict[str, dict[str, str]] = {}
    points_by_id: dict[str, dict[int, float]] = {}
    for week, rows in weekly_rows.items():
        for row in rows:
            player_id = str(row.get("sleeperPlayerId") or row.get("sleeper_player_id") or "")
            position = str(row.get("position") or "").upper()
            if not player_id or position not in positions:
                continue
            if player_id in owned and player_id not in own:
                continue
            identities[player_id] = {
                "player_name": str(row.get("playerName") or row.get("player_name") or player_id),
                "position": position,
                "team": str(row.get("team") or "").upper(),
            }
            try:
                projected = float(row.get("projectedPoints") or row.get("projected_points") or 0.0)
            except (TypeError, ValueError):
                projected = 0.0
            points_by_id.setdefault(player_id, {})[week] = max(0.0, projected)

    rows: list[StreamerHorizonRow] = []
    raw_rows: list[tuple[str, dict[str, str], list[float], list[bool], list[str]]] = []
    for player_id, identity in identities.items():
        points: list[float] = []
        coverage: list[bool] = []
        schedule: list[str] = []
        team = identity["team"]
        for week in requested:
            week_covered = week in weekly_rows
            coverage.append(week_covered)
            points.append(points_by_id.get(player_id, {}).get(week, 0.0))
            if week not in schedule_opponents:
                schedule.append(f"W{week} unknown")
            elif not team:
                schedule.append(f"W{week} team unknown")
            else:
                opponent = schedule_opponents[week].get(team)
                schedule.append(f"W{week} {opponent}" if opponent else f"W{week} BYE")
        raw_rows.append((player_id, identity, points, coverage, schedule))

    own_best: dict[str, float] = {}
    for player_id, identity, points, coverage, _schedule in raw_rows:
        selected = _cumulative(points, coverage, horizon_weeks)
        if player_id in own and selected is not None:
            own_best[identity["position"]] = max(
                own_best.get(identity["position"], float("-inf")),
                selected,
            )

    for player_id, identity, points, coverage, schedule in raw_rows:
        values = tuple(_cumulative(points, coverage, weeks) for weeks in range(1, 5))
        selected = values[horizon_weeks - 1]
        availability = "ON YOUR ROSTER" if player_id in own else "AVAILABLE"
        current_best = own_best.get(identity["position"])
        if player_id in own:
            action = (
                "KEEP CURRENT"
                if selected is not None and selected >= current_best
                else "ROSTER DEPTH"
            )
        elif selected is None:
            action = "NOT ENOUGH DATA"
        elif current_best is None or selected > current_best + 0.5:
            action = "STREAM"
        else:
            action = "KEEP CURRENT"
        why = (
            f"NWR weekly projections total {selected:.1f} points across the selected "
            f"{horizon_weeks}-week window."
            if selected is not None
            else f"The full {horizon_weeks}-week projection window is not available."
        )
        rows.append(
            StreamerHorizonRow(
                sleeper_player_id=player_id,
                player_name=identity["player_name"],
                position=identity["position"],
                team=identity["team"],
                availability=availability,
                values=values,  # type: ignore[arg-type]
                selected_horizon_value=selected,
                schedule=tuple(schedule),
                why=why,
                action=action,
            )
        )

    selected_rows: list[StreamerHorizonRow] = []
    for position in sorted(positions):
        position_rows = [row for row in rows if row.position == position]
        position_rows.sort(
            key=lambda row: (
                row.selected_horizon_value is None,
                -(row.selected_horizon_value or 0.0),
                row.availability != "AVAILABLE",
                row.player_name.casefold(),
            )
        )
        chosen = position_rows[:max_rows_per_position]
        # Always retain the best currently-owned comparison row even when
        # ten available players project higher.
        best_owned = next(
            (row for row in position_rows if row.availability == "ON YOUR ROSTER"),
            None,
        )
        if best_owned is not None and best_owned not in chosen:
            chosen = [*chosen[:-1], best_owned]
        selected_rows.extend(chosen)

    limitations: list[str] = []
    missing_projection = [week for week in requested[:horizon_weeks] if week not in weekly_rows]
    if missing_projection:
        limitations.append(
            "Weekly projections unavailable for "
            + ", ".join(f"Week {week}" for week in missing_projection)
            + "."
        )
    missing_schedule = [
        week for week in requested[:horizon_weeks] if week not in schedule_opponents
    ]
    if missing_schedule:
        limitations.append(
            "Schedule context unavailable for "
            + ", ".join(f"Week {week}" for week in missing_schedule)
            + "."
        )
    if not limitations:
        limitations.append("Schedule is descriptive only; no hidden matchup multiplier is applied.")
    return StreamerHorizonResult(
        horizon_weeks=horizon_weeks,
        start_week=start_week,
        requested_weeks=requested,
        projection_weeks_available=projection_weeks,
        schedule_weeks_available=schedule_weeks,
        rows=tuple(selected_rows),
        limitations=tuple(limitations),
    )
