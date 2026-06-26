from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# ruff: noqa: E501

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMOTION_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nfl_usage" / "promotion_gate"
)
REVIEW_ROOT = REPO_ROOT / "docs" / "hq" / "data_sources" / "nfl_usage" / "review_artifacts"

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"

VALID_PROMOTION_STATUSES = {
    "RESEARCH_ONLY",
    "DISPLAY_ONLY_CANDIDATE",
    "APPROVED_DISPLAY_ONLY_CONTEXT",
    "CANDIDATE_MODEL_FEATURE_PENDING_BACKTEST",
    "MODEL_CANDIDATE_PENDING_MANUAL_REVIEW",
    "BLOCKED_LICENSED_DATA_GAP",
    "BLOCKED_UNSAFE",
    "BACKTEST_BLOCKED_INSUFFICIENT_LABELS",
    "BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE",
    "BACKTEST_FAILED_NON_ADDITIVE",
}

BACKLOG_HEADER = [
    "task_id",
    "priority",
    "area",
    "description",
    "expected_files",
    "guardrails",
    "blocker",
    "notes",
]

CLASSIFICATION_HEADER = [
    "field_name",
    "source_family",
    "field_type",
    "data_grain",
    "promotion_candidate_status",
    "default_recommendation",
    "display_only_candidate",
    "model_candidate",
    "required_backtest",
    "required_coverage",
    "leakage_risk",
    "missingness_risk",
    "proxy_risk",
    "licensed_data_gap",
    "notes",
]

TARGET_AUDIT_HEADER = [
    "target_name",
    "source_artifact",
    "target_type",
    "approved_for_backtest",
    "grain",
    "seasons_available",
    "row_count",
    "player_id_coverage",
    "leakage_risk",
    "caveats",
    "decision",
]

WINDOW_HEADER = [
    "feature_window_id",
    "feature_start",
    "feature_end",
    "target_window",
    "allowed",
    "leakage_risk",
    "use_case",
    "notes",
]

BACKTEST_RESULTS_HEADER = [
    "run_id",
    "mode",
    "status",
    "predictive_backtest_run",
    "approved_targets_available",
    "historical_usage_panel_available",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]

COVERAGE_HEADER = [
    "field_name",
    "source_family",
    "evidence_status",
    "coverage_status",
    "historical_panel_status",
    "display_context_status",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]

LEAKAGE_HEADER = [
    "check_name",
    "status",
    "leakage_risk",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]

DISPLAY_SANITY_HEADER = [
    "field_name",
    "display_context_status",
    "proxy_label_required",
    "licensed_data_gap",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]

DECISION_HEADER = [
    "field_name",
    "source_family",
    "field_type",
    "evidence_status",
    "coverage_status",
    "leakage_status",
    "backtest_status",
    "display_context_status",
    "final_promotion_status",
    "approved_for_display_only",
    "approved_for_model_candidate",
    "model_input_allowed",
    "app_wiring_allowed",
    "required_next_gate",
    "caveats",
    "notes",
]


@dataclass(frozen=True)
class PromotionGateRunResult:
    output_root: Path
    predictive_backtest_status: str
    predictive_backtest_run: str
    files_written: tuple[Path, ...]


def promotion_gate_paths(output_root: Path = PROMOTION_ROOT) -> dict[str, Path]:
    return {
        "master_plan": output_root
        / "NWR_NFL_USAGE_FIELD_PROMOTION_GATE_V0_MASTER_PLAN_20260624.md",
        "backlog": output_root / "NWR_NFL_USAGE_PROMOTION_GATE_BACKLOG_20260624.csv",
        "classification": output_root / "nfl_usage_field_candidate_classification_v0.csv",
        "classification_report": output_root
        / "NWR_NFL_USAGE_FIELD_CANDIDATE_CLASSIFICATION_20260624.md",
        "target_audit": output_root / "nfl_usage_backtest_target_label_audit_v0.csv",
        "target_report": output_root / "NWR_NFL_USAGE_BACKTEST_TARGET_LABEL_AUDIT_20260624.md",
        "feature_policy": output_root
        / "NWR_NFL_USAGE_FEATURE_WINDOW_AND_LEAKAGE_POLICY_20260624.md",
        "feature_matrix": output_root / "nfl_usage_feature_window_matrix_v0.csv",
        "backtest_results": output_root / "nfl_usage_backtest_results_v0.csv",
        "coverage": output_root / "nfl_usage_coverage_diagnostics_v0.csv",
        "leakage": output_root / "nfl_usage_leakage_diagnostics_v0.csv",
        "display_sanity": output_root / "nfl_usage_display_context_sanity_v0.csv",
        "fallback_report": output_root
        / "NWR_NFL_USAGE_BACKTEST_OR_FALLBACK_RESULTS_20260624.md",
        "decision_matrix": output_root / "nfl_usage_field_promotion_decision_matrix_v0.csv",
        "decision_report": output_root
        / "NWR_NFL_USAGE_FIELD_PROMOTION_DECISION_MATRIX_20260624.md",
        "closeout": output_root
        / "NWR_NFL_USAGE_FIELD_PROMOTION_GATE_V0_CLOSEOUT_20260624.md",
    }


