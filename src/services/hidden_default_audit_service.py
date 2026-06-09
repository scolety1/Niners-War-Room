from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.feature_data_truth_contract_service import (
    SOURCE_DERIVED_REAL_DATA,
    SOURCE_IMPORTED_REAL_DATA,
    SOURCE_MANUAL_REVIEW,
    SOURCE_NEUTRAL_IMPUTATION,
)
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    FORMULA_DERIVED_WARNING,
    build_player_feature_receipts,
)

DEFAULT_VALUES = (50.0, 75.0, 76.0, 78.0)
DEFAULT_VALUE_EPSILON = 0.001

PRIVATE_VALUE_COMPONENTS = {
    "private_lve_value",
    "win_now_value",
    "dynasty_hold_value",
    "veteran_base_value",
    "horizon_retention_score",
    "lve_format_fit",
}
KEEPER_DROP_TRADE_COMPONENTS = {
    "keeper_score",
    "drop_candidate_score",
    "trade_value",
    "private_lve_value",
    "win_now_value",
    "dynasty_hold_value",
}
TRADE_ONLY_FEATURES = {"market_liquidity", "market_trade_value", "market_edge"}
MISSING_OR_DEFAULT_MARKERS = (
    "missing",
    "neutral",
    "default",
    "local_baseline",
    "not independent",
    "source not imported",
)


@dataclass(frozen=True)
class HiddenDefaultAuditReport:
    rows: tuple[dict[str, object], ...]
    unsafe_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]


def build_hidden_default_audit(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path = DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
) -> HiddenDefaultAuditReport:
    """Scan active receipts for default-looking values and classify their risk."""

    receipt_report = build_player_feature_receipts(
        data_pack_path,
        veteran_model_dir=veteran_model_dir,
    )
    rows = hidden_default_audit_rows_from_receipts(receipt_report.rows)
    unsafe_rows = tuple(row for row in rows if row["default_bucket"] == "unsafe_hidden_evidence")
    summary_rows = _summary_rows(rows)
    return HiddenDefaultAuditReport(
        rows=tuple(rows),
        unsafe_rows=unsafe_rows,
        summary_rows=tuple(summary_rows),
    )


