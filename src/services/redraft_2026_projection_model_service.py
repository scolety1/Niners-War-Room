from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_ID = "NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1"
MODEL_POSITIONS = ("QB", "RB", "WR", "TE")
# NWR class-time hardening, Diggs-class false-positive guard (real,
# root-caused: docs/codex/NWR_BROOKS_DIGGS_JUDKINS_ROOT_CAUSE_V1_20260908.md).
# The `last_season` one-year widening below admits real, currently active
# players missing their most recent stat line (Diggs-class) -- but the
# nflverse player-registry `status` field alone does not reliably catch
# real long-retired players (verified: Philip Rivers and Russell Wilson
# both show status=ACT in the same registry, years after they actually
# stopped playing). The real, staged `seasonal_rosters` snapshot's own
# `status` column is a genuinely different, more precise signal for this
# ("final roster status" for the season, not a stats-presence field) --
# verified directly: Rivers/Wilson show INA there while every real
# currently-rostered player checked (Diggs, Hill, Allen, Chubb,
# Garoppolo, Deebo Samuel Sr.) shows ACT/RES. These three real statuses
# are the ones that mean "not actually on an NFL roster" for our purpose.
NOT_CURRENTLY_ROSTERED_STATUSES = frozenset({"INA", "RET", "CUT"})
MODEL_STAT_COLUMNS = (
    "games",
    "attempts",
    "completions",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "passing_first_downs",
    "rushing_first_downs",
    "receiving_first_downs",
    "return_yards",
    "return_tds",
    "fumbles_lost",
)
ENGINE_SCORE_COLUMNS = (
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "receiving_yards",
    "receptions",
    "receiving_tds",
    "passing_first_downs",
    "rushing_first_downs",
    "receiving_first_downs",
    "return_yards",
    "return_tds",
    "fumbles_lost",
)
SOURCE_COLUMN_MAP = {
    "interceptions": "passing_interceptions",
    "return_yards": ("punt_return_yards", "kickoff_return_yards"),
    "return_tds": "special_teams_tds",
    "fumbles_lost": "fumbles_lost_total",
}
LAG_WEIGHTS = {1: 0.60, 2: 0.25, 3: 0.15}


@dataclass(frozen=True)
class ProjectionBuildResult:
    projections: pd.DataFrame
    blocked: pd.DataFrame
    identity: pd.DataFrame


def load_seasonal_history(raw_directory: str | Path, seasons: Iterable[int]) -> pd.DataFrame:
    """Load only the governed nflverse columns used by the transparent model."""
    raw_directory = Path(raw_directory)
    frames: list[pd.DataFrame] = []
    source_columns = {
        "player_id",
        "player_display_name",
        "player_name",
        "position",
        "recent_team",
        "season",
        "games",
        "attempts",
        "completions",
        "passing_yards",
        "passing_tds",
        "passing_interceptions",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "passing_first_downs",
        "rushing_first_downs",
        "receiving_first_downs",
        "punt_return_yards",
        "kickoff_return_yards",
        "special_teams_tds",
        "fumbles_lost_total",
    }
    for season in sorted(set(int(value) for value in seasons)):
        path = raw_directory / f"player_stats_seasonal_{season}.parquet"
        frame = pd.read_parquet(path)
        missing = sorted(source_columns.difference(frame.columns))
        if missing:
            raise ValueError(f"{path.name} is missing model columns: {', '.join(missing)}")
        frames.append(frame.loc[:, sorted(source_columns)].copy())
    history = pd.concat(frames, ignore_index=True)
    history = history[
        history["position"].isin(MODEL_POSITIONS)
        & history["player_id"].notna()
        & history["season"].notna()
    ].copy()
    history["season"] = history["season"].astype(int)
    history["games"] = pd.to_numeric(history["games"], errors="coerce").fillna(0.0)
    return history.sort_values(["season", "player_id"], kind="stable").reset_index(drop=True)


