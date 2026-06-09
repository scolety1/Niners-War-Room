from __future__ import annotations

import csv
import json
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ACTIVE_MODEL_ROOT = Path("local_exports/active_veteran_model_public_sources")
V3_PREVIEW_ROOT = Path("local_exports/nflverse_model_previews")
V3_2_OUTPUT_ROOT = Path("local_exports/truth_set_lab/v3_2/promoted_review_models")

PROMOTE_TO_ACTIVE = "promote_to_active"
PROMOTE_WITH_CONFIDENCE_PENALTY = "promote_with_confidence_penalty"
PREVIEW_ONLY = "preview_only"
CONTEXT_ONLY = "context_only"
REJECTED = "rejected"
UNAVAILABLE = "unavailable"

STATS_FIRST_FILES = (
    "stats_first_normalized_features.csv",
    "stats_first_feature_contributions.csv",
    "stats_first_veteran_model_preview_outputs.csv",
)

ACTIVE_SUPPORT_FILES = (
    "veteran_player_inputs.csv",
    "veteran_feature_registry.csv",
    "veteran_source_catalog.csv",
    "veteran_feature_scores.csv",
    "veteran_manual_overrides.csv",
    "veteran_audit_notes.csv",
    "model_outputs_scored_non_k.csv",
    "sleeper_nflverse_identity_bridge.csv",
    "active_roster_identity_review.csv",
    "model_outlier_acceptances.csv",
    "source_coverage_gap_acceptances.csv",
    "stats_first_preview_outliers.csv",
)

V3_CONTEXT_FILES = (
    "truth_set_v3_source_coverage.csv",
    "truth_set_v3_rejected_field_log.csv",
    "truth_set_v3_movement_vs_v2.csv",
    "truth_set_v3_preview_summary.csv",
    "truth_set_v3_preview_summary.json",
    "truth_set_v3_preview_manifest.json",
    "stats_first_preview_manifest.json",
)

PROMOTION_MATRIX_HEADER = (
    "input_bucket",
    "source_field_group",
    "promotion_status",
    "source_status",
    "model_usage_status",
    "active_schema_output",
    "confidence_policy",
    "reason",
    "restriction",
)

PROMOTION_SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class TruthSetV32PromotionResult:
    output_path: Path
    promotion_matrix_path: Path
    source_coverage_path: Path
    report_path: Path
    manifest_path: Path
    summary_path: Path
    summary: dict[str, object]


def promotion_matrix_rows() -> list[dict[str, object]]:
    return [
        _matrix_row(
            "production",
            "native nflverse production",
            PROMOTE_TO_ACTIVE,
            "imported_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit after validation",
            "Official nflverse player stats replace rejected manual production tables.",
        ),
        _matrix_row(
            "production",
            "rushing/receiving first downs",
            PROMOTE_TO_ACTIVE,
            "imported_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit after validation",
            "Historical first downs are structured nflverse evidence.",
        ),
        _matrix_row(
            "role/usage",
            "derived target share",
            PROMOTE_TO_ACTIVE,
            "derived_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit as derived evidence",
            "Derived from play-by-play counts with explicit denominator.",
        ),
        _matrix_row(
            "role/usage",
            "derived RB carry share",
            PROMOTE_TO_ACTIVE,
            "derived_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit as derived evidence",
            "Derived from play-by-play rushing opportunity counts.",
        ),
        _matrix_row(
            "role/usage",
            "derived RB target share",
            PROMOTE_TO_ACTIVE,
            "derived_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit as derived evidence",
            "Derived from play-by-play target counts.",
        ),
        _matrix_row(
            "role/usage",
            "derived weighted opportunities",
            PROMOTE_TO_ACTIVE,
            "derived_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit as derived evidence",
            "Deterministic local derivation from structured opportunity counts.",
        ),
        _matrix_row(
            "role/usage",
            "red-zone/goal-line usage",
            PROMOTE_TO_ACTIVE,
            "derived_real_data",
            "private_model_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit as derived evidence",
            "Derived from play-by-play yardline filters.",
        ),
        _matrix_row(
            "role/usage",
            "snap share",
            PROMOTE_TO_ACTIVE,
            "imported_real_data",
            "role_context_evidence",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "full credit after identity validation",
            "Imported snap counts are role evidence but not route participation.",
        ),
        _matrix_row(
            "projections",
            "projection raw stat recompute",
            PROMOTE_WITH_CONFIDENCE_PENALTY,
            "recomputed_projection",
            "projection_evidence_with_warning",
            "stats_first_source_coverage.csv|stats_first_normalized_features.csv",
            "confidence penalty retained",
            "Raw stat projections are recomputed into LVE scoring.",
        ),
        _matrix_row(
            "projections",
            "estimated first-down projections",
            PREVIEW_ONLY,
            "estimated_from_history",
            "preview_only",
            "truth_set_v3_1_first_down_projection_estimates.csv",
            "not active scoring evidence",
            "Estimates are useful for audit but not direct projection evidence yet.",
        ),
        _matrix_row(
            "role/usage",
            "true route metrics",
            UNAVAILABLE,
            "unavailable_free_public",
            "not_used",
            "source coverage warning only",
            "lowers role confidence for route-dependent calls",
            "No safe structured free/public source; restricted sources are quarantined.",
            "Do not use PFR, PlayerProfiler, Fantasy Life, or scraped route tables.",
        ),
        _matrix_row(
            "injury",
            "current injury context",
            CONTEXT_ONLY,
            "context_only_unless_sourced",
            "confidence_context_only",
            "stats_first_source_coverage.csv",
            "does not boost confidence",
            "Unsourced healthy rows remain weak context only.",
        ),
        _matrix_row(
            "market",
            "market/liquidity",
            CONTEXT_ONLY,
            "trade_context_only",
            "trade_surface_only",
            "stats_first_source_coverage.csv",
            "zero private value contribution",
            "Market data may explain trade edge but cannot alter private football value.",
        ),
        _matrix_row(
            "young bridge",
            "young bridge prior",
            PROMOTE_WITH_CONFIDENCE_PENALTY,
            "derived_context",
            "young_lifecycle_evidence",
            "stats_first_normalized_features.csv|stats_first_feature_contributions.csv",
            "decay weight and confidence penalty retained",
            "Draft capital/prospect prior applies only to eligible young players.",
        ),
        _matrix_row(
            "rejected",
            "manual agent-collected player-stat tables",
            REJECTED,
            "rejected_manual_source",
            "not_used",
            "truth_set_v3_rejected_field_log.csv",
            "no credit",
            "Manual tables remain rejected unless replaced by strict validated exports.",
        ),
    ]


