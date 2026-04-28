from __future__ import annotations

from dataclasses import dataclass

from src.models.player_scores import official_rank_score
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
    market = inputs.market_score if inputs.market_score is not None else inputs.private_score
    my_rank = inputs.my_rank_score if inputs.my_rank_score is not None else inputs.private_score
    official = official_rank_score(inputs.official_rank)
    confidence_bonus = (clamp_score(inputs.confidence_score, 0.0, 1.0) - 0.5) * 8

    score = (
        (0.46 * clamp_score(inputs.private_score))
        + (0.22 * clamp_score(market))
        + (0.20 * official)
        + (0.12 * clamp_score(my_rank))
        + confidence_bonus
    )
    return round(clamp_score(score), 2)


def drop_candidate_score(
    score: float,
    *,
    is_forced_release_candidate: bool = False,
    roster_bubble_penalty: float = 0.0,
) -> float:
    forced_release_penalty = 18.0 if is_forced_release_candidate else 0.0
    return round(clamp_score((100 - score) + forced_release_penalty + roster_bubble_penalty), 2)


def keeper_decision(
    inputs: KeeperScoreInputs,
    *,
    is_forced_release_candidate: bool = False,
    is_top_five_shield_eligible: bool = False,
    roster_bubble_penalty: float = 0.0,
) -> KeeperDecision:
    score = keeper_score(inputs)
    return KeeperDecision(
        player_id=inputs.player_id,
        player_name=inputs.player_name,
        position=inputs.position,
        official_rank=inputs.official_rank,
        keeper_score=score,
        drop_candidate_score=drop_candidate_score(
            score,
            is_forced_release_candidate=is_forced_release_candidate,
            roster_bubble_penalty=roster_bubble_penalty,
        ),
        confidence_score=round(clamp_score(inputs.confidence_score, 0.0, 1.0), 3),
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