def build_current_projection_candidate(
    players: pd.DataFrame,
    history: pd.DataFrame,
    *,
    season: int,
    source_as_of: str,
    uncertainty_by_position: dict[str, float] | None = None,
    roster_status_by_gsis_id: Mapping[str, str] | None = None,
) -> ProjectionBuildResult:
    """Build a review-only forecast from exact current GSIS identities.

    Rookies and veterans with no recent NFL production remain blocked. No alias or fuzzy join is
    attempted. The result is deliberately not marked governed; owner governance is separate.

    `roster_status_by_gsis_id` is an optional, real, gsis_id-keyed cross-check (from the staged
    `seasonal_rosters` snapshot) used only to exclude real long-retired players from the
    `last_season == season - 1` widening below -- see `NOT_CURRENTLY_ROSTERED_STATUSES`. Omitting
    it (the default) reproduces the prior, unguarded widening exactly.
    """
    date.fromisoformat(source_as_of)
    required = {
        "gsis_id",
        "display_name",
        "position",
        "latest_team",
        "status",
        "rookie_season",
        "last_season",
    }
    missing = sorted(required.difference(players.columns))
    if missing:
        raise ValueError("Current player registry is missing: " + ", ".join(missing))
    # NWR class-time hardening, Diggs-class acquisition-gap fix (real,
    # root-caused: docs/codex/NWR_BROOKS_DIGGS_JUDKINS_ROOT_CAUSE_V1_20260908.md).
    # `last_season` is a STATS-based field on the real nflverse player
    # registry -- the most recent season a player has a real, RECORDED
    # stat line -- not a roster-membership field. A real, currently
    # active, rostered player (status=ACT) who missed the immediately
    # prior season entirely (injury, suspension, opt-out) has a
    # `last_season` that lags one real season behind, even though he is
    # genuinely eligible and about to play. `eq(season)` silently
    # excluded exactly this real case (verified: Stefon Diggs,
    # status=ACT, last_season=2025 in the real snapshot the 2026 build
    # reads, excluded from the 608-row admitted universe entirely).
    #
    # Minimum safe widening: accept `last_season` one real season
    # earlier too (`season - 1`), STILL gated by the real
    # `status.isin(("ACT","RES"))` check -- that status check is the
    # real safety valve against flooding the universe with retired/
    # inactive players (a retired player's real status is RET/INA/CUT/
    # etc., never ACT/RES, regardless of how recent his `last_season`
    # is). A genuinely stale historical player (`last_season` 2+ years
    # back) is still excluded either way. Verified via a real, direct
    # before/after audit against the real nflverse snapshot this build
    # actually reads -- see the fix's own test for the exact real counts.
    universe = players[
        players["last_season"].between(season - 1, season)
        & players["position"].isin(MODEL_POSITIONS)
        & players["status"].isin(("ACT", "RES"))
    ].copy()
    if roster_status_by_gsis_id:
        # Real false-positive guard (see NOT_CURRENTLY_ROSTERED_STATUSES above):
        # only ever removes rows from the newly-widened `last_season == season - 1`
        # slice -- the original `last_season == season` rows are unaffected, and a
        # gsis_id with no roster-snapshot entry is kept (missing coverage is not
        # treated as evidence of retirement).
        newly_widened = universe["last_season"].eq(season - 1)
        roster_status = universe["gsis_id"].astype(str).map(roster_status_by_gsis_id)
        stale_retired = newly_widened & roster_status.isin(NOT_CURRENTLY_ROSTERED_STATUSES)
        universe = universe.loc[~stale_retired].copy()
    universe = universe.sort_values(["position", "gsis_id"], kind="stable")
    prior = history[
        history["season"].between(season - 3, season - 1)
        & history["player_id"].isin(universe["gsis_id"])
    ].copy()
    projections: list[dict[str, object]] = []
    blocked: list[dict[str, object]] = []
    identity: list[dict[str, object]] = []
    uncertainty_by_position = uncertainty_by_position or {}
    history_by_player = {
        str(player_id): frame.copy() for player_id, frame in prior.groupby("player_id", sort=False)
    }
    for record in universe.to_dict("records"):
        player_id = str(record["gsis_id"])
        name = str(record["display_name"])
        position = str(record["position"])
        player_history = history_by_player.get(player_id, prior.iloc[0:0])
        is_rookie = int(record["rookie_season"] or 0) == season
        identity.append(
            {
                "player_id": player_id,
                "player_name": name,
                "position": position,
                "team": str(record["latest_team"]),
                "identity_status": "EXACT",
                "identity_source": "nflverse.players.gsis_id",
            }
        )
        reason = ""
        if is_rookie:
            reason = "2026 rookie workload is not governed; no NFL-history projection generated"
        elif not player_history["season"].eq(season - 1).any():
            reason = "no prior-season NFL stat line; persistence forecast blocked"
        elif float(player_history.loc[player_history["season"].eq(season - 1), "games"].sum()) <= 0:
            reason = "prior-season games are zero; persistence forecast blocked"
        if reason:
            blocked.append(
                {
                    "player_id": player_id,
                    "player_name": name,
                    "position": position,
                    "team": str(record["latest_team"]),
                    "rookie": is_rookie,
                    "reason": reason,
                }
            )
            continue
        row = _project_persistence(
            player_history,
            target_season=season,
            player_id=player_id,
            player_name=name,
            position=position,
            team=str(record["latest_team"]),
        )
        row.update(
            {
                "season": season,
                "source_id": MODEL_ID,
                "source_as_of": source_as_of,
                "source_status": "GOVERNANCE_PENDING",
                "evidence_status": "MODEL_VALIDATED_REVIEW_ONLY",
                "provenance": ("nflverse seasonal stats t-1 + current nflverse GSIS registry"),
                "rookie": False,
            }
        )
        reference_points = score_half_ppr(row)
        interval = float(uncertainty_by_position.get(position, max(25.0, 0.40 * reference_points)))
        row["projection_low"] = round(max(0.0, reference_points - interval), 4)
        row["projection_high"] = round(reference_points + interval, 4)
        row["availability_probability"] = round(float(row["games"]) / 17.0, 4)
        projections.append(row)
    projection_frame = pd.DataFrame(projections)
    # NWR class-time hardening: explicit `columns=` keeps `blocked_frame`/`identity_frame`
    # real DataFrames (with the columns `.sort_values` below needs) even when the roster-
    # status cross-check above empties `universe` entirely -- previously an unguarded
    # `pd.DataFrame([])` produced a columnless frame and `.sort_values(["position", ...])`
    # raised KeyError. Column order/content is unchanged for the non-empty case.
    blocked_frame = pd.DataFrame(
        blocked, columns=["player_id", "player_name", "position", "team", "rookie", "reason"]
    )
    identity_frame = pd.DataFrame(
        identity,
        columns=[
            "player_id",
            "player_name",
            "position",
            "team",
            "identity_status",
            "identity_source",
        ],
    )
    return ProjectionBuildResult(
        projections=_stable_projection_columns(projection_frame),
        blocked=blocked_frame.sort_values(["position", "player_id"], kind="stable"),
        identity=identity_frame.sort_values(["position", "player_id"], kind="stable"),
    )