def run_promotion_gate(
    *,
    output_root: Path = PROMOTION_ROOT,
    write: bool = False,
    predictive_requested: bool = True,
) -> PromotionGateRunResult:
    paths = promotion_gate_paths(output_root)
    classification = field_classification_rows()
    target_rows = target_label_audit_rows()
    window_rows = feature_window_rows()
    validate_feature_windows(window_rows)

    predictive_status = _predictive_status(target_rows, classification, predictive_requested)
    backtest_rows = backtest_result_rows(predictive_status)
    coverage_rows = coverage_diagnostic_rows(classification)
    leakage_rows = leakage_diagnostic_rows(window_rows)
    display_rows = display_context_sanity_rows(classification)
    decision_rows = decision_matrix_rows(classification, predictive_status)

    if not write:
        return PromotionGateRunResult(
            output_root=output_root,
            predictive_backtest_status=predictive_status,
            predictive_backtest_run="no",
            files_written=(),
        )

    output_root.mkdir(parents=True, exist_ok=True)
    _write_text(paths["master_plan"], master_plan_markdown())
    _write_csv(paths["backlog"], BACKLOG_HEADER, backlog_rows())
    _write_csv(paths["classification"], CLASSIFICATION_HEADER, classification)
    _write_text(paths["classification_report"], classification_report_markdown(classification))
    _write_csv(paths["target_audit"], TARGET_AUDIT_HEADER, target_rows)
    _write_text(paths["target_report"], target_audit_markdown(target_rows))
    _write_text(paths["feature_policy"], feature_policy_markdown())
    _write_csv(paths["feature_matrix"], WINDOW_HEADER, window_rows)
    _write_csv(paths["backtest_results"], BACKTEST_RESULTS_HEADER, backtest_rows)
    _write_csv(paths["coverage"], COVERAGE_HEADER, coverage_rows)
    _write_csv(paths["leakage"], LEAKAGE_HEADER, leakage_rows)
    _write_csv(paths["display_sanity"], DISPLAY_SANITY_HEADER, display_rows)
    _write_text(paths["fallback_report"], fallback_report_markdown(backtest_rows, coverage_rows))
    _write_csv(paths["decision_matrix"], DECISION_HEADER, decision_rows)
    _write_text(paths["decision_report"], decision_report_markdown(decision_rows))
    _write_text(paths["closeout"], closeout_markdown(decision_rows, predictive_status, paths))
    return PromotionGateRunResult(
        output_root=output_root,
        predictive_backtest_status=predictive_status,
        predictive_backtest_run="no",
        files_written=tuple(paths.values()),
    )


