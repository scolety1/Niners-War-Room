from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.veteran_scores import PRIVATE_CONFIDENCE_EXCLUDED_FEATURES
from src.services.identity_audit_service import build_identity_audit
from src.services.model_outlier_service import (
    OUTLIER_STALE_SOURCE,
    build_model_outlier_report,
    is_review_required_bucket,
)
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
)
from src.services.source_coverage_audit_service import build_source_coverage_audit
from src.services.veteran_model_service import (
    run_veteran_model_from_dir,
    veteran_inputs_from_report,
)
from src.utils.scoring import clamp_score

CONFIDENCE_COMPONENT_WEIGHTS = {
    "source_coverage": 25.0,
    "source_freshness": 15.0,
    "identity_confidence": 20.0,
    "core_field_completeness": 17.0,
    "feature_agreement": 13.0,
    "model_outlier_status": 10.0,
}
BLOCKED_ACTION = "blocked_review"
REVIEW_ACTION = "review_before_action"
LIMITED_ACTION = "limited_certainty"
USABLE_ACTION = "usable_confidence"


@dataclass(frozen=True)
class ConfidenceRebuildReport:
    rows: list[dict[str, object]]
    explanation_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    action_certainty_levels: list[str]
    issues: list[str]
    source_root: str


def build_confidence_rebuild_report(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    as_of_date: str | date | None = None,
) -> ConfidenceRebuildReport:
    source_root = (
        Path(veteran_model_dir)
        if veteran_model_dir
        else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    try:
        model_run = run_veteran_model_from_dir(source_root)
    except ValueError as exc:
        return _empty_report(source_root, [str(exc)])

    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return _empty_report(source_root, ["Data pack has validation errors."])

    coverage = build_source_coverage_audit(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    identity = build_identity_audit(data_pack_path, source_root=source_root)
    outliers = build_model_outlier_report(
        data_pack_path,
        veteran_model_dir=source_root,
        as_of_date=as_of_date,
    )
    inputs = {
        veteran.player_id: veteran
        for veteran in veteran_inputs_from_report(model_run.schema_report)
    }
    coverage_by_player = _lookup_by_id_and_name(coverage.player_rows)
    identity_by_player = _lookup_by_id_and_name(identity.rows)
    outliers_by_player = _group_outliers(outliers.rows)
    output_lookup = _model_output_lookup(validated.rows_by_table.get("model_outputs", []))

    rows: list[dict[str, object]] = []
    explanations: list[dict[str, object]] = []
    for score in model_run.scores:
        key = _player_key(score.player_name, score.position.value)
        coverage_row = coverage_by_player.get(score.player_id) or coverage_by_player.get(key, {})
        identity_row = identity_by_player.get(score.player_id) or identity_by_player.get(key, {})
        player_outliers = outliers_by_player.get(score.player_id) or outliers_by_player.get(key, [])
        input_row = inputs.get(score.player_id)
        output_row = output_lookup.get(score.player_id) or output_lookup.get(key, {})
        component_rows = _component_rows(
            score.player_id,
            score.player_name,
            score.position.value,
            coverage_row,
            identity_row,
            player_outliers,
            input_row,
        )
        rebuilt = _weighted_confidence(component_rows)
        action_certainty, certainty_reason = _action_certainty(
            rebuilt,
            coverage_row,
            identity_row,
            player_outliers,
            component_rows,
        )
        warning_reasons = _confidence_warning_reasons(
            rebuilt,
            coverage_row,
            identity_row,
            player_outliers,
            component_rows,
        )
        rows.append(
            {
                "player_id": score.player_id,
                "data_pack_player_id": output_row.get("player_id", ""),
                "player": score.player_name,
                "position": score.position.value,
                "team": output_row.get("team", ""),
                "current_model_confidence": score.confidence_score,
                "rebuilt_confidence_score": round(rebuilt, 2),
                "confidence_delta": round(rebuilt - score.confidence_score, 2),
                "action_certainty": action_certainty,
                "certainty_reason": certainty_reason,
                "confidence_warning_reasons": "|".join(warning_reasons),
                "source_coverage_score": _component_score(component_rows, "source_coverage"),
                "source_freshness_score": _component_score(component_rows, "source_freshness"),
                "identity_confidence": _component_score(component_rows, "identity_confidence"),
                "core_field_completeness": _component_score(
                    component_rows,
                    "core_field_completeness",
                ),
                "feature_agreement": _component_score(component_rows, "feature_agreement"),
                "model_outlier_score": _component_score(component_rows, "model_outlier_status"),
                "missing_critical_inputs": coverage_row.get("missing_critical_inputs", ""),
                "missing_critical_count": int(_float(coverage_row.get("missing_critical_count"))),
                "critical_review_inputs": coverage_row.get("critical_review_inputs", ""),
                "critical_review_count": int(_float(coverage_row.get("critical_review_count"))),
                "review_gap_inputs": coverage_row.get("review_gap_inputs", ""),
                "review_gap_count": int(_float(coverage_row.get("review_gap_count"))),
                "unaccepted_review_gap_inputs": coverage_row.get(
                    "unaccepted_review_gap_inputs",
                    "",
                ),
                "unaccepted_review_gap_count": int(
                    _float(coverage_row.get("unaccepted_review_gap_count"))
                ),
                "accepted_review_gap_inputs": coverage_row.get(
                    "accepted_review_gap_inputs",
                    "",
                ),
                "accepted_review_gap_count": int(
                    _float(coverage_row.get("accepted_review_gap_count"))
                ),
                "imputed_bucket_count": int(_float(coverage_row.get("imputed_bucket_count"))),
                "identity_status": identity_row.get("ranking_trust_status")
                or identity_row.get("audit_status")
                or "not_verified",
                "outlier_count": len(player_outliers),
                "probably_broken_outliers": sum(
                    1 for row in player_outliers if is_review_required_bucket(row.get("bucket"))
                ),
                "score_adjustment_from_confidence": 0.0,
                "model_version": score.model_version,
            }
        )
        explanations.extend(component_rows)

    rows.sort(
        key=lambda row: (
            _action_priority(str(row["action_certainty"])),
            float(row["rebuilt_confidence_score"]),
            str(row["player"]).lower(),
        )
    )
    return ConfidenceRebuildReport(
        rows=rows,
        explanation_rows=explanations,
        summary_rows=_summary_rows(rows),
        action_certainty_levels=sorted({str(row["action_certainty"]) for row in rows}),
        issues=[*coverage.issues, *identity.issues, *outliers.issues],
        source_root=str(source_root),
    )


def _empty_report(root: Path, issues: list[str]) -> ConfidenceRebuildReport:
    return ConfidenceRebuildReport([], [], [], [], issues, str(root))


def _component_rows(
    player_id: str,
    player_name: str,
    position: str,
    coverage_row: dict[str, object],
    identity_row: dict[str, object],
    outlier_rows: list[dict[str, object]],
    input_row: object,
) -> list[dict[str, object]]:
    source_coverage = _float(coverage_row.get("coverage_pct"), 70.0)
    freshness = _source_freshness_score(input_row, outlier_rows)
    identity = _identity_score(identity_row)
    core = _core_field_score(coverage_row)
    agreement = _feature_agreement_score(input_row)
    outlier = _outlier_score(outlier_rows)
    components = (
        (
            "source_coverage",
            source_coverage,
            _coverage_reason(coverage_row),
        ),
        (
            "source_freshness",
            freshness,
            _freshness_reason(input_row, outlier_rows),
        ),
        (
            "identity_confidence",
            identity,
            _identity_reason(identity_row),
        ),
        (
            "core_field_completeness",
            core,
            _core_reason(coverage_row),
        ),
        (
            "feature_agreement",
            agreement,
            _feature_agreement_reason(input_row),
        ),
        (
            "model_outlier_status",
            outlier,
            _outlier_reason(outlier_rows),
        ),
    )
    return [
        {
            "player_id": player_id,
            "player": player_name,
            "position": position,
            "component": component,
            "component_score": round(score, 2),
            "component_weight": CONFIDENCE_COMPONENT_WEIGHTS[component],
            "weighted_contribution": round(
                score * CONFIDENCE_COMPONENT_WEIGHTS[component] / 100.0,
                4,
            ),
            "reason": reason,
        }
        for component, score, reason in components
    ]


def _weighted_confidence(component_rows: list[dict[str, object]]) -> float:
    weight_sum = sum(float(row["component_weight"]) for row in component_rows)
    if weight_sum <= 0:
        return 0.0
    total = sum(
        float(row["component_score"]) * float(row["component_weight"])
        for row in component_rows
    )
    return clamp_score(total / weight_sum)


def _source_freshness_score(input_row: object, outlier_rows: list[dict[str, object]]) -> float:
    freshness_values = []
    if input_row is not None:
        source_freshness = getattr(input_row, "source_freshness", {})
        features = getattr(input_row, "features", {})
        for feature_name, value in source_freshness.items():
            if feature_name in PRIVATE_CONFIDENCE_EXCLUDED_FEATURES:
                continue
            if features.get(feature_name) is not None:
                freshness_values.append(float(value))
    score = _average(freshness_values, 70.0)
    if any(row.get("outlier_type") == OUTLIER_STALE_SOURCE for row in outlier_rows):
        score = min(score, 55.0)
    return clamp_score(score)


def _identity_score(identity_row: dict[str, object]) -> float:
    if not identity_row:
        return 70.0
    status = str(identity_row.get("ranking_trust_status") or identity_row.get("audit_status") or "")
    if status == "blocked_identity_review" or status == "blocked":
        return min(_float(identity_row.get("identity_confidence")), 35.0)
    return _float(identity_row.get("identity_confidence"), 70.0)


def _core_field_score(coverage_row: dict[str, object]) -> float:
    if not coverage_row:
        return 70.0
    missing = _float(coverage_row.get("missing_critical_count"))
    imputed = _float(coverage_row.get("imputed_bucket_count"))
    penalty = (missing * 18.0) + (imputed * 7.0)
    return clamp_score(100.0 - penalty)


def _feature_agreement_score(input_row: object) -> float:
    if input_row is None:
        return 70.0
    features = getattr(input_row, "features", {})
    values = [
        float(value)
        for feature_name, value in features.items()
        if feature_name not in PRIVATE_CONFIDENCE_EXCLUDED_FEATURES and value is not None
    ]
    if len(values) < 2:
        return 70.0
    spread = max(values) - min(values)
    return clamp_score(100.0 - (spread * 0.70), 15.0, 100.0)


def _outlier_score(outlier_rows: list[dict[str, object]]) -> float:
    if not outlier_rows:
        return 100.0
    penalties = []
    for row in outlier_rows:
        bucket = str(row.get("bucket") or "")
        severity = str(row.get("severity") or "")
        if not is_review_required_bucket(bucket):
            penalties.append(4.0)
            continue
        penalties.append(
            {
                "blocking": 45.0,
                "high": 30.0,
                "medium": 18.0,
                "low": 8.0,
            }.get(severity, 12.0)
        )
    return clamp_score(100.0 - min(60.0, sum(penalties)))


def _action_certainty(
    rebuilt_confidence: float,
    coverage_row: dict[str, object],
    identity_row: dict[str, object],
    outlier_rows: list[dict[str, object]],
    component_rows: list[dict[str, object]],
) -> tuple[str, str]:
    identity_status = str(
        identity_row.get("ranking_trust_status")
        or identity_row.get("audit_status")
        or ""
    )
    severe_outlier = any(
        is_review_required_bucket(row.get("bucket"))
        and row.get("severity") in {"blocking", "high"}
        for row in outlier_rows
    )
    missing_critical = int(_float(coverage_row.get("missing_critical_count")))
    critical_review_count = int(_float(coverage_row.get("critical_review_count")))
    unaccepted_review_gaps = int(_float(coverage_row.get("unaccepted_review_gap_count")))
    feature_agreement = _component_score(component_rows, "feature_agreement")
    if identity_status in {"blocked_identity_review", "blocked"}:
        return BLOCKED_ACTION, "Identity confidence blocks stat-backed action."
    if rebuilt_confidence < 40 or missing_critical:
        return BLOCKED_ACTION, "Critical source coverage is too low."
    if critical_review_count:
        return REVIEW_ACTION, "Review imputed or stale critical source coverage."
    if unaccepted_review_gaps:
        return REVIEW_ACTION, "Review noncritical source gaps before acting."
    if feature_agreement < 65:
        return REVIEW_ACTION, "Feature agreement is low; inspect the player receipt."
    if rebuilt_confidence < 65 or severe_outlier or missing_critical:
        return REVIEW_ACTION, "Review the confidence receipts before acting."
    if rebuilt_confidence < 78:
        return LIMITED_ACTION, "Usable only with caution; confidence is below target."
    return USABLE_ACTION, "Confidence inputs are usable for review-only ranking context."


def _confidence_warning_reasons(
    rebuilt_confidence: float,
    coverage_row: dict[str, object],
    identity_row: dict[str, object],
    outlier_rows: list[dict[str, object]],
    component_rows: list[dict[str, object]],
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if rebuilt_confidence < 40:
        reasons.add("blocking_low_rebuilt_confidence")
    elif rebuilt_confidence < 65:
        reasons.add("review_low_rebuilt_confidence")
    elif rebuilt_confidence < 78:
        reasons.add("limited_rebuilt_confidence")
    if _float(coverage_row.get("missing_critical_count")) > 0:
        reasons.add("missing_core_source_bucket")
    if _float(coverage_row.get("critical_review_count")) > 0:
        reasons.add("critical_source_review")
    if _float(coverage_row.get("unaccepted_review_gap_count")) > 0:
        reasons.add("review_source_gap")
    if _float(coverage_row.get("accepted_review_gap_count")) > 0:
        reasons.add("accepted_source_gap_confidence_drag")
    if _float(coverage_row.get("imputed_bucket_count")) > 0:
        reasons.add("imputed_core_source_bucket")
    if str(identity_row.get("ranking_trust_status") or "") == "blocked_identity_review":
        reasons.add("blocked_identity_confidence")
    if any(row.get("outlier_type") == OUTLIER_STALE_SOURCE for row in outlier_rows):
        reasons.add("stale_source_data")
    if any(
        is_review_required_bucket(row.get("bucket"))
        and row.get("severity") in {"blocking", "high"}
        for row in outlier_rows
    ):
        reasons.add("severe_model_outlier")
    if _component_score(component_rows, "feature_agreement") < 65:
        reasons.add("feature_disagreement")
    return tuple(sorted(reasons))


def _lookup_by_id_and_name(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        player_id = str(row.get("player_id") or row.get("data_pack_player_id") or "")
        if player_id and player_id not in lookup:
            lookup[player_id] = row
        key = _player_key(row.get("player", ""), row.get("position", ""))
        if key and key not in lookup:
            lookup[key] = row
    return lookup


def _group_outliers(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if player_id:
            grouped.setdefault(player_id, []).append(row)
        key = _player_key(row.get("player", ""), row.get("position", ""))
        if key:
            grouped.setdefault(key, []).append(row)
    return grouped


def _model_output_lookup(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if player_id:
            lookup[player_id] = row
        key = _player_key(row.get("player_name", ""), row.get("position", ""))
        if key:
            lookup[key] = row
    return lookup


def _coverage_reason(row: dict[str, object]) -> str:
    if not row:
        return "No source coverage row was available; using review-default coverage."
    missing = str(row.get("missing_critical_inputs") or "")
    if missing:
        return f"Coverage is missing critical bucket(s): {missing}."
    return f"Source coverage is {row.get('coverage_pct', '')}%."


def _freshness_reason(input_row: object, outlier_rows: list[dict[str, object]]) -> str:
    if any(row.get("outlier_type") == OUTLIER_STALE_SOURCE for row in outlier_rows):
        return "At least one active source is stale for this player."
    if input_row is None:
        return "No model input row was available; using review-default freshness."
    return "Freshness is averaged across present non-market scoring inputs."


def _identity_reason(row: dict[str, object]) -> str:
    if not row:
        return "No identity audit row was available; using review-default identity confidence."
    return (
        f"Identity status={row.get('ranking_trust_status') or row.get('audit_status')}; "
        f"method={row.get('match_method', '')}; confidence={row.get('identity_confidence', '')}."
    )


def _core_reason(row: dict[str, object]) -> str:
    if not row:
        return "No coverage row was available for core-field completeness."
    missing = int(_float(row.get("missing_critical_count")))
    imputed = int(_float(row.get("imputed_bucket_count")))
    return f"Missing critical buckets={missing}; imputed/proxy buckets={imputed}."


def _feature_agreement_reason(input_row: object) -> str:
    if input_row is None:
        return "No feature row was available for agreement scoring."
    features = getattr(input_row, "features", {})
    values = [
        float(value)
        for feature_name, value in features.items()
        if feature_name not in PRIVATE_CONFIDENCE_EXCLUDED_FEATURES and value is not None
    ]
    if len(values) < 2:
        return "Too few present private features to measure agreement."
    return f"Private feature spread is {max(values) - min(values):.1f} points."


def _outlier_reason(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "No active outlier tripwires for this player."
    types = sorted({str(row.get("outlier_type") or "") for row in rows if row.get("outlier_type")})
    return "Outlier tripwires: " + "|".join(types)


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for action in (BLOCKED_ACTION, REVIEW_ACTION, LIMITED_ACTION, USABLE_ACTION):
        action_rows = [row for row in rows if row["action_certainty"] == action]
        if not action_rows:
            continue
        output.append(
            {
                "action_certainty": action,
                "players": len(action_rows),
                "avg_rebuilt_confidence": round(
                    sum(float(row["rebuilt_confidence_score"]) for row in action_rows)
                    / len(action_rows),
                    2,
                ),
                "missing_core_players": sum(
                    1 for row in action_rows if int(row["missing_critical_count"]) > 0
                ),
                "identity_review_players": sum(
                    1
                    for row in action_rows
                    if str(row["identity_status"])
                    in {"blocked_identity_review", "blocked", "review"}
                ),
                "outlier_players": sum(
                    1 for row in action_rows if int(row["outlier_count"]) > 0
                ),
            }
        )
    return output


def _component_score(rows: list[dict[str, object]], component: str) -> float:
    for row in rows:
        if row["component"] == component:
            return round(float(row["component_score"]), 2)
    return 0.0


def _player_key(player: object, position: object) -> str:
    name = "".join(character.lower() for character in str(player) if character.isalnum())
    if not name or not position:
        return ""
    return f"name::{name}::{position}"


def _action_priority(action: str) -> int:
    return {
        BLOCKED_ACTION: 0,
        REVIEW_ACTION: 1,
        LIMITED_ACTION: 2,
        USABLE_ACTION: 3,
    }.get(action, 9)


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _average(values: list[float], default: float) -> float:
    if not values:
        return default
    return sum(values) / len(values)
