from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.market_edge_service import build_market_edge_report

SAMPLE_PACK = Path("sample_data/2026_pre_declaration")


def test_market_edge_report_splits_model_higher_and_market_higher_views(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    rows = _read_csv(pack / "model_outputs.csv")
    for row in rows:
        if row["player_id"] == "p_achane":
            row["private_score"] = "92"
            row["market_score"] = "74"
            row["confidence_score"] = "83"
            row["warning_status"] = "ready"
            row["warning_reasons"] = ""
        if row["player_id"] == "p_lamar":
            row["private_score"] = "78"
            row["market_score"] = "94"
            row["confidence_score"] = "81"
            row["warning_status"] = "data_warning"
            row["warning_reasons"] = "data_warning_market_source_stale"
    _write_csv(pack / "model_outputs.csv", rows)

    report = build_market_edge_report(pack)

    assert not report.issues
    model_edge = _row_for(report.model_higher_rows, "p_achane")
    market_edge = _row_for(report.market_higher_rows, "p_lamar")
    assert model_edge["market_edge_score"] == 18.0
    assert model_edge["edge_classification"] == "strong_positive_edge_model_higher"
    assert model_edge["edge_confidence"] == "usable_edge"
    assert model_edge["edge_confidence_label"] == "usable edge"
    assert market_edge["market_edge_score"] == -16.0
    assert market_edge["edge_classification"] == "strong_negative_edge_market_higher"
    assert market_edge["source_warning"] == "stale source"
    assert market_edge["warning_summary"] == "stale source; source data needs review"


def test_market_edge_report_marks_missing_inputs_as_blocked_review(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    rows = _read_csv(pack / "model_outputs.csv")
    rows[0]["private_score"] = ""
    rows[0]["market_score"] = ""
    _write_csv(pack / "model_outputs.csv", rows)

    report = build_market_edge_report(pack)
    missing = _row_for(report.rows, rows[0]["player_id"])

    assert missing["edge_classification"] == "missing_market_inputs"
    assert missing["edge_view"] == "missing_market_inputs"
    assert missing["edge_confidence"] == "blocked_missing_inputs"
    assert missing["edge_confidence_label"] == "blocked by missing inputs"
    assert missing["source_warning"] == "missing market value"


def _copy_pack(tmp_path: Path) -> Path:
    target = tmp_path / "pack"
    shutil.copytree(SAMPLE_PACK, target)
    return target


def _row_for(rows: list[dict[str, object]], player_id: str) -> dict[str, object]:
    return next(row for row in rows if row["player_id"] == player_id)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
