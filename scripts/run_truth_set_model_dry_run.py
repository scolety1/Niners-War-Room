from __future__ import annotations

# ruff: noqa: E402,I001

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.truth_set_model_dry_run_service import (
    build_truth_set_model_dry_run,
    write_truth_set_model_dry_run,
    write_truth_set_model_dry_run_rejections,
    write_truth_set_model_dry_run_summary,
    write_truth_set_model_dry_run_summary_json,
)


TRUTH_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v1"
REPORTS_ROOT = TRUTH_ROOT / "reports"
ACTIVE_ROOT = ROOT / "local_exports" / "active_veteran_model_public_sources"
DOCS_ROOT = ROOT / "docs" / "codex"


def main() -> None:
    result = build_truth_set_model_dry_run(
        active_output_path=ACTIVE_ROOT / "stats_first_veteran_model_preview_outputs.csv",
        normalized_features_path=ACTIVE_ROOT / "stats_first_normalized_features.csv",
        projection_preview_path=REPORTS_ROOT / "projection_recompute_preview.csv",
        young_bridge_preview_path=REPORTS_ROOT / "young_bridge_prior_preview.csv",
        production_clean_path=TRUTH_ROOT / "source_clean" / "production_data.csv",
        injury_path=TRUTH_ROOT / "source_clean" / "injury.csv",
        trade_liquidity_path=TRUTH_ROOT / "source_clean" / "trade_liquidity.csv",
    )
    dry_run_path = REPORTS_ROOT / "truth_set_model_dry_run_preview.csv"
    rejected_path = REPORTS_ROOT / "truth_set_model_dry_run_rejected_fields.csv"
    summary_csv_path = REPORTS_ROOT / "truth_set_model_dry_run_summary.csv"
    summary_json_path = REPORTS_ROOT / "truth_set_model_dry_run_summary.json"
    note_path = DOCS_ROOT / "TRUTH_SET_LAB_V1_MODEL_DRY_RUN_PREVIEW.md"

    write_truth_set_model_dry_run(dry_run_path, result.rows)
    write_truth_set_model_dry_run_rejections(rejected_path, result.rejected_rows)
    write_truth_set_model_dry_run_summary(summary_csv_path, result.summary)
    write_truth_set_model_dry_run_summary_json(summary_json_path, result.summary)
    note_path.write_text(
        _markdown_note(result.summary, dry_run_path, rejected_path),
        encoding="utf-8",
    )
    print(result.summary)


def _markdown_note(summary: dict[str, object], dry_run_path: Path, rejected_path: Path) -> str:
    return "\n".join(
        [
            "# Truth Set Lab v1 Model Dry Run Preview",
            "",
            "This is a preview-only model dry run. It does not overwrite active rankings, "
            "app outputs, model gates, or roster decisions.",
            "",
            "## Outputs",
            "",
            f"- Dry-run CSV: `{dry_run_path}`",
            f"- Rejected fields CSV: `{rejected_path}`",
            "",
            "## Summary",
            "",
            f"- Rows: {summary['rows']}",
            f"- Players with active model row: {summary['players_with_active_model_row']}",
            f"- Large-change rows: {summary['large_change_rows']}",
            f"- Projection recompute rows used: {summary['projection_recompute_rows_used']}",
            f"- Young bridge rows used: {summary['young_bridge_rows_used']}",
            f"- Production fields rejected: {summary['production_fields_rejected']}",
            "",
            "## Guardrails",
            "",
            "- Rejected production columns remain rejected.",
            "- Supplied projection point totals remain rejected.",
            "- Projection value comes from recomputed no-PPR LVE points only.",
            "- Young bridge prior is applied only to eligible young players.",
            "- Injury and market sources are confidence/context only.",
            "- This report is for audit, not promotion.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