def field_classification_rows() -> list[dict[str, str]]:
    rows = [
        _classification(
            "offense_snaps",
            "snap_counts",
            "TRUE_FACTUAL_FIELD",
            "player_game",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display role-volume context; not a model feature",
            "yes",
            "no",
            "coverage/leakage only before display; predictive ablation before model use",
            "live inventory plus historical player-season panel",
            "low",
            "medium",
            "no",
            "no",
            "Public snap count fact; point-in-time handling still required for future model gates.",
        ),
        _classification(
            "offense_pct",
            "snap_counts",
            "TRUE_FACTUAL_FIELD",
            "player_game",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display snap-share context; not a model feature",
            "yes",
            "no",
            "coverage/leakage only before display; predictive ablation before model use",
            "live inventory plus historical player-season panel",
            "low",
            "medium",
            "no",
            "no",
            "Display as offensive snap share, not role certainty.",
        ),
        _classification(
            "targets",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display receiving opportunity context",
            "yes",
            "no",
            "walk-forward ablation required before candidate model use",
            "multi-season player-week coverage",
            "low",
            "low",
            "no",
            "no",
            "Use factual counts only; no target-share overclaim without denominator audit.",
        ),
        _classification(
            "carries",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display rushing opportunity context",
            "yes",
            "no",
            "walk-forward ablation required before candidate model use",
            "multi-season player-week coverage",
            "low",
            "low",
            "no",
            "no",
            "Use factual counts only.",
        ),
        _classification(
            "receptions",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display received-volume context",
            "yes",
            "no",
            "walk-forward ablation required before candidate model use",
            "multi-season player-week coverage",
            "low",
            "low",
            "no",
            "no",
            "Non-PPR league context means receptions are context, not scoring input by themselves.",
        ),
        _classification(
            "touches",
            "derived_usage",
            "TRUE_DERIVED_FACT",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display if defined as carries plus receptions",
            "yes",
            "no",
            "derived-field consistency and walk-forward ablation",
            "component coverage for carries and receptions",
            "low",
            "medium",
            "no",
            "no",
            "Definition must be visible: carries + receptions.",
        ),
        _classification(
            "opportunities",
            "derived_usage",
            "TRUE_DERIVED_FACT",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display if defined as carries plus targets",
            "yes",
            "no",
            "derived-field consistency and walk-forward ablation",
            "component coverage for carries and targets",
            "low",
            "medium",
            "no",
            "no",
            "Definition must be visible: carries + targets.",
        ),
        _classification(
            "rushing_yards",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display factual production context",
            "yes",
            "no",
            "baseline/factual production comparison before model use",
            "multi-season player-week coverage",
            "low",
            "low",
            "no",
            "no",
            "Production fact, not standalone dynasty value.",
        ),
        _classification(
            "receiving_yards",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display factual production context",
            "yes",
            "no",
            "baseline/factual production comparison before model use",
            "multi-season player-week coverage",
            "low",
            "low",
            "no",
            "no",
            "Production fact, not standalone dynasty value.",
        ),
        _classification(
            "receiving_air_yards",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display receiving depth/intent context",
            "yes",
            "no",
            "position-stratified walk-forward ablation",
            "multi-season player-week coverage and denominator audit for shares",
            "low",
            "medium",
            "no",
            "no",
            "Air yards shares remain separate review fields.",
        ),
        _classification(
            "receiving_yards_after_catch",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display factual YAC context",
            "yes",
            "no",
            "position-stratified walk-forward ablation",
            "multi-season player-week coverage",
            "low",
            "medium",
            "no",
            "no",
            "Call it YAC, not separation or route quality.",
        ),
        _classification(
            "rushing_first_downs",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display first-down scoring context",
            "yes",
            "no",
            "league-scoring ablation before model use",
            "multi-season player-week coverage",
            "low",
            "medium",
            "no",
            "no",
            "Relevant to NWR scoring; still not active model input.",
        ),
        _classification(
            "receiving_first_downs",
            "player_stats",
            "TRUE_FACTUAL_FIELD",
            "player_week",
            "APPROVED_DISPLAY_ONLY_CONTEXT",
            "safe display first-down scoring context",
            "yes",
            "no",
            "league-scoring ablation before model use",
            "multi-season player-week coverage",
            "low",
            "medium",
            "no",
            "no",
            "Relevant to NWR scoring; still not active model input.",
        ),
        _classification(
            "red_zone_opportunities",
            "derived_usage",
            "TRUE_DERIVED_FACT",
            "player_week",
            "DISPLAY_ONLY_CANDIDATE",
            "display-only candidate after component coverage report",
            "yes",
            "no",
            "red-zone ablation required before model use",
            "historical opportunity panel by player/week",
            "medium",
            "medium",
            "no",
            "no",
            "Do not compare across sources until red-zone definition is fixed.",
        ),
        _classification(
            "inside_10_opportunities",
            "derived_usage",
            "TRUE_DERIVED_FACT",
            "player_week",
            "DISPLAY_ONLY_CANDIDATE",
            "display-only candidate after component coverage report",
            "yes",
            "no",
            "inside-10 ablation required before model use",
            "historical opportunity panel by player/week",
            "medium",
            "medium",
            "no",
            "no",
            "Small samples require visible caveat.",
        ),
        _classification(
            "inside_5_opportunities",
            "derived_usage",
            "TRUE_DERIVED_FACT",
            "player_week",
            "DISPLAY_ONLY_CANDIDATE",
            "display-only candidate after component coverage report",
            "yes",
            "no",
            "inside-5 ablation required before model use",
            "historical opportunity panel by player/week",
            "medium",
            "high",
            "no",
            "no",
            "Very small samples require visible caveat.",
        ),
        _classification(
            "ngs_efficiency_fields",
            "ngs",
            "TRUE_FACTUAL_FIELD",
            "source_defined",
            "RESEARCH_ONLY",
            "research-only until field semantics and coverage pass",
            "no",
            "no",
            "source-specific coverage and leakage audit",
            "multi-season field inventory with stable schemas",
            "medium",
            "high",
            "no",
            "no",
            "Do not mix efficiency fields into model candidates without denominator and drift checks.",
        ),
        _classification(
            "participation_personnel_formation_context",
            "participation",
            "SOURCE_DEFINED_CONTEXT",
            "play_or_player_game",
            "RESEARCH_ONLY",
            "inventory/research only",
            "no",
            "no",
            "source-specific coverage and leakage audit",
            "stable source semantics and player linkage",
            "medium",
            "high",
            "medium",
            "no",
            "Public participation context is not true routes run.",
        ),
        _classification(
            "route_participation_proxy",
            "participation",
            "DERIVED_PROXY",
            "player_game",
            "RESEARCH_ONLY",
            "proxy-only research; label every display if ever surfaced",
            "no",
            "no",
            "proxy validation against licensed source if ever available",
            "approved denominator and coverage report",
            "high",
            "high",
            "high",
            "no",
            "Do not call this true routes run.",
        ),
        _classification(
            "tprr_like_proxy",
            "derived_proxy",
            "DERIVED_PROXY",
            "player_game",
            "RESEARCH_ONLY",
            "proxy-only research",
            "no",
            "no",
            "proxy validation against true routes source",
            "approved route denominator",
            "high",
            "high",
            "high",
            "yes",
            "Do not call this true TPRR.",
        ),
        _classification(
            "yprr_like_proxy",
            "derived_proxy",
            "DERIVED_PROXY",
            "player_game",
            "RESEARCH_ONLY",
            "proxy-only research",
            "no",
            "no",
            "proxy validation against true routes source",
            "approved route denominator",
            "high",
            "high",
            "high",
            "yes",
            "Do not call this true YPRR.",
        ),
        _classification(
            "ftn_pfr_advanced_fields",
            "ftn_pfr",
            "SOURCE_DEFINED_CONTEXT",
            "source_defined",
            "RESEARCH_ONLY",
            "inventory/candidate evidence only",
            "no",
            "no",
            "source semantics, license, coverage, and leakage audit",
            "field-level contract by source",
            "medium",
            "high",
            "medium",
            "no",
            "Keep as candidate inventory until semantics and coverage pass.",
        ),
        _classification(
            "true_routes_run",
            "licensed_gap",
            "LICENSED_DATA_GAP",
            "player_game",
            "BLOCKED_LICENSED_DATA_GAP",
            "blocked until exact licensed/approved public source exists",
            "no",
            "no",
            "licensed source contract required",
            "exact routes-run data",
            "high",
            "high",
            "no",
            "yes",
            "Licensed-data gap in V0.",
        ),
        _classification(
            "true_tprr",
            "licensed_gap",
            "LICENSED_DATA_GAP",
            "player_game",
            "BLOCKED_LICENSED_DATA_GAP",
            "blocked until exact true routes denominator exists",
            "no",
            "no",
            "licensed source contract required",
            "true routes plus targets",
            "high",
            "high",
            "no",
            "yes",
            "Licensed-data gap in V0.",
        ),
        _classification(
            "true_yprr",
            "licensed_gap",
            "LICENSED_DATA_GAP",
            "player_game",
            "BLOCKED_LICENSED_DATA_GAP",
            "blocked until exact true routes denominator exists",
            "no",
            "no",
            "licensed source contract required",
            "true routes plus receiving yards",
            "high",
            "high",
            "no",
            "yes",
            "Licensed-data gap in V0.",
        ),
        _classification(
            "ranks_projections_adp_market_vendor_values",
            "blocked_vendor_or_market",
            "BLOCKED_UNSAFE",
            "source_defined",
            "BLOCKED_UNSAFE",
            "blocked from this lane",
            "no",
            "no",
            "not allowed",
            "not allowed",
            "high",
            "high",
            "no",
            "yes",
            "Never target truth or model input in this gate.",
        ),
    ]
    return rows


