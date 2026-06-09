from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_preview_engine_service import (
    DEFAULT_V3_REPORT_ROOT,
)
from src.services.model_v4_sanity_fixture_dry_run_service import (
    DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    DEFAULT_V4_RECEIPTS_PATH,
)

PHASE_5_WR_NORMALIZATION_AUDIT_CSV_PATH = Path(
    "docs/model_v4/PHASE_5_WR_NORMALIZATION_AUDIT.csv"
)
PHASE_5_WR_NORMALIZATION_AUDIT_MD_PATH = Path(
    "docs/model_v4/PHASE_5_WR_NORMALIZATION_AUDIT.md"
)

WR_NORMALIZATION_AUDIT_PLAYERS = (
    "Jaxon Smith-Njigba",
    "Puka Nacua",
    "CeeDee Lamb",
    "Tee Higgins",
    "Brian Thomas Jr.",
    "Malik Nabers",
    "Ja'Marr Chase",
    "Justin Jefferson",
    "Amon-Ra St. Brown",
)

RB_BALANCE_CONTROLS = (
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "De'Von Achane",
    "Christian McCaffrey",
    "Kyren Williams",
    "Chase Brown",
)

WR_NORMALIZATION_AUDIT_HEADER = (
    "requested_player",
    "matched_player",
    "match_status",
    "nfl_team",
    "lifecycle",
    "overall_preview_rank",
    "wr_preview_rank",
    "dynasty_asset_value",
    "confidence_label",
    "latest_production_season",
    "latest_usage_season",
    "latest_snap_season",
    "production_lve_points_no_first_downs",
    "production_normalized_score",
    "production_contribution",
    "production_source_status",
    "first_downs",
    "first_down_points",
    "first_down_normalized_score",
    "first_down_contribution",
    "target_share",
    "weighted_opportunities",
    "red_zone_usage",
    "goal_line_usage",
    "usage_sub_scores",
    "usage_normalized_score",
    "usage_contribution",
    "usage_source_status",
    "snap_share",
    "snap_normalized_score",
    "snap_contribution",
    "projection_recomputed_lve_points",
    "projection_recomputed_lve_points_no_first_downs",
    "projection_first_down_status",
    "projection_normalized_score",
    "projection_contribution",
    "age",
    "age_bucket",
    "age_normalized_score",
    "age_contribution",
    "young_player_prior_contribution",
    "warning_summary",
    "unavailable_sections",
    "production_normalization_assessment",
    "usage_normalization_assessment",
    "rb_balance_assessment",
    "route_data_effect",
    "first_down_projection_effect",
    "formula_concern",
    "recommended_action",
)


@dataclass(frozen=True)
class ModelV4WRNormalizationAuditResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_wr_normalization_audit(
    *,
    players: tuple[str, ...] = WR_NORMALIZATION_AUDIT_PLAYERS,
    preview_outputs_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    receipts_path: str | Path = DEFAULT_V4_RECEIPTS_PATH,
    source_report_root: str | Path = DEFAULT_V3_REPORT_ROOT,
    output_csv_path: str | Path = PHASE_5_WR_NORMALIZATION_AUDIT_CSV_PATH,
    output_md_path: str | Path = PHASE_5_WR_NORMALIZATION_AUDIT_MD_PATH,
) -> ModelV4WRNormalizationAuditResult:
    preview_rows = _rank_preview_rows(_read_dicts(Path(preview_outputs_path)))
    receipt_lookup = _receipt_lookup(Path(receipts_path))
    source_indexes = _source_indexes(Path(source_report_root))
    rb_context = _rb_balance_context(preview_rows, receipt_lookup)
    rows = tuple(
        _audit_row(player, preview_rows, receipt_lookup, source_indexes, rb_context)
        for player in players
    )
    summary = _summary(rows, rb_context, source_indexes)
    csv_path = Path(output_csv_path)
    markdown_path = Path(output_md_path)
    _write_csv(csv_path, WR_NORMALIZATION_AUDIT_HEADER, rows)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_markdown(summary, rows), encoding="utf-8")
    return ModelV4WRNormalizationAuditResult(
        csv_path=csv_path,
        markdown_path=markdown_path,
        rows=rows,
        summary=summary,
    )


