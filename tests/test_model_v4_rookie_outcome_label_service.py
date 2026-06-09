from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_historical_rookie_tuning_service import (
    HISTORICAL_OUTCOMES,
    build_historical_rookie_tuning_report,
)
from src.services.model_v4_rookie_outcome_label_service import (
    build_rookie_outcome_labels,
    write_rookie_outcome_label_outputs,
)


def test_rookie_outcome_labels_use_rotowire_stats_without_changing_scores() -> None:
    result = build_rookie_outcome_labels()

    assert result.summary["rows"] == 395
    assert result.summary["labels_loaded"] > 300
    assert result.summary["model_scores_changed"] is False

    by_name = {str(row["player"]): row for row in result.rows}
    chase = by_name["Ja'Marr Chase"]
    assert chase["outcome_label"] == "difference_maker"
    assert float(chase["best_3yr_ppg"]) > 13
    assert chase["source_status"] == "rotowire_imported_real_outcome_display_only"


def test_rookie_outcome_label_writer_exports_expected_files(tmp_path: Path) -> None:
    paths = write_rookie_outcome_label_outputs(output_root=tmp_path)

    assert paths["labels"].exists()
    assert paths["summary"].exists()
    with paths["summary"].open(newline="", encoding="utf-8") as handle:
        summary = {row["metric"]: row["value"] for row in csv.DictReader(handle)}
    assert int(summary["labels_loaded"]) > 300
    assert summary["model_scores_changed"] == "False"


def test_historical_tuning_report_uses_full_outcome_labels() -> None:
    report = build_historical_rookie_tuning_report()

    assert report.outcome_path == str(HISTORICAL_OUTCOMES)
    assert len(report.board_rows) == 395
    loaded = [row for row in report.board_rows if row["Outcome Loaded"]]
    assert len(loaded) > 300
    assert "Starter-Level Seasons" in report.board_rows[0]
    assert "Top-24 Seasons" not in report.board_rows[0]
    assert "Fantasy-Relevant Replay Pool" in report.board_rows[0]
    assert "Strict Starter Hit?" in report.board_rows[0]

    chase = next(row for row in report.board_rows if row["Player"] == "Ja'Marr Chase")
    assert chase["Outcome Category"] == "difference_maker"
    assert chase["Broad Outcome Hit?"] is True
    assert chase["Strict Starter Hit?"] is True
    assert chase["Difference Maker?"] is True
    assert chase["Best LVE PPG"] != ""


def test_historical_tuning_summary_separates_universe_and_hit_strictness() -> None:
    report = build_historical_rookie_tuning_report()

    assert report.summary_rows
    sample = report.summary_rows[0]
    assert "Universe" in sample
    assert "Broad Hit Rate" in sample
    assert "Strict Starter Hit Rate" in sample
    assert "Mature Strict Hit Rate" in sample
    assert {row["Future Stats Used In Ranking"] for row in report.summary_rows} == {False}
