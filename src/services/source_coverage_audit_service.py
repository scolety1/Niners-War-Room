from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.feature_data_truth_contract_service import (
    SOURCE_NEUTRAL_IMPUTATION,
    classify_feature_truth,
)
from src.services.identity_audit_service import build_identity_audit
from src.services.player_feature_receipts_service import DEFAULT_RECEIPT_VETERAN_MODEL_DIR
from src.services.source_gap_acceptance_service import (
    SOURCE_GAP_ACCEPTANCE_FILE,
    source_gap_acceptance_lookup,
)
from src.services.veteran_model_schema_service import (
    VeteranFeatureDefinition,
    VeteranFeatureScore,
    VeteranPlayerRow,
    VeteranSourceRow,
)
from src.services.veteran_model_service import run_veteran_model_from_dir
from src.services.warning_language_service import warning_summary

BUCKETS = (
    "production",
    "projections",
    "role/usage",
    "injury",
    "age/bio",
    "identity",
    "market",
    "league rank",
)
CRITICAL_BUCKETS = {"production", "role/usage", "age/bio", "identity"}
REVIEW_BUCKETS = {"projections", "injury", "market"}
GOVERNANCE_BUCKETS = {"league rank"}
CORE_BUCKETS = CRITICAL_BUCKETS
DECISION_BLOCKING_BUCKETS = CRITICAL_BUCKETS
ACCEPTANCE_FILE = SOURCE_GAP_ACCEPTANCE_FILE
IDENTITY_FEATURE = "__identity_match__"
BUCKET_CONFIDENCE_PENALTY = {
    "production": 12.0,
    "projections": 10.0,
    "role/usage": 12.0,
    "injury": 6.0,
    "age/bio": 4.0,
    "identity": 10.0,
    "market": 0.0,
    "league rank": 2.0,
}
LEAGUE_RANK_FEATURE = "__league_rank__"
STATS_FIRST_SOURCE_COVERAGE_FILE = "stats_first_source_coverage.csv"
STATS_FIRST_NORMALIZED_FEATURE_FILE = "stats_first_normalized_features.csv"

EXPECTED_BUCKET_FEATURES = {
    "QB": {
        "production": ("passing_td_yardage_output", "rushing_value"),
        "projections": ("lve_projection_value",),
        "role/usage": ("role_security", "start_security"),
        "injury": ("current_injury_durability",),
        "age/bio": ("age_curve",),
        "market": ("market_liquidity",),
        "league rank": (LEAGUE_RANK_FEATURE,),
    },
    "RB": {
        "production": (
            "high_value_touches",
            "first_down_td_fit",
            "rush_efficiency_creation",
        ),
        "projections": ("lve_projection_value",),
        "role/usage": ("role_security", "touch_share", "goal_line_short_yardage_role"),
        "injury": ("injury_durability",),
        "age/bio": ("age_curve",),
        "market": ("market_liquidity",),
        "league rank": (LEAGUE_RANK_FEATURE,),
    },
    "WR": {
        "production": ("target_earning", "yards_per_route_run", "first_down_profile"),
        "projections": ("lve_projection_value",),
        "role/usage": ("role_security", "target_earning_stability"),
        "injury": ("injury_durability",),
        "age/bio": ("age_curve",),
        "market": ("market_liquidity",),
        "league rank": (LEAGUE_RANK_FEATURE,),
    },
    "TE": {
        "production": ("targets_per_route_run", "yards_per_route_run", "first_downs_per_route"),
        "projections": ("lve_projection_value",),
        "role/usage": ("role_security", "route_share_stability"),
        "injury": ("injury_durability",),
        "age/bio": ("age_curve",),
        "market": ("market_liquidity",),
        "league rank": (LEAGUE_RANK_FEATURE,),
    },
}
PRODUCTION_FEATURES = {
    feature
    for position_features in EXPECTED_BUCKET_FEATURES.values()
    for feature in position_features["production"]
}
PROJECTION_FEATURES = {
    feature
    for position_features in EXPECTED_BUCKET_FEATURES.values()
    for feature in position_features["projections"]
}
ROLE_USAGE_FEATURES = {
    feature
    for position_features in EXPECTED_BUCKET_FEATURES.values()
    for feature in position_features["role/usage"]
}


@dataclass(frozen=True)
class SourceCoverageAuditReport:
    player_rows: list[dict[str, object]]
    bucket_rows: list[dict[str, object]]
    feature_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    missing_critical_rows: list[dict[str, object]]
    review_gap_rows: list[dict[str, object]]
    accepted_review_gap_rows: list[dict[str, object]]
    invalid_gap_acceptance_rows: list[dict[str, object]]
    gap_acceptance_summary_rows: list[dict[str, object]]
    players: list[str]
    buckets: list[str]
    statuses: list[str]
    issues: list[str]
    source_root: str


