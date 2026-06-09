from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.veteran_scores import VeteranScore
from src.services.identity_audit_service import build_identity_audit
from src.services.outlier_acceptance_service import (
    OUTLIER_ACCEPTANCE_FILE,
    apply_outlier_acceptances,
)
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    build_player_feature_receipts,
)
from src.services.veteran_model_schema_service import VeteranSchemaReport
from src.services.veteran_model_service import run_veteran_model_from_dir

BUCKET_TRUE_RANKING_WEIRDNESS = "True Ranking Weirdness"
BUCKET_MISSING_MARKET_REFERENCE = "Missing Market Reference"
BUCKET_MISSING_INJURY_PROJECTION = "Missing Injury/Projection"
BUCKET_IDENTITY_ISSUE = "Identity Issue"
BUCKET_ONE_FEATURE_DRIVEN = "One-Feature-Driven Rank"
BUCKET_ONTO_SOMETHING = "Model Might Be Onto Something"
BUCKET_PROBABLY_BROKEN = BUCKET_TRUE_RANKING_WEIRDNESS
REVIEW_REQUIRED_BUCKETS = (
    BUCKET_TRUE_RANKING_WEIRDNESS,
    BUCKET_MISSING_MARKET_REFERENCE,
    BUCKET_MISSING_INJURY_PROJECTION,
    BUCKET_IDENTITY_ISSUE,
    BUCKET_ONE_FEATURE_DRIVEN,
)
BUCKET_ORDER = (
    BUCKET_IDENTITY_ISSUE,
    BUCKET_MISSING_INJURY_PROJECTION,
    BUCKET_MISSING_MARKET_REFERENCE,
    BUCKET_ONE_FEATURE_DRIVEN,
    BUCKET_TRUE_RANKING_WEIRDNESS,
    BUCKET_ONTO_SOMETHING,
)
OUTLIER_MARKET_MODEL_GAP = "market_model_rank_gap"
OUTLIER_MARKET_REFERENCE_GAP = "market_reference_missing_or_neutral"
OUTLIER_TOP3_LOW_CONFIDENCE = "position_top3_low_confidence"
OUTLIER_ONE_FEATURE_DRIVEN = "high_rank_one_feature_driven"
OUTLIER_IMPUTED_CORE = "missing_imputed_core_data"
OUTLIER_STALE_SOURCE = "stale_source_data"
OUTLIER_IDENTITY_AMBIGUITY = "identity_ambiguity"


@dataclass(frozen=True)
class ModelOutlierReport:
    rows: list[dict[str, object]]
    bucket_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    acceptance_rows: list[dict[str, object]]
    acceptance_summary_rows: list[dict[str, object]]
    invalid_acceptance_rows: list[dict[str, object]]
    buckets: list[str]
    outlier_types: list[str]
    issues: list[str]
    source_root: str


def is_review_required_bucket(bucket: object) -> bool:
    return str(bucket or "") in REVIEW_REQUIRED_BUCKETS


