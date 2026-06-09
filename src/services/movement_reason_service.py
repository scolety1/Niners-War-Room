from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

MOVEMENT_REASONS = {
    "source_update",
    "formula_update",
    "lifecycle_update",
    "confidence_update",
    "outlier_acceptance",
    "source_gap_acceptance",
    "market_isolation",
    "ranking_surface_change",
    "no_material_movement",
    "unknown_movement",
}

MOVEMENT_MAGNITUDES = {"none", "small", "medium", "large"}

SOURCE_FIELDS = (
    "source_key",
    "source_status",
    "source_fingerprint",
    "projection_source_status",
    "injury_source_status",
    "role_source_status",
    "production_source_status",
)
FORMULA_FIELDS = (
    "model_version",
    "formula_version",
    "formula_policy_version",
)
LIFECYCLE_FIELDS = (
    "asset_lifecycle",
    "asset_lifecycle_label",
    "experience_bucket",
    "young_nfl_bridge_weight",
    "young_nfl_bridge_source",
)
CONFIDENCE_FIELDS = (
    "confidence_score",
    "confidence",
    "confidence_label",
    "warning_status",
    "warning_reasons",
)
OUTLIER_ACCEPTANCE_FIELDS = (
    "outlier_review_status",
    "outlier_acceptance_status",
    "accepted_outlier_count",
)
SOURCE_GAP_ACCEPTANCE_FIELDS = (
    "source_gap_review_status",
    "source_gap_acceptance_status",
    "accepted_source_gap_count",
)
MARKET_FIELDS = (
    "market_value_status",
    "market_trade_value",
    "market_edge_score",
    "market_edge_label",
    "market_edge_warning",
    "market_keeper_influence",
)
RANKING_SURFACE_FIELDS = (
    "board_name",
    "surface",
    "surface_id",
    "rank_source",
    "rank_audit",
)


@dataclass(frozen=True)
class MovementClassification:
    movement_reason: str
    movement_magnitude: str
    movement_review_flag: bool


def movement_magnitude_bucket(
    *,
    rank_delta: object = "",
    value_delta: object = "",
    keeper_delta: object = "",
    confidence_delta: object = "",
) -> str:
    rank_abs = abs(_to_float(rank_delta))
    value_abs = max(
        abs(_to_float(value_delta)),
        abs(_to_float(keeper_delta)),
        abs(_to_float(confidence_delta)),
    )
    if rank_abs < 0.5 and value_abs < 0.25:
        return "none"
    if rank_abs <= 5 and value_abs < 2:
        return "small"
    if rank_abs <= 25 and value_abs < 8:
        return "medium"
    return "large"


def classify_movement(
    current: Mapping[str, object],
    previous: Mapping[str, object] | None,
    *,
    rank_delta: object = "",
    value_delta: object = "",
    keeper_delta: object = "",
    confidence_delta: object = "",
) -> MovementClassification:
    magnitude = movement_magnitude_bucket(
        rank_delta=rank_delta,
        value_delta=value_delta,
        keeper_delta=keeper_delta,
        confidence_delta=confidence_delta,
    )
    reason = _movement_reason(current=current, previous=previous, magnitude=magnitude)
    return MovementClassification(
        movement_reason=reason,
        movement_magnitude=magnitude,
        movement_review_flag=reason == "unknown_movement" and magnitude in {"medium", "large"},
    )


def movement_review_label(classification: MovementClassification) -> str:
    if classification.movement_review_flag:
        return "review_unknown_medium_large_movement"
    return "no_movement_review_needed"


def _movement_reason(
    *,
    current: Mapping[str, object],
    previous: Mapping[str, object] | None,
    magnitude: str,
) -> str:
    if magnitude == "none":
        return "no_material_movement"
    if previous is None:
        return "source_update"
    if _changed_any(current, previous, OUTLIER_ACCEPTANCE_FIELDS):
        return "outlier_acceptance"
    if _changed_any(current, previous, SOURCE_GAP_ACCEPTANCE_FIELDS):
        return "source_gap_acceptance"
    if _changed_any(current, previous, FORMULA_FIELDS):
        return "formula_update"
    if _changed_any(current, previous, LIFECYCLE_FIELDS):
        return "lifecycle_update"
    if _changed_any(current, previous, MARKET_FIELDS):
        return "market_isolation"
    if _ranking_surface_changed_without_score_change(current, previous):
        return "ranking_surface_change"
    if _changed_any(current, previous, SOURCE_FIELDS):
        return "source_update"
    if _changed_any(current, previous, CONFIDENCE_FIELDS):
        return "confidence_update"
    if _changed_any(current, previous, RANKING_SURFACE_FIELDS):
        return "ranking_surface_change"
    return "unknown_movement"


def _ranking_surface_changed_without_score_change(
    current: Mapping[str, object],
    previous: Mapping[str, object],
) -> bool:
    if not _changed_any(current, previous, RANKING_SURFACE_FIELDS):
        return False
    score_fields = (
        "private_lve_value",
        "keeper_score",
        "drop_candidate_score",
        "trade_value",
        "confidence_score",
    )
    return not _changed_any(current, previous, score_fields)


def _changed_any(
    current: Mapping[str, object],
    previous: Mapping[str, object],
    fields: tuple[str, ...],
) -> bool:
    return any(_clean(current.get(field)) != _clean(previous.get(field)) for field in fields)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _to_float(value: object) -> float:
    try:
        text = str(value or "").strip()
        return float(text) if text else 0.0
    except ValueError:
        return 0.0
