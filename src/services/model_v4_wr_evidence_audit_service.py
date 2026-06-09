from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_sanity_fixture_dry_run_service import (
    DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    DEFAULT_V4_RECEIPTS_PATH,
)

PHASE_4_WR_AUDIT_CSV_PATH = Path("docs/model_v4/PHASE_4_WR_EVIDENCE_AUDIT.csv")
PHASE_4_WR_AUDIT_MD_PATH = Path("docs/model_v4/PHASE_4_WR_EVIDENCE_AUDIT.md")

WR_EVIDENCE_AUDIT_PLAYERS = (
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

WR_COMPONENTS = (
    "production",
    "first_down_scoring_fit",
    "usage_opportunity",
    "snap_proxy_role",
    "projection",
    "age_dropoff",
    "young_player_prior",
)

WR_EVIDENCE_AUDIT_HEADER = (
    "requested_player",
    "matched_player",
    "match_status",
    "nfl_team",
    "lifecycle",
    "dynasty_asset_value",
    "overall_preview_rank",
    "wr_preview_rank",
    "production_score",
    "production_contribution",
    "first_down_fit_score",
    "first_down_fit_contribution",
    "usage_opportunity_score",
    "usage_opportunity_contribution",
    "snap_proxy_role_score",
    "snap_proxy_role_contribution",
    "projection_score",
    "projection_contribution",
    "age_dropoff_score",
    "age_dropoff_contribution",
    "young_player_prior_contribution",
    "confidence_label",
    "warnings",
    "unavailable_sections",
    "missing_data",
    "route_data_unavailable",
    "projection_gap",
    "first_down_projection_gap",
    "usage_normalization_review",
    "production_normalization_review",
    "young_bridge_review",
    "true_formula_imbalance_review",
    "evidence_summary",
    "recommended_action",
)


@dataclass(frozen=True)
class ModelV4WREvidenceAuditResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_wr_evidence_audit(
    *,
    players: tuple[str, ...] = WR_EVIDENCE_AUDIT_PLAYERS,
    preview_outputs_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    receipts_path: str | Path = DEFAULT_V4_RECEIPTS_PATH,
    output_csv_path: str | Path = PHASE_4_WR_AUDIT_CSV_PATH,
    output_md_path: str | Path = PHASE_4_WR_AUDIT_MD_PATH,
) -> ModelV4WREvidenceAuditResult:
    preview_rows = _rank_preview_rows(_read_dicts(Path(preview_outputs_path)))
    receipt_lookup = _receipt_lookup(Path(receipts_path))
    rows = tuple(
        _audit_row(player, preview_rows, receipt_lookup)
        for player in players
    )
    summary = _summary(rows)
    csv_path = Path(output_csv_path)
    markdown_path = Path(output_md_path)
    _write_csv(csv_path, WR_EVIDENCE_AUDIT_HEADER, rows)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_markdown(summary, rows), encoding="utf-8")
    return ModelV4WREvidenceAuditResult(
        csv_path=csv_path,
        markdown_path=markdown_path,
        rows=rows,
        summary=summary,
    )


def _audit_row(
    requested_player: str,
    preview_rows: dict[str, dict[str, object]],
    receipt_lookup: dict[str, list[dict[str, str]]],
) -> dict[str, object]:
    row = preview_rows.get(_key(requested_player))
    if row is None:
        return _missing_row(requested_player)
    receipts = receipt_lookup.get(_key(row["player"]), [])
    receipt_by_component = {receipt["component"]: receipt for receipt in receipts}
    warnings = _split(row.get("review_warnings"))
    unavailable = _split(row.get("unavailable_sections"))
    flags = _cause_flags(row, receipt_by_component, warnings, unavailable)
    evidence_summary = _evidence_summary(row, receipt_by_component, flags)
    recommended_action = _recommended_action(flags)
    return {
        "requested_player": requested_player,
        "matched_player": row["player"],
        "match_status": "matched",
        "nfl_team": row["nfl_team"],
        "lifecycle": row["lifecycle"],
        "dynasty_asset_value": _format_number(row["dynasty_asset_value"]),
        "overall_preview_rank": row["overall_rank"],
        "wr_preview_rank": row["position_rank"],
        "production_score": _component_score(receipt_by_component, "production"),
        "production_contribution": _component_contribution(
            receipt_by_component,
            "production",
        ),
        "first_down_fit_score": _component_score(
            receipt_by_component,
            "first_down_scoring_fit",
        ),
        "first_down_fit_contribution": _component_contribution(
            receipt_by_component,
            "first_down_scoring_fit",
        ),
        "usage_opportunity_score": _component_score(
            receipt_by_component,
            "usage_opportunity",
        ),
        "usage_opportunity_contribution": _component_contribution(
            receipt_by_component,
            "usage_opportunity",
        ),
        "snap_proxy_role_score": _component_score(receipt_by_component, "snap_proxy_role"),
        "snap_proxy_role_contribution": _component_contribution(
            receipt_by_component,
            "snap_proxy_role",
        ),
        "projection_score": _component_score(receipt_by_component, "projection"),
        "projection_contribution": _component_contribution(
            receipt_by_component,
            "projection",
        ),
        "age_dropoff_score": _component_score(receipt_by_component, "age_dropoff"),
        "age_dropoff_contribution": _component_contribution(
            receipt_by_component,
            "age_dropoff",
        ),
        "young_player_prior_contribution": _component_contribution(
            receipt_by_component,
            "young_player_prior",
        ),
        "confidence_label": row["confidence_label"],
        "warnings": "|".join(warnings),
        "unavailable_sections": "|".join(unavailable),
        **flags,
        "evidence_summary": evidence_summary,
        "recommended_action": recommended_action,
    }