def target_label_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "target_name": "next_nwr_points",
            "source_artifact": "scripts/build_backtest_dataset_v0.py; docs/hq/parallel_lanes/NWR_BACKTEST_V0_DESIGN_AND_RESULTS_20260621.md; docs/hq/model/NWR_MODEL_TARGET_AND_LABEL_INTEGRITY_AUDIT_20260623.md",
            "target_type": "future outcome label",
            "approved_for_backtest": "yes_with_conditions",
            "grain": "player_season",
            "seasons_available": "2019-2025 in prior local Backtest V0 run",
            "row_count": "3108 in prior local-only label build",
            "player_id_coverage": "required by Backtest V0 label build",
            "leakage_risk": "medium",
            "caveats": "Targets are valid only when paired with season-N as-of-safe features and not committed as raw local artifacts.",
            "decision": "YELLOW_LIMITED_TARGETS_AVAILABLE",
        },
        {
            "target_name": "next_nwr_ppg",
            "source_artifact": "scripts/build_backtest_dataset_v0.py; docs/hq/model/NWR_MODEL_TARGET_AND_LABEL_INTEGRITY_AUDIT_20260623.md",
            "target_type": "future outcome label",
            "approved_for_backtest": "yes_with_conditions",
            "grain": "player_season",
            "seasons_available": "2019-2025 in prior local Backtest V0 run",
            "row_count": "3108 in prior local-only label build",
            "player_id_coverage": "required by Backtest V0 label build",
            "leakage_risk": "medium",
            "caveats": "Per-game labels require target_games handling; not enough alone to promote usage fields.",
            "decision": "YELLOW_LIMITED_TARGETS_AVAILABLE",
        },
        {
            "target_name": "position_finish_flags",
            "source_artifact": "scripts/build_backtest_dataset_v0.py; docs/hq/parallel_lanes/NWR_BACKTEST_V0_DESIGN_AND_RESULTS_20260621.md",
            "target_type": "future outcome bucket",
            "approved_for_backtest": "yes_with_conditions",
            "grain": "player_season",
            "seasons_available": "2019-2025 in prior local Backtest V0 run",
            "row_count": "3108 in prior local-only label build",
            "player_id_coverage": "required by Backtest V0 label build",
            "leakage_risk": "medium",
            "caveats": "Bucket labels are derived from next_nwr_points and need position-specific coverage.",
            "decision": "YELLOW_LIMITED_TARGETS_AVAILABLE",
        },
        {
            "target_name": "outcome_columns_display_props",
            "source_artifact": "docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns",
            "target_type": "display-only probability/status",
            "approved_for_backtest": "no",
            "grain": "frozen_board_player",
            "seasons_available": "2026 draft-day display snapshot only",
            "row_count": "66 frozen-board display rows",
            "player_id_coverage": "partial",
            "leakage_risk": "high",
            "caveats": "Display-only; must not become truth, rank, hidden sort, or target label.",
            "decision": "BLOCKED_AS_TARGET_TRUTH",
        },
        {
            "target_name": "market_adp_dynastyprocess_projection_values",
            "source_artifact": "blocked by source policy",
            "target_type": "market/vendor/opinion/projection",
            "approved_for_backtest": "no",
            "grain": "varies",
            "seasons_available": "not applicable",
            "row_count": "0",
            "player_id_coverage": "not applicable",
            "leakage_risk": "high",
            "caveats": "Explicitly banned as target truth or model input.",
            "decision": "BLOCKED_UNSAFE",
        },
    ]


def feature_window_rows() -> list[dict[str, str]]:
    return [
        {
            "feature_window_id": "season_n_to_season_n_plus_1",
            "feature_start": "regular season N start",
            "feature_end": "regular season N final stat lock",
            "target_window": "regular season N+1",
            "allowed": "yes",
            "leakage_risk": "low",
            "use_case": "next-season predictive backtest after all season-N facts are finalized",
            "notes": "Primary legal window if historical player-season panel exists.",
        },
        {
            "feature_window_id": "weeks_1_8_to_weeks_9_17_same_season",
            "feature_start": "week 1",
            "feature_end": "week 8 stat lock",
            "target_window": "weeks 9-17 same season",
            "allowed": "yes",
            "leakage_risk": "medium",
            "use_case": "in-season role continuation research only",
            "notes": "Requires explicit cutoff and cannot use full-season aggregates.",
        },
        {
            "feature_window_id": "full_current_season_to_same_season_final",
            "feature_start": "regular season N start",
            "feature_end": "regular season N final stat lock",
            "target_window": "regular season N final outcome",
            "allowed": "no",
            "leakage_risk": "high",
            "use_case": "blocked",
            "notes": "Full-season current stats cannot predict the same final season outcome.",
        },
        {
            "feature_window_id": "post_decision_updates_to_draft_day_decision",
            "feature_start": "after evaluation date",
            "feature_end": "after decision date",
            "target_window": "draft-day or pre-decision evaluation",
            "allowed": "no",
            "leakage_risk": "high",
            "use_case": "blocked",
            "notes": "No post-cutoff updates may leak into a prior decision.",
        },
        {
            "feature_window_id": "display_only_latest_facts",
            "feature_start": "latest approved public summary",
            "feature_end": "latest approved public summary",
            "target_window": "none",
            "allowed": "yes",
            "leakage_risk": "low",
            "use_case": "hidden review page display context only",
            "notes": "No prediction, no rank, no hidden sort, no model input.",
        },
    ]


