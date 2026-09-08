"""TEAM_SCORE_V2_MULTI_LEAGUE -- the frozen, permanent, stable consumer
interface for the league-size-generalized Team Score model.

Frozen on the evidence in
docs/codex/NWR_TEAM_SCORE_V2_LEAGUE_GENERALIZATION_REPORT_20260905.md:
Architecture B (one shared latent-value ridge model on within-league-
population-percentile features + explicit team_count, with a
lightweight per-team_count linear recalibration) won on real,
season-clustered leave-one-season-out evidence at team_count in
{8, 10, 12, 16} -- including a genuine cross-team-count transport test
(a model that never saw a given team_count generalized to it AT LEAST
AS WELL AS a model fit specifically on that team_count's own data).

DO NOT MODIFY the frozen weights/calibration below without a new,
explicitly-authorized re-freeze -- this candidate is not to be tuned
further in this experiment.

**Live-draft design**: every raw feature is converted to a percentile
against a REAL simulated comparable-league population at the target
league's own team_count (`comparable_leagues`, from
`shadow_numeric_authorities_service.simulate_comparable_leagues()`) --
never a fixed, transplanted 4-team population. Building that
population is the expensive step; callers should build and cache it
ONCE per draft session (the same pattern the live product's own
`decision_bundle_service` already uses for `team_score()`'s
population), not once per pick.

**Live/offline feature parity (closed this pass)**: an earlier draft of
this module approximated `nwr_rank_sum`/`market_adp_percentile_sum`'s
comparable-league population from `all_roster_sum`'s ordering, since
`RosterPlayer` doesn't itself carry rank/ADP. That was a real gap, not
a fundamental one -- every comparable-league roster's `player_id` is a
real id from the same `pool`/ADP context the target roster uses, so
`build_feature_population()` now computes all four raw features
EXACTLY the same way for comparable-league rosters as for the target
roster. See `docs/codex/NWR_TEAM_SCORE_V2_LIVE_PARITY_REPORT_20260905.md`
for the parity tests proving this.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    optimal_starting_lineup_value,
)

TEAM_SCORE_V2_LABEL = "TEAM_SCORE_V2_MULTI_LEAGUE"
MODEL_VERSION = "team-score-v2-multi-league-20260905"

# Evidence-level taxonomy: no exact existing taxonomy for per-model
# historical-evidence classification was found in this codebase (the
# nearby ADMITTED_EVIDENCE_STATUSES / "NOT MODELED" conventions in
# redraft_engine_v1_service.py and shadow_numeric_authorities_service.py
# classify DATA admission and per-player scoring status, not model
# validation coverage) -- these names match the directive's own
# suggestion and the codebase's UPPER_SNAKE_CASE convention.
EVIDENCE_HISTORICALLY_VALIDATED = "HISTORICALLY_VALIDATED"
EVIDENCE_TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED = (
    "TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED"
)
EVIDENCE_DATA_LIMITED = "DATA_LIMITED"
EVIDENCE_UNSUPPORTED = "UNSUPPORTED"

# Frozen at docs/codex/NWR_TEAM_SCORE_V2_LEAGUE_GENERALIZATION_REPORT_20260905.md,
# fit on the real multi-league historical corpus (team_count in
# {8,10,12,16}, 2012-2023 development seasons, 2016/2024/2025 untouched).
FEATURE_NAMES: tuple[str, ...] = (
    "nwr_rank_sum_pctile", "optimal_lineup_pctile", "all_roster_sum_pctile",
    "market_adp_percentile_sum_pctile", "team_count",
)
RAW_FEATURE_NAMES: tuple[str, ...] = (
    "nwr_rank_sum", "optimal_lineup", "all_roster_sum", "market_adp_percentile_sum",
)
ALPHA: float = 1.0
SUPPORTED_TEAM_COUNTS: tuple[int, ...] = (8, 10, 12, 16)

# Placeholder container -- the real fitted values are loaded from the
# frozen artifact at import time by `_load_frozen()` below, keeping the
# single source of truth in one committed, versioned place rather than
# duplicating hand-typed floats that could silently drift.


class TeamScoreV2Error(ValueError):
    pass


def evidence_level_for(
    *, team_count: int, scoring_format: str, roster_matches_historical_shape: bool,
) -> str:
    """Classifies the real evidence level behind a Team Score V2 call for
    a given league configuration -- never claims PPR/Half-PPR or a
    non-historical roster shape carries the same evidence as the
    validated Non-PPR, `_HISTORICAL_ROSTER`-shaped, team_count in
    {8,10,12,16} configuration the frozen model was actually validated
    against. `roster_matches_historical_shape` should be True only when
    the league's roster exactly matches `_HISTORICAL_ROSTER` (1 QB/1
    RB/1 WR/1 TE/1 FLEX/1 bench, no K/DST) -- the only shape the
    multi-league corpus ever varied team_count against."""
    if team_count not in SUPPORTED_TEAM_COUNTS:
        return EVIDENCE_UNSUPPORTED
    if scoring_format != "Non-PPR" or not roster_matches_historical_shape:
        return EVIDENCE_TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED
    return EVIDENCE_HISTORICALLY_VALIDATED


@dataclass(frozen=True)
class TeamScoreV2Result:
    calibrated_score: float  # 0-100, calibrated for the SPECIFIC team_count supplied
    raw_prediction: float
    team_count: int
    raw_features: dict[str, float]
    normalized_features: dict[str, float]
    label: str = TEAM_SCORE_V2_LABEL


def _pool_value(entry: Mapping[str, object]) -> float:
    """NWR post-draft overnight (phase 1): a manual/unmodeled asset (K/DST,
    or a skill-position player NWR's ranking excluded but still keeps
    searchable/draftable via the manual pool) has `replacement_adjusted_value
    = None` by design -- there is no fabricated fallback score for them.
    Reuses the EXACT same semantic V1's `_roster_players`
    (shadow_numeric_authorities_service.py) already established for this
    same real gap: an unmodeled asset contributes 0.0 to a roster-value
    sum, never a crash, never an invented nonzero value. Team Score V2's
    raw-features builder previously had no such guard at all and raised
    `TypeError: float() argument must be a string or a real number, not
    'NoneType'` for any roster containing one -- reproduced live while
    running the RAV/DQ candidate-budget study (redraft_decision_bundle_v2
    against a real, already-manual-K/DST-carrying 403 roster)."""
    value = entry.get("replacement_adjusted_value")
    return float(value) if value is not None else 0.0


def _raw_features_for_roster(
    roster_player_ids: Sequence[str],
    pool: Mapping[str, Mapping[str, object]],
    profile: LeagueProfile,
    adp_percentile_by_player: Mapping[str, float],
) -> dict[str, float]:
    projected_players = [
        RosterPlayer(pid, str(pool[pid]["position"]), _pool_value(pool[pid]))
        for pid in roster_player_ids if pid in pool
    ]
    optimal_lineup = optimal_starting_lineup_value(projected_players, profile)
    all_roster_sum = sum(
        _pool_value(pool[pid]) for pid in roster_player_ids if pid in pool
    )
    nwr_rank_sum = sum(
        float(pool[pid]["nwr_rank"]) for pid in roster_player_ids
        if pid in pool and pool[pid].get("nwr_rank") is not None
    )
    market_adp_percentile_sum = sum(
        adp_percentile_by_player.get(pid, 0.0) for pid in roster_player_ids
    )
    return {
        "nwr_rank_sum": nwr_rank_sum, "optimal_lineup": optimal_lineup,
        "all_roster_sum": all_roster_sum, "market_adp_percentile_sum": market_adp_percentile_sum,
    }


def _percentile(value: float, population: Sequence[float]) -> float:
    if not population:
        return 0.0
    below = sum(1 for v in population if v < value)
    return 100.0 * below / len(population)


def build_feature_population(
    comparable_leagues: Sequence[Mapping[int, list[RosterPlayer]]],
    profile: LeagueProfile,
    pool: Mapping[str, Mapping[str, object]],
    adp_percentile_by_player: Mapping[str, float],
) -> dict[str, list[float]]:
    """The real population every roster's raw features are percentile-
    ranked against -- built once per draft session from a real
    `simulate_comparable_leagues()` call at the target league's own
    team_count, never transplanted from a different league size.

    EXACT for all four raw features, not an approximation: every
    comparable-league roster's `RosterPlayer.player_id` is a real
    player_id from the same `pool`/ADP context the target roster is
    scored against, so `nwr_rank_sum` and `market_adp_percentile_sum`
    are computed identically to how the target roster's own features
    are computed in `_raw_features_for_roster` -- there was never a
    genuine data barrier here, only an earlier oversight that this
    pass corrects (see the live-parity report's parity tests)."""
    population: dict[str, list[float]] = {name: [] for name in RAW_FEATURE_NAMES}
    for league in comparable_leagues:
        for roster in league.values():
            optimal_lineup = optimal_starting_lineup_value(roster, profile)
            all_roster_sum = sum(p.value for p in roster)
            nwr_rank_sum = sum(
                float(pool[p.player_id]["nwr_rank"]) for p in roster
                if p.player_id in pool and pool[p.player_id].get("nwr_rank") is not None
            )
            market_adp_percentile_sum = sum(
                adp_percentile_by_player.get(p.player_id, 0.0) for p in roster
            )
            population["optimal_lineup"].append(optimal_lineup)
            population["all_roster_sum"].append(all_roster_sum)
            population["nwr_rank_sum"].append(nwr_rank_sum)
            population["market_adp_percentile_sum"].append(market_adp_percentile_sum)
    return population


def compute_team_score_v2(
    roster_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, object]],
    *,
    team_count: int,
    feature_population: Mapping[str, list[float]],
    adp_percentile_by_player: Mapping[str, float],
    frozen_model: Mapping[str, object],
) -> TeamScoreV2Result:
    """The one, frozen, league-size-generalized Team Score V2 entry
    point. `feature_population` comes from `build_feature_population()`
    -- built once per draft session at the real target `team_count`,
    reused across every pick, never rebuilt per candidate (that would
    make live latency unacceptable)."""
    if team_count not in SUPPORTED_TEAM_COUNTS:
        raise TeamScoreV2Error(
            f"team_count={team_count} was not in the validated set {SUPPORTED_TEAM_COUNTS}; "
            "refusing to silently extrapolate."
        )
    pool = _asset_pool(ranking, manual_assets)
    raw = _raw_features_for_roster(roster_player_ids, pool, profile, adp_percentile_by_player)
    normalized = {
        f"{name}_pctile": _percentile(raw[name], feature_population.get(name, []))
        for name in RAW_FEATURE_NAMES
    }
    normalized["team_count"] = float(team_count)

    weights = frozen_model["weights"]
    means = frozen_model["feature_means"]
    stdevs = frozen_model["feature_stdevs"]
    raw_prediction = float(frozen_model["intercept"])
    for name in FEATURE_NAMES:
        mean, stdev = means[name], stdevs[name]
        standardized = (normalized[name] - mean) / stdev if stdev > 0 else 0.0
        raw_prediction += weights[name] * standardized

    calibration = frozen_model["calibration_by_team_count"][str(team_count)]
    calibrated = calibration["slope"] * raw_prediction + calibration["intercept"]
    calibrated = max(0.0, min(100.0, calibrated))
    return TeamScoreV2Result(
        calibrated_score=round(calibrated, 2), raw_prediction=round(raw_prediction, 2),
        team_count=team_count, raw_features={k: round(v, 2) for k, v in raw.items()},
        normalized_features={k: round(v, 2) for k, v in normalized.items()},
    )