def build_truth_set_v3_2_safe_promotion(
    *,
    active_model_root: str | Path = ACTIVE_MODEL_ROOT,
    v3_preview_path: str | Path | None = None,
    output_root: str | Path = V3_2_OUTPUT_ROOT,
    promotion_id: str | None = None,
    computed_at: str | None = None,
) -> TruthSetV32PromotionResult:
    active_root = Path(active_model_root)
    preview_path = Path(v3_preview_path) if v3_preview_path else latest_v3_preview_path()
    timestamp = computed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe_id = promotion_id or f"truth_set_v3_2_promoted_review_{_compact_timestamp(timestamp)}"
    output_path = Path(output_root) / safe_id
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    copied = _copy_required_files(active_root, preview_path, output_path)
    coverage_rows = build_promoted_source_coverage_rows(
        active_coverage_rows=_read_dicts(active_root / "stats_first_source_coverage.csv"),
        v3_coverage_rows=_read_dicts(preview_path / "truth_set_v3_source_coverage.csv"),
        normalized_rows=_read_dicts(preview_path / "stats_first_normalized_features.csv"),
    )
    source_coverage_path = output_path / "stats_first_source_coverage.csv"
    _write_dicts(source_coverage_path, tuple(coverage_rows[0].keys()), coverage_rows)

    matrix_rows = promotion_matrix_rows()
    matrix_path = output_path / "truth_set_v3_2_promotion_matrix.csv"
    _write_dicts(matrix_path, PROMOTION_MATRIX_HEADER, matrix_rows)

    summary = _summary(output_path, copied, coverage_rows, matrix_rows, timestamp, preview_path)
    summary_path = output_path / "truth_set_v3_2_promotion_summary.csv"
    _write_dicts(summary_path, PROMOTION_SUMMARY_HEADER, _summary_rows(summary))
    manifest_path = output_path / "truth_set_v3_2_promotion_manifest.json"
    manifest_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    report_path = output_path / "truth_set_v3_2_promotion_report.md"
    report_path.write_text(_markdown_report(summary, matrix_rows), encoding="utf-8")

    return TruthSetV32PromotionResult(
        output_path=output_path,
        promotion_matrix_path=matrix_path,
        source_coverage_path=source_coverage_path,
        report_path=report_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        summary=summary,
    )


