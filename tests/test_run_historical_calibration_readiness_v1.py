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
    # The synthetic fixture carries real (fabricated) projection stat components,
    # so the historical-row -> RankingResult bridge succeeds and these are real
    # content, not blocked_reason placeholders.
    for section in (
        "CHAMPIONSHIP_EQUITY_CALIBRATION", "PICK_SCORE_EVALUATION", "COST_OF_WAITING_CALIBRATION",
        "STRATEGY_TOURNAMENT",
    ):
        assert "blocked_reason" not in report[section]
        assert report[section]
    assert report["IDENTITY_REPORT"]["checked"] is True
    assert report["IDENTITY_REPORT"]["resolved_pick_count"] == 2
    assert report["MODEL_HEALTH_REPORT"]["metric_count"] >= 0


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
    # No projection stat-component columns in this CSV either -> the bridge
    # cannot build a RankingResult -- these stay honest blocked_reason
    # placeholders, never fabricated.
    assert "blocked_reason" in report["CHAMPIONSHIP_EQUITY_CALIBRATION"]
    assert "blocked_reason" in report["STRATEGY_TOURNAMENT"]


def test_a_real_shaped_csv_with_real_stat_columns_also_reaches_the_bridge(tmp_path) -> None:
    """Section 20: proves the historical-row -> RankingResult bridge is not
    secretly overfit to the synthetic in-memory fixture's own shape -- a
    plain CSV round-trip, with real stat-category columns added, reaches
    the exact same real (non-blocked) CHAMPIONSHIP_EQUITY_CALIBRATION path
    the synthetic run does."""
    dataset_dir = tmp_path / "real_dataset_with_stats"
    dataset_dir.mkdir()
    stat_fields = [
        "passing_yards", "passing_tds", "rushing_yards", "rushing_tds",
        "receiving_yards", "receptions", "receiving_tds",
    ]
    fieldnames = list(REQUIRED_PRE_DRAFT_FIELDS) + list(OUTCOME_ONLY_FIELDS) + stat_fields
    rows_path = dataset_dir / "historical_replay_rows.csv"
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for position, count in (("QB", 5), ("RB", 5), ("WR", 5), ("TE", 5)):
            for i in range(count):
                writer.writerow(
                    {
                        "player_id": f"{position}-{i:02d}", "player_name": f"{position} {i:02d}",
                        "position": position, "team": f"T{i % 4}", "season": 2019,
                        "draft_date": "2019-08-25", "projection_as_of": "2019-08-20",
                        "adp_as_of": "2019-08-20", "platform_adp": float(i + 1),
                        "status_as_of": "2019-08-25", "scoring_format": "ppr",
                        "realized_weekly_points": 200.0 - 5.0 * i, "outcome_as_of": "2020-01-25",
                        "passing_yards": 4000.0 if position == "QB" else 0.0,
                        "passing_tds": 25.0 if position == "QB" else 0.0,
                        "rushing_yards": 1000.0 if position == "RB" else 0.0,
                        "rushing_tds": 8.0 if position == "RB" else 0.0,
                        "receiving_yards": 900.0 if position in ("WR", "TE") else 0.0,
                        "receptions": 70.0 if position in ("WR", "TE") else 0.0,
                        "receiving_tds": 6.0 if position in ("WR", "TE") else 0.0,
                    }
                )
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == STATUS_PASS_READY_FOR_REPLAY
    assert "blocked_reason" not in report["CHAMPIONSHIP_EQUITY_CALIBRATION"]
    assert report["CHAMPIONSHIP_EQUITY_CALIBRATION"]
    assert "blocked_reason" not in report["STRATEGY_TOURNAMENT"]


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


# --- Section 19: synthetic full-pipeline dry run with deliberately injected
# bad cases -- each must block or degrade safely, never silently pass. -------


def _base_row(**overrides) -> dict:
    row = {
        "player_id": "INJ-01", "player_name": "Injected Player", "position": "RB",
        "team": "T1", "season": 2019, "draft_date": "2019-08-25",
        "projection_as_of": "2019-08-20", "adp_as_of": "2019-08-20",
        "platform_adp": 5.0, "status_as_of": "2019-08-25", "scoring_format": "ppr",
        "realized_weekly_points": 150.0, "outcome_as_of": "2020-01-25",
    }
    row.update(overrides)
    return row


