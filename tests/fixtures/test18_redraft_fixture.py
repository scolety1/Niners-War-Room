"""Deterministic Test 18 draft-state fixture.

The names and owner picks are evidence fixtures only.  No production policy
or score path keys off any player name, round, or position count here.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from src.services.redraft_draft_room_v1_service import AdpSnapshot, draft_order
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)

TEST18_OWNER_SLOT = 5
TEST18_WR_MAXIMUM = 8

TEST18_OWNER_PICKS_THROUGH_ROUND_13 = (
    ("christian-mccaffrey", "Christian McCaffrey", "RB"),
    ("trey-mcbride", "Trey McBride", "TE"),
    ("chris-olave", "Chris Olave", "WR"),
    ("zay-flowers", "Zay Flowers", "WR"),
    ("josh-jacobs", "Josh Jacobs", "RB"),
    ("matthew-stafford", "Matthew Stafford", "QB"),
    ("michael-wilson", "Michael Wilson", "WR"),
    ("wandale-robinson", "Wan'Dale Robinson", "WR"),
    ("courtland-sutton", "Courtland Sutton", "WR"),
    ("trevor-lawrence", "Trevor Lawrence", "QB"),
    ("keenan-allen", "Keenan Allen", "WR"),
    ("jakobi-meyers", "Jakobi Meyers", "WR"),
    ("jauan-jennings", "Jauan Jennings", "WR"),
)

TEST18_R14_AVAILABLE = (
    ("troy-franklin", "Troy Franklin", "WR"),
    ("romeo-doubs", "Romeo Doubs", "WR"),
    ("kyler-murray", "Kyler Murray", "QB"),
    ("legal-rb", "Legal Running Back", "RB"),
    ("legal-te", "Legal Tight End", "TE"),
)


def make_test18_profile(*, wr_maximum: int | None) -> LeagueProfile:
    limits = {} if wr_maximum is None else {"WR": wr_maximum}
    return LeagueProfile(
        profile_id="test18",
        league_name="Pittsburgh Pro H2H Points PPR League",
        season=2026,
        team_count=10,
        roster=RosterSettings(
            qb=1,
            rb=2,
            wr=2,
            te=1,
            flex=1,
            superflex=0,
            k=1,
            dst=1,
            bench_size=7,
        ),
        scoring=ScoringSettings(reception=1.0),
        draft=DraftContext(
            rounds=16,
            draft_slot=TEST18_OWNER_SLOT,
            roster_limits=limits,
        ),
        provider="local",
    )


def make_test18_ranking(profile: LeagueProfile) -> RankingResult:
    # Franklin and Doubs intentionally lead the rank order.  This mirrors
    # the observed R14 Suggestions rows while keeping production logic free
    # of named-player treatment.
    players = (*TEST18_R14_AVAILABLE, *TEST18_OWNER_PICKS_THROUGH_ROUND_13)
    rows = tuple(
        RedraftRankingRow(
            overall_rank=index,
            position_rank=index,
            player_id=player_id,
            player_name=name,
            position=position,
            team="TST",
            projected_points=300.0 - index,
            replacement_points=0.0,
            replacement_adjusted_value=300.0 - index,
            starter_gap=0.0,
            confidence="HIGH",
            tier=1,
            profile_id=profile.profile_id,
            profile_name=profile.league_name,
            source_status="GOVERNED",
            evidence_status="AVAILABLE",
            source_as_of="2026-09-08",
            rookie=False,
        )
        for index, (player_id, name, position) in enumerate(players, start=1)
    )
    return RankingResult(
        profile=profile,
        rows=rows,
        replacement_levels=(),
        blocked_rows=(),
        generated_at_utc="2026-09-08T23:38:00-06:00",
        projection_sha256="test18-fixture",
    )


def make_test18_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(profile.profile_id, "", "ppr", 10, "", "", "", (), ())


def make_test18_room_state_at_14_06() -> dict[str, object]:
    """Return the state immediately before overall pick 136 (14.06)."""
    order = draft_order(make_test18_profile(wr_maximum=None))
    owner_by_round = {
        round_number: pick
        for round_number, pick in enumerate(TEST18_OWNER_PICKS_THROUGH_ROUND_13, start=1)
    }
    picks: list[dict[str, object]] = []
    # Pick 135 is 14.05; 14.06 (owner slot 5 in an even snake round) is next.
    for pick_number, team_slot in enumerate(order[:135], start=1):
        round_number = ((pick_number - 1) // 10) + 1
        owner_pick = team_slot == TEST18_OWNER_SLOT and round_number <= 13
        if owner_pick:
            player_id, player_name, position = owner_by_round[round_number]
        else:
            player_id = f"opponent-{pick_number}"
            player_name = f"Opponent Pick {pick_number}"
            position = "RB"
        picks.append(
            {
                "pick_number": pick_number,
                "round": round_number,
                "team_slot": team_slot,
                "player_id": player_id,
                "player_name": player_name,
                "position": position,
                "team": "TST",
            }
        )
    return {
        "schema_version": 1,
        "profile_id": "test18",
        "owner_slot": TEST18_OWNER_SLOT,
        "seed": 20260908,
        "speed": "FAST",
        "mode": "LIVE_READ_ONLY",
        "drafted": [pick["player_id"] for pick in picks],
        "picks": picks,
        "updated_at_utc": "2026-09-09T00:00:00-06:00",
    }


def captured_candidate_bundle(candidate_ids: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        candidates=tuple(SimpleNamespace(player_id=player_id) for player_id in candidate_ids)
    )


def with_profile(ranking: RankingResult, profile: LeagueProfile) -> RankingResult:
    return replace(ranking, profile=profile)
