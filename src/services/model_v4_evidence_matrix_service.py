from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_player_identity_crosswalk_service import normalize_identity_name
from src.services.model_v4_source_trust_contract_service import (
    CLASSIFICATION_CONTEXT_ONLY,
    CLASSIFICATION_DERIVED_EVIDENCE,
    CLASSIFICATION_MARKET_CONTEXT_ONLY,
    CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
    CLASSIFICATION_SCORING_EVIDENCE,
    CLASSIFICATION_SOURCE_LIMITED,
    build_source_trust_contract_rows,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/evidence_matrices/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_10R_PROSPECT_FORMULA_ADMISSION_HARDENING.md")

DEFAULT_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_SOURCE_TRUST = Path("docs/model_v4/PHASE_10F_SOURCE_TRUST_CONTRACT.csv")
DEFAULT_ROTOWIRE_INTAKE = Path("local_exports/model_v4/rotowire_intake/latest")
DEFAULT_FIRST_DOWNS = Path("local_exports/model_v4/first_downs/latest")
DEFAULT_RETURNS = Path("local_exports/model_v4/returns/latest")
DEFAULT_STATS_FIRST = Path("local_exports/model_v4/stats_first_expected_value/latest")
DEFAULT_VORP_REVIEW = Path("local_exports/model_v4/rotowire_vorp_review/latest")
DEFAULT_PROSPECT_ROOT = Path("local_exports/model_v4/prospect_sources/latest/files")

MATRIX_VERSION = "model_v4_phase_10m_current_prospect_identity_admission_0.1.0"
SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}
CFBD_FORMULA_ADMITTED_STATUS = "redistribution_limited_but_formula_admitted_after_validation"
CFB_PRODUCTION_FORMULA_ADMITTED_STATUS = (
    "licensed_user_export_formula_admitted_after_validation|"
    f"{CFBD_FORMULA_ADMITTED_STATUS}"
)

WORKOUT_ZERO_PLACEHOLDER_FIELDS = {
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
}

TEAM_KEY_ALIASES = {
    "bama": "alabama",
    "bc": "bostoncollege",
    "nmst": "newmexicostate",
    "psu": "pennstate",
    "vandy": "vanderbilt",
}

NFL_MATRIX_HEADER = (
    "canonical_player_key",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "lifecycle_expected",
    "roster_context",
    "identity_status",
    "factual_evidence_json",
    "derived_evidence_json",
    "prospect_prior_evidence_json",
    "context_fields_json",
    "market_context_fields_json",
    "source_status_json",
    "receipt_pointers_json",
    "warning_flags",
    "excluded_reason",
    "matrix_version",
)

PROSPECT_MATRIX_HEADER = (
    "canonical_prospect_key",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_year",
    "identity_status",
    "formula_identity_admitted",
    "factual_evidence_json",
    "derived_evidence_json",
    "prospect_prior_evidence_json",
    "context_fields_json",
    "market_context_fields_json",
    "source_status_json",
    "receipt_pointers_json",
    "warning_flags",
    "excluded_reason",
    "matrix_version",
)

BACKTEST_MATRIX_HEADER = (
    "historical_prospect_key",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_year",
    "draft_round",
    "draft_pick",
    "identity_status",
    "factual_evidence_json",
    "derived_evidence_json",
    "prospect_prior_evidence_json",
    "context_fields_json",
    "market_context_fields_json",
    "source_status_json",
    "receipt_pointers_json",
    "warning_flags",
    "excluded_reason",
    "matrix_version",
)

COVERAGE_HEADER = (
    "matrix_name",
    "entity_key",
    "entity_name",
    "entity_type",
    "position",
    "feature_group",
    "lane",
    "source_status",
    "present",
    "row_count",
    "latest_season",
    "source_files",
    "receipt_pointer",
    "warnings",
    "matrix_version",
)

WARNING_HEADER = (
    "matrix_name",
    "entity_key",
    "entity_name",
    "entity_type",
    "position",
    "feature_group",
    "severity",
    "warning_code",
    "warning_detail",
    "source_status",
    "next_action",
    "matrix_version",
)

SUMMARY_HEADER = ("metric", "value")

CURRENT_PROSPECT_IDENTITY_HEADER = (
    "canonical_prospect_key",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_year",
    "identity_status",
    "formula_identity_admitted",
    "warning_flags",
    "source_status_json",
    "receipt_pointers_json",
    "matrix_version",
)

CURRENT_PROSPECT_IDENTITY_REVIEW_HEADER = CURRENT_PROSPECT_IDENTITY_HEADER + (
    "review_reason",
)

CURRENT_PROSPECT_IDENTITY_ADMISSION_NOTES_HEADER = CURRENT_PROSPECT_IDENTITY_HEADER + (
    "admission_decision",
    "admission_method",
    "review_reason",
    "evidence_summary_json",
    "next_action",
)

OUTPUT_FILENAMES = {
    "nfl": "nfl_player_current_evidence_matrix.csv",
    "prospects": "prospect_current_feature_matrix.csv",
    "admitted_prospect_features": "admitted_prospect_current_feature_matrix.csv",
    "backtest": "historical_rookie_backtest_feature_matrix.csv",
    "coverage": "source_coverage_matrix.csv",
    "warnings": "warning_matrix.csv",
    "summary": "evidence_matrix_summary.csv",
    "admitted_prospects": "admitted_current_prospect_identity_spine.csv",
    "prospect_identity_review": "current_prospect_identity_review_report.csv",
    "prospect_identity_notes": "current_prospect_identity_admission_notes.csv",
}

MARKET_LEAKAGE_TOKENS = (
    "adp",
    '"rank"',
    "ranking",
    "rankings",
    "cheatsheet",
    "mock",
    "big_board",
    "market_context",
    "market_liquidity",
    "projection_points",
    "projected_points",
)


@dataclass(frozen=True)
class EvidenceMatrixResult:
    nfl_rows: tuple[dict[str, object], ...]
    prospect_rows: tuple[dict[str, object], ...]
    backtest_rows: tuple[dict[str, object], ...]
    coverage_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class MatrixPaths:
    nfl: Path
    prospects: Path
    admitted_prospect_features: Path
    backtest: Path
    coverage: Path
    warnings: Path
    summary: Path
    admitted_prospects: Path
    prospect_identity_review: Path
    prospect_identity_notes: Path
    doc: Path


def build_evidence_matrices(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
    rotowire_intake_root: str | Path = DEFAULT_ROTOWIRE_INTAKE,
    first_down_root: str | Path = DEFAULT_FIRST_DOWNS,
    returns_root: str | Path = DEFAULT_RETURNS,
    stats_first_root: str | Path = DEFAULT_STATS_FIRST,
    vorp_review_root: str | Path = DEFAULT_VORP_REVIEW,
    prospect_root: str | Path = DEFAULT_PROSPECT_ROOT,
) -> EvidenceMatrixResult:
    trust_counts = _trust_classification_counts()
    rotowire_root = Path(rotowire_intake_root)
    first_downs = Path(first_down_root)
    returns = Path(returns_root)
    stats_first = Path(stats_first_root)
    vorp_review = Path(vorp_review_root)
    prospects = Path(prospect_root)

    source = _SourceRows(
        truth_rows=_read_rows(Path(truth_set_path)),
        player_stats=_read_rows(rotowire_root / "rotowire_player_stats_clean_rows.csv"),
        role_usage=_read_rows(rotowire_root / "rotowire_role_usage_clean_rows.csv"),
        context=_read_rows(rotowire_root / "rotowire_context_clean_rows.csv"),
        evidence_coverage=_read_rows(rotowire_root / "rotowire_evidence_coverage.csv"),
        rushing_first_downs=_read_rows(first_downs / "canonical_rushing_first_downs.csv"),
        receiving_first_downs=_read_rows(first_downs / "canonical_receiving_first_downs.csv"),
        returns=_read_rows(returns / "canonical_return_stats.csv"),
        first_down_coverage=_read_rows(first_downs / "first_down_source_coverage.csv"),
        return_coverage=_read_rows(returns / "return_source_coverage.csv"),
        stats_first_rows=_read_rows(stats_first / "stats_first_expected_value_rows.csv"),
        stats_first_components=_read_rows(stats_first / "stats_first_component_evidence_rows.csv"),
        stats_first_unavailable=_read_rows(stats_first / "stats_first_unavailable_sections.csv"),
        stats_first_warnings=_read_rows(stats_first / "stats_first_source_warnings.csv"),
        vorp_rows=_read_rows(vorp_review / "rotowire_vorp_review_rows.csv"),
        college_summary=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "college_football_data"
            / "processed"
            / "college_player_category_summary.csv"
        ),
        college_seasons=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "college_football_data"
            / "processed"
            / "college_player_seasons_wide.csv"
        ),
        college_market_share=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "college_football_data"
            / "processed"
            / "college_market_share.csv"
        ),
        recruiting=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "college_football_data"
            / "processed"
            / "recruiting_players.csv"
        ),
        draft_results=_read_rows(
            prospects / "kaggle_nfl_draft" / "extracted" / "draft_results.csv"
        ),
        consensus_big_board=_read_rows(
            prospects / "kaggle_nfl_draft" / "extracted" / "consensus_big_board_latest_2026.csv"
        ),
        cfb_stats=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "rotowire"
            / "processed"
            / "rotowire_cfb_stats_all.csv"
        ),
        cfb_targets=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "rotowire"
            / "processed"
            / "rotowire_cfb_targets_all.csv"
        ),
        cfb_team_context=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "rotowire"
            / "processed"
            / "rotowire_cfb_advanced_team_stats_all.csv"
        ),
        workout=_read_rows(_preferred_workout_path(prospects)),
        depth_charts=_read_rows(_preferred_depth_chart_path(prospects)),
        rookie_rankings=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "rotowire"
            / "processed"
            / "rotowire_rookie_rankings_2026.csv"
        ),
        fantasypros_adp=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "fantasypros"
            / "processed"
            / "fantasypros_overall_adp_2026.csv"
        ),
        rookie_adp=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "market"
            / "processed"
            / "rookie_adp_2026_04_23_to_2026_05_17.csv"
        ),
        combine=_read_rows(
            prospects
            / "source_project"
            / "data"
            / "third_party"
            / "nfl_draft_data"
            / "processed"
            / "combine_skill_positions_all.csv"
        ),
    )

    nfl_rows, nfl_coverage, nfl_warnings = _build_nfl_player_matrix(source)
    prospect_rows, prospect_coverage, prospect_warnings = _build_current_prospect_matrix(source)
    backtest_rows, backtest_coverage, backtest_warnings = _build_backtest_matrix(source)

    coverage_rows = tuple(nfl_coverage + prospect_coverage + backtest_coverage)
    warning_rows = tuple(nfl_warnings + prospect_warnings + backtest_warnings)
    qa = _qa_summary(nfl_rows, prospect_rows, backtest_rows, coverage_rows, warning_rows)
    summary = {
        "matrix_version": MATRIX_VERSION,
        "nfl_player_rows": len(nfl_rows),
        "current_prospect_rows": len(prospect_rows),
        "admitted_current_prospect_identity_rows": sum(
            1 for row in prospect_rows if _identity_admitted(row.get("identity_status"))
        ),
        "admitted_prospect_feature_rows": sum(
            1 for row in prospect_rows if _bool_value(row.get("formula_identity_admitted"))
        ),
        "review_current_prospect_identity_rows": sum(
            1 for row in prospect_rows if not _identity_admitted(row.get("identity_status"))
        ),
        "current_prospect_identity_admission_notes_rows": len(prospect_rows),
        "historical_backtest_rows": len(backtest_rows),
        "source_coverage_rows": len(coverage_rows),
        "warning_rows": len(warning_rows),
        "source_trust_classification_counts": json.dumps(trust_counts, sort_keys=True),
        "formula_scores_calculated": False,
        "final_rankings_calculated": False,
        "market_leakage_violations": qa["market_leakage_violations"],
        "duplicate_entity_rows": qa["duplicate_entity_rows"],
        "fake_zero_missing_violations": qa["fake_zero_missing_violations"],
        "workout_zero_placeholder_violations": qa["workout_zero_placeholder_violations"],
        "ambiguous_join_rows": qa["ambiguous_join_rows"],
        "blocker_warnings": qa["blocker_warnings"],
        "historical_post_draft_college_evidence_violations": qa[
            "historical_post_draft_college_evidence_violations"
        ],
        "status": "ready_for_formula_design_review"
        if _qa_is_clean(qa)
        else "review_required_before_formula_design",
    }
    return EvidenceMatrixResult(
        nfl_rows=tuple(nfl_rows),
        prospect_rows=tuple(prospect_rows),
        backtest_rows=tuple(backtest_rows),
        coverage_rows=coverage_rows,
        warning_rows=warning_rows,
        summary=summary,
    )


