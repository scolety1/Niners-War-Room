from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_sanity_fixture_runner_service import (
    FIXTURE_CONTRACT_HEADER,
    REVIEW_ONLY_READINESS_LABEL,
    run_model_v4_sanity_fixture_report,
)


def test_current_sanity_fixture_contract_loads_as_review_only_not_applicable() -> None:
    report = run_model_v4_sanity_fixture_report()

    assert report.status == "not_applicable_yet"
    assert report.fixture_count == 31
    assert report.not_applicable_count == 31
    assert report.blocked_count == 0
    assert report.decision_ready_unlocked is False
    assert report.readiness_label == REVIEW_ONLY_READINESS_LABEL
    assert report.issues == ()


def test_fixture_runner_blocks_bad_fixture_schema(tmp_path: Path) -> None:
    fixture_path = tmp_path / "bad_fixtures.csv"
    _write_rows(
        fixture_path,
        ["fixture_id", "fixture_name"],
        [{"fixture_id": "fixture_1", "fixture_name": "Bad fixture"}],
    )
    truth_path = tmp_path / "truth_set.csv"
    _write_rows(truth_path, ["player_name"], [{"player_name": "Bijan Robinson"}])

    report = run_model_v4_sanity_fixture_report(fixture_path, truth_path)

    assert report.status == "blocked_missing_input"
    assert report.fixture_count == 0
    assert any(issue.field == "header" for issue in report.issues)
    assert report.decision_ready_unlocked is False


def test_fixture_runner_reports_missing_players(tmp_path: Path) -> None:
    fixture_path = _fixture_contract(
        tmp_path,
        players="Bijan Robinson|Missing Player",
    )
    truth_path = tmp_path / "truth_set.csv"
    _write_rows(truth_path, ["player_name"], [{"player_name": "Bijan Robinson"}])

    report = run_model_v4_sanity_fixture_report(fixture_path, truth_path)

    assert report.status == "blocked_missing_input"
    assert report.blocked_count == 1
    result = report.results[0]
    assert result.status == "blocked_missing_input"
    assert result.missing_players == ("Missing Player",)
    assert report.decision_ready_unlocked is False


def test_fixture_runner_reports_unavailable_model_outputs(tmp_path: Path) -> None:
    fixture_path = _fixture_contract(
        tmp_path,
        players="Bijan Robinson|Jahmyr Gibbs",
    )
    truth_path = tmp_path / "truth_set.csv"
    _write_rows(
        truth_path,
        ["player_name"],
        [{"player_name": "Bijan Robinson"}, {"player_name": "Jahmyr Gibbs"}],
    )
    model_outputs_path = tmp_path / "model_outputs.csv"
    _write_rows(
        model_outputs_path,
        ["player_name", "private_value"],
        [{"player_name": "Bijan Robinson", "private_value": "99"}],
    )

    report = run_model_v4_sanity_fixture_report(
        fixture_path,
        truth_path,
        model_outputs_path=model_outputs_path,
    )

    assert report.status == "blocked_missing_input"
    result = report.results[0]
    assert result.status == "blocked_missing_input"
    assert result.missing_model_outputs == ("Jahmyr Gibbs",)


def test_fixture_runner_marks_complete_output_coverage_ready_without_pass_fail(
    tmp_path: Path,
) -> None:
    fixture_path = _fixture_contract(
        tmp_path,
        players="Bijan Robinson|Jahmyr Gibbs",
    )
    truth_path = tmp_path / "truth_set.csv"
    model_outputs_path = tmp_path / "model_outputs.csv"
    rows = [{"player_name": "Bijan Robinson"}, {"player_name": "Jahmyr Gibbs"}]
    _write_rows(truth_path, ["player_name"], rows)
    _write_rows(model_outputs_path, ["player_name"], rows)

    report = run_model_v4_sanity_fixture_report(
        fixture_path,
        truth_path,
        model_outputs_path=model_outputs_path,
    )

    assert report.status == "ready"
    assert report.ready_count == 1
    assert "no pass/fail scoring" in report.results[0].detail
    assert report.decision_ready_unlocked is False


def test_fixture_runner_review_finding_stays_review_only(tmp_path: Path) -> None:
    fixture_path = _fixture_contract(
        tmp_path,
        fixture_id="rb_bijan_rb1_002",
        players="Bijan Robinson",
    )
    truth_path = tmp_path / "truth_set.csv"
    _write_rows(truth_path, ["player_name"], [{"player_name": "Bijan Robinson"}])

    report = run_model_v4_sanity_fixture_report(
        fixture_path,
        truth_path,
        review_findings={"rb_bijan_rb1_002": "review"},
    )

    assert report.status == "review"
    assert report.review_count == 1
    assert report.results[0].status == "review"
    assert report.decision_ready_unlocked is False
    assert report.readiness_label == "Review Only"


def _fixture_contract(
    tmp_path: Path,
    *,
    fixture_id: str = "fixture_1",
    players: str,
) -> Path:
    fixture_path = tmp_path / "fixtures.csv"
    _write_rows(
        fixture_path,
        list(FIXTURE_CONTRACT_HEADER),
        [
            {
                "fixture_id": fixture_id,
                "fixture_name": "Test fixture",
                "fixture_type": "expected_ordering",
                "players": players,
                "expected_behavior": "Players should be review checked.",
                "review_severity": "high",
                "receipt_requirement": "Show receipts.",
                "football_logic": "Fixture checks review behavior.",
            }
        ],
    )
    return fixture_path


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
