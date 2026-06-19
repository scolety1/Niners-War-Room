from src.trading_lab.trade_lab_fixtures import (
    asset_by_name,
    fixture_assets,
    fixture_picks,
    fixture_players,
    fixture_team_contexts,
    fixture_value_snapshot,
    team_context_by_name,
)

FAKE_NAMES = {
    "Target Player",
    "Player A",
    "Player B",
    "Player C",
    "Player D",
    "2026 2nd",
    "2026 3rd",
    "Team Alpha",
    "Team Bravo",
    "Team Charlie",
}


def test_fixture_provider_returns_players_picks_and_teams() -> None:
    assert {player.display_name for player in fixture_players()} == {
        "Target Player",
        "Player A",
        "Player B",
        "Player C",
        "Player D",
    }
    assert {pick.display_name for pick in fixture_picks()} == {"2026 2nd", "2026 3rd"}
    assert {team.team_name for team in fixture_team_contexts()} == {
        "Team Alpha",
        "Team Bravo",
        "Team Charlie",
    }


def test_all_fixture_names_are_fake() -> None:
    text = " ".join(
        (
            *(asset.display_name for asset in fixture_assets()),
            *(team.team_name for team in fixture_team_contexts()),
        )
    )

    assert set(text.split(" Team ")).isdisjoint({"49ers"})
    assert all(name in FAKE_NAMES for name in [asset.display_name for asset in fixture_assets()])


def test_fixture_snapshot_is_in_memory() -> None:
    snapshot = fixture_value_snapshot()

    assert snapshot.assets
    assert snapshot.team_contexts
    assert "fixture-only" in snapshot.source_note


def test_no_file_paths_or_source_clients_in_fixture_repr() -> None:
    text = repr(fixture_value_snapshot()).lower()

    for blocked in ("data/", "local_exports", ".csv", ".json", "http", "fetch", "client"):
        assert blocked not in text


def test_nwr_private_value_remains_separate_from_public_market_value() -> None:
    target = asset_by_name("Target Player")

    assert target.nwr_value == 82.0
    assert target.public_market_value == 70.0
    assert target.nwr_value != target.public_market_value


def test_team_lookup_returns_fake_context() -> None:
    context = team_context_by_name("Team Alpha")

    assert "RB depth" in context.roster_needs
    assert "fake" in " ".join(context.notes)
