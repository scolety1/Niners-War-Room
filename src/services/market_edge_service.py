from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.market_influence_policy_service import (
    first_market_value,
    market_edge_classification,
    market_edge_label,
    market_edge_view,
    market_status_warning,
    market_value_status,
    safe_market_edge_score,
)
from src.services.warning_language_service import warning_summary


@dataclass(frozen=True)
class MarketEdgeReport:
    rows: list[dict[str, object]]
    model_higher_rows: list[dict[str, object]]
    market_higher_rows: list[dict[str, object]]
    classification_rows: list[dict[str, object]]
    issues: list[str]


def build_market_edge_report(data_pack_path: str | Path) -> MarketEdgeReport:
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return MarketEdgeReport(
            rows=[],
            model_higher_rows=[],
            market_higher_rows=[],
            classification_rows=[],
            issues=["Data pack validation errors block market-edge review."],
        )

    roster_lookup = _roster_lookup(validated.rows_by_table.get("rosters", []))
    rows = [
        _edge_row(output_row, roster_lookup.get(str(output_row.get("player_id") or ""), {}))
        for output_row in validated.rows_by_table.get("model_outputs", [])
        if output_row.get("player_id")
    ]
    rows = sorted(
        rows,
        key=lambda row: (
            str(row["edge_view"]),
            -abs(float(row["market_edge_score"] or 0.0)),
            str(row["player"]),
        ),
    )
    model_higher_rows = sorted(
        [
            row
            for row in rows
            if row["edge_view"] == "model_higher_than_market"
        ],
        key=lambda row: (-float(row["market_edge_score"] or 0.0), str(row["player"])),
    )
    market_higher_rows = sorted(
        [
            row
            for row in rows
            if row["edge_view"] == "market_higher_than_model"
        ],
        key=lambda row: (float(row["market_edge_score"] or 0.0), str(row["player"])),
    )
    return MarketEdgeReport(
        rows=rows,
        model_higher_rows=model_higher_rows,
        market_higher_rows=market_higher_rows,
        classification_rows=_classification_rows(rows),
        issues=[],
    )


def _edge_row(
    output_row: dict[str, object],
    roster_row: dict[str, object],
) -> dict[str, object]:
    private_value = _first_float(
        output_row,
        "private_lve_value",
        "private_score",
        "veteran_base_value",
    )
    market_trade_value = _first_float(
        output_row,
        "market_trade_value",
        "market_score",
        "trade_liquidity",
    )
    market_status = market_value_status(output_row)
    if market_trade_value is None:
        market_trade_value = first_market_value(output_row)
    safe_edge = safe_market_edge_score(
        private_value,
        market_trade_value,
        market_status,
        explicit_edge=output_row.get("market_edge_score"),
    )
    edge = safe_edge if safe_edge is not None else 0.0
    missing_reason = _missing_reason(private_value, market_trade_value, market_status)
    label = market_edge_classification(market_status, safe_edge)
    if missing_reason in {"missing_private_and_market_values", "missing_private_value"}:
        label = "missing_market_inputs"
    if market_status == "real_imported_market" and safe_edge is not None:
        label = str(output_row.get("market_edge_label") or market_edge_label(edge))
    warning_status = str(output_row.get("warning_status") or "")
    warning_reasons = str(output_row.get("warning_reasons") or "")
    raw_edge_warning = _edge_warning(
        output_row,
        warning_status,
        warning_reasons,
        missing_reason,
    )
    confidence = _first_float(output_row, "confidence_score", default=0.0) or 0.0
    edge_confidence = _edge_confidence(confidence, warning_status, missing_reason)
    return {
        "player_id": output_row.get("player_id", ""),
        "player": output_row.get("player_name", ""),
        "position": output_row.get("position", roster_row.get("position", "")),
        "team": roster_row.get("team_name", ""),
        "private_lve_value": private_value if private_value is not None else "",
        "market_trade_value": market_trade_value if market_trade_value is not None else "",
        "market_edge_score": edge,
        "market_value_status": market_status,
        "edge_classification": label,
        "edge_view": (
            "missing_market_inputs"
            if label == "missing_market_inputs"
            else market_edge_view(market_status, safe_edge)
        ),
        "edge_confidence": edge_confidence,
        "edge_confidence_label": _edge_confidence_label(edge_confidence),
        "confidence_score": confidence,
        "warning_status": warning_status,
        "warning_reasons": warning_reasons,
        "source_warning": warning_summary(raw_edge_warning, default="No source warning."),
        "raw_source_warning": raw_edge_warning,
        "warning_summary": warning_summary(warning_reasons, warning_status),
        "model_version": output_row.get("model_version", ""),
        "computed_at": output_row.get("computed_at", ""),
        "notes": output_row.get("notes", ""),
    }


