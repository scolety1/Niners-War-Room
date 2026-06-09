from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.model_v4_stats_first_sanity_audit_service import (
    STATS_FIRST_SANITY_AUDIT_HEADER,
    run_model_v4_stats_first_sanity_audit,
)


def test_phase_9d_flags_projection_guardrail_and_deep_history_pass(
    tmp_path: Path,
) -> None:
    expected = tmp_path / "expected.csv"
    components = tmp_path / "components.csv"
    unavailable = tmp_path / "unavailable.csv"
    warnings = tmp_path / "warnings.csv"
    summary = tmp_path / "summary.json"
    _write_expected_rows(
        expected,
        [
            _expected_row("Tom Brady", "QB", "2022", "5.25"),
            _expected_row("Josh Allen", "QB", "2025", "83.61"),
        ],
    )
    _write_csv(components, ("matched_model_player", "component"), [])
    _write_csv(
        unavailable,
        ("matched_model_player", "position", "component_or_section", "reason", "severity"),
        [],
    )
    _write_csv(
        warnings,
        ("matched_model_player", "position", "season", "source_name", "warning", "detail"),
        [],
    )
    _write_summary(summary, projection_rows=0)

    result = run_model_v4_stats_first_sanity_audit(
        expected_value_path=expected,
        component_evidence_path=components,
        unavailable_sections_path=unavailable,
        source_warnings_path=warnings,
        summary_path=summary,
        truth_set_path=tmp_path / "missing_truth_set.csv",
        output_csv_path=tmp_path / "audit.csv",
        output_md_path=tmp_path / "audit.md",
        audit_groups={
            "aging_retired_historical": ("Tom Brady",),
            "qb_controls": ("Josh Allen",),
        },
    )

    tom = _row_for(result.rows, "Tom Brady")
    assert tom["deep_history_status"] == "deep_history_only_not_boosted"
    assert tom["issue_type"] == "no_issue"
    assert result.summary["guardrails"]["projection_core_value_status"] == (
        "passes_no_projection_core_value"
    )
    assert _row_for(result.rows, "Josh Allen")["issue_type"] == "formula_context_needed"


def test_phase_9d_flags_deep_history_only_player_too_high(tmp_path: Path) -> None:
    expected = tmp_path / "expected.csv"
    _write_expected_rows(
        expected,
        [_expected_row("Old Star", "WR", "2021", "40.0")],
    )
    summary = tmp_path / "summary.json"
    _write_summary(summary, projection_rows=0)

    result = run_model_v4_stats_first_sanity_audit(
        expected_value_path=expected,
        component_evidence_path=tmp_path / "missing_components.csv",
        unavailable_sections_path=tmp_path / "missing_unavailable.csv",
        source_warnings_path=tmp_path / "missing_warnings.csv",
        summary_path=summary,
        truth_set_path=tmp_path / "missing_truth_set.csv",
        output_csv_path=tmp_path / "audit.csv",
        output_md_path=tmp_path / "audit.md",
        audit_groups={"aging_retired_historical": ("Old Star",)},
    )

    row = _row_for(result.rows, "Old Star")
    assert row["deep_history_status"] == "deep_history_only_too_high"
    assert row["issue_type"] == "formula_data_issue"


def test_phase_9d_writes_csv_and_markdown(tmp_path: Path) -> None:
    expected = tmp_path / "expected.csv"
    summary = tmp_path / "summary.json"
    output_csv = tmp_path / "audit.csv"
    output_md = tmp_path / "audit.md"
    _write_expected_rows(
        expected,
        [_expected_row("Puka Nacua", "WR", "2025", "77.0")],
    )
    _write_summary(summary, projection_rows=0)

    result = run_model_v4_stats_first_sanity_audit(
        expected_value_path=expected,
        component_evidence_path=tmp_path / "missing_components.csv",
        unavailable_sections_path=tmp_path / "missing_unavailable.csv",
        source_warnings_path=tmp_path / "missing_warnings.csv",
        summary_path=summary,
        truth_set_path=tmp_path / "missing_truth_set.csv",
        output_csv_path=output_csv,
        output_md_path=output_md,
        audit_groups={"elite_wrs": ("Puka Nacua",)},
    )

    assert result.csv_path == output_csv
    assert result.markdown_path == output_md
    assert _header(output_csv) == STATS_FIRST_SANITY_AUDIT_HEADER
    assert "Phase 9D Stats-First Sanity Audit" in output_md.read_text(encoding="utf-8")


def _expected_row(
    player: str,
    position: str,
    latest_season: str,
    value: str,
) -> list[str]:
    return [
        player,
        position,
        "",
        "",
        latest_season,
        f"deep_history_through_2022:0.12({latest_season}-{latest_season})"
        if int(latest_season) <= 2022
        else f"{latest_season}:1.0",
        value,
        "1.0",
        "{}",
        json.dumps({"production_trend": float(value)}),
        "{}",
        "0",
        "0",
        "comparison_only_not_core_value",
        "review_only",
        "test_layer",
    ]


def _write_expected_rows(path: Path, rows: list[list[str]]) -> None:
    _write_csv(
        path,
        (
            "matched_model_player",
            "position",
            "sleeper_id",
            "gsis_id",
            "latest_season",
            "weighted_seasons",
            "stats_first_expected_value",
            "evidence_coverage",
            "component_scores",
            "component_contributions",
            "component_weights",
            "source_warning_count",
            "unavailable_section_count",
            "external_projection_context_status",
            "review_status",
            "layer_version",
        ),
        rows,
    )


def _write_summary(path: Path, *, projection_rows: int) -> None:
    path.write_text(
        json.dumps(
            {
                "projection_context_rows_used_for_core_value": projection_rows,
                "route_metrics_used": False,
                "market_value_used": False,
                "league_rank_used": False,
                "active_rankings_overwritten": False,
                "players": 2,
                "component_evidence_rows": 0,
                "unavailable_rows": 0,
                "source_warning_rows": 0,
            }
        ),
        encoding="utf-8",
    )


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))


def _row_for(rows: tuple[dict[str, object], ...], player: str) -> dict[str, object]:
    return next(row for row in rows if row["player"] == player)
