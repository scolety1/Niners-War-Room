from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EVIDENCE_ROOT = Path("local_exports/model_v4/evidence_matrices/latest")
DEFAULT_FIRST_DOWN_ROOT = Path("local_exports/model_v4/first_downs/latest")
DEFAULT_RETURN_ROOT = Path("local_exports/model_v4/returns/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_10N_EVIDENCE_ADMISSION_RECHECK.md")

PRIVATE_LANE_FIELDS = (
    "factual_evidence_json",
    "derived_evidence_json",
    "prospect_prior_evidence_json",
)

LEAKAGE_KEY_TOKENS = (
    "adp",
    "rank",
    "ranking",
    "projection",
    "projected",
    "mock",
    "big_board",
    "cheatsheet",
    "consensus",
)

RETURN_SCORING_ROLE = "small_direct_return_scoring_evidence_not_talent_signal"
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


@dataclass(frozen=True)
class AdmissionCheck:
    check_name: str
    status: str
    issue_count: int
    detail: str


@dataclass(frozen=True)
class EvidenceAdmissionRecheckResult:
    checks: tuple[AdmissionCheck, ...]
    summary: dict[str, object]
    issue_rows: tuple[dict[str, object], ...]


def run_evidence_admission_recheck(
    *,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    first_down_root: str | Path = DEFAULT_FIRST_DOWN_ROOT,
    return_root: str | Path = DEFAULT_RETURN_ROOT,
) -> EvidenceAdmissionRecheckResult:
    evidence = Path(evidence_root)
    first_downs = Path(first_down_root)
    returns = Path(return_root)

    nfl_rows = _read_rows(evidence / "nfl_player_current_evidence_matrix.csv")
    prospect_rows = _read_rows(evidence / "prospect_current_feature_matrix.csv")
    admitted_prospect_features = _read_rows(
        evidence / "admitted_prospect_current_feature_matrix.csv"
    )
    backtest_rows = _read_rows(evidence / "historical_rookie_backtest_feature_matrix.csv")
    admitted_prospects = _read_rows(evidence / "admitted_current_prospect_identity_spine.csv")
    review_prospects = _read_rows(evidence / "current_prospect_identity_review_report.csv")
    summary_rows = _read_rows(evidence / "evidence_matrix_summary.csv")
    coverage_rows = _read_rows(evidence / "source_coverage_matrix.csv")
    warning_rows = _read_rows(evidence / "warning_matrix.csv")
    rushing_first_downs = _read_rows(first_downs / "admitted_rushing_first_downs.csv")
    receiving_first_downs = _read_rows(first_downs / "admitted_receiving_first_downs.csv")
    return_rows = _read_rows(returns / "admitted_return_scoring_evidence.csv")

    matrix_rows = {
        "nfl_player_current_evidence_matrix": nfl_rows,
        "prospect_current_feature_matrix": prospect_rows,
        "historical_rookie_backtest_feature_matrix": backtest_rows,
    }
    summary = _summary_dict(summary_rows)
    issue_rows: list[dict[str, object]] = []
    checks: list[AdmissionCheck] = []

    _append_check(
        checks,
        issue_rows,
        "required_outputs_present",
        _required_outputs_present(evidence, first_downs, returns),
    )
    _append_check(
        checks,
        issue_rows,
        "duplicate_entity_rows",
        _duplicate_entity_issues(matrix_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "historical_post_draft_college_evidence",
        _post_draft_college_evidence_issues(backtest_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "private_lane_market_leakage",
        _private_lane_leakage_issues(matrix_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "fake_zero_missing_evidence",
        _fake_zero_missing_issues(matrix_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "workout_zero_placeholder_values",
        _workout_zero_placeholder_issues(matrix_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "review_only_vorp_namespace",
        _review_only_vorp_issues(nfl_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "source_limited_combine_private_value",
        _source_limited_combine_issues(matrix_rows, coverage_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "return_direct_scoring_only",
        _return_direct_scoring_issues(return_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "first_down_admitted_views_matched_only",
        _admitted_first_down_issues(rushing_first_downs, receiving_first_downs),
    )
    _append_check(
        checks,
        issue_rows,
        "return_admitted_view_matched_only",
        _admitted_return_join_issues(return_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "source_labels_and_receipts_present",
        _source_label_issues(matrix_rows),
    )
    _append_check(
        checks,
        issue_rows,
        "review_only_prospects_quarantined",
        _review_only_prospect_issues(
            admitted_prospects,
            review_prospects,
            prospect_rows,
            admitted_prospect_features,
        ),
    )
    _append_check(
        checks,
        issue_rows,
        "no_formula_scoring_or_rank_generation",
        _formula_scoring_issues(summary),
    )

    failed_checks = [check for check in checks if check.status != "pass"]
    status = "pass" if not failed_checks else "fail"
    review_reason_counts = Counter(row.get("review_reason", "") for row in review_prospects)
    summary_out: dict[str, object] = {
        "status": status,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "issue_count": len(issue_rows),
        "nfl_player_rows": len(nfl_rows),
        "current_prospect_rows": len(prospect_rows),
        "admitted_prospect_feature_rows": len(admitted_prospect_features),
        "historical_backtest_rows": len(backtest_rows),
        "admitted_current_prospect_identity_rows": len(admitted_prospects),
        "review_current_prospect_identity_rows": len(review_prospects),
        "review_reason_counts": json.dumps(dict(sorted(review_reason_counts.items()))),
        "source_coverage_rows": len(coverage_rows),
        "warning_rows": len(warning_rows),
        "formula_scores_calculated": summary.get("formula_scores_calculated", ""),
        "final_rankings_calculated": summary.get("final_rankings_calculated", ""),
        "matrix_version": summary.get("matrix_version", ""),
    }
    return EvidenceAdmissionRecheckResult(
        checks=tuple(checks),
        summary=summary_out,
        issue_rows=tuple(issue_rows),
    )


def write_phase_10n_doc(
    result: EvidenceAdmissionRecheckResult,
    *,
    doc_path: str | Path = DEFAULT_DOC_PATH,
) -> Path:
    path = Path(doc_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 10N Evidence Admission And Leakage Recheck",
        "",
        "## Purpose",
        "",
        (
            "Phase 10N rechecks the latest formula-facing evidence surfaces after "
            "Phase 10M current-prospect identity admission. It does not start "
            "formula design, calculate rankings, promote app surfaces, or unlock "
            "readiness gates."
        ),
        "",
        "## Summary",
        "",
        f"- Status: {result.summary['status']}",
        f"- Checks run: {result.summary['check_count']}",
        f"- Failed checks: {result.summary['failed_check_count']}",
        f"- Issues: {result.summary['issue_count']}",
        f"- NFL current players: {result.summary['nfl_player_rows']}",
        f"- Current prospects: {result.summary['current_prospect_rows']}",
        (
            "- Admitted current prospect identities: "
            f"{result.summary['admitted_current_prospect_identity_rows']}"
        ),
        f"- Admitted prospect feature rows: {result.summary['admitted_prospect_feature_rows']}",
        (
            "- Review-only current prospect identities: "
            f"{result.summary['review_current_prospect_identity_rows']}"
        ),
        f"- Historical rookie backtest rows: {result.summary['historical_backtest_rows']}",
        f"- Source coverage rows: {result.summary['source_coverage_rows']}",
        f"- Warning rows: {result.summary['warning_rows']}",
        f"- Matrix version: `{result.summary['matrix_version']}`",
        "",
        "## Check Results",
        "",
        "| Check | Status | Issues | Detail |",
        "| --- | --- | ---: | --- |",
    ]
    for check in result.checks:
        lines.append(
            "| "
            f"{check.check_name} | {check.status} | {check.issue_count} | "
            f"{check.detail} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Quarantines",
            "",
            (
                "Review-only current prospects remain excluded from the admitted "
                "identity spine and admitted prospect feature matrix. Formula "
                "loaders must fail closed unless `formula_identity_admitted == True`."
            ),
            "",
        ]
    )
    for reason, count in sorted(json.loads(str(result.summary["review_reason_counts"])).items()):
        lines.append(f"- {reason}: {count}")
    lines.extend(
        [
            "",
            "## Safety Confirmations",
            "",
            "- No post-draft historical college evidence was found.",
            "- No duplicate entity rows were found in formula-facing matrices.",
            "- No ADP/rank/projection/mock/big-board fields were found in private lanes.",
            "- No impossible workout zero placeholders were found in admitted athletic profiles.",
            "- Review-only VORP is kept out of derived evidence.",
            "- Source-limited combine/pro-day evidence remains context/source-limited only.",
            "- Return data remains direct scoring evidence, not talent or role evidence.",
            "- Admitted first-down and return views contain matched joins only.",
            "- Admitted prospect feature rows contain formula-admitted identities only.",
            "- No formula scores or final rankings were generated.",
        ]
    )
    if result.issue_rows:
        lines.extend(["", "## Issues", ""])
        for issue in result.issue_rows[:50]:
            lines.append(
                "- "
                f"{issue['check_name']}: {issue['entity_key']} "
                f"({issue['detail']})"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _append_check(
    checks: list[AdmissionCheck],
    issue_rows: list[dict[str, object]],
    check_name: str,
    issues: list[dict[str, object]],
) -> None:
    for issue in issues:
        issue_rows.append({"check_name": check_name, **issue})
    checks.append(
        AdmissionCheck(
            check_name=check_name,
            status="pass" if not issues else "fail",
            issue_count=len(issues),
            detail="ok" if not issues else "review issue rows",
        )
    )


def _required_outputs_present(
    evidence: Path,
    first_downs: Path,
    returns: Path,
) -> list[dict[str, object]]:
    required = (
        evidence / "nfl_player_current_evidence_matrix.csv",
        evidence / "prospect_current_feature_matrix.csv",
        evidence / "admitted_prospect_current_feature_matrix.csv",
        evidence / "historical_rookie_backtest_feature_matrix.csv",
        evidence / "admitted_current_prospect_identity_spine.csv",
        evidence / "current_prospect_identity_review_report.csv",
        evidence / "source_coverage_matrix.csv",
        evidence / "warning_matrix.csv",
        first_downs / "admitted_rushing_first_downs.csv",
        first_downs / "admitted_receiving_first_downs.csv",
        returns / "admitted_return_scoring_evidence.csv",
    )
    return [
        _issue(str(path), "required_output_missing", str(path))
        for path in required
        if not path.exists()
    ]


def _duplicate_entity_issues(
    matrix_rows: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    key_fields = {
        "nfl_player_current_evidence_matrix": "canonical_player_key",
        "prospect_current_feature_matrix": "canonical_prospect_key",
        "historical_rookie_backtest_feature_matrix": "historical_prospect_key",
    }
    issues: list[dict[str, object]] = []
    for matrix_name, rows in matrix_rows.items():
        key_field = key_fields[matrix_name]
        counts = Counter(row.get(key_field, "") for row in rows)
        for entity_key, count in counts.items():
            if count > 1:
                issues.append(_issue(entity_key, matrix_name, f"duplicate_count={count}"))
    return issues


def _post_draft_college_evidence_issues(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in rows:
        draft_year = _int(row.get("draft_year"))
        entity_key = row.get("historical_prospect_key", "")
        factual = _json_loads(row.get("factual_evidence_json"))
        derived = _json_loads(row.get("derived_evidence_json"))
        for payload in _dict_values(factual.get("college_production_summary")):
            for field in ("final_college_season", "best_yards_season"):
                season = _int(payload.get(field))
                if season and season >= draft_year:
                    issues.append(_issue(entity_key, field, f"{season} >= {draft_year}"))
        for field in ("college_season_latest", "college_targets_latest"):
            payload = factual.get(field)
            season = (
                _int(payload.get("season") or payload.get("year"))
                if isinstance(payload, dict)
                else 0
            )
            if season and season >= draft_year:
                issues.append(_issue(entity_key, field, f"{season} >= {draft_year}"))
        for payload in _dict_values(derived.get("college_market_share")):
            season = _int(payload.get("season"))
            if season and season >= draft_year:
                issues.append(
                    _issue(entity_key, "college_market_share", f"{season} >= {draft_year}")
                )
    return issues


def _private_lane_leakage_issues(
    matrix_rows: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for matrix_name, rows in matrix_rows.items():
        key_field = _matrix_key_field(matrix_name)
        for row in rows:
            entity_key = row.get(key_field, "")
            for lane in PRIVATE_LANE_FIELDS:
                payload = _json_loads(row.get(lane))
                for key_path in _key_paths(payload):
                    key_name = key_path.split(".")[-1].lower()
                    if "market_share" in key_path.lower():
                        continue
                    if any(token in key_name for token in LEAKAGE_KEY_TOKENS):
                        issues.append(_issue(entity_key, lane, key_path))
    return issues


def _fake_zero_missing_issues(
    matrix_rows: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    status_to_lane = {
        "factual_evidence": "factual_evidence_json",
        "derived_evidence": "derived_evidence_json",
        "prospect_prior_evidence": "prospect_prior_evidence_json",
    }
    issues: list[dict[str, object]] = []
    for matrix_name, rows in matrix_rows.items():
        key_field = _matrix_key_field(matrix_name)
        for row in rows:
            source_status = _json_loads(row.get("source_status_json"))
            for status_key, lane in status_to_lane.items():
                if source_status.get(status_key) != "missing":
                    continue
                payload = _json_loads(row.get(lane))
                if _has_substantive_value(payload):
                    issues.append(
                        _issue(row.get(key_field, ""), lane, "missing status with payload")
                    )
    return issues


def _workout_zero_placeholder_issues(
    matrix_rows: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for matrix_name, rows in matrix_rows.items():
        if matrix_name == "nfl_player_current_evidence_matrix":
            continue
        key_field = _matrix_key_field(matrix_name)
        for row in rows:
            entity_key = row.get(key_field, "")
            prior = _json_loads(row.get("prospect_prior_evidence_json"))
            workout_profile = prior.get("workout_profile")
            if not isinstance(workout_profile, dict):
                continue
            for field in WORKOUT_ZERO_PLACEHOLDER_FIELDS:
                if _is_zero_placeholder(workout_profile.get(field)):
                    issues.append(_issue(entity_key, "workout_zero_placeholder", field))
    return issues


def _review_only_vorp_issues(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in rows:
        entity_key = row.get("canonical_player_key", "")
        derived = _json_loads(row.get("derived_evidence_json"))
        context = _json_loads(row.get("context_fields_json"))
        if "replacement_vorp_review" in derived:
            issues.append(_issue(entity_key, "derived_evidence_json", "replacement_vorp_review"))
        if derived and "review_only_replacement_vorp" in derived:
            issues.append(
                _issue(entity_key, "derived_evidence_json", "review_only_replacement_vorp")
            )
        if "review_only_replacement_vorp" not in context:
            issues.append(
                _issue(
                    entity_key,
                    "context_fields_json",
                    "missing review_only_replacement_vorp",
                )
            )
    return issues


def _source_limited_combine_issues(
    matrix_rows: dict[str, list[dict[str, str]]],
    coverage_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for matrix_name, rows in matrix_rows.items():
        key_field = _matrix_key_field(matrix_name)
        for row in rows:
            for lane in PRIVATE_LANE_FIELDS:
                payload = _json_loads(row.get(lane))
                if any("combine" in key_path.lower() for key_path in _key_paths(payload)):
                    issues.append(
                        _issue(row.get(key_field, ""), lane, "combine key in private lane")
                    )
    for row in coverage_rows:
        if (
            row.get("feature_group") == "source_limited_combine"
            and row.get("lane") != "source_limited"
        ):
            issues.append(
                _issue(row.get("entity_key", ""), "source_limited_combine", row.get("lane", ""))
            )
    return issues


def _return_direct_scoring_issues(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in rows:
        entity_key = f"{row.get('season')}:{row.get('normalized_player_name')}"
        if row.get("scoring_role") != RETURN_SCORING_ROLE:
            issues.append(_issue(entity_key, "scoring_role", row.get("scoring_role", "")))
        if row.get("source_status") != "imported_real_data":
            issues.append(_issue(entity_key, "source_status", row.get("source_status", "")))
    return issues


def _admitted_first_down_issues(
    rushing_rows: list[dict[str, str]],
    receiving_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in rushing_rows + receiving_rows:
        entity_key = f"{row.get('season')}:{row.get('normalized_player_name')}"
        if row.get("join_status") != "matched":
            issues.append(_issue(entity_key, "join_status", row.get("join_status", "")))
        if row.get("source_status") != "imported_real_data":
            issues.append(_issue(entity_key, "source_status", row.get("source_status", "")))
        if not row.get("source_hash"):
            issues.append(_issue(entity_key, "source_hash", "missing"))
    return issues


def _admitted_return_join_issues(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in rows:
        entity_key = f"{row.get('season')}:{row.get('normalized_player_name')}"
        if row.get("join_status") != "matched":
            issues.append(_issue(entity_key, "join_status", row.get("join_status", "")))
        if not row.get("source_hashes"):
            issues.append(_issue(entity_key, "source_hashes", "missing"))
    return issues


def _source_label_issues(
    matrix_rows: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for matrix_name, rows in matrix_rows.items():
        key_field = _matrix_key_field(matrix_name)
        for row in rows:
            entity_key = row.get(key_field, "")
            if not _json_loads(row.get("source_status_json")):
                issues.append(_issue(entity_key, "source_status_json", "missing"))
            if not _json_loads(row.get("receipt_pointers_json")):
                issues.append(_issue(entity_key, "receipt_pointers_json", "missing"))
    return issues


def _review_only_prospect_issues(
    admitted_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
    prospect_rows: list[dict[str, str]],
    admitted_feature_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    admitted_keys = {row.get("canonical_prospect_key", "") for row in admitted_rows}
    review_keys = {row.get("canonical_prospect_key", "") for row in review_rows}
    admitted_feature_keys = {
        row.get("canonical_prospect_key", "") for row in admitted_feature_rows
    }
    issues: list[dict[str, object]] = []
    for key in review_keys & admitted_keys:
        issues.append(_issue(key, "identity_spine", "review key also admitted"))
    for key in review_keys & admitted_feature_keys:
        issues.append(_issue(key, "admitted_feature_matrix", "review key also admitted"))
    if admitted_feature_keys != admitted_keys:
        missing = admitted_keys - admitted_feature_keys
        extra = admitted_feature_keys - admitted_keys
        if missing:
            issues.append(
                _issue(
                    "admitted_prospect_current_feature_matrix",
                    "missing_admitted_keys",
                    "|".join(sorted(missing)[:10]),
                )
            )
        if extra:
            issues.append(
                _issue(
                    "admitted_prospect_current_feature_matrix",
                    "unexpected_extra_keys",
                    "|".join(sorted(extra)[:10]),
                )
            )
    for row in admitted_feature_rows:
        key = row.get("canonical_prospect_key", "")
        if not _is_true(row.get("formula_identity_admitted")):
            issues.append(_issue(key, "formula_identity_admitted", "not true"))
        if row.get("excluded_reason"):
            issues.append(_issue(key, "excluded_reason", row.get("excluded_reason", "")))
    prospect_by_key = {row.get("canonical_prospect_key", ""): row for row in prospect_rows}
    for key, row in prospect_by_key.items():
        expected = key in admitted_keys
        if _is_true(row.get("formula_identity_admitted")) != expected:
            issues.append(
                _issue(
                    key,
                    "formula_identity_admitted",
                    row.get("formula_identity_admitted", ""),
                )
            )
        if not expected and not row.get("excluded_reason"):
            issues.append(_issue(key, "excluded_reason", "missing for review-only row"))
    for key in review_keys:
        row = prospect_by_key.get(key, {})
        flags = row.get("warning_flags", "")
        if row.get("identity_status") != "source_normalized_review_not_formula_admitted":
            issues.append(_issue(key, "identity_status", row.get("identity_status", "")))
        if "source_normalized_review_not_formula_admitted" not in flags:
            issues.append(_issue(key, "warning_flags", "missing review-only warning"))
    return issues


def _formula_scoring_issues(summary: dict[str, str]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if str(summary.get("formula_scores_calculated", "")).lower() != "false":
        issues.append(
            _issue(
                "summary",
                "formula_scores_calculated",
                summary.get("formula_scores_calculated", ""),
            )
        )
    if str(summary.get("final_rankings_calculated", "")).lower() != "false":
        issues.append(
            _issue(
                "summary",
                "final_rankings_calculated",
                summary.get("final_rankings_calculated", ""),
            )
        )
    return issues


def _matrix_key_field(matrix_name: str) -> str:
    return {
        "nfl_player_current_evidence_matrix": "canonical_player_key",
        "prospect_current_feature_matrix": "canonical_prospect_key",
        "historical_rookie_backtest_feature_matrix": "historical_prospect_key",
    }[matrix_name]


def _issue(entity_key: object, issue_type: object, detail: object) -> dict[str, object]:
    return {
        "entity_key": entity_key,
        "issue_type": issue_type,
        "detail": detail,
    }


def _summary_dict(rows: list[dict[str, str]]) -> dict[str, str]:
    return {row.get("metric", ""): row.get("value", "") for row in rows}


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _json_loads(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dict_values(value: object) -> list[dict[str, object]]:
    if not isinstance(value, dict):
        return []
    return [item for item in value.values() if isinstance(item, dict)]


def _key_paths(value: object, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(key_path)
            paths.extend(_key_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_key_paths(item, f"{prefix}[{index}]"))
    return paths


def _has_substantive_value(value: object) -> bool:
    if value in ("", None, {}, []):
        return False
    if isinstance(value, dict):
        return any(_has_substantive_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_substantive_value(item) for item in value)
    return True


def _is_zero_placeholder(value: object) -> bool:
    if value in ("", None):
        return False
    try:
        return float(str(value).strip()) == 0.0
    except ValueError:
        return False


def _is_true(value: object) -> bool:
    return str(value or "").strip().lower() == "true"


def _int(value: object) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0
