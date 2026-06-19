from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_readiness_service import build_mock_draft_readiness_report


def test_fixture_contracts_are_green_with_real_inputs_yellow() -> None:
    report = build_mock_draft_readiness_report()

    assert report.readiness == "YELLOW"
    assert report.fixture_readiness == "GREEN"
    assert report.real_input_readiness == "YELLOW"
    assert report.no_simulations_run is True
    assert report.no_files_written is True


def test_missing_real_manifest_is_yellow() -> None:
    report = build_mock_draft_readiness_report(
        manifest_path="local_exports/mock_draft/missing_manifest.local.json"
    )

    assert report.manifest_readiness == "YELLOW"


def test_malformed_fixture_contract_is_red(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    for name in (
        "rookie_input_fixture.csv",
        "veteran_pool_fixture.csv",
        "pick_order_fixture.csv",
        "my_picks_fixture.csv",
        "rosters_fixture.csv",
        "team_needs_fixture.csv",
        "nwr_private_values_fixture.csv",
        "market_context_fixture.csv",
    ):
        (fixture_root / name).write_text("asset_id\nbad\n", encoding="utf-8")

    report = build_mock_draft_readiness_report(fixture_root=fixture_root)

    assert report.readiness == "RED"
    assert report.schema_violations


def test_market_separation_violation_returns_red(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/mock_draft_inputs")
    market_path = tmp_path / "market_context_fixture.csv"
    market_path.write_text(
        "asset_id,player,position,market_adp_pick,market_source,"
        "opponent_likelihood_signal,allowed_use,separation_note,nwr_private_value\n"
        "a,A,WR,2,fixture,early,opponent_behavior_only,no,70\n",
        encoding="utf-8",
    )
    temp_root = tmp_path / "fixtures"
    temp_root.mkdir()
    for path in fixture_root.iterdir():
        if path.is_file() and path.suffix == ".csv":
            target = temp_root / path.name
            target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (temp_root / "market_context_fixture.csv").write_text(
        market_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = build_mock_draft_readiness_report(fixture_root=temp_root)

    assert report.readiness == "RED"


def test_aggregate_yellow_when_only_real_inputs_are_missing() -> None:
    report = build_mock_draft_readiness_report()

    assert report.readiness == "YELLOW"
    assert report.fixture_readiness == "GREEN"
    assert report.schema_violations == ()
