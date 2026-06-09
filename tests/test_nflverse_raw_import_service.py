from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.nflverse_raw_import_service import (
    RAW_NFLVERSE_FILES,
    nflverse_raw_import_readiness_rows,
    nflverse_raw_import_summary_rows,
    validate_nflverse_raw_imports,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_raw_nflverse_templates_validate_ready() -> None:
    report = validate_nflverse_raw_imports(TEMPLATE_ROOT)

    assert report.status == "ready"
    assert report.issues == ()
    assert set(report.row_counts) == set(RAW_NFLVERSE_FILES)


def test_raw_import_validation_blocks_missing_required_file(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    (source_root / "nflverse_snap_counts_weekly.csv").unlink()

    report = validate_nflverse_raw_imports(source_root)
    readiness = {
        row["file_name"]: row
        for row in nflverse_raw_import_readiness_rows(report)
    }

    assert report.status == "blocked"
    assert readiness["nflverse_snap_counts_weekly.csv"]["status"] == "blocked"
    assert "Required raw nflverse CSV is missing." in {
        issue.issue for issue in report.issues
    }


def test_raw_import_validation_blocks_bad_header(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    (source_root / "nflverse_player_stats_weekly.csv").write_text(
        "wrong,header\n",
        encoding="utf-8",
    )

    report = validate_nflverse_raw_imports(source_root)

    assert report.status == "blocked"
    assert "CSV header does not match the raw nflverse import contract." in {
        issue.issue for issue in report.issues
    }


def test_raw_import_validation_blocks_non_numeric_values(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "receiving_yards": "lots",
            }
        ],
    )

    report = validate_nflverse_raw_imports(source_root)

    assert report.status == "blocked"
    assert "receiving_yards must be numeric." in {
        issue.issue for issue in report.issues
    }


def test_raw_import_readiness_summarizes_review_only_scoring_effect(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "nflverse_player_stats_weekly.csv",
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        [
            {
                "season": "2025",
                "week": "1",
                "player_id": "p_kicker",
                "player_name": "Kicker One",
                "position": "K",
            }
        ],
    )

    report = validate_nflverse_raw_imports(source_root)
    readiness = nflverse_raw_import_readiness_rows(report)
    summary = {
        row["status"]: row
        for row in nflverse_raw_import_summary_rows(readiness)
    }

    assert report.status == "review"
    assert any(row["status"] == "review" for row in readiness)
    assert all(row["scoring_effect"] == "none; raw import contract only" for row in readiness)
    assert summary["review"]["files"] == 1


def _copy_templates(tmp_path: Path) -> Path:
    target = tmp_path / "nflverse_stats_upgrade"
    shutil.copytree(TEMPLATE_ROOT, target)
    return target


def _write_rows(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
