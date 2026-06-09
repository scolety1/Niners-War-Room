from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.command_board_service import ACTIVE_STATS_FIRST_MODEL_DIR
from src.services.confidence_rebuild_service import (
    BLOCKED_ACTION,
    LIMITED_ACTION,
    REVIEW_ACTION,
    USABLE_ACTION,
    build_confidence_rebuild_report,
)
from src.services.source_coverage_audit_service import build_source_coverage_audit

CONFIDENCE_TIER_ORDER = {
    "blocked": 0,
    "review": 1,
    "limited": 2,
    "usable": 3,
}


@dataclass(frozen=True)
class ConfidenceCalibrationAuditReport:
    rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    explanation_rows: list[dict[str, object]]
    issues: list[str]
    source_root: str


def build_confidence_calibration_audit(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> ConfidenceCalibrationAuditReport:
    source_root = Path(veteran_model_dir) if veteran_model_dir else ACTIVE_STATS_FIRST_MODEL_DIR
    confidence = build_confidence_rebuild_report(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    coverage = build_source_coverage_audit(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    bucket_lookup = _coverage_bucket_lookup(coverage.bucket_rows)
    visible_confidence_lookup = _visible_stats_first_output_lookup(source_root)
    rows = [
        _audit_row(
            _row_with_visible_confidence(row, visible_confidence_lookup),
            bucket_lookup.get(str(row["player_id"]), {}),
        )
        for row in confidence.rows
    ]
    rows.sort(
        key=lambda row: (
            0 if row["mismatch_flag"] else 1,
            -float(row["confidence_tier_gap"]),
            str(row["player"]).lower(),
        )
    )
    return ConfidenceCalibrationAuditReport(
        rows=rows,
        summary_rows=_summary_rows(rows),
        explanation_rows=confidence.explanation_rows,
        issues=[*confidence.issues, *coverage.issues],
        source_root=str(source_root),
    )


def _audit_row(
    row: dict[str, object],
    bucket_rows: dict[str, dict[str, object]],
) -> dict[str, object]:
    actual_tier = _tier_for_score(float(row["current_model_confidence"]))
    expected_tier = _expected_tier(row)
    tier_gap = CONFIDENCE_TIER_ORDER[actual_tier] - CONFIDENCE_TIER_ORDER[expected_tier]
    mismatch = _is_mismatch(
        actual_tier,
        expected_tier,
        tier_gap,
        float(row["current_model_confidence"]),
        float(row["rebuilt_confidence_score"]),
    )
    return {
        "player_id": row["player_id"],
        "player": row["player"],
        "position": row["position"],
        "team": row.get("team", ""),
        "confidence": row["current_model_confidence"],
        "rebuilt_confidence": row["rebuilt_confidence_score"],
        "expected_confidence_tier": expected_tier,
        "actual_confidence_tier": actual_tier,
        "confidence_tier_gap": tier_gap,
        "mismatch_flag": mismatch,
        "mismatch_reason": _mismatch_reason(row, actual_tier, expected_tier, mismatch),
        "production_coverage": _bucket_status(bucket_rows, "production"),
        "role_usage_coverage": _bucket_status(bucket_rows, "role/usage"),
        "projection_status": _projection_status(bucket_rows),
        "injury_status": _bucket_status(bucket_rows, "injury"),
        "age_bio_source": _bucket_status(bucket_rows, "age/bio"),
        "identity_confidence": row.get("identity_confidence", ""),
        "identity_status": row.get("identity_status", ""),
        "outlier_status": _outlier_status(row),
        "missing_proxy_buckets": _missing_proxy_buckets(row, bucket_rows),
        "action_certainty": row["action_certainty"],
        "certainty_reason": row["certainty_reason"],
        "confidence_warning_reasons": row["confidence_warning_reasons"],
    }


def _row_with_visible_confidence(
    row: dict[str, object],
    visible_lookup: dict[str, dict[str, str]],
) -> dict[str, object]:
    player_id = str(row.get("player_id") or "")
    key = _player_key(row.get("player", ""), row.get("position", ""))
    visible = visible_lookup.get(player_id) or visible_lookup.get(key)
    if not visible:
        return row
    output = dict(row)
    output["current_model_confidence"] = _float(
        visible.get("confidence_score"),
        _float(row.get("current_model_confidence")),
    )
    output["team"] = visible.get("team", row.get("team", ""))
    return output


def _visible_stats_first_output_lookup(source_root: Path) -> dict[str, dict[str, str]]:
    path = source_root / "stats_first_veteran_model_preview_outputs.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if player_id and player_id not in lookup:
            lookup[player_id] = row
        key = _player_key(row.get("player_name", ""), row.get("position", ""))
        if key and key not in lookup:
            lookup[key] = row
    return lookup


def _expected_tier(row: dict[str, object]) -> str:
    action = str(row["action_certainty"])
    if action == BLOCKED_ACTION:
        return "blocked"
    if action == REVIEW_ACTION:
        return "review"
    if action == LIMITED_ACTION:
        return "limited"
    if action == USABLE_ACTION:
        return _tier_for_score(float(row["rebuilt_confidence_score"]))
    return _tier_for_score(float(row["rebuilt_confidence_score"]))


def _tier_for_score(score: float) -> str:
    if score < 40:
        return "blocked"
    if score < 65:
        return "review"
    if score < 78:
        return "limited"
    return "usable"


def _is_mismatch(
    actual_tier: str,
    expected_tier: str,
    tier_gap: int,
    current_confidence: float,
    rebuilt_confidence: float,
) -> bool:
    if tier_gap <= 0:
        return False
    if actual_tier == "usable" and expected_tier in {"blocked", "review"}:
        return True
    return tier_gap >= 1 and current_confidence - rebuilt_confidence >= 8.0


def _mismatch_reason(
    row: dict[str, object],
    actual_tier: str,
    expected_tier: str,
    mismatch: bool,
) -> str:
    if not mismatch:
        return "Confidence tier matches source-quality audit."
    if actual_tier == "usable" and expected_tier != "usable":
        return (
            "Visible confidence claims usable certainty while source/identity/outlier "
            f"audit expects {expected_tier}."
        )
    return (
        "Visible confidence is materially higher than rebuilt source-quality confidence."
    )


def _coverage_bucket_lookup(
    bucket_rows: list[dict[str, object]],
) -> dict[str, dict[str, dict[str, object]]]:
    lookup: dict[str, dict[str, dict[str, object]]] = {}
    for row in bucket_rows:
        player_id = str(row.get("player_id") or "")
        bucket = str(row.get("bucket") or "")
        if player_id and bucket:
            lookup.setdefault(player_id, {})[bucket] = row
    return lookup


def _player_key(player: object, position: object) -> str:
    parts = [
        part.lower().strip(".,'")
        for part in str(player).split()
        if part.strip(".,'")
    ]
    if parts and parts[-1] in {"jr", "sr", "ii", "iii", "iv", "v"}:
        parts = parts[:-1]
    name = "".join(character for part in parts for character in part if character.isalnum())
    if not name or not position:
        return ""
    return f"name::{name}::{position}"


def _bucket_status(bucket_rows: dict[str, dict[str, object]], bucket: str) -> str:
    row = bucket_rows.get(bucket, {})
    status = str(row.get("bucket_status") or "")
    data_status = str(row.get("feature_data_status") or "")
    if status and data_status:
        return f"{status}:{data_status}"
    return status or data_status or "not_available"


def _projection_status(bucket_rows: dict[str, dict[str, object]]) -> str:
    row = bucket_rows.get("projections", {})
    status = str(row.get("projection_source_status") or "")
    return status or _bucket_status(bucket_rows, "projections")


def _outlier_status(row: dict[str, object]) -> str:
    probably_broken = int(float(row.get("probably_broken_outliers") or 0))
    count = int(float(row.get("outlier_count") or 0))
    if probably_broken:
        return f"review_required:{probably_broken}"
    if count:
        return f"lower_severity:{count}"
    return "none"


def _missing_proxy_buckets(
    row: dict[str, object],
    bucket_rows: dict[str, dict[str, object]],
) -> str:
    buckets: set[str] = set()
    for field in (
        "missing_critical_inputs",
        "critical_review_inputs",
        "review_gap_inputs",
        "accepted_review_gap_inputs",
        "unaccepted_review_gap_inputs",
    ):
        buckets.update(_split(row.get(field, "")))
    for bucket, bucket_row in bucket_rows.items():
        if str(bucket_row.get("feature_data_status") or "") == "estimated_or_proxy":
            buckets.add(bucket)
    return "|".join(sorted(buckets))


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = [
        {
            "metric": "players",
            "value": len(rows),
            "detail": "Players included in confidence calibration audit.",
        },
        {
            "metric": "mismatch_players",
            "value": sum(1 for row in rows if row["mismatch_flag"]),
            "detail": "Visible confidence tier is higher than source-quality audit supports.",
        },
    ]
    for tier in ("blocked", "review", "limited", "usable"):
        output.append(
            {
                "metric": f"expected_{tier}",
                "value": sum(1 for row in rows if row["expected_confidence_tier"] == tier),
                "detail": "Expected confidence tier from rebuilt source-quality audit.",
            }
        )
        output.append(
            {
                "metric": f"actual_{tier}",
                "value": sum(1 for row in rows if row["actual_confidence_tier"] == tier),
                "detail": "Current visible model confidence tier.",
            }
        )
    return output


def _split(value: object) -> set[str]:
    return {part.strip() for part in str(value or "").split("|") if part.strip()}


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
