"""Phase 6 local-only production-candidate modeling harness.

This wrapper narrows the committed Phase 5 historical harness to the 5CY
production-candidate head list. It keeps the same source-safe historical
feature/label packages and aggregate-only outputs, while failing closed on
current-player inference, app-readable paths, and non-eligible heads.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from importlib import util
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE5_HARNESS_PATH = REPO_ROOT / "scripts" / "outcome_probability" / "run_sprint_5ct_phase5_candidate_modeling_harness.py"

spec = util.spec_from_file_location("phase5_candidate_harness", PHASE5_HARNESS_PATH)
if spec is None or spec.loader is None:
    raise SystemExit(f"FAIL_CLOSED: unable to load Phase 5 harness from {PHASE5_HARNESS_PATH}")
phase5 = util.module_from_spec(spec)
spec.loader.exec_module(phase5)


PHASE6_APPROVED_HEADS = {
    "qb_t12": ("QB", "same_year_qb_t12"),
    "rb_t12": ("RB", "same_year_rb_t12"),
    "wr_t12": ("WR", "same_year_wr_t12"),
    "wr_t24": ("WR", "same_year_wr_t24"),
    "wr_t36": ("WR", "same_year_wr_t36"),
    "te_t12": ("TE", "same_year_te_t12"),
}

CAUTION_HEADS = {"qb_t18", "qb_t24", "rb_t24", "te_t18", "te_t24"}
DEFERRED_HEADS = {"rb_t36", "rb_t48", "wr_t48"}
BLOCKED_HEADS = {"qb_t6", "rb_t6", "wr_t6", "te_t3", "te_t6"}


def _install_phase6_policy() -> None:
    phase5.APPROVED_HEADS = PHASE6_APPROVED_HEADS
    phase5.DEFERRED_HEADS = CAUTION_HEADS | DEFERRED_HEADS
    phase5.BLOCKED_HEADS = BLOCKED_HEADS
    phase5.write_outputs = write_outputs


def _metric(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def write_outputs(
    output_dir: Path,
    heads: list[str],
    aggregate_rows: list[dict[str, Any]],
    coefficient_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = phase5.summarize(aggregate_rows)
    feature_audit_rows = [
        {
            "output_scope": "internal_only_not_app_readable",
            "feature": feature,
            "approved": "yes",
            "forbidden_term_match": "|".join(term for term in phase5.FORBIDDEN_FEATURE_TERMS if term in feature.lower()),
            "used": "yes",
        }
        for feature in phase5.APPROVED_FEATURES
    ]
    phase5.write_csv(
        output_dir / "aggregate_metrics_by_head_fold_method.csv",
        aggregate_rows,
        [
            "output_scope",
            "head",
            "canonical_head",
            "position",
            "fold",
            "train_seasons",
            "holdout_season",
            "method",
            "score_type",
            "train_rows",
            "train_positives",
            "train_negatives",
            "holdout_rows",
            "holdout_positives",
            "holdout_negatives",
            "auc",
            "pr_auc",
            "brier",
            "log_loss",
            "calibration_bins_populated",
            "calibration_bins_thin",
            "calibration_max_abs_gap",
        ],
    )
    phase5.write_csv(
        output_dir / "head_candidate_verdicts.csv",
        summary_rows,
        [
            "output_scope",
            "head",
            "canonical_head",
            "position",
            "folds",
            "auc_mean",
            "brier_mean",
            "base_brier_mean",
            "log_loss_mean",
            "base_log_loss_mean",
            "thin_calibration_bins",
            "candidate_verdict",
        ],
    )
    phase5.write_csv(
        output_dir / "feature_quarantine_audit.csv",
        feature_audit_rows,
        ["output_scope", "feature", "approved", "forbidden_term_match", "used"],
    )
    phase5.write_csv(
        output_dir / "candidate_logistic_coefficients.csv",
        coefficient_rows,
        ["output_scope", "head", "canonical_head", "position", "fold", "holdout_season", "feature", "coefficient"],
    )
    verdict_counts = Counter(row["candidate_verdict"] for row in summary_rows)
    metadata = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": "phase_6_local_only_production_candidate_modeling",
        "output_scope": "internal_only_not_app_readable",
        "heads_requested": heads,
        "eligible_heads_only": True,
        "caution_heads_excluded": sorted(CAUTION_HEADS),
        "deferred_heads_excluded": sorted(DEFERRED_HEADS),
        "blocked_heads_excluded": sorted(BLOCKED_HEADS),
        "candidate_verdict_counts": dict(verdict_counts),
        "row_level_predictions_exported": False,
        "current_player_inference_performed": False,
        "current_player_probabilities_created": False,
        "app_readable_outputs_created": False,
        "serialized_model_artifacts_created": False,
        "production_model_artifacts_created": False,
        "exact_display_percentages_created": False,
        "coarse_display_bands_created": False,
        "app_wiring_created": False,
        "rankings_sorting_created": False,
        "hidden_sort_keys_created": False,
        "promoted_artifacts_created": False,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Phase 6 local-only production-candidate evidence\n\n"
        "Historical fold aggregate metrics only. This directory is quarantined local evidence, "
        "not app-readable output and not a promoted or production artifact. No current-player "
        "inference, row-level predictions, rankings, hidden sort keys, exact display percentages, "
        "or coarse display bands were created.\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    _install_phase6_policy()
    phase5.main()


if __name__ == "__main__":
    main()
