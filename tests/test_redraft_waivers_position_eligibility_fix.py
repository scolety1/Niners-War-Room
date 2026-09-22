from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RosterSettings,
    ScoringSettings,
)
from src.services.waiver_engine_service import rank_waiver_candidates


def test_dst_is_never_recommended_when_the_league_has_no_dst_slot() -> None:
    profile = LeagueProfile(
        "no-dst",
        "No DST League",
        2026,
        10,
        RosterSettings(qb=1, rb=2, wr=3, te=1, flex=2, k=1, dst=0, bench_size=14),
        ScoringSettings(reception=0),
        DraftContext(rounds=24, draft_slot=1),
        provider="sleeper",
        provider_league_id="league-1",
    )
    ranking = RankingResult(profile, (), (), (), "2026-09-22T00:00:00+00:00", "fixture")
    free_agents = (
        {
            "sleeperPlayerId": "JAX",
            "playerId": "",
            "playerName": "Jacksonville Jaguars",
            "position": "DST",
            "team": "JAX",
            "overallRank": None,
            "replacementAdjustedValue": None,
        },
    )

    candidates = rank_waiver_candidates(
        free_agents=free_agents,
        owner_roster_canonical_ids=(),
        profile=profile,
        ranking=ranking,
        manual_assets=(),
        mode="REST_OF_SEASON",
    )

    assert candidates == ()
