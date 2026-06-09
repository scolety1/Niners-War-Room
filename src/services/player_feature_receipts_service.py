from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.veteran_scores import VeteranScore
from src.services.feature_data_truth_contract_service import classify_feature_truth
from src.services.player_lifecycle_service import (
    asset_lifecycle_label,
    is_young_nfl_bridge_lifecycle,
    lifecycle_from_lookup,
    load_active_lifecycle_lookup,
)
from src.services.veteran_model_schema_service import (
    FEATURE_SCORE_FILE,
    VeteranFeatureDefinition,
    VeteranFeatureScore,
    VeteranSchemaReport,
    VeteranSourceRow,
)
from src.services.veteran_model_service import run_veteran_model_from_dir
from src.services.warning_language_service import (
    confidence_explanation,
    confidence_label,
    warning_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_VETERAN_MODEL_DIR = (
    PROJECT_ROOT / "local_exports" / "active_veteran_model_public_sources"
)
FALLBACK_RECEIPT_VETERAN_MODEL_DIR = PROJECT_ROOT / "sample_data" / "veteran_model_v1"
STATS_FIRST_NORMALIZED_FEATURE_FILE = "stats_first_normalized_features.csv"
STATS_FIRST_CONTRIBUTION_FILE = "stats_first_feature_contributions.csv"
FORMULA_DERIVED_WARNING = "formula derived from displayed component features"
BRIDGE_RECEIPT_FEATURES = {
    "draft_capital_prior_score",
    "young_nfl_bridge_decay_weight",
    "young_nfl_bridge_nfl_evidence_weight",
    "young_nfl_bridge_prior",
}
DETAILED_PRIVATE_COMPONENTS = {
    "veteran_base_value",
    "win_now_value",
    "dynasty_hold_value",
    "horizon_retention_score",
    "lve_format_fit",
}
WRAPPER_FEATURES = {
    "private_lve_value",
    "keeper_score",
    "trade_value",
    "win_now_value",
    "dynasty_hold_value",
    "confidence_score",
}

STATS_FIRST_FEATURE_PRIORITY = (
    "lve_projection_value",
    "expected_lve_points_score",
    "weighted_recent_lve_ppg_score",
    "role_security",
    "workload_earning",
    "target_earning_stability",
    "route_share_stability",
    "route_role",
    "efficiency_score",
    "first_down_td_fit",
    "age_curve",
    "injury_durability",
    "position_replaceability",
    "market_liquidity",
)
COMPONENT_PRIORITY = (
    "veteran_base_value",
    "private_lve_value",
    "lve_format_fit",
    "horizon_retention_score",
    "trade_value",
)

RECEIPT_DISPLAY_COLUMNS: tuple[str, ...] = (
    "player",
    "position",
    "asset_lifecycle_label",
    "receipt_section_label",
    "lifecycle_explanation",
    "component",
    "formula_feature_name",
    "raw_feature_value",
    "normalized_score",
    "feature_weight",
    "contribution",
    "source_file",
    "source_date",
    "imputed_flag",
    "warning_reason",
)

RECEIPT_COLUMN_LABELS: dict[str, str] = {
    "player": "Player",
    "position": "Pos",
    "asset_lifecycle_label": "Lifecycle",
    "receipt_section_label": "Receipt Section",
    "lifecycle_explanation": "Lifecycle Explanation",
    "component": "Component",
    "formula_feature_name": "Feature",
    "raw_feature_value": "Raw Value",
    "normalized_score": "Normalized Score",
    "feature_weight": "Feature Weight",
    "contribution": "Contribution",
    "source_file": "Source",
    "source_date": "Source Date",
    "imputed_flag": "Imputed?",
    "warning_reason": "Warning",
}

RECEIPT_SECTION_LABELS: dict[str, str] = {
    "nfl_production": "NFL Production",
    "role_usage": "Role/Usage",
    "first_down_td_fit": "First-Down/TD Fit",
    "age_injury": "Age/Injury",
    "projection": "Projection",
    "young_player_bridge_prior": "Young-Player Bridge Prior",
    "market_liquidity": "Market/Liquidity",
}

FEATURE_RECEIPT_SECTIONS: dict[str, str] = {
    "weighted_recent_lve_ppg_score": "nfl_production",
    "production_stability": "nfl_production",
    "win_now_value": "nfl_production",
    "dynasty_hold_value": "nfl_production",
    "private_lve_value": "nfl_production",
    "keeper_score": "nfl_production",
    "role_security": "role_usage",
    "workload_earning": "role_usage",
    "target_earning_stability": "role_usage",
    "route_share_stability": "role_usage",
    "route_role": "role_usage",
    "start_gated_rushing_profile": "role_usage",
    "qb_replacement_level_baseline": "role_usage",
    "qb_replacement_suppression": "role_usage",
    "te_replacement_level_baseline": "role_usage",
    "te_no_premium_suppression": "role_usage",
    "first_down_td_fit": "first_down_td_fit",
    "first_down_td_fit_capped": "first_down_td_fit",
    "efficiency_score": "first_down_td_fit",
    "age_curve": "age_injury",
    "injury_durability": "age_injury",
    "rb_dynasty_cap": "age_injury",
    "wr_dynasty_cap": "age_injury",
    "lve_structural_formula_adjustment": "age_injury",
    "expected_lve_points_score": "projection",
    "lve_projection_value": "projection",
    "draft_capital_prior_score": "young_player_bridge_prior",
    "young_nfl_bridge_decay_weight": "young_player_bridge_prior",
    "young_nfl_bridge_nfl_evidence_weight": "young_player_bridge_prior",
    "young_nfl_bridge_prior": "young_player_bridge_prior",
    "market_liquidity": "market_liquidity",
    "trade_value": "market_liquidity",
    "market_edge": "market_liquidity",
    "visible_stats_value": "nfl_production",
    "confidence": "nfl_production",
    "why_available": "market_liquidity",
}


@dataclass(frozen=True)
class PlayerFeatureReceiptsReport:
    rows: list[dict[str, object]]
    component_summary_rows: list[dict[str, object]]
    players: list[str]
    components: list[str]
    issues: list[str]
    source_root: str


def compact_receipt_preview_for_player(
    report: PlayerFeatureReceiptsReport,
    player_row: dict[str, object],
    *,
    page_source: str = "War Board",
    driver_count: int = 5,
) -> dict[str, object]:
    receipt_rows = receipt_rows_for_players(
        report,
        [player_row],
        player_column="player",
        position_column="pos",
        include_fallback_rows=True,
        page_source=page_source,
    )
    driver_source_rows = _primary_model_driver_rows(receipt_rows)
    positive_rows = [
        row for row in driver_source_rows if _float(row.get("contribution")) > 0
    ][:driver_count]
    negative_rows = _receipt_drag_rows(driver_source_rows, driver_count=driver_count)
    bridge_rows = _bridge_receipt_rows(receipt_rows)
    market_rows = _market_receipt_rows(receipt_rows)

    lifecycle_explanation = _first_non_empty(
        [row.get("lifecycle_explanation") for row in receipt_rows]
    )
    if not lifecycle_explanation:
        lifecycle = str(
            player_row.get("asset_lifecycle_label")
            or player_row.get("lifecycle")
            or "Unknown lifecycle"
        )
        lifecycle_explanation = f"This player is currently labeled as {lifecycle}."

    source_warnings = _unique_non_empty(
        [
            _first_view_warning(player_row.get("warning_reason")),
            _first_view_warning(player_row.get("score_source_warning")),
            *[_first_view_warning(row.get("warning_reason")) for row in receipt_rows],
        ]
    )
    return {
        "summary": {
            "rank": player_row.get("overall_rank", ""),
            "position_rank": player_row.get("position_rank_label", ""),
            "player": player_row.get("player", ""),
            "position": player_row.get("pos") or player_row.get("position") or "",
            "model_value": player_row.get("stats_value", ""),
            "confidence": player_row.get("confidence", ""),
            "confidence_label": player_row.get("confidence_label")
            or confidence_label(player_row.get("confidence", "")),
            "confidence_explanation": player_row.get("confidence_explanation")
            or confidence_explanation(
                player_row.get("confidence", ""),
                player_row.get("warning_reason"),
                player_row.get("score_source_warning"),
            ),
            "lifecycle": player_row.get("asset_lifecycle_label", ""),
            "warning": player_row.get("warning_reason", ""),
        },
        "positive_drivers": _compact_driver_rows(positive_rows),
        "negative_drivers": _compact_driver_rows(negative_rows),
        "bridge_drivers": _compact_driver_rows(bridge_rows),
        "market_context": _compact_driver_rows(market_rows),
        "lifecycle_explanation": lifecycle_explanation,
        "source_warnings": source_warnings,
        "advanced_receipt_rows": receipt_rows,
    }


def _primary_model_driver_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    detailed_private_rows = [
        row
        for row in rows
        if str(row.get("component") or "") in DETAILED_PRIVATE_COMPONENTS
        and str(row.get("receipt_section_label") or "") != "Market/Liquidity"
        and str(row.get("formula_feature_name") or "") not in BRIDGE_RECEIPT_FEATURES
        and str(row.get("formula_feature_name") or "") not in WRAPPER_FEATURES
    ]
    if detailed_private_rows:
        return _dedupe_driver_rows(_sort_receipt_rows_by_contribution(detailed_private_rows))
    private_rows = [
        row
        for row in rows
        if str(row.get("component") or "") == "private_lve_value"
        and str(row.get("receipt_section_label") or "") != "Market/Liquidity"
        and str(row.get("formula_feature_name") or "") not in BRIDGE_RECEIPT_FEATURES
    ]
    if private_rows:
        return _dedupe_driver_rows(private_rows)
    return _dedupe_driver_rows(rows)


def _dedupe_driver_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_feature: dict[str, dict[str, object]] = {}
    for row in rows:
        feature = str(row.get("formula_feature_name") or "")
        current = by_feature.get(feature)
        if current is None or abs(_float(row.get("contribution"))) > abs(
            _float(current.get("contribution"))
        ):
            by_feature[feature] = row
    return _sort_receipt_rows_by_contribution(list(by_feature.values()))


def _receipt_drag_rows(
    rows: list[dict[str, object]],
    *,
    driver_count: int,
) -> list[dict[str, object]]:
    negative_rows = sorted(
        [row for row in rows if _float(row.get("contribution")) < 0],
        key=lambda row: (_float(row.get("contribution")), str(row.get("formula_feature_name"))),
    )
    if negative_rows:
        return negative_rows[:driver_count]
    warning_rows = [
        row
        for row in rows
        if row.get("imputed_flag")
        or (
            _first_view_warning(row.get("warning_reason"))
            and _float(row.get("normalized_score"), 100.0) <= 70.0
        )
    ]
    low_score_rows = [
        row
        for row in rows
        if row not in warning_rows and _float(row.get("normalized_score"), 100.0) < 60.0
    ]
    return sorted(
        warning_rows + low_score_rows,
        key=lambda row: (
            _float(row.get("normalized_score"), 100.0),
            -abs(_float(row.get("contribution"))),
            str(row.get("formula_feature_name") or ""),
        ),
    )[:driver_count]


def _bridge_receipt_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        [
            row
            for row in rows
            if str(row.get("formula_feature_name") or "") in BRIDGE_RECEIPT_FEATURES
            or str(row.get("receipt_section_label") or "") == "Young-Player Bridge Prior"
        ],
        key=lambda row: (
            0 if str(row.get("formula_feature_name") or "") == "young_nfl_bridge_prior" else 1,
            -abs(_float(row.get("contribution"))),
            str(row.get("formula_feature_name") or ""),
        ),
    )


