from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_evidence_matrix_service import (
    load_formula_admitted_prospect_rows,
)

DEFAULT_EVIDENCE_ROOT = Path("local_exports/model_v4/evidence_matrices/latest")
DEFAULT_FIRST_DOWN_ROOT = Path("local_exports/model_v4/first_downs/latest")
DEFAULT_RETURN_ROOT = Path("local_exports/model_v4/returns/latest")
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/formula_contract/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_11A_FORMULA_CONTRACT.md")

NFL_MATRIX = (
    "local_exports/model_v4/evidence_matrices/latest/"
    "nfl_player_current_evidence_matrix.csv"
)
ADMITTED_PROSPECT_MATRIX = (
    "local_exports/model_v4/evidence_matrices/latest/"
    "admitted_prospect_current_feature_matrix.csv"
)
ROOKIE_AGE_SOURCE = "local_exports/model_v4/prospect_age/latest/player_age_2026.csv"
SLEEPER_PLAYER_AGE_SOURCE = (
    "local_exports/model_v4/prospect_age/latest/"
    "sleeper_player_age_supplement_20260528.csv"
)
DRAFT_CAPITAL_SOURCE = (
    "local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv"
)
ADMITTED_PROSPECT_PRIOR_PRIVATE_INPUTS = {
    ADMITTED_PROSPECT_MATRIX,
    ROOKIE_AGE_SOURCE,
    DRAFT_CAPITAL_SOURCE,
}
FULL_PROSPECT_MATRIX = (
    "local_exports/model_v4/evidence_matrices/latest/prospect_current_feature_matrix.csv"
)
HISTORICAL_BACKTEST_MATRIX = (
    "local_exports/model_v4/evidence_matrices/latest/"
    "historical_rookie_backtest_feature_matrix.csv"
)
SOURCE_COVERAGE_MATRIX = (
    "local_exports/model_v4/evidence_matrices/latest/source_coverage_matrix.csv"
)
WARNING_MATRIX = "local_exports/model_v4/evidence_matrices/latest/warning_matrix.csv"
ADMITTED_RUSHING_FIRST_DOWNS = (
    "local_exports/model_v4/first_downs/latest/admitted_rushing_first_downs.csv"
)
ADMITTED_RECEIVING_FIRST_DOWNS = (
    "local_exports/model_v4/first_downs/latest/admitted_receiving_first_downs.csv"
)
CANONICAL_RUSHING_FIRST_DOWNS = (
    "local_exports/model_v4/first_downs/latest/canonical_rushing_first_downs.csv"
)
CANONICAL_RECEIVING_FIRST_DOWNS = (
    "local_exports/model_v4/first_downs/latest/canonical_receiving_first_downs.csv"
)
ADMITTED_RETURN_SCORING = (
    "local_exports/model_v4/returns/latest/admitted_return_scoring_evidence.csv"
)
CANONICAL_RETURN_STATS = "local_exports/model_v4/returns/latest/canonical_return_stats.csv"
REPLACEMENT_VORP_PLAYER_ROWS = (
    "local_exports/model_v4/replacement_vorp/latest/player_vorp_review_rows.csv"
)

FORMULA_ALLOWED_FIELD_REGISTRY_HEADER = (
    "module_name",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "field_purpose",
    "private_value_allowed",
    "review_only_allowed",
    "market_or_projection_allowed",
    "missing_value_policy",
    "source_status_requirement",
    "receipt_requirement",
)

FORMULA_BLOCKED_FIELD_REGISTRY_HEADER = (
    "module_name",
    "blocked_input_file",
    "blocked_lane",
    "blocked_field_or_json_path",
    "block_reason",
    "private_value_blocked",
    "review_only_exception",
)

FORMULA_LOADER_GUARD_REPORT_HEADER = (
    "check_name",
    "status",
    "issue_count",
    "detail",
)

REQUIRED_MODULES = (
    "replacement_vorp_core",
    "rb_current_value",
    "wr_current_value",
    "qb_current_value",
    "te_current_value",
    "lifecycle_archetype",
    "confidence_missingness",
    "first_down_scoring_evidence",
    "return_scoring_evidence",
    "prospect_prior",
    "rookie_context_review",
)

PRIVATE_VALUE_LANES = {
    "factual_evidence_json",
    "derived_evidence_json",
    "prospect_prior_evidence_json",
    "admitted_first_down_view",
    "admitted_return_view",
    "row_metadata",
}

GENERIC_JSON_PATHS = {
    "factual_evidence_json",
    "factual_evidence_json.*",
    "derived_evidence_json",
    "derived_evidence_json.*",
    "prospect_prior_evidence_json",
    "prospect_prior_evidence_json.*",
    "context_fields_json",
    "context_fields_json.*",
    "market_context_fields_json",
    "market_context_fields_json.*",
}

PRIVATE_BLOCKED_TOKENS = (
    "adp",
    "rank",
    "ranking",
    "projection",
    "projected",
    "mock",
    "big_board",
    "cheatsheet",
    "consensus",
    "market_context",
    "market_liquidity",
)