def build_source_coverage_audit(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> SourceCoverageAuditReport:
    source_root = (
        Path(veteran_model_dir)
        if veteran_model_dir
        else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    stats_first_report = _build_stats_first_source_coverage_report(source_root)
    if stats_first_report is not None:
        return stats_first_report
    try:
        model_run = run_veteran_model_from_dir(source_root)
    except ValueError as exc:
        return _empty_report(source_root, [str(exc)])

    report = model_run.schema_report
    registry_by_position = _registry_by_position(report.registry)
    feature_lookup = {
        (feature.player_id, feature.feature_name): feature
        for feature in report.feature_scores
    }
    source_lookup = {source.source_key: source for source in report.sources}
    score_lookup = {score.player_id: score for score in model_run.scores}
    acceptance_lookup, acceptance_report = source_gap_acceptance_lookup(
        source_root / ACCEPTANCE_FILE
    )
    identity_lookup = _identity_lookup(data_pack_path, source_root)

    feature_rows: list[dict[str, object]] = []
    bucket_rows: list[dict[str, object]] = []
    player_rows: list[dict[str, object]] = []
    for player in report.players:
        player_feature_rows, player_bucket_rows = _player_coverage_rows(
            player,
            registry_by_position.get(player.position, {}),
            feature_lookup,
            source_lookup,
            identity_lookup,
            acceptance_lookup,
        )
        feature_rows.extend(player_feature_rows)
        bucket_rows.extend(player_bucket_rows)
        player_rows.append(
            _player_summary_row(
                player,
                player_bucket_rows,
                score_lookup.get(player.player_id),
            )
        )

    player_rows.sort(
        key=lambda row: (
            _status_priority(str(row["coverage_status"])),
            float(row["coverage_pct"]),
            str(row["player"]).lower(),
        )
    )
    bucket_rows.sort(
        key=lambda row: (
            _status_priority(str(row["bucket_status"])),
            str(row["player"]).lower(),
            BUCKETS.index(str(row["bucket"])),
        )
    )
    feature_rows.sort(
        key=lambda row: (
            str(row["player"]).lower(),
            BUCKETS.index(str(row["bucket"])),
            str(row["feature_name"]),
        )
    )
    return SourceCoverageAuditReport(
        player_rows=player_rows,
        bucket_rows=bucket_rows,
        feature_rows=feature_rows,
        summary_rows=_summary_rows(player_rows, bucket_rows),
        missing_critical_rows=[
            row
            for row in bucket_rows
            if row["decision_blocking_bucket"] and int(row["missing_feature_count"]) > 0
        ],
        review_gap_rows=[
            row
            for row in bucket_rows
            if row["coverage_class"] == "review"
            and row["coverage_pct"] < 75
            and row["gap_acceptance_status"] != "accepted"
        ],
        accepted_review_gap_rows=[
            row
            for row in bucket_rows
            if row["coverage_class"] == "review"
            and row["coverage_pct"] < 75
            and row["gap_acceptance_status"] == "accepted"
        ],
        invalid_gap_acceptance_rows=acceptance_report.invalid_rows,
        gap_acceptance_summary_rows=acceptance_report.summary_rows,
        players=sorted({str(row["player"]) for row in player_rows}),
        buckets=list(BUCKETS),
        statuses=sorted({str(row["coverage_status"]) for row in player_rows}),
        issues=[],
        source_root=str(source_root),
    )


def _empty_report(root: Path, issues: list[str]) -> SourceCoverageAuditReport:
    return SourceCoverageAuditReport(
        [], [], [], [], [], [], [], [], [], [], [], [], issues, str(root)
    )


def _build_stats_first_source_coverage_report(
    source_root: Path,
) -> SourceCoverageAuditReport | None:
    coverage_path = source_root / STATS_FIRST_SOURCE_COVERAGE_FILE
    normalized_path = source_root / STATS_FIRST_NORMALIZED_FEATURE_FILE
    players_path = source_root / "veteran_player_inputs.csv"
    if not coverage_path.exists() or not normalized_path.exists() or not players_path.exists():
        return None

    coverage_rows = _csv_rows(coverage_path)
    normalized_rows = _csv_rows(normalized_path)
    player_rows_raw = _csv_rows(players_path)
    coverage_by_gsis = {
        str(row.get("player_id") or ""): row
        for row in coverage_rows
        if row.get("player_id")
    }
    coverage_by_name_position = {
        _player_key(row.get("player_name", ""), row.get("position", "")): row
        for row in coverage_rows
        if row.get("player_name") and row.get("position")
    }
    normalized_by_sleeper = {
        str(row.get("sleeper_id") or ""): row
        for row in normalized_rows
        if row.get("sleeper_id")
    }
    normalized_by_name_position = {
        _player_key(row.get("player_name", ""), row.get("position", "")): row
        for row in normalized_rows
        if row.get("player_name") and row.get("position")
    }
    acceptance_lookup, acceptance_report = source_gap_acceptance_lookup(
        source_root / ACCEPTANCE_FILE
    )

    feature_rows: list[dict[str, object]] = []
    bucket_rows: list[dict[str, object]] = []
    player_rows: list[dict[str, object]] = []
    for player in player_rows_raw:
        player_id = str(player.get("player_id") or "")
        player_name = str(player.get("player_name") or "")
        position = str(player.get("position") or "")
        name_key = _player_key(player_name, position)
        normalized = normalized_by_sleeper.get(player_id) or normalized_by_name_position.get(
            name_key, {}
        )
        gsis_id = str(normalized.get("gsis_id") or normalized.get("player_id") or "")
        coverage = coverage_by_gsis.get(gsis_id) or coverage_by_name_position.get(
            name_key, {}
        )
        per_player_features: list[dict[str, object]] = []
        per_player_buckets: list[dict[str, object]] = []
        for bucket in BUCKETS:
            feature_row = _stats_first_feature_row(
                player,
                normalized,
                coverage,
                bucket,
                source_root=source_root,
            )
            per_player_features.append(feature_row)
            per_player_buckets.append(
                _stats_first_bucket_row(
                    player,
                    bucket,
                    feature_row,
                    _acceptance_row(acceptance_lookup, player_id, bucket),
                )
            )
        feature_rows.extend(per_player_features)
        bucket_rows.extend(per_player_buckets)
        player_rows.append(
            _stats_first_player_row(player, normalized, per_player_buckets)
        )

    player_rows.sort(
        key=lambda row: (
            _status_priority(str(row["coverage_status"])),
            float(row["coverage_pct"]),
            str(row["player"]).lower(),
        )
    )
    bucket_rows.sort(
        key=lambda row: (
            _status_priority(str(row["bucket_status"])),
            str(row["player"]).lower(),
            BUCKETS.index(str(row["bucket"])),
        )
    )
    feature_rows.sort(
        key=lambda row: (
            str(row["player"]).lower(),
            BUCKETS.index(str(row["bucket"])),
            str(row["feature_name"]),
        )
    )
    return SourceCoverageAuditReport(
        player_rows=player_rows,
        bucket_rows=bucket_rows,
        feature_rows=feature_rows,
        summary_rows=_summary_rows(player_rows, bucket_rows),
        missing_critical_rows=[
            row
            for row in bucket_rows
            if row["decision_blocking_bucket"] and int(row["missing_feature_count"]) > 0
        ],
        review_gap_rows=[
            row
            for row in bucket_rows
            if row["coverage_class"] == "review"
            and row["coverage_pct"] < 75
            and row["gap_acceptance_status"] != "accepted"
        ],
        accepted_review_gap_rows=[
            row
            for row in bucket_rows
            if row["coverage_class"] == "review"
            and row["coverage_pct"] < 75
            and row["gap_acceptance_status"] == "accepted"
        ],
        invalid_gap_acceptance_rows=acceptance_report.invalid_rows,
        gap_acceptance_summary_rows=acceptance_report.summary_rows,
        players=sorted({str(row["player"]) for row in player_rows}),
        buckets=list(BUCKETS),
        statuses=sorted({str(row["coverage_status"]) for row in player_rows}),
        issues=[],
        source_root=str(source_root),
    )


def _stats_first_feature_row(
    player: dict[str, str],
    normalized: dict[str, str],
    coverage: dict[str, str],
    bucket: str,
    *,
    source_root: Path,
) -> dict[str, object]:
    raw_status = _stats_first_bucket_status(coverage, bucket, player, normalized)
    data_status = _stats_first_feature_data_status(raw_status)
    feature_name = _stats_first_feature_name(bucket, normalized)
    normalized_score = _stats_first_normalized_score(normalized, bucket)
    truth = classify_feature_truth(
        feature_name,
        normalized,
        raw_value=normalized_score,
        warning_reason=normalized.get("warnings", ""),
    )
    if truth.source_status == SOURCE_NEUTRAL_IMPUTATION and data_status == "real":
        data_status = "estimated_or_proxy"
    return {
        "player_id": player.get("player_id", ""),
        "player": player.get("player_name", ""),
        "position": player.get("position", ""),
        "team": player.get("team_name", ""),
        "bucket": bucket,
        "feature_name": feature_name,
        "expected": True,
        "coverage_class": _coverage_class(bucket),
        "critical_bucket": bucket in CRITICAL_BUCKETS,
        "review_bucket": bucket in REVIEW_BUCKETS,
        "decision_blocking_bucket": bucket in DECISION_BLOCKING_BUCKETS,
        "feature_data_status": data_status,
        "source_status": truth.source_status,
        "source_status_reason": truth.warning_reason,
        "projection_source_status": (
            normalized.get("projection_source_status", "") if bucket == "projections" else ""
        ),
        "raw_value": normalized_score,
        "normalized_value": normalized_score,
        "imputed_flag": truth.imputed_flag,
        "neutral_default_value": truth.neutral_default_value,
        "coverage_credit": _coverage_credit(data_status),
        "normalized_score": normalized_score if data_status != "missing" else "",
        "source_bucket": bucket,
        "source_key": "stats_first_public_snapshot",
        "source_name": "Stats-first nflverse public source snapshot",
        "source_type": "stats_first_public",
        "source_family": "nflverse_stats_first",
        "source_date": normalized.get("computed_at", ""),
        "source_confidence": "verified" if data_status == "real" else "estimated",
        "source_reliability": normalized.get("confidence", ""),
        "is_missing": data_status == "missing",
        "missing_reason": "" if data_status != "missing" else f"missing_{feature_name}",
        "is_user_override": False,
        "scoring_status": "stats_first_active",
        "is_core_feature": bucket in CRITICAL_BUCKETS,
        "source_file": str(source_root / STATS_FIRST_SOURCE_COVERAGE_FILE),
    }


def _stats_first_bucket_row(
    player: dict[str, str],
    bucket: str,
    feature_row: dict[str, object],
    acceptance_row: dict[str, str],
) -> dict[str, object]:
    coverage_pct = min(100.0, 100.0 * float(feature_row["coverage_credit"]))
    penalty = BUCKET_CONFIDENCE_PENALTY[bucket] * (1.0 - (coverage_pct / 100.0))
    if coverage_pct >= 90:
        status = "ready"
    elif coverage_pct >= 50:
        status = "review"
    else:
        status = "missing"
    acceptance_status = _gap_acceptance_status(bucket, coverage_pct, acceptance_row)
    missing_features = (
        "" if coverage_pct > 0 else str(feature_row["feature_name"])
    )
    imputed_features = (
        str(feature_row["feature_name"])
        if feature_row["feature_data_status"] == "estimated_or_proxy"
        else ""
    )
    real_features = (
        str(feature_row["feature_name"])
        if feature_row["feature_data_status"] == "real"
        else ""
    )
    source_gap_scope = _source_gap_scope(
        player=player,
        bucket=bucket,
        coverage_pct=coverage_pct,
        acceptance_status=acceptance_status,
    )
    return {
        "player_id": player.get("player_id", ""),
        "player": player.get("player_name", ""),
        "position": player.get("position", ""),
        "team": player.get("team_name", ""),
        "bucket": bucket,
        "coverage_class": _coverage_class(bucket),
        "critical_bucket": bucket in CRITICAL_BUCKETS,
        "review_bucket": bucket in REVIEW_BUCKETS,
        "decision_blocking_bucket": bucket in DECISION_BLOCKING_BUCKETS,
        "bucket_status": status,
        "coverage_pct": round(coverage_pct, 2),
        "confidence_penalty": round(penalty, 2),
        "decision_effect": _decision_effect(bucket, coverage_pct, acceptance_status),
        "source_gap_scope": source_gap_scope,
        "source_gap_summary": _source_gap_summary(source_gap_scope),
        "gap_acceptance_status": acceptance_status,
        "gap_acceptance_reason": acceptance_row.get("accepted_reason", ""),
        "confidence_penalty_retained": acceptance_row.get(
            "confidence_penalty_retained", ""
        ),
        "gap_review_owner": acceptance_row.get("reviewed_by", ""),
        "gap_reviewed_at": acceptance_row.get("reviewed_at", ""),
        "next_action": _bucket_next_action(bucket, coverage_pct, acceptance_status),
        "expected_features": str(feature_row["feature_name"]),
        "real_features": real_features,
        "imputed_features": imputed_features,
        "missing_features": missing_features,
        "real_feature_count": 1 if real_features else 0,
        "imputed_feature_count": 1 if imputed_features else 0,
        "missing_feature_count": 1 if missing_features else 0,
    }


def _stats_first_player_row(
    player: dict[str, str],
    normalized: dict[str, str],
    bucket_rows: list[dict[str, object]],
) -> dict[str, object]:
    weighted_possible = sum(BUCKET_CONFIDENCE_PENALTY[row["bucket"]] for row in bucket_rows)
    weighted_covered = sum(
        BUCKET_CONFIDENCE_PENALTY[row["bucket"]] * float(row["coverage_pct"]) / 100.0
        for row in bucket_rows
    )
    coverage_pct = 100.0 if weighted_possible <= 0 else 100.0 * weighted_covered / weighted_possible
    penalty = sum(float(row["confidence_penalty"]) for row in bucket_rows)
    model_confidence = _safe_float(normalized.get("confidence"), 0.0)
    adjusted_confidence = max(0.0, model_confidence - penalty)
    missing_critical = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "critical" and int(row["missing_feature_count"]) > 0
    ]
    critical_review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "critical"
        and int(row["missing_feature_count"]) == 0
        and float(row["coverage_pct"]) < 75
    ]
    review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "review" and float(row["coverage_pct"]) < 75
    ]
    unaccepted_review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "review"
        and float(row["coverage_pct"]) < 75
        and row["gap_acceptance_status"] != "accepted"
    ]
    accepted_review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "review"
        and float(row["coverage_pct"]) < 75
        and row["gap_acceptance_status"] == "accepted"
    ]
    missing_blocking = [
        str(row["bucket"])
        for row in bucket_rows
        if row["decision_blocking_bucket"] and int(row["missing_feature_count"]) > 0
    ]
    if missing_blocking:
        status = "blocked_critical_coverage"
    elif critical_review_gaps or unaccepted_review_gaps:
        status = "review_coverage"
    elif accepted_review_gaps or adjusted_confidence < 75:
        status = "ready_with_confidence_drag"
    else:
        status = "ready"
    source_gap_scopes = _source_gap_scopes(bucket_rows)
    return {
        "player_id": player.get("player_id", ""),
        "player": player.get("player_name", ""),
        "position": player.get("position", ""),
        "team": player.get("team_name", ""),
        "coverage_status": status,
        "coverage_pct": round(coverage_pct, 2),
        "model_confidence": round(model_confidence, 2),
        "coverage_confidence_penalty": round(penalty, 2),
        "coverage_adjusted_confidence": round(adjusted_confidence, 2),
        "missing_critical_inputs": "|".join(missing_critical),
        "missing_critical_count": len(missing_critical),
        "critical_review_inputs": "|".join(critical_review_gaps),
        "critical_review_count": len(critical_review_gaps),
        "review_gap_inputs": "|".join(review_gaps),
        "review_gap_count": len(review_gaps),
        "unaccepted_review_gap_inputs": "|".join(unaccepted_review_gaps),
        "unaccepted_review_gap_count": len(unaccepted_review_gaps),
        "accepted_review_gap_inputs": "|".join(accepted_review_gaps),
        "accepted_review_gap_count": len(accepted_review_gaps),
        "source_gap_scopes": "|".join(source_gap_scopes),
        "source_gap_summary": _player_source_gap_summary(source_gap_scopes),
        "missing_bucket_count": sum(1 for row in bucket_rows if row["bucket_status"] == "missing"),
        "imputed_bucket_count": sum(
            1 for row in bucket_rows if int(row["imputed_feature_count"]) > 0
        ),
        "real_bucket_count": sum(1 for row in bucket_rows if row["bucket_status"] == "ready"),
        "high_value_score": round(_safe_float(normalized.get("private_stat_value"), 0.0), 2),
        "warning_status": "ready" if not normalized.get("warnings") else "review",
        "warning_reasons": normalized.get("warnings", ""),
        "warning_summary": warning_summary(
            normalized.get("warnings", ""),
            "ready" if not normalized.get("warnings") else "review",
        ),
    }


