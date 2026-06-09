from __future__ import annotations

from dataclasses import dataclass

from src.models.confidence import ConfidenceInputs, confidence_score
from src.utils.scoring import clamp_score


@dataclass(frozen=True)
class KeeperScoreInputs:
    player_id: str
    player_name: str
    position: str
    private_score: float
    official_rank: int | None = None
    market_score: float | None = None
    my_rank_score: float | None = None
    confidence_score: float = 0.6
    roster_status: str = "rostered"
    long_term_private_value: float | None = None
    next_2_year_starter_value: float | None = None
    scarcity_bonus: float | None = None
    trade_liquidity: float | None = None
    age_curve: float | None = None
    risk_adj: float | None = None
    build_fit: float | None = None
    roster_redundancy: float = 0.0
    decline_risk: float = 0.0
    data_completeness: float | None = None
    historical_cohort_size: float | None = None
    market_agreement: float | None = None
    model_separation: float | None = None


@dataclass(frozen=True)
class KeeperDecision:
    player_id: str
    player_name: str
    position: str
    official_rank: int | None
    keeper_score: float
    drop_candidate_score: float
    confidence_score: float
    top_five_shield_eligible: bool


@dataclass(frozen=True)
class KeeperPressure:
    team_id: str
    team_name: str
    roster_count: int
    protect_limit: int
    official_top_five_count: int
    forced_release_count: int
    pressure_count: int
    pressure_level: str


def keeper_score(inputs: KeeperScoreInputs) -> float:
    # Market/trade liquidity is intentionally excluded here. It belongs in
    # trade value and market-edge views, not private keeper value.
    score = (
        (0.32 * _score_component(inputs.long_term_private_value))
        + (0.22 * _score_component(inputs.next_2_year_starter_value))
        + (0.16 * _score_component(inputs.scarcity_bonus))
        + (0.11 * _score_component(inputs.age_curve))
        + (0.12 * _score_component(inputs.risk_adj))
        + (0.07 * _score_component(inputs.build_fit))
    )
    return round(clamp_score(score), 2)


def drop_candidate_score(
    inputs: KeeperScoreInputs,
    keeper_score_value: float | None = None,
) -> float:
    score = keeper_score(inputs) if keeper_score_value is None else keeper_score_value
    private_cut_risk = 100 - clamp_score(inputs.private_score)
    drop_score = (
        (0.45 * (100 - score))
        + (0.25 * private_cut_risk)
        + (0.15 * clamp_score(inputs.roster_redundancy))
        + (0.15 * clamp_score(inputs.decline_risk))
    )
    return round(clamp_score(drop_score), 2)


def keeper_decision(
    inputs: KeeperScoreInputs,
    *,
    is_forced_release_candidate: bool = False,
    is_top_five_shield_eligible: bool = False,
    roster_bubble_penalty: float = 0.0,
) -> KeeperDecision:
    _ = is_forced_release_candidate, roster_bubble_penalty
    score = keeper_score(inputs)
    return KeeperDecision(
        player_id=inputs.player_id,
        player_name=inputs.player_name,
        position=inputs.position,
        official_rank=inputs.official_rank,
        keeper_score=score,
        drop_candidate_score=drop_candidate_score(inputs, score),
        confidence_score=confidence_score(
            ConfidenceInputs(
                data_completeness=_confidence_component(inputs.data_completeness),
                historical_cohort_size=_confidence_component(
                    inputs.historical_cohort_size
                ),
                market_agreement=_confidence_component(inputs.market_agreement),
                model_separation=_confidence_component(inputs.model_separation),
            )
        ),
        top_five_shield_eligible=is_top_five_shield_eligible,
    )


def official_top_five(players: list[KeeperScoreInputs]) -> list[KeeperScoreInputs]:
    ranked_players = [
        player
        for player in players
        if player.official_rank is not None
    ]
    return sorted(
        ranked_players,
        key=lambda player: (player.official_rank or 999, player.player_name),
    )[:5]


def best_23_keepers(
    decisions: list[KeeperDecision], protect_limit: int = 23
) -> list[KeeperDecision]:
    return sorted(
        decisions,
        key=lambda decision: (
            -decision.keeper_score,
            decision.official_rank if decision.official_rank is not None else 999,
            decision.player_name,
        ),
    )[:protect_limit]


def forced_release_candidates(
    players: list[KeeperScoreInputs],
    *,
    official_top_five_keep_limit: int = 4,
) -> list[KeeperScoreInputs]:
    top_five = official_top_five(players)
    release_count = max(0, len(top_five) - official_top_five_keep_limit)
    if release_count == 0:
        return []
    return sorted(
        top_five,
        key=lambda player: (
            -drop_candidate_score(player),
            keeper_score(player),
            player.official_rank if player.official_rank is not None else 999,
            player.player_name,
        ),
    )[:release_count]


def top_five_shield_eligibility(
    player: KeeperScoreInputs,
    forced_release_player_ids: set[str],
    *,
    official_top_five_player_ids: set[str] | None = None,
    minimum_keeper_score: float = 70.0,
) -> bool:
    if official_top_five_player_ids is None:
        is_official_top_five = player.official_rank is not None and player.official_rank <= 5
    else:
        is_official_top_five = player.player_id in official_top_five_player_ids

    if not is_official_top_five:
        return False
    if player.player_id in forced_release_player_ids:
        return False
    return keeper_score(player) >= minimum_keeper_score


def keeper_pressure(
    team_id: str,
    team_name: str,
    roster_count: int,
    official_top_five_count: int,
    *,
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> KeeperPressure:
    forced_release_count = max(0, official_top_five_count - official_top_five_keep_limit)
    pressure_count = max(0, roster_count - protect_limit) + forced_release_count
    if pressure_count >= 3:
        pressure_level = "high"
    elif pressure_count >= 1:
        pressure_level = "medium"
    else:
        pressure_level = "low"

    return KeeperPressure(
        team_id=team_id,
        team_name=team_name,
        roster_count=roster_count,
        protect_limit=protect_limit,
        official_top_five_count=official_top_five_count,
        forced_release_count=forced_release_count,
        pressure_count=pressure_count,
        pressure_level=pressure_level,
    )


def _score_component(value: float | None) -> float:
    return clamp_score(0.0 if value is None else value)


def _confidence_component(value: float | None) -> float:
    return clamp_score(0.0 if value is None else value, 0.0, 1.0)
