from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_formula_contract_service import (
    ADMITTED_PROSPECT_MATRIX,
    HISTORICAL_BACKTEST_MATRIX,
    NFL_MATRIX,
    SOURCE_COVERAGE_MATRIX,
    WARNING_MATRIX,
    assert_formula_field_allowed,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_11F_CONFIDENCE_MISSINGNESS_LAYER.md")

CONFIDENCE_MISSINGNESS_VERSION = "model_v4_phase_11f_confidence_missingness_0.1.0"

CONFIDENCE_REVIEW_HEADER = (
    "entity_key",
    "entity_name",
    "entity_type",
    "position",
    "source_matrix",
    "confidence_cap",
    "confidence_status",
    "critical_missing_count",
    "review_warning_count",
    "source_limited_count",
    "identity_warning_count",
    "partial_join_count",
    "stale_season_warning_count",
    "missing_lifecycle_warning_count",
    "missing_receipt_count",
    "coverage_missing_groups",
    "cap_reasons",
    "warning_flags",
    "allowed_use",
    "confidence_version",
)

CONFIDENCE_RECEIPT_HEADER = (
    "entity_key",
    "entity_name",
    "entity_type",
    "feature_group",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_pointer",
    "source_status",
    "receipt_requirement",
    "confidence_version",
)

CONFIDENCE_WARNING_HEADER = (
    "entity_key",
    "entity_name",
    "entity_type",
    "position",
    "warning_type",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "confidence_version",
)

CRITICAL_MATRIX_FIELDS = (
    "source_status_json",
    "receipt_pointers_json",
    "warning_flags",
)


@dataclass(frozen=True)
class ConfidenceMissingnessResult:
    review_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class ConfidenceMissingnessPaths:
    review_rows: Path
    receipts: Path
    warnings: Path
    doc: Path


@dataclass(frozen=True)
class _EntitySpec:
    path: str
    source_matrix: str
    entity_type: str
    key_field: str
    name_field: str


class MissingConfidenceCriticalFieldError(ValueError):
    pass


def build_confidence_missingness_layer(
    *,
    nfl_matrix_path: str | Path = NFL_MATRIX,
    admitted_prospect_matrix_path: str | Path = ADMITTED_PROSPECT_MATRIX,
    historical_backtest_matrix_path: str | Path = HISTORICAL_BACKTEST_MATRIX,
    source_coverage_matrix_path: str | Path = SOURCE_COVERAGE_MATRIX,
    warning_matrix_path: str | Path = WARNING_MATRIX,
) -> ConfidenceMissingnessResult:
    _assert_phase_11f_contract()
    coverage_index = _coverage_index(Path(source_coverage_matrix_path))
    warning_index = _warning_index(Path(warning_matrix_path))
    specs = (
        _EntitySpec(
            str(nfl_matrix_path),
            "nfl_player_current_evidence_matrix",
            "nfl_player",
            "canonical_player_key",
            "player_name",
        ),
        _EntitySpec(
            str(admitted_prospect_matrix_path),
            "admitted_prospect_current_feature_matrix",
            "current_prospect",
            "canonical_prospect_key",
            "prospect_name",
        ),
        _EntitySpec(
            str(historical_backtest_matrix_path),
            "historical_rookie_backtest_feature_matrix",
            "historical_rookie",
            "historical_prospect_key",
            "prospect_name",
        ),
    )
    review_rows: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    for spec in specs:
        for row in _read_rows(Path(spec.path)):
            validate_confidence_critical_fields(row, source_matrix=spec.source_matrix)
            built = _confidence_row(
                row,
                spec,
                coverage_index.get(str(row.get(spec.key_field) or ""), ()),
                warning_index.get(str(row.get(spec.key_field) or ""), ()),
            )
            review_rows.append(built["review_row"])
            receipt_rows.extend(built["receipt_rows"])
            warning_rows.extend(built["warning_rows"])
    warning_rows.extend(_sanity_warnings())
    summary = {
        "confidence_version": CONFIDENCE_MISSINGNESS_VERSION,
        "review_status": "review_only",
        "review_rows": len(review_rows),
        "receipt_rows": len(receipt_rows),
        "warning_rows": len(warning_rows),
        "nfl_player_rows": sum(1 for row in review_rows if row["entity_type"] == "nfl_player"),
        "current_prospect_rows": sum(
            1 for row in review_rows if row["entity_type"] == "current_prospect"
        ),
        "historical_rookie_rows": sum(
            1 for row in review_rows if row["entity_type"] == "historical_rookie"
        ),
        "market_rows_used": 0,
        "projection_rows_used": 0,
        "generic_json_rows_used": 0,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return ConfidenceMissingnessResult(
        review_rows=tuple(review_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary=summary,
    )


def write_confidence_missingness_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: ConfidenceMissingnessResult | None = None,
) -> ConfidenceMissingnessPaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_confidence_missingness_layer()
    paths = ConfidenceMissingnessPaths(
        review_rows=output / "confidence_missingness_review_rows.csv",
        receipts=output / "confidence_missingness_receipts.csv",
        warnings=output / "confidence_missingness_warnings.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.review_rows, CONFIDENCE_REVIEW_HEADER, result.review_rows)
    _write_csv(paths.receipts, CONFIDENCE_RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, CONFIDENCE_WARNING_HEADER, result.warning_rows)
    _write_doc(paths.doc, result, paths)
    return paths


def validate_confidence_critical_fields(
    row: dict[str, object],
    *,
    source_matrix: str,
) -> None:
    missing = [field for field in CRITICAL_MATRIX_FIELDS if field not in row]
    if missing:
        raise MissingConfidenceCriticalFieldError(
            f"{source_matrix} missing confidence-critical fields: {', '.join(missing)}"
        )


def _assert_phase_11f_contract() -> None:
    for matrix in (NFL_MATRIX, ADMITTED_PROSPECT_MATRIX, HISTORICAL_BACKTEST_MATRIX):
        for lane, path in (
            ("source_status_json", "source_status_json"),
            ("receipt_pointers_json", "receipt_pointers_json"),
            ("warning_flags", "warning_flags"),
        ):
            assert_formula_field_allowed(
                module_name="confidence_missingness",
                allowed_input_file=matrix,
                allowed_lane=lane,
                allowed_field_or_json_path=path,
                private_value=False,
            )
    assert_formula_field_allowed(
        module_name="confidence_missingness",
        allowed_input_file=SOURCE_COVERAGE_MATRIX,
        allowed_lane="source_coverage",
        allowed_field_or_json_path="feature_group|present|source_status|warnings",
        private_value=False,
    )
    assert_formula_field_allowed(
        module_name="confidence_missingness",
        allowed_input_file=WARNING_MATRIX,
        allowed_lane="warnings",
        allowed_field_or_json_path="warning_code|severity|warning_detail",
        private_value=False,
    )


def _confidence_row(
    row: dict[str, str],
    spec: _EntitySpec,
    coverage_rows: tuple[dict[str, str], ...],
    warning_rows: tuple[dict[str, str], ...],
) -> dict[str, object]:
    entity_key = str(row.get(spec.key_field) or "")
    entity_name = str(row.get(spec.name_field) or "")
    position = str(row.get("position") or "")
    source_status = _json(row.get("source_status_json"))
    receipts = _json(row.get("receipt_pointers_json"))
    row_warning_flags = _split_flags(row.get("warning_flags"))
    matrix_warning_flags = tuple(str(warning.get("warning_code") or "") for warning in warning_rows)
    coverage_missing = tuple(
        str(coverage.get("feature_group") or "")
        for coverage in coverage_rows
        if str(coverage.get("present") or "").lower() != "true"
        and _is_confidence_critical_coverage(
            spec.entity_type,
            str(coverage.get("feature_group") or ""),
        )
    )
    coverage_warnings = tuple(
        str(coverage.get("warnings") or "")
        for coverage in coverage_rows
        if str(coverage.get("warnings") or "")
    )
    source_limited_count = _count_tokens(
        source_status,
        coverage_rows,
        row_warning_flags,
        matrix_warning_flags,
        tokens=("source_limited", "third_party_combine_source_limited"),
    )
    cap_relevant_flags = tuple(
        flag
        for flag in (*row_warning_flags, *matrix_warning_flags)
        if "current_college_team_mismatch_quarantined" not in str(flag)
    )
    identity_warning_count = _count_flag_tokens(
        cap_relevant_flags,
        (
            "identity",
            "source_normalized",
            "position_conflict",
            "multiple_source_ids",
            "team_mismatch",
            "college_team_mismatch",
        ),
    )
    partial_join_count = _count_flag_tokens(
        (*cap_relevant_flags, *coverage_warnings),
        ("partial", "join", "ambiguous", "mismatch", "quarantined"),
    )
    stale_season_warning_count = _count_flag_tokens(
        (*row_warning_flags, *matrix_warning_flags, *coverage_warnings),
        ("stale", "old_season", "season_gap"),
    )
    missing_lifecycle_warning_count = _count_flag_tokens(
        (*row_warning_flags, *matrix_warning_flags),
        ("lifecycle", "route_metrics_not_available", "missing_stats_first_component"),
    )
    missing_receipt_count = _missing_receipt_count(receipts)
    review_warning_count = len(
        tuple(flag for flag in (*row_warning_flags, *matrix_warning_flags) if flag)
    )
    reasons = _cap_reasons(
        spec.entity_type,
        coverage_missing,
        row_warning_flags,
        matrix_warning_flags,
        source_limited_count,
        identity_warning_count,
        partial_join_count,
        stale_season_warning_count,
        missing_lifecycle_warning_count,
        missing_receipt_count,
    )
    confidence_cap = _confidence_cap(reasons, review_warning_count)
    review_row = {
        "entity_key": entity_key,
        "entity_name": entity_name,
        "entity_type": spec.entity_type,
        "position": position,
        "source_matrix": spec.source_matrix,
        "confidence_cap": confidence_cap,
        "confidence_status": _confidence_status(confidence_cap),
        "critical_missing_count": len(coverage_missing),
        "review_warning_count": review_warning_count,
        "source_limited_count": source_limited_count,
        "identity_warning_count": identity_warning_count,
        "partial_join_count": partial_join_count,
        "stale_season_warning_count": stale_season_warning_count,
        "missing_lifecycle_warning_count": missing_lifecycle_warning_count,
        "missing_receipt_count": missing_receipt_count,
        "coverage_missing_groups": "|".join(dict.fromkeys(coverage_missing)),
        "cap_reasons": "|".join(reasons),
        "warning_flags": "|".join(dict.fromkeys((*row_warning_flags, *matrix_warning_flags))),
        "allowed_use": "review_only_confidence_cap",
        "confidence_version": CONFIDENCE_MISSINGNESS_VERSION,
    }
    return {
        "review_row": review_row,
        "receipt_rows": _receipt_rows(entity_key, entity_name, spec.entity_type, spec.path),
        "warning_rows": _warning_rows(
            entity_key,
            entity_name,
            spec.entity_type,
            position,
            reasons,
        ),
    }


def _is_confidence_critical_coverage(entity_type: str, feature_group: str) -> bool:
    critical_by_type = {
        "nfl_player": {
            "manual_first_downs",
            "rotowire_role_usage",
            "rotowire_player_stats",
            "stats_first_component_evidence",
        },
        "current_prospect": {
            "college_production",
            "college_market_share",
            "prospect_prior",
            "source_limited_combine",
        },
        "historical_rookie": {
            "college_production",
            "college_market_share",
            "prospect_prior",
            "source_limited_combine",
        },
    }
    return feature_group in critical_by_type.get(entity_type, set())


def _cap_reasons(
    entity_type: str,
    coverage_missing: tuple[str, ...],
    row_warning_flags: tuple[str, ...],
    matrix_warning_flags: tuple[str, ...],
    source_limited_count: int,
    identity_warning_count: int,
    partial_join_count: int,
    stale_season_warning_count: int,
    missing_lifecycle_warning_count: int,
    missing_receipt_count: int,
) -> tuple[str, ...]:
    reasons: list[str] = []
    missing = set(coverage_missing)
    flags = "|".join((*row_warning_flags, *matrix_warning_flags)).lower()
    if "manual_first_downs" in missing or "first_down" in flags:
        reasons.append("missing_or_review_first_down_evidence")
    if "rotowire_role_usage" in missing or any(
        token in flags for token in ("route", "target", "snap")
    ):
        reasons.append("missing_or_review_route_target_snap_evidence")
    if {"college_production", "college_market_share", "prospect_prior"} & missing:
        reasons.append("missing_prospect_or_college_evidence")
    if source_limited_count:
        reasons.append("source_limited_evidence_cap")
    if identity_warning_count:
        reasons.append("identity_review_cap")
    if partial_join_count:
        reasons.append("partial_or_quarantined_join_cap")
    if stale_season_warning_count:
        reasons.append("stale_season_warning_cap")
    if missing_lifecycle_warning_count:
        reasons.append("missing_lifecycle_or_role_shape_evidence")
    if missing_receipt_count:
        reasons.append("missing_receipt_pointer_cap")
    if (
        entity_type in {"current_prospect", "historical_rookie"}
        and "source_limited_combine" in missing
    ):
        reasons.append("combine_absent_not_zero_filled")
    return tuple(dict.fromkeys(reasons))


def _confidence_cap(reasons: tuple[str, ...], review_warning_count: int) -> float:
    cap = 1.0
    caps = {
        "missing_or_review_first_down_evidence": 0.9,
        "missing_or_review_route_target_snap_evidence": 0.88,
        "missing_prospect_or_college_evidence": 0.84,
        "source_limited_evidence_cap": 0.92,
        "identity_review_cap": 0.8,
        "partial_or_quarantined_join_cap": 0.86,
        "stale_season_warning_cap": 0.9,
        "missing_lifecycle_or_role_shape_evidence": 0.9,
        "missing_receipt_pointer_cap": 0.78,
        "combine_absent_not_zero_filled": 0.94,
    }
    for reason in reasons:
        cap = min(cap, caps.get(reason, cap))
    if review_warning_count >= 5:
        cap = min(cap, 0.82)
    elif review_warning_count >= 3:
        cap = min(cap, 0.88)
    return round(cap, 4)


def _confidence_status(confidence_cap: float) -> str:
    if confidence_cap >= 0.95:
        return "high_confidence_metadata"
    if confidence_cap >= 0.85:
        return "usable_with_confidence_cap"
    if confidence_cap >= 0.75:
        return "capped_review_required"
    return "fail_closed_review_required"


def _receipt_rows(
    entity_key: str,
    entity_name: str,
    entity_type: str,
    matrix_path: str,
) -> tuple[dict[str, object], ...]:
    rows = [
        _receipt(
            entity_key,
            entity_name,
            entity_type,
            "source_status_json",
            matrix_path,
            "source_status_json",
            "source_status_json",
        ),
        _receipt(
            entity_key,
            entity_name,
            entity_type,
            "receipt_pointers_json",
            matrix_path,
            "receipt_pointers_json",
            "receipt_pointers_json",
        ),
        _receipt(
            entity_key,
            entity_name,
            entity_type,
            "warning_flags",
            matrix_path,
            "warning_flags",
            "warning_flags",
        ),
        _receipt(
            entity_key,
            entity_name,
            entity_type,
            "source_coverage",
            SOURCE_COVERAGE_MATRIX,
            "source_coverage",
            "feature_group|present|source_status|warnings",
        ),
        _receipt(
            entity_key,
            entity_name,
            entity_type,
            "warning_matrix",
            WARNING_MATRIX,
            "warnings",
            "warning_code|severity|warning_detail",
        ),
    ]
    return tuple(rows)


def _receipt(
    entity_key: str,
    entity_name: str,
    entity_type: str,
    feature_group: str,
    allowed_input_file: str,
    allowed_lane: str,
    allowed_field_or_json_path: str,
) -> dict[str, object]:
    return {
        "entity_key": entity_key,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "feature_group": feature_group,
        "allowed_input_file": allowed_input_file,
        "allowed_lane": allowed_lane,
        "allowed_field_or_json_path": allowed_field_or_json_path,
        "receipt_pointer": allowed_input_file,
        "source_status": "confidence_metadata_only_not_player_value",
        "receipt_requirement": (
            "Confidence-critical metadata must be present; fail closed if absent."
        ),
        "confidence_version": CONFIDENCE_MISSINGNESS_VERSION,
    }


def _warning_rows(
    entity_key: str,
    entity_name: str,
    entity_type: str,
    position: str,
    reasons: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "entity_key": entity_key,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "position": position,
            "warning_type": "confidence_cap",
            "severity": "review",
            "warning_code": reason,
            "warning_detail": reason.replace("_", " "),
            "next_action": (
                "Apply cap only; missing evidence cannot become zero or positive evidence."
            ),
            "confidence_version": CONFIDENCE_MISSINGNESS_VERSION,
        }
        for reason in reasons
    )


def _sanity_warnings() -> tuple[dict[str, object], ...]:
    codes = {
        "confidence_missingness_fail_closed_sanity": (
            "Confidence-critical metadata fields are required before formulas may load rows."
        ),
        "missing_data_not_zero_or_average_sanity": (
            "Missing evidence creates caps and warnings, not zero, average, or positive evidence."
        ),
        "stale_season_direct_check_unavailable": (
            "Phase 11A confidence fields do not expose latest_season; stale evidence "
            "is warning-driven."
        ),
        "lifecycle_output_not_allowed_for_confidence_missingness": (
            "Phase 11E outputs are not Phase 11A confidence inputs; lifecycle gaps "
            "are warning-driven."
        ),
    }
    return tuple(
        {
            "entity_key": "phase_11f_sanity",
            "entity_name": "",
            "entity_type": "all",
            "position": "QB|RB|WR|TE",
            "warning_type": "sanity_fixture",
            "severity": "review",
            "warning_code": code,
            "warning_detail": detail,
            "next_action": "Use as a formula-loader guardrail before app promotion planning.",
            "confidence_version": CONFIDENCE_MISSINGNESS_VERSION,
        }
        for code, detail in codes.items()
    )


def _coverage_index(path: Path) -> dict[str, tuple[dict[str, str], ...]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in _read_rows(path):
        output.setdefault(str(row.get("entity_key") or ""), []).append(row)
    return {key: tuple(rows) for key, rows in output.items()}


def _warning_index(path: Path) -> dict[str, tuple[dict[str, str], ...]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in _read_rows(path):
        output.setdefault(str(row.get("entity_key") or ""), []).append(row)
    return {key: tuple(rows) for key, rows in output.items()}


def _missing_receipt_count(receipts: dict[str, Any]) -> int:
    if not receipts:
        return 1
    return sum(1 for value in receipts.values() if value in (None, "", {}, []))


def _count_tokens(
    source_status: dict[str, Any],
    coverage_rows: tuple[dict[str, str], ...],
    row_warning_flags: tuple[str, ...],
    matrix_warning_flags: tuple[str, ...],
    *,
    tokens: tuple[str, ...],
) -> int:
    texts = [
        json.dumps(source_status, sort_keys=True),
        *(str(row.get("source_status") or "") for row in coverage_rows),
        *row_warning_flags,
        *matrix_warning_flags,
    ]
    return _count_flag_tokens(tuple(texts), tokens)


def _count_flag_tokens(flags: tuple[str, ...], tokens: tuple[str, ...]) -> int:
    count = 0
    for flag in flags:
        lowered = str(flag).lower()
        if any(token in lowered for token in tokens):
            count += 1
    return count


def _split_flags(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    flags: list[str] = []
    for chunk in str(value).split("|"):
        clean = chunk.strip()
        if clean:
            flags.append(clean)
    return tuple(flags)


def _json(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(
    path: Path,
    result: ConfidenceMissingnessResult,
    outputs: ConfidenceMissingnessPaths,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 11F Confidence And Missingness Layer",
        "",
        "## Purpose",
        "",
        "Phase 11F creates review-only confidence caps from admitted metadata. It "
        "does not read player stat JSON, market context, projections, ADP, rankings, "
        "or active app surfaces.",
        "",
        "## Outputs",
        "",
        f"- `{outputs.review_rows}`",
        f"- `{outputs.receipts}`",
        f"- `{outputs.warnings}`",
        "",
        "## Source Rules",
        "",
        "- Uses only Phase 11A confidence_missingness fields.",
        "- Current prospects come from admitted_prospect_current_feature_matrix.csv.",
        "- Missing evidence creates caps and warnings, never zero, average, or positive evidence.",
        "- Stale-season and lifecycle gaps are warning-driven because those direct "
        "fields are not allowed.",
        "",
        "## Summary",
        "",
        f"- Review rows: {result.summary['review_rows']}",
        f"- NFL player rows: {result.summary['nfl_player_rows']}",
        f"- Current prospect rows: {result.summary['current_prospect_rows']}",
        f"- Historical rookie rows: {result.summary['historical_rookie_rows']}",
        f"- Receipt rows: {result.summary['receipt_rows']}",
        f"- Warning rows: {result.summary['warning_rows']}",
        f"- Market rows used: {result.summary['market_rows_used']}",
        f"- Generic JSON rows used: {result.summary['generic_json_rows_used']}",
        "",
        "## Confidence Status Counts",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    counts: dict[str, int] = {}
    for row in result.review_rows:
        counts[str(row["confidence_status"])] = counts.get(str(row["confidence_status"]), 0) + 1
    for status, count in sorted(counts.items()):
        lines.append(f"| {status} | {count} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
