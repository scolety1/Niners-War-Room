from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.models.keeper_scores import (
    KeeperDecision,
    KeeperPressure,
    KeeperScoreInputs,
    best_23_keepers,
    forced_release_candidates,
    keeper_decision,
    keeper_pressure,
    official_top_five,
    top_five_shield_eligibility,
)


@dataclass(frozen=True)
class TeamKeeperBoard:
    team_id: str
    team_name: str
    official_top_five: list[KeeperScoreInputs]
    forced_release_candidates: list[KeeperScoreInputs]
    best_keepers: list[KeeperDecision]
    decisions: list[KeeperDecision]
    pressure: KeeperPressure


def build_team_keeper_board(
    players: list[KeeperScoreInputs],
    *,
    team_id: str = "niners",
    team_name: str = "Niners",
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> TeamKeeperBoard:
    top_five = official_top_five(players)
    forced_players = forced_release_candidates(
        players,
        official_top_five_keep_limit=official_top_five_keep_limit,
    )
    forced_ids = {player.player_id for player in forced_players}
    top_five_ids = {player.player_id for player in top_five}
    decisions = [
        keeper_decision(
            player,
            is_forced_release_candidate=player.player_id in forced_ids,
            is_top_five_shield_eligible=top_five_shield_eligibility(
                player,
                forced_ids,
                official_top_five_player_ids=top_five_ids,
            ),
        )
        for player in players
    ]
    return TeamKeeperBoard(
        team_id=team_id,
        team_name=team_name,
        official_top_five=top_five,
        forced_release_candidates=forced_players,
        best_keepers=best_23_keepers(decisions, protect_limit),
        decisions=sorted(decisions, key=lambda decision: -decision.keeper_score),
        pressure=keeper_pressure(
            team_id,
            team_name,
            len(players),
            len(top_five),
            protect_limit=protect_limit,
            official_top_five_keep_limit=official_top_five_keep_limit,
        ),
    )


def load_team_keeper_board(
    connection: sqlite3.Connection,
    team_id: str = "niners",
    *,
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> TeamKeeperBoard:
    rows = connection.execute(
        """
        SELECT
            r.team_id,
            r.team_name,
            r.player_id,
            r.player_name,
            r.position,
            r.roster_status,
            COALESCE(r.league_rank, o.league_rank, r.official_rank, o.official_rank)
                AS official_rank,
            m.private_score,
            m.market_score,
            m.keeper_score,
            m.confidence_score
        FROM rosters r
        LEFT JOIN official_rankings o ON o.player_id = r.player_id
        LEFT JOIN model_outputs m ON m.player_id = r.player_id
        WHERE r.team_id = ?
        """,
        (team_id,),
    ).fetchall()
    players = [_row_to_keeper_input(row) for row in rows]
    team_name = str(rows[0]["team_name"]) if rows else team_id
    return build_team_keeper_board(
        players,
        team_id=team_id,
        team_name=team_name,
        protect_limit=protect_limit,
        official_top_five_keep_limit=official_top_five_keep_limit,
    )


def _row_to_keeper_input(row: sqlite3.Row) -> KeeperScoreInputs:
    private_score = row["private_score"] if row["private_score"] is not None else 50.0
    formula_value = row["keeper_score"] if row["keeper_score"] is not None else private_score
    confidence_score = row["confidence_score"] if row["confidence_score"] is not None else 0.6
    return KeeperScoreInputs(
        player_id=str(row["player_id"]),
        player_name=str(row["player_name"]),
        position=str(row["position"]),
        official_rank=row["official_rank"],
        private_score=float(private_score),
        market_score=_optional_float(row["market_score"]),
        confidence_score=float(confidence_score),
        roster_status=str(row["roster_status"] or "rostered"),
        long_term_private_value=float(formula_value),
        next_2_year_starter_value=float(formula_value),
        scarcity_bonus=float(formula_value),
        trade_liquidity=float(formula_value),
        age_curve=float(formula_value),
        risk_adj=float(formula_value),
        build_fit=float(formula_value),
        data_completeness=float(confidence_score),
        historical_cohort_size=float(confidence_score),
        market_agreement=float(confidence_score),
        model_separation=float(confidence_score),
    )


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