WORKOUT_ZERO_PLACEHOLDER_FIELDS = (
    "height",
    "height_inches",
    "weight",
    "arm",
    "hand",
    "forty",
    "forty_pct",
    "shuttle",
    "shuttle_pct",
    "cone",
    "cone_pct",
    "vertical",
    "vertical_pct",
    "broad",
    "broad_pct",
    "bench",
    "bench_pct",
)


@dataclass(frozen=True)
class FormulaAllowedFieldRule:
    module_name: str
    allowed_input_file: str
    allowed_lane: str
    allowed_field_or_json_path: str
    field_purpose: str
    private_value_allowed: bool
    review_only_allowed: bool
    market_or_projection_allowed: bool
    missing_value_policy: str
    source_status_requirement: str
    receipt_requirement: str

    def to_row(self) -> dict[str, object]:
        return {
            "module_name": self.module_name,
            "allowed_input_file": self.allowed_input_file,
            "allowed_lane": self.allowed_lane,
            "allowed_field_or_json_path": self.allowed_field_or_json_path,
            "field_purpose": self.field_purpose,
            "private_value_allowed": self.private_value_allowed,
            "review_only_allowed": self.review_only_allowed,
            "market_or_projection_allowed": self.market_or_projection_allowed,
            "missing_value_policy": self.missing_value_policy,
            "source_status_requirement": self.source_status_requirement,
            "receipt_requirement": self.receipt_requirement,
        }


@dataclass(frozen=True)
class FormulaBlockedFieldRule:
    module_name: str
    blocked_input_file: str
    blocked_lane: str
    blocked_field_or_json_path: str
    block_reason: str
    private_value_blocked: bool = True
    review_only_exception: str = ""

    def to_row(self) -> dict[str, object]:
        return {
            "module_name": self.module_name,
            "blocked_input_file": self.blocked_input_file,
            "blocked_lane": self.blocked_lane,
            "blocked_field_or_json_path": self.blocked_field_or_json_path,
            "block_reason": self.block_reason,
            "private_value_blocked": self.private_value_blocked,
            "review_only_exception": self.review_only_exception,
        }


@dataclass(frozen=True)
class FormulaGuardCheck:
    check_name: str
    status: str
    issue_count: int
    detail: str

    def to_row(self) -> dict[str, object]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "issue_count": self.issue_count,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class FormulaContractOutputs:
    allowed_registry: Path
    blocked_registry: Path
    guard_report: Path
    doc: Path


def build_formula_allowed_field_registry_rows() -> tuple[dict[str, object], ...]:
    rows: list[FormulaAllowedFieldRule] = []
    rows.extend(_replacement_vorp_rules())
    rows.extend(_current_value_rules())
    rows.extend(_lifecycle_rules())
    rows.extend(_confidence_rules())
    rows.extend(_first_down_rules())
    rows.extend(_return_rules())
    rows.extend(_prospect_prior_rules())
    rows.extend(_rookie_context_review_rules())
    return tuple(rule.to_row() for rule in rows)


def build_formula_blocked_field_registry_rows() -> tuple[dict[str, object], ...]:
    rows: list[FormulaBlockedFieldRule] = []
    for module in REQUIRED_MODULES:
        rows.extend(
            [
                FormulaBlockedFieldRule(
                    module,
                    "*",
                    "any_private_value_lane",
                    "market_context_fields_json.*",
                    "Market, ADP, rankings, projections, mock drafts, and big boards "
                    "cannot drive private football value.",
                    review_only_exception="rookie_context_review may display market context only",
                ),
                FormulaBlockedFieldRule(
                    module,
                    "*",
                    "any_private_value_lane",
                    "factual_evidence_json.*",
                    "Generic factual JSON slurping is forbidden; use explicit paths.",
                ),
                FormulaBlockedFieldRule(
                    module,
                    "*",
                    "any_private_value_lane",
                    "derived_evidence_json.*",
                    "Generic derived JSON slurping is forbidden; use explicit paths.",
                ),
                FormulaBlockedFieldRule(
                    module,
                    "*",
                    "any_private_value_lane",
                    "prospect_prior_evidence_json.*",
                    "Generic prospect-prior JSON slurping is forbidden; use explicit paths.",
                ),
                FormulaBlockedFieldRule(
                    module,
                    FULL_PROSPECT_MATRIX,
                    "any_private_value_lane",
                    "*",
                    "Current prospect formulas must use "
                    "admitted_prospect_current_feature_matrix.csv.",
                ),
                FormulaBlockedFieldRule(
                    module,
                    "*",
                    "context_fields_json",
                    "review_only_replacement_vorp",
                    "Review-only prior VORP context cannot be consumed as derived evidence.",
                ),
                FormulaBlockedFieldRule(
                    module,
                    "*",
                    "context_fields_json",
                    "combine_profile_source_limited",
                    "Third-party combine/pro-day data remains source-limited for private value.",
                ),
            ]
        )

    for module in (
        "replacement_vorp_core",
        "rb_current_value",
        "wr_current_value",
        "qb_current_value",
        "te_current_value",
        "first_down_scoring_evidence",
    ):
        rows.extend(
            [
                FormulaBlockedFieldRule(
                    module,
                    CANONICAL_RUSHING_FIRST_DOWNS,
                    "canonical_first_down_view",
                    "*",
                    "Formula-facing first-down evidence must use admitted matched-only views.",
                ),
                FormulaBlockedFieldRule(
                    module,
                    CANONICAL_RECEIVING_FIRST_DOWNS,
                    "canonical_first_down_view",
                    "*",
                    "Formula-facing first-down evidence must use admitted matched-only views.",
                ),
            ]
        )

    rows.append(
        FormulaBlockedFieldRule(
            "return_scoring_evidence",
            CANONICAL_RETURN_STATS,
            "canonical_return_view",
            "*",
            "Formula-facing return evidence must use admitted matched-only direct scoring view.",
        )
    )
    rows.extend(
        [
            FormulaBlockedFieldRule(
                "prospect_prior",
                ROOKIE_AGE_SOURCE,
                "rookie_age_intake_csv",
                "source_row|row_order|list_rank",
                (
                    "Rookie age sidecar may contribute only factual age fields; "
                    "source row order or list position cannot drive private value."
                ),
            ),
            FormulaBlockedFieldRule(
                "prospect_prior",
                DRAFT_CAPITAL_SOURCE,
                "rookie_draft_capital_csv",
                "adp|rank|ranking|projection|mock|big_board|consensus",
                (
                    "Draft-capital sidecar may contribute only factual NFL draft result "
                    "fields; market, ranking, mock, projection, or consensus fields remain "
                    "blocked."
                ),
            ),
        ]
    )
    return tuple(rule.to_row() for rule in rows)