def _audit_row(
    requested_player: str,
    preview_rows: dict[str, dict[str, object]],
    receipt_lookup: dict[str, dict[str, dict[str, str]]],
    source_indexes: dict[str, dict[str, dict[str, str]]],
    rb_context: dict[str, float],
) -> dict[str, object]:
    row = preview_rows.get(_key(requested_player))
    if row is None:
        return _missing_row(requested_player)
    player_key = _key(row["player"])
    receipts = receipt_lookup.get(player_key, {})
    production = receipts.get("production", {})
    first_down = receipts.get("first_down_scoring_fit", {})
    usage = receipts.get("usage_opportunity", {})
    snap = receipts.get("snap_proxy_role", {})
    projection = receipts.get("projection", {})
    age = receipts.get("age_dropoff", {})
    young_prior = receipts.get("young_player_prior", {})
    production_raw = _raw_values(production)
    first_down_raw = _raw_values(first_down)
    usage_raw = _raw_values(usage)
    snap_raw = _raw_values(snap)
    projection_raw = _raw_values(projection)
    age_raw = _raw_values(age)
    warnings = str(row.get("review_warnings") or "")
    unavailable = str(row.get("unavailable_sections") or "")

    production_assessment = _production_assessment(production, production_raw)
    usage_assessment = _usage_assessment(usage, usage_raw)
    route_effect = _route_effect(warnings, usage, snap)
    first_down_projection_effect = _first_down_projection_effect(projection_raw)
    formula_concern = _formula_concern(
        production_assessment=production_assessment,
        usage_assessment=usage_assessment,
        route_effect=route_effect,
        first_down_projection_effect=first_down_projection_effect,
        row=row,
        receipts=receipts,
        rb_context=rb_context,
    )
    return {
        "requested_player": requested_player,
        "matched_player": row["player"],
        "match_status": "matched",
        "nfl_team": row["nfl_team"],
        "lifecycle": row["lifecycle"],
        "overall_preview_rank": row["overall_rank"],
        "wr_preview_rank": row["position_rank"],
        "dynasty_asset_value": _format_number(row["dynasty_asset_value"]),
        "confidence_label": row["confidence_label"],
        "latest_production_season": _season_for(
            source_indexes,
            "production",
            player_key,
        ),
        "latest_usage_season": _season_for(source_indexes, "usage", player_key),
        "latest_snap_season": _season_for(source_indexes, "snap", player_key),
        "production_lve_points_no_first_downs": _format_number(
            production_raw.get("lve_points_no_first_downs")
        ),
        "production_normalized_score": _score(production),
        "production_contribution": _contribution(production),
        "production_source_status": production.get("source_status", ""),
        "first_downs": _format_number(first_down_raw.get("first_downs")),
        "first_down_points": _format_number(first_down_raw.get("first_down_points")),
        "first_down_normalized_score": _score(first_down),
        "first_down_contribution": _contribution(first_down),
        "target_share": _format_number(usage_raw.get("target_share")),
        "weighted_opportunities": _format_number(
            usage_raw.get("weighted_opportunities")
        ),
        "red_zone_usage": _format_number(
            _float(usage_raw.get("red_zone_carries"))
            + _float(usage_raw.get("red_zone_targets"))
        ),
        "goal_line_usage": _format_number(
            _float(usage_raw.get("goal_line_carries"))
            + _float(usage_raw.get("goal_line_targets"))
        ),
        "usage_sub_scores": json.dumps(
            usage_raw.get("sub_scores", {}),
            sort_keys=True,
        ),
        "usage_normalized_score": _score(usage),
        "usage_contribution": _contribution(usage),
        "usage_source_status": usage.get("source_status", ""),
        "snap_share": _format_number(
            snap_raw.get("snap_share") or snap_raw.get("offense_pct")
        ),
        "snap_normalized_score": _score(snap),
        "snap_contribution": _contribution(snap),
        "projection_recomputed_lve_points": _format_number(
            projection_raw.get("recomputed_lve_points")
        ),
        "projection_recomputed_lve_points_no_first_downs": _format_number(
            projection_raw.get("recomputed_lve_points_no_first_downs")
        ),
        "projection_first_down_status": projection_raw.get(
            "first_down_projection_status",
            "",
        ),
        "projection_normalized_score": _score(projection),
        "projection_contribution": _contribution(projection),
        "age": _format_number(age_raw.get("age")),
        "age_bucket": age_raw.get("age_bucket", ""),
        "age_normalized_score": _score(age),
        "age_contribution": _contribution(age),
        "young_player_prior_contribution": _contribution(young_prior),
        "warning_summary": warnings,
        "unavailable_sections": unavailable,
        "production_normalization_assessment": production_assessment,
        "usage_normalization_assessment": usage_assessment,
        "rb_balance_assessment": _rb_balance_assessment(row, receipts, rb_context),
        "route_data_effect": route_effect,
        "first_down_projection_effect": first_down_projection_effect,
        "formula_concern": formula_concern,
        "recommended_action": _recommended_action(
            production_assessment,
            usage_assessment,
            route_effect,
            formula_concern,
        ),
    }


