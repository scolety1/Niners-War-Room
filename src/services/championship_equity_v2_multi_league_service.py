"""CHAMPIONSHIP_EQUITY_V2_MULTI_LEAGUE -- the frozen, stable consumer
interface for the league-size-generalized Championship Equity model.

Frozen on the evidence in
docs/codex/NWR_CHAMPIONSHIP_EQUITY_V2_MULTI_LEAGUE_REPORT_20260906.md:
a single shared ridge model on raw (projected_win_probability,
team_score_v2_calibrated, team_count) -> oracle_win_probability
directly, plus a light per-team_count linear recalibration, validated
via leave-one-season-out AND a genuine leave-one-team-count-out
transport test at team_count in {8, 10, 12, 16}.

**Honest, disclosed split finding this model is built on** (do not
overstate): Team Score V2 decisively improves this model's absolute
CALIBRATION (2x-5x lower MAE than raw `championship_equity()` alone at
every team_count) but does NOT clearly improve RANKING beyond the raw
baseline -- both are reported via `ranking_evidence`/
`calibration_evidence` fields below, never collapsed into one
undifferentiated "improved" claim.

DO NOT MODIFY the frozen weights/calibration below without a new,
explicitly-authorized re-freeze.

This module NEVER calls `championship_equity()`'s own Monte Carlo
simulator itself -- callers must supply the real `projected_win_
probability` (from `shadow_numeric_authorities_service.
championship_equity()`, already computed) and the real Team Score V2
calibrated score (from `team_score_v2_multi_league_service.
evaluate_team()`), matching this codebase's standing convention that
each layer composes previously-validated real outputs rather than
recomputing them.
"""

from __future__ import annotations

from collections.abc import Mapping

CHAMPIONSHIP_EQUITY_V2_LABEL = "CHAMPIONSHIP_EQUITY_V2_MULTI_LEAGUE"
MODEL_VERSION = "championship-equity-v2-multi-league-20260906"

SUPPORTED_TEAM_COUNTS = frozenset({8, 10, 12, 16})

HISTORICALLY_VALIDATED = "HISTORICALLY_VALIDATED"
TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED = "TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED"
UNSUPPORTED = "UNSUPPORTED"


class ChampionshipEquityV2Error(ValueError):
    pass


def evidence_level_for(
    *, team_count: int, scoring_format: str, roster_matches_historical_shape: bool,
) -> str:
    if team_count not in SUPPORTED_TEAM_COUNTS:
        return UNSUPPORTED
    if scoring_format != "Non-PPR" or not roster_matches_historical_shape:
        return TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED
    return HISTORICALLY_VALIDATED


def compute_championship_equity_v2(
    *, projected_win_probability: float, team_score_v2_calibrated: float,
    team_count: int, frozen_model: Mapping[str, object],
) -> float:
    """The one shared ridge model's raw prediction, standardized then
    recalibrated per `team_count` -- identical arithmetic to the frozen
    Team Score V2 pattern (standardize with the frozen means/stdevs,
    weighted sum + intercept, then a per-team_count affine
    recalibration), reused deliberately rather than re-derived."""
    if team_count not in SUPPORTED_TEAM_COUNTS:
        raise ChampionshipEquityV2Error(
            f"team_count={team_count} is not supported. Supported: {sorted(SUPPORTED_TEAM_COUNTS)}."
        )
    raw_features = {
        "projected_win_probability": projected_win_probability,
        "team_score_v2_calibrated": team_score_v2_calibrated,
        "team_count": float(team_count),
    }
    means = frozen_model["feature_means"]
    stdevs = frozen_model["feature_stdevs"]
    weights = frozen_model["weights"]
    raw = float(frozen_model["intercept"])
    for name in frozen_model["feature_names"]:
        mean, stdev = means[name], stdevs[name]
        standardized = (raw_features[name] - mean) / stdev if stdev > 0 else 0.0
        raw += weights[name] * standardized
    calibration = frozen_model["calibration_by_team_count"][str(team_count)]
    calibrated = calibration["slope"] * raw + calibration["intercept"]
    return max(0.0, min(1.0, round(calibrated, 4)))


def evaluate_candidate_equity(
    *,
    current_projected_win_probability: float,
    post_pick_projected_win_probability: float,
    current_team_score_v2: float,
    post_pick_team_score_v2: float,
    candidate_player_id: str,
    team_count: int,
    frozen_model: Mapping[str, object],
    scoring_format: str = "Non-PPR",
    roster_matches_historical_shape: bool = True,
) -> dict[str, object]:
    """Current/post-pick/delta calibrated Championship Equity for one
    candidate, given already-computed real `championship_equity()` and
    Team Score V2 outputs for both roster states -- this function never
    runs a new Monte Carlo simulation itself."""
    current = compute_championship_equity_v2(
        projected_win_probability=current_projected_win_probability,
        team_score_v2_calibrated=current_team_score_v2,
        team_count=team_count, frozen_model=frozen_model,
    )
    after = compute_championship_equity_v2(
        projected_win_probability=post_pick_projected_win_probability,
        team_score_v2_calibrated=post_pick_team_score_v2,
        team_count=team_count, frozen_model=frozen_model,
    )
    return {
        "candidate_player_id": candidate_player_id,
        "current_championship_equity": current,
        "post_pick_championship_equity": after,
        "championship_equity_delta": round(after - current, 4),
        "team_count": team_count,
        "model_version": MODEL_VERSION,
        "evidence_level": evidence_level_for(
            team_count=team_count, scoring_format=scoring_format,
            roster_matches_historical_shape=roster_matches_historical_shape,
        ),
        "ranking_evidence": (
            "NOT DECISIVE -- augmenting the raw baseline with Team Score V2 did not "
            "clearly improve ranking (Spearman) over championship_equity() alone in "
            "the historical validation. See NWR_CHAMPIONSHIP_EQUITY_V2_MULTI_LEAGUE_REPORT."
        ),
        "calibration_evidence": (
            "DECISIVE -- this model's calibrated probability carries 2x-5x lower "
            "absolute error against the real outcome oracle than the raw baseline "
            "alone, at every validated team_count."
        ),
        "label": CHAMPIONSHIP_EQUITY_V2_LABEL,
    }