def assert_formula_field_allowed(
    *,
    module_name: str,
    allowed_input_file: str,
    allowed_lane: str,
    allowed_field_or_json_path: str,
    private_value: bool = True,
    registry_rows: tuple[dict[str, object], ...] | None = None,
) -> None:
    """Fail closed unless a module requests an explicitly admitted field path."""
    normalized_path = _normalize_field_path(allowed_field_or_json_path)
    if private_value and _is_generic_json_path(normalized_path):
        raise ValueError(f"Generic JSON access is not formula-admitted: {normalized_path}")
    if private_value and _has_private_blocked_token(normalized_path):
        raise ValueError(f"Blocked private-value token in formula field: {normalized_path}")
    if private_value and allowed_lane == "market_context_fields_json":
        raise ValueError("Market context cannot drive private football value.")
    if private_value and allowed_input_file == FULL_PROSPECT_MATRIX:
        raise ValueError("Current prospect formulas must use admitted prospect matrix only.")

    rows = registry_rows or build_formula_allowed_field_registry_rows()
    for row in rows:
        if (
            row["module_name"] == module_name
            and row["allowed_input_file"] == allowed_input_file
            and row["allowed_lane"] == allowed_lane
            and row["allowed_field_or_json_path"] == allowed_field_or_json_path
        ):
            if private_value and not _bool(row["private_value_allowed"]):
                raise ValueError("Requested field is review/context only, not private value.")
            return
    raise ValueError(
        "Formula field is not explicitly admitted: "
        f"{module_name} {allowed_input_file} {allowed_lane} {allowed_field_or_json_path}"
    )


def run_formula_loader_guard_report(
    *,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    first_down_root: str | Path = DEFAULT_FIRST_DOWN_ROOT,
    return_root: str | Path = DEFAULT_RETURN_ROOT,
) -> tuple[dict[str, object], ...]:
    evidence = Path(evidence_root)
    first_downs = Path(first_down_root)
    returns = Path(return_root)
    allowed_rows = build_formula_allowed_field_registry_rows()
    blocked_rows = build_formula_blocked_field_registry_rows()

    checks = [
        _required_modules_check(allowed_rows),
        _required_input_files_check(evidence, first_downs, returns),
        _no_generic_private_json_paths_check(allowed_rows),
        _no_market_private_value_check(allowed_rows),
        _prospect_input_admitted_only_check(allowed_rows),
        _admitted_prospect_rows_check(evidence),
        _workout_zero_missingness_check(evidence),
        _source_limited_private_value_check(allowed_rows),
        _first_down_admitted_only_check(allowed_rows),
        _return_admitted_only_check(allowed_rows),
        _review_only_vorp_blocked_check(allowed_rows, blocked_rows),
        _blocked_registry_coverage_check(blocked_rows),
        _assertion_guard_examples_check(allowed_rows),
    ]
    return tuple(check.to_row() for check in checks)


def write_formula_contract_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
) -> FormulaContractOutputs:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    allowed_rows = build_formula_allowed_field_registry_rows()
    blocked_rows = build_formula_blocked_field_registry_rows()
    guard_rows = run_formula_loader_guard_report()

    allowed_path = output / "formula_allowed_field_registry.csv"
    blocked_path = output / "formula_blocked_field_registry.csv"
    guard_path = output / "formula_loader_guard_report.csv"
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)

    _write_csv(allowed_path, FORMULA_ALLOWED_FIELD_REGISTRY_HEADER, allowed_rows)
    _write_csv(blocked_path, FORMULA_BLOCKED_FIELD_REGISTRY_HEADER, blocked_rows)
    _write_csv(guard_path, FORMULA_LOADER_GUARD_REPORT_HEADER, guard_rows)
    _write_doc(doc, allowed_rows, blocked_rows, guard_rows)
    return FormulaContractOutputs(
        allowed_registry=allowed_path,
        blocked_registry=blocked_path,
        guard_report=guard_path,
        doc=doc,
    )


