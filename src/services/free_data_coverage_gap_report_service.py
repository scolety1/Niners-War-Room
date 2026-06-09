from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.free_data_import_coverage_service import (
    build_free_data_import_coverage_matrix,
)
from src.services.source_coverage_audit_service import (
    CRITICAL_BUCKETS,
    REVIEW_BUCKETS,
    build_source_coverage_audit,
)

BUCKET_TO_FREE_MATRIX_BUCKET = {
    "production": "production",
    "role/usage": "role/usage",
    "injury": "injury",
    "age/bio": "age/bio",
    "identity": "identity",
    "projections": "projection",
    "market": "market/liquidity",
    "league rank": "league rank",
}


@dataclass(frozen=True)
class FreeDataCoverageGapReport:
    category_rows: tuple[dict[str, object], ...]
    missing_critical_field_rows: tuple[dict[str, object], ...]
    unavailable_free_source_rows: tuple[dict[str, object], ...]
    recommendation_rows: tuple[dict[str, object], ...]
    source_coverage_summary_rows: tuple[dict[str, object], ...]
    free_data_summary_rows: tuple[dict[str, object], ...]
    review_only_status: bool
    issues: tuple[str, ...]


def build_free_data_coverage_gap_report(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    raw_import_root: str | Path = "templates/real_data_inputs/nflverse_stats_upgrade",
) -> FreeDataCoverageGapReport:
    source_report = build_source_coverage_audit(
        data_pack_path,
        veteran_model_dir=veteran_model_dir,
    )
    free_report = build_free_data_import_coverage_matrix(raw_import_root)
    free_by_bucket = {
        str(row["feature_bucket"]): row
        for row in free_report.coverage_rows
    }
    category_rows = tuple(_category_rows(source_report.bucket_rows, free_by_bucket))
    missing_critical = tuple(
        _missing_critical_field_rows(source_report.bucket_rows, free_by_bucket)
    )
    unavailable = tuple(_unavailable_free_source_rows(free_report.coverage_rows))
    recommendations = tuple(
        _recommendation_rows(category_rows, missing_critical, unavailable)
    )
    issues = tuple(source_report.issues) + tuple(free_report.issues)
    return FreeDataCoverageGapReport(
        category_rows=category_rows,
        missing_critical_field_rows=missing_critical,
        unavailable_free_source_rows=unavailable,
        recommendation_rows=recommendations,
        source_coverage_summary_rows=tuple(source_report.summary_rows),
        free_data_summary_rows=tuple(free_report.summary_rows),
        review_only_status=True,
        issues=issues,
    )


def write_free_data_coverage_gap_report(
    export_dir: str | Path,
    report: FreeDataCoverageGapReport,
) -> dict[str, Path]:
    root = Path(export_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "category_report": root / "free_data_gap_categories.csv",
        "missing_critical_fields": root / "missing_critical_fields.csv",
        "unavailable_free_sources": root / "unavailable_from_free_sources.csv",
        "recommendations": root / "free_data_gap_recommendations.csv",
        "source_coverage_summary": root / "source_coverage_summary.csv",
        "free_data_summary": root / "free_data_summary.csv",
    }
    _write_csv(paths["category_report"], report.category_rows)
    _write_csv(paths["missing_critical_fields"], report.missing_critical_field_rows)
    _write_csv(paths["unavailable_free_sources"], report.unavailable_free_source_rows)
    _write_csv(paths["recommendations"], report.recommendation_rows)
    _write_csv(paths["source_coverage_summary"], report.source_coverage_summary_rows)
    _write_csv(paths["free_data_summary"], report.free_data_summary_rows)
    return paths


