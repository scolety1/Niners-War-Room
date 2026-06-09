from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from typing import Any, Literal

LineageClass = Literal[
    "review_v4_current_player",
    "review_v4_dynasty_asset",
    "legacy_active_pack",
    "market_display_only",
    "unknown",
]
AssetType = Literal["player", "rookie", "prospect", "pick"]

APPROVED_PRIMARY_LINEAGES = {
    "review_v4_current_player",
    "review_v4_dynasty_asset",
}
LINEAGE_CLASSES = APPROVED_PRIMARY_LINEAGES | {
    "legacy_active_pack",
    "market_display_only",
    "unknown",
}
REQUIRED_DISCLOSURE_FIELDS = (
    "asset_id",
    "asset_type",
    "source_path",
    "source_column",
    "model_version",
    "lineage_class",
    "score_type",
    "score_as_of_date",
    "confidence_cap",
    "warnings",
)
DISCLOSURE_EXPORT_FIELDS = (
    "asset_id",
    "asset_type",
    "display_name",
    "primary_review_score",
    "legacy_active_pack_score",
    "source_path",
    "source_column",
    "model_version",
    "lineage_class",
    "score_type",
    "score_as_of_date",
    "confidence_cap",
    "warnings",
    "market_display_only",
    "legacy_formula_warning",
    "stale_or_legacy_formula_warning",
    "manual_decision_required",
    "allowed_use",
    "blocked_use",
)
MARKET_DISPLAY_FIELD_TOKENS = (
    "adp",
    "market",
    "ranking",
    "rankings",
    "projection",
    "projections",
    "consensus",
    "mock",
    "startup",
    "trade_calculator",
)


@dataclass(frozen=True)
class ScoreSource:
    source_path: str
    source_column: str
    lineage_class: LineageClass
    score_type: str


MODEL_V4_CURRENT_PLAYER_CHECKPOINT = ScoreSource(
    source_path="local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
    source_column="checkpoint_review_score",
    lineage_class="review_v4_current_player",
    score_type="checkpoint_review_score",
)
MODEL_V4_DYNASTY_ASSET = ScoreSource(
    source_path=(
        "local_exports/model_v4/dynasty_asset_value/latest/"
        "dynasty_asset_value_review_rows.csv"
    ),
    source_column="dynasty_asset_value_review_score",
    lineage_class="review_v4_dynasty_asset",
    score_type="dynasty_asset_value_review_score",
)


class UnknownScoreSourceError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewScoreEnvelope:
    asset_id: str
    asset_type: AssetType
    display_name: str | None
    primary_review_score: float | None
    source_path: str | None
    source_column: str | None
    model_version: str | None
    lineage_class: LineageClass
    score_type: str | None
    score_as_of_date: str | None
    confidence_cap: float | None
    warnings: tuple[str, ...]
    legacy_formula_warning: bool
    stale_or_legacy_formula_warning: bool
    market_display_only: bool
    manual_decision_required: bool
    allowed_use: str | None
    blocked_use: str | None
    legacy_active_pack_score: float | None = None
    market_context: Mapping[str, Any] | None = None
    display_context: Mapping[str, Any] | None = None


def resolve_primary_score_source(surface: str, asset_type: str) -> ScoreSource:
    normalized_surface = _normalize_token(surface)
    if normalized_surface == "player_board":
        return MODEL_V4_CURRENT_PLAYER_CHECKPOINT
    if normalized_surface in {
        "trade_review",
        "external_asset_reviews",
        "startup_slot_simulator",
        "roster_opportunity_cost",
        "pick_decision_lab",
        "draft_room",
        "rookie_board",
    }:
        return MODEL_V4_DYNASTY_ASSET
    raise UnknownScoreSourceError(f"No approved primary score source for {surface}:{asset_type}")


def classify_score_layer(row: Mapping[str, Any]) -> LineageClass:
    explicit = normalize_lineage_class(row.get("lineage_class"))
    if explicit != "unknown":
        return explicit
    model_version = str(row.get("model_version") or "")
    source_path = str(
        row.get("source_path")
        or row.get("source_file_path")
        or row.get("source_file")
        or ""
    )
    if model_version == "veteran_lve_stats_first_v1_0_0":
        return "legacy_active_pack"
    if "current_player_value_review_rows" in source_path:
        return "review_v4_current_player"
    if "dynasty_asset_value_review_rows" in source_path:
        return "review_v4_dynasty_asset"
    if _bool_value(row.get("market_display_only")):
        return "market_display_only"
    return "unknown"