def _replacement_vorp_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    return (
        _allow(
            "replacement_vorp_core",
            NFL_MATRIX,
            "row_metadata",
            "position",
            "Position-specific replacement baseline bucket.",
        ),
        _allow(
            "replacement_vorp_core",
            NFL_MATRIX,
            "factual_evidence_json",
            "rotowire_player_stats",
            "Admitted NFL production rows for review-only replacement baseline.",
        ),
        _allow(
            "replacement_vorp_core",
            NFL_MATRIX,
            "derived_evidence_json",
            "stats_first_component_evidence",
            "Stats-first components, excluding review-only VORP context.",
        ),
        _allow(
            "replacement_vorp_core",
            ADMITTED_RUSHING_FIRST_DOWNS,
            "admitted_first_down_view",
            "rushing_first_downs",
            "Imported real rushing first downs from matched-only admitted view.",
            source_status="join_status=matched;source_status=imported_real_data",
        ),
        _allow(
            "replacement_vorp_core",
            ADMITTED_RECEIVING_FIRST_DOWNS,
            "admitted_first_down_view",
            "receiving_first_downs",
            "Imported real receiving first downs from matched-only admitted view.",
            source_status="join_status=matched;source_status=imported_real_data",
        ),
        _allow(
            "replacement_vorp_core",
            ADMITTED_RETURN_SCORING,
            "admitted_return_view",
            "return_yards_total|return_td_total",
            "Small direct return scoring evidence only.",
            source_status="join_status=matched;direct_scoring_only",
        ),
        _allow(
            "replacement_vorp_core",
            NFL_MATRIX,
            "source_status_json",
            "source_status_json",
            "Source labels needed for receipts and missingness checks.",
            private=False,
        ),
        _allow(
            "replacement_vorp_core",
            NFL_MATRIX,
            "receipt_pointers_json",
            "receipt_pointers_json",
            "Receipt pointers for every consumed feature group.",
            private=False,
        ),
    )


def _current_value_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    rows: list[FormulaAllowedFieldRule] = []
    for module in ("rb_current_value", "wr_current_value", "qb_current_value", "te_current_value"):
        rows.extend(
            [
                _allow(
                    module,
                    NFL_MATRIX,
                    "row_metadata",
                    "position",
                    "Position-specific module routing.",
                ),
                _allow(
                    module,
                    NFL_MATRIX,
                    "factual_evidence_json",
                    "rotowire_player_stats",
                    "Admitted NFL production evidence.",
                ),
                _allow(
                    module,
                    NFL_MATRIX,
                    "derived_evidence_json",
                    "rotowire_role_usage",
                    "Admitted snap, target, alignment, and route/TE-route usage evidence.",
                ),
                _allow(
                    module,
                    NFL_MATRIX,
                    "derived_evidence_json",
                    "stats_first_component_evidence",
                    "Stats-first evidence components built before formula scoring.",
                ),
                _allow(
                    module,
                    REPLACEMENT_VORP_PLAYER_ROWS,
                    "replacement_vorp_review",
                    (
                        "vorp_points|positive_vorp_points|review_scoring_points|"
                        "imported_rushing_first_downs|imported_receiving_first_downs|"
                        "imported_first_down_points|first_down_source_status|"
                        "return_source_status"
                    ),
                    "Review-only VORP anchor generated under Phase 11B.",
                    source_status="review_only_replacement_vorp_core",
                ),
                _allow(
                    module,
                    SOURCE_COVERAGE_MATRIX,
                    "source_coverage",
                    "feature_group|present|source_status|warnings",
                    "Coverage and missingness context; missing cannot be zero-filled.",
                    private=False,
                ),
                _allow(
                    module,
                    WARNING_MATRIX,
                    "warnings",
                    "warning_code|severity|warning_detail",
                    "Formula confidence and review warning inputs.",
                    private=False,
                ),
            ]
        )
    return tuple(rows)


def _lifecycle_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    return (
        _allow(
            "lifecycle_archetype",
            NFL_MATRIX,
            "row_metadata",
            "position|lifecycle_expected",
            "Current player lifecycle and position bucket.",
        ),
        _allow(
            "lifecycle_archetype",
            NFL_MATRIX,
            "factual_evidence_json",
            "rotowire_player_stats",
            "Historical production shape used for archetype/lifecycle labels.",
        ),
        _allow(
            "lifecycle_archetype",
            NFL_MATRIX,
            "derived_evidence_json",
            "rotowire_role_usage",
            "Usage shape for role stability and athletic-dependence labels.",
        ),
        _allow(
            "lifecycle_archetype",
            ROOKIE_AGE_SOURCE,
            "player_age_intake_csv",
            "age_years_decimal|age_total_months",
            "User-provided age sidecar used only for lifecycle age guardrails.",
            source_status="user_provided_age_source_formula_admitted_after_validation",
        ),
        _allow(
            "lifecycle_archetype",
            SLEEPER_PLAYER_AGE_SOURCE,
            "sleeper_player_age_csv",
            "age_years_decimal|age_total_months",
            "Sleeper birth-date-derived age fallback for current-player age guardrails.",
            source_status="sleeper_birth_date_age_derived_admitted_fact",
        ),
        _allow(
            "lifecycle_archetype",
            WARNING_MATRIX,
            "warnings",
            "warning_code|severity|warning_detail",
            "Lifecycle warnings and confidence caps.",
            private=False,
        ),
    )


