from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_sanity_fixture_dry_run_service import (
    DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
)

DEFAULT_V4_SOURCE_COVERAGE_PATH = Path(
    "local_exports/model_v4/review_only_latest/v4_source_coverage_rows.csv"
)
PHASE_5H_CSV_PATH = Path("docs/model_v4/PHASE_5_VETERAN_MISSING_DATA_PENALTY.csv")
PHASE_5H_MD_PATH = Path("docs/model_v4/PHASE_5_VETERAN_MISSING_DATA_PENALTY.md")

CRITICAL_VALUE_SECTIONS = (
    "production",
    "first_down_scoring_fit",
    "usage_opportunity",
    "snap_proxy_role",
    "projection",
)

PHASE_5H_HEADER = (
    "player",
    "position",
    "nfl_team",
    "lifecycle",
    "dynasty_asset_value",
    "value_basis",
    "scored_component_weight",
    "missing_component_weight",
    "missing_value_components",
    "confidence_label",
    "missing_sections",
    "not_applicable_sections",
    "root_cause",
    "action_taken",
    "review_status",
)


@dataclass(frozen=True)
class VeteranMissingDataPenaltyAuditResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_veteran_missing_data_penalty_audit(
    *,
    preview_outputs_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    source_coverage_path: str | Path = DEFAULT_V4_SOURCE_COVERAGE_PATH,
    output_csv_path: str | Path = PHASE_5H_CSV_PATH,
    output_md_path: str | Path = PHASE_5H_MD_PATH,
) -> VeteranMissingDataPenaltyAuditResult:
    preview_rows = _read_dicts(Path(preview_outputs_path))
    coverage = _coverage_by_player(Path(source_coverage_path))
    rows = tuple(
        _audit_row(row, coverage.get(row["player"], []))
        for row in preview_rows
        if row.get("lifecycle") == "established_veteran"
        and _has_missing_or_adjusted_value(row, coverage.get(row["player"], []))
    )
    summary = _summary(rows)
    csv_path = Path(output_csv_path)
    markdown_path = Path(output_md_path)
    _write_csv(csv_path, PHASE_5H_HEADER, rows)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_markdown(summary, rows), encoding="utf-8")
    return VeteranMissingDataPenaltyAuditResult(
        csv_path=csv_path,
        markdown_path=markdown_path,
        rows=rows,
        summary=summary,
    )


def _audit_row(
    preview: dict[str, str],
    coverage_rows: list[dict[str, str]],
) -> dict[str, object]:
    missing = tuple(
        row["section"]
        for row in coverage_rows
        if row.get("coverage_status") == "missing"
    )
    not_applicable = tuple(
        row["section"]
        for row in coverage_rows
        if row.get("coverage_status") == "not_applicable"
    )
    missing_critical = tuple(section for section in missing if section in CRITICAL_VALUE_SECTIONS)
    root_cause = _root_cause(missing_critical, missing, not_applicable, preview)
    return {
        "player": preview.get("player", ""),
        "position": preview.get("position", ""),
        "nfl_team": preview.get("nfl_team", ""),
        "lifecycle": preview.get("lifecycle", ""),
        "dynasty_asset_value": preview.get("dynasty_asset_value", ""),
        "value_basis": preview.get("value_basis", ""),
        "scored_component_weight": preview.get("scored_component_weight", ""),
        "missing_component_weight": preview.get("missing_component_weight", ""),
        "missing_value_components": preview.get("missing_value_components", ""),
        "confidence_label": preview.get("confidence_label", ""),
        "missing_sections": "|".join(missing),
        "not_applicable_sections": "|".join(not_applicable),
        "root_cause": root_cause,
        "action_taken": _action_taken(root_cause, preview),
        "review_status": "review_only",
    }