def _market_receipt_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        [
            row
            for row in rows
            if str(row.get("receipt_section_label") or "") == "Market/Liquidity"
        ],
        key=lambda row: (
            -abs(_float(row.get("contribution"))),
            str(row.get("formula_feature_name") or ""),
        ),
    )[:5]


def receipt_rows_for_players(
    report: PlayerFeatureReceiptsReport,
    player_rows: list[dict[str, object]],
    *,
    player_column: str = "player",
    position_column: str = "position",
    include_fallback_rows: bool = True,
    page_source: str = "",
) -> list[dict[str, object]]:
    requested = [
        (
            str(row.get(player_column) or ""),
            str(row.get(position_column) or row.get("pos") or ""),
            row,
        )
        for row in player_rows
        if row.get(player_column)
    ]
    requested_keys = {
        (_normalize_receipt_match_key(player), _normalize_receipt_match_key(position))
        for player, position, _ in requested
    }
    receipt_rows = [
        row
        for row in report.rows
        if (
            _normalize_receipt_match_key(row.get("player")),
            _normalize_receipt_match_key(row.get("position")),
        )
        in requested_keys
    ]
    matched_keys = {
        (
            _normalize_receipt_match_key(row.get("player")),
            _normalize_receipt_match_key(row.get("position")),
        )
        for row in receipt_rows
    }
    if include_fallback_rows:
        for player, position, source_row in requested:
            match_key = (
                _normalize_receipt_match_key(player),
                _normalize_receipt_match_key(position),
            )
            if match_key not in matched_keys:
                receipt_rows.extend(
                    _fallback_receipt_rows(
                        player,
                        position,
                        source_row,
                        page_source=page_source,
                    )
                )
    return _sort_receipt_rows_by_contribution(receipt_rows)