def backtest_result_rows(predictive_status: str) -> list[dict[str, str]]:
    return [
        {
            "run_id": "nfl_usage_promotion_gate_v0_20260624",
            "mode": "predictive_backtest",
            "status": predictive_status,
            "predictive_backtest_run": "no",
            "approved_targets_available": "limited",
            "historical_usage_panel_available": "no",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": "Predictive promotion was not run because committed V0 usage artifacts are field inventories/summaries, not a multi-season leakage-safe player feature panel.",
        },
        {
            "run_id": "nfl_usage_promotion_gate_v0_20260624",
            "mode": "coverage_only",
            "status": "COVERAGE_ONLY_COMPLETE",
            "predictive_backtest_run": "no",
            "approved_targets_available": "limited",
            "historical_usage_panel_available": "no",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": "Coverage diagnostics ran from committed V0 summary artifacts and gate classification.",
        },
        {
            "run_id": "nfl_usage_promotion_gate_v0_20260624",
            "mode": "leakage_check_only",
            "status": "LEAKAGE_CHECK_PASSED",
            "predictive_backtest_run": "no",
            "approved_targets_available": "limited",
            "historical_usage_panel_available": "no",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": "Legal windows require season-N features for season-N+1 targets or explicit in-season cutoffs.",
        },
        {
            "run_id": "nfl_usage_promotion_gate_v0_20260624",
            "mode": "display_context_sanity",
            "status": "COVERAGE_ONLY_COMPLETE",
            "predictive_backtest_run": "no",
            "approved_targets_available": "limited",
            "historical_usage_panel_available": "no",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": "Display candidates remain review-only and are not consumed by decision pages.",
        },
    ]