def write_evidence_matrix_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: EvidenceMatrixResult | None = None,
) -> MatrixPaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_evidence_matrices()
    paths = MatrixPaths(
        nfl=output / OUTPUT_FILENAMES["nfl"],
        prospects=output / OUTPUT_FILENAMES["prospects"],
        admitted_prospect_features=output / OUTPUT_FILENAMES["admitted_prospect_features"],
        backtest=output / OUTPUT_FILENAMES["backtest"],
        coverage=output / OUTPUT_FILENAMES["coverage"],
        warnings=output / OUTPUT_FILENAMES["warnings"],
        summary=output / OUTPUT_FILENAMES["summary"],
        admitted_prospects=output / OUTPUT_FILENAMES["admitted_prospects"],
        prospect_identity_review=output / OUTPUT_FILENAMES["prospect_identity_review"],
        prospect_identity_notes=output / OUTPUT_FILENAMES["prospect_identity_notes"],
        doc=Path(doc_path),
    )
    _write_csv(paths.nfl, NFL_MATRIX_HEADER, result.nfl_rows)
    _write_csv(paths.prospects, PROSPECT_MATRIX_HEADER, result.prospect_rows)
    _write_csv(
        paths.admitted_prospect_features,
        PROSPECT_MATRIX_HEADER,
        _admitted_prospect_feature_rows(result.prospect_rows),
    )
    _write_csv(paths.backtest, BACKTEST_MATRIX_HEADER, result.backtest_rows)
    _write_csv(paths.coverage, COVERAGE_HEADER, result.coverage_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_csv(
        paths.admitted_prospects,
        CURRENT_PROSPECT_IDENTITY_HEADER,
        _current_prospect_identity_rows(result.prospect_rows, admitted=True),
    )
    _write_csv(
        paths.prospect_identity_review,
        CURRENT_PROSPECT_IDENTITY_REVIEW_HEADER,
        _current_prospect_identity_rows(result.prospect_rows, admitted=False),
    )
    _write_csv(
        paths.prospect_identity_notes,
        CURRENT_PROSPECT_IDENTITY_ADMISSION_NOTES_HEADER,
        _current_prospect_identity_admission_notes(result.prospect_rows),
    )
    _write_csv(
        paths.summary,
        SUMMARY_HEADER,
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    _write_doc(paths.doc, result, paths)
    return paths


def require_formula_admitted_prospect_rows(
    rows: Iterable[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    """Fail closed unless every row is explicitly admitted for formula use."""
    admitted_rows: list[dict[str, object]] = []
    for row in rows:
        if not _bool_value(row.get("formula_identity_admitted")):
            entity_key = row.get("canonical_prospect_key") or row.get("prospect_name") or "unknown"
            raise ValueError(f"Prospect row is not formula identity admitted: {entity_key}")
        admitted_rows.append(dict(row))
    return tuple(admitted_rows)


def load_formula_admitted_prospect_rows(
    path: str | Path = DEFAULT_OUTPUT_ROOT / OUTPUT_FILENAMES["admitted_prospect_features"],
) -> tuple[dict[str, object], ...]:
    return require_formula_admitted_prospect_rows(_read_rows(Path(path)))


@dataclass(frozen=True)
class _SourceRows:
    truth_rows: list[dict[str, str]]
    player_stats: list[dict[str, str]]
    role_usage: list[dict[str, str]]
    context: list[dict[str, str]]
    evidence_coverage: list[dict[str, str]]
    rushing_first_downs: list[dict[str, str]]
    receiving_first_downs: list[dict[str, str]]
    returns: list[dict[str, str]]
    first_down_coverage: list[dict[str, str]]
    return_coverage: list[dict[str, str]]
    stats_first_rows: list[dict[str, str]]
    stats_first_components: list[dict[str, str]]
    stats_first_unavailable: list[dict[str, str]]
    stats_first_warnings: list[dict[str, str]]
    vorp_rows: list[dict[str, str]]
    college_summary: list[dict[str, str]]
    college_seasons: list[dict[str, str]]
    college_market_share: list[dict[str, str]]
    recruiting: list[dict[str, str]]
    draft_results: list[dict[str, str]]
    consensus_big_board: list[dict[str, str]]
    cfb_stats: list[dict[str, str]]
    cfb_targets: list[dict[str, str]]
    cfb_team_context: list[dict[str, str]]
    workout: list[dict[str, str]]
    depth_charts: list[dict[str, str]]
    rookie_rankings: list[dict[str, str]]
    fantasypros_adp: list[dict[str, str]]
    rookie_adp: list[dict[str, str]]
    combine: list[dict[str, str]]


def _build_nfl_player_matrix(
    source: _SourceRows,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    player_stats_by_name = _rows_by_normalized_name(source.player_stats, "player_name")
    role_usage_by_name = _rows_by_normalized_name(source.role_usage, "player_name")
    context_by_name = _rows_by_normalized_name(source.context, "entity_name")
    coverage_by_name = _single_by_normalized_name(source.evidence_coverage, "player_name")
    rushing_fd_by_player = _rows_by_matched_player(source.rushing_first_downs)
    receiving_fd_by_player = _rows_by_matched_player(source.receiving_first_downs)
    returns_by_player = _rows_by_matched_player(source.returns)
    stats_first_components_by_player = _rows_by_key(
        source.stats_first_components, "matched_model_player"
    )
    unavailable_by_player = _rows_by_key(source.stats_first_unavailable, "matched_model_player")
    source_warnings_by_player = _rows_by_key(source.stats_first_warnings, "matched_model_player")
    vorp_by_player = _single_by_key(source.vorp_rows, "player_name")

    rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    for truth in source.truth_rows:
        name = truth["player_name"]
        normalized = normalize_identity_name(name)
        position = truth["position"]
        entity_key = f"nfl:{normalized}:{position}"
        if entity_key in seen_keys:
            warning_rows.append(
                _warning(
                    "nfl_player_current_evidence_matrix",
                    entity_key,
                    name,
                    "nfl_player",
                    position,
                    "identity",
                    "blocker",
                    "duplicate_current_player_key",
                    "Duplicate canonical NFL player key encountered.",
                    "duplicate",
                    "Resolve current-player identity before formulas.",
                )
            )
            continue
        seen_keys.add(entity_key)

        player_stats = player_stats_by_name.get(normalized, [])
        role_usage = role_usage_by_name.get(normalized, [])
        context = context_by_name.get(normalized, [])
        rushing_fd = rushing_fd_by_player.get(name, [])
        receiving_fd = receiving_fd_by_player.get(name, [])
        return_rows = returns_by_player.get(name, [])
        stats_components = stats_first_components_by_player.get(name, [])
        unavailable = unavailable_by_player.get(name, [])
        source_warnings = source_warnings_by_player.get(name, [])
        vorp = vorp_by_player.get(name)
        coverage = coverage_by_name.get(normalized)

        factual = {
            "rotowire_player_stats": _latest_metric_snapshots(
                player_stats, family_key="source_family", detail_key="source_detail"
            ),
            "manual_first_downs": _first_down_snapshot(rushing_fd, receiving_fd),
            "return_scoring": _return_snapshot(return_rows),
        }
        derived = {
            "rotowire_role_usage": _latest_metric_snapshots(
                role_usage, family_key="source_family", detail_key=""
            ),
            "stats_first_component_evidence": _stats_first_component_snapshot(stats_components),
        }
        context_fields = {
            "coverage": _clean_dict(coverage or {}),
            "non_market_context": _context_snapshot(context, include_market=False),
            "review_only_replacement_vorp": _vorp_snapshot(vorp),
        }
        market_context = {
            "market_and_projection_context": _context_snapshot(context, include_market=True),
        }
        source_status = {
            "factual_evidence": _group_status(
                player_stats + rushing_fd + receiving_fd + return_rows,
                default_status="missing",
            ),
            "derived_evidence": _group_status(role_usage + stats_components),
            "prospect_prior_evidence": "not_applicable",
            "context_market_fields": _group_status(context, default_status="missing"),
            "review_only_context_fields": _group_status([vorp] if vorp else []),
        }
        receipts = {
            "rotowire_player_stats": _receipt("rotowire_player_stats_clean_rows.csv"),
            "rotowire_role_usage": _receipt("rotowire_role_usage_clean_rows.csv"),
            "first_downs": _receipt("first_down_receipts.csv"),
            "returns": _receipt("return_scoring_receipts.csv"),
            "stats_first_components": _receipt("stats_first_component_evidence_rows.csv"),
            "vorp_review": _receipt("rotowire_vorp_review_rows.csv"),
        }
        warning_flags = sorted(
            set(
                _warnings_from_rows(
                    player_stats + role_usage + rushing_fd + receiving_fd + return_rows
                )
                + [row.get("reason", "") for row in unavailable if row.get("reason")]
                + [row.get("warning", "") for row in source_warnings if row.get("warning")]
            )
        )
        if not player_stats:
            warning_flags.append("missing_rotowire_player_stats")
        if not stats_components:
            warning_flags.append("missing_stats_first_component_evidence")
        if vorp:
            warning_flags.append("review_only_vorp_context_excluded_from_private_value")

        rows.append(
            {
                "canonical_player_key": entity_key,
                "player_name": name,
                "normalized_player_name": normalized,
                "position": position,
                "nfl_team": truth.get("nfl_team", ""),
                "lifecycle_expected": truth.get("lifecycle_expected", ""),
                "roster_context": truth.get("roster_context", ""),
                "identity_status": "truth_set_canonical",
                "factual_evidence_json": _json(factual),
                "derived_evidence_json": _json(derived),
                "prospect_prior_evidence_json": _json({}),
                "context_fields_json": _json(context_fields),
                "market_context_fields_json": _json(market_context),
                "source_status_json": _json(source_status),
                "receipt_pointers_json": _json(receipts),
                "warning_flags": "|".join(sorted(set(flag for flag in warning_flags if flag))),
                "excluded_reason": "",
                "matrix_version": MATRIX_VERSION,
            }
        )
        coverage_rows.extend(
            _coverage_for_entity(
                matrix_name="nfl_player_current_evidence_matrix",
                entity_key=entity_key,
                entity_name=name,
                entity_type="nfl_player",
                position=position,
                groups=(
                    _coverage_group(
                        "rotowire_player_stats",
                        CLASSIFICATION_SCORING_EVIDENCE,
                        player_stats,
                        _receipt("rotowire_player_stats_clean_rows.csv"),
                    ),
                    _coverage_group(
                        "manual_first_downs",
                        CLASSIFICATION_SCORING_EVIDENCE,
                        rushing_fd + receiving_fd,
                        _receipt("first_down_receipts.csv"),
                    ),
                    _coverage_group(
                        "return_scoring",
                        CLASSIFICATION_SCORING_EVIDENCE,
                        return_rows,
                        _receipt("return_scoring_receipts.csv"),
                    ),
                    _coverage_group(
                        "rotowire_role_usage",
                        CLASSIFICATION_DERIVED_EVIDENCE,
                        role_usage,
                        _receipt("rotowire_role_usage_clean_rows.csv"),
                    ),
                    _coverage_group(
                        "stats_first_component_evidence",
                        CLASSIFICATION_DERIVED_EVIDENCE,
                        stats_components,
                        _receipt("stats_first_component_evidence_rows.csv"),
                    ),
                    _coverage_group(
                        "context_market_fields",
                        CLASSIFICATION_CONTEXT_ONLY,
                        context,
                        _receipt("rotowire_context_clean_rows.csv"),
                    ),
                    _coverage_group(
                        "review_only_replacement_vorp",
                        CLASSIFICATION_CONTEXT_ONLY,
                        [vorp] if vorp else [],
                        _receipt("rotowire_vorp_review_rows.csv"),
                    ),
                ),
            )
        )
        warning_rows.extend(
            _warnings_for_entity(
                matrix_name="nfl_player_current_evidence_matrix",
                entity_key=entity_key,
                entity_name=name,
                entity_type="nfl_player",
                position=position,
                warning_flags=warning_flags,
            )
        )

    return rows, coverage_rows, warning_rows


def _build_current_prospect_matrix(
    source: _SourceRows,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    universe = _current_prospect_universe(source)
    college_summary = _rows_by_normalized_name(source.college_summary, "player")
    college_seasons = _rows_by_normalized_name(source.college_seasons, "player")
    college_market_share = _rows_by_normalized_name(source.college_market_share, "player")
    cfb_stats = _rows_by_normalized_name(source.cfb_stats, "player")
    cfb_targets = _rows_by_normalized_name(source.cfb_targets, "player")
    recruiting = _rows_by_normalized_name(source.recruiting, "name")
    workout = _rows_by_normalized_name(source.workout, "player")
    combine = _rows_by_normalized_name(source.combine, "player")
    depth = _rows_by_normalized_name(source.depth_charts, "player")
    rookie_rankings = _single_by_normalized_name(source.rookie_rankings, "player")
    fantasypros_adp = _single_by_normalized_name(source.fantasypros_adp, "player")
    rookie_adp = _single_by_normalized_name(source.rookie_adp, "player")
    big_board = _single_by_normalized_name(source.consensus_big_board, "player_name")
    team_context = _team_context_by_team(source.cfb_team_context)

    rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    for prospect in sorted(universe.values(), key=lambda row: (row["position"], row["name"])):
        name = prospect["name"]
        normalized = normalize_identity_name(name)
        position = prospect["position"]
        draft_year = prospect.get("draft_year", "2026") or "2026"
        entity_key = f"prospect:{draft_year}:{normalized}:{position}"
        if entity_key in seen_keys:
            continue
        seen_keys.add(entity_key)

        ranking_row = rookie_rankings.get(normalized)
        fp_adp_row = fantasypros_adp.get(normalized)
        rookie_adp_row = rookie_adp.get(normalized)
        board_row = big_board.get(normalized)
        reference_college = (
            board_row.get("college", "") if board_row else prospect.get("college", "")
        )
        raw_college_rows = college_summary.get(normalized, [])
        raw_college_season_rows = [
            row for row in college_seasons.get(normalized, []) if _int(row.get("season")) <= 2025
        ]
        raw_market_share_rows = [
            row
            for row in college_market_share.get(normalized, [])
            if _int(row.get("season")) <= 2025
        ]
        raw_cfb_stat_rows = [
            row
            for row in cfb_stats.get(normalized, [])
            if _int(row.get("season")) <= 2025
        ]
        raw_cfb_target_rows = [
            row for row in cfb_targets.get(normalized, []) if _int(row.get("season")) <= 2025
        ]
        if not reference_college:
            reference_college = _single_reference_college(
                raw_college_rows
                + raw_college_season_rows
                + raw_market_share_rows
                + raw_cfb_stat_rows
                + raw_cfb_target_rows
            )
        college_rows, college_admission_warnings = _admit_current_college_rows(
            raw_college_rows,
            reference_college=reference_college,
        )
        college_season_rows, college_season_warnings = _admit_current_college_rows(
            raw_college_season_rows,
            reference_college=reference_college,
        )
        market_share_rows, market_share_warnings = _admit_current_college_rows(
            raw_market_share_rows,
            reference_college=reference_college,
        )
        cfb_stat_rows, cfb_stat_warnings = _admit_current_college_rows(
            raw_cfb_stat_rows,
            reference_college=reference_college,
        )
        cfb_target_rows, cfb_target_warnings = _admit_current_college_rows(
            raw_cfb_target_rows,
            reference_college=reference_college,
        )
        recruiting_rows = recruiting.get(normalized, [])
        workout_rows = workout.get(normalized, [])
        combine_rows = combine.get(normalized, [])
        depth_rows = depth.get(normalized, [])
        latest_team = _latest_value(
            cfb_stat_rows + college_season_rows, "team"
        ) or reference_college or prospect.get("college", "")
        team_rows = team_context.get(_team_key(latest_team), [])
        identity_status, identity_warnings = _current_prospect_identity_status(
            position=position,
            reference_college=reference_college,
            admitted_evidence_rows=(
                college_rows
                + college_season_rows
                + market_share_rows
                + cfb_stat_rows
                + cfb_target_rows
            ),
            source_rows=(
                raw_college_rows
                + raw_college_season_rows
                + raw_market_share_rows
                + raw_cfb_stat_rows
                + raw_cfb_target_rows
                + workout_rows
                + combine_rows
                + depth_rows
            ),
            board_row=board_row,
            rookie_adp_row=rookie_adp_row,
            ranking_row=ranking_row,
        )

        factual = {
            "college_production_summary": _college_summary_snapshot(college_rows),
            "college_season_latest": _latest_stat_row(
                cfb_stat_rows or college_season_rows,
                max_season=2025,
            ),
            "college_targets_latest": _latest_stat_row(cfb_target_rows, max_season=2025),
        }
        derived = {
            "college_market_share": _market_share_snapshot(market_share_rows),
            "college_team_context": _latest_stat_row(team_rows, max_season=2025),
        }
        workout_profile = _workout_profile_snapshot(workout_rows)
        prospect_prior = {
            "recruiting_profile": _latest_stat_row(recruiting_rows),
            "workout_profile": workout_profile,
        }
        context_fields = {
            "nfl_depth_chart": _latest_stat_row(depth_rows),
            "combine_profile_source_limited": _latest_stat_row(combine_rows),
        }
        market_context = {
            "rotowire_rookie_ranking": _clean_dict(ranking_row or {}),
            "fantasypros_overall_adp": _clean_dict(fp_adp_row or {}),
            "rookie_adp": _clean_dict(rookie_adp_row or {}),
            "kaggle_consensus_big_board": _clean_dict(board_row or {}),
        }
        source_status = {
            "factual_evidence": _group_status(college_rows + cfb_stat_rows + cfb_target_rows),
            "derived_evidence": _group_status(market_share_rows + team_rows),
            "prospect_prior_evidence": _group_status(recruiting_rows + workout_rows + combine_rows),
            "context_fields": _group_status(depth_rows),
            "market_context_fields": "market_context_only"
            if any((ranking_row, fp_adp_row, rookie_adp_row, board_row))
            else "missing",
        }
        receipts = {
            "college_production": _receipt("college_player_category_summary.csv"),
            "college_market_share": _receipt("college_market_share.csv"),
            "rotowire_cfb_stats": _receipt("rotowire_cfb_stats_all.csv"),
            "rotowire_cfb_targets": _receipt("rotowire_cfb_targets_all.csv"),
            "workouts": _receipt("rotowire_workout_stats.csv"),
            "combine_source_limited": _receipt("combine_skill_positions_all.csv"),
            "market_context": _receipt("rookie_adp_2026_04_23_to_2026_05_17.csv"),
        }
        warning_flags = (
            college_admission_warnings
            + college_season_warnings
            + market_share_warnings
            + cfb_stat_warnings
            + cfb_target_warnings
            + identity_warnings
        )
        if not college_rows and not cfb_stat_rows:
            warning_flags.append("missing_college_production")
        if not market_share_rows:
            warning_flags.append("missing_college_market_share")
        if combine_rows:
            warning_flags.append("third_party_combine_source_limited")
        if any((ranking_row, fp_adp_row, rookie_adp_row, board_row)):
            warning_flags.append("market_context_excluded_from_private_value")
        if identity_status == "source_normalized_review_not_formula_admitted":
            warning_flags.append("source_normalized_review_not_formula_admitted")
        warning_flags.extend(_workout_warning_flags(workout_profile))
        is_formula_identity_admitted = _identity_admitted(identity_status)
        excluded_reason = _prospect_excluded_reason(
            identity_status=identity_status,
            warning_flags=warning_flags,
        )

        rows.append(
            {
                "canonical_prospect_key": entity_key,
                "prospect_name": name,
                "normalized_player_name": normalized,
                "position": position,
                "college": latest_team or prospect.get("college", ""),
                "nfl_team": prospect.get("nfl_team", ""),
                "draft_year": draft_year,
                "identity_status": identity_status,
                "formula_identity_admitted": is_formula_identity_admitted,
                "factual_evidence_json": _json(factual),
                "derived_evidence_json": _json(derived),
                "prospect_prior_evidence_json": _json(prospect_prior),
                "context_fields_json": _json(context_fields),
                "market_context_fields_json": _json(market_context),
                "source_status_json": _json(source_status),
                "receipt_pointers_json": _json(receipts),
                "warning_flags": "|".join(sorted(set(warning_flags))),
                "excluded_reason": excluded_reason,
                "matrix_version": MATRIX_VERSION,
            }
        )
        coverage_rows.extend(
            _coverage_for_entity(
                matrix_name="prospect_current_feature_matrix",
                entity_key=entity_key,
                entity_name=name,
                entity_type="current_prospect",
                position=position,
                groups=(
                    _coverage_group(
                        "college_production",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        college_rows + cfb_stat_rows + cfb_target_rows,
                        _receipt("college_player_category_summary.csv"),
                        source_status=CFB_PRODUCTION_FORMULA_ADMITTED_STATUS,
                    ),
                    _coverage_group(
                        "college_market_share",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        market_share_rows,
                        _receipt("college_market_share.csv"),
                        source_status=CFBD_FORMULA_ADMITTED_STATUS,
                    ),
                    _coverage_group(
                        "prospect_prior",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        recruiting_rows + workout_rows,
                        _receipt("rotowire_workout_stats.csv"),
                    ),
                    _coverage_group(
                        "source_limited_combine",
                        CLASSIFICATION_SOURCE_LIMITED,
                        combine_rows,
                        _receipt("combine_skill_positions_all.csv"),
                    ),
                    _coverage_group(
                        "depth_chart_context",
                        CLASSIFICATION_CONTEXT_ONLY,
                        depth_rows,
                        _receipt("rotowire_upcoming_depth_charts.csv"),
                    ),
                    _coverage_group(
                        "market_context",
                        CLASSIFICATION_MARKET_CONTEXT_ONLY,
                        [
                            row
                            for row in (ranking_row, fp_adp_row, rookie_adp_row, board_row)
                            if row
                        ],
                        _receipt("rookie_adp_2026_04_23_to_2026_05_17.csv"),
                    ),
                ),
            )
        )
        warning_rows.extend(
            _warnings_for_entity(
                matrix_name="prospect_current_feature_matrix",
                entity_key=entity_key,
                entity_name=name,
                entity_type="current_prospect",
                position=position,
                warning_flags=warning_flags,
            )
        )

    return rows, coverage_rows, warning_rows


def _build_backtest_matrix(
    source: _SourceRows,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    draft_rows = [
        row
        for row in source.draft_results
        if row.get("position") in SUPPORTED_POSITIONS
        and 2021 <= _int(row.get("draft_year")) <= 2025
    ]
    college_summary = _rows_by_normalized_name(source.college_summary, "player")
    college_seasons = _rows_by_normalized_name(source.college_seasons, "player")
    college_market_share = _rows_by_normalized_name(source.college_market_share, "player")
    cfb_stats = _rows_by_normalized_name(source.cfb_stats, "player")
    cfb_targets = _rows_by_normalized_name(source.cfb_targets, "player")
    recruiting = _rows_by_normalized_name(source.recruiting, "name")
    workout = _rows_by_normalized_name(source.workout, "player")
    combine = _rows_by_normalized_name(source.combine, "player")
    team_context = _team_context_by_team(source.cfb_team_context)

    rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    for draft in sorted(
        draft_rows,
        key=lambda row: (_int(row.get("draft_year")), _int(row.get("pick"))),
    ):
        name = draft["player_name"]
        normalized = normalize_identity_name(name)
        position = draft["position"]
        draft_year = _int(draft.get("draft_year"))
        max_feature_season = draft_year - 1
        entity_key = f"backtest:{draft_year}:{normalized}:{position}:{draft.get('pick', '')}"
        if entity_key in seen_keys:
            continue
        seen_keys.add(entity_key)

        draft_college = draft.get("college", "")
        raw_college_rows = college_summary.get(normalized, [])
        raw_college_season_rows = college_seasons.get(normalized, [])
        raw_market_share_rows = college_market_share.get(normalized, [])
        raw_cfb_stat_rows = cfb_stats.get(normalized, [])
        raw_cfb_target_rows = cfb_targets.get(normalized, [])
        college_rows, college_admission_warnings = _admit_historical_college_rows(
            raw_college_rows,
            draft_year=draft_year,
            draft_college=draft_college,
        )
        college_season_rows, college_season_warnings = _admit_historical_college_rows(
            raw_college_season_rows,
            draft_year=draft_year,
            draft_college=draft_college,
        )
        market_share_rows, market_share_warnings = _admit_historical_college_rows(
            raw_market_share_rows,
            draft_year=draft_year,
            draft_college=draft_college,
        )
        cfb_stat_rows, cfb_stat_warnings = _admit_historical_college_rows(
            raw_cfb_stat_rows,
            draft_year=draft_year,
            draft_college=draft_college,
        )
        cfb_target_rows, cfb_target_warnings = _admit_historical_college_rows(
            raw_cfb_target_rows,
            draft_year=draft_year,
            draft_college=draft_college,
        )
        recruiting_rows = [
            row for row in recruiting.get(normalized, []) if _int(row.get("year")) <= draft_year
        ]
        workout_rows = [
            row for row in workout.get(normalized, []) if _int(row.get("draft_year")) <= draft_year
        ]
        combine_rows = [
            row for row in combine.get(normalized, []) if _int(row.get("year")) <= draft_year
        ]
        latest_team = _latest_value(
            cfb_stat_rows + college_season_rows, "team"
        ) or draft.get("college", "")
        team_rows = [
            row
            for row in team_context.get(_team_key(latest_team), [])
            if _int(row.get("season")) <= max_feature_season
        ]

        factual = {
            "college_production_summary": _college_summary_snapshot(college_rows),
            "college_season_latest": _latest_stat_row(
                cfb_stat_rows or college_season_rows,
                max_season=max_feature_season,
            ),
            "college_targets_latest": _latest_stat_row(
                cfb_target_rows,
                max_season=max_feature_season,
            ),
        }
        derived = {
            "college_market_share": _market_share_snapshot(market_share_rows),
            "college_team_context": _latest_stat_row(team_rows, max_season=max_feature_season),
        }
        workout_profile = _workout_profile_snapshot(workout_rows)
        prospect_prior = {
            "draft_capital": {
                "draft_year": draft_year,
                "draft_round": _int(draft.get("round")),
                "draft_pick": _int(draft.get("pick")),
                "nfl_team": draft.get("team", ""),
            },
            "recruiting_profile": _latest_stat_row(recruiting_rows),
            "workout_profile": workout_profile,
        }
        context_fields = {
            "combine_profile_source_limited": _latest_stat_row(combine_rows),
        }
        source_status = {
            "factual_evidence": _group_status(college_rows + cfb_stat_rows + cfb_target_rows),
            "derived_evidence": _group_status(market_share_rows + team_rows),
            "prospect_prior_evidence": _group_status(
                [draft] + recruiting_rows + workout_rows + combine_rows
            ),
            "context_fields": "not_applicable",
            "market_context_fields": "not_included",
        }
        receipts = {
            "draft_results": _receipt("draft_results.csv"),
            "college_production": _receipt("college_player_category_summary.csv"),
            "college_market_share": _receipt("college_market_share.csv"),
            "rotowire_cfb_stats": _receipt("rotowire_cfb_stats_all.csv"),
            "rotowire_cfb_targets": _receipt("rotowire_cfb_targets_all.csv"),
            "workouts": _receipt("rotowire_workout_stats.csv"),
            "combine_source_limited": _receipt("combine_skill_positions_all.csv"),
        }
        warning_flags = (
            college_admission_warnings
            + college_season_warnings
            + market_share_warnings
            + cfb_stat_warnings
            + cfb_target_warnings
        )
        raw_college_evidence_count = (
            len(raw_college_rows)
            + len(raw_college_season_rows)
            + len(raw_market_share_rows)
            + len(raw_cfb_stat_rows)
            + len(raw_cfb_target_rows)
        )
        admitted_college_evidence_count = (
            len(college_rows)
            + len(college_season_rows)
            + len(market_share_rows)
            + len(cfb_stat_rows)
            + len(cfb_target_rows)
        )
        if raw_college_evidence_count and not admitted_college_evidence_count:
            warning_flags.append("same_name_collision_possible_college_evidence_quarantined")
        if not college_rows and not cfb_stat_rows:
            warning_flags.append("missing_pre_draft_college_production")
        if not market_share_rows:
            warning_flags.append("missing_pre_draft_market_share")
        if combine_rows:
            warning_flags.append("third_party_combine_source_limited")
        warning_flags.extend(_workout_warning_flags(workout_profile))

        rows.append(
            {
                "historical_prospect_key": entity_key,
                "prospect_name": name,
                "normalized_player_name": normalized,
                "position": position,
                "college": latest_team or draft.get("college", ""),
                "nfl_team": draft.get("team", ""),
                "draft_year": draft_year,
                "draft_round": _int(draft.get("round")),
                "draft_pick": _int(draft.get("pick")),
                "identity_status": "draft_result_canonical",
                "factual_evidence_json": _json(factual),
                "derived_evidence_json": _json(derived),
                "prospect_prior_evidence_json": _json(prospect_prior),
                "context_fields_json": _json(context_fields),
                "market_context_fields_json": _json({}),
                "source_status_json": _json(source_status),
                "receipt_pointers_json": _json(receipts),
                "warning_flags": "|".join(sorted(set(warning_flags))),
                "excluded_reason": "",
                "matrix_version": MATRIX_VERSION,
            }
        )
        coverage_rows.extend(
            _coverage_for_entity(
                matrix_name="historical_rookie_backtest_feature_matrix",
                entity_key=entity_key,
                entity_name=name,
                entity_type="historical_rookie",
                position=position,
                groups=(
                    _coverage_group(
                        "college_production",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        college_rows + cfb_stat_rows + cfb_target_rows,
                        _receipt("college_player_category_summary.csv"),
                        source_status=CFB_PRODUCTION_FORMULA_ADMITTED_STATUS,
                    ),
                    _coverage_group(
                        "college_market_share",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        market_share_rows,
                        _receipt("college_market_share.csv"),
                        source_status=CFBD_FORMULA_ADMITTED_STATUS,
                    ),
                    _coverage_group(
                        "draft_capital",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        [draft],
                        _receipt("draft_results.csv"),
                    ),
                    _coverage_group(
                        "prospect_prior",
                        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
                        recruiting_rows + workout_rows,
                        _receipt("rotowire_workout_stats.csv"),
                    ),
                    _coverage_group(
                        "source_limited_combine",
                        CLASSIFICATION_SOURCE_LIMITED,
                        combine_rows,
                        _receipt("combine_skill_positions_all.csv"),
                    ),
                ),
            )
        )
        warning_rows.extend(
            _warnings_for_entity(
                matrix_name="historical_rookie_backtest_feature_matrix",
                entity_key=entity_key,
                entity_name=name,
                entity_type="historical_rookie",
                position=position,
                warning_flags=warning_flags,
            )
        )

    return rows, coverage_rows, warning_rows


def _current_prospect_universe(source: _SourceRows) -> dict[tuple[str, str], dict[str, str]]:
    universe: dict[tuple[str, str], dict[str, str]] = {}

    def add(name: object, position: object, **extra: str) -> None:
        clean_name = str(name or "").strip()
        clean_position = str(position or "").strip().upper()
        if not clean_name or clean_position not in SUPPORTED_POSITIONS:
            return
        key = (normalize_identity_name(clean_name), clean_position)
        current = universe.get(key, {})
        universe[key] = {
            "name": current.get("name", clean_name),
            "position": clean_position,
            "draft_year": current.get("draft_year") or extra.get("draft_year", "2026"),
            "college": current.get("college") or extra.get("college", ""),
            "nfl_team": current.get("nfl_team") or extra.get("nfl_team", ""),
        }

    for row in source.rookie_adp:
        add(row.get("player"), row.get("position"), draft_year=row.get("draft_year") or "2026")
    for row in source.rookie_rankings:
        add(
            row.get("player"),
            row.get("position"),
            draft_year="2026",
            nfl_team=row.get("nfl_team", ""),
        )
    for row in source.consensus_big_board:
        if row.get("draft_year") == "2026":
            add(
                row.get("player_name"),
                row.get("position"),
                draft_year=row.get("draft_year", "2026"),
                college=row.get("college", ""),
            )
    for row in source.fantasypros_adp:
        normalized = normalize_identity_name(row.get("player"))
        position = str(row.get("position") or "").strip().upper()
        if (normalized, position) in universe:
            add(row.get("player"), position, draft_year="2026", nfl_team=row.get("team", ""))
    return universe


def _latest_metric_snapshots(
    rows: list[dict[str, str]],
    *,
    family_key: str,
    detail_key: str,
) -> dict[str, object]:
    snapshots: dict[str, object] = {}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        family = row.get(family_key, "unknown") or "unknown"
        detail = row.get(detail_key, "") if detail_key else ""
        group_key = f"{family}:{detail}" if detail else family
        grouped[group_key].append(row)
    for key, group_rows in grouped.items():
        latest = max(group_rows, key=lambda row: _int(row.get("season")))
        snapshots[key] = {
            "season": _int(latest.get("season")),
            "source_status": latest.get("source_status", ""),
            "source_file": latest.get("source_file", ""),
            "metrics": _private_metric_snapshot(_json_loads(latest.get("metrics_json"))),
        }
    return snapshots


def _private_metric_snapshot(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _private_metric_snapshot(item)
            for key, item in value.items()
            if key not in {"metric_rank", "rank", "pos_rank", "position_rank", "source_rank"}
        }
    if isinstance(value, list):
        return [_private_metric_snapshot(item) for item in value]
    return value


def _first_down_snapshot(
    rushing_rows: list[dict[str, str]],
    receiving_rows: list[dict[str, str]],
) -> dict[str, object]:
    rushing = _latest_row(rushing_rows)
    receiving = _latest_row(receiving_rows)
    return {
        "rushing": _select_fields(
            rushing,
            (
                "season",
                "rushing_attempts",
                "rushing_yards",
                "rushing_touchdowns",
                "rushing_first_downs",
                "rushing_first_down_rate",
                "source_status",
                "source_file",
            ),
        ),
        "receiving": _select_fields(
            receiving,
            (
                "season",
                "targets",
                "receptions",
                "receiving_yards",
                "receiving_touchdowns",
                "receiving_first_downs",
                "receiving_first_down_rate",
                "source_status",
                "source_file",
            ),
        ),
    }


def _return_snapshot(rows: list[dict[str, str]]) -> dict[str, object]:
    row = _latest_row(rows)
    return _select_fields(
        row,
        (
            "season",
            "kick_return_yards",
            "kick_return_touchdowns",
            "punt_return_yards",
            "punt_return_touchdowns",
            "return_yards_total",
            "return_td_total",
            "return_lve_points",
            "scoring_role",
            "source_status",
            "source_files",
        ),
    )


def _stats_first_component_snapshot(rows: list[dict[str, str]]) -> dict[str, object]:
    by_component: dict[str, dict[str, object]] = {}
    for component, group in _group_by(rows, "component").items():
        latest = max(group, key=lambda row: _int(row.get("season")))
        by_component[component] = {
            "latest_season": _int(latest.get("season")),
            "source_status": latest.get("source_status", ""),
            "raw_value": _float(latest.get("raw_value")),
            "weighted_raw_value": _float(latest.get("weighted_raw_value")),
            "normalized_score": _float(latest.get("normalized_score")),
            "source_fields": latest.get("source_fields", ""),
            "source_warning": latest.get("source_warning", ""),
        }
    return by_component


def _vorp_snapshot(row: dict[str, str] | None) -> dict[str, object]:
    if not row:
        return {}
    return _select_fields(
        row,
        (
            "weighted_lve_base_points",
            "current_lve_base_points",
            "estimated_rushing_first_downs",
            "estimated_receiving_first_downs",
            "first_down_adjusted_points",
            "first_down_source_status",
            "replacement_rank",
            "replacement_player",
            "production_vorp_points",
            "vorp_status",
            "warning",
            "allowed_use",
        ),
    )


def _context_snapshot(rows: list[dict[str, str]], *, include_market: bool) -> dict[str, object]:
    snapshots: dict[str, object] = {}
    for lane, group in _group_by(rows, "model_lane").items():
        is_market = lane in {"market_context", "projection_context"} or any(
            "projection" in row.get("source_family", "") for row in group
        )
        if is_market != include_market:
            continue
        latest = max(group, key=lambda row: _int(row.get("season")))
        snapshots[lane or "context"] = {
            "season": _int(latest.get("season")),
            "allowed_use": latest.get("allowed_use", ""),
            "source_status": latest.get("source_status", ""),
            "source_file": latest.get("source_file", ""),
            "metrics": _json_loads(latest.get("metrics_json")),
        }
    return snapshots


def _college_summary_snapshot(rows: list[dict[str, str]]) -> dict[str, object]:
    by_category: dict[str, object] = {}
    for row in rows:
        category = row.get("category", "unknown") or "unknown"
        by_category[category] = _select_fields(
            row,
            (
                "first_college_season",
                "final_college_season",
                "seasons_with_stats",
                "final_team",
                "final_conference",
                "best_yards_season",
                "career_yards",
                "career_tds",
                "career_attempts",
                "career_carries",
                "career_receptions",
                "final_yards",
                "final_tds",
                "best_yards",
                "max_receiving_yard_share",
                "max_receiving_td_share",
                "max_reception_share",
                "max_rushing_yard_share",
                "max_rushing_td_share",
                "max_rushing_attempt_share",
                "max_passing_yard_share",
                "max_passing_td_share",
                "max_passing_attempt_share",
            ),
        )
    return by_category


def _market_share_snapshot(rows: list[dict[str, str]]) -> dict[str, object]:
    if not rows:
        return {}
    by_category: dict[str, object] = {}
    for category, group in _group_by(rows, "category").items():
        latest = max(group, key=lambda row: _int(row.get("season")))
        by_category[category or "unknown"] = _select_fields(
            latest,
            (
                "season",
                "team",
                "conference",
                "passing_yard_share",
                "passing_td_share",
                "passing_attempt_share",
                "receiving_yard_share",
                "receiving_td_share",
                "reception_share",
                "rushing_yard_share",
                "rushing_td_share",
                "rushing_attempt_share",
            ),
        )
    return by_category


def _latest_stat_row(
    rows: list[dict[str, str]],
    *,
    max_season: int | None = None,
) -> dict[str, object]:
    if max_season is not None:
        rows = [row for row in rows if _int(row.get("season") or row.get("year")) <= max_season]
    if not rows:
        return {}
    row = max(rows, key=lambda item: (_int(item.get("season") or item.get("year")), len(item)))
    return _clean_dict(row)


def _workout_profile_snapshot(rows: list[dict[str, str]]) -> dict[str, object]:
    profile = _latest_stat_row(rows)
    if not profile:
        return {}
    repaired_fields = sorted(
        field
        for field in WORKOUT_ZERO_PLACEHOLDER_FIELDS
        if _is_zero_placeholder(profile.get(field))
    )
    if not repaired_fields:
        return profile
    profile = dict(profile)
    for field in repaired_fields:
        profile[field] = None
    profile["zero_placeholder_fields_repaired"] = repaired_fields
    profile["missing_after_zero_repair"] = repaired_fields
    return profile


def _workout_warning_flags(workout_profile: dict[str, object]) -> list[str]:
    if not workout_profile.get("zero_placeholder_fields_repaired"):
        return []
    return [
        "workout_metric_zero_placeholder_repaired",
        "workout_metric_missing_after_zero_repair",
    ]


def _is_zero_placeholder(value: object) -> bool:
    if value in {"", None}:
        return False
    try:
        return float(str(value).strip()) == 0.0
    except ValueError:
        return False


def _admit_historical_college_rows(
    rows: list[dict[str, str]],
    *,
    draft_year: int,
    draft_college: str,
) -> tuple[list[dict[str, str]], list[str]]:
    admitted: list[dict[str, str]] = []
    warnings: list[str] = []
    for row in rows:
        row_season = _college_row_season(row)
        if row_season and row_season >= draft_year:
            warnings.append("historical_college_evidence_after_draft_year_quarantined")
            continue
        row_team = _college_row_team(row)
        if draft_college and row_team and _team_key(row_team) != _team_key(draft_college):
            warnings.append("college_team_mismatch_needs_transfer_validation_quarantined")
            continue
        admitted.append(row)
    return admitted, sorted(set(warnings))


def _admit_current_college_rows(
    rows: list[dict[str, str]],
    *,
    reference_college: str,
) -> tuple[list[dict[str, str]], list[str]]:
    if not reference_college:
        warnings = (
            ["missing_reference_college_for_current_prospect_identity_review"]
            if rows
            else []
        )
        return rows, warnings
    admitted: list[dict[str, str]] = []
    warnings: list[str] = []
    for row in rows:
        row_team = _college_row_team(row)
        if row_team and _team_key(row_team) != _team_key(reference_college):
            warnings.append("current_college_team_mismatch_quarantined")
            continue
        admitted.append(row)
    return admitted, sorted(set(warnings))


def _single_reference_college(rows: list[dict[str, str]]) -> str:
    teams: dict[str, str] = {}
    for row in rows:
        team = _college_row_team(row)
        team_key = _team_key(team)
        if team and team_key:
            teams[team_key] = team
    if len(teams) == 1:
        return next(iter(teams.values()))
    return ""


def _current_prospect_identity_status(
    *,
    position: str,
    reference_college: str,
    admitted_evidence_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    board_row: dict[str, str] | None,
    rookie_adp_row: dict[str, str] | None,
    ranking_row: dict[str, str] | None,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    source_positions = {
        _position_from_row(row)
        for row in source_rows + [row for row in (board_row, rookie_adp_row, ranking_row) if row]
    }
    source_positions = {source_position for source_position in source_positions if source_position}
    conflicting_positions = sorted(
        source_position for source_position in source_positions if source_position != position
    )
    if conflicting_positions:
        warnings.append("current_prospect_position_conflict_review")

    evidence_ids = _stable_evidence_ids(admitted_evidence_rows)
    duplicate_id_namespaces = [
        namespace for namespace, values in evidence_ids.items() if len(values) > 1
    ]
    if duplicate_id_namespaces:
        warnings.append("current_prospect_multiple_source_ids_review")

    board_position = _position_from_row(board_row or {})
    board_college = board_row.get("college", "") if board_row else ""
    board_ok = bool(
        board_row
        and board_position == position
        and board_college
        and _team_key(board_college) == _team_key(reference_college)
    )
    sleeper_ok = bool(rookie_adp_row and rookie_adp_row.get("sleeper_id"))
    source_id_ok = bool(evidence_ids) and not duplicate_id_namespaces
    evidence_ok = bool(admitted_evidence_rows)

    if conflicting_positions:
        return "source_normalized_review_not_formula_admitted", warnings
    if board_ok and (evidence_ok or sleeper_ok or source_id_ok):
        return "admitted_exact_name_position_college_draft_year", warnings
    if reference_college and source_id_ok and evidence_ok:
        warnings.append("admitted_without_big_board_identity_receipt")
        return "admitted_single_source_id_position_college", warnings
    if sleeper_ok and reference_college and evidence_ok:
        warnings.append("admitted_with_sleeper_id_and_college_context")
        return "admitted_sleeper_id_position_college", warnings

    warnings.append("insufficient_current_prospect_identity_support")
    return "source_normalized_review_not_formula_admitted", warnings


def _position_from_row(row: dict[str, str]) -> str:
    position = str(row.get("position") or row.get("Pos") or "").strip().upper()
    return position if position in SUPPORTED_POSITIONS else ""


def _stable_evidence_ids(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    ids: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cfbd_id = str(row.get("cfbd_player_id", "")).strip()
        if cfbd_id:
            ids["cfbd_player_id"].add(cfbd_id)
        rotowire_id = str(row.get("rotowire_player_id", "")).strip()
        if rotowire_id:
            ids["rotowire_player_id"].add(rotowire_id)
        generic_id = str(row.get("player_id", "")).strip()
        if not generic_id:
            continue
        if str(row.get("source", "")).strip().lower() == "rotowire":
            ids["rotowire_player_id"].add(generic_id)
        else:
            ids["cfbd_player_id"].add(generic_id)
    return ids


def _college_row_season(row: dict[str, str]) -> int:
    season_values = (
        row.get("final_college_season"),
        row.get("season"),
        row.get("year"),
    )
    return max((_int(value) for value in season_values), default=0)


def _college_row_team(row: dict[str, str]) -> str:
    return (
        row.get("final_team")
        or row.get("team")
        or row.get("college")
        or row.get("school")
        or ""
    )


def _coverage_group(
    feature_group: str,
    lane: str,
    rows: list[dict[str, str]],
    receipt_pointer: str,
    *,
    source_status: str | None = None,
) -> dict[str, object]:
    return {
        "feature_group": feature_group,
        "lane": lane,
        "rows": rows,
        "receipt_pointer": receipt_pointer,
        "source_status": source_status,
    }


def _coverage_for_entity(
    *,
    matrix_name: str,
    entity_key: str,
    entity_name: str,
    entity_type: str,
    position: str,
    groups: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group in groups:
        source_rows = list(group["rows"])
        rows.append(
            {
                "matrix_name": matrix_name,
                "entity_key": entity_key,
                "entity_name": entity_name,
                "entity_type": entity_type,
                "position": position,
                "feature_group": group["feature_group"],
                "lane": group["lane"],
                "source_status": (
                    group.get("source_status") if source_rows else _group_status(source_rows)
                ),
                "present": bool(source_rows),
                "row_count": len(source_rows),
                "latest_season": _latest_season(source_rows),
                "source_files": "|".join(
                    sorted(set(_source_file(row) for row in source_rows if _source_file(row)))
                ),
                "receipt_pointer": group["receipt_pointer"],
                "warnings": "|".join(sorted(set(_warnings_from_rows(source_rows)))),
                "matrix_version": MATRIX_VERSION,
            }
        )
    return rows


def _warnings_for_entity(
    *,
    matrix_name: str,
    entity_key: str,
    entity_name: str,
    entity_type: str,
    position: str,
    warning_flags: list[str],
) -> list[dict[str, object]]:
    return [
        _warning(
            matrix_name,
            entity_key,
            entity_name,
            entity_type,
            position,
            "qa",
            _warning_severity(warning),
            warning,
            warning,
            _warning_source_status(warning),
            _warning_next_action(warning),
        )
        for warning in sorted(set(flag for flag in warning_flags if flag))
    ]


def _warning_severity(warning: str) -> str:
    if warning in {
        "historical_college_evidence_after_draft_year",
        "duplicate_current_player_key",
    }:
        return "blocker"
    return "review"


def _warning_source_status(warning: str) -> str:
    if "quarantined" in warning or warning.startswith("source_normalized_review"):
        return "review_only"
    if "market_context" in warning:
        return "context_only"
    if warning.startswith("workout_metric"):
        return "missingness_repaired"
    if "source_limited" in warning:
        return "source_limited"
    return "review"


def _warning_next_action(warning: str) -> str:
    if warning == "source_normalized_review_not_formula_admitted":
        return "Admit this prospect through a strict identity spine before formula scoring."
    if "quarantined" in warning or "same_name_collision" in warning:
        return "Validate source identity, college path, and season cutoff before admitting rows."
    if "rank_field" in warning:
        return "Keep rank-like table metadata out of factual and derived evidence."
    if warning.startswith("workout_metric"):
        return "Treat repaired workout placeholders as missing, not poor athletic performance."
    return "Inspect before formula scoring."


def _warning(
    matrix_name: str,
    entity_key: str,
    entity_name: str,
    entity_type: str,
    position: str,
    feature_group: str,
    severity: str,
    warning_code: str,
    warning_detail: str,
    source_status: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "matrix_name": matrix_name,
        "entity_key": entity_key,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "position": position,
        "feature_group": feature_group,
        "severity": severity,
        "warning_code": warning_code,
        "warning_detail": warning_detail,
        "source_status": source_status,
        "next_action": next_action,
        "matrix_version": MATRIX_VERSION,
    }


def _identity_admitted(identity_status: object) -> bool:
    return str(identity_status or "").startswith("admitted_")


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def _admitted_prospect_feature_rows(
    prospect_rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    return tuple(
        dict(row)
        for row in prospect_rows
        if _bool_value(row.get("formula_identity_admitted"))
    )


def _prospect_excluded_reason(*, identity_status: str, warning_flags: list[str]) -> str:
    if _identity_admitted(identity_status):
        return ""
    return _identity_review_reason_from_flags("|".join(sorted(set(warning_flags))))


def _current_prospect_identity_rows(
    prospect_rows: tuple[dict[str, object], ...],
    *,
    admitted: bool,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in prospect_rows:
        is_admitted = _identity_admitted(row.get("identity_status"))
        if is_admitted != admitted:
            continue
        identity_row = {
            "canonical_prospect_key": row.get("canonical_prospect_key", ""),
            "prospect_name": row.get("prospect_name", ""),
            "normalized_player_name": row.get("normalized_player_name", ""),
            "position": row.get("position", ""),
            "college": row.get("college", ""),
            "nfl_team": row.get("nfl_team", ""),
            "draft_year": row.get("draft_year", ""),
            "identity_status": row.get("identity_status", ""),
            "formula_identity_admitted": is_admitted,
            "warning_flags": row.get("warning_flags", ""),
            "source_status_json": row.get("source_status_json", ""),
            "receipt_pointers_json": row.get("receipt_pointers_json", ""),
            "matrix_version": MATRIX_VERSION,
        }
        if not admitted:
            identity_row["review_reason"] = _identity_review_reason(row)
        rows.append(identity_row)
    return rows


def _current_prospect_identity_admission_notes(
    prospect_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in prospect_rows:
        is_admitted = _identity_admitted(row.get("identity_status"))
        review_reason = "" if is_admitted else _identity_review_reason(row)
        warning_flags = str(row.get("warning_flags", ""))
        evidence_summary = {
            "source_status": _json_loads(str(row.get("source_status_json", ""))),
            "warnings": sorted(flag for flag in warning_flags.split("|") if flag),
        }
        rows.append(
            {
                "canonical_prospect_key": row.get("canonical_prospect_key", ""),
                "prospect_name": row.get("prospect_name", ""),
                "normalized_player_name": row.get("normalized_player_name", ""),
                "position": row.get("position", ""),
                "college": row.get("college", ""),
                "nfl_team": row.get("nfl_team", ""),
                "draft_year": row.get("draft_year", ""),
                "identity_status": row.get("identity_status", ""),
                "formula_identity_admitted": is_admitted,
                "warning_flags": warning_flags,
                "source_status_json": row.get("source_status_json", ""),
                "receipt_pointers_json": row.get("receipt_pointers_json", ""),
                "matrix_version": MATRIX_VERSION,
                "admission_decision": "admitted" if is_admitted else "review_only",
                "admission_method": row.get("identity_status", "") if is_admitted else "",
                "review_reason": review_reason,
                "evidence_summary_json": _json(evidence_summary),
                "next_action": _identity_next_action(review_reason),
            }
        )
    return rows


def _identity_review_reason(row: dict[str, object]) -> str:
    return _identity_review_reason_from_flags(str(row.get("warning_flags", "")))


def _identity_review_reason_from_flags(flags: str) -> str:
    if "current_prospect_position_conflict_review" in flags:
        return "position_conflict"
    if "insufficient_current_prospect_identity_support" in flags:
        return "insufficient_identity_support"
    if "missing_college_production" in flags:
        return "missing_college_evidence"
    return "not_admitted_for_formula_identity"


def _identity_next_action(review_reason: str) -> str:
    if not review_reason:
        return (
            "Admitted to the current prospect identity spine; formulas may consume "
            "only admitted evidence lanes."
        )
    if review_reason == "position_conflict":
        return "Keep review-only until position conflicts are resolved with source receipts."
    if review_reason == "insufficient_identity_support":
        return (
            "Keep review-only until exact name, position, college/team, draft-year, "
            "or stable-ID evidence is sufficient."
        )
    if review_reason == "missing_college_evidence":
        return (
            "Keep review-only until compatible college evidence exists or the player "
            "is explicitly allowed as no-data context."
        )
    return "Keep review-only before formula scoring."


def _qa_summary(
    nfl_rows: tuple[dict[str, object], ...] | list[dict[str, object]],
    prospect_rows: tuple[dict[str, object], ...] | list[dict[str, object]],
    backtest_rows: tuple[dict[str, object], ...] | list[dict[str, object]],
    coverage_rows: tuple[dict[str, object], ...] | list[dict[str, object]],
    warning_rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> dict[str, int]:
    matrix_key_pairs = (
        ("nfl", "canonical_player_key", nfl_rows),
        ("prospects", "canonical_prospect_key", prospect_rows),
        ("backtest", "historical_prospect_key", backtest_rows),
    )
    duplicate_rows = 0
    leakage = 0
    ambiguous = 0
    for _, key_field, rows in matrix_key_pairs:
        counts = Counter(str(row.get(key_field, "")) for row in rows)
        duplicate_rows += sum(1 for count in counts.values() if count > 1)
        for row in rows:
            if "ambiguous" in str(row.get("identity_status", "")).lower():
                ambiguous += 1
            leakage += len(_market_leakage_fields(row))
    fake_zero_missing = sum(
        1
        for row in coverage_rows
        if str(row.get("present")) == "False"
        and str(row.get("source_status")) not in {"missing", "not_applicable", "not_included"}
    )
    workout_zero_placeholders = _workout_zero_placeholder_violations(
        [*prospect_rows, *backtest_rows]
    )
    blocker_warnings = sum(1 for row in warning_rows if row.get("severity") == "blocker")
    historical_post_draft = _historical_post_draft_college_violations(backtest_rows)
    return {
        "duplicate_entity_rows": duplicate_rows,
        "market_leakage_violations": leakage,
        "fake_zero_missing_violations": fake_zero_missing,
        "workout_zero_placeholder_violations": workout_zero_placeholders,
        "ambiguous_join_rows": ambiguous,
        "blocker_warnings": blocker_warnings,
        "historical_post_draft_college_evidence_violations": historical_post_draft,
    }


def _qa_is_clean(qa: dict[str, int]) -> bool:
    return (
        qa["duplicate_entity_rows"] == 0
        and qa["market_leakage_violations"] == 0
        and qa["fake_zero_missing_violations"] == 0
        and qa["workout_zero_placeholder_violations"] == 0
        and qa["ambiguous_join_rows"] == 0
        and qa["blocker_warnings"] == 0
        and qa["historical_post_draft_college_evidence_violations"] == 0
    )


def _historical_post_draft_college_violations(
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> int:
    violations = 0
    for row in rows:
        draft_year = _int(row.get("draft_year"))
        if not draft_year:
            continue
        factual = _json_loads(row.get("factual_evidence_json"))
        derived = _json_loads(row.get("derived_evidence_json"))
        if not isinstance(factual, dict) or not isinstance(derived, dict):
            continue
        for payload in _dict_values(factual.get("college_production_summary")):
            if _int(payload.get("final_college_season")) >= draft_year:
                violations += 1
        for field_name in ("college_season_latest", "college_targets_latest"):
            payload = factual.get(field_name)
            payload_season = _int(payload.get("season") or payload.get("year")) if isinstance(
                payload, dict
            ) else 0
            if payload_season >= draft_year:
                violations += 1
        for payload in _dict_values(derived.get("college_market_share")):
            if _int(payload.get("season")) >= draft_year:
                violations += 1
        team_context = derived.get("college_team_context")
        if isinstance(team_context, dict) and _int(team_context.get("season")) >= draft_year:
            violations += 1
    return violations


def _workout_zero_placeholder_violations(
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> int:
    violations = 0
    for row in rows:
        prior = _json_loads(row.get("prospect_prior_evidence_json"))
        if not isinstance(prior, dict):
            continue
        workout_profile = prior.get("workout_profile")
        if not isinstance(workout_profile, dict):
            continue
        violations += sum(
            1
            for field in WORKOUT_ZERO_PLACEHOLDER_FIELDS
            if _is_zero_placeholder(workout_profile.get(field))
        )
    return violations


def _dict_values(value: object) -> list[dict[str, object]]:
    if not isinstance(value, dict):
        return []
    return [item for item in value.values() if isinstance(item, dict)]


def _market_leakage_fields(row: dict[str, object]) -> list[str]:
    violations: list[str] = []
    for field in (
        "factual_evidence_json",
        "derived_evidence_json",
        "prospect_prior_evidence_json",
    ):
        text = str(row.get(field, "")).lower()
        text = text.replace("market_share", "marketshare")
        text = text.replace('"ranking":', '"recruiting_rating_rank":')
        for token in MARKET_LEAKAGE_TOKENS:
            if token in text:
                violations.append(f"{field}:{token}")
    return violations


def _trust_classification_counts() -> dict[str, int]:
    rows = build_source_trust_contract_rows()
    return dict(sorted(Counter(str(row["classification"]) for row in rows).items()))


def _write_doc(path: Path, result: EvidenceMatrixResult, paths: MatrixPaths) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = result.summary
    review_reason_counts = Counter(
        _identity_review_reason(row)
        for row in result.prospect_rows
        if not _identity_admitted(row.get("identity_status"))
    )
    lines = [
        "# Phase 10R Prospect Formula Admission Hardening",
        "",
        "## Purpose",
        "",
        (
            "Phase 10R hardens current-prospect formula admission before formula "
            "design. It writes explicit formula identity admission flags onto the "
            "full prospect matrix, creates an admitted-only prospect feature matrix, "
            "and keeps unresolved prospects visible for review but unavailable to "
            "formula scoring."
        ),
        "",
        "## Outputs",
        "",
        f"- NFL current evidence matrix: `{paths.nfl}`",
        f"- Current prospect feature matrix: `{paths.prospects}`",
        f"- Admitted prospect feature matrix: `{paths.admitted_prospect_features}`",
        f"- Historical rookie backtest feature matrix: `{paths.backtest}`",
        f"- Source coverage matrix: `{paths.coverage}`",
        f"- Warning matrix: `{paths.warnings}`",
        f"- Admitted prospect identity spine: `{paths.admitted_prospects}`",
        f"- Prospect identity review report: `{paths.prospect_identity_review}`",
        f"- Prospect identity admission notes: `{paths.prospect_identity_notes}`",
        f"- Summary: `{paths.summary}`",
        "",
        "## Row Counts",
        "",
        f"- NFL current players: {summary['nfl_player_rows']}",
        f"- Current prospects: {summary['current_prospect_rows']}",
        (
            "- Admitted current prospect identities: "
            f"{summary['admitted_current_prospect_identity_rows']}"
        ),
        f"- Admitted prospect feature rows: {summary['admitted_prospect_feature_rows']}",
        (
            "- Review-only current prospect identities: "
            f"{summary['review_current_prospect_identity_rows']}"
        ),
        f"- Historical rookie backtest rows: {summary['historical_backtest_rows']}",
        f"- Source coverage rows: {summary['source_coverage_rows']}",
        f"- Warning rows: {summary['warning_rows']}",
        "",
        "## Admission Repair Notes",
        "",
        (
            "- Blank current-prospect college/team values are backfilled from later "
            "source records only when the exact normalized name and position key match."
        ),
        (
            "- `Nick Singleton` is explicitly aliased to `Nicholas Singleton` because "
            "Penn State RB evidence aligns across board, market, RotoWire, and CFBD sources."
        ),
        (
            "- Generic `player_id` values are namespaced by source family so CFBD and "
            "RotoWire IDs do not create false same-namespace conflicts."
        ),
        (
            "- Recruiting positions remain prospect-prior context but no longer veto "
            "current-position admission by themselves."
        ),
        "- Transfer/team mismatches remain quarantined unless source compatibility is clear.",
        "",
        "## Remaining Review-Only Reasons",
        "",
        *[
            f"- {reason}: {count}"
            for reason, count in sorted(review_reason_counts.items())
        ],
        "",
        "## QA",
        "",
        f"- Duplicate entity rows: {summary['duplicate_entity_rows']}",
        f"- Market leakage violations: {summary['market_leakage_violations']}",
        f"- Fake-zero missing violations: {summary['fake_zero_missing_violations']}",
        f"- Ambiguous join rows: {summary['ambiguous_join_rows']}",
        f"- Blocker warnings: {summary['blocker_warnings']}",
        (
            "- Historical post-draft college evidence violations: "
            f"{summary['historical_post_draft_college_evidence_violations']}"
        ),
        f"- Status: {summary['status']}",
        "",
        "## Formula Safety",
        "",
        "- Formula loaders must fail closed unless `formula_identity_admitted == True`.",
        "- Review-only prospects have populated `excluded_reason` values.",
        "- `admitted_prospect_current_feature_matrix.csv` contains only admitted rows.",
        (
            "- ADP, rankings, cheat sheets, mock drafts, and big boards are kept "
            "in `market_context_fields_json` only."
        ),
        "- Projection context is not included in factual, derived, or prospect-prior evidence.",
        "- Review-only replacement/VORP previews are kept in context fields only.",
        "- Missing data is represented by coverage rows and warnings, not zero-filled evidence.",
        "- Source-limited combine/pro-day rows are visible but flagged as source-limited.",
        "- No active rankings, My Team, War Board, or readiness gates were changed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, header: tuple[str, ...], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _preferred_depth_chart_path(prospects_root: Path) -> Path:
    may22_snapshot = Path(
        "local_exports/model_v4/depth_charts/latest/"
        "rotowire_upcoming_depth_charts_may22.csv"
    )
    if may22_snapshot.exists():
        return may22_snapshot
    return (
        prospects_root
        / "source_project"
        / "data"
        / "rotowire"
        / "processed"
        / "rotowire_upcoming_depth_charts.csv"
    )


def _preferred_workout_path(prospects_root: Path) -> Path:
    may25_snapshot = Path(
        "local_exports/model_v4/workouts/latest/rotowire_workout_stats_may25.csv"
    )
    if may25_snapshot.exists():
        return may25_snapshot
    return (
        prospects_root
        / "source_project"
        / "data"
        / "rotowire"
        / "processed"
        / "rotowire_workout_stats.csv"
    )


def _rows_by_normalized_name(
    rows: list[dict[str, str]],
    field: str,
) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        normalized = normalize_identity_name(row.get(field, ""))
        if normalized:
            grouped[normalized].append(row)
    return grouped


def _single_by_normalized_name(
    rows: list[dict[str, str]],
    field: str,
) -> dict[str, dict[str, str]]:
    grouped = _rows_by_normalized_name(rows, field)
    return {key: _latest_row(value) for key, value in grouped.items()}


def _rows_by_matched_player(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("join_status") and row.get("join_status") != "matched":
            continue
        player = row.get("matched_model_player") or row.get("player_name")
        if player:
            grouped[player].append(row)
    return grouped


def _rows_by_key(rows: list[dict[str, str]], field: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = row.get(field, "")
        if key:
            grouped[key].append(row)
    return grouped


def _single_by_key(rows: list[dict[str, str]], field: str) -> dict[str, dict[str, str]]:
    grouped = _rows_by_key(rows, field)
    return {key: _latest_row(value) for key, value in grouped.items()}


def _team_context_by_team(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = _team_key(row.get("team"))
        if key:
            grouped[key].append(row)
    return grouped


def _group_by(rows: list[dict[str, str]], field: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(field, "")].append(row)
    return grouped


def _latest_row(rows: list[dict[str, str]]) -> dict[str, str]:
    if not rows:
        return {}
    return max(rows, key=lambda row: (_int(row.get("season") or row.get("year")), len(row)))


def _latest_value(rows: list[dict[str, str]], field: str) -> str:
    row = _latest_row(rows)
    return row.get(field, "") if row else ""


def _latest_season(rows: list[dict[str, str]]) -> str:
    values = [
        _int(row.get("season") or row.get("year") or row.get("draft_year"))
        for row in rows
        if row.get("season") or row.get("year") or row.get("draft_year")
    ]
    values = [value for value in values if value]
    return str(max(values)) if values else ""


def _group_status(rows: list[dict[str, str]], *, default_status: str = "missing") -> str:
    if not rows:
        return default_status
    statuses = [
        row.get("source_status")
        or row.get("validation_status")
        or row.get("allowed_use")
        or "present"
        for row in rows
    ]
    statuses = sorted(set(str(status) for status in statuses if status))
    return "|".join(statuses) if statuses else "present"


def _warnings_from_rows(rows: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    for row in rows:
        for field in ("warning", "cleanup_warnings", "source_warning"):
            value = row.get(field, "")
            if value:
                warnings.extend(part for part in str(value).split("|") if part)
    return warnings


def _source_file(row: dict[str, str]) -> str:
    return row.get("source_file") or row.get("source_files") or ""


def _receipt(filename: str) -> str:
    return f"local_exports/model_v4/.../{filename}"


def _select_fields(row: dict[str, str], fields: tuple[str, ...]) -> dict[str, object]:
    if not row:
        return {}
    return {field: _typed_value(row.get(field, "")) for field in fields if row.get(field, "") != ""}


def _clean_dict(row: dict[str, str]) -> dict[str, object]:
    return {
        key: _typed_value(value)
        for key, value in row.items()
        if value not in {"", None}
        and key
        not in {"notes", "comment", "rank", "ranking", "pos_rank", "position_rank", "source_rank"}
    }


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json_loads(value: object) -> object:
    if not value:
        return {}
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return {}


def _typed_value(value: object) -> object:
    text = str(value or "").strip()
    if text == "":
        return ""
    numeric = text.replace(",", "")
    if _looks_like_number(numeric):
        if "." in numeric:
            return _float(numeric)
        return _int(numeric)
    return text


def _looks_like_number(value: str) -> bool:
    if not value:
        return False
    if value.startswith("-"):
        value = value[1:]
    return bool(value) and value.replace(".", "", 1).isdigit()


def _int(value: object) -> int:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def _float(value: object) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return round(float(text), 4)
    except ValueError:
        return 0.0


def _team_key(value: object) -> str:
    key = str(value or "").strip().lower().replace(" ", "").replace("-", "")
    return TEAM_KEY_ALIASES.get(key, key)