def _stats_first_bucket_status(
    coverage: dict[str, str],
    bucket: str,
    player: dict[str, str],
    normalized: dict[str, str],
) -> str:
    warnings = {
        item.strip()
        for item in str(normalized.get("warnings") or "").split("|")
        if item.strip()
    }
    if bucket == "identity":
        return "ready"
    if bucket == "league rank":
        return "ready" if player.get("league_rank") else "review_missing"
    if bucket == "role/usage":
        if _route_role_is_unavailable_or_proxy(normalized):
            return "review"
        if "missing_role_usage_features" in warnings:
            return "review_missing"
        if "missing_participation_proxy" in warnings or "missing_snap_counts" in warnings:
            return "review"
    if bucket == "injury":
        if "missing_injury_features" in warnings:
            return "review_missing"
        if "no_injury_report_rows" in warnings or "no_activity_rows" in warnings:
            return "review"
    if bucket == "projections":
        projection_status = str(normalized.get("projection_source_status") or "")
        if projection_status in {"local_baseline_projection", "disabled_projection"}:
            return "review"
        if projection_status == "missing_projection":
            return "review_missing"
    if (
        bucket == "production"
        and _safe_float(normalized.get("young_nfl_bridge_weight"), 0.0) > 0
    ):
        raw = str(coverage.get("production") or "")
        if raw != "ready":
            return "review"
    if bucket == "production" and _stats_first_production_is_stale(player, normalized):
        raw = str(coverage.get("production") or "")
        return "review" if raw == "ready" else raw or "review_missing"
    key = {
        "role/usage": "role_usage",
        "projections": "projection",
        "age/bio": "age_bio",
        "market": "market_liquidity",
    }.get(bucket, bucket)
    return str(coverage.get(key) or "review_missing")