def evaluate_team(
    roster_player_ids: Sequence[str],
    available_player_ids: Sequence[str],  # noqa: ARG001 -- reserved for future depth-aware features
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, object]],
    *,
    team_count: int,
    feature_population: Mapping[str, list[float]],
    adp_percentile_by_player: Mapping[str, float],
    frozen_model: Mapping[str, object],
) -> TeamScoreV2Result:
    """`evaluate_team(roster, available_players, league_config)`, per
    the owner's requested API shape -- `league_config` here is the
    caller's already-loaded `profile`/`team_count` pair, since this
    module never constructs a LeagueProfile itself."""
    return compute_team_score_v2(
        roster_player_ids, profile, ranking, manual_assets, team_count=team_count,
        feature_population=feature_population, adp_percentile_by_player=adp_percentile_by_player,
        frozen_model=frozen_model,
    )


def evaluate_candidate(
    current_roster_player_ids: Sequence[str],
    candidate_player_id: str,
    available_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, object]],
    *,
    team_count: int,
    feature_population: Mapping[str, list[float]],
    adp_percentile_by_player: Mapping[str, float],
    frozen_model: Mapping[str, object],
    scoring_format: str = "Non-PPR",
    roster_matches_historical_shape: bool = True,
) -> dict[str, object]:
    """`evaluate_candidate(current_roster, candidate, available_players,
    league_config, market_state)` -- `market_state` is
    `adp_percentile_by_player` here, since that is the one real market
    quantity this model consumes. Returns current/post-pick/delta plus
    the model version, this league's exact calibration parameters, and
    an honest evidence-level classification -- never silently implying
    full historical validation for a configuration that doesn't have
    it."""
    current = evaluate_team(
        current_roster_player_ids, available_player_ids, profile, ranking, manual_assets,
        team_count=team_count, feature_population=feature_population,
        adp_percentile_by_player=adp_percentile_by_player, frozen_model=frozen_model,
    )
    after_ids = (*current_roster_player_ids, candidate_player_id)
    after = evaluate_team(
        after_ids, available_player_ids, profile, ranking, manual_assets,
        team_count=team_count, feature_population=feature_population,
        adp_percentile_by_player=adp_percentile_by_player, frozen_model=frozen_model,
    )
    calibration = frozen_model["calibration_by_team_count"][str(team_count)]
    return {
        "candidate_player_id": candidate_player_id,
        "current_team_score": current.calibrated_score,
        "post_pick_team_score": after.calibrated_score,
        "team_score_delta": round(after.calibrated_score - current.calibrated_score, 2),
        "team_count": team_count,
        "model_version": MODEL_VERSION,
        "league_calibration": {
            "slope": calibration["slope"], "intercept": calibration["intercept"],
        },
        "evidence_level": evidence_level_for(
            team_count=team_count, scoring_format=scoring_format,
            roster_matches_historical_shape=roster_matches_historical_shape,
        ),
        "label": TEAM_SCORE_V2_LABEL,
    }


def mean_population(population: Mapping[str, list[float]], name: str) -> float | None:
    values = population.get(name)
    return round(statistics.fmean(values), 2) if values else None