def _category_rows(
    bucket_rows: list[dict[str, object]],
    free_by_bucket: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    categories = (
        ("critical_data_available", CRITICAL_BUCKETS, _is_available),
        ("critical_data_missing", CRITICAL_BUCKETS, _is_missing_or_review),
        ("optional_data_available", REVIEW_BUCKETS, _is_available),
        ("optional_data_missing", REVIEW_BUCKETS, _is_missing_or_review),
    )
    rows: list[dict[str, object]] = []
    for category, bucket_set, predicate in categories:
        for bucket in sorted(bucket_set):
            matches = [
                row
                for row in bucket_rows
                if row["bucket"] == bucket and predicate(row)
            ]
            matrix_bucket = BUCKET_TO_FREE_MATRIX_BUCKET.get(bucket, bucket)
            free_row = free_by_bucket.get(matrix_bucket, {})
            players = sorted({str(row["player"]) for row in matches})
            rows.append(
                {
                    "category": category,
                    "bucket": bucket,
                    "players": len(players),
                    "affected_players": "|".join(players[:50]),
                    "truncated_player_list": len(players) > 50,
                    "avg_confidence_impact": _avg(matches, "confidence_penalty"),
                    "decision_blocking_rows": sum(
                        1
                        for row in matches
                        if row.get("decision_effect") == "blocks_decision_trust"
                    ),
                    "free_source_support": free_row.get("support_status", "not_in_matrix"),
                    "free_source_limit": free_row.get("limitations", ""),
                    "next_action": _category_next_action(category, bucket, free_row),
                }
            )
    return rows


def _missing_critical_field_rows(
    bucket_rows: list[dict[str, object]],
    free_by_bucket: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in bucket_rows:
        if row["bucket"] not in CRITICAL_BUCKETS:
            continue
        if not _is_missing_or_review(row):
            continue
        affected_features = _affected_features(row)
        if not affected_features:
            continue
        matrix_bucket = BUCKET_TO_FREE_MATRIX_BUCKET.get(str(row["bucket"]), str(row["bucket"]))
        free_row = free_by_bucket.get(matrix_bucket, {})
        for feature in affected_features:
            imputed = feature in _pipe_set(row.get("imputed_features", ""))
            missing = feature in _pipe_set(row.get("missing_features", ""))
            rows.append(
                {
                    "affected_feature": feature,
                    "affected_player": row["player"],
                    "player_id": row["player_id"],
                    "position": row["position"],
                    "team": row["team"],
                    "bucket": row["bucket"],
                    "bucket_status": row["bucket_status"],
                    "coverage_pct": row["coverage_pct"],
                    "model_currently_imputes": imputed,
                    "model_marks_missing": missing,
                    "confidence_impact": row["confidence_penalty"],
                    "blocks_decision_ready": (
                        row.get("decision_effect") == "blocks_decision_trust"
                    ),
                    "gap_acceptance_status": row.get("gap_acceptance_status", ""),
                    "free_source_support": free_row.get("support_status", "not_in_matrix"),
                    "free_source_limit": free_row.get("limitations", ""),
                    "next_action": row.get("next_action", ""),
                }
            )
    rows.sort(
        key=lambda row: (
            not bool(row["blocks_decision_ready"]),
            str(row["bucket"]),
            str(row["affected_player"]).lower(),
            str(row["affected_feature"]),
        )
    )
    return rows


def _unavailable_free_source_rows(
    free_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in free_rows:
        if row["validation_status"] not in {"external_required", "review"}:
            continue
        output.append(
            {
                "feature_bucket": row["feature_bucket"],
                "free_source_support": row["support_status"],
                "support_level": row["support_level"],
                "unavailable_or_limited_field": row["required_fields"],
                "why_free_data_cannot_fully_solve": row["limitations"],
                "model_usage": row["model_usage"],
                "paid_or_manual_candidate": _paid_or_manual_candidate(str(row["feature_bucket"])),
                "next_action": row["next_action"],
            }
        )
    return output


def _recommendation_rows(
    category_rows: tuple[dict[str, object], ...],
    missing_critical_rows: tuple[dict[str, object], ...],
    unavailable_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    critical_blockers = [
        row for row in missing_critical_rows if row["blocks_decision_ready"]
    ]
    unavailable_buckets = "|".join(str(row["feature_bucket"]) for row in unavailable_rows)
    enough_for = (
        "Free data is enough to audit identity, age/bio, historical production, "
        "first-down/TD fit, and injury context in review-only mode."
    )
    cannot_solve = (
        "Free data cannot fully solve independent projections, true route/participation "
        "quality, expected opportunity, or trade-market liquidity without external exports."
    )
    paid_tests = (
        "If spending money, test projection exports first, then route/usage or expected "
        "opportunity data. Market feeds should stay trade/liquidity only."
    )
    if critical_blockers:
        decision = (
            f"{len(critical_blockers)} critical player-feature gaps still block "
            "decision-ready. Keep rankings review-only."
        )
    else:
        decision = (
            "No missing critical player-feature rows found in this report. Decision-ready "
            "still depends on sanity/outlier gates."
        )
    return [
        {
            "recommendation_type": "what_free_data_is_enough_for",
            "recommendation": enough_for,
            "supporting_detail": _category_count(category_rows, "critical_data_available"),
        },
        {
            "recommendation_type": "what_free_data_cannot_solve",
            "recommendation": cannot_solve,
            "supporting_detail": unavailable_buckets,
        },
        {
            "recommendation_type": "paid_data_worth_testing",
            "recommendation": paid_tests,
            "supporting_detail": "projection|route/usage|expected_opportunity",
        },
        {
            "recommendation_type": "decision_ready_effect",
            "recommendation": decision,
            "supporting_detail": f"blocking_critical_gaps={len(critical_blockers)}",
        },
    ]


def _is_available(row: dict[str, object]) -> bool:
    return float(row.get("coverage_pct", 0)) >= 75


def _is_missing_or_review(row: dict[str, object]) -> bool:
    return float(row.get("coverage_pct", 0)) < 75


def _affected_features(row: dict[str, object]) -> list[str]:
    missing = _pipe_set(row.get("missing_features", ""))
    imputed = _pipe_set(row.get("imputed_features", ""))
    if missing or imputed:
        return sorted(missing | imputed)
    return sorted(_pipe_set(row.get("expected_features", "")))


def _pipe_set(value: object) -> set[str]:
    return {part for part in str(value or "").split("|") if part}


def _avg(rows: list[dict[str, object]], column: str) -> float:
    if not rows:
        return 0.0
    return round(sum(float(row.get(column, 0) or 0) for row in rows) / len(rows), 2)


def _category_next_action(
    category: str,
    bucket: str,
    free_row: dict[str, object],
) -> str:
    if category.endswith("_available"):
        return "No source action; keep receipts visible."
    if bucket in CRITICAL_BUCKETS:
        return "Fill, repair, or explain this critical bucket before decision-ready."
    if free_row.get("validation_status") == "external_required":
        return "Supply a legal export or accept the optional gap with confidence penalty."
    return "Review the optional gap; confidence penalty remains."


def _paid_or_manual_candidate(bucket: str) -> str:
    if bucket == "projection":
        return "paid/free projection export with custom scoring fields"
    if bucket in {"opportunity", "role/usage"}:
        return "route participation, expected opportunity, or charting export"
    if bucket == "market/liquidity":
        return "legal trade-market export, trade/liquidity only"
    return "manual review or local CSV export"


def _category_count(rows: tuple[dict[str, object], ...], category: str) -> str:
    players = sum(int(row["players"]) for row in rows if row["category"] == category)
    return f"player_bucket_rows={players}"


def _write_csv(path: Path, rows: tuple[dict[str, object], ...] | list[dict[str, object]]) -> None:
    fieldnames = tuple(rows[0].keys()) if rows else ("empty",)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
