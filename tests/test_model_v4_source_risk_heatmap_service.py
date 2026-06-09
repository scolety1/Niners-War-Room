from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_source_risk_heatmap_service import (
    FEATURE_HEADER,
    PLAYER_HEADER,
    PLAYER_SUMMARY_HEADER,
    SUMMARY_HEADER,
    build_source_risk_heatmap,
    write_source_risk_heatmap_outputs,
)


def test_source_risk_heatmap_is_review_only_and_has_players() -> None:
    result = build_source_risk_heatmap()

    assert result.player_rows
    assert result.feature_rows
    assert {row["allowed_use"] for row in result.player_rows} == {
        "review_only_source_risk_heatmap_not_final_recommendation"
    }


def test_source_risk_heatmap_missing_data_is_gray_not_zero() -> None:
    result = build_source_risk_heatmap()
    gray_rows = [row for row in result.feature_rows if row["risk_level"] == "gray_missing"]

    assert gray_rows
    assert all("missing" in str(row["status_reason"]).lower() for row in gray_rows[:25])
    assert not any(str(row["status_reason"]).endswith("0") for row in gray_rows)


def test_source_risk_heatmap_flags_source_limited_and_quarantined() -> None:
    result = build_source_risk_heatmap()
    feature_levels = {row["risk_level"] for row in result.feature_rows}
    player_levels = {row["source_risk_level"] for row in result.player_rows}

    assert "orange_source_limited" in feature_levels | player_levels
    assert "red_manual_review" in feature_levels | player_levels


def test_source_risk_heatmap_distinguishes_mismatch_from_quarantine() -> None:
    result = build_source_risk_heatmap()
    mismatch_rows = [
        row
        for row in result.player_rows
        if "team or context mismatch warning" in str(row["warning_summary"])
    ]

    assert mismatch_rows
    assert all(
        "quarantined or identity-review source" not in str(row["warning_summary"])
        for row in mismatch_rows
        if row["source_risk_level"] != "red_manual_review"
    )
    assert all(
        "quarantined or identity-review source" not in str(row["warning_summary"])
        for row in result.player_rows
        if row["source_risk_level"] == "orange_source_limited"
    )


def test_source_risk_heatmap_avoids_blocked_market_terms() -> None:
    result = build_source_risk_heatmap()
    text = " ".join(" ".join(str(value) for value in row.values()) for row in result.player_rows)
    text += " ".join(" ".join(str(value) for value in row.values()) for row in result.feature_rows)
    text = text.lower()

    blocked_terms = ("adp", "fantasypros", "projection", "mock draft", "consensus")
    assert not any(term in text for term in blocked_terms)


def test_source_risk_heatmap_summary_counts_match_players() -> None:
    result = build_source_risk_heatmap()

    assert sum(int(row["player_count"]) for row in result.summary_rows) == len(result.player_rows)


def test_source_risk_heatmap_player_summary_is_one_row_per_player() -> None:
    result = build_source_risk_heatmap()
    summary_names = [row["player_name"] for row in result.player_summary_rows]
    raw_names = [row["player_name"] for row in result.player_rows]

    assert result.player_summary_rows
    assert len(summary_names) == len(set(summary_names))
    assert len(summary_names) <= len(raw_names)
    assert all(int(row["raw_module_row_count"]) >= 1 for row in result.player_summary_rows)
    assert all(
        row["allowed_use"] == result.player_rows[0]["allowed_use"]
        for row in result.player_summary_rows
    )


def test_source_risk_heatmap_player_summary_has_severity_labels() -> None:
    result = build_source_risk_heatmap()

    assert all(str(row["severity_label"]) for row in result.player_summary_rows)
    assert all(str(row["severity_rank"]) for row in result.player_summary_rows)
    assert all(str(row["human_review_priority"]) for row in result.player_summary_rows)
    assert all(str(row["worst_source_risk_level"]) for row in result.player_summary_rows)
    red_rows = [
        row
        for row in result.player_summary_rows
        if row["worst_source_risk_level"] == "red_manual_review"
    ]
    assert red_rows
    assert {row["severity_label"] for row in red_rows} == {"High"}
    assert {row["severity_rank"] for row in red_rows} == {1}


def test_source_risk_heatmap_player_summary_preserves_missing_modules() -> None:
    result = build_source_risk_heatmap()
    missing_rows = [
        row
        for row in result.player_summary_rows
        if str(row["evidence_modules_missing_or_partial"])
    ]

    assert missing_rows
    has_missing_signal = any(
        "gray_missing" in str(row["worst_source_risk_level"]) for row in missing_rows
    ) or any("missing" in str(row["warning_summary"]) for row in missing_rows)
    assert has_missing_signal


def test_source_risk_heatmap_writes_outputs(tmp_path: Path) -> None:
    paths = write_source_risk_heatmap_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["player_rows"]) == PLAYER_HEADER
    assert _header(paths["player_summary_rows"]) == PLAYER_SUMMARY_HEADER
    assert _header(paths["feature_rows"]) == FEATURE_HEADER
    assert _header(paths["summary"]) == SUMMARY_HEADER
    doc_text = paths["doc"].read_text(encoding="utf-8")
    assert doc_text.startswith("# Source-Risk Heatmap")
    assert "one-row-per-player export" in doc_text


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