def _stats_first_production_is_stale(
    player: dict[str, str],
    normalized: dict[str, str],
) -> bool:
    decision_season = _safe_float(player.get("season"), 0.0)
    source_season = _safe_float(normalized.get("season"), 0.0)
    if decision_season <= 0 or source_season <= 0:
        return False
    expected_recent_completed_season = decision_season - 1
    return source_season < expected_recent_completed_season


def _stats_first_feature_data_status(raw_status: str) -> str:
    normalized = raw_status.strip().lower()
    if normalized == "ready":
        return "real"
    if normalized == "review":
        return "estimated_or_proxy"
    return "missing"


def _route_role_is_unavailable_or_proxy(normalized: dict[str, str]) -> bool:
    position = str(normalized.get("position") or "").upper()
    if position not in {"WR", "TE"}:
        return False
    route_role = _safe_float(normalized.get("route_role"), 50.0)
    warnings = {
        item.strip()
        for item in str(normalized.get("warnings") or "").split("|")
        if item.strip()
    }
    return (
        route_role == 50.0
        or "missing_participation_proxy" in warnings
        or "missing_role_usage_features" in warnings
        or "route_data_unavailable_free_public" in warnings
    )


def _stats_first_feature_name(bucket: str, normalized: dict[str, str] | None = None) -> str:
    if (
        bucket == "production"
        and normalized is not None
        and _safe_float(normalized.get("young_nfl_bridge_weight"), 0.0) > 0
    ):
        return "young_nfl_bridge_production_prior"
    return {
        "production": "stats_first_production",
        "projections": "lve_projection_value",
        "role/usage": "stats_first_role_usage",
        "injury": "injury_durability",
        "age/bio": "age_curve",
        "identity": IDENTITY_FEATURE,
        "market": "market_liquidity",
        "league rank": LEAGUE_RANK_FEATURE,
    }[bucket]


