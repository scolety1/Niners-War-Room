from __future__ import annotations

# ruff: noqa: E402,I001

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.truth_set_production_validation_service import (
    TRUTH_SET_PRODUCTION_STRICT_HEADER,
    validate_truth_set_production_export,
    write_production_validation_flags,
    write_production_validation_summary,
    write_production_validation_summary_json,
)

TRUTH_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v1"
RAW_SOURCE = TRUTH_ROOT / "source_raw" / "production_data.csv"
CLEAN_REJECTED_SOURCE = TRUTH_ROOT / "source_clean" / "production_data.csv"
PROJECTIONS_SOURCE = TRUTH_ROOT / "source_clean" / "projections.csv"
REPORTS_ROOT = TRUTH_ROOT / "reports"
DOCS_ROOT = ROOT / "docs" / "codex"


def main() -> None:
    expected_players = _expected_players(PROJECTIONS_SOURCE)
    results = (
        validate_truth_set_production_export(
            RAW_SOURCE,
            expected_players=expected_players,
        ),
        validate_truth_set_production_export(
            CLEAN_REJECTED_SOURCE,
            expected_players=expected_players,
        ),
    )
    flags = tuple(flag for result in results for flag in result.flags)
    summaries = tuple(result.summary for result in results)

    flags_path = REPORTS_ROOT / "production_strict_validation_flags.csv"
    summary_path = REPORTS_ROOT / "production_strict_validation_summary.csv"
    summary_json_path = REPORTS_ROOT / "production_strict_validation_summary.json"
    note_path = DOCS_ROOT / "TRUTH_SET_LAB_V1_PRODUCTION_STRICT_VALIDATION.md"

    write_production_validation_flags(flags_path, flags)
    write_production_validation_summary(summary_path, summaries)
    write_production_validation_summary_json(summary_json_path, summaries)
    note_path.write_text(
        _markdown_note(summaries, flags_path, summary_path),
        encoding="utf-8",
    )
    for summary in summaries:
        print(summary)


def _expected_players(path: Path) -> tuple[str, ...]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(row["player_name"] for row in csv.DictReader(handle))


def _markdown_note(
    summaries: tuple[dict[str, object], ...],
    flags_path: Path,
    summary_path: Path,
) -> str:
    raw_summary = next(
        row
        for row in summaries
        if str(row["source_file"]).endswith("source_raw\\production_data.csv")
    )
    clean_summary = next(
        row
        for row in summaries
        if str(row["source_file"]).endswith("source_clean\\production_data.csv")
    )
    return "\n".join(
        [
            "# Truth Set Lab v1 Production Strict Validation",
            "",
            "Status: rejected. This phase prepares the app to accept a corrected "
            "production export, but the current production files remain blocked.",
            "",
            "## Files",
            "",
            f"- Strict validation summary: `{summary_path}`",
            f"- Strict validation flags: `{flags_path}`",
            "",
            "## Strict Schema",
            "",
            "The corrected production export must use this exact header:",
            "",
            "```csv",
            ",".join(TRUTH_SET_PRODUCTION_STRICT_HEADER),
            "```",
            "",
            "## Current Raw Export Result",
            "",
            f"- Status: `{raw_summary['status']}`",
            f"- Header: `{raw_summary['header_status']}`",
            f"- Rows: {raw_summary['rows']}",
            f"- Malformed-width rows: {raw_summary['malformed_width_rows']}",
            f"- Numeric-error rows: {raw_summary['numeric_error_rows']}",
            f"- Uncertain-marker rows: {raw_summary['uncertain_marker_rows']}",
            f"- Embedded-url rows: {raw_summary['embedded_url_rows']}",
            f"- Source-separation rows: {raw_summary['source_separation_rows']}",
            f"- Blocking flags: {raw_summary['blocking_flags']}",
            "",
            "## Current Clean/Rejection Metadata Result",
            "",
            f"- Status: `{clean_summary['status']}`",
            f"- Header: `{clean_summary['header_status']}`",
            f"- Rows: {clean_summary['rows']}",
            f"- Blocking flags: {clean_summary['blocking_flags']}",
            "",
            "## Validation Rules",
            "",
            "- Exact header only.",
            "- One row per truth-set player.",
            "- Every row must have the same column count as the header.",
            "- Numeric fields must be numeric or blank.",
            "- Question marks are not allowed in numeric fields.",
            "- URLs are not allowed in numeric/stat fields.",
            "- `source_name` must not contain URLs.",
            "- `source_url` must contain the URL when a URL is provided.",
            "",
            "## Guardrail",
            "",
            "This validator does not import production data into model scoring. It only "
            "decides whether a future corrected export is structurally safe enough for "
            "a preview import.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
