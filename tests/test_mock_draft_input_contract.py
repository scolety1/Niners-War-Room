from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_input_contract import (
    default_real_input_paths,
    fixture_input_paths,
    report_rows_as_dicts,
    validate_input_contract,
)

FIXTURE_ROOT = Path("tests/fixtures/mock_draft_inputs")


def test_fixture_input_contracts_validate_without_simulation() -> None:
    report = validate_input_contract(
        fixture_input_paths(FIXTURE_ROOT),
        mode="fixture",
    )

    assert report.review_only is True
    assert report.no_simulations_run is True
    assert report.readiness == "GREEN"
    assert all(row.readiness == "GREEN" for row in report.rows)
    assert "never NWR private value" in report.market_policy


def test_missing_real_inputs_are_yellow_not_crashing() -> None:
    report = validate_input_contract(
        default_real_input_paths(),
        mode="real",
    )

    assert report.readiness == "YELLOW"
    assert all(row.readiness == "YELLOW" for row in report.rows)
    assert any(row.key == "frozen_rookie_input" and not row.present for row in report.rows)


def test_missing_required_fixture_columns_are_red(tmp_path: Path) -> None:
    rookie_path = tmp_path / "rookie_input_fixture.csv"
    rookie_path.write_text("asset_id,player\nrookie:bad,Fixture Bad\n", encoding="utf-8")
    paths = fixture_input_paths(FIXTURE_ROOT)
    paths["frozen_rookie_input"] = rookie_path

    report = validate_input_contract(paths, mode="fixture")
    rows = {row.key: row for row in report.rows}

    assert report.readiness == "RED"
    assert rows["frozen_rookie_input"].readiness == "RED"
    assert "position" in rows["frozen_rookie_input"].missing_columns
    assert "Required columns are missing." in rows["frozen_rookie_input"].errors


def test_market_context_and_nwr_private_values_stay_separate() -> None:
    report = validate_input_contract(fixture_input_paths(FIXTURE_ROOT), mode="fixture")
    rows = {row.key: row for row in report.rows}

    assert rows["market_context"].readiness == "GREEN"
    assert rows["nwr_private_values"].readiness == "GREEN"
    assert rows["market_context"].blocked_columns == ()
    assert rows["nwr_private_values"].blocked_columns == ()


def test_market_context_rejects_nwr_private_value_columns(tmp_path: Path) -> None:
    market_path = tmp_path / "market_context_fixture.csv"
    market_path.write_text(
        (
            "asset_id,player,position,market_adp_pick,market_source,"
            "opponent_likelihood_signal,allowed_use,separation_note,nwr_private_value\n"
            "rookie:bad,Fixture Bad,WR,2.0,fixture,early,opponent_behavior_only,"
            "market_does_not_set_nwr_value,99\n"
        ),
        encoding="utf-8",
    )
    paths = fixture_input_paths(FIXTURE_ROOT)
    paths["market_context"] = market_path

    report = validate_input_contract(paths, mode="fixture")
    rows = {row.key: row for row in report.rows}

    assert report.readiness == "RED"
    assert rows["market_context"].readiness == "RED"
    assert "nwr_private_value" in rows["market_context"].blocked_columns


def test_nwr_private_values_reject_market_columns(tmp_path: Path) -> None:
    nwr_path = tmp_path / "nwr_private_values_fixture.csv"
    nwr_path.write_text(
        (
            "asset_id,player,position,nwr_private_value,value_source,"
            "separation_note,market_adp_pick\n"
            "rookie:bad,Fixture Bad,WR,70,fixture_private_value,no_market_fields,2.0\n"
        ),
        encoding="utf-8",
    )
    paths = fixture_input_paths(FIXTURE_ROOT)
    paths["nwr_private_values"] = nwr_path

    report = validate_input_contract(paths, mode="fixture")
    rows = {row.key: row for row in report.rows}

    assert report.readiness == "RED"
    assert rows["nwr_private_values"].readiness == "RED"
    assert "market_adp_pick" in rows["nwr_private_values"].blocked_columns


def test_contract_validation_does_not_write_outputs(tmp_path: Path) -> None:
    before = sorted(path.name for path in tmp_path.iterdir())

    report = validate_input_contract(
        fixture_input_paths(FIXTURE_ROOT),
        mode="fixture",
        repo_root=".",
    )
    rows = report_rows_as_dicts(report)

    after = sorted(path.name for path in tmp_path.iterdir())
    assert before == after
    assert rows
    assert "blocked_columns" in rows[0]
