"""DecisionBundle V2 -- the historically-validated CHALLENGER layer
(NWR Big-Draft Readiness Overnight V1).

Composes `team_score_v2_multi_league_service` (frozen candidate commit
`d55bab2c14591172f662a09c627d90af551fa38a`, GREEN_2025_FINAL_HOLDOUT_PASSED)
and `championship_equity_v2_multi_league_service` on top of the existing,
live, already-tested `decision_bundle_service.build_decision_bundle()` --
this module NEVER re-runs a Monte Carlo simulation itself. Team Score V2 is
pure arithmetic over the real roster/pool/ADP state; Championship Equity V2
is pure arithmetic over the V1 bundle's own already-computed win
probabilities. Both are therefore cheap enough to compute for every
candidate on the real draft clock (see the latency report).

This is a strictly ADDITIVE, SHADOW/CHALLENGER bundle -- it does not modify,
replace, or retune `decision_bundle_service.py`/`decision_bundle_live_service.py`,
which remain the live, unmodified V1 authority. Pick Score / Cost of
Waiting / Make-It-Back / Player Score are carried through UNCHANGED from
the V1 bundle -- this program did not build (and explicitly declined to
rush, the night before a real draft) a live, real-time Raw Action Value V2 /
Pick Score V2 rollout pipeline; see
docs/codex/NWR_BIG_DRAFT_READINESS_OVERNIGHT_V1_REPORT_20260906.md for why.

Graceful degradation (directive section 11): if Team Score V2 or
Championship Equity V2 raises for ANY reason (e.g. an unsupported
team_count, a malformed frozen model, a missing feature), this module
NEVER lets that take down the underlying V1 bundle -- it returns the V1
bundle unchanged plus an explicit `v2_status` explaining what degraded and
why, never a fabricated V2 number and never a crash.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.services.championship_equity_v2_multi_league_service import (
    evaluate_candidate_equity,
)
from src.services.decision_bundle_service import DecisionBundle, build_decision_bundle
from src.services.redraft_draft_room_v1_service import AdpSnapshot, _asset_pool
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult, RosterSettings
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import RosterPlayer
from src.services.team_score_v2_multi_league_service import (
    MODEL_VERSION as TEAM_SCORE_V2_MODEL_VERSION,
)
from src.services.team_score_v2_multi_league_service import (
    SUPPORTED_TEAM_COUNTS,
    TEAM_SCORE_V2_LABEL,
    TeamScoreV2Error,
    build_feature_population,
    evaluate_candidate,
    evaluate_team,
    evidence_level_for,
)

DECISION_BUNDLE_V2_VERSION = "decision-bundle-v2-challenger-v1"

_FROZEN_MODELS_DIR = Path(__file__).resolve().parent.parent / "frozen_models"
_TEAM_SCORE_V2_FROZEN_MODEL_PATH = _FROZEN_MODELS_DIR / "team_score_v2_frozen_model.json"
_EQUITY_V2_FROZEN_MODEL_PATH = _FROZEN_MODELS_DIR / "championship_equity_v2_frozen_model.json"

# The exact roster shape the multi-league historical corpus validated
# Team Score V2 / Championship Equity V2 against (see
# scripts/run_historical_calibration_readiness_v1.py's `_HISTORICAL_ROSTER`
# on the research branch) -- 1 QB/1 RB/1 WR/1 TE/1 FLEX/1 bench, no K/DST,
# no Superflex. Real owner leagues essentially never match this exactly
# (they carry K/DST, deeper benches, etc.), so `roster_matches_historical_shape`
# will honestly be False for almost every real live league -- this is
# intentional, not a bug, and is why the evidence label for a real league
# is TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED rather than
# HISTORICALLY_VALIDATED.
_HISTORICAL_ROSTER_SHAPE = RosterSettings(
    qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=1
)


class DecisionBundleV2Unavailable(Exception):
    """Raised only for a real setup problem (e.g. a missing frozen-model
    file) that makes V2 entirely inoperable -- never for one candidate's
    degraded computation, which is instead reported per-candidate."""


def _load_frozen_model(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DecisionBundleV2Unavailable(
            f"Frozen model file missing or unreadable: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise DecisionBundleV2Unavailable(f"Frozen model file is not valid JSON: {path}") from exc


def roster_matches_historical_shape(roster: RosterSettings) -> bool:
    """True only when `roster` is byte-identical (every field) to the
    exact shape Team Score V2 / Championship Equity V2 were historically
    validated against. Never a fuzzy/approximate match."""
    return roster == _HISTORICAL_ROSTER_SHAPE


def scoring_format_label(reception_points: float) -> str:
    """Mirrors this codebase's existing Non-PPR/Half-PPR/PPR taxonomy
    (`_RECEPTION_POINTS_BY_SCORING_FORMAT` on the research branch) --
    anything else is honestly labeled Custom rather than misclassified."""
    if reception_points == 0.0:
        return "Non-PPR"
    if reception_points == 0.5:
        return "Half-PPR"
    if reception_points == 1.0:
        return "PPR"
    return "Custom"


def adp_percentile_by_player(adp: AdpSnapshot) -> dict[str, float]:
    """Real market-ADP percentile per player (0=worst/latest ADP,
    100=best/earliest ADP) -- the one real market feature Team Score V2
    consumes. Empty/unavailable ADP yields an empty mapping (never a
    fabricated 50.0 default); `_raw_features_for_roster` already treats a
    missing player as 0.0 contribution, so this degrades honestly."""
    if not adp.available or not adp.entries:
        return {}
    picks = [entry.expected_pick for entry in adp.entries]
    return {
        entry.player_id: 100.0 * sum(1 for p in picks if p > entry.expected_pick) / len(picks)
        for entry in adp.entries
    }


@dataclass(frozen=True)
class CandidateBundleV2:
    player_id: str
    team_score_v2: dict[str, Any] | None
    championship_equity_v2: dict[str, Any] | None
    v2_status: str  # "OK" | "DEGRADED: <reason>"


@dataclass(frozen=True)
class DecisionBundleV2:
    version: str
    v1_bundle: DecisionBundle
    current_team_score_v2: dict[str, Any] | None
    candidates: tuple[CandidateBundleV2, ...]
    team_count: int
    evidence_context: dict[str, Any]
    v2_status: str
    warnings: tuple[str, ...] = field(default_factory=tuple)


def build_decision_bundle_v2(
    *,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    owner_slot: int,
    current_owner_player_ids: Sequence[str],
    candidate_player_ids: Sequence[str],
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    provenance: ScoreProvenance,
    player_scores: Mapping[str, float] | None = None,
    from_state: Mapping[str, Any] | None = None,
    include_cost_of_waiting: bool = True,
    current_pick_number: int = 1,
    trials: int = 200,
    seasons: int = 200,
    base_seed: int = 20260903,
) -> DecisionBundleV2:
    """Builds the V1 bundle exactly as today (unchanged call), then
    augments it with Team Score V2 / Championship Equity V2. Never
    raises for a per-candidate or per-model degradation -- only
    `DecisionBundleV2Unavailable` (frozen-model file missing) can abort
    the whole call, matching `LiveDecisionBundleUnavailable`'s existing
    fail-explicit convention one level up."""
    v1_bundle = build_decision_bundle(
        profile=profile,
        ranking=ranking,
        manual_assets=manual_assets,
        adp=adp,
        owner_slot=owner_slot,
        current_owner_player_ids=current_owner_player_ids,
        candidate_player_ids=candidate_player_ids,
        comparable_leagues=comparable_leagues,
        provenance=provenance,
        player_scores=player_scores,
        from_state=from_state,
        include_cost_of_waiting=include_cost_of_waiting,
        current_pick_number=current_pick_number,
        trials=trials,
        seasons=seasons,
        base_seed=base_seed,
    )

    team_count = profile.team_count
    scoring_format = scoring_format_label(profile.scoring.reception)
    shape_match = roster_matches_historical_shape(profile.roster)
    evidence_context = {
        "team_count": team_count,
        "scoring_format": scoring_format,
        "roster_matches_historical_shape": shape_match,
        "team_score_v2_supported_team_counts": list(SUPPORTED_TEAM_COUNTS),
    }
    warnings: list[str] = []

    if team_count not in SUPPORTED_TEAM_COUNTS:
        return DecisionBundleV2(
            version=DECISION_BUNDLE_V2_VERSION,
            v1_bundle=v1_bundle,
            current_team_score_v2=None,
            candidates=(),
            team_count=team_count,
            evidence_context=evidence_context,
            v2_status=(
                f"DEGRADED: team_count={team_count} is outside the validated set "
                f"{sorted(SUPPORTED_TEAM_COUNTS)} -- V1 Team Score / Equity / Pick "
                "Score above remain fully available and unaffected."
            ),
            warnings=tuple(warnings),
        )

    try:
        ts_frozen = _load_frozen_model(_TEAM_SCORE_V2_FROZEN_MODEL_PATH)
        eq_frozen = _load_frozen_model(_EQUITY_V2_FROZEN_MODEL_PATH)
    except DecisionBundleV2Unavailable as exc:
        return DecisionBundleV2(
            version=DECISION_BUNDLE_V2_VERSION,
            v1_bundle=v1_bundle,
            current_team_score_v2=None,
            candidates=(),
            team_count=team_count,
            evidence_context=evidence_context,
            v2_status=f"DEGRADED: {exc} -- V1 Team Score / Equity / Pick Score above "
            "remain fully available and unaffected.",
            warnings=tuple(warnings),
        )

    pool = _asset_pool(ranking, manual_assets)
    adp_pct = adp_percentile_by_player(adp)
    feature_population = build_feature_population(comparable_leagues, profile, pool, adp_pct)

    try:
        current_result = evaluate_team(
            list(current_owner_player_ids),
            (),
            profile,
            ranking,
            manual_assets,
            team_count=team_count,
            feature_population=feature_population,
            adp_percentile_by_player=adp_pct,
            frozen_model=ts_frozen,
        )
        current_team_score_v2 = {
            "calibrated_score": current_result.calibrated_score,
            "team_count": team_count,
            "model_version": TEAM_SCORE_V2_MODEL_VERSION,
            "evidence_level": evidence_level_for(
                team_count=team_count,
                scoring_format=scoring_format,
                roster_matches_historical_shape=shape_match,
            ),
            "label": TEAM_SCORE_V2_LABEL,
        }
        overall_status = "OK"
    except (TeamScoreV2Error, KeyError, ZeroDivisionError) as exc:
        current_team_score_v2 = None
        overall_status = f"DEGRADED: current Team Score V2 failed ({exc}); V1 fields unaffected."
        warnings.append(overall_status)

    v1_by_player = {c.player_id: c for c in v1_bundle.candidates}
    candidates: list[CandidateBundleV2] = []
    for player_id in candidate_player_ids:
        if overall_status != "OK" or current_team_score_v2 is None:
            candidates.append(
                CandidateBundleV2(
                    player_id=player_id,
                    team_score_v2=None,
                    championship_equity_v2=None,
                    v2_status=overall_status,
                )
            )
            continue
        try:
            ts_candidate = evaluate_candidate(
                list(current_owner_player_ids),
                player_id,
                (),
                profile,
                ranking,
                manual_assets,
                team_count=team_count,
                feature_population=feature_population,
                adp_percentile_by_player=adp_pct,
                frozen_model=ts_frozen,
                scoring_format=scoring_format,
                roster_matches_historical_shape=shape_match,
            )
            v1_candidate = v1_by_player.get(player_id)
            post_pick_win_prob = (
                v1_candidate.championship_equity_after
                if v1_candidate is not None
                else v1_bundle.current_championship_equity.win_probability
            )
            eq_candidate = evaluate_candidate_equity(
                current_projected_win_probability=v1_bundle.current_championship_equity.win_probability,
                post_pick_projected_win_probability=post_pick_win_prob,
                current_team_score_v2=current_team_score_v2["calibrated_score"],
                post_pick_team_score_v2=ts_candidate["post_pick_team_score"],
                candidate_player_id=player_id,
                team_count=team_count,
                frozen_model=eq_frozen,
                scoring_format=scoring_format,
                roster_matches_historical_shape=shape_match,
            )
            candidates.append(
                CandidateBundleV2(
                    player_id=player_id,
                    team_score_v2=ts_candidate,
                    championship_equity_v2=eq_candidate,
                    v2_status="OK",
                )
            )
        except (TeamScoreV2Error, KeyError, ZeroDivisionError, ValueError) as exc:
            candidates.append(
                CandidateBundleV2(
                    player_id=player_id,
                    team_score_v2=None,
                    championship_equity_v2=None,
                    v2_status=f"DEGRADED: {exc}",
                )
            )

    return DecisionBundleV2(
        version=DECISION_BUNDLE_V2_VERSION,
        v1_bundle=v1_bundle,
        current_team_score_v2=current_team_score_v2,
        candidates=tuple(candidates),
        team_count=team_count,
        evidence_context=evidence_context,
        v2_status=overall_status,
        warnings=tuple(warnings),
    )