def build_promoted_source_coverage_rows(
    *,
    active_coverage_rows: list[dict[str, str]],
    v3_coverage_rows: list[dict[str, str]],
    normalized_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    v3_by_key = _bucket_rows_by_player(v3_coverage_rows)
    normalized_by_key = {
        _player_key(row.get("player_name", ""), row.get("position", "")): row
        for row in normalized_rows
        if row.get("player_name") and row.get("position")
    }
    output: list[dict[str, object]] = []
    for active in active_coverage_rows:
        row: dict[str, object] = dict(active)
        key = _player_key(row.get("player_name", ""), row.get("position", ""))
        buckets = v3_by_key.get(key)
        normalized = normalized_by_key.get(key, {})
        if buckets:
            _promote_player_coverage(row, buckets, normalized)
        else:
            row["truth_set_v3_2_promotion_status"] = "not_in_truth_set_v3"
            row["truth_set_v3_2_promotion_notes"] = "Retained active source coverage row."
        output.append(row)
    return output


def latest_v3_preview_path(root: str | Path = V3_PREVIEW_ROOT) -> Path:
    candidates = [
        path
        for path in Path(root).glob("truth_set_lab_v3_preview_*")
        if path.is_dir() and (path / "truth_set_v3_source_coverage.csv").exists()
    ]
    if not candidates:
        raise FileNotFoundError(f"No Truth Set Lab v3 preview folder found under {root}.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _promote_player_coverage(
    row: dict[str, object],
    buckets: dict[str, dict[str, str]],
    normalized: dict[str, str],
) -> None:
    row["production"] = _coverage_status(
        buckets,
        "production",
        ready_statuses={"imported_real_data"},
        fallback="review_missing",
    )
    role_status = _coverage_status(
        buckets,
        "role_usage",
        ready_statuses={"derived_real_data"},
        fallback="review_missing",
    )
    snap_status = _coverage_status(
        buckets,
        "snap_share",
        ready_statuses={"imported_real_data"},
        fallback="review_missing",
    )
    row["role_usage"] = "ready" if "ready" in {role_status, snap_status} else "review_missing"
    row["projection"] = _projection_bucket_status(buckets)
    if normalized.get("projection_source_status"):
        row["projection_source_status"] = normalized["projection_source_status"]
    row["injury"] = _injury_bucket_status(buckets)
    row["market_liquidity"] = _market_bucket_status(buckets)
    row["truth_set_v3_2_promotion_status"] = "safe_fields_promoted_review_only"
    row["truth_set_v3_2_promotion_notes"] = (
        "Production/usage/snap/projection statuses are promoted into active schema; "
        "route, injury, market, and manual sources remain constrained."
    )
    if _bucket_source_status(buckets, "route_participation") in {
        "unavailable_free_public",
        "missing_paid_or_charted_data",
    }:
        row["route_metrics_source_status"] = _bucket_source_status(
            buckets, "route_participation"
        )
        row["route_metrics_model_usage"] = "not_used"
    row["estimated_first_down_projection_status"] = _first_down_projection_status(normalized)
    row["injury_context_policy"] = "does_not_boost_confidence"
    row["market_context_policy"] = "trade_context_only_zero_private_value"


def _projection_bucket_status(buckets: dict[str, dict[str, str]]) -> str:
    projection = buckets.get("projection", {})
    source_status = str(projection.get("source_status") or "")
    if source_status in {"derived_real_data", "recomputed_projection"}:
        return "ready"
    if source_status in {"missing_projection", ""}:
        return "review_missing"
    return "review"


def _injury_bucket_status(buckets: dict[str, dict[str, str]]) -> str:
    injury = buckets.get("injury", {})
    source_status = str(injury.get("source_status") or "")
    if source_status in {"imported_real_data", "sourced_injury_context"}:
        return "ready"
    if source_status in {"unsourced_or_healthy_context", "context_only"}:
        return "review"
    return "review_missing"


def _market_bucket_status(buckets: dict[str, dict[str, str]]) -> str:
    market = buckets.get("market_liquidity", {})
    source_status = str(market.get("source_status") or "")
    if source_status in {"real_imported_market", "sourced_market_context"}:
        return "ready"
    if source_status in {"missing_market", ""}:
        return "review_missing"
    return "review"


def _coverage_status(
    buckets: dict[str, dict[str, str]],
    bucket: str,
    *,
    ready_statuses: set[str],
    fallback: str,
) -> str:
    source_status = _bucket_source_status(buckets, bucket)
    if source_status in ready_statuses:
        return "ready"
    if source_status:
        return "review"
    return fallback


def _first_down_projection_status(normalized: dict[str, str]) -> str:
    warnings = str(normalized.get("warnings") or "")
    if "projection_first_downs_estimated_from_history" in warnings:
        return "estimated_from_history"
    if "projection_first_downs_missing" in warnings:
        return "missing_first_down_projection"
    return "not_applicable_or_direct_historical"


def _bucket_source_status(buckets: dict[str, dict[str, str]], bucket: str) -> str:
    return str(buckets.get(bucket, {}).get("source_status") or "")


def _bucket_rows_by_player(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, dict[str, str]]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        key = _player_key(row.get("player_name", ""), row.get("position", ""))
        if key == ("", ""):
            continue
        grouped[key][str(row.get("bucket") or "")] = row
    return dict(grouped)


def _copy_required_files(active_root: Path, preview_path: Path, output_path: Path) -> list[str]:
    copied: list[str] = []
    for filename in ACTIVE_SUPPORT_FILES:
        source = active_root / filename
        if source.exists():
            shutil.copy2(source, output_path / filename)
            copied.append(filename)
    for filename in STATS_FIRST_FILES:
        source = preview_path / filename
        if not source.exists():
            raise FileNotFoundError(f"Missing required v3 preview file: {source}")
        shutil.copy2(source, output_path / filename)
        copied.append(filename)
    for filename in V3_CONTEXT_FILES:
        source = preview_path / filename
        if source.exists():
            shutil.copy2(source, output_path / filename)
            copied.append(filename)
    return copied


def _summary(
    output_path: Path,
    copied_files: list[str],
    coverage_rows: list[dict[str, object]],
    matrix_rows: list[dict[str, object]],
    computed_at: str,
    preview_path: Path,
) -> dict[str, object]:
    matrix_counts: dict[str, int] = defaultdict(int)
    for row in matrix_rows:
        matrix_counts[str(row["promotion_status"])] += 1
    truth_rows = [
        row
        for row in coverage_rows
        if row.get("truth_set_v3_2_promotion_status") == "safe_fields_promoted_review_only"
    ]
    return {
        "promotion_id": output_path.name,
        "review_status": "review_only",
        "computed_at": computed_at,
        "output_path": str(output_path),
        "source_preview_path": str(preview_path),
        "active_rankings_overwritten": False,
        "final_money_decision_ready": False,
        "draft_ready_unlocked": False,
        "copied_files": copied_files,
        "copied_file_count": len(copied_files),
        "coverage_rows": len(coverage_rows),
        "truth_set_rows_promoted": len(truth_rows),
        "promotion_status_counts": dict(sorted(matrix_counts.items())),
        "promoted_source_statuses": (
            "production=imported_real_data;"
            "usage=derived_real_data;"
            "snap_share=imported_real_data;"
            "projection=recomputed_with_status"
        ),
        "preview_only_sources": "estimated_first_down_projections|route_metrics",
        "context_only_sources": "injury_context|market_liquidity",
        "rejected_sources": "manual_agent_player_stat_tables|restricted_route_sources",
        "remaining_blockers": (
            "route metrics unavailable without licensed structured source; "
            "injury context remains weak unless sourced; "
            "draft/final gates still require their own checks"
        ),
    }


def _markdown_report(
    summary: dict[str, object],
    matrix_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Truth Set Lab v3.2 Safe Source Promotion Report",
        "",
        f"- Review status: {summary['review_status']}",
        f"- Output path: `{summary['output_path']}`",
        f"- Source preview: `{summary['source_preview_path']}`",
        f"- Active rankings overwritten: {summary['active_rankings_overwritten']}",
        f"- Truth-set rows promoted into active schema: {summary['truth_set_rows_promoted']}",
        "",
        "## Promotion Matrix",
        "",
        "| Input | Field group | Status | Source status | Policy |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in matrix_rows:
        lines.append(
            "| "
            f"{row['input_bucket']} | {row['source_field_group']} | "
            f"{row['promotion_status']} | {row['source_status']} | "
            f"{row['confidence_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Blockers",
            "",
            str(summary["remaining_blockers"]),
            "",
            "## Safety Notes",
            "",
            "- Manual agent-collected player-stat tables remain rejected.",
            "- True route metrics remain unavailable without a licensed structured source.",
            "- Market/liquidity stays trade-context only and has zero private value contribution.",
            "- Unsourced healthy injury rows do not boost confidence.",
            "- Generated outputs remain review-only until formal gates pass.",
            "",
        ]
    )
    return "\n".join(lines)


def _matrix_row(
    input_bucket: str,
    source_field_group: str,
    promotion_status: str,
    source_status: str,
    model_usage_status: str,
    active_schema_output: str,
    confidence_policy: str,
    reason: str,
    restriction: str = "",
) -> dict[str, object]:
    return {
        "input_bucket": input_bucket,
        "source_field_group": source_field_group,
        "promotion_status": promotion_status,
        "source_status": source_status,
        "model_usage_status": model_usage_status,
        "active_schema_output": active_schema_output,
        "confidence_policy": confidence_policy,
        "reason": reason,
        "restriction": restriction,
    }


def _summary_rows(summary: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key, value in summary.items():
        if isinstance(value, (dict, list, tuple)):
            rendered = json.dumps(value, sort_keys=True)
        else:
            rendered = value
        rows.append({"metric": key, "value": rendered})
    return rows


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _player_key(name: object, position: object) -> tuple[str, str]:
    return (str(name or "").strip().lower(), str(position or "").strip().upper())


def _compact_timestamp(timestamp: str) -> str:
    return (
        timestamp.replace("-", "")
        .replace(":", "")
        .replace("T", "T")
        .replace("Z", "Z")
    )