def _missing_row(requested_player: str) -> dict[str, object]:
    return {
        "requested_player": requested_player,
        "matched_player": "",
        "match_status": "missing_preview_output",
        "nfl_team": "",
        "lifecycle": "",
        "dynasty_asset_value": "",
        "overall_preview_rank": "",
        "wr_preview_rank": "",
        "production_score": "",
        "production_contribution": "",
        "first_down_fit_score": "",
        "first_down_fit_contribution": "",
        "usage_opportunity_score": "",
        "usage_opportunity_contribution": "",
        "snap_proxy_role_score": "",
        "snap_proxy_role_contribution": "",
        "projection_score": "",
        "projection_contribution": "",
        "age_dropoff_score": "",
        "age_dropoff_contribution": "",
        "young_player_prior_contribution": "",
        "confidence_label": "",
        "warnings": "",
        "unavailable_sections": "",
        "missing_data": True,
        "route_data_unavailable": False,
        "projection_gap": False,
        "first_down_projection_gap": False,
        "usage_normalization_review": False,
        "production_normalization_review": False,
        "young_bridge_review": False,
        "true_formula_imbalance_review": False,
        "evidence_summary": "Missing v4 preview row.",
        "recommended_action": "Verify identity coverage before formula review.",
    }


def _cause_flags(
    row: dict[str, object],
    receipts: dict[str, dict[str, str]],
    warnings: tuple[str, ...],
    unavailable: tuple[str, ...],
) -> dict[str, bool]:
    warning_text = "|".join(warnings).lower()
    unavailable_text = "|".join(unavailable).lower()
    projection = receipts.get("projection", {})
    usage = receipts.get("usage_opportunity", {})
    production = receipts.get("production", {})
    young_prior = receipts.get("young_player_prior", {})
    usage_score = _float(usage.get("normalized_score"))
    production_score = _float(production.get("normalized_score"))
    projection_score = _float(projection.get("normalized_score"))
    value = _float(row.get("dynasty_asset_value"))
    confidence_label = str(row.get("confidence_label") or "")
    missing_data = bool(unavailable) or not receipts
    route_data_unavailable = (
        "route" in warning_text
        or "snap_share_proxy_only_not_route_participation" in warning_text
    )
    projection_gap = (
        "projection" in unavailable_text
        or "missing_projection" in warning_text
        or projection_score < 35
    )
    first_down_projection_gap = (
        "missing_first_down_projection" in warning_text
        or "projection_first_downs_missing" in warning_text
    )
    usage_normalization_review = (
        usage_score < 45
        and str(usage.get("source_status") or "") == "derived_real_data"
    )
    production_normalization_review = (
        production_score < 50
        and str(production.get("source_status") or "") == "imported_real_data"
    )
    young_bridge_review = (
        "bridge" in str(row.get("lifecycle") or "").lower()
        and (
            "young_player_prior_review_only" in warning_text
            or "young_player_prior" in unavailable
            or str(young_prior.get("source_status") or "") in {"missing", "review_only"}
        )
    )
    true_formula_imbalance_review = (
        value < 60
        and confidence_label in {"usable", "strong"}
        and not production_normalization_review
        and not usage_normalization_review
        and not projection_gap
        and not missing_data
    )
    return {
        "missing_data": missing_data,
        "route_data_unavailable": route_data_unavailable,
        "projection_gap": projection_gap,
        "first_down_projection_gap": first_down_projection_gap,
        "usage_normalization_review": usage_normalization_review,
        "production_normalization_review": production_normalization_review,
        "young_bridge_review": young_bridge_review,
        "true_formula_imbalance_review": true_formula_imbalance_review,
    }


def _evidence_summary(
    row: dict[str, object],
    receipts: dict[str, dict[str, str]],
    flags: dict[str, bool],
) -> str:
    main_parts = [
        f"value={_format_number(row.get('dynasty_asset_value'))}",
        _component_pair_summary(receipts, "production"),
        _component_pair_summary(receipts, "usage_opportunity"),
        _component_pair_summary(receipts, "projection"),
    ]
    active_flags = [
        flag.replace("_", " ")
        for flag, active in flags.items()
        if active
    ]
    if active_flags:
        main_parts.append("review_flags=" + ", ".join(active_flags))
    return "; ".join(main_parts)


def _component_pair_summary(
    receipts: dict[str, dict[str, str]],
    component: str,
) -> str:
    label = component.replace("_opportunity", "")
    return (
        f"{label}={_component_score(receipts, component)} / "
        f"{_component_contribution(receipts, component)}"
    )