def _stats_first_normalized_score(
    normalized: dict[str, str],
    bucket: str,
) -> object:
    keys = {
        "production": "weighted_recent_lve_ppg_score",
        "projections": "lve_projection_value",
        "role/usage": "role_security",
        "injury": "injury_durability",
        "age/bio": "age_curve",
        "market": "market_liquidity",
        "identity": "confidence",
        "league rank": "",
    }
    key = keys[bucket]
    return normalized.get(key, "") if key else ""


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _safe_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _player_coverage_rows(
    player: VeteranPlayerRow,
    registry: dict[str, VeteranFeatureDefinition],
    feature_lookup: dict[tuple[str, str], VeteranFeatureScore],
    source_lookup: dict[str, VeteranSourceRow],
    identity_lookup: dict[str, dict[str, object]],
    acceptance_lookup: dict[tuple[str, str], dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    feature_rows: list[dict[str, object]] = []
    bucket_rows: list[dict[str, object]] = []
    for bucket in BUCKETS:
        bucket_feature_rows = [
            _feature_coverage_row(
                player,
                bucket,
                feature_name,
                registry.get(feature_name),
                feature_lookup.get((player.player_id, feature_name)),
                source_lookup,
            )
            for feature_name in _expected_features(player.position, bucket, registry)
        ]
        if bucket == "identity":
            bucket_feature_rows = [
                _identity_feature_row(
                    player,
                    identity_lookup.get(player.player_id)
                    or identity_lookup.get(_player_key(player.player_name, player.position), {})
                    or {},
                )
            ]
        if bucket == "league rank":
            bucket_feature_rows = [_league_rank_feature_row(player)]
        feature_rows.extend(bucket_feature_rows)
        bucket_rows.append(
            _bucket_summary_row(
                player,
                bucket,
                bucket_feature_rows,
                _acceptance_row(acceptance_lookup, player.player_id, bucket),
            )
        )
    return feature_rows, bucket_rows


def _feature_coverage_row(
    player: VeteranPlayerRow,
    bucket: str,
    feature_name: str,
    definition: VeteranFeatureDefinition | None,
    feature: VeteranFeatureScore | None,
    source_lookup: dict[str, VeteranSourceRow],
) -> dict[str, object]:
    source = source_lookup.get(feature.source_key) if feature else None
    source_bucket = _source_bucket(feature_name, definition, feature, source)
    data_status = _feature_data_status(feature, source, bucket, source_bucket)
    normalized_score: object = ""
    if feature and data_status in {"real", "manual_override", "estimated_or_proxy"}:
        normalized_score = "" if feature.normalized_score is None else feature.normalized_score
    return {
        "player_id": player.player_id,
        "player": player.player_name,
        "position": player.position,
        "team": player.team_name,
        "bucket": bucket,
        "feature_name": feature_name,
        "expected": True,
        "coverage_class": _coverage_class(bucket),
        "critical_bucket": bucket in CRITICAL_BUCKETS,
        "review_bucket": bucket in REVIEW_BUCKETS,
        "decision_blocking_bucket": bucket in DECISION_BLOCKING_BUCKETS,
        "feature_data_status": data_status,
        "coverage_credit": _coverage_credit(data_status),
        "normalized_score": normalized_score,
        "source_bucket": source_bucket,
        "source_key": feature.source_key if feature else "",
        "source_name": source.source_name if source else "",
        "source_type": source.source_type if source else "",
        "source_family": source.source_family if source else "",
        "source_date": source.source_date if source else "",
        "source_confidence": feature.source_confidence if feature else "",
        "source_reliability": source.reliability_score if source else "",
        "is_missing": True if not feature else feature.is_missing,
        "missing_reason": _missing_reason(feature, data_status),
        "is_user_override": bool(feature.is_user_override) if feature else False,
        "scoring_status": definition.scoring_status if definition else "",
        "is_core_feature": bool(definition.is_core) if definition else False,
    }


def _identity_feature_row(
    player: VeteranPlayerRow,
    identity_row: dict[str, object],
) -> dict[str, object]:
    audit_status = str(identity_row.get("audit_status") or "blocked")
    ranking_status = str(identity_row.get("ranking_trust_status") or audit_status)
    if ranking_status in {"ready"}:
        data_status = "real"
        credit = 1.0
    elif ranking_status in {"review"}:
        data_status = "estimated_or_proxy"
        credit = 0.5
    else:
        data_status = "missing"
        credit = 0.0
    return {
        "player_id": player.player_id,
        "player": player.player_name,
        "position": player.position,
        "team": player.team_name,
        "bucket": "identity",
        "feature_name": IDENTITY_FEATURE,
        "expected": True,
        "coverage_class": "critical",
        "critical_bucket": True,
        "review_bucket": False,
        "decision_blocking_bucket": True,
        "feature_data_status": data_status,
        "coverage_credit": credit,
        "normalized_score": identity_row.get("identity_confidence", ""),
        "source_bucket": "identity",
        "source_key": "identity_audit",
        "source_name": "Sleeper/nflverse identity bridge",
        "source_type": "identity",
        "source_family": "identity_bridge",
        "source_date": "",
        "source_confidence": identity_row.get("match_method", ""),
        "source_reliability": identity_row.get("identity_confidence", ""),
        "is_missing": data_status == "missing",
        "missing_reason": identity_row.get("manual_review_note", "")
        or "missing_or_untrusted_identity_match",
        "is_user_override": False,
        "scoring_status": "trust_gate",
        "is_core_feature": True,
    }


def _league_rank_feature_row(player: VeteranPlayerRow) -> dict[str, object]:
    has_rank = player.league_rank is not None
    return {
        "player_id": player.player_id,
        "player": player.player_name,
        "position": player.position,
        "team": player.team_name,
        "bucket": "league rank",
        "feature_name": LEAGUE_RANK_FEATURE,
        "expected": True,
        "coverage_class": "governance",
        "critical_bucket": False,
        "review_bucket": False,
        "decision_blocking_bucket": False,
        "feature_data_status": "real" if has_rank else "missing",
        "coverage_credit": 1.0 if has_rank else 0.0,
        "normalized_score": player.league_rank if has_rank else "",
        "source_bucket": "league rank" if has_rank else "",
        "source_key": player.source_snapshot_id,
        "source_name": player.source_name,
        "source_type": "league_rank",
        "source_family": "league_rank_doc",
        "source_date": player.source_date,
        "source_confidence": player.data_quality_tier,
        "source_reliability": "",
        "is_missing": not has_rank,
        "missing_reason": "" if has_rank else "missing_league_rank",
        "is_user_override": False,
        "scoring_status": "governance_only",
        "is_core_feature": False,
    }


def _bucket_summary_row(
    player: VeteranPlayerRow,
    bucket: str,
    feature_rows: list[dict[str, object]],
    acceptance_row: dict[str, str],
) -> dict[str, object]:
    expected = max(1, len(feature_rows))
    credit = sum(float(row["coverage_credit"]) for row in feature_rows)
    coverage_pct = min(100.0, 100.0 * credit / expected)
    missing_features = [
        str(row["feature_name"])
        for row in feature_rows
        if float(row["coverage_credit"]) <= 0.0
    ]
    imputed_features = [
        str(row["feature_name"])
        for row in feature_rows
        if row["feature_data_status"] == "estimated_or_proxy"
    ]
    penalty = BUCKET_CONFIDENCE_PENALTY[bucket] * (1.0 - (coverage_pct / 100.0))
    if coverage_pct >= 90:
        status = "ready"
    elif coverage_pct >= 50:
        status = "review"
    else:
        status = "missing"
    acceptance_status = _gap_acceptance_status(bucket, coverage_pct, acceptance_row)
    source_gap_scope = _source_gap_scope(
        player={
            "team_name": player.team_name,
            "asset_lifecycle": getattr(player, "asset_lifecycle", ""),
        },
        bucket=bucket,
        coverage_pct=coverage_pct,
        acceptance_status=acceptance_status,
    )
    return {
        "player_id": player.player_id,
        "player": player.player_name,
        "position": player.position,
        "team": player.team_name,
        "bucket": bucket,
        "coverage_class": _coverage_class(bucket),
        "critical_bucket": bucket in CRITICAL_BUCKETS,
        "review_bucket": bucket in REVIEW_BUCKETS,
        "decision_blocking_bucket": bucket in DECISION_BLOCKING_BUCKETS,
        "bucket_status": status,
        "coverage_pct": round(coverage_pct, 2),
        "confidence_penalty": round(penalty, 2),
        "decision_effect": _decision_effect(bucket, coverage_pct, acceptance_status),
        "source_gap_scope": source_gap_scope,
        "source_gap_summary": _source_gap_summary(source_gap_scope),
        "gap_acceptance_status": acceptance_status,
        "gap_acceptance_reason": acceptance_row.get("accepted_reason", ""),
        "confidence_penalty_retained": acceptance_row.get(
            "confidence_penalty_retained", ""
        ),
        "gap_review_owner": acceptance_row.get("reviewed_by", ""),
        "gap_reviewed_at": acceptance_row.get("reviewed_at", ""),
        "next_action": _bucket_next_action(bucket, coverage_pct, acceptance_status),
        "expected_features": "|".join(str(row["feature_name"]) for row in feature_rows),
        "real_features": "|".join(
            str(row["feature_name"])
            for row in feature_rows
            if row["feature_data_status"] in {"real", "manual_override"}
        ),
        "imputed_features": "|".join(imputed_features),
        "missing_features": "|".join(missing_features),
        "real_feature_count": sum(
            1 for row in feature_rows if row["feature_data_status"] == "real"
        ),
        "imputed_feature_count": len(imputed_features),
        "missing_feature_count": len(missing_features),
    }


def _player_summary_row(
    player: VeteranPlayerRow,
    bucket_rows: list[dict[str, object]],
    score: object,
) -> dict[str, object]:
    weighted_possible = sum(BUCKET_CONFIDENCE_PENALTY[row["bucket"]] for row in bucket_rows)
    weighted_covered = sum(
        BUCKET_CONFIDENCE_PENALTY[row["bucket"]] * float(row["coverage_pct"]) / 100.0
        for row in bucket_rows
    )
    coverage_pct = 100.0 if weighted_possible <= 0 else 100.0 * weighted_covered / weighted_possible
    penalty = sum(float(row["confidence_penalty"]) for row in bucket_rows)
    model_confidence = float(getattr(score, "confidence_score", 0.0))
    adjusted_confidence = max(0.0, model_confidence - penalty)
    missing_critical = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "critical" and int(row["missing_feature_count"]) > 0
    ]
    critical_review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "critical"
        and int(row["missing_feature_count"]) == 0
        and float(row["coverage_pct"]) < 75
    ]
    review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "review" and float(row["coverage_pct"]) < 75
    ]
    unaccepted_review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "review"
        and float(row["coverage_pct"]) < 75
        and row["gap_acceptance_status"] != "accepted"
    ]
    accepted_review_gaps = [
        str(row["bucket"])
        for row in bucket_rows
        if row["coverage_class"] == "review"
        and float(row["coverage_pct"]) < 75
        and row["gap_acceptance_status"] == "accepted"
    ]
    missing_blocking = [
        str(row["bucket"])
        for row in bucket_rows
        if row["decision_blocking_bucket"] and int(row["missing_feature_count"]) > 0
    ]
    if missing_blocking:
        status = "blocked_critical_coverage"
    elif critical_review_gaps or unaccepted_review_gaps:
        status = "review_coverage"
    elif accepted_review_gaps or adjusted_confidence < 75:
        status = "ready_with_confidence_drag"
    else:
        status = "ready"
    source_gap_scopes = _source_gap_scopes(bucket_rows)
    high_value_score = max(
        float(getattr(score, "keeper_score", 0.0)),
        float(getattr(score, "veteran_base_value", 0.0)),
        float(getattr(score, "trade_value", 0.0)),
    )
    return {
        "player_id": player.player_id,
        "player": player.player_name,
        "position": player.position,
        "team": player.team_name,
        "coverage_status": status,
        "coverage_pct": round(coverage_pct, 2),
        "model_confidence": round(model_confidence, 2),
        "coverage_confidence_penalty": round(penalty, 2),
        "coverage_adjusted_confidence": round(adjusted_confidence, 2),
        "missing_critical_inputs": "|".join(missing_critical),
        "missing_critical_count": len(missing_critical),
        "critical_review_inputs": "|".join(critical_review_gaps),
        "critical_review_count": len(critical_review_gaps),
        "review_gap_inputs": "|".join(review_gaps),
        "review_gap_count": len(review_gaps),
        "unaccepted_review_gap_inputs": "|".join(unaccepted_review_gaps),
        "unaccepted_review_gap_count": len(unaccepted_review_gaps),
        "accepted_review_gap_inputs": "|".join(accepted_review_gaps),
        "accepted_review_gap_count": len(accepted_review_gaps),
        "source_gap_scopes": "|".join(source_gap_scopes),
        "source_gap_summary": _player_source_gap_summary(source_gap_scopes),
        "missing_bucket_count": sum(1 for row in bucket_rows if row["bucket_status"] == "missing"),
        "imputed_bucket_count": sum(
            1 for row in bucket_rows if int(row["imputed_feature_count"]) > 0
        ),
        "real_bucket_count": sum(1 for row in bucket_rows if row["bucket_status"] == "ready"),
        "high_value_score": round(high_value_score, 2),
        "warning_status": getattr(score, "warning_status", ""),
        "warning_reasons": "|".join(getattr(score, "warning_reasons", ())),
        "warning_summary": warning_summary(
            "|".join(getattr(score, "warning_reasons", ())),
            getattr(score, "warning_status", ""),
        ),
    }