def _root_cause(
    missing_critical: tuple[str, ...],
    missing: tuple[str, ...],
    not_applicable: tuple[str, ...],
    preview: dict[str, str],
) -> str:
    if "production" in missing_critical or "usage_opportunity" in missing_critical:
        return "possible_import_or_identity_gap"
    if "projection" in missing_critical:
        return "truth_set_projection_coverage_gap"
    if preview.get("value_basis") == "evidence_adjusted_missing_not_zero":
        return "missing_optional_value_evidence_adjusted"
    if not_applicable and not missing:
        return "not_applicable_data_no_longer_counted_as_missing"
    if missing:
        return "source_unavailable_or_truth_set_gap"
    return "value_semantics_audit"


def _action_taken(root_cause: str, preview: dict[str, str]) -> str:
    if root_cause == "possible_import_or_identity_gap":
        return "Keep weak/review confidence and inspect source mapping before scoring."
    if root_cause == "truth_set_projection_coverage_gap":
        return (
            "Missing projection excluded from established-veteran value denominator; "
            "confidence remains review/weak."
        )
    if root_cause == "missing_optional_value_evidence_adjusted":
        return "Unavailable value evidence is not scored as zero production."
    if root_cause == "not_applicable_data_no_longer_counted_as_missing":
        return "Not-applicable young-player prior is displayed separately from missing data."
    if preview.get("value_basis") == "insufficient_evidence_not_rankable":
        return "Row remains review-only because too little evidence is available."
    return "No score promotion; row remains review-only."


def _summary(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    return {
        "review_status": "review_only",
        "audited_rows": len(rows),
        "projection_gap_rows": sum(
            1 for row in rows if row["root_cause"] == "truth_set_projection_coverage_gap"
        ),
        "possible_import_or_identity_gap_rows": sum(
            1 for row in rows if row["root_cause"] == "possible_import_or_identity_gap"
        ),
        "evidence_adjusted_rows": sum(
            1
            for row in rows
            if row["value_basis"] == "evidence_adjusted_missing_not_zero"
        ),
        "insufficient_evidence_rows": sum(
            1 for row in rows if row["value_basis"] == "insufficient_evidence_not_rankable"
        ),
        "active_rankings_promoted": False,
        "score_changes_are_review_only": True,
    }


def _markdown(summary: dict[str, object], rows: tuple[dict[str, object], ...]) -> str:
    lines = [
        "# Phase 5H Veteran Missing-Data Penalty Repair",
        "",
        "This audit verifies that missing evidence for established veterans is labeled "
        "as unavailable or insufficient evidence instead of being treated as proof of "
        "zero production. It remains review-only.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Repair Notes",
            "",
            "- Established-veteran missing value components are excluded from the value "
            "denominator when enough other evidence exists.",
            "- Missing projections remain visible and keep confidence in review/weak territory.",
            "- Not-applicable young-player prior rows no longer show as missing evidence.",
            "- No fake production, projection, injury, route, or market values were created.",
            "",
            "## Audited Rows",
            "",
        ]
    )
    table_header = (
        "player",
        "position",
        "dynasty_asset_value",
        "value_basis",
        "confidence_label",
        "missing_sections",
        "not_applicable_sections",
        "root_cause",
        "action_taken",
    )
    lines.extend(_markdown_table(table_header, rows))
    lines.append("")
    return "\n".join(lines)


def _has_missing_or_adjusted_value(
    preview: dict[str, str],
    coverage_rows: list[dict[str, str]],
) -> bool:
    if preview.get("value_basis") in {
        "evidence_adjusted_missing_not_zero",
        "insufficient_evidence_not_rankable",
    }:
        return True
    return any(row.get("coverage_status") != "covered" for row in coverage_rows)


def _coverage_by_player(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _read_dicts(path):
        grouped[row["player"]].append(row)
    return grouped


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _markdown_table(
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> list[str]:
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(row.get(column, "")) for column in header) + " |")
    return lines


def _md_cell(value: object) -> str:
    return str(value or "").replace("|", "<br>").replace("\n", " ")