def hidden_default_audit_rows_from_receipts(
    receipt_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    aggregate: dict[tuple[object, ...], dict[str, object]] = {}
    examples: dict[tuple[object, ...], list[str]] = defaultdict(list)
    for receipt in receipt_rows:
        feature = str(receipt.get("formula_feature_name") or "")
        default_value = _default_value_hit(receipt)
        if default_value is None:
            continue
        bucket = _default_bucket(receipt)
        source_status = str(receipt.get("source_status") or "")
        component = str(receipt.get("component") or "")
        why_used = _why_used(receipt, bucket)
        key = (
            feature,
            default_value,
            bucket,
            source_status,
            component,
            why_used,
        )
        if key not in aggregate:
            aggregate[key] = {
                "feature": feature,
                "default_value": _format_default(default_value),
                "default_bucket": bucket,
                "why_used": why_used,
                "source_status": source_status,
                "confidence_impact": _confidence_impact(bucket, receipt),
                "affects_private_value": _affects_private_value(receipt),
                "affects_keeper_drop_trade_value": _affects_keeper_drop_trade(receipt),
                "component": component,
                "model_usage": receipt.get("model_usage", ""),
                "row_count": 0,
                "example_players": "",
                "patch_required": bucket == "unsafe_hidden_evidence",
            }
        aggregate[key]["row_count"] = int(aggregate[key]["row_count"]) + 1
        if len(examples[key]) < 5:
            player = str(receipt.get("player") or "").strip()
            if player and player not in examples[key]:
                examples[key].append(player)

    rows = []
    for key, row in aggregate.items():
        row["example_players"] = "|".join(examples[key])
        rows.append(row)
    rows.sort(
        key=lambda row: (
            _bucket_sort(str(row["default_bucket"])),
            str(row["feature"]),
            float(row["default_value"]),
            str(row["component"]),
        )
    )
    return rows


def write_hidden_default_audit_csv(path: str | Path, rows: list[dict[str, object]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "feature",
        "default_value",
        "default_bucket",
        "why_used",
        "source_status",
        "confidence_impact",
        "affects_private_value",
        "affects_keeper_drop_trade_value",
        "component",
        "model_usage",
        "row_count",
        "example_players",
        "patch_required",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _default_value_hit(receipt: dict[str, object]) -> float | None:
    for field in ("neutral_default_value", "normalized_score", "raw_feature_value"):
        value = receipt.get(field, "")
        if _blank(value):
            continue
        default = _matching_default(value)
        if default is not None:
            return default
    return None


def _matching_default(value: object) -> float | None:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    for default in DEFAULT_VALUES:
        if abs(parsed - default) <= DEFAULT_VALUE_EPSILON:
            return default
    return None


def _default_bucket(receipt: dict[str, object]) -> str:
    source_status = str(receipt.get("source_status") or "")
    source_feature = str(receipt.get("source_feature_name") or "")
    warning = _combined_warning(receipt).lower()
    feature = str(receipt.get("formula_feature_name") or "")
    if source_feature == "formula_derived" or FORMULA_DERIVED_WARNING in warning:
        return "formula_fallback"
    if source_status == SOURCE_NEUTRAL_IMPUTATION or _truthy(receipt.get("imputed_flag")):
        return "safe_neutral_imputation"
    if source_status == SOURCE_MANUAL_REVIEW:
        return "optional_review_input"
    if feature in TRADE_ONLY_FEATURES:
        return "optional_review_input"
    if source_status in {SOURCE_IMPORTED_REAL_DATA, SOURCE_DERIVED_REAL_DATA} and any(
        marker in warning for marker in MISSING_OR_DEFAULT_MARKERS
    ):
        return "unsafe_hidden_evidence"
    return "optional_review_input"


def _why_used(receipt: dict[str, object], bucket: str) -> str:
    reason = _combined_warning(receipt)
    if reason:
        return reason
    if bucket == "formula_fallback":
        return "formula fallback from displayed component features"
    if bucket == "safe_neutral_imputation":
        return "neutral imputation exposed in receipts"
    if bucket == "optional_review_input":
        return "default-like value appears in an optional/review context"
    return "default-like value is marked as real evidence despite missing/default warning"


def _confidence_impact(bucket: str, receipt: dict[str, object]) -> str:
    if bucket == "unsafe_hidden_evidence":
        return "patch required; default could receive evidence credit"
    if bucket == "safe_neutral_imputation":
        return "confidence penalty or imputed warning retained"
    if bucket == "optional_review_input":
        return "review warning retained; no source credit upgrade"
    if str(receipt.get("formula_feature_name") or "") in TRADE_ONLY_FEATURES:
        return "trade/liquidity only; private value unaffected"
    return "formula fallback visible; inspect through contribution receipts"


def _affects_private_value(receipt: dict[str, object]) -> bool:
    component = str(receipt.get("component") or "")
    feature = str(receipt.get("formula_feature_name") or "")
    if feature in TRADE_ONLY_FEATURES:
        return False
    return component in PRIVATE_VALUE_COMPONENTS


def _affects_keeper_drop_trade(receipt: dict[str, object]) -> bool:
    component = str(receipt.get("component") or "")
    feature = str(receipt.get("formula_feature_name") or "")
    return component in KEEPER_DROP_TRADE_COMPONENTS or feature in TRADE_ONLY_FEATURES


def _combined_warning(receipt: dict[str, object]) -> str:
    warnings = [
        str(receipt.get("data_truth_warning") or "").strip(),
        str(receipt.get("warning_reason") or "").strip(),
    ]
    return "; ".join(warning for warning in warnings if warning)


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row["default_bucket"])] += int(row["row_count"])
    return [
        {"default_bucket": bucket, "row_count": counts[bucket]}
        for bucket in sorted(counts, key=_bucket_sort)
    ]


def _bucket_sort(bucket: str) -> int:
    return {
        "unsafe_hidden_evidence": 0,
        "safe_neutral_imputation": 1,
        "optional_review_input": 2,
        "formula_fallback": 3,
    }.get(bucket, 99)


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def _blank(value: object) -> bool:
    return str(value or "").strip() == ""


def _format_default(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)