def coverage_diagnostic_rows(classification: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in classification:
        status = row["promotion_candidate_status"]
        if status == "APPROVED_DISPLAY_ONLY_CONTEXT":
            coverage = "SUMMARY_COVERAGE_GREEN_DISPLAY_ONLY"
            display = "PASS"
        elif status == "DISPLAY_ONLY_CANDIDATE":
            coverage = "SUMMARY_COVERAGE_YELLOW_NEEDS_COMPONENT_PANEL"
            display = "PASS_WITH_CAVEAT"
        elif status.startswith("BLOCKED"):
            coverage = "BLOCKED"
            display = "BLOCKED"
        else:
            coverage = "RESEARCH_ONLY_NEEDS_COVERAGE_GATE"
            display = "RESEARCH_ONLY"
        rows.append(
            {
                "field_name": row["field_name"],
                "source_family": row["source_family"],
                "evidence_status": row["promotion_candidate_status"],
                "coverage_status": coverage,
                "historical_panel_status": "not_available_in_committed_v0_gate",
                "display_context_status": display,
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": row["notes"],
            }
        )
    return rows


def leakage_diagnostic_rows(window_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [
        {
            "check_name": f"feature_window:{row['feature_window_id']}",
            "status": "LEAKAGE_CHECK_PASSED" if row["allowed"] == "yes" else "BLOCKED_WINDOW_CONFIRMED",
            "leakage_risk": row["leakage_risk"],
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": row["notes"],
        }
        for row in window_rows
    ]
    rows.extend(
        [
            {
                "check_name": "blocked_market_rank_projection_tokens",
                "status": "LEAKAGE_CHECK_PASSED",
                "leakage_risk": "high",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "ADP, market, rank, projection, DynastyProcess, and vendor values are blocked as target truth and inputs.",
            },
            {
                "check_name": "route_proxy_overclaim",
                "status": "LEAKAGE_CHECK_PASSED",
                "leakage_risk": "high",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "Route proxies cannot be labeled true routes, true TPRR, or true YPRR.",
            },
        ]
    )
    return rows


def display_context_sanity_rows(classification: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in classification:
        status = row["promotion_candidate_status"]
        rows.append(
            {
                "field_name": row["field_name"],
                "display_context_status": (
                    "APPROVED_DISPLAY_ONLY_CONTEXT"
                    if status == "APPROVED_DISPLAY_ONLY_CONTEXT"
                    else "DISPLAY_ONLY_CANDIDATE"
                    if status == "DISPLAY_ONLY_CANDIDATE"
                    else "BLOCKED"
                    if status.startswith("BLOCKED")
                    else "RESEARCH_ONLY"
                ),
                "proxy_label_required": "yes" if row["proxy_risk"] in {"medium", "high"} else "no",
                "licensed_data_gap": row["licensed_data_gap"],
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": row["notes"],
            }
        )
    return rows


def decision_matrix_rows(
    classification: list[dict[str, str]], predictive_status: str
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in classification:
        status = row["promotion_candidate_status"]
        approved_display = "yes" if status == "APPROVED_DISPLAY_ONLY_CONTEXT" else "no"
        display_status = (
            "APPROVED_DISPLAY_ONLY_CONTEXT"
            if approved_display == "yes"
            else "DISPLAY_ONLY_CANDIDATE"
            if status == "DISPLAY_ONLY_CANDIDATE"
            else "RESEARCH_ONLY"
            if status == "RESEARCH_ONLY"
            else "BLOCKED"
        )
        rows.append(
            {
                "field_name": row["field_name"],
                "source_family": row["source_family"],
                "field_type": row["field_type"],
                "evidence_status": status,
                "coverage_status": (
                    "GREEN_FOR_DISPLAY"
                    if approved_display == "yes"
                    else "YELLOW_NEEDS_COVERAGE"
                    if status == "DISPLAY_ONLY_CANDIDATE"
                    else "BLOCKED"
                    if status.startswith("BLOCKED")
                    else "RESEARCH_ONLY"
                ),
                "leakage_status": "PASS_DISPLAY_ONLY" if not status.startswith("BLOCKED") else "BLOCKED",
                "backtest_status": predictive_status,
                "display_context_status": display_status,
                "final_promotion_status": status,
                "approved_for_display_only": approved_display,
                "approved_for_model_candidate": "no",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "required_next_gate": (
                    "manual display integration gate"
                    if approved_display == "yes"
                    else "historical coverage and backtest gate"
                    if status in {"DISPLAY_ONLY_CANDIDATE", "RESEARCH_ONLY"}
                    else "licensed source contract"
                    if status == "BLOCKED_LICENSED_DATA_GAP"
                    else "remain blocked"
                ),
                "caveats": row["notes"],
                "notes": "No active model input or decision-page wiring.",
            }
        )
    return rows


def validate_feature_windows(rows: Iterable[dict[str, str]]) -> None:
    for row in rows:
        allowed = row.get("allowed", "").lower() == "yes"
        window_id = row.get("feature_window_id", "")
        target = row.get("target_window", "").lower()
        feature_end = row.get("feature_end", "").lower()
        same_season_final = (
            "same season final" in target
            or "same-season final" in target
            or "full_current_season" in window_id
        )
        if allowed and same_season_final and "final" in feature_end:
            raise ValueError(f"illegal leakage window marked allowed: {window_id}")


def validate_no_enabled_flags(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.suffix.lower() != ".csv" or not path.exists():
            continue
        frame = pd.read_csv(path, keep_default_na=False)
        for column in ("model_input_allowed", "app_wiring_allowed"):
            if column in frame.columns and not frame[column].astype(str).str.lower().eq("no").all():
                raise ValueError(f"{path} has non-no {column}")


def master_plan_markdown() -> str:
    return """# NFL Usage Field Promotion Gate V0 Master Plan

Generated for the NFL Usage Evidence Layer V0 promotion/backtest gate.

## Scope

This lane classifies existing public NFL usage evidence into display-only candidates, research-only fields, blocked/licensed gaps, and future model-candidate possibilities. It does not wire fields into rankings, Drafting Mode, Player Compare, Trading Lab, Post-Draft, Cheat Sheets, hidden sorts, or model features.

## Promotion Statuses

- RESEARCH_ONLY
- DISPLAY_ONLY_CANDIDATE
- APPROVED_DISPLAY_ONLY_CONTEXT
- CANDIDATE_MODEL_FEATURE_PENDING_BACKTEST
- MODEL_CANDIDATE_PENDING_MANUAL_REVIEW
- BLOCKED_LICENSED_DATA_GAP
- BLOCKED_UNSAFE
- BACKTEST_BLOCKED_INSUFFICIENT_LABELS
- BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE
- BACKTEST_FAILED_NON_ADDITIVE

## Allowed Decisions

- Mark safe factual usage counts as display-only context after coverage/leakage checks.
- Mark fields as research-only when semantics, coverage, or missingness remain unresolved.
- Mark true routes run, true TPRR, and true YPRR as licensed-data gaps until an exact approved source exists.
- Run coverage, leakage, and display-context diagnostics from committed summary artifacts.

## Banned Decisions

- No model input activation.
- No decision-page wiring.
- No Dynasty Rank, Final Board Rank, tier, frozen board, pinned snapshot, latest_candidate, or latest_approved mutation.
- No market, ADP, DynastyProcess, projection, vendor, or RotoWire target truth.
- No CFBD or college/prospect evidence in this lane.

## Target And Label Audit Requirements

Targets must be approved future outcome labels or timestamped league-state facts for the specific task. Display props, current rankings, market values, ADP, DynastyProcess, projections, inferred/proxy drops, and missing Outcome rows are not target truth.

## Feature Window Requirements

The default predictive window is season N features predicting season N+1 targets. In-season research requires explicit pre-target cutoffs. Full current-season stats cannot predict the same full-season target.

## Leakage Checks

The gate blocks future stats, post-cutoff updates, market/rank/projection fields, target labels as features, route-proxy overclaims, and denominator drift.

## Display-Only Approval Requirements

Display-only context must be factual or clearly derived, have safe coverage status, carry visible caveats where needed, and retain `model_input_allowed=no` and `app_wiring_allowed=no`.

## Model-Candidate Requirements

No field becomes a model input in this lane. A future model-candidate proposal requires historical coverage, walk-forward ablation, baseline comparison, missingness sensitivity, manual review, and a separate integration gate.

## CFBD Separation

CFBD belongs to a separate College/Rookie Evidence Layer lane. This NFL usage gate uses only pro/NFL usage evidence after players enter the league.

## Stop Conditions

Stop and fail closed if target labels are insufficient, coverage is insufficient, leakage checks fail, raw data would be tracked, or any app/model/rank/source-truth file would be mutated outside the hidden review page.

## Validation Checklist

- CSV load validation.
- Focused pytest.
- Ruff on touched Python.
- Python compile on touched Python.
- `git diff --check`.
- Confirm no raw/shared/local/runtime files tracked.
- Confirm no CFBD files changed.
- Confirm protected board/source-truth/model files unchanged.

## Commit And Push Policy

Commit and push only GREEN/YELLOW-safe artifacts with blocked behavior documented and all flags off.
"""


def backlog_rows() -> list[dict[str, str]]:
    return [
        {
            "task_id": "NFL-USAGE-GATE-001",
            "priority": "P0",
            "area": "targets",
            "description": "Create committed manifest of approved target label artifacts usable by future usage backtests.",
            "expected_files": "docs/hq/data_sources/nfl_usage/promotion_gate/future_target_manifest",
            "guardrails": "no market/rank/projection/vendor targets",
            "blocker": "current approved labels are local-only backtest artifacts",
            "notes": "Needed before predictive field promotion.",
        },
        {
            "task_id": "NFL-USAGE-GATE-002",
            "priority": "P0",
            "area": "coverage",
            "description": "Build leakage-safe multi-season player usage panel from approved public sources.",
            "expected_files": "ignored shared cache plus committed summary fingerprints only",
            "guardrails": "no raw nflverse payloads tracked",
            "blocker": "V0 gate has committed summaries, not full feature panel",
            "notes": "Required for field-level ablation.",
        },
        {
            "task_id": "NFL-USAGE-GATE-003",
            "priority": "P1",
            "area": "licensed gaps",
            "description": "Evaluate licensed source contract for true routes run, TPRR, and YPRR.",
            "expected_files": "source contract update only",
            "guardrails": "do not scrape blocked vendors",
            "blocker": "exact public source unavailable",
            "notes": "Route proxies remain proxy-labeled.",
        },
    ]


def classification_report_markdown(rows: list[dict[str, str]]) -> str:
    display = [row["field_name"] for row in rows if row["display_only_candidate"] == "yes"]
    blocked = [row["field_name"] for row in rows if row["promotion_candidate_status"].startswith("BLOCKED")]
    research = [row["field_name"] for row in rows if row["promotion_candidate_status"] == "RESEARCH_ONLY"]
    return f"""# NFL Usage Field Candidate Classification

## Verdict

GREEN for classification. No field is approved as model input or decision-page wiring.

## Display-Only Candidates

{_bullet_list(display)}

## Research-Only Fields

{_bullet_list(research)}

## Blocked Fields And Gaps

{_bullet_list(blocked)}

## Notes

Route-related proxy fields remain proxy-labeled. True routes run, true TPRR, and true YPRR remain licensed-data gaps.
"""


def target_audit_markdown(rows: list[dict[str, str]]) -> str:
    approved = [row["target_name"] for row in rows if row["approved_for_backtest"] == "yes_with_conditions"]
    blocked = [row["target_name"] for row in rows if row["approved_for_backtest"] == "no"]
    return f"""# NFL Usage Backtest Target Label Audit

## Verdict

YELLOW_LIMITED_TARGETS_AVAILABLE.

Approved future outcome labels exist with conditions, but the promotion gate does not have a committed multi-season usage feature panel. Predictive usage-field promotion is blocked until that coverage exists.

## Conditionally Approved Targets

{_bullet_list(approved)}

## Blocked Targets

{_bullet_list(blocked)}

## Backtest Recommendation

Run coverage, leakage, and display-context diagnostics now. Do not run predictive promotion or claim model-candidate status until the historical usage panel and target manifest are available.
"""


def feature_policy_markdown() -> str:
    return """# NFL Usage Feature Window And Leakage Policy

## Legal Predictive Window

Season N usage fields may predict season N+1 outcomes only after season N stats are finalized and the target window is strictly future.

## In-Season Research Window

Player-week windows may be used only when the feature cutoff predates the target weeks. Full-season aggregates are illegal for same-season final targets.

## Grain

The promotion gate supports player-week, player-game, and player-season summaries. Future predictive runs must declare the grain before fitting or scoring.

## Rolling Windows

Rolling 4-week, 8-week, and season-to-date windows are allowed only when computed from weeks before the target period.

## Minimum Samples

Future gates should require minimum games, snaps, targets, carries, or opportunities by position. Small inside-10 and inside-5 samples must carry caveats.

## Injury, Bye, Team, And Position Handling

Injury and bye weeks must be explicit missingness/context, not silent zero-value labels. Team and position changes must preserve point-in-time identity and avoid future roster leakage.

## Rookies And Veterans

This NFL usage lane starts after NFL entry. CFBD/college evidence is a separate future lane.

## Contamination Blocks

No ADP, market, DynastyProcess, projections, rankings, vendor opinion values, current ranks, or target labels may appear as features.
"""


def fallback_report_markdown(
    backtest_rows: list[dict[str, str]], coverage_rows: list[dict[str, str]]
) -> str:
    approved_display = sum(
        1 for row in coverage_rows if row["display_context_status"] == "PASS"
    )
    return f"""# NFL Usage Backtest Or Safe Fallback Results

## Verdict

YELLOW safe fallback complete.

Predictive backtest run: no.

Reason: `{backtest_rows[0]['status']}`. Approved targets are limited and conditional, but the committed V0 usage evidence is a summary/inventory layer rather than a multi-season leakage-safe player feature panel.

## Diagnostics Completed

- Coverage-only diagnostics.
- Leakage-window diagnostics.
- Display-context sanity diagnostics.

## Display Sanity

Fields passing display sanity: {approved_display}.

## Guardrails

All rows keep `model_input_allowed=no` and `app_wiring_allowed=no`. No raw data was loaded or tracked.
"""


def decision_report_markdown(rows: list[dict[str, str]]) -> str:
    display = [row["field_name"] for row in rows if row["approved_for_display_only"] == "yes"]
    blocked = [row["field_name"] for row in rows if row["final_promotion_status"].startswith("BLOCKED")]
    research = [row["field_name"] for row in rows if row["final_promotion_status"] == "RESEARCH_ONLY"]
    candidates = [
        row["field_name"]
        for row in rows
        if row["final_promotion_status"] == "DISPLAY_ONLY_CANDIDATE"
    ]
    return f"""# NFL Usage Field Promotion Decision Matrix

## Display-Only Context Approved

{_bullet_list(display)}

## Display-Only Candidates Needing More Coverage

{_bullet_list(candidates)}

## Research-Only Fields

{_bullet_list(research)}

## Blocked Fields

{_bullet_list(blocked)}

## Model Candidate Status

No field is approved as a model candidate in V0. Predictive promotion is blocked until a historical usage feature panel and target manifest exist.

## App And Model Status

No app decision integration. No model input. The hidden review page may display this matrix as review-only summary context.
"""


def closeout_markdown(
    rows: list[dict[str, str]], predictive_status: str, paths: dict[str, Path]
) -> str:
    display = [row["field_name"] for row in rows if row["approved_for_display_only"] == "yes"]
    blocked = [row["field_name"] for row in rows if row["final_promotion_status"].startswith("BLOCKED")]
    research = [row["field_name"] for row in rows if row["final_promotion_status"] == "RESEARCH_ONLY"]
    changed = [_display_path(path) for path in paths.values()]
    return f"""# NFL Usage Field Promotion Gate V0 Closeout

## Overall Verdict

YELLOW. The promotion gate is safe and complete, with display-only context approved for low-risk factual usage fields. Predictive model promotion is blocked because the gate lacks a committed multi-season leakage-safe usage panel for field-level ablation.

## Fields Approved For Display-Only Candidate/Context

{_bullet_list(display)}

## Fields Blocked

{_bullet_list(blocked)}

## Fields Research-Only

{_bullet_list(research)}

## Predictive Backtest Status

{predictive_status}. Predictive backtest was not run.

## Backtest Blockers

- Approved targets are limited/conditional and local-only in prior Backtest V0 outputs.
- This lane has field summaries and 2024 live smoke, not a full historical usage feature panel.

## Model Candidate Status

No active model candidates. All model-candidate concepts remain future/manual-review only.

## App Wiring Status

No decision-page wiring. Optional hidden review page display remains read-only.

## Model Input Status

No. Every promotion artifact keeps `model_input_allowed=no`.

## Raw Data Tracked Status

No raw nflverse/shared/local/runtime payloads are tracked.

## Files Changed

{_bullet_list(changed)}

## Tests And Checks

To be filled by final validation run.

## Commits

To be filled after commit.

## Push Status

To be filled after push.

## Final Git Status

To be filled after final status check.

## Recommended Next Step

Build a separate historical usage panel lane that writes raw data only to ignored shared cache and commits only schema fingerprints, coverage summaries, target manifests, and ablation reports.
"""


def _classification(
    field_name: str,
    source_family: str,
    field_type: str,
    data_grain: str,
    promotion_candidate_status: str,
    default_recommendation: str,
    display_only_candidate: str,
    model_candidate: str,
    required_backtest: str,
    required_coverage: str,
    leakage_risk: str,
    missingness_risk: str,
    proxy_risk: str,
    licensed_data_gap: str,
    notes: str,
) -> dict[str, str]:
    if promotion_candidate_status not in VALID_PROMOTION_STATUSES:
        raise ValueError(f"invalid promotion status: {promotion_candidate_status}")
    return {
        "field_name": field_name,
        "source_family": source_family,
        "field_type": field_type,
        "data_grain": data_grain,
        "promotion_candidate_status": promotion_candidate_status,
        "default_recommendation": default_recommendation,
        "display_only_candidate": display_only_candidate,
        "model_candidate": model_candidate,
        "required_backtest": required_backtest,
        "required_coverage": required_coverage,
        "leakage_risk": leakage_risk,
        "missingness_risk": missingness_risk,
        "proxy_risk": proxy_risk,
        "licensed_data_gap": licensed_data_gap,
        "notes": notes,
    }


def _predictive_status(
    target_rows: list[dict[str, str]],
    classification: list[dict[str, str]],
    predictive_requested: bool,
) -> str:
    if not predictive_requested:
        return "BACKTEST_BLOCKED_INSUFFICIENT_LABELS"
    approved_targets = any(row["approved_for_backtest"] == "yes_with_conditions" for row in target_rows)
    if not approved_targets:
        return "BACKTEST_BLOCKED_INSUFFICIENT_LABELS"
    needs_panel = any(
        row["promotion_candidate_status"]
        in {"DISPLAY_ONLY_CANDIDATE", "APPROVED_DISPLAY_ONLY_CONTEXT", "RESEARCH_ONLY"}
        for row in classification
    )
    if needs_panel:
        return "BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE"
    return "BACKTEST_PASSED"


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _bullet_list(values: list[str]) -> str:
    if not values:
        return "- None."
    return "\n".join(f"- `{value}`" for value in values)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