def _confidence_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    rows: list[FormulaAllowedFieldRule] = []
    for matrix in (NFL_MATRIX, ADMITTED_PROSPECT_MATRIX, HISTORICAL_BACKTEST_MATRIX):
        rows.extend(
            [
                _allow(
                    "confidence_missingness",
                    matrix,
                    "source_status_json",
                    "source_status_json",
                    "Source status labels used for confidence, not player value.",
                    private=False,
                ),
                _allow(
                    "confidence_missingness",
                    matrix,
                    "receipt_pointers_json",
                    "receipt_pointers_json",
                    "Receipts required before formula evidence is trusted.",
                    private=False,
                ),
                _allow(
                    "confidence_missingness",
                    matrix,
                    "warning_flags",
                    "warning_flags",
                    "Warning flags cap confidence and trigger review labels.",
                    private=False,
                ),
            ]
        )
    rows.extend(
        [
            _allow(
                "confidence_missingness",
                SOURCE_COVERAGE_MATRIX,
                "source_coverage",
                "feature_group|present|source_status|warnings",
                "Coverage matrix for missingness and source status.",
                private=False,
            ),
            _allow(
                "confidence_missingness",
                WARNING_MATRIX,
                "warnings",
                "warning_code|severity|warning_detail",
                "Warning rows for confidence caps.",
                private=False,
            ),
        ]
    )
    return tuple(rows)


def _first_down_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    return (
        _allow(
            "first_down_scoring_evidence",
            ADMITTED_RUSHING_FIRST_DOWNS,
            "admitted_first_down_view",
            "rushing_first_downs",
            "Imported real rushing first downs; matched-only admitted view.",
            source_status="join_status=matched;source_status=imported_real_data",
        ),
        _allow(
            "first_down_scoring_evidence",
            ADMITTED_RECEIVING_FIRST_DOWNS,
            "admitted_first_down_view",
            "receiving_first_downs",
            "Imported real receiving first downs; matched-only admitted view.",
            source_status="join_status=matched;source_status=imported_real_data",
        ),
    )


def _return_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    return (
        _allow(
            "return_scoring_evidence",
            ADMITTED_RETURN_SCORING,
            "admitted_return_view",
            "return_yards_total|return_td_total",
            "Direct return scoring only; not talent or role signal.",
            source_status="join_status=matched;direct_scoring_only",
        ),
    )


def _prospect_prior_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    return (
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "row_metadata",
            "formula_identity_admitted|position|draft_year|college|nfl_team",
            "Identity-admitted prospect metadata and routing.",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "factual_evidence_json",
            "college_production_summary",
            "Admitted college production summary for prospect prior only.",
            source_status="prospect_prior_evidence;identity_admitted",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "factual_evidence_json",
            "college_season_latest",
            "Latest admitted college season evidence for prospect prior only.",
            source_status="prospect_prior_evidence;identity_admitted",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "factual_evidence_json",
            "college_targets_latest",
            "Latest admitted target evidence where present.",
            source_status="prospect_prior_evidence;identity_admitted",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "derived_evidence_json",
            "college_market_share",
            "College market-share evidence, not market/ADP context.",
            source_status="prospect_prior_evidence;identity_admitted",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "derived_evidence_json",
            "college_team_context",
            "College team pace/pass-run context.",
            source_status="prospect_prior_evidence;identity_admitted",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "prospect_prior_evidence_json",
            "recruiting_profile",
            "Recruiting profile as prospect prior only.",
            source_status="prospect_prior_evidence;identity_admitted",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "prospect_prior_evidence_json",
            "workout_profile",
            "RotoWire workout profile with repaired missingness; zeros are not missing.",
            source_status="licensed_user_export_formula_admitted_after_validation",
        ),
        _allow(
            "prospect_prior",
            ROOKIE_AGE_SOURCE,
            "rookie_age_intake_csv",
            "age_years_decimal|age_total_months",
            (
                "User-provided rookie age evidence for lifecycle context only; "
                "source row order is blocked."
            ),
            source_status="user_provided_age_source_formula_admitted_after_validation",
        ),
        _allow(
            "prospect_prior",
            DRAFT_CAPITAL_SOURCE,
            "rookie_draft_capital_csv",
            "round|overall_pick|draft_day",
            (
                "Factual 2026 NFL draft capital from locally frozen user download; "
                "not market, ADP, ranking, mock, or projection context."
            ),
            source_status="user_download_factual_draft_result_formula_admitted_after_validation",
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "source_status_json",
            "source_status_json",
            "Source labels for prospect-prior evidence.",
            private=False,
        ),
        _allow(
            "prospect_prior",
            ADMITTED_PROSPECT_MATRIX,
            "receipt_pointers_json",
            "receipt_pointers_json",
            "Receipts for prospect-prior feature groups.",
            private=False,
        ),
    )


