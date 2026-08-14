from src.services.practical_redraft_mock_service import run_practical_mock
from src.services.redraft_engine_v1_service import DraftContext, LeagueProfile, RankingResult, RedraftRankingRow, RosterSettings, ScoringSettings


def _ranking() -> RankingResult:
    rows = []
    for position, count in (("QB", 30), ("RB", 80), ("WR", 100), ("TE", 30)):
        for index in range(count):
            rows.append(RedraftRankingRow(len(rows) + 1, index + 1, f"{position}-{index}", f"{position} {index}", position, "TST", 300 - index, 0, 0, 0, "MEDIUM", 1, "test", "Test", "GOVERNED", "AVAILABLE", "2026-08-01", False))
    profile = LeagueProfile("test", "Test", 2026, 10, RosterSettings(k=1, dst=1), ScoringSettings(reception=1), DraftContext(rounds=15), practical_mode=True)
    return RankingResult(profile, tuple(rows), (), (), "2026-08-01T00:00:00+00:00", "fixture")


def test_practical_mock_finishes_150_unique_picks_and_legal_kdst_for_all_slots() -> None:
    manual = [{"player_id": f"manual:K:{index}", "player_name": f"K {index}", "position": "K", "team": f"K{index}", "authority": "MANUAL — NOT MODELED BY NWR"} for index in range(12)] + [{"player_id": f"manual:DST:{index}", "player_name": f"DST {index}", "position": "DST", "team": f"D{index}", "authority": "MANUAL — NOT MODELED BY NWR"} for index in range(12)]
    for slot in (2, 5, 9):
        result = run_practical_mock(_ranking().profile, _ranking(), manual, owner_slot=slot)
        assert not result.errors
        assert len(result.picks) == 150
        assert len({row["player_id"] for row in result.picks}) == 150
        assert all(roster["K"] >= 1 and roster["DST"] >= 1 for roster in result.rosters.values())
        assert all(row["selection_behavior"] == "MANUAL_UNMODELED" for row in result.picks if row["position"] in {"K", "DST"})