def component_summary_rows_for_players(
    report: PlayerFeatureReceiptsReport,
    player_rows: list[dict[str, object]],
    *,
    player_column: str = "player",
    position_column: str = "position",
) -> list[dict[str, object]]:
    requested_keys = {
        (
            _normalize_receipt_match_key(row.get(player_column)),
            _normalize_receipt_match_key(row.get(position_column) or row.get("pos")),
        )
        for row in player_rows
        if row.get(player_column)
    }
    rows = [
        row
        for row in report.component_summary_rows
        if (
            _normalize_receipt_match_key(row.get("player")),
            _normalize_receipt_match_key(row.get("position")),
        )
        in requested_keys
    ]
    return sorted(
        rows,
        key=lambda row: (
            str(row["player"]).lower(),
            _component_priority(str(row["component"])),
        ),
    )


def build_player_feature_receipts(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> PlayerFeatureReceiptsReport:
    source_root = _resolve_veteran_model_dir(veteran_model_dir)
    stats_first_report = _build_stats_first_feature_receipts(data_pack_path, source_root)
    if stats_first_report is not None:
        return stats_first_report
    try:
        model_run = run_veteran_model_from_dir(source_root)
    except ValueError as exc:
        return PlayerFeatureReceiptsReport(
            rows=[],
            component_summary_rows=[],
            players=[],
            components=[],
            issues=[str(exc)],
            source_root=str(source_root),
        )

    report = model_run.schema_report
    data_pack_lookup = _data_pack_model_lookup(data_pack_path)
    feature_lookup = {
        (feature.player_id, feature.feature_name): feature for feature in report.feature_scores
    }
    player_lookup = {player.player_id: player for player in report.players}
    registry_lookup = {
        (definition.position, definition.feature_name): definition for definition in report.registry
    }
    source_lookup = {source.source_key: source for source in report.sources}

    receipt_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for score in model_run.scores:
        receipt_rows.extend(
            _score_receipt_rows(
                score,
                report,
                data_pack_lookup,
                player_lookup,
                feature_lookup,
                registry_lookup,
                source_lookup,
            )
        )
        summary_rows.extend(_score_component_summary_rows(score))

    receipt_rows.sort(
        key=lambda row: (
            str(row["player"]).lower(),
            _component_priority(str(row["component"])),
            int(row["receipt_order"]),
            str(row["formula_feature_name"]),
        )
    )
    summary_rows.sort(
        key=lambda row: (
            str(row["player"]).lower(),
            _component_priority(str(row["component"])),
        )
    )
    return PlayerFeatureReceiptsReport(
        rows=receipt_rows,
        component_summary_rows=summary_rows,
        players=sorted({str(row["player"]) for row in receipt_rows}),
        components=sorted({str(row["component"]) for row in receipt_rows}),
        issues=[],
        source_root=str(source_root),
    )


def _build_stats_first_feature_receipts(
    data_pack_path: str | Path,
    source_root: Path,
) -> PlayerFeatureReceiptsReport | None:
    contribution_path = source_root / STATS_FIRST_CONTRIBUTION_FILE
    normalized_path = source_root / STATS_FIRST_NORMALIZED_FEATURE_FILE
    if not contribution_path.exists() or not normalized_path.exists():
        return None
    contribution_rows = _read_dict_rows(contribution_path)
    normalized_rows = _read_dict_rows(normalized_path)
    if not contribution_rows or not normalized_rows:
        return None
    normalized_lookup = {
        str(row.get("player_id") or ""): row for row in normalized_rows if row.get("player_id")
    }
    data_pack_lookup = _data_pack_model_lookup(data_pack_path)
    lifecycle_lookup = load_active_lifecycle_lookup(source_root)
    receipt_rows: list[dict[str, object]] = []
    for order, contribution in enumerate(contribution_rows, start=1):
        player_id = str(contribution.get("player_id") or "")
        normalized = normalized_lookup.get(player_id, {})
        output_row = data_pack_lookup.get(player_id, {})
        lifecycle_row = lifecycle_from_lookup(
            {**output_row, **normalized, **contribution},
            lifecycle_lookup,
        )
        feature_name = str(contribution.get("feature_name") or "")
        raw_value = normalized.get(feature_name, "")
        is_derived = _stats_first_formula_derived_feature(feature_name)
        section = _receipt_section(feature_name, str(contribution.get("component") or ""))
        raw_feature_value = (
            contribution.get("normalized_score", "") if is_derived else raw_value
        )
        warning_reason = _stats_first_warning_reason(feature_name, normalized, is_derived)
        truth = classify_feature_truth(
            feature_name,
            normalized,
            raw_value=raw_feature_value,
            warning_reason=warning_reason,
            is_formula_derived=is_derived,
            component=contribution.get("component", ""),
        )
        receipt_rows.append(
            {
                "player_id": player_id,
                "player": contribution.get("player_name", ""),
                "position": contribution.get("position", ""),
                "asset_lifecycle": lifecycle_row.get("asset_lifecycle", ""),
                "asset_lifecycle_label": lifecycle_row.get(
                    "asset_lifecycle_label",
                    asset_lifecycle_label(lifecycle_row.get("asset_lifecycle")),
                ),
                "experience_bucket": lifecycle_row.get("experience_bucket", ""),
                "young_nfl_bridge_prior_score": lifecycle_row.get(
                    "young_nfl_bridge_prior_score", ""
                ),
                "young_nfl_bridge_weight": lifecycle_row.get("young_nfl_bridge_weight", ""),
                "young_nfl_bridge_source": lifecycle_row.get("young_nfl_bridge_source", ""),
                "receipt_section": section,
                "receipt_section_label": RECEIPT_SECTION_LABELS.get(section, section),
                "lifecycle_explanation": _lifecycle_explanation(lifecycle_row),
                "team": output_row.get("team") or normalized.get("team", ""),
                "component": contribution.get("component", ""),
                "formula_feature_name": feature_name,
                "source_feature_name": feature_name if not is_derived else "formula_derived",
                "raw_feature_value": raw_feature_value,
                "normalized_score": _float_or_text(contribution.get("normalized_score", "")),
                "feature_weight": _float_or_text(contribution.get("feature_weight", "")),
                "contribution": _float_or_text(contribution.get("component_contribution", "")),
                "component_score": _stats_first_component_score(
                    output_row,
                    str(contribution.get("component") or ""),
                ),
                "source_key": normalized.get("source_key", ""),
                "source_name": "stats-first public source backfill",
                "source_file": normalized.get("source_file", ""),
                "source_date": normalized.get("source_date", ""),
                "source_confidence": output_row.get("confidence_score", ""),
                "source_status": truth.source_status,
                "neutral_default_value": truth.neutral_default_value,
                "data_truth_warning": truth.warning_reason,
                "evidence_strength": "stats_first_model",
                "imputed_flag": truth.imputed_flag
                or _stats_first_imputed_flag(feature_name, normalized, is_derived),
                "warning_reason": truth.warning_reason or warning_reason,
                "model_usage": truth.model_usage,
                "model_version": contribution.get("model_version", ""),
                "warning_status": output_row.get("warning_status", ""),
                "receipt_order": order,
            }
        )
    summary_rows = _stats_first_component_summary_rows(receipt_rows, data_pack_lookup)
    receipt_rows.sort(
        key=lambda row: (
            str(row["player"]).lower(),
            _component_priority(str(row["component"])),
            int(row["receipt_order"]),
            str(row["formula_feature_name"]),
        )
    )
    summary_rows.sort(
        key=lambda row: (
            str(row["player"]).lower(),
            _component_priority(str(row["component"])),
        )
    )
    return PlayerFeatureReceiptsReport(
        rows=receipt_rows,
        component_summary_rows=summary_rows,
        players=sorted({str(row["player"]) for row in receipt_rows}),
        components=sorted({str(row["component"]) for row in receipt_rows}),
        issues=[],
        source_root=str(source_root),
    )


def _stats_first_component_summary_rows(
    receipt_rows: list[dict[str, object]],
    data_pack_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    by_player_component: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in receipt_rows:
        by_player_component.setdefault(
            (str(row["player_id"]), str(row["component"])),
            [],
        ).append(row)
    summary_rows: list[dict[str, object]] = []
    for (player_id, component), rows in by_player_component.items():
        output_row = data_pack_lookup.get(player_id, {})
        contribution_sum = round(
            sum(_float(row.get("contribution")) for row in rows),
            4,
        )
        component_score = _stats_first_component_score(output_row, component)
        delta = round(_float(component_score) - contribution_sum, 4)
        if abs(delta) <= 0.05:
            reconciliation_status = "matched"
        elif component == "trade_value":
            reconciliation_status = "position_liquidity_adjustment_or_clamp"
        else:
            reconciliation_status = "review_delta"
        first = rows[0]
        summary_rows.append(
            {
                "player_id": player_id,
                "player": first["player"],
                "position": first["position"],
                "component": component,
                "component_score": component_score,
                "contribution_sum": contribution_sum,
                "reconciliation_delta": delta,
                "reconciliation_status": reconciliation_status,
                "model_version": first["model_version"],
            }
        )
    return summary_rows


def _stats_first_component_score(
    output_row: dict[str, object],
    component: str,
) -> object:
    return {
        "win_now_value": output_row.get("win_now_value", ""),
        "dynasty_hold_value": output_row.get("dynasty_hold_value", ""),
        "private_lve_value": output_row.get("private_lve_value")
        or output_row.get("private_score", ""),
        "trade_value": output_row.get("trade_value", ""),
    }.get(component, "")


def _stats_first_imputed_flag(
    feature_name: str,
    normalized: dict[str, object],
    is_derived: bool,
) -> bool:
    if is_derived:
        return False
    return str(normalized.get(feature_name) or "") == ""


def _stats_first_warning_reason(
    feature_name: str,
    normalized: dict[str, object],
    is_derived: bool,
) -> str:
    warnings = str(normalized.get("warnings") or "")
    if is_derived:
        return "formula derived from displayed component features"
    if str(normalized.get(feature_name) or "") == "":
        return "missing stats-first source feature; model used neutral formula default"
    if warnings:
        return warning_summary(warnings.split("|")[0], default=warnings.split("|")[0])
    return ""


def _stats_first_formula_derived_feature(feature_name: str) -> bool:
    return feature_name in {
        "win_now_value",
        "dynasty_hold_value",
        "production_stability",
        "first_down_td_fit_capped",
        "start_gated_rushing_profile",
        "lve_structural_formula_adjustment",
        "rb_dynasty_cap",
        "wr_dynasty_cap",
        "te_route_target_penalty",
        "te_replacement_level_baseline",
        "te_no_premium_suppression",
        "qb_replacement_level_baseline",
        "qb_replacement_suppression",
        "confidence_score",
        "keeper_score",
        "private_lve_value",
        "draft_capital_prior_score",
        "young_nfl_bridge_decay_weight",
        "young_nfl_bridge_nfl_evidence_weight",
        "young_nfl_bridge_prior",
    }


def _receipt_section(feature_name: str, component: str = "") -> str:
    if component == "trade_value" and feature_name in {
        "market_liquidity",
        "market_edge",
        "trade_value",
    }:
        return "market_liquidity"
    return FEATURE_RECEIPT_SECTIONS.get(feature_name, "nfl_production")


def _lifecycle_explanation(row: dict[str, object]) -> str:
    lifecycle = str(row.get("asset_lifecycle") or "")
    label = str(row.get("asset_lifecycle_label") or "") or (
        asset_lifecycle_label(lifecycle) if lifecycle else ""
    )
    experience_bucket = _experience_bucket_label(row.get("experience_bucket"))
    bridge_weight = _bridge_weight_percent(row.get("young_nfl_bridge_weight"))
    if is_young_nfl_bridge_lifecycle(lifecycle):
        nfl_weight = max(0.0, 100.0 - bridge_weight)
        return (
            "This player is being treated as a young NFL bridge asset because "
            f"he is classified as {experience_bucket}. Draft/prospect prior is "
            f"shown separately and currently carries about {bridge_weight:.0f}% "
            f"of the bridge blend, while NFL evidence carries about {nfl_weight:.0f}%."
        )
    if lifecycle == "incoming_rookie":
        return (
            "This player is being treated as an incoming rookie; rookie/prospect "
            "context drives the value until NFL production and role evidence exists."
        )
    if lifecycle == "released_veteran":
        return (
            "This player is being treated as a released veteran; NFL evidence drives "
            "private value, while availability and market/liquidity explain acquisition context."
        )
    if lifecycle == "free_agent":
        return (
            "This player is being treated as a free agent; NFL evidence drives value, "
            "with availability and confidence warnings kept separate from talent."
        )
    if label:
        return (
            f"This player is being treated as {label.lower()}; current NFL stats, "
            "role, age, injury, projection, and liquidity receipts explain the score."
        )
    return (
        "This receipt separates current NFL evidence, projection, age/injury, "
        "young-player prior, and market/liquidity so the score can be audited."
    )


def _experience_bucket_label(value: object) -> str:
    text = str(value or "").strip()
    return {
        "true_rookie": "a true rookie",
        "year_one_nfl_player": "a year-one NFL player",
        "year_two_nfl_player": "a year-two NFL player",
        "year_three_nfl_player": "a year-three NFL player",
        "established_veteran": "an established veteran",
    }.get(text, text.replace("_", " ") if text else "a young NFL bucket")


def _bridge_weight_percent(value: object) -> float:
    weight = _float(value, 0.0)
    if 0.0 < weight <= 1.0:
        return weight * 100.0
    return weight


def _read_dict_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float_or_text(value: object) -> object:
    try:
        text = str(value)
        if text == "":
            return ""
        return float(text)
    except (TypeError, ValueError):
        return value


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _sort_receipt_rows_by_contribution(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("player") or "").lower(),
            -abs(_float(row.get("contribution"))),
            _component_priority(str(row.get("component") or "")),
            str(row.get("formula_feature_name") or ""),
        ),
    )