def build_model_outlier_report(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    as_of_date: str | date | None = None,
) -> ModelOutlierReport:
    source_root = (
        Path(veteran_model_dir)
        if veteran_model_dir
        else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    try:
        model_run = run_veteran_model_from_dir(source_root)
    except ValueError as exc:
        return _empty_report(str(source_root), [str(exc)])

    output_lookup = _data_pack_model_lookup(data_pack_path)
    rows: list[dict[str, object]] = []
    player_lookup = {player.player_id: player for player in model_run.schema_report.players}
    score_context = _score_context_rows(model_run.scores, output_lookup, player_lookup)
    rows.extend(_market_model_gap_rows(score_context))
    rows.extend(_position_top3_low_confidence_rows(score_context))

    receipts = build_player_feature_receipts(data_pack_path, veteran_model_dir=source_root)
    rows.extend(_one_feature_driven_rows(receipts.rows, score_context))
    rows.extend(_imputed_core_rows(receipts.rows, score_context))
    rows.extend(
        _stale_source_rows(
            model_run.schema_report,
            score_context,
            _as_of_date(as_of_date),
        )
    )
    rows.extend(_identity_ambiguity_rows(data_pack_path, source_root, score_context))

    rows = _dedupe_and_sort(rows)
    rows, acceptance_report = apply_outlier_acceptances(
        rows,
        source_root / OUTLIER_ACCEPTANCE_FILE,
    )
    return ModelOutlierReport(
        rows=rows,
        bucket_rows=_bucket_rows(rows),
        summary_rows=_summary_rows(rows),
        acceptance_rows=acceptance_report.rows,
        acceptance_summary_rows=acceptance_report.summary_rows,
        invalid_acceptance_rows=acceptance_report.invalid_rows,
        buckets=sorted({str(row["bucket"]) for row in rows}),
        outlier_types=sorted({str(row["outlier_type"]) for row in rows}),
        issues=receipts.issues,
        source_root=str(source_root),
    )


def _empty_report(source_root: str, issues: list[str]) -> ModelOutlierReport:
    return ModelOutlierReport([], [], [], [], [], [], [], [], issues, source_root)


def _data_pack_model_lookup(data_pack_path: str | Path) -> dict[str, dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return {}
    return {
        str(row.get("player_id") or ""): row
        for row in validated.rows_by_table.get("model_outputs", [])
        if row.get("player_id")
    }


def _score_context_rows(
    scores: tuple[VeteranScore, ...],
    output_lookup: dict[str, dict[str, object]],
    player_lookup: dict[str, object],
) -> dict[str, dict[str, object]]:
    rows: list[dict[str, object]] = []
    for score in scores:
        output = output_lookup.get(score.player_id, {})
        private_score = _float(output.get("private_score"), score.veteran_base_value)
        trade_liquidity = _float(output.get("market_score"), score.trade_value)
        war_score = _float(
            output.get("war_score"),
            round((0.70 * score.keeper_score) + (0.30 * score.trade_value), 2),
        )
        rows.append(
            {
                "player_id": score.player_id,
                "player": score.player_name,
                "position": score.position.value,
                "team": output.get("team")
                or getattr(player_lookup.get(score.player_id), "team_name", ""),
                "private_score": private_score,
                "trade_liquidity": trade_liquidity,
                "war_score": war_score,
                "keeper_score": _float(output.get("keeper_score"), score.keeper_score),
                "drop_score": _float(
                    output.get("drop_candidate_score"),
                    score.drop_candidate_score,
                ),
                "confidence_score": _float(
                    output.get("confidence_score"),
                    score.confidence_score,
                ),
                "warning_status": output.get("warning_status") or score.warning_status,
                "warning_reasons": output.get("warning_reasons")
                or "|".join(score.warning_reasons),
                "risk_flags": output.get("risk_flags") or "|".join(score.risk_flags),
                "model_version": output.get("model_version") or score.model_version,
            }
        )
    _add_rank(rows, "war_score", "model_rank")
    _add_rank(rows, "private_score", "private_rank")
    _add_rank(rows, "trade_liquidity", "market_rank")
    _add_position_rank(rows)
    return {str(row["player_id"]): row for row in rows}


def _market_model_gap_rows(score_context: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in score_context.values():
        rank_gap = int(row["market_rank"]) - int(row["model_rank"])
        score_gap = _float(row["private_score"]) - _float(row["trade_liquidity"])
        if abs(rank_gap) < 30 and abs(score_gap) < 8.0:
            continue
        if _is_deep_rank_market_noise(row, score_gap):
            continue
        market_reference_missing = _neutral_market_reference(row) and abs(score_gap) >= 18.0
        if market_reference_missing:
            output.append(
                _outlier_row(
                    row,
                    bucket=BUCKET_MISSING_MARKET_REFERENCE,
                    outlier_type=OUTLIER_MARKET_REFERENCE_GAP,
                    severity="medium",
                    signal_value=round(score_gap, 2),
                    reason=(
                        "Trade-liquidity reference is neutral/defaulted at 50.0, so "
                        f"market-edge math is not trustworthy for this player; private "
                        f"minus trade liquidity {score_gap:.2f}."
                    ),
                    suggested_review=(
                        "Fill or approve a real market/liquidity reference before using "
                        "this row as a buy/sell edge."
                    ),
                )
            )
            continue
        direction = "model_above_market" if rank_gap > 0 or score_gap > 0 else "market_above_model"
        bucket = (
            BUCKET_ONTO_SOMETHING
            if _high_confidence(row) and _data_clean(row)
            else _data_issue_bucket(row)
        )
        output.append(
            _outlier_row(
                row,
                bucket=bucket,
                outlier_type=OUTLIER_MARKET_MODEL_GAP,
                severity="medium",
                signal_value=round(score_gap, 2),
                reason=(
                    f"{direction}: model rank {row['model_rank']} vs market rank "
                    f"{row['market_rank']}; private minus trade liquidity {score_gap:.2f}."
                ),
                suggested_review=(
                    "If data is clean, this may be an exploitable market disagreement."
                    if bucket == BUCKET_ONTO_SOMETHING
                    else (
                        "Treat this as a market-edge lead only after the source and "
                        "identity gates are clean."
                    )
                ),
            )
        )
    return output


def _position_top3_low_confidence_rows(
    score_context: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    return [
        _outlier_row(
            row,
            bucket=_data_issue_bucket(row),
            outlier_type=OUTLIER_TOP3_LOW_CONFIDENCE,
            severity="high",
            signal_value=row["confidence_score"],
            reason=(
                f"Position rank {row['position_rank']} with confidence "
                f"{float(row['confidence_score']):.2f}."
            ),
            suggested_review="A top-three positional ranking needs stronger source confidence.",
        )
        for row in score_context.values()
        if int(row["position_rank"]) <= 3 and _float(row["confidence_score"]) < 70
    ]


def _one_feature_driven_rows(
    receipt_rows: list[dict[str, object]],
    score_context: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], float] = {}
    component_scores: dict[tuple[str, str], float] = {}
    for row in receipt_rows:
        player_id = str(row["player_id"])
        component = str(row["component"])
        if component == "trade_value":
            continue
        source_feature = str(row["source_feature_name"])
        if source_feature == "formula_derived":
            continue
        key = (player_id, component, source_feature)
        grouped[key] = grouped.get(key, 0.0) + _float(row.get("contribution"))
        component_scores[(player_id, component)] = _float(row.get("component_score"))

    output: list[dict[str, object]] = []
    for (player_id, component, source_feature), contribution in grouped.items():
        context = score_context.get(player_id)
        if not context:
            continue
        if int(context["model_rank"]) > 35 and int(context["position_rank"]) > 3:
            continue
        component_score = component_scores.get((player_id, component), 0.0)
        if component_score <= 0:
            continue
        share = contribution / component_score
        if share < 0.42:
            continue
        output.append(
            _outlier_row(
                context,
                bucket=BUCKET_ONE_FEATURE_DRIVEN,
                outlier_type=OUTLIER_ONE_FEATURE_DRIVEN,
                severity=_one_feature_outlier_severity(component, share),
                signal_value=round(share, 3),
                reason=(
                    f"{source_feature} supplies {share:.1%} of {component}; "
                    "ranking may be too dependent on one feature."
                ),
                suggested_review="Open Player Feature Receipts and verify this source feature.",
                source_feature=source_feature,
                component=component,
            )
        )
    return output


def _imputed_core_rows(
    receipt_rows: list[dict[str, object]],
    score_context: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    core_components = {
        "veteran_base_value",
        "win_now_value",
        "dynasty_hold_value",
        "private_lve_value",
        "lve_format_fit",
    }
    for row in receipt_rows:
        if not bool(row.get("imputed_flag")):
            continue
        if str(row.get("source_feature_name")) == "formula_derived":
            continue
        if str(row.get("component")) not in core_components:
            continue
        if _float(row.get("feature_weight")) < 8:
            continue
        context = score_context.get(str(row["player_id"]))
        if not context:
            continue
        grouped.setdefault((str(row["player_id"]), str(row["component"])), []).append(row)
    output: list[dict[str, object]] = []
    for (player_id, component), rows in grouped.items():
        context = score_context.get(player_id)
        if not context:
            continue
        source_features = sorted(
            {
                str(row.get("source_feature_name") or row.get("formula_feature_name") or "")
                for row in rows
                if row.get("source_feature_name") or row.get("formula_feature_name")
            }
        )
        warning_details = sorted(
            {
                str(row.get("warning_reason") or "")
                for row in rows
                if row.get("warning_reason")
            }
        )
        severity = (
            "high"
            if int(context["model_rank"]) <= 75
            or int(context["position_rank"]) <= 5
            or _float(context["confidence_score"]) < 50
            else "medium"
        )
        output.append(
            _outlier_row(
                context,
                bucket=_missing_source_bucket(source_features, warning_details),
                outlier_type=OUTLIER_IMPUTED_CORE,
                severity=severity,
                signal_value=len(source_features),
                reason=(
                    f"{component} has missing or neutral-default core features: "
                    + ", ".join(source_features[:5])
                    + ("." if len(source_features) <= 5 else ", ...")
                    + (
                        ""
                        if not warning_details
                        else " Details: " + "; ".join(warning_details[:3])
                    )
                ),
                suggested_review=(
                    "Do not trust this ranking until the source features are filled or approved."
                ),
                source_feature="multiple_missing_core_features",
                component=component,
            )
        )
    return output


def _stale_source_rows(
    report: VeteranSchemaReport,
    score_context: dict[str, dict[str, object]],
    as_of: date,
) -> list[dict[str, object]]:
    stale_sources = {
        source.source_key: source
        for source in report.sources
        if source.is_active and _is_stale(source.source_date, source.freshness_window_hours, as_of)
    }
    if not stale_sources:
        return []
    feature_by_player: dict[str, set[str]] = {}
    for feature in report.feature_scores:
        if feature.source_key in stale_sources:
            feature_by_player.setdefault(feature.player_id, set()).add(feature.source_key)
    output: list[dict[str, object]] = []
    for player_id, source_keys in feature_by_player.items():
        context = score_context.get(player_id)
        if not context:
            continue
        source_names = ", ".join(sorted(source_keys)[:3])
        output.append(
            _outlier_row(
                context,
                bucket=_stale_source_bucket(source_keys),
                outlier_type=OUTLIER_STALE_SOURCE,
                severity="medium",
                signal_value=len(source_keys),
                reason=f"Player depends on stale source data: {source_names}.",
                suggested_review="Refresh/apply updated source data before using this ranking.",
            )
        )
    return output


def _identity_ambiguity_rows(
    data_pack_path: str | Path,
    source_root: Path,
    score_context: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    identity_report = build_identity_audit(
        data_pack_path,
        source_root=source_root,
    )
    if identity_report.issues:
        return output
    context_by_name = _score_context_by_name(score_context)
    for row in identity_report.rows:
        player_id = str(row.get("player_id") or row.get("sleeper_id") or "")
        context = score_context.get(player_id) or context_by_name.get(
            _identity_name_key(row.get("player", ""), row.get("position", ""))
        )
        if not context:
            continue
        ambiguous = (
            bool(row.get("manual_review_required"))
            or row.get("audit_status") != "ready"
            or row.get("ranking_trust_status") == "blocked_identity_review"
        )
        if not ambiguous:
            continue
        severity = (
            "blocking"
            if row.get("ranking_trust_status") == "blocked_identity_review"
            else "medium"
        )
        output.append(
            _outlier_row(
                context,
                bucket=BUCKET_IDENTITY_ISSUE,
                outlier_type=OUTLIER_IDENTITY_AMBIGUITY,
                severity=severity,
                signal_value=row.get("identity_confidence", ""),
                reason=(
                    "Identity bridge requires review: "
                    f"match_method={row.get('match_method', '')}; "
                    f"audit_status={row.get('audit_status', '')}; "
                    f"confidence={row.get('identity_confidence', '')}."
                ),
                suggested_review=(
                    "Resolve Sleeper-to-nflverse identity before trusting statistics."
                ),
            )
        )
    return output


def _score_context_by_name(
    score_context: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in score_context.values():
        key = _identity_name_key(row.get("player", ""), row.get("position", ""))
        grouped.setdefault(key, []).append(row)
    return {
        key: rows[0]
        for key, rows in grouped.items()
        if key and len(rows) == 1
    }


def _identity_name_key(player: object, position: object) -> str:
    name = "".join(character.lower() for character in str(player) if character.isalnum())
    return f"{name}::{position}"


def _data_issue_bucket(row: dict[str, object]) -> str:
    text = " ".join(
        [
            str(row.get("warning_status") or ""),
            str(row.get("warning_reasons") or ""),
            str(row.get("risk_flags") or ""),
        ]
    ).lower()
    if "identity" in text:
        return BUCKET_IDENTITY_ISSUE
    if any(marker in text for marker in ("injury", "projection", "stale", "missing")):
        return BUCKET_MISSING_INJURY_PROJECTION
    return BUCKET_TRUE_RANKING_WEIRDNESS


def _missing_source_bucket(
    source_features: list[str],
    warning_details: list[str],
) -> str:
    text = " ".join([*source_features, *warning_details]).lower()
    if any(marker in text for marker in ("injury", "projection", "projected", "lve_projection")):
        return BUCKET_MISSING_INJURY_PROJECTION
    return BUCKET_TRUE_RANKING_WEIRDNESS


def _stale_source_bucket(source_keys: set[str]) -> str:
    text = " ".join(sorted(source_keys)).lower()
    if any(marker in text for marker in ("injury", "projection")):
        return BUCKET_MISSING_INJURY_PROJECTION
    if any(
        marker in text
        for marker in (
            "market",
            "fantasycalc",
            "dynastyprocess",
            "replaceability",
            "liquidity",
        )
    ):
        return BUCKET_MISSING_MARKET_REFERENCE
    return BUCKET_TRUE_RANKING_WEIRDNESS


def _review_status(bucket: str, severity: str, outlier_type: str) -> str:
    if bucket == BUCKET_ONTO_SOMETHING:
        return "edge_candidate_review"
    if bucket == BUCKET_MISSING_MARKET_REFERENCE:
        return "needs_market_reference"
    if bucket == BUCKET_MISSING_INJURY_PROJECTION:
        return "needs_injury_projection_source"
    if bucket == BUCKET_IDENTITY_ISSUE:
        return "blocked_identity_review" if severity == "blocking" else "identity_review"
    if bucket == BUCKET_ONE_FEATURE_DRIVEN:
        return "needs_receipt_review"
    if outlier_type == OUTLIER_MARKET_MODEL_GAP:
        return "true_ranking_gap_review"
    return "ranking_review"


def _next_action(bucket: str, outlier_type: str, suggested_review: str) -> str:
    if bucket == BUCKET_ONTO_SOMETHING:
        return "Compare receipts and market edge; treat as possible opportunity, not a bug."
    if bucket == BUCKET_MISSING_MARKET_REFERENCE:
        return "Add or approve a market/liquidity reference before reading market edge."
    if bucket == BUCKET_MISSING_INJURY_PROJECTION:
        return "Backfill injury/projection/role source data or explicitly approve the gap."
    if bucket == BUCKET_IDENTITY_ISSUE:
        return "Resolve player identity mapping before trusting stat-derived scores."
    if bucket == BUCKET_ONE_FEATURE_DRIVEN:
        return "Open feature receipts and verify the dominant feature source."
    if outlier_type == OUTLIER_MARKET_MODEL_GAP:
        return "Compare player receipts against market; decide if this is model error or edge."
    return suggested_review


def _bucket_priority(bucket: str) -> int:
    try:
        return BUCKET_ORDER.index(bucket)
    except ValueError:
        return len(BUCKET_ORDER)


def _outlier_row(
    context: dict[str, object],
    *,
    bucket: str,
    outlier_type: str,
    severity: str,
    signal_value: object,
    reason: str,
    suggested_review: str,
    source_feature: str = "",
    component: str = "",
) -> dict[str, object]:
    review_status = _review_status(bucket, severity, outlier_type)
    next_action = _next_action(bucket, outlier_type, suggested_review)
    return {
        "bucket": bucket,
        "outlier_type": outlier_type,
        "severity": severity,
        "review_status": review_status,
        "player_id": context["player_id"],
        "player": context["player"],
        "position": context["position"],
        "team": context["team"],
        "model_rank": context["model_rank"],
        "position_rank": context["position_rank"],
        "private_rank": context["private_rank"],
        "market_rank": context["market_rank"],
        "war_score": context["war_score"],
        "private_score": context["private_score"],
        "trade_liquidity": context["trade_liquidity"],
        "keeper_score": context["keeper_score"],
        "confidence_score": context["confidence_score"],
        "warning_status": context["warning_status"],
        "signal_value": signal_value,
        "component": component,
        "source_feature": source_feature,
        "reason": reason,
        "suggested_review": suggested_review,
        "next_action": next_action,
        "model_version": context["model_version"],
    }


def _dedupe_and_sort(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    severity_order = {"blocking": 0, "high": 1, "medium": 2, "low": 3}
    seen: set[tuple[str, str, str, str]] = set()
    output: list[dict[str, object]] = []
    for row in rows:
        key = (
            str(row["player_id"]),
            str(row["outlier_type"]),
            str(row["component"]),
            str(row["source_feature"]),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return sorted(
        output,
        key=lambda row: (
            _bucket_priority(str(row["bucket"])),
            severity_order.get(str(row["severity"]), 9),
            int(row["model_rank"]),
            str(row["player"]).lower(),
        ),
    )


def _bucket_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for bucket in BUCKET_ORDER:
        bucket_rows = [row for row in rows if row["bucket"] == bucket]
        accepted_rows = [row for row in bucket_rows if row.get("acceptance_status") == "accepted"]
        unresolved_rows = [
            row for row in bucket_rows if row.get("acceptance_status") != "accepted"
        ]
        output.append(
            {
                "bucket": bucket,
                "outliers": len(bucket_rows),
                "accepted": len(accepted_rows),
                "unresolved": len(unresolved_rows),
                "players": len({row["player_id"] for row in bucket_rows}),
                "review_required": bucket in REVIEW_REQUIRED_BUCKETS,
                "blocking": sum(
                    1
                    for row in unresolved_rows
                    if row["severity"] == "blocking"
                ),
                "high": sum(1 for row in unresolved_rows if row["severity"] == "high"),
                "medium": sum(1 for row in unresolved_rows if row["severity"] == "medium"),
            }
        )
    return output


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for outlier_type in sorted({str(row["outlier_type"]) for row in rows}):
        type_rows = [row for row in rows if row["outlier_type"] == outlier_type]
        unresolved_type_rows = [
            row for row in type_rows if row.get("acceptance_status") != "accepted"
        ]
        output.append(
            {
                "outlier_type": outlier_type,
                "rows": len(type_rows),
                "accepted": sum(
                    1 for row in type_rows if row.get("acceptance_status") == "accepted"
                ),
                "unresolved": len(unresolved_type_rows),
                "players": len({row["player_id"] for row in type_rows}),
                "review_required": sum(
                    1
                    for row in unresolved_type_rows
                    if is_review_required_bucket(row["bucket"])
                ),
                "might_be_onto_something": sum(
                    1 for row in type_rows if row["bucket"] == BUCKET_ONTO_SOMETHING
                ),
            }
        )
    return output


def _add_rank(rows: list[dict[str, object]], value_key: str, rank_key: str) -> None:
    sorted_rows = sorted(rows, key=lambda row: (-_float(row[value_key]), str(row["player"])))
    for rank, row in enumerate(sorted_rows, start=1):
        row[rank_key] = rank


def _add_position_rank(rows: list[dict[str, object]]) -> None:
    for position in sorted({str(row["position"]) for row in rows}):
        position_rows = [row for row in rows if row["position"] == position]
        sorted_rows = sorted(
            position_rows,
            key=lambda row: (-_float(row["war_score"]), str(row["player"])),
        )
        for rank, row in enumerate(sorted_rows, start=1):
            row["position_rank"] = rank


def _is_stale(source_date: str, freshness_window_hours: int | None, as_of: date) -> bool:
    try:
        source_day = date.fromisoformat(str(source_date)[:10])
    except ValueError:
        return True
    if not freshness_window_hours:
        return False
    return (as_of - source_day).days * 24 > freshness_window_hours


def _as_of_date(value: str | date | None) -> date:
    if isinstance(value, date):
        return value
    if value:
        return date.fromisoformat(str(value)[:10])
    return date.today()


def _high_confidence(row: dict[str, object]) -> bool:
    return _float(row["confidence_score"]) >= 75


def _data_clean(row: dict[str, object]) -> bool:
    warning_status = str(row.get("warning_status") or "")
    warning_reasons = str(row.get("warning_reasons") or "")
    clean_statuses = {"ready", "data_warning", "model_warning", "review_needed"}
    return warning_status in clean_statuses and not any(
        marker in warning_reasons
        for marker in (
            "missing",
            "identity",
            "blocking",
            "manual_override",
            "placeholder",
            "stale",
            "imputed",
        )
    )


def _is_deep_rank_market_noise(row: dict[str, object], score_gap: float) -> bool:
    return (
        int(row["model_rank"]) > 150
        and int(row["market_rank"]) > 150
        and abs(score_gap) < 18.0
    )


def _neutral_market_reference(row: dict[str, object]) -> bool:
    return abs(_float(row.get("trade_liquidity")) - 50.0) < 0.01


def _one_feature_outlier_severity(component: str, share: float) -> str:
    if component == "lve_format_fit":
        return "medium"
    return "high" if share >= 0.55 else "medium"


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _boolish(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}