def _missing_row(requested_player: str) -> dict[str, object]:
    row = {field: "" for field in WR_NORMALIZATION_AUDIT_HEADER}
    row.update(
        {
            "requested_player": requested_player,
            "match_status": "missing_preview_output",
            "production_normalization_assessment": "missing preview row",
            "usage_normalization_assessment": "missing preview row",
            "recommended_action": "Verify identity coverage before normalization review.",
        }
    )
    return row


def _production_assessment(
    receipt: dict[str, str],
    raw_values: dict[str, Any],
) -> str:
    if not receipt:
        return "missing production evidence"
    score = _float(receipt.get("normalized_score"))
    expected = _points_to_wr_score(raw_values.get("lve_points_no_first_downs"))
    if expected is not None and abs(expected - score) > 0.02:
        return (
            "confirmed normalization mismatch: WR production score does not match "
            "LVE points divided by the WR production ceiling"
        )
    if score < 55:
        return (
            "math consistent but low from latest structured production; likely stale "
            "or low latest-season evidence rather than a normalization bug"
        )
    return "position-relative math is consistent with the WR production ceiling"


def _usage_assessment(receipt: dict[str, str], raw_values: dict[str, Any]) -> str:
    if not receipt:
        return "missing usage evidence"
    sub_scores = raw_values.get("sub_scores")
    score = _float(receipt.get("normalized_score"))
    if isinstance(sub_scores, dict) and sub_scores:
        expected = sum(_float(value) for value in sub_scores.values()) / len(sub_scores)
        if abs(expected - score) > 0.02:
            return (
                "confirmed normalization mismatch: usage score does not equal the "
                "average of displayed usage sub-scores"
            )
        if score < 45:
            return (
                "math consistent but compressed by absolute target/red-zone/goal-line "
                "usage sub-scores; route quality is unavailable"
            )
    return "usage math is internally consistent"


def _rb_balance_assessment(
    row: dict[str, object],
    receipts: dict[str, dict[str, str]],
    rb_context: dict[str, float],
) -> str:
    value = _float(row.get("dynasty_asset_value"))
    rb_median = rb_context.get("median_dynasty_asset_value", 0.0)
    usage_score = _float(receipts.get("usage_opportunity", {}).get("normalized_score"))
    rb_usage_median = rb_context.get("median_usage_score", 0.0)
    projection_score = _float(receipts.get("projection", {}).get("normalized_score"))
    rb_projection_median = rb_context.get("median_projection_score", 0.0)
    if value < rb_median and projection_score >= rb_projection_median:
        return (
            "WR trails top RB controls despite comparable projection because historical "
            "production/usage and route-unavailable evidence carry the comparison"
        )
    if usage_score < rb_usage_median:
        return "WR usage score is below top RB control median in current absolute usage scale"
    return "WR/RB comparison is not showing a clear normalization-only bug"


