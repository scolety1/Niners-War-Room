from dataclasses import replace

from src.services.current_player_status_overrides_service import (
    StatusOverride,
    apply_status_overrides_to_ranking,
    load_status_overrides,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)


def _row(player_id, name, position, team, value, projected, rank) -> RedraftRankingRow:
    return RedraftRankingRow(
        rank, 1, player_id, name, position, team, projected, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-08", False,
    )


def _ranking() -> RankingResult:
    rows = (
        _row("A", "Player A", "WR", "NE", 50.0, 200.0, 1),
        _row("B", "Player B", "WR", "SF", 40.0, 180.0, 2),
        _row("C", "Player C", "WR", "DAL", 30.0, 160.0, 3),
    )
    profile = LeagueProfile(
        "fixture", "Fixture", 2026, 10, RosterSettings(), ScoringSettings(),
        DraftContext(rounds=16),
    )
    return RankingResult(profile, rows, (), (), "2026-08-08T00:00:00Z", "fixture")


def test_load_status_overrides_reads_the_real_committed_file() -> None:
    overrides = load_status_overrides(".")
    kinds = {o.player_id: o.kind for o in overrides}
    assert kinds.get("00-0040130") == "SEASON_OUT"
    assert kinds.get("00-0038608") == "TEAM_CORRECTION"
    for override in overrides:
        assert override.sources, f"{override.player_id} has no cited source"


def test_season_out_override_zeros_value_but_keeps_player_searchable() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="B", player_name="Player B", kind="SEASON_OUT",
            reason="test", effective_date="2026-08-19", verified_at_utc="2026-09-07T00:00:00Z",
            sources=("https://example.test/source",),
        ),
    )
    corrected = apply_status_overrides_to_ranking(ranking, overrides)
    row = next(r for r in corrected.rows if r.player_id == "B")
    assert row.replacement_adjusted_value == 0.0
    # Never removed -- still present and still findable by search/name.
    assert row.player_name == "Player B"
    assert {r.player_id for r in corrected.rows} == {"A", "B", "C"}
    # Sinks to the bottom of the re-derived rank order (worst value now).
    assert row.overall_rank == 3


def test_team_correction_override_only_touches_team() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="A", player_name="Player A", kind="TEAM_CORRECTION",
            corrected_team="HOU", reason="test", effective_date="2026-08-25",
            verified_at_utc="2026-09-07T00:00:00Z", sources=("https://example.test/source",),
        ),
    )
    corrected = apply_status_overrides_to_ranking(ranking, overrides)
    row = next(r for r in corrected.rows if r.player_id == "A")
    assert row.team == "HOU"
    # Value/rank untouched -- a team correction never changes valuation.
    assert row.replacement_adjusted_value == 50.0
    assert row.overall_rank == 1


def test_no_matching_override_leaves_ranking_byte_identical() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="ZZZ-not-in-ranking", player_name="Nobody", kind="SEASON_OUT",
            reason="test", effective_date="2026-08-19", verified_at_utc="2026-09-07T00:00:00Z",
            sources=("https://example.test/source",),
        ),
    )
    assert apply_status_overrides_to_ranking(ranking, overrides) == ranking


def test_empty_overrides_is_a_true_no_op() -> None:
    ranking = _ranking()
    assert apply_status_overrides_to_ranking(ranking, ()) is ranking