def _rookie_context_review_rules() -> tuple[FormulaAllowedFieldRule, ...]:
    return (
        FormulaAllowedFieldRule(
            "rookie_context_review",
            ADMITTED_PROSPECT_MATRIX,
            "market_context_fields_json",
            "fantasypros_overall_adp|rookie_adp|rotowire_rookie_ranking|kaggle_consensus_big_board",
            "Review-only market/opinion context beside private value, never inside it.",
            private_value_allowed=False,
            review_only_allowed=True,
            market_or_projection_allowed=True,
            missing_value_policy="Missing market context remains missing; no neutral edge.",
            source_status_requirement="market_context_only",
            receipt_requirement="Market/context receipt pointer required if displayed.",
        ),
        _allow(
            "rookie_context_review",
            ADMITTED_PROSPECT_MATRIX,
            "context_fields_json",
            "nfl_depth_chart",
            "Landing spot/depth context as capped review context.",
            private=False,
        ),
    )


def _allow(
    module_name: str,
    allowed_input_file: str,
    allowed_lane: str,
    allowed_field_or_json_path: str,
    field_purpose: str,
    *,
    private: bool = True,
    review: bool = True,
    market: bool = False,
    missing: str = (
        "Missing/null evidence remains missing; formula modules must not convert it "
        "to zero, average, or positive evidence."
    ),
    source_status: str = "formula_admitted_after_validation",
    receipt: str = "Receipt pointer required for every consumed feature group.",
) -> FormulaAllowedFieldRule:
    return FormulaAllowedFieldRule(
        module_name=module_name,
        allowed_input_file=allowed_input_file,
        allowed_lane=allowed_lane,
        allowed_field_or_json_path=allowed_field_or_json_path,
        field_purpose=field_purpose,
        private_value_allowed=private,
        review_only_allowed=review,
        market_or_projection_allowed=market,
        missing_value_policy=missing,
        source_status_requirement=source_status,
        receipt_requirement=receipt,
    )


def _required_modules_check(rows: tuple[dict[str, object], ...]) -> FormulaGuardCheck:
    modules = {str(row["module_name"]) for row in rows}
    missing = sorted(set(REQUIRED_MODULES) - modules)
    return _check(
        "required_modules_present",
        missing,
        "All required Phase 11A modules have at least one admitted field.",
    )


def _required_input_files_check(
    evidence: Path,
    first_downs: Path,
    returns: Path,
) -> FormulaGuardCheck:
    required = (
        evidence / "nfl_player_current_evidence_matrix.csv",
        evidence / "admitted_prospect_current_feature_matrix.csv",
        evidence / "historical_rookie_backtest_feature_matrix.csv",
        evidence / "source_coverage_matrix.csv",
        evidence / "warning_matrix.csv",
        first_downs / "admitted_rushing_first_downs.csv",
        first_downs / "admitted_receiving_first_downs.csv",
        returns / "admitted_return_scoring_evidence.csv",
        Path(ROOKIE_AGE_SOURCE),
        Path(DRAFT_CAPITAL_SOURCE),
    )
    missing = [str(path) for path in required if not path.exists()]
    return _check(
        "required_input_files_exist",
        missing,
        "All formula contract input surfaces exist.",
    )


def _no_generic_private_json_paths_check(
    rows: tuple[dict[str, object], ...],
) -> FormulaGuardCheck:
    issues = [
        str(row["allowed_field_or_json_path"])
        for row in rows
        if _bool(row["private_value_allowed"])
        and _is_generic_json_path(str(row["allowed_field_or_json_path"]))
    ]
    return _check(
        "generic_private_json_slurping_blocked",
        issues,
        "Allowed private-value paths are explicit; no lane-wide JSON slurping.",
    )


def _no_market_private_value_check(rows: tuple[dict[str, object], ...]) -> FormulaGuardCheck:
    issues = []
    for row in rows:
        if not _bool(row["private_value_allowed"]):
            continue
        haystack = " ".join(
            str(row[key]).lower()
            for key in ("allowed_lane", "allowed_field_or_json_path", "allowed_input_file")
        )
        if any(token in haystack for token in PRIVATE_BLOCKED_TOKENS):
            issues.append(haystack)
    return _check(
        "market_projection_rank_private_value_blocked",
        issues,
        "No private-value allowed row contains market/projection/ranking tokens.",
    )


def _prospect_input_admitted_only_check(
    rows: tuple[dict[str, object], ...],
) -> FormulaGuardCheck:
    issues = [
        str(row)
        for row in rows
        if row["module_name"] == "prospect_prior"
        and _bool(row["private_value_allowed"])
        and row["allowed_input_file"] not in ADMITTED_PROSPECT_PRIOR_PRIVATE_INPUTS
    ]
    allowed = ", ".join(sorted(ADMITTED_PROSPECT_PRIOR_PRIVATE_INPUTS))
    return _check(
        "current_prospect_input_admitted_only",
        issues,
        (
            "Prospect prior private inputs are limited to the admitted prospect "
            "matrix plus explicitly admitted factual age and NFL draft-capital "
            f"sidecars: {allowed}."
        ),
    )


