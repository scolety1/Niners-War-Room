from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_war_board
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    FORMULA_DERIVED_WARNING,
    build_player_feature_receipts,
)
from src.services.warning_language_service import warning_summary

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

NAMED_AUDIT_PAIRS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "BTJ vs Luther Burden",
        ("Brian Thomas Jr.", "Brian Thomas", "BTJ"),
        ("Luther Burden",),
    ),
    ("Luther Burden vs Chase Brown", ("Luther Burden",), ("Chase Brown",)),
    (
        "Kaleb Johnson vs older fragile RB",
        ("Kaleb Johnson",),
        ("Derrick Henry", "Alvin Kamara", "Austin Ekeler", "Joe Mixon", "Kyren Williams"),
    ),
    ("JSN vs Tee Higgins", ("Jaxon Smith-Njigba", "JSN"), ("Tee Higgins",)),
    ("Kyren vs Bijan", ("Kyren Williams",), ("Bijan Robinson",)),
    ("Kyren vs Gibbs", ("Kyren Williams",), ("Jahmyr Gibbs",)),
    ("Kyren vs Jeanty", ("Kyren Williams",), ("Ashton Jeanty",)),
)


@dataclass(frozen=True)
class NamedPlayerAuditReport:
    player_rows: list[dict[str, object]]
    pair_rows: list[dict[str, object]]
    pair_detail_rows: list[dict[str, object]]
    receipt_rows: list[dict[str, object]]
    players: list[str]
    issues: list[str]