def _compact_driver_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "Section": row.get("receipt_section_label", ""),
            "Driver": _feature_label(row.get("formula_feature_name")),
            "Score": row.get("normalized_score", ""),
            "Weight": row.get("feature_weight", ""),
            "Contribution": row.get("contribution", ""),
            "Warning": _first_view_warning(row.get("warning_reason")),
        }
        for row in rows
    ]


def _feature_label(value: object) -> str:
    text = str(value or "").strip()
    labels = {
        "weighted_recent_lve_ppg_score": "Recent LVE scoring",
        "expected_lve_points_score": "Expected LVE points",
        "lve_projection_value": "Projection value",
        "role_security": "Role security",
        "workload_earning": "Workload earning",
        "target_earning_stability": "Target earning",
        "route_share_stability": "Route share stability",
        "route_role": "Route role",
        "efficiency_score": "Efficiency",
        "first_down_td_fit": "First-down/TD fit",
        "first_down_td_fit_capped": "First-down/TD fit cap",
        "age_curve": "Age window",
        "injury_durability": "Injury durability",
        "position_replaceability": "Position replaceability",
        "lve_structural_formula_adjustment": "LVE structural adjustment",
        "draft_capital_prior_score": "Draft/prospect prior",
        "young_nfl_bridge_prior": "Young-player bridge contribution",
        "young_nfl_bridge_decay_weight": "Bridge prior weight",
        "young_nfl_bridge_nfl_evidence_weight": "NFL evidence weight",
        "market_liquidity": "Trade market liquidity",
        "market_edge": "Model vs market",
        "trade_value": "Trade value",
        "visible_stats_value": "Visible model value",
        "confidence": "Confidence",
        "why_available": "Why available",
    }
    return labels.get(text, text.replace("_", " ").strip().title())