def temporal_backtest(history: pd.DataFrame, *, seasons: Iterable[int]) -> pd.DataFrame:
    """Evaluate forecasts using only data available before each target season."""
    rows: list[dict[str, object]] = []
    for target_season in sorted(set(int(value) for value in seasons)):
        training = history[history["season"].lt(target_season)]
        lookback = training[training["season"].eq(target_season - 1)]
        actual = history[history["season"].eq(target_season)].set_index("player_id")
        latest = (
            lookback.sort_values(["season", "player_id"], kind="stable")
            .groupby("player_id", as_index=False)
            .tail(1)
        )
        lookback_by_player = {
            str(player_id): frame.copy()
            for player_id, frame in lookback.groupby("player_id", sort=False)
        }
        position_medians = {
            position: float(
                group.apply(lambda row: score_half_ppr(_actual_stat_row(row)), axis=1).median()
            )
            for position, group in lookback.groupby("position", sort=True)
        }
        predictions: list[dict[str, object]] = []
        for record in latest.to_dict("records"):
            player_id = str(record["player_id"])
            position = str(record["position"])
            player_history = lookback_by_player[player_id]
            if position not in MODEL_POSITIONS or float(player_history["games"].sum()) <= 0:
                continue
            prediction = _project_persistence(
                player_history,
                target_season=target_season,
                player_id=player_id,
                player_name=str(record.get("player_display_name") or record.get("player_name")),
                position=position,
                team=str(record.get("recent_team") or ""),
            )
            actual_row = actual.loc[player_id] if player_id in actual.index else None
            if isinstance(actual_row, pd.DataFrame):
                actual_row = actual_row.iloc[0]
            actual_points = (
                score_half_ppr(_actual_stat_row(actual_row)) if actual_row is not None else 0.0
            )
            predicted_points = score_half_ppr(prediction)
            baseline_points = position_medians[position]
            predictions.append(
                {
                    "season": target_season,
                    "player_id": player_id,
                    "position": position,
                    "predicted_points": predicted_points,
                    "actual_points": actual_points,
                    "baseline_points": baseline_points,
                    "absolute_error": abs(predicted_points - actual_points),
                    "baseline_absolute_error": abs(baseline_points - actual_points),
                }
            )
        frame = pd.DataFrame(predictions)
        if frame.empty:
            continue
        for position, group in frame.groupby("position", sort=True):
            rows.append(
                {
                    "season": target_season,
                    "position": position,
                    "player_count": len(group),
                    "model_mae": round(float(group["absolute_error"].mean()), 4),
                    "position_median_mae": round(float(group["baseline_absolute_error"].mean()), 4),
                    "mae_improvement": round(
                        float(
                            group["baseline_absolute_error"].mean() - group["absolute_error"].mean()
                        ),
                        4,
                    ),
                    "spearman": round(
                        float(
                            group["predicted_points"]
                            .rank(method="average")
                            .corr(group["actual_points"].rank(method="average"))
                        ),
                        4,
                    ),
                    "absolute_error_p80": round(float(group["absolute_error"].quantile(0.80)), 4),
                }
            )
    return pd.DataFrame(rows).sort_values(["season", "position"], kind="stable")