def _route_effect(
    warnings: str,
    usage: dict[str, str],
    snap: dict[str, str],
) -> str:
    warning_text = warnings.lower()
    if "route_participation_unavailable" in warning_text:
        return (
            "route data unavailable; usage relies on target/opportunity fields and snap "
            "share remains proxy-only"
        )
    if usage or snap:
        return "route data not used; no route-specific warning found"
    return "route and snap/usage evidence missing"


def _first_down_projection_effect(raw_values: dict[str, Any]) -> str:
    status = str(raw_values.get("first_down_projection_status") or "")
    if status == "estimated_from_history":
        return "first-down projection is estimated from history and remains preview-only"
    if status == "direct_first_down_projection":
        return "direct first-down projection present"
    if status == "missing_first_down_projection":
        return "missing first-down projection"
    return "projection first-down status unavailable"


def _formula_concern(
    *,
    production_assessment: str,
    usage_assessment: str,
    route_effect: str,
    first_down_projection_effect: str,
    row: dict[str, object],
    receipts: dict[str, dict[str, str]],
    rb_context: dict[str, float],
) -> str:
    if "confirmed normalization mismatch" in production_assessment:
        return "normalization bug - patch before formula review"
    if "confirmed normalization mismatch" in usage_assessment:
        return "normalization bug - patch before formula review"
    value = _float(row.get("dynasty_asset_value"))
    projection_score = _float(receipts.get("projection", {}).get("normalized_score"))
    production_score = _float(receipts.get("production", {}).get("normalized_score"))
    usage_score = _float(receipts.get("usage_opportunity", {}).get("normalized_score"))
    rb_median = rb_context.get("median_dynasty_asset_value", 0.0)
    if (
        value < rb_median
        and projection_score >= 65
        and (production_score < 55 or usage_score < 45)
    ):
        return (
            "formula/data recency concern: strong projection cannot overcome low/stale "
            "latest production/usage in current weights"
        )
    if "route data unavailable" in route_effect:
        return "data gap concern: missing route quality limits WR confidence and separation"
    if "estimated from history" in first_down_projection_effect:
        return "projection evidence is usable only as labeled estimate, not direct proof"
    return "no formula change supported by this row alone"


def _recommended_action(
    production_assessment: str,
    usage_assessment: str,
    route_effect: str,
    formula_concern: str,
) -> str:
    if "confirmed normalization mismatch" in production_assessment:
        return "Patch production normalization and regenerate v4 preview."
    if "confirmed normalization mismatch" in usage_assessment:
        return "Patch usage normalization and regenerate v4 preview."
    if "formula/data recency concern" in formula_concern:
        return (
            "Document for formula/data-recency pass; do not tune until fixture-backed "
            "and fresher data are available."
        )
    if "route data unavailable" in route_effect:
        return "Keep route gap visible; use licensed structured route source or leave proxy-only."
    return (
        "No confirmed normalization bug; keep review-only and use receipts for next "
        "formula audit."
    )


