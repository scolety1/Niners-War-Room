from __future__ import annotations

# ruff: noqa: E402,I001

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.truth_set_safe_preview_service import (
    create_truth_set_safe_model_preview,
    write_safe_preview_comparison,
    write_safe_preview_source_log,
    write_safe_preview_summary,
)


TRUTH_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v1"
REPORTS_ROOT = TRUTH_ROOT / "reports"
ACTIVE_ROOT = ROOT / "local_exports" / "active_veteran_model_public_sources"
MODEL_PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
DOCS_ROOT = ROOT / "docs" / "codex"


def main() -> None:
    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    preview_id = "truth_set_safe_inputs_" + computed_at.replace("-", "").replace(":", "")
    preview_id = preview_id.replace("Z", "")
    result = create_truth_set_safe_model_preview(
        active_output_path=ACTIVE_ROOT / "stats_first_veteran_model_preview_outputs.csv",
        active_normalized_path=ACTIVE_ROOT / "stats_first_normalized_features.csv",
        projection_preview_path=REPORTS_ROOT / "projection_recompute_preview.csv",
        young_bridge_preview_path=REPORTS_ROOT / "young_bridge_prior_preview.csv",
        injury_path=TRUTH_ROOT / "source_clean" / "injury.csv",
        market_path=TRUTH_ROOT / "source_clean" / "trade_liquidity.csv",
        production_path=TRUTH_ROOT / "source_clean" / "production_data.csv",
        output_root=MODEL_PREVIEW_ROOT,
        preview_id=preview_id,
        computed_at=computed_at,
    )
    comparison_path = result.preview_path / "truth_set_safe_preview_comparison.csv"
    source_log_path = result.preview_path / "truth_set_safe_preview_source_log.csv"
    summary_path = result.preview_path / "truth_set_safe_preview_summary.csv"
    note_path = DOCS_ROOT / "TRUTH_SET_LAB_V1_SAFE_INPUTS_MODEL_PREVIEW.md"
    write_safe_preview_comparison(comparison_path, result.comparison_rows)
    write_safe_preview_source_log(source_log_path, result.source_log_rows)
    write_safe_preview_summary(summary_path, result.summary)
    note_path.write_text(_markdown_note(result, comparison_path, source_log_path), encoding="utf-8")
    print(result.summary)


def _markdown_note(result, comparison_path: Path, source_log_path: Path) -> str:
    source_log_rows = result.source_log_rows
    projection_quality_counts = {
        "missing_first_down_projection": sum(
            row["source"] == "projection_quality_missing_first_down_projection"
            for row in source_log_rows
        ),
        "missing_projection": sum(
            row["source"] == "projection_quality_missing_projection"
            for row in source_log_rows
        ),
        "team_mismatch": sum(
            row["source"] == "projection_quality_team_mismatch"
            for row in source_log_rows
        ),
        "high_active_value_missing_projection": sum(
            row["source"] == "projection_quality_high_active_value_missing_projection"
            for row in source_log_rows
        ),
    }
    return "\n".join(
        [
            "# Truth Set Lab v1 Safe Inputs Model Preview",
            "",
            "This preview applies only approved Truth Set Lab fields to the stats-first "
            "preview pipeline. It does not overwrite active rankings or unlock gates.",
            "",
            "## Outputs",
            "",
            f"- Preview folder: `{result.preview_path}`",
            f"- Model outputs: `{result.output_path}`",
            f"- Contribution receipts: `{result.contribution_path}`",
            f"- Normalized features: `{result.normalized_path}`",
            f"- Before/after comparison: `{comparison_path}`",
            f"- Source usage/rejection log: `{source_log_path}`",
            "",
            "## Summary",
            "",
            f"- Truth-set players: {result.summary['truth_set_players']}",
            f"- Truth-set rows overlayed: {result.summary['truth_set_rows_overlayed']}",
            f"- Projection rows applied: {result.summary['projection_rows_applied']}",
            f"- Young bridge rows applied: {result.summary['young_bridge_rows_applied']}",
            f"- Market context rows applied: {result.summary['market_context_rows_applied']}",
            f"- Rejected production rows: {result.summary['rejected_production_rows']}",
            f"- Large value-change rows: {result.summary['large_value_change_rows']}",
            "",
            "## Projection Quality Flags",
            "",
            "Projection quality flags are retained in the safe preview source log and "
            "receipt inputs. They are review signals only and do not unlock "
            "decision-ready status.",
            "",
            "- Missing first-down projection flags: "
            f"{projection_quality_counts['missing_first_down_projection']}",
            "- Missing offensive projection flags: "
            f"{projection_quality_counts['missing_projection']}",
            f"- Team-mismatch flags: {projection_quality_counts['team_mismatch']}",
            "- High-active-value missing-projection flags: "
            f"{projection_quality_counts['high_active_value_missing_projection']}",
            "",
            "Known projection team mismatches:",
            "",
            "- David Montgomery: projection `HOU`, active model `DET`",
            "- Romeo Doubs: projection `NE`, active model `GB`",
            "- Wan'Dale Robinson: projection `TEN`, active model `NYG`",
            "",
            "## Young Bridge Gap Fill",
            "",
            "The sixth-report gap-fill controls for Jahmyr Gibbs, Ashton Jeanty, "
            "and Brock Bowers are now present in the preview source. Only factual "
            "draft year, round, pick, team, and source URLs were added; college "
            "production and athletic testing remain blank/review-only for those "
            "gap-fill rows.",
            "",
            "## Guardrails",
            "",
            "- Rejected production fields are not imported.",
            "- Unsafe RB role text is not imported as numeric workload data.",
            "- Market rows are trade context only.",
            "- Injury rows are confidence/context only.",
            "- Active app rankings remain review-only.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