def build_named_player_audit(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> NamedPlayerAuditReport:
    validated = validate_data_pack(data_pack_path)
    if validated.has_errors:
        return NamedPlayerAuditReport(
            player_rows=[],
            pair_rows=[],
            pair_detail_rows=[],
            receipt_rows=[],
            players=[],
            issues=["Active data pack has validation errors; named audit is unavailable."],
        )

    output_rows = [
        dict(row)
        for row in build_war_board(data_pack_path).rows
        if row.get("player_id") and (row.get("player") or row.get("player_name"))
    ]
    receipt_report = build_player_feature_receipts(
        data_pack_path,
        veteran_model_dir=veteran_model_dir or DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    )
    receipt_lookup = _receipt_lookup(receipt_report.rows)
    player_rows = [_audit_player_row(row, receipt_lookup) for row in output_rows]
    row_lookup = {str(row["player_id"]): row for row in player_rows}

    pair_rows: list[dict[str, object]] = []
    pair_detail_rows: list[dict[str, object]] = []
    for pair_label, left_aliases, right_aliases in NAMED_AUDIT_PAIRS:
        left = _resolve_player(output_rows, left_aliases)
        right = _resolve_player(output_rows, right_aliases)
        pair_row = _pair_row(pair_label, left, right, row_lookup)
        pair_rows.append(pair_row)
        for side, source in (("A", left), ("B", right)):
            if source is None:
                continue
            detail = dict(row_lookup.get(str(source["player_id"]), {}))
            if not detail:
                continue
            detail.update({"pair": pair_label, "side": side})
            pair_detail_rows.append(detail)

    return NamedPlayerAuditReport(
        player_rows=sorted(
            player_rows,
            key=lambda row: (
                _rank_sort(row.get("rank")),
                str(row.get("player") or "").lower(),
            ),
        ),
        pair_rows=pair_rows,
        pair_detail_rows=pair_detail_rows,
        receipt_rows=_named_receipt_rows(pair_detail_rows, receipt_lookup),
        players=sorted(str(row["player"]) for row in player_rows),
        issues=receipt_report.issues,
    )


def _audit_player_row(
    output: dict[str, object],
    receipt_lookup: dict[str, list[dict[str, object]]],
) -> dict[str, object]:
    player_id = str(output.get("player_id") or "")
    private_value = _float(
        output.get("private_score"),
        _float(output.get("veteran_base_value")),
    )
    market_value = _float(
        output.get("market_score"),
        _float(output.get("market_trade_value"), _float(output.get("trade_value"))),
    )
    market_edge = _float(output.get("market_edge_score"), round(private_value - market_value, 2))
    warning = warning_summary(
        output.get("warning_reasons"),
        output.get("warning_status"),
        default="No active warning.",
    )
    receipt_rows = _receipt_rows_for_output(output, receipt_lookup)
    top_receipts = _top_receipt_summary(receipt_rows)
    return {
        "player_id": player_id,
        "player": output.get("player_name") or output.get("player") or "",
        "position": output.get("position") or output.get("pos") or "",
        "team": output.get("team") or output.get("nfl_team") or "",
        "lifecycle": output.get("asset_lifecycle_label")
        or _lifecycle_label(output.get("asset_lifecycle")),
        "rank": _int(output.get("overall_rank")),
        "position_rank": output.get("position_rank_label") or output.get("position_rank") or "",
        "private_stat_value": private_value,
        "market_value": market_value,
        "market_edge": market_edge,
        "confidence": _float(output.get("confidence_score"), _float(output.get("confidence"))),
        "warning": warning,
        "score_source": output.get("score_source", ""),
        "identity_match_method": output.get("identity_match_method", ""),
        "top_receipt_contributions": top_receipts,
        "model_version": output.get("model_version", ""),
    }


def _pair_row(
    pair_label: str,
    left: dict[str, object] | None,
    right: dict[str, object] | None,
    row_lookup: dict[str, dict[str, object]],
) -> dict[str, object]:
    left_row = row_lookup.get(str(left.get("player_id"))) if left else None
    right_row = row_lookup.get(str(right.get("player_id"))) if right else None
    if left_row is None or right_row is None:
        missing = []
        if left_row is None:
            missing.append("left player")
        if right_row is None:
            missing.append("right player")
        return {
            "pair": pair_label,
            "status": "missing_player",
            "player_a": left_row.get("player") if left_row else "",
            "player_b": right_row.get("player") if right_row else "",
            "leader": "",
            "private_gap_a_minus_b": "",
            "market_edge_gap_a_minus_b": "",
            "confidence_min": "",
            "top_gap_driver": "",
            "next_action": f"Add or map {', '.join(missing)} before using this audit pair.",
        }

    private_gap = round(
        _float(left_row.get("private_stat_value")) - _float(right_row.get("private_stat_value")),
        2,
    )
    edge_gap = round(
        _float(left_row.get("market_edge")) - _float(right_row.get("market_edge")),
        2,
    )
    confidence_min = min(_float(left_row.get("confidence")), _float(right_row.get("confidence")))
    return {
        "pair": pair_label,
        "status": "ready",
        "player_a": left_row["player"],
        "player_b": right_row["player"],
        "leader": _leader(left_row["player"], right_row["player"], private_gap),
        "private_gap_a_minus_b": private_gap,
        "market_edge_gap_a_minus_b": edge_gap,
        "confidence_min": round(confidence_min, 2),
        "top_gap_driver": _top_gap_driver(left_row, right_row),
        "next_action": "Open the pair detail and receipts before changing any formula.",
    }


def _receipt_lookup(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    lookup: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if not player_id:
            player_id = ""
        if player_id:
            lookup.setdefault(f"id::{player_id}", []).append(row)
        name_key = _receipt_name_key(row)
        if name_key:
            lookup.setdefault(name_key, []).append(row)
    for player_rows in lookup.values():
        player_rows.sort(key=lambda row: abs(_float(row.get("contribution"))), reverse=True)
    return lookup


def _receipt_rows_for_output(
    output: dict[str, object],
    receipt_lookup: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    player_id = str(output.get("player_id") or "")
    if player_id:
        id_rows = receipt_lookup.get(f"id::{player_id}", [])
        if id_rows:
            return id_rows
    name_key = _receipt_name_key(output)
    return receipt_lookup.get(name_key, [])


def _named_receipt_rows(
    pair_detail_rows: list[dict[str, object]],
    receipt_lookup: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for detail in pair_detail_rows:
        for receipt in _audit_receipt_rows(_receipt_rows_for_output(detail, receipt_lookup))[:10]:
            rows.append(
                {
                    "pair": detail["pair"],
                    "side": detail["side"],
                    "player": detail["player"],
                    "component": receipt.get("component", ""),
                    "receipt_section": receipt.get("receipt_section_label", ""),
                    "feature": receipt.get("formula_feature_name", ""),
                    "raw_value": receipt.get("raw_feature_value", ""),
                    "normalized_score": receipt.get("normalized_score", ""),
                    "weight": receipt.get("feature_weight", ""),
                    "contribution": receipt.get("contribution", ""),
                    "source": receipt.get("source_file") or receipt.get("source_name") or "",
                    "warning": warning_summary(
                        _audit_warning(receipt.get("warning_reason")),
                        default="No active warning.",
                    ),
                    "imputed": receipt.get("imputed_flag", ""),
                }
            )
    return rows


def _resolve_player(
    rows: list[dict[str, object]],
    aliases: tuple[str, ...],
) -> dict[str, object] | None:
    normalized_aliases = [_normalize_name(alias) for alias in aliases]
    for alias in normalized_aliases:
        for row in rows:
            if _normalize_name(row.get("player_name") or row.get("player")) == alias:
                return row
    for alias in normalized_aliases:
        for row in rows:
            row_name = _normalize_name(row.get("player_name") or row.get("player"))
            if alias and (alias in row_name or row_name in alias):
                return row
    return None


def _top_receipt_summary(receipt_rows: list[dict[str, object]], limit: int = 3) -> str:
    parts: list[str] = []
    for row in _audit_receipt_rows(receipt_rows)[:limit]:
        feature = str(row.get("formula_feature_name") or "")
        contribution = _float(row.get("contribution"))
        if feature:
            parts.append(f"{_feature_label(feature)} {contribution:+.2f}")
    return " | ".join(parts)


def _audit_receipt_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    primary_rows = [
        row
        for row in rows
        if str(row.get("component") or "") in DETAILED_PRIVATE_COMPONENTS
        and str(row.get("receipt_section_label") or "") != "Market/Liquidity"
        and str(row.get("formula_feature_name") or "") not in WRAPPER_FEATURES
        and str(row.get("formula_feature_name") or "") not in BRIDGE_RECEIPT_FEATURES
    ]
    if not primary_rows:
        primary_rows = [
            row
            for row in rows
            if str(row.get("component") or "") == "private_lve_value"
            and str(row.get("receipt_section_label") or "") != "Market/Liquidity"
            and str(row.get("formula_feature_name") or "") not in WRAPPER_FEATURES
            and str(row.get("formula_feature_name") or "") not in BRIDGE_RECEIPT_FEATURES
        ]
    if not primary_rows:
        primary_rows = rows
    return _dedupe_receipt_rows(primary_rows)


def _dedupe_receipt_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_feature: dict[str, dict[str, object]] = {}
    for row in rows:
        feature = str(row.get("formula_feature_name") or "")
        current = by_feature.get(feature)
        if current is None or abs(_float(row.get("contribution"))) > abs(
            _float(current.get("contribution"))
        ):
            by_feature[feature] = row
    return sorted(
        by_feature.values(),
        key=lambda row: (
            -abs(_float(row.get("contribution"))),
            str(row.get("formula_feature_name") or ""),
        ),
    )


def _feature_label(feature: str) -> str:
    labels = {
        "weighted_recent_lve_ppg_score": "recent LVE scoring",
        "expected_lve_points_score": "expected LVE points",
        "lve_projection_value": "projection value",
        "role_security": "role security",
        "workload_earning": "workload earning",
        "target_earning_stability": "target earning",
        "route_share_stability": "route share stability",
        "route_role": "route role",
        "efficiency_score": "efficiency",
        "first_down_td_fit": "first-down/TD fit",
        "first_down_td_fit_capped": "first-down/TD fit cap",
        "age_curve": "age window",
        "injury_durability": "injury durability",
        "lve_structural_formula_adjustment": "LVE structural adjustment",
        "position_replaceability": "position replaceability",
    }
    return labels.get(feature, feature.replace("_", " "))


def _audit_warning(value: object) -> str:
    text = str(value or "").strip()
    if text == FORMULA_DERIVED_WARNING:
        return ""
    return text


def _top_gap_driver(left_row: dict[str, object], right_row: dict[str, object]) -> str:
    left_parts = _summary_parts(left_row.get("top_receipt_contributions"))
    right_parts = _summary_parts(right_row.get("top_receipt_contributions"))
    if left_parts and right_parts and left_parts[0] != right_parts[0]:
        return f"{left_parts[0]} vs {right_parts[0]}"
    if left_parts:
        return left_parts[0]
    if right_parts:
        return right_parts[0]
    return "No receipt contribution available."


def _summary_parts(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


def _leader(player_a: object, player_b: object, gap: float) -> str:
    if gap > 0:
        return str(player_a)
    if gap < 0:
        return str(player_b)
    return "even"


def _lifecycle_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("_", " ").title()


def _normalize_name(value: object) -> str:
    text = str(value or "").lower()
    for token in ("'", ".", "-", " jr", " sr", " iii", " ii", " iv"):
        text = text.replace(token, "")
    return " ".join(text.split())


def _receipt_name_key(row: dict[str, object]) -> str:
    player = row.get("player") or row.get("player_name") or ""
    position = row.get("position") or row.get("pos") or ""
    name = _normalize_name(player)
    pos = str(position or "").strip().upper()
    if not name or not pos:
        return ""
    return f"name::{name}::{pos}"


def _rank_sort(value: object) -> int:
    rank = _int(value)
    return rank if rank is not None else 9999


def _int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if not text:
            return default
        return round(float(text), 2)
    except (TypeError, ValueError):
        return default
