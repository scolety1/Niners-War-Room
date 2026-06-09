from __future__ import annotations

# ruff: noqa: E402,I001

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.truth_set_young_bridge_prior_service import (  # noqa: E402
    build_truth_set_young_bridge_prior,
    write_truth_set_young_bridge_flags,
    write_truth_set_young_bridge_prior,
    write_truth_set_young_bridge_receipts,
)


TRUTH_SET_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v1"
SOURCE_PATH = TRUTH_SET_ROOT / "source_clean" / "young_player_prior.csv"
REPORTS_ROOT = TRUTH_SET_ROOT / "reports"
DOCS_ROOT = ROOT / "docs" / "codex"


def main() -> None:
    result = build_truth_set_young_bridge_prior(SOURCE_PATH)
    preview_path = REPORTS_ROOT / "young_bridge_prior_preview.csv"
    receipts_path = REPORTS_ROOT / "young_bridge_prior_receipts.csv"
    flags_path = REPORTS_ROOT / "young_bridge_prior_preview_flags.csv"
    summary_path = REPORTS_ROOT / "young_bridge_prior_preview_summary.json"
    note_path = DOCS_ROOT / "TRUTH_SET_LAB_V1_YOUNG_BRIDGE_PRIOR_PREVIEW.md"

    write_truth_set_young_bridge_prior(preview_path, result.rows)
    write_truth_set_young_bridge_receipts(receipts_path, result.receipt_rows)
    write_truth_set_young_bridge_flags(flags_path, result.flags)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result.summary, indent=2) + "\n", encoding="utf-8")
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        _markdown_note(result.summary, preview_path, receipts_path, flags_path),
        encoding="utf-8",
    )
    print(json.dumps(result.summary, indent=2))


def _markdown_note(
    summary: dict[str, object],
    preview_path: Path,
    receipts_path: Path,
    flags_path: Path,
) -> str:
    return "\n".join(
        [
            "# Truth Set Lab v1 Young Bridge Prior Preview",
            "",
            "This artifact converts the sixth Truth Set Lab report into preview-only "
            "young-player bridge-prior evidence.",
            "It does not change live model scores, rankings, gates, or receipts used by the app.",
            "",
            "## Outputs",
            "",
            f"- Preview CSV: `{preview_path}`",
            f"- Receipt-style summary: `{receipts_path}`",
            f"- Flags: `{flags_path}`",
            "",
            "## Summary",
            "",
            f"- Rows: {summary['rows']}",
            f"- Source rows: {summary['source_rows']}",
            f"- Missing young bridge rows: {summary['missing_young_bridge_rows']}",
            f"- Scored bridge-prior rows: {summary['scored_bridge_prior_rows']}",
            f"- Established/not-scored rows: {summary['established_not_scored_rows']}",
            f"- Incoming rookies: {summary['incoming_rookie_rows']}",
            f"- Year-one bridge rows: {summary['year_one_rows']}",
            f"- Year-two bridge rows: {summary['year_two_rows']}",
            f"- Year-three bridge rows: {summary['year_three_rows']}",
            "",
            "## Gap-Fill Controls",
            "",
            "The prior missing controls are now present:",
            "",
            "- Jahmyr Gibbs: 2023 round 1 pick 12, Detroit Lions, NFL.com source",
            "- Ashton Jeanty: 2025 round 1 pick 6, Las Vegas Raiders, NFL.com source",
            "- Brock Bowers: 2024 round 1 pick 13, Las Vegas Raiders, NFL.com source",
            "",
            "Only factual draft-capital fields were added for these rows. College "
            "production and athletic testing remain blank/review-only instead of "
            "being invented.",
            "",
            "## Guardrails",
            "",
            "- Draft capital is blank for established veterans.",
            "- Missing report rows stay flagged instead of receiving invented values.",
            "- Subjective prospect notes are display/context only.",
            "- College production and athletic testing are contextual strings, not "
            "normalized scores.",
            "- Model usage status remains `preview_only_not_scoring`.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
