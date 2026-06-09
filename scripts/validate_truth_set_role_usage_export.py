from __future__ import annotations

# ruff: noqa: E402,I001

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.truth_set_role_usage_validation_service import (
    TRUTH_SET_ROLE_USAGE_STRICT_HEADER,
    validate_truth_set_role_usage_export,
    write_role_usage_validation_flags,
    write_role_usage_validation_summary,
    write_role_usage_validation_summary_json,
)

TRUTH_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v1"
SOURCE = TRUTH_ROOT / "source_clean" / "role_usage.csv"
PROJECTIONS_SOURCE = TRUTH_ROOT / "source_clean" / "projections.csv"
REPORTS_ROOT = TRUTH_ROOT / "reports"
DOCS_ROOT = ROOT / "docs" / "codex"


def main() -> None:
    expected_players = _expected_players(PROJECTIONS_SOURCE)
    result = validate_truth_set_role_usage_export(
        SOURCE,
        expected_players=expected_players,
    )
    flags_path = REPORTS_ROOT / "role_usage_strict_validation_flags.csv"
    summary_path = REPORTS_ROOT / "role_usage_strict_validation_summary.csv"
    summary_json_path = REPORTS_ROOT / "role_usage_strict_validation_summary.json"
    note_path = DOCS_ROOT / "TRUTH_SET_LAB_V1_ROLE_USAGE_STRICT_VALIDATION.md"

    write_role_usage_validation_flags(flags_path, result.flags)
    write_role_usage_validation_summary(summary_path, (result.summary,))
    write_role_usage_validation_summary_json(summary_json_path, (result.summary,))
    note_path.write_text(
        _markdown_note(result.summary, flags_path, summary_path),
        encoding="utf-8",
    )
    print(result.summary)


def _expected_players(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(row["player_name"] for row in csv.DictReader(handle))


def _markdown_note(
    summary: dict[str, object],
    flags_path: Path,
    summary_path: Path,
) -> str:
    return "\n".join(
        [
            "# Truth Set Lab v1 Role/Usage Strict Validation",
            "",
            "Status: rejected. This phase prepares the app to accept a corrected "
            "role/usage export, but the current role/usage file remains blocked.",
            "",
            "## Files",
            "",
            f"- Strict validation summary: `{summary_path}`",
            f"- Strict validation flags: `{flags_path}`",
            "",
            "## Strict Schema",
            "",
            "The corrected role/usage export must use this exact header:",
            "",
            "```csv",
            ",".join(TRUTH_SET_ROLE_USAGE_STRICT_HEADER),
            "```",
            "",
            "## Current Export Result",
            "",
            f"- Status: `{summary['status']}`",
            f"- Header: `{summary['header_status']}`",
            f"- Rows: {summary['rows']}",
            f"- Malformed-width rows: {summary['malformed_width_rows']}",
            f"- Numeric-error rows: {summary['numeric_error_rows']}",
            f"- Uncertain-marker rows: {summary['uncertain_marker_rows']}",
            f"- Prose numeric rows: {summary['prose_numeric_rows']}",
            f"- Embedded-url rows: {summary['embedded_url_rows']}",
            f"- Source-separation rows: {summary['source_separation_rows']}",
            f"- Blocking flags: {summary['blocking_flags']}",
            "",
            "## Validation Rules",
            "",
            "- Exact header only.",
            "- One row per truth-set player.",
            "- Numeric fields must be numeric, percent-formatted, or blank.",
            "- Question marks are not allowed in numeric fields.",
            "- RB workload prose is rejected as numeric evidence.",
            "- URLs are not allowed in numeric/stat fields.",
            "- `source_name` must not contain URLs.",
            "- `source_url` must contain the URL when a URL is provided.",
            "",
            "## Guardrail",
            "",
            "This validator does not import role/usage data into model scoring. It "
            "only decides whether a future corrected export is structurally safe "
            "enough for preview import.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