def normalize_lineage_class(value: object) -> LineageClass:
    normalized = _normalize_token(value)
    if normalized == "legacy":
        return "legacy_active_pack"
    if normalized in LINEAGE_CLASSES:
        return normalized  # type: ignore[return-value]
    return "unknown"


def validate_score_envelope(env: ReviewScoreEnvelope) -> ReviewScoreEnvelope:
    env = replace(env, lineage_class=normalize_lineage_class(env.lineage_class))
    if missing_required_fields(env):
        return suppress_primary(env, reason="missing_score_disclosure_fields")
    if env.lineage_class in {"unknown", "market_display_only"}:
        return suppress_primary(env, reason="unknown_or_market_only_lineage")
    if env.lineage_class == "legacy_active_pack":
        return comparison_only(env, reason="legacy_score_comparison_only")
    if env.lineage_class not in APPROVED_PRIMARY_LINEAGES:
        return suppress_primary(env, reason="unapproved_primary_lineage")
    if env.legacy_formula_warning or env.market_display_only:
        return suppress_primary(env, reason="primary_score_guardrail_flagged")
    return env


def missing_required_fields(env: ReviewScoreEnvelope) -> bool:
    return any(_missing(getattr(env, field)) for field in REQUIRED_DISCLOSURE_FIELDS)


def suppress_primary(env: ReviewScoreEnvelope, *, reason: str) -> ReviewScoreEnvelope:
    return replace(
        env,
        primary_review_score=None,
        manual_decision_required=True,
        warnings=_append_warning(env.warnings, reason),
        blocked_use=_append_blocked_use(env.blocked_use, reason),
    )


def comparison_only(env: ReviewScoreEnvelope, *, reason: str) -> ReviewScoreEnvelope:
    legacy_score = env.legacy_active_pack_score
    if legacy_score is None:
        legacy_score = env.primary_review_score
    return replace(
        env,
        primary_review_score=None,
        legacy_active_pack_score=legacy_score,
        legacy_formula_warning=True,
        stale_or_legacy_formula_warning=True,
        manual_decision_required=True,
        warnings=_append_warning(env.warnings, reason),
        allowed_use="legacy_score_comparison_only",
        blocked_use=_append_blocked_use(env.blocked_use, "primary_review_score"),
    )


def envelope_from_row(
    row: Mapping[str, Any],
    *,
    asset_id_field: str = "asset_id",
    asset_type: AssetType | None = None,
    display_name_field: str = "display_name",
    score_column: str | None = None,
    source_path: str | None = None,
    source_column: str | None = None,
    score_type: str | None = None,
) -> ReviewScoreEnvelope:
    resolved_source_path = source_path or _first_present(
        row,
        "source_path",
        "source_file_path",
        "source_file",
    )
    resolved_source_column = source_column or score_column or _first_present(
        row,
        "source_column",
        "score_column",
        "score_field",
    )
    resolved_score_type = score_type or resolved_source_column
    lineage = classify_score_layer({**dict(row), "source_path": resolved_source_path or ""})
    primary_score = _float(row.get(resolved_source_column or ""))
    legacy_score = None
    if lineage == "legacy_active_pack":
        legacy_score = _float(row.get("legacy_active_pack_score")) or _float(
            row.get("private_score")
        )
        primary_score = legacy_score
        resolved_score_type = "legacy_active_pack_score"
        if resolved_source_column is None and "private_score" in row:
            resolved_source_column = "private_score"
    return ReviewScoreEnvelope(
        asset_id=str(row.get(asset_id_field) or row.get("canonical_player_key") or ""),
        asset_type=asset_type or _asset_type(row),
        display_name=str(row.get(display_name_field) or row.get("player_name") or "") or None,
        primary_review_score=primary_score,
        source_path=resolved_source_path,
        source_column=resolved_source_column,
        model_version=str(
            row.get("model_version")
            or row.get("checkpoint_version")
            or row.get("formula_version")
            or ""
        )
        or None,
        lineage_class=lineage,
        score_type=resolved_score_type,
        score_as_of_date=str(row.get("score_as_of_date") or row.get("as_of_date") or "") or None,
        confidence_cap=_float(row.get("confidence_cap")),
        warnings=_split_warnings(row.get("warnings") or row.get("warning_flags")),
        legacy_formula_warning=lineage == "legacy_active_pack"
        or _bool_value(row.get("legacy_formula_warning")),
        stale_or_legacy_formula_warning=lineage == "legacy_active_pack"
        or _bool_value(row.get("stale_or_legacy_formula_warning")),
        market_display_only=lineage == "market_display_only"
        or _bool_value(row.get("market_display_only")),
        manual_decision_required=_bool_value(row.get("manual_decision_required")),
        allowed_use=str(row.get("allowed_use") or "") or None,
        blocked_use=str(row.get("blocked_use") or "") or None,
        legacy_active_pack_score=legacy_score,
    )