def _admitted_prospect_rows_check(evidence: Path) -> FormulaGuardCheck:
    path = evidence / "admitted_prospect_current_feature_matrix.csv"
    try:
        rows = load_formula_admitted_prospect_rows(path)
    except (FileNotFoundError, ValueError) as exc:
        return FormulaGuardCheck(
            "admitted_prospect_rows_require_formula_identity",
            "fail",
            1,
            str(exc),
        )
    return FormulaGuardCheck(
        "admitted_prospect_rows_require_formula_identity",
        "pass",
        0,
        f"{len(rows)} admitted prospect rows all have formula_identity_admitted == True.",
    )


def _workout_zero_missingness_check(evidence: Path) -> FormulaGuardCheck:
    rows = _read_rows(evidence / "admitted_prospect_current_feature_matrix.csv")
    issues: list[str] = []
    repaired_rows = 0
    for row in rows:
        prior = _json_object(row.get("prospect_prior_evidence_json"))
        workout = prior.get("workout_profile")
        if not isinstance(workout, dict):
            continue
        if workout.get("zero_placeholder_fields_repaired"):
            repaired_rows += 1
        for field in WORKOUT_ZERO_PLACEHOLDER_FIELDS:
            value = workout.get(field)
            if isinstance(value, int | float) and value == 0:
                issues.append(f"{row.get('prospect_name')}:{field}")
    detail = (
        "Repaired workout zero placeholders remain null/missing, not zero "
        f"({repaired_rows} admitted prospect rows carry repair metadata)."
    )
    return _check("workout_zero_placeholders_remain_missing", issues, detail)


def _source_limited_private_value_check(
    rows: tuple[dict[str, object], ...],
) -> FormulaGuardCheck:
    issues = [
        str(row)
        for row in rows
        if _bool(row["private_value_allowed"])
        and (
            "source_limited" in str(row["allowed_field_or_json_path"]).lower()
            or "source_limited" in str(row["source_status_requirement"]).lower()
        )
    ]
    return _check(
        "source_limited_not_private_value",
        issues,
        "Source-limited-not-admitted data is absent from private-value registry rows.",
    )


def _first_down_admitted_only_check(rows: tuple[dict[str, object], ...]) -> FormulaGuardCheck:
    relevant = [
        row for row in rows if row["module_name"] == "first_down_scoring_evidence"
    ]
    issues = [
        str(row)
        for row in relevant
        if "admitted_" not in str(row["allowed_input_file"])
        or row["allowed_lane"] != "admitted_first_down_view"
    ]
    return _check(
        "first_down_inputs_are_admitted_views_only",
        issues,
        "First-down formula evidence uses admitted matched-only views only.",
    )


def _return_admitted_only_check(rows: tuple[dict[str, object], ...]) -> FormulaGuardCheck:
    relevant = [
        row for row in rows if row["module_name"] == "return_scoring_evidence"
    ]
    issues = [
        str(row)
        for row in relevant
        if row["allowed_input_file"] != ADMITTED_RETURN_SCORING
        or row["allowed_lane"] != "admitted_return_view"
    ]
    return _check(
        "return_input_is_admitted_direct_scoring_only",
        issues,
        "Return formula evidence uses admitted matched-only direct scoring view only.",
    )


def _review_only_vorp_blocked_check(
    allowed_rows: tuple[dict[str, object], ...],
    blocked_rows: tuple[dict[str, object], ...],
) -> FormulaGuardCheck:
    allowed_issues = [
        str(row)
        for row in allowed_rows
        if "review_only_replacement_vorp" in str(row["allowed_field_or_json_path"])
        and _bool(row["private_value_allowed"])
    ]
    blocked = any(
        row["blocked_field_or_json_path"] == "review_only_replacement_vorp"
        for row in blocked_rows
    )
    issues = allowed_issues
    if not blocked:
        issues.append("blocked_registry_missing_review_only_replacement_vorp")
    return _check(
        "review_only_vorp_context_not_formula_admitted",
        issues,
        "Review-only VORP context is blocked from derived/private formula evidence.",
    )


def _blocked_registry_coverage_check(
    blocked_rows: tuple[dict[str, object], ...],
) -> FormulaGuardCheck:
    required_patterns = (
        "market_context_fields_json.*",
        "factual_evidence_json.*",
        "derived_evidence_json.*",
        "prospect_prior_evidence_json.*",
        "combine_profile_source_limited",
        "review_only_replacement_vorp",
        "source_row|row_order|list_rank",
        "adp|rank|ranking|projection|mock|big_board|consensus",
    )
    patterns = {str(row["blocked_field_or_json_path"]) for row in blocked_rows}
    missing = [pattern for pattern in required_patterns if pattern not in patterns]
    return _check(
        "blocked_registry_covers_known_hazards",
        missing,
        "Blocked registry includes market, generic JSON, source-limited, and review-only hazards.",
    )