def _recommended_action(flags: dict[str, bool]) -> str:
    if flags["production_normalization_review"]:
        return "Inspect production normalization before any weight change."
    if flags["usage_normalization_review"]:
        return "Inspect derived usage normalization before any weight change."
    if flags["projection_gap"] or flags["first_down_projection_gap"]:
        return "Keep projection gap visible; do not tune around missing projection evidence."
    if flags["route_data_unavailable"]:
        return "Treat route participation as unavailable/proxy-only until a licensed source exists."
    if flags["young_bridge_review"]:
        return "Review young-player bridge receipts; do not boost draft prior blindly."
    if flags["true_formula_imbalance_review"]:
        return "Candidate for formula review after fixture-backed evidence."
    if flags["missing_data"]:
        return "Resolve missing data or keep review-only."
    return "No data/identity/receipt bug proven; keep as review evidence."


def _summary(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    matched = [row for row in rows if row["match_status"] == "matched"]
    return {
        "review_status": "review_only",
        "requested_players": len(rows),
        "matched_players": len(matched),
        "missing_players": len(rows) - len(matched),
        "route_data_unavailable_rows": _count(rows, "route_data_unavailable"),
        "projection_gap_rows": _count(rows, "projection_gap"),
        "first_down_projection_gap_rows": _count(rows, "first_down_projection_gap"),
        "usage_normalization_review_rows": _count(rows, "usage_normalization_review"),
        "production_normalization_review_rows": _count(
            rows,
            "production_normalization_review",
        ),
        "young_bridge_review_rows": _count(rows, "young_bridge_review"),
        "true_formula_imbalance_review_rows": _count(
            rows,
            "true_formula_imbalance_review",
        ),
        "score_changes_applied": False,
        "active_rankings_promoted": False,
    }


def _count(rows: tuple[dict[str, object], ...], key: str) -> int:
    return sum(1 for row in rows if row.get(key) is True)


def _markdown(
    summary: dict[str, object],
    rows: tuple[dict[str, object], ...],
) -> str:
    lines = [
        "# Phase 4 WR Evidence Audit",
        "",
        "This report investigates the main Phase 3 WR review finding before any "
        "formula tuning. It does not change weights, promote rankings, or unlock "
        "decision readiness.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Route participation remains unavailable/proxy-only in the free-data model.",
            "- Missing first-down projections remain a projection-layer gap, not a WR-only bug.",
            "- Any formula imbalance should be handled only after fixture-backed review.",
            "",
            "## Player Evidence Table",
            "",
        ]
    )
    table_header = (
        "matched_player",
        "dynasty_asset_value",
        "overall_preview_rank",
        "wr_preview_rank",
        "confidence_label",
        "route_data_unavailable",
        "projection_gap",
        "first_down_projection_gap",
        "usage_normalization_review",
        "production_normalization_review",
        "young_bridge_review",
        "true_formula_imbalance_review",
        "recommended_action",
    )
    lines.extend(_markdown_table(table_header, rows))
    lines.extend(["", "## Component Detail", ""])
    detail_header = (
        "matched_player",
        "production_score",
        "production_contribution",
        "first_down_fit_score",
        "first_down_fit_contribution",
        "usage_opportunity_score",
        "usage_opportunity_contribution",
        "snap_proxy_role_score",
        "snap_proxy_role_contribution",
        "projection_score",
        "projection_contribution",
        "age_dropoff_score",
        "age_dropoff_contribution",
        "young_player_prior_contribution",
    )
    lines.extend(_markdown_table(detail_header, rows))
    lines.append("")
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
    output = {}
    for overall_rank, row in enumerate(sorted_rows, 1):
        copy: dict[str, object] = dict(row)
        copy["overall_rank"] = overall_rank
        copy["position_rank"] = position_ranks[_key(row.get("player"))]
        output[_key(row.get("player"))] = copy
    return output


def _receipt_lookup(path: Path) -> dict[str, list[dict[str, str]]]:
    lookup: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _read_dicts(path):
        lookup[_key(row.get("player"))].append(row)
    return dict(lookup)


def _component_score(
    receipts: dict[str, dict[str, str]],
    component: str,
) -> str:
    return _format_number(receipts.get(component, {}).get("normalized_score"))


def _component_contribution(
    receipts: dict[str, dict[str, str]],
    component: str,
) -> str:
    return _format_number(receipts.get(component, {}).get("contribution"))


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
        lines.append(
            "| "
            + " | ".join(_md_cell(row.get(column, "")) for column in header)
            + " |"
        )
    return lines


def _split(value: object) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split("|") if part.strip())


def _key(value: object) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", text)
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


def _format_number(value: object) -> str:
    try:
        text = str(value).strip()
    except AttributeError:
        text = str(value or "")
    if not text:
        return ""
    return f"{_float(text):.2f}"


def _md_cell(value: object) -> str:
    text = str(value or "")
    return text.replace("|", "<br>").replace("\n", " ")