def _summary(
    rows: tuple[dict[str, object], ...],
    rb_context: dict[str, float],
    source_indexes: dict[str, dict[str, dict[str, str]]],
) -> dict[str, object]:
    matched = [row for row in rows if row["match_status"] == "matched"]
    formula_concern_rows = [
        row for row in matched if str(row["formula_concern"]).startswith("formula/")
    ]
    normalization_bug_rows = [
        row
        for row in matched
        if "confirmed normalization mismatch" in str(row["production_normalization_assessment"])
        or "confirmed normalization mismatch" in str(row["usage_normalization_assessment"])
    ]
    return {
        "review_status": "review_only",
        "requested_players": len(rows),
        "matched_players": len(matched),
        "missing_players": len(rows) - len(matched),
        "confirmed_normalization_bug_rows": len(normalization_bug_rows),
        "formula_or_data_recency_concern_rows": len(formula_concern_rows),
        "route_unavailable_rows": sum(
            1 for row in matched if "route data unavailable" in str(row["route_data_effect"])
        ),
        "estimated_first_down_projection_rows": sum(
            1
            for row in matched
            if "estimated from history" in str(row["first_down_projection_effect"])
        ),
        "latest_production_source_season": _max_source_season(source_indexes, "production"),
        "latest_usage_source_season": _max_source_season(source_indexes, "usage"),
        "latest_snap_source_season": _max_source_season(source_indexes, "snap"),
        "rb_control_median_dynasty_asset_value": _format_number(
            rb_context.get("median_dynasty_asset_value")
        ),
        "rb_control_median_usage_score": _format_number(rb_context.get("median_usage_score")),
        "score_changes_applied": False,
        "active_rankings_promoted": False,
    }


def _markdown(
    summary: dict[str, object],
    rows: tuple[dict[str, object], ...],
) -> str:
    lines = [
        "# Phase 5G WR Production And Usage Normalization Audit",
        "",
        "This report checks whether elite WR preview values are low because of a "
        "normalization bug, missing/limited evidence, route-data gaps, or a formula "
        "balance concern. It does not change weights, promote rankings, or unlock "
        "readiness.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            "- No confirmed production or usage normalization mismatch was patched by this audit.",
            "- The main WR limitation is evidence quality: current structured production, usage, "
            "and snap inputs are latest-season nflverse rows from the 2022-2024 source set, "
            "while several sanity beliefs rely on newer dynasty context.",
            "- Route participation, routes run, TPRR, and YPRR remain unavailable in the safe "
            "free-data model; snap share is proxy-only and cannot explain route quality.",
            "- First-down projections are estimated from history for most projected WRs, "
            "not direct.",
            "- Formula imbalance remains a review concern where strong projection evidence cannot "
            "overcome low/stale historical production or conservative usage scores.",
            "",
            "## Player Audit",
            "",
        ]
    )
    player_header = (
        "matched_player",
        "dynasty_asset_value",
        "overall_preview_rank",
        "wr_preview_rank",
        "latest_production_season",
        "production_normalized_score",
        "usage_normalized_score",
        "projection_normalized_score",
        "route_data_effect",
        "formula_concern",
        "recommended_action",
    )
    lines.extend(_markdown_table(player_header, rows))
    lines.extend(["", "## Raw And Normalized Components", ""])
    component_header = (
        "matched_player",
        "production_lve_points_no_first_downs",
        "first_downs",
        "target_share",
        "weighted_opportunities",
        "snap_share",
        "projection_recomputed_lve_points",
        "age",
        "age_bucket",
        "young_player_prior_contribution",
    )
    lines.extend(_markdown_table(component_header, rows))
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- A low WR row is not automatically a bug. This audit only treats a row as a "
            "confirmed normalization bug when the displayed normalized score does not "
            "reconcile to the displayed raw component inputs.",
            "- Stale or incomplete evidence should be fixed with better source rows before "
            "changing weights.",
            "",
        ]
    )
    return "\n".join(lines)


def _rank_preview_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    sorted_rows = sorted(
        rows,
        key=lambda row: _float(row.get("dynasty_asset_value")),
        reverse=True,
    )
    by_position: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sorted_rows:
        by_position[str(row.get("position") or "").upper()].append(row)
    position_ranks = {}
    for rows_for_position in by_position.values():
        for index, row in enumerate(rows_for_position, 1):
            position_ranks[_key(row.get("player"))] = index
    output: dict[str, dict[str, object]] = {}
    for overall_rank, row in enumerate(sorted_rows, 1):
        copy: dict[str, object] = dict(row)
        copy["overall_rank"] = overall_rank
        copy["position_rank"] = position_ranks[_key(row.get("player"))]
        output[_key(row.get("player"))] = copy
    return output