def export_score_disclosure(env: ReviewScoreEnvelope) -> dict[str, object]:
    exported = asdict(env)
    exported["warnings"] = "|".join(env.warnings)
    return {field: exported[field] for field in DISCLOSURE_EXPORT_FIELDS}


def market_display_context(row: Mapping[str, Any]) -> dict[str, object]:
    return {
        "market_display_only": True,
        "allowed_use": "display_context_only",
        "blocked_use": (
            "primary_review_score|private_value_inputs|decision_inputs|"
            "review_label|review_band|default_sort"
        ),
        "fields": {
            key: value
            for key, value in row.items()
            if _is_market_display_field(key) and not _missing(value)
        },
    }


def row_has_market_display_fields(row: Mapping[str, Any]) -> bool:
    return any(_is_market_display_field(key) and not _missing(value) for key, value in row.items())


def active_pack_private_score_context(
    row: Mapping[str, Any],
    *,
    source_path: str,
    score_as_of_date: str | None = None,
    asset_id: str = "",
    display_name: str = "",
    asset_type: AssetType = "player",
) -> dict[str, object]:
    env = envelope_from_row(
        {
            **dict(row),
            "asset_id": asset_id or row.get("player_id") or row.get("asset_id") or "",
            "asset_type": asset_type,
            "display_name": display_name or row.get("player_name") or row.get("display_name") or "",
            "source_path": source_path,
            "source_column": "private_score",
            "score_as_of_date": score_as_of_date or row.get("snapshot_date") or "",
            "confidence_cap": row.get("confidence_score") or row.get("confidence_cap") or 0.0,
            "warnings": row.get("warning_reasons") or row.get("warning_flags") or (),
            "allowed_use": "legacy_or_unapproved_active_pack_score_context",
            "blocked_use": "primary_review_score|default_sort|review_label|summary_tile",
        },
        asset_type=asset_type,
        score_column="private_score",
        source_column="private_score",
        score_type="active_pack_private_score",
    )
    validated = validate_score_envelope(env)
    disclosure = export_score_disclosure(validated)
    return {
        "primary_review_score": "",
        "legacy_active_pack_score": disclosure["legacy_active_pack_score"] or "",
        "score_lineage_class": disclosure["lineage_class"],
        "score_source_path": disclosure["source_path"],
        "score_source_column": disclosure["source_column"],
        "score_model_version": disclosure["model_version"] or "",
        "score_allowed_use": disclosure["allowed_use"] or "",
        "score_blocked_use": disclosure["blocked_use"] or "",
        "score_manual_decision_required": disclosure["manual_decision_required"],
        "legacy_formula_warning": disclosure["legacy_formula_warning"],
        "stale_or_legacy_formula_warning": disclosure["stale_or_legacy_formula_warning"],
    }


def _asset_type(row: Mapping[str, Any]) -> AssetType:
    value = _normalize_token(row.get("asset_type") or row.get("entity_type"))
    if value in {"rookie", "rookie_prospect"}:
        return "rookie"
    if value in {"prospect"}:
        return "prospect"
    if value in {"pick", "owned_rookie_pick"}:
        return "pick"
    return "player"


def _append_warning(warnings: tuple[str, ...], reason: str) -> tuple[str, ...]:
    if reason in warnings:
        return warnings
    return (*warnings, reason)


def _append_blocked_use(blocked_use: str | None, reason: str) -> str:
    values = [value for value in str(blocked_use or "").split("|") if value]
    if reason not in values:
        values.append(reason)
    return "|".join(values)


def _first_present(row: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if not _missing(value):
            return str(value)
    return None


def _split_warnings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return tuple(part.strip() for part in str(value).split("|") if part.strip())


def _missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _float(value: object) -> float | None:
    if _missing(value):
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _normalize_token(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _is_market_display_field(key: object) -> bool:
    normalized = _normalize_token(key)
    return any(token in normalized for token in MARKET_DISPLAY_FIELD_TOKENS)