def _first_view_warning(value: object) -> str:
    text = str(value or "").strip()
    if not text or text == FORMULA_DERIVED_WARNING:
        return ""
    if text == "missing stats-first source feature; model used neutral formula default":
        return "Missing stats-first feature; neutral default used."
    return warning_summary(text, default=text)


def _first_non_empty(values: list[object]) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _unique_non_empty(values: list[object]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def _fallback_receipt_rows(
    player: str,
    position: str,
    row: dict[str, object],
    *,
    page_source: str,
) -> list[dict[str, object]]:
    component = str(row.get("component") or "visible_board_score")
    source_file = str(row.get("source") or row.get("source_file") or page_source)
    warning = str(
        row.get("warning")
        or row.get("warning_reason")
        or row.get("warning_status")
        or ""
    )
    stats_value = _first_present(
        row.get("stats_model_value"),
        row.get("stats_value"),
        row.get("model_value"),
        row.get("draft_value"),
        row.get("acquisition_value"),
        row.get("keeper_score"),
    )
    lifecycle_label = str(
        row.get("asset_lifecycle_label")
        or row.get("asset_lifecycle")
        or ""
    )
    lifecycle_row = {
        "asset_lifecycle": str(row.get("asset_lifecycle") or ""),
        "asset_lifecycle_label": lifecycle_label,
        "experience_bucket": str(row.get("experience_bucket") or ""),
        "young_nfl_bridge_weight": row.get("young_nfl_bridge_weight", ""),
    }
    fallback_rows = [
        _fallback_receipt_row(
            player,
            position,
            asset_lifecycle_label=lifecycle_label,
            lifecycle_explanation=_lifecycle_explanation(lifecycle_row),
            component=component,
            feature_name="visible_stats_value",
            value=stats_value,
            weight=100,
            contribution=_float(stats_value),
            source_file=source_file,
            warning=warning,
            imputed=stats_value in (None, ""),
        )
    ]
    for feature_name, value in (
        ("market_edge", row.get("market_edge")),
        ("confidence", row.get("confidence")),
        ("why_available", row.get("why_available")),
    ):
        if value not in (None, ""):
            fallback_rows.append(
                _fallback_receipt_row(
                    player,
                    position,
                    asset_lifecycle_label=lifecycle_label,
                    lifecycle_explanation=_lifecycle_explanation(lifecycle_row),
                    component="display_context",
                    feature_name=feature_name,
                    value=value,
                    weight=0,
                    contribution=0,
                    source_file=source_file,
                    warning=warning if feature_name == "confidence" else "",
                    imputed=False,
                )
            )
    return fallback_rows


def _fallback_receipt_row(
    player: str,
    position: str,
    *,
    asset_lifecycle_label: str = "",
    lifecycle_explanation: str = "",
    component: str,
    feature_name: str,
    value: object,
    weight: float,
    contribution: float,
    source_file: str,
    warning: str,
    imputed: bool,
) -> dict[str, object]:
    section = _receipt_section(feature_name, component)
    return {
        "player_id": "",
        "player": player,
        "position": position,
        "asset_lifecycle_label": asset_lifecycle_label,
        "receipt_section": section,
        "receipt_section_label": RECEIPT_SECTION_LABELS.get(section, section),
        "lifecycle_explanation": lifecycle_explanation,
        "team": "",
        "component": component,
        "formula_feature_name": feature_name,
        "source_feature_name": feature_name,
        "raw_feature_value": "" if value is None else value,
        "normalized_score": "" if value is None else value,
        "feature_weight": weight,
        "contribution": round(contribution, 4),
        "component_score": "" if value is None else value,
        "source_key": "",
        "source_name": "visible page row",
        "source_file": source_file,
        "source_date": "",
        "source_confidence": "",
        "evidence_strength": "display_fallback",
        "imputed_flag": imputed,
        "warning_reason": warning,
        "model_version": "",
        "warning_status": warning,
        "receipt_order": 999,
    }


def _first_present(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def _normalize_receipt_match_key(value: object) -> str:
    suffix_tokens = {"jr", "sr", "ii", "iii", "iv", "v"}
    normalized = (
        str(value or "")
        .replace(".", " ")
        .replace("'", "")
        .replace("-", " ")
    )
    tokens = [
        "".join(character.lower() for character in token if character.isalnum())
        for token in normalized.split()
    ]
    tokens = [token for token in tokens if token]
    while tokens and tokens[-1] in suffix_tokens:
        tokens.pop()
    return "".join(tokens)


def _score_receipt_rows(
    score: VeteranScore,
    report: VeteranSchemaReport,
    data_pack_lookup: dict[str, dict[str, object]],
    player_lookup: dict[str, object],
    feature_lookup: dict[tuple[str, str], VeteranFeatureScore],
    registry_lookup: dict[tuple[str, str], VeteranFeatureDefinition],
    source_lookup: dict[str, VeteranSourceRow],
) -> list[dict[str, object]]:
    output_row = data_pack_lookup.get(score.player_id, {})
    player_row = player_lookup.get(score.player_id)
    rows: list[dict[str, object]] = []
    for contribution in score.contributions:
        source_feature_name = _source_feature_name(
            score.position.value,
            contribution.component,
            contribution.feature_name,
        )
        if (
            contribution.feature_name not in {"keeper_score", "confidence_score"}
            and (score.player_id, contribution.feature_name) in feature_lookup
        ):
            source_feature_name = contribution.feature_name
        feature_row = feature_lookup.get((score.player_id, source_feature_name))
        source_row = source_lookup.get(feature_row.source_key) if feature_row else None
        registry_row = registry_lookup.get((score.position.value, source_feature_name))
        imputed_flag, warning_reason = _receipt_warning(
            contribution.feature_name,
            source_feature_name,
            feature_row,
        )
        lifecycle_row = {
            "asset_lifecycle": output_row.get("asset_lifecycle", ""),
            "asset_lifecycle_label": output_row.get("asset_lifecycle_label", ""),
            "experience_bucket": output_row.get("experience_bucket", ""),
            "young_nfl_bridge_weight": output_row.get("young_nfl_bridge_weight", ""),
        }
        section = _receipt_section(contribution.feature_name, contribution.component)
        rows.append(
            {
                "player_id": score.player_id,
                "player": score.player_name,
                "position": score.position.value,
                "asset_lifecycle": output_row.get("asset_lifecycle", ""),
                "asset_lifecycle_label": output_row.get("asset_lifecycle_label", ""),
                "experience_bucket": output_row.get("experience_bucket", ""),
                "young_nfl_bridge_prior_score": output_row.get(
                    "young_nfl_bridge_prior_score", ""
                ),
                "young_nfl_bridge_weight": output_row.get("young_nfl_bridge_weight", ""),
                "young_nfl_bridge_source": output_row.get("young_nfl_bridge_source", ""),
                "receipt_section": section,
                "receipt_section_label": RECEIPT_SECTION_LABELS.get(section, section),
                "lifecycle_explanation": _lifecycle_explanation(lifecycle_row),
                "team": output_row.get("team") or getattr(player_row, "team_name", ""),
                "component": contribution.component,
                "formula_feature_name": contribution.feature_name,
                "source_feature_name": source_feature_name,
                "raw_feature_value": _raw_feature_value(feature_row, contribution),
                "normalized_score": contribution.normalized_score,
                "feature_weight": contribution.feature_weight,
                "contribution": contribution.component_contribution,
                "component_score": _component_score(score, contribution.component),
                "source_key": feature_row.source_key if feature_row else "",
                "source_name": source_row.source_name if source_row else "",
                "source_file": _source_file(report, source_row),
                "source_date": _source_date(feature_row, source_row),
                "source_confidence": feature_row.source_confidence if feature_row else "",
                "evidence_strength": registry_row.evidence_strength if registry_row else "",
                "imputed_flag": imputed_flag,
                "warning_reason": warning_reason,
                "model_version": score.model_version,
                "warning_status": score.warning_status,
                "receipt_order": _receipt_order(source_feature_name, contribution.feature_name),
            }
        )
    return rows


def _score_component_summary_rows(score: VeteranScore) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    components = sorted({contribution.component for contribution in score.contributions})
    for component in components:
        contribution_sum = round(
            sum(
                contribution.component_contribution
                for contribution in score.contributions
                if contribution.component == component
            ),
            4,
        )
        component_score = _component_score(score, component)
        delta = round(component_score - contribution_sum, 4)
        if abs(delta) <= 0.05:
            reconciliation_status = "matched"
        elif component == "trade_value":
            reconciliation_status = "position_liquidity_adjustment_or_clamp"
        else:
            reconciliation_status = "review_delta"
        rows.append(
            {
                "player_id": score.player_id,
                "player": score.player_name,
                "position": score.position.value,
                "asset_lifecycle_label": "",
                "component": component,
                "component_score": component_score,
                "contribution_sum": contribution_sum,
                "reconciliation_delta": delta,
                "reconciliation_status": reconciliation_status,
                "model_version": score.model_version,
            }
        )
    return rows


def _resolve_veteran_model_dir(veteran_model_dir: str | Path | None) -> Path:
    if veteran_model_dir is not None:
        return Path(veteran_model_dir).resolve()
    if (DEFAULT_RECEIPT_VETERAN_MODEL_DIR / FEATURE_SCORE_FILE).exists():
        return DEFAULT_RECEIPT_VETERAN_MODEL_DIR.resolve()
    return FALLBACK_RECEIPT_VETERAN_MODEL_DIR.resolve()


def _data_pack_model_lookup(data_pack_path: str | Path) -> dict[str, dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return {}
    return {
        str(row.get("player_id") or ""): row
        for row in validated.rows_by_table.get("model_outputs", [])
        if row.get("player_id")
    }


def _source_feature_name(position: str, component: str, feature_name: str) -> str:
    if feature_name in {"keeper_score", "confidence_score"}:
        return feature_name
    if feature_name in STATS_FIRST_FEATURE_PRIORITY:
        return feature_name
    if component == "trade_value" and feature_name == "market_liquidity_proxy":
        return "market_liquidity"
    fallbacks: dict[str, dict[str, str]] = {
        "QB": {
            "start_security": "role_security",
            "passing_td_yardage_output": "lve_projection_value",
            "rushing_value": "position_replaceability",
            "passing_efficiency_epa": "lve_projection_value",
            "sack_avoidance": "role_security",
            "age_curve_archetype": "age_curve",
            "current_injury_durability": "injury_durability",
            "age_window": "age_curve",
            "health_stability": "injury_durability",
            "skill_portability": "lve_projection_value",
            "team_commitment": "role_security",
        },
        "RB": {
            "touch_share": "role_security",
            "high_value_touches": "first_down_td_fit",
            "goal_line_short_yardage_role": "first_down_td_fit",
            "receiving_role_no_ppr_adjusted": "lve_projection_value",
            "rush_efficiency_creation": "lve_projection_value",
            "first_down_conversion_profile": "first_down_td_fit",
            "offense_environment_line": "lve_projection_value",
            "age_window": "age_curve",
            "health_stability": "injury_durability",
            "skill_portability": "role_security",
            "team_commitment": "role_security",
        },
        "WR": {
            "target_share": "target_earning_stability",
            "route_participation": "role_security",
            "targets_per_route_run": "target_earning_stability",
            "yards_per_route_run": "lve_projection_value",
            "first_downs_per_route": "target_earning_stability",
            "get_open_role_robustness": "role_security",
            "td_area_air_yards_role": "lve_projection_value",
            "offense_environment": "lve_projection_value",
            "age_window": "age_curve",
            "health_stability": "injury_durability",
            "skill_portability": "target_earning_stability",
            "team_commitment": "role_security",
        },
        "TE": {
            "route_participation": "route_share_stability",
            "target_earning": "lve_projection_value",
            "yards_per_route_run": "lve_projection_value",
            "blocking_suppression_inverse": "position_replaceability",
            "td_area_adot_role": "lve_projection_value",
            "first_down_profile": "route_share_stability",
            "offense_environment": "lve_projection_value",
            "age_window": "age_curve",
            "health_stability": "injury_durability",
            "skill_portability": "lve_projection_value",
            "team_commitment": "role_security",
        },
    }
    return fallbacks.get(position, {}).get(feature_name, feature_name)


def _receipt_warning(
    formula_feature_name: str,
    source_feature_name: str,
    feature_row: VeteranFeatureScore | None,
) -> tuple[bool, str]:
    if formula_feature_name in {"keeper_score", "confidence_score"}:
        return False, warning_summary("derived_component_input", default="")
    if feature_row is None:
        return True, warning_summary("missing_source_feature_uses_formula_default", default="")
    if feature_row.is_missing:
        return True, warning_summary(
            feature_row.missing_reason or "source_feature_marked_missing",
            default="",
        )
    if formula_feature_name != source_feature_name:
        return False, warning_summary(f"formula_proxy_from_{source_feature_name}", default="")
    return False, ""


def _raw_feature_value(
    feature_row: VeteranFeatureScore | None,
    contribution: object,
) -> object:
    if feature_row is None:
        return ""
    return feature_row.normalized_score if feature_row.normalized_score is not None else ""


def _source_file(report: VeteranSchemaReport, source_row: VeteranSourceRow | None) -> str:
    if source_row and source_row.local_path:
        return source_row.local_path
    return str(report.data_dir / FEATURE_SCORE_FILE)


def _source_date(
    feature_row: VeteranFeatureScore | None,
    source_row: VeteranSourceRow | None,
) -> str:
    if source_row and source_row.source_date:
        return source_row.source_date
    if feature_row:
        return feature_row.snapshot_date
    return ""


def _component_score(score: VeteranScore, component: str) -> float:
    values = {
        "veteran_base_value": score.veteran_base_value,
        "horizon_retention_score": score.horizon_retention_score,
        "lve_format_fit": score.lve_format_fit,
        "trade_value": score.trade_value,
    }
    return values.get(component, 0.0)


def _receipt_order(source_feature_name: str, formula_feature_name: str) -> int:
    if source_feature_name in STATS_FIRST_FEATURE_PRIORITY:
        return STATS_FIRST_FEATURE_PRIORITY.index(source_feature_name)
    return 100 + sum(ord(char) for char in formula_feature_name[:8])


def _component_priority(component: str) -> int:
    try:
        return COMPONENT_PRIORITY.index(component)
    except ValueError:
        return len(COMPONENT_PRIORITY)