def _receipt_lookup(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    lookup: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in _read_dicts(path):
        lookup[_key(row.get("player"))][str(row.get("component") or "")] = row
    return dict(lookup)


def _source_indexes(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    return {
        "production": _latest_source_index(root / "truth_set_v3_production_player_season.csv"),
        "usage": _latest_source_index(root / "truth_set_v3_usage_player_season.csv"),
        "snap": _latest_source_index(root / "truth_set_v3_snap_share_player_season.csv"),
    }


def _latest_source_index(path: Path) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in _read_optional(path):
        key = _key(row.get("truth_set_player_name") or row.get("player_name"))
        if not key:
            continue
        existing = index.get(key)
        if existing is None or _int(row.get("season")) >= _int(existing.get("season")):
            index[key] = row
    return index


def _rb_balance_context(
    preview_rows: dict[str, dict[str, object]],
    receipt_lookup: dict[str, dict[str, dict[str, str]]],
) -> dict[str, float]:
    values: list[float] = []
    usage_scores: list[float] = []
    projection_scores: list[float] = []
    for player in RB_BALANCE_CONTROLS:
        row = preview_rows.get(_key(player))
        receipts = receipt_lookup.get(_key(player), {})
        if row:
            values.append(_float(row.get("dynasty_asset_value")))
        if "usage_opportunity" in receipts:
            usage_scores.append(_float(receipts["usage_opportunity"].get("normalized_score")))
        if "projection" in receipts:
            projection_scores.append(_float(receipts["projection"].get("normalized_score")))
    return {
        "median_dynasty_asset_value": _median(values),
        "median_usage_score": _median(usage_scores),
        "median_projection_score": _median(projection_scores),
    }


def _points_to_wr_score(value: object) -> float | None:
    try:
        return round(min(max((float(str(value)) / 300.0) * 100.0, 0.0), 100.0), 3)
    except (TypeError, ValueError):
        return None


def _raw_values(receipt: dict[str, str]) -> dict[str, Any]:
    try:
        value = json.loads(str(receipt.get("raw_values") or "{}"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _score(receipt: dict[str, str]) -> str:
    return _format_number(receipt.get("normalized_score"))


def _contribution(receipt: dict[str, str]) -> str:
    return _format_number(receipt.get("contribution"))


def _season_for(
    source_indexes: dict[str, dict[str, dict[str, str]]],
    source: str,
    player_key: str,
) -> str:
    return str(source_indexes.get(source, {}).get(player_key, {}).get("season", ""))


def _max_source_season(
    source_indexes: dict[str, dict[str, dict[str, str]]],
    source: str,
) -> str:
    seasons = [
        _int(row.get("season"))
        for row in source_indexes.get(source, {}).values()
        if _int(row.get("season")) > 0
    ]
    return str(max(seasons)) if seasons else ""


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_optional(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return _read_dicts(path)


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _markdown_table(
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> list[str]:
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(row.get(column, "")) for column in header) + " |")
    return lines


def _median(values: list[float]) -> float:
    cleaned = sorted(value for value in values if value > 0)
    if not cleaned:
        return 0.0
    middle = len(cleaned) // 2
    if len(cleaned) % 2:
        return cleaned[middle]
    return round((cleaned[middle - 1] + cleaned[middle]) / 2.0, 3)


def _key(value: object) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ").replace("'", "").replace(".", "")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if not text:
            return default
        return round(float(text), 3)
    except (TypeError, ValueError):
        return default


def _int(value: object) -> int:
    try:
        text = str(value).strip()
        if not text:
            return 0
        return int(float(text))
    except (TypeError, ValueError):
        return 0


def _format_number(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return f"{float(text):.2f}"
    except ValueError:
        return text


def _md_cell(value: object) -> str:
    text = str(value or "")
    return text.replace("|", "<br>").replace("\n", " ")