def _roster_lookup(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("player_id") or ""): row
        for row in rows
        if row.get("player_id")
    }


def _classification_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    labels = sorted({str(row["edge_classification"]) for row in rows})
    return [
        {
            "edge_classification": label,
            "rows": sum(1 for row in rows if row["edge_classification"] == label),
            "review_rows": sum(
                1
                for row in rows
                if row["edge_classification"] == label
                and row["edge_confidence"] != "usable_edge"
            ),
            "meaning": _classification_meaning(label),
        }
        for label in labels
    ]


def _classification_meaning(label: str) -> str:
    return {
        "strong_positive_edge_model_higher": (
            "Model is far higher than market; inspect as a possible buy or hold edge."
        ),
        "positive_edge_model_higher": "Model is higher than market; check receipts before acting.",
        "near_market": "Model and market are roughly aligned.",
        "negative_edge_market_higher": "Market is higher than model; possible sell/shop signal.",
        "strong_negative_edge_market_higher": (
            "Market is far higher than model; inspect as a major sell/liquidity edge."
        ),
        "missing_market_inputs": "Private or market value is missing; edge is not usable.",
        "missing_market": "Market value is missing; edge is not usable.",
        "neutral_market_placeholder": (
            "Market value is only a neutral placeholder; do not treat edge as real."
        ),
        "disabled_market": "Market value is disabled for this row.",
        "stale_market": "Market value is stale; review before using the edge.",
    }.get(label, "Review edge classification.")


def _edge_confidence(confidence: float, warning_status: str, missing_reason: str) -> str:
    if missing_reason:
        return "blocked_missing_inputs"
    if confidence < 65 or warning_status in {"blocking", "review_needed"}:
        return "review_before_action"
    if confidence < 75 or warning_status in {"model_warning", "data_warning"}:
        return "usable_with_source_warning"
    return "usable_edge"


def _edge_confidence_label(edge_confidence: str) -> str:
    return {
        "blocked_missing_inputs": "blocked by missing inputs",
        "review_before_action": "review before action",
        "usable_with_source_warning": "usable with source warning",
        "usable_edge": "usable edge",
    }.get(edge_confidence, edge_confidence.replace("_", " "))


def _edge_warning(
    row: dict[str, object],
    warning_status: str,
    warning_reasons: str,
    missing_reason: str,
) -> str:
    if missing_reason:
        return missing_reason
    status_warning = market_status_warning(
        market_value_status(row),
    )
    if status_warning != "none":
        return status_warning
    explicit = str(row.get("market_edge_warning") or "")
    if explicit:
        return explicit
    if warning_reasons:
        return warning_reasons
    if warning_status:
        return warning_status
    return "none"


def _missing_reason(
    private_value: float | None,
    market_trade_value: float | None,
    market_status: str = "",
) -> str:
    if private_value is None and market_trade_value is None:
        return "missing_private_and_market_values"
    if private_value is None:
        return "missing_private_value"
    if market_trade_value is None:
        return "missing_market_trade_value"
    if market_status in {
        "missing_market",
        "disabled_market",
        "neutral_market_placeholder",
    }:
        return market_status
    return ""


def _first_float(
    row: dict[str, object],
    *keys: str,
    default: float | None = None,
) -> float | None:
    for key in keys:
        value = row.get(key)
        if value in {None, ""}:
            continue
        try:
            return float(str(value))
        except (TypeError, ValueError):
            continue
    return default