def uncertainty_from_backtest(backtest: pd.DataFrame) -> dict[str, float]:
    return {
        str(position): round(float(group["absolute_error_p80"].median()), 4)
        for position, group in backtest.groupby("position", sort=True)
    }


def score_half_ppr(row: dict[str, object] | pd.Series) -> float:
    def number(name: str) -> float:
        value = row.get(name, 0.0)
        return 0.0 if pd.isna(value) else float(value)

    value = 0.04 * number("passing_yards")
    value += 4.0 * number("passing_tds")
    value -= 2.0 * number("interceptions")
    value += 0.1 * number("rushing_yards")
    value += 6.0 * number("rushing_tds")
    value += 0.1 * number("receiving_yards")
    value += 0.5 * number("receptions")
    value += 6.0 * number("receiving_tds")
    value += 6.0 * number("return_tds")
    value -= 2.0 * number("fumbles_lost")
    return round(value, 4)


def _project_player(
    player_history: pd.DataFrame,
    population_history: pd.DataFrame,
    *,
    target_season: int,
    player_id: str,
    player_name: str,
    position: str,
    team: str,
    priors: dict[str, float] | None = None,
) -> dict[str, object]:
    lookback = player_history[
        player_history["season"].between(target_season - 3, target_season - 1)
    ].copy()
    priors = priors or _projection_priors(population_history, target_season, position)
    weighted_games = _weighted_average(lookback, "games", target_season, per_game=False)
    prior_games = priors["games"]
    total_games = float(lookback["games"].sum())
    reliability = min(1.0, total_games / 24.0)
    projected_games = reliability * weighted_games + (1.0 - reliability) * prior_games
    projected_games = round(min(17.0, max(1.0, projected_games)), 4)
    row: dict[str, object] = {
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "team": team,
        "games": projected_games,
    }
    for stat in MODEL_STAT_COLUMNS:
        if stat == "games":
            continue
        player_rate = _weighted_average(lookback, stat, target_season, per_game=True)
        prior_rate = priors[stat]
        projected_rate = reliability * player_rate + (1.0 - reliability) * prior_rate
        row[stat] = round(max(0.0, projected_rate * projected_games), 4)
    return row