def _write_csv_dataset(dataset_dir, rows, picks=None) -> None:
    dataset_dir.mkdir(exist_ok=True)
    fieldnames = list(REQUIRED_PRE_DRAFT_FIELDS) + list(OUTCOME_ONLY_FIELDS)
    with (dataset_dir / "historical_replay_rows.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    if picks:
        with (dataset_dir / "historical_picks.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=["player_id", "identity_status"])
            writer.writeheader()
            writer.writerows(picks)


def test_injected_missing_required_field_blocks_at_schema(tmp_path) -> None:
    dataset_dir = tmp_path / "bad_missing_field"
    _write_csv_dataset(dataset_dir, [_base_row(player_name="")])  # missing required field
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == "BLOCKED_SCHEMA"
    assert report["DATASET_READINESS_REPORT"]["missing_field_rows"] >= 1


def test_injected_unparseable_date_blocks_at_schema(tmp_path) -> None:
    dataset_dir = tmp_path / "bad_unknown_date"
    _write_csv_dataset(dataset_dir, [_base_row(draft_date="NOT_A_REAL_DATE")])
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == "BLOCKED_SCHEMA"


def test_injected_duplicate_player_season_blocks_safely(tmp_path) -> None:
    dataset_dir = tmp_path / "bad_duplicate"
    _write_csv_dataset(dataset_dir, [_base_row(), _base_row()])  # identical player+season twice
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == "BLOCKED_DUPLICATE_PLAYER_SEASON"
    assert report["DATASET_READINESS_REPORT"]["duplicate_player_seasons"] >= 1


def test_injected_stale_immature_outcome_blocks_safely(tmp_path) -> None:
    dataset_dir = tmp_path / "bad_stale_outcome"
    # outcome_as_of only 10 days after draft_date -- far short of the real
    # MATURITY_MIN_DAYS_AFTER_DRAFT (140d) floor.
    _write_csv_dataset(dataset_dir, [_base_row(outcome_as_of="2019-09-04")])
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == "BLOCKED_IMMATURE_OUTCOME"
    assert report["DATASET_READINESS_REPORT"]["immature_outcome_rows"] >= 1


def test_injected_unresolved_identity_conflict_blocks_safely(tmp_path) -> None:
    dataset_dir = tmp_path / "bad_identity"
    _write_csv_dataset(
        dataset_dir, [_base_row()],
        # A real historical pick that resolves to NO row and carries no
        # identity_status at all -- the exact "unflagged unresolved" case.
        picks=[{"player_id": "GHOST-PLAYER-NOT-IN-ROWS", "identity_status": ""}],
    )
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == "BLOCKED_IDENTITY"


def test_injected_missing_projection_stats_degrades_safely_not_a_crash(tmp_path) -> None:
    """'Unknown values' case: a schema/leakage-valid row with NO projection
    stat components at all -- the dataset passes readiness (those fields
    aren't part of the required contract), but the bridge must degrade
    safely (exclude the player, never fabricate points) rather than crash
    or silently zero-score anyone. Proven here at the full-pipeline level,
    not just the bridge's own unit tests."""
    dataset_dir = tmp_path / "bad_no_stats"
    rows = [
        _base_row(player_id=f"NOSTAT-{i}", player_name=f"No Stat {i}", position="RB")
        for i in range(3)
    ]
    _write_csv_dataset(dataset_dir, rows)
    out_path = tmp_path / "report.json"
    exit_code = main(["--dataset-dir", str(dataset_dir), "--out", str(out_path)])
    assert exit_code == 0  # never a crash
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["DATASET_READINESS_REPORT"]["status"] == STATUS_PASS_READY_FOR_REPLAY
    # No stat components anywhere -> the bridge cannot run -> honest blocked_reason.
    assert "blocked_reason" in report["CHAMPIONSHIP_EQUITY_CALIBRATION"]