def _assertion_guard_examples_check(
    rows: tuple[dict[str, object], ...],
) -> FormulaGuardCheck:
    issues = []
    try:
        assert_formula_field_allowed(
            module_name="rb_current_value",
            allowed_input_file=NFL_MATRIX,
            allowed_lane="factual_evidence_json",
            allowed_field_or_json_path="factual_evidence_json.*",
            registry_rows=rows,
        )
        issues.append("generic_json_path_allowed")
    except ValueError:
        pass
    try:
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=FULL_PROSPECT_MATRIX,
            allowed_lane="factual_evidence_json",
            allowed_field_or_json_path="college_production_summary",
            registry_rows=rows,
        )
        issues.append("full_prospect_matrix_allowed")
    except ValueError:
        pass
    try:
        assert_formula_field_allowed(
            module_name="rookie_context_review",
            allowed_input_file=ADMITTED_PROSPECT_MATRIX,
            allowed_lane="market_context_fields_json",
            allowed_field_or_json_path="rookie_adp",
            registry_rows=rows,
        )
        issues.append("market_context_private_value_allowed")
    except ValueError:
        pass
    try:
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=ROOKIE_AGE_SOURCE,
            allowed_lane="rookie_age_intake_csv",
            allowed_field_or_json_path="source_row",
            registry_rows=rows,
        )
        issues.append("rookie_age_unadmitted_field_allowed")
    except ValueError:
        pass
    try:
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=DRAFT_CAPITAL_SOURCE,
            allowed_lane="rookie_draft_capital_csv",
            allowed_field_or_json_path="mock_draft_rank",
            registry_rows=rows,
        )
        issues.append("draft_capital_market_like_field_allowed")
    except ValueError:
        pass
    return _check(
        "loader_assertions_fail_closed",
        issues,
        (
            "Programmatic guard rejects generic JSON, full prospect matrix, market "
            "private value, and non-admitted age/draft-capital fields."
        ),
    )


def _write_doc(
    path: Path,
    allowed_rows: tuple[dict[str, object], ...],
    blocked_rows: tuple[dict[str, object], ...],
    guard_rows: tuple[dict[str, object], ...],
) -> None:
    module_counts: dict[str, int] = {}
    for row in allowed_rows:
        module_counts[str(row["module_name"])] = module_counts.get(str(row["module_name"]), 0) + 1
    failed = [row for row in guard_rows if row["status"] != "pass"]
    lines = [
        "# Phase 11A Formula Contract And Allowed Field Registry",
        "",
        "## Purpose",
        "",
        (
            "Phase 11A creates the review-only formula contract for Model v4. It "
            "does not calculate player scores, promote app surfaces, change active "
            "rankings, alter My Team or War Board, or unlock readiness gates."
        ),
        "",
        "The contract's core rule is simple: formula modules may consume only the "
        "explicit input files, lanes, and JSON paths listed in the allowed-field "
        "registry. Generic JSON slurping is forbidden.",
        "",
        "## Outputs",
        "",
        "- `local_exports/model_v4/formula_contract/latest/formula_allowed_field_registry.csv`",
        "- `local_exports/model_v4/formula_contract/latest/formula_blocked_field_registry.csv`",
        "- `local_exports/model_v4/formula_contract/latest/formula_loader_guard_report.csv`",
        "",
        "## Required Module Coverage",
        "",
    ]
    for module in REQUIRED_MODULES:
        lines.append(f"- `{module}`: {module_counts.get(module, 0)} allowed field rows")
    lines.extend(
        [
            "",
            "## Hard Rules Locked",
            "",
            "- No private-value formula module may consume `market_context_fields_json`.",
            "- ADP, rankings, projections, mock drafts, big boards, and consensus ranks "
            "are context only.",
            "- Current prospect formula inputs must come from "
            "`admitted_prospect_current_feature_matrix.csv`, except for explicitly "
            "admitted factual rookie age and factual NFL draft-capital sidecars.",
            "- Review-only prospects are not formula-admitted.",
            "- Source-limited-not-admitted evidence cannot drive private football value.",
            "- Missing/null evidence cannot become zero, average, or positive evidence.",
            "- Return evidence is direct scoring only, not talent or role signal.",
            "- First-down evidence must use admitted matched-only first-down views.",
            "- Review-only VORP context cannot be consumed as derived evidence.",
            "",
            "## Guard Report",
            "",
            f"- Checks run: {len(guard_rows)}",
            f"- Failed checks: {len(failed)}",
            "",
            "| Check | Status | Issues | Detail |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for row in guard_rows:
        lines.append(
            "| "
            f"`{row['check_name']}` | {row['status']} | {row['issue_count']} | "
            f"{row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Formula Stage Boundary",
            "",
            "This phase is a contract and loader-guard phase only. The next phase may "
            "build review-only replacement/VORP outputs, but it must still use this "
            "registry and fail closed on any unregistered field request.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check(name: str, issues: list[str], pass_detail: str) -> FormulaGuardCheck:
    if issues:
        sample = "; ".join(issues[:5])
        extra = "" if len(issues) <= 5 else f"; ...and {len(issues) - 5} more"
        return FormulaGuardCheck(name, "fail", len(issues), sample + extra)
    return FormulaGuardCheck(name, "pass", 0, pass_detail)


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _json_object(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_field_path(path: str) -> str:
    return path.strip()


def _is_generic_json_path(path: str) -> bool:
    return path in GENERIC_JSON_PATHS or path.endswith(".*")


def _has_private_blocked_token(path: str) -> bool:
    lower = path.lower()
    return any(token in lower for token in PRIVATE_BLOCKED_TOKENS)


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