def _summary_rows(
    player_rows: list[dict[str, object]],
    bucket_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for bucket in BUCKETS:
        rows = [row for row in bucket_rows if row["bucket"] == bucket]
        if not rows:
            continue
        output.append(
            {
                "summary_type": "bucket",
                "name": bucket,
                "coverage_class": _coverage_class(bucket),
                "players": len(rows),
                "avg_coverage_pct": round(
                    sum(float(row["coverage_pct"]) for row in rows) / len(rows),
                    2,
                ),
                "missing": sum(1 for row in rows if row["bucket_status"] == "missing"),
                "review": sum(1 for row in rows if row["bucket_status"] == "review"),
                "ready": sum(1 for row in rows if row["bucket_status"] == "ready"),
                "confidence_penalty": round(
                    sum(float(row["confidence_penalty"]) for row in rows),
                    2,
                ),
                "review_needed": sum(
                    1 for row in rows if row["gap_acceptance_status"] == "review_needed"
                ),
                "accepted": sum(
                    1 for row in rows if row["gap_acceptance_status"] == "accepted"
                ),
                "source_gap_scope": "",
                "source_gap_summary": "",
            }
        )
    for status in sorted({str(row["coverage_status"]) for row in player_rows}):
        rows = [row for row in player_rows if row["coverage_status"] == status]
        output.append(
            {
                "summary_type": "player_status",
                "name": status,
                "coverage_class": "",
                "players": len(rows),
                "avg_coverage_pct": round(
                    sum(float(row["coverage_pct"]) for row in rows) / len(rows),
                    2,
                ),
                "missing": sum(int(row["missing_bucket_count"]) for row in rows),
                "review": "",
                "ready": "",
                "confidence_penalty": round(
                    sum(float(row["coverage_confidence_penalty"]) for row in rows),
                    2,
                ),
                "review_needed": sum(
                    int(row.get("unaccepted_review_gap_count", 0)) for row in rows
                ),
                "accepted": sum(
                    int(row.get("accepted_review_gap_count", 0)) for row in rows
                ),
                "source_gap_scope": "",
                "source_gap_summary": "",
            }
        )
    for scope in (
        "roster-critical",
        "draft-critical",
        "final-money-critical",
        "optional accepted",
        "future paid-data candidate",
        "none",
    ):
        rows = [row for row in bucket_rows if row.get("source_gap_scope") == scope]
        if not rows:
            continue
        output.append(
            {
                "summary_type": "source_gap_scope",
                "name": scope,
                "coverage_class": "",
                "players": len({str(row["player_id"]) for row in rows}),
                "avg_coverage_pct": round(
                    sum(float(row["coverage_pct"]) for row in rows) / len(rows),
                    2,
                ),
                "missing": sum(1 for row in rows if row["bucket_status"] == "missing"),
                "review": sum(1 for row in rows if row["bucket_status"] == "review"),
                "ready": sum(1 for row in rows if row["bucket_status"] == "ready"),
                "confidence_penalty": round(
                    sum(float(row["confidence_penalty"]) for row in rows),
                    2,
                ),
                "review_needed": sum(
                    1 for row in rows if row["gap_acceptance_status"] == "review_needed"
                ),
                "accepted": sum(
                    1 for row in rows if row["gap_acceptance_status"] == "accepted"
                ),
                "source_gap_scope": scope,
                "source_gap_summary": _source_gap_summary(scope),
            }
        )
    return output


def _expected_features(
    position: str,
    bucket: str,
    registry: dict[str, VeteranFeatureDefinition],
) -> tuple[str, ...]:
    expected = EXPECTED_BUCKET_FEATURES.get(position, {}).get(bucket, ())
    if bucket == "league rank":
        return expected
    if bucket == "identity":
        return (IDENTITY_FEATURE,)
    supported = tuple(feature for feature in expected if feature in registry)
    return supported or expected


def _coverage_class(bucket: str) -> str:
    if bucket in CRITICAL_BUCKETS:
        return "critical"
    if bucket in REVIEW_BUCKETS:
        return "review"
    if bucket in GOVERNANCE_BUCKETS:
        return "governance"
    return "review"


def _gap_acceptance_status(
    bucket: str,
    coverage_pct: float,
    acceptance_row: dict[str, str],
) -> str:
    if coverage_pct >= 75:
        return "not_needed"
    if bucket in CRITICAL_BUCKETS:
        return "not_allowed"
    if bucket in REVIEW_BUCKETS:
        status = str(acceptance_row.get("review_status") or "").lower()
        return "accepted" if status == "accepted" else "review_needed"
    return "not_needed"


def _decision_effect(
    bucket: str,
    coverage_pct: float,
    acceptance_status: str,
) -> str:
    if coverage_pct >= 75:
        return "no_gap"
    if bucket in CRITICAL_BUCKETS:
        return "blocks_decision_trust"
    if bucket in REVIEW_BUCKETS:
        if acceptance_status == "accepted":
            return "confidence_penalty_accepted"
        return "confidence_penalty_review_needed"
    return "governance_context_only"


def _bucket_next_action(
    bucket: str,
    coverage_pct: float,
    acceptance_status: str,
) -> str:
    if coverage_pct >= 75:
        return "No action needed."
    if bucket in CRITICAL_BUCKETS:
        return "Fill this critical source before trusting decisions."
    if acceptance_status == "accepted":
        return "Gap accepted for now; confidence penalty remains visible."
    if bucket in REVIEW_BUCKETS:
        return "Review source gap, then fill it or add an audited acceptance row."
    return "Use for context only."


def _source_gap_scope(
    *,
    player: dict[str, object],
    bucket: str,
    coverage_pct: float,
    acceptance_status: str,
) -> str:
    if coverage_pct >= 75:
        return "none"
    if acceptance_status == "accepted":
        return "optional accepted"
    if bucket in REVIEW_BUCKETS:
        return "future paid-data candidate"
    if bucket in CRITICAL_BUCKETS:
        if _is_niners_roster_player(player):
            return "roster-critical"
        if _is_draft_pool_player(player):
            return "draft-critical"
        return "final-money-critical"
    return "future paid-data candidate"


def _source_gap_summary(scope: str) -> str:
    return {
        "none": "safe for roster review",
        "roster-critical": "blocks roster review until source evidence is fixed",
        "draft-critical": "not enough for draft",
        "final-money-critical": "blocks final-money confidence",
        "optional accepted": "accepted optional gap; confidence penalty retained",
        "future paid-data candidate": "needs paid/free source upgrade",
    }.get(scope, "needs source review")


def _source_gap_scopes(bucket_rows: list[dict[str, object]]) -> list[str]:
    scopes = {
        str(row.get("source_gap_scope") or "")
        for row in bucket_rows
        if str(row.get("source_gap_scope") or "") not in {"", "none"}
    }
    return sorted(scopes)


def _player_source_gap_summary(scopes: list[str]) -> str:
    if not scopes:
        return "safe for roster review"
    if "roster-critical" in scopes:
        return "blocks roster review until source evidence is fixed"
    if "draft-critical" in scopes:
        return "not enough for draft"
    if "final-money-critical" in scopes:
        return "blocks final-money confidence"
    if "future paid-data candidate" in scopes:
        return "needs paid/free source upgrade"
    if "optional accepted" in scopes:
        return "accepted optional gap; confidence penalty retained"
    return "needs source review"


def _is_niners_roster_player(player: dict[str, object]) -> bool:
    team = str(player.get("team_name") or player.get("team") or "").strip().lower()
    return team == "niners"


def _is_draft_pool_player(player: dict[str, object]) -> bool:
    team = str(player.get("team_name") or player.get("team") or "").strip().lower()
    lifecycle = str(player.get("asset_lifecycle") or "").strip().lower()
    return (
        team in {"", "free agent", "free_agent", "released veteran", "released_veteran"}
        or lifecycle in {"incoming_rookie", "free_agent", "released_veteran", "manual"}
    )


def _identity_lookup(
    data_pack_path: str | Path,
    source_root: Path,
) -> dict[str, dict[str, object]]:
    report = build_identity_audit(data_pack_path, source_root=source_root)
    output: dict[str, dict[str, object]] = {}
    for row in report.rows:
        player_id = str(row.get("player_id") or "")
        if player_id:
            output[player_id] = row
        key = _player_key(row.get("player", ""), row.get("position", ""))
        if key:
            output[key] = row
    return output


def _player_key(player: object, position: object) -> str:
    name = "".join(character.lower() for character in str(player) if character.isalnum())
    if not name or not position:
        return ""
    return f"name::{name}::{position}"


def _acceptance_row(
    lookup: dict[tuple[str, str], dict[str, object]],
    player_id: str,
    bucket: str,
) -> dict[str, object]:
    return lookup.get((player_id, bucket), lookup.get(("", bucket), {}))


def _registry_by_position(
    registry: tuple[VeteranFeatureDefinition, ...],
) -> dict[str, dict[str, VeteranFeatureDefinition]]:
    output: dict[str, dict[str, VeteranFeatureDefinition]] = {}
    for definition in registry:
        if definition.parent_component == "display_only":
            continue
        if definition.scoring_status not in {"active_v1", "future_candidate"}:
            continue
        output.setdefault(definition.position, {})[definition.feature_name] = definition
    return output


def _feature_data_status(
    feature: VeteranFeatureScore | None,
    source: VeteranSourceRow | None,
    bucket: str,
    source_bucket: str,
) -> str:
    if feature is None:
        return "missing"
    if feature.is_missing or feature.normalized_score is None:
        return "missing"
    if source_bucket != bucket:
        return "covered_elsewhere"
    if feature.is_user_override:
        return "manual_override"
    if feature.source_confidence in {"estimated", "unknown"}:
        return "estimated_or_proxy"
    if source and source.reliability_score < 55:
        return "estimated_or_proxy"
    return "real"


def _source_bucket(
    feature_name: str,
    definition: VeteranFeatureDefinition | None,
    feature: VeteranFeatureScore | None,
    source: VeteranSourceRow | None,
) -> str:
    if feature_name in PROJECTION_FEATURES:
        return "projections"
    if feature_name in PRODUCTION_FEATURES:
        return "production"
    if feature_name in ROLE_USAGE_FEATURES:
        return "role/usage"
    source_text = " ".join(
        str(value).lower()
        for value in (
            feature_name,
            feature.source_key if feature else "",
            source.source_name if source else "",
            source.source_type if source else "",
            source.source_family if source else "",
            source.source_domain if source else "",
            definition.requires_source_type if definition else "",
        )
    )
    if "league_rank" in source_text or "league rank" in source_text:
        return "league rank"
    if "market" in source_text:
        return "market"
    if "injury" in source_text or "durability" in feature_name:
        return "injury"
    if feature_name in {"age_curve", "age_curve_archetype"} or "metadata" in source_text:
        return "age/bio"
    if any(marker in source_text for marker in ("role", "snap", "route", "target", "depth")):
        return "role/usage"
    if any(marker in source_text for marker in ("player_stats", "weekly", "first_down", "scoring")):
        return "production"
    if "projection" in source_text:
        return "projections"
    return "projections"


def _coverage_credit(data_status: str) -> float:
    if data_status == "real":
        return 1.0
    if data_status == "manual_override":
        return 0.8
    if data_status == "estimated_or_proxy":
        return 0.5
    return 0.0


def _missing_reason(
    feature: VeteranFeatureScore | None,
    data_status: str,
) -> str:
    if data_status == "covered_elsewhere":
        return "feature_source_belongs_to_another_bucket"
    if feature is None:
        return "missing_feature_score"
    if feature.is_missing:
        return feature.missing_reason or "feature_marked_missing"
    if feature.normalized_score is None:
        return "missing_normalized_score"
    return ""


def _status_priority(status: str) -> int:
    return {
        "blocked_critical_coverage": 0,
        "blocked_coverage_review": 0,
        "missing": 1,
        "review_coverage": 2,
        "review": 3,
        "ready_with_confidence_drag": 4,
        "ready": 4,
    }.get(status, 9)