def _project_persistence(
    player_history: pd.DataFrame,
    *,
    target_season: int,
    player_id: str,
    player_name: str,
    position: str,
    team: str,
) -> dict[str, object]:
    prior = player_history[player_history["season"].eq(target_season - 1)]
    if prior.empty:
        raise ValueError("Persistence projection requires a prior-season stat line.")
    last_row = prior.iloc[-1]
    values = _actual_stat_row(last_row)
    row: dict[str, object] = {
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "team": team,
    }
    row.update({stat: round(float(values[stat]), 4) for stat in MODEL_STAT_COLUMNS})
    return row


def _projection_priors(
    population_history: pd.DataFrame,
    target_season: int,
    position: str,
) -> dict[str, float]:
    population = population_history[
        population_history["season"].between(target_season - 3, target_season - 1)
        & population_history["position"].eq(position)
    ]
    priors = {"games": _position_prior(population, "games", target_season, per_game=False)}
    priors.update(
        {
            stat: _position_prior(population, stat, target_season, per_game=True)
            for stat in MODEL_STAT_COLUMNS
            if stat != "games"
        }
    )
    return priors


def _source_values(frame: pd.DataFrame, stat: str) -> pd.Series:
    source = SOURCE_COLUMN_MAP.get(stat, stat)
    if isinstance(source, tuple):
        values = sum(
            (pd.to_numeric(frame[column], errors="coerce").fillna(0.0) for column in source),
            start=pd.Series(0.0, index=frame.index),
        )
        return values
    return pd.to_numeric(frame[source], errors="coerce").fillna(0.0)


def _weighted_average(
    frame: pd.DataFrame,
    stat: str,
    target_season: int,
    *,
    per_game: bool,
) -> float:
    if frame.empty:
        return 0.0
    values = _source_values(frame, stat)
    games = pd.to_numeric(frame["games"], errors="coerce").fillna(0.0)
    if per_game:
        values = values.div(games.where(games.gt(0), np.nan)).fillna(0.0)
    weights = frame["season"].map(lambda value: LAG_WEIGHTS.get(target_season - int(value), 0.0))
    if per_game:
        weights = weights * games.clip(lower=0.0, upper=17.0)
    denominator = float(weights.sum())
    return 0.0 if denominator <= 0 else float((values * weights).sum() / denominator)


def _position_prior(
    population: pd.DataFrame,
    stat: str,
    target_season: int,
    *,
    per_game: bool,
) -> float:
    if population.empty:
        return 0.0
    latest = population[population["season"].eq(target_season - 1)].copy()
    if latest.empty:
        latest = population.copy()
    games = pd.to_numeric(latest["games"], errors="coerce").fillna(0.0)
    values = _source_values(latest, stat)
    if per_game:
        values = values.div(games.where(games.gt(0), np.nan)).fillna(0.0)
    return float(values.median())


def _actual_stat_row(row: pd.Series | None) -> dict[str, float]:
    if row is None:
        return {stat: 0.0 for stat in MODEL_STAT_COLUMNS}
    frame = pd.DataFrame([row])
    return {stat: float(_source_values(frame, stat).iloc[0]) for stat in MODEL_STAT_COLUMNS}


def _stable_projection_columns(frame: pd.DataFrame) -> pd.DataFrame:
    leading = [
        "player_id",
        "player_name",
        "position",
        "team",
        "season",
        "source_id",
        "source_as_of",
        "source_status",
        "evidence_status",
        "provenance",
        "rookie",
    ]
    trailing = ["projection_low", "projection_high", "availability_probability"]
    stable = frame.reindex(columns=leading + list(MODEL_STAT_COLUMNS) + trailing)
    if stable.empty:
        return stable
    return stable.sort_values(["position", "player_id"], kind="stable")
