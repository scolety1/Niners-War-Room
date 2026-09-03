import csv
import json

from scripts.run_historical_calibration_readiness_v1 import (
    STATUS_BLOCKED_NO_DATASET_FOUND,
    STATUS_PASS_READY_FOR_REPLAY,
    SYNTHETIC_LABEL,
    main,
    synthetic_dataset_rows,
)
from src.services.historical_replay_data_adapter_service import (
    OUTCOME_ONLY_FIELDS,
    REQUIRED_PRE_DRAFT_FIELDS,
    validate_leakage,
    validate_schema,
)


def test_synthetic_dataset_passes_its_own_schema_and_leakage_validators() -> None:
    rows, _picks = synthetic_dataset_rows()
    schema = validate_schema(rows)
    leakage = validate_leakage(rows)
    assert schema.valid
    assert leakage.valid


def test_synthetic_run_reaches_pass_and_populates_every_section(tmp_path) -> None:
    out_path = tmp_path / "report.json"
    exit_code = main(["--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["label"] == SYNTHETIC_LABEL
    assert report["DATASET_READINESS_REPORT"]["status"] == STATUS_PASS_READY_FOR_REPLAY
    assert report["LEAKAGE_REPORT"]["valid"] is True
    assert report["BASELINE_RESULTS"]
    assert report["TEAM_SCORE_CALIBRATION"]["per_strategy_mean_realized_production"]
    assert report["CHALLENGER_COMPARISON"]
    # These three are explicitly, honestly blocked this pass -- never faked.
    for section in (
        "CHAMPIONSHIP_EQUITY_CALIBRATION", "PICK_SCORE_EVALUATION", "COST_OF_WAITING_CALIBRATION",
    ):
        assert "blocked_reason" in report[section]


def test_missing_dataset_dir_returns_an_explicit_blocked_status(tmp_path) -> None:
    empty_dir = tmp_path / "nothing_here"
    empty_dir.mkdir()
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(empty_dir), "--out", str(out_path)])
    assert exit_code == 1
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == STATUS_BLOCKED_NO_DATASET_FOUND


def test_a_real_conformant_csv_dataset_reaches_pass_ready_for_replay(tmp_path) -> None:
    dataset_dir = tmp_path / "real_dataset"
    dataset_dir.mkdir()
    fieldnames = list(REQUIRED_PRE_DRAFT_FIELDS) + list(OUTCOME_ONLY_FIELDS)
    rows_path = dataset_dir / "historical_replay_rows.csv"
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(12):
            writer.writerow(
                {
                    "player_id": f"REAL-{i:02d}",
                    "player_name": f"Real Player {i:02d}",
                    "position": ("QB", "RB", "WR", "TE")[i % 4],
                    "team": f"T{i % 4}",
                    "season": 2019,
                    "draft_date": "2019-08-25",
                    "projection_as_of": "2019-08-20",
                    "adp_as_of": "2019-08-20",
                    "platform_adp": float(i + 1),
                    "status_as_of": "2019-08-25",
                    "scoring_format": "ppr",
                    "realized_weekly_points": 200.0 - 5.0 * i,
                    "outcome_as_of": "2020-01-25",
                }
            )
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["label"] == "REAL_DATASET"
    assert report["DATASET_READINESS_REPORT"]["status"] == STATUS_PASS_READY_FOR_REPLAY
    assert report["BASELINE_RESULTS"]
    # No nwr_overall_rank column in a real CSV -> only PLATFORM_ADP is runnable.
    assert all("PLATFORM_ADP" in key for key in report["BASELINE_RESULTS"])


def test_a_real_dataset_with_a_leakage_violation_reports_the_exact_blocker(tmp_path) -> None:
    dataset_dir = tmp_path / "bad_dataset"
    dataset_dir.mkdir()
    fieldnames = list(REQUIRED_PRE_DRAFT_FIELDS) + list(OUTCOME_ONLY_FIELDS)
    rows_path = dataset_dir / "historical_replay_rows.csv"
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "player_id": "BAD-01", "player_name": "Bad Player", "position": "RB",
                "team": "T1", "season": 2019, "draft_date": "2019-08-25",
                # Leakage: projection dated AFTER the draft.
                "projection_as_of": "2019-09-01", "adp_as_of": "2019-08-20",
                "platform_adp": 5.0, "status_as_of": "2019-08-25", "scoring_format": "ppr",
                "realized_weekly_points": 150.0, "outcome_as_of": "2020-01-25",
            }
        )
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0  # a validation block is a normal, well-formed result, not a crash
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == "BLOCKED_LEAKAGE"
    assert "blocked_reason" in report["BASELINE_RESULTS"]
