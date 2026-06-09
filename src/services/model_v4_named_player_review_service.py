from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_sanity_fixture_dry_run_service import (
    DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    DEFAULT_V4_RECEIPTS_PATH,
)

PHASE_3_NAMED_REVIEW_CSV_PATH = Path(
    "docs/model_v4/PHASE_3_NAMED_PLAYER_REVIEW.csv"
)
PHASE_3_NAMED_REVIEW_MD_PATH = Path(
    "docs/model_v4/PHASE_3_NAMED_PLAYER_REVIEW.md"
)

NAMED_PLAYER_REVIEW_PLAYERS = (
    "De'Von Achane",
    "Lamar Jackson",
    "Chase Brown",
    "Luther Burden",
    "Brian Thomas Jr.",
    "Kaleb Johnson",
    "Jaxon Smith-Njigba",
    "Tee Higgins",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "Christian McCaffrey",
    "Puka Nacua",
    "Ja'Marr Chase",
    "Justin Jefferson",
    "Amon-Ra St. Brown",
    "CeeDee Lamb",
    "Malik Nabers",
    "Keenan Allen",
    "Brock Bowers",
)

NAMED_PLAYER_REVIEW_HEADER = (
    "requested_player",
    "matched_player",
    "match_status",
    "position",
    "nfl_team",
    "lifecycle",
    "overall_rank",
    "position_rank",
    "dynasty_asset_value",
    "confidence",
    "confidence_label",
    "component_scores",
    "component_contributions",
    "top_positive_receipt_drivers",
    "top_negative_receipt_drivers",
    "warnings",
    "unavailable_sections",
    "review_notes",
)

INSPECTION_HEADER = (
    "inspection",
    "status",
    "finding",
    "evidence",
    "next_action",
)

FORBIDDEN_PRIVATE_COMPONENT_TOKENS = (
    "market",
    "trade",
    "liquidity",
    "league_rank",
    "league-rank",
)


@dataclass(frozen=True)
class ModelV4NamedPlayerReviewResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    inspection_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_named_player_review(
    *,
    players: tuple[str, ...] = NAMED_PLAYER_REVIEW_PLAYERS,
    preview_outputs_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    receipts_path: str | Path = DEFAULT_V4_RECEIPTS_PATH,
    output_csv_path: str | Path = PHASE_3_NAMED_REVIEW_CSV_PATH,
    output_md_path: str | Path = PHASE_3_NAMED_REVIEW_MD_PATH,
    report_title: str = "Phase 3G Named Player Review",
) -> ModelV4NamedPlayerReviewResult:
    preview_rows = _rank_preview_rows(_read_dicts(Path(preview_outputs_path)))
    receipt_lookup = _receipt_lookup(Path(receipts_path))
    rows = tuple(
        _review_row(player, preview_rows, receipt_lookup)
        for player in players
    )
    inspection_rows = tuple(_inspection_rows(rows, receipt_lookup))
    summary = _summary(rows, inspection_rows)
    csv_path = Path(output_csv_path)
    md_path = Path(output_md_path)
    _write_csv(csv_path, NAMED_PLAYER_REVIEW_HEADER, rows)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        _markdown(summary, rows, inspection_rows, report_title),
        encoding="utf-8",
    )
    return ModelV4NamedPlayerReviewResult(
        csv_path=csv_path,
        markdown_path=md_path,
        rows=rows,
        inspection_rows=inspection_rows,
        summary=summary,
    )


def _review_row(
    requested_player: str,
    preview_rows: dict[str, dict[str, object]],
    receipt_lookup: dict[str, list[dict[str, str]]],
) -> dict[str, object]:
    row = preview_rows.get(_key(requested_player))
    if row is None:
        return {
            "requested_player": requested_player,
            "matched_player": "",
            "match_status": "missing_preview_output",
            "position": "",
            "nfl_team": "",
            "lifecycle": "",
            "overall_rank": "",
            "position_rank": "",
            "dynasty_asset_value": "",
            "confidence": "",
            "confidence_label": "",
            "component_scores": "",
            "component_contributions": "",
            "top_positive_receipt_drivers": "",
            "top_negative_receipt_drivers": "",
            "warnings": "",
            "unavailable_sections": "",
            "review_notes": "Missing v4 preview row; verify identity/source coverage.",
        }
    receipts = receipt_lookup.get(_key(row["player"]), [])
    warnings = _split(row.get("review_warnings"))
    unavailable = _split(row.get("unavailable_sections"))
    confidence_label = str(row.get("confidence_label") or "")
    return {
        "requested_player": requested_player,
        "matched_player": row["player"],
        "match_status": "matched",
        "position": row["position"],
        "nfl_team": row["nfl_team"],
        "lifecycle": row["lifecycle"],
        "overall_rank": row["overall_rank"],
        "position_rank": row["position_rank"],
        "dynasty_asset_value": _format_number(row["dynasty_asset_value"]),
        "confidence": _format_number(row["confidence"]),
        "confidence_label": confidence_label,
        "component_scores": _component_summary(row.get("component_scores")),
        "component_contributions": _component_summary(row.get("component_contributions")),
        "top_positive_receipt_drivers": _top_positive_drivers(receipts),
        "top_negative_receipt_drivers": _top_negative_drivers(receipts),
        "warnings": "|".join(warnings),
        "unavailable_sections": "|".join(unavailable),
        "review_notes": _review_notes(row, warnings, unavailable, receipts),
    }


def _inspection_rows(
    rows: tuple[dict[str, object], ...],
    receipt_lookup: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    matched = [row for row in rows if row["match_status"] == "matched"]
    by_player = {str(row["matched_player"]): row for row in matched}
    return [
        _rb_wr_balance_row(matched),
        _young_bridge_row(matched),
        _qb_suppression_row(by_player),
        _te_suppression_row(by_player),
        _aging_dropoff_row(by_player),
        _separation_row(receipt_lookup),
    ]


def _rb_wr_balance_row(rows: list[dict[str, object]]) -> dict[str, object]:
    rbs = [row for row in rows if row["position"] == "RB"]
    wrs = [row for row in rows if row["position"] == "WR"]
    top_rbs = _top_rows(rbs, limit=5)
    top_wrs = _top_rows(wrs, limit=5)
    below_threshold_wrs = [
        row["matched_player"]
        for row in wrs
        if _float(row["dynasty_asset_value"]) < 50
        and row["matched_player"] in {"Jaxon Smith-Njigba", "Puka Nacua", "CeeDee Lamb"}
    ]
    status = "review" if below_threshold_wrs else "ready"
    finding = (
        "Some elite-WR sanity players remain below the v4 core threshold."
        if below_threshold_wrs
        else "Named RB/WR balance has no automatic blocker in review-only preview."
    )
    return {
        "inspection": "RB vs WR balance",
        "status": status,
        "finding": finding,
        "evidence": f"Top RBs: {_row_list(top_rbs)}. Top WRs: {_row_list(top_wrs)}.",
        "next_action": (
            "Inspect WR production/usage/projection receipts before changing weights."
            if below_threshold_wrs
            else "Keep as review-only evidence until fixture review passes."
        ),
    }


def _young_bridge_row(rows: list[dict[str, object]]) -> dict[str, object]:
    young_rows = [
        row for row in rows if "bridge" in str(row["lifecycle"]).lower()
    ]
    missing_prior = [
        row["matched_player"]
        for row in young_rows
        if "young_player_prior" in str(row["unavailable_sections"]).split("|")
    ]
    weak_young = [
        row["matched_player"]
        for row in young_rows
        if str(row["confidence_label"]) in {"weak", "blocked"}
    ]
    status = "review" if missing_prior or weak_young else "ready"
    finding = (
        "Young-player bridge rows are visible; weak or missing-evidence rows stay reviewable."
        if status == "review"
        else "Young-player bridge contribution is visible for named bridge players."
    )
    return {
        "inspection": "Young-player bridge behavior",
        "status": status,
        "finding": finding,
        "evidence": _row_list(_top_rows(young_rows, limit=8)),
        "next_action": (
            "Review weak bridge rows instead of boosting draft-capital priors blindly."
            if status == "review"
            else "Use receipts if a young-player ordering looks surprising."
        ),
    }


def _qb_suppression_row(by_player: dict[str, dict[str, object]]) -> dict[str, object]:
    lamar = by_player.get("Lamar Jackson")
    elite_skill = [
        row
        for name, row in by_player.items()
        if name != "Lamar Jackson" and row["position"] in {"RB", "WR"}
    ]
    top_skill = max((_float(row["dynasty_asset_value"]) for row in elite_skill), default=0)
    lamar_value = _float(lamar["dynasty_asset_value"]) if lamar else 0
    status = "review" if lamar and lamar_value >= top_skill else "ready"
    return {
        "inspection": "QB suppression",
        "status": status,
        "finding": (
            "Lamar does not top the named elite RB/WR group in this 1QB preview."
            if status == "ready"
            else "Lamar equals/exceeds the named elite RB/WR group; inspect 1QB suppression."
        ),
        "evidence": (
            f"Lamar={lamar_value:.2f}; top named RB/WR={top_skill:.2f}."
            if lamar
            else "Lamar missing from named review."
        ),
        "next_action": "Inspect QB production/projection receipt before any suppression change.",
    }


def _te_suppression_row(by_player: dict[str, dict[str, object]]) -> dict[str, object]:
    bowers = by_player.get("Brock Bowers")
    top_skill = max(
        (
            _float(row["dynasty_asset_value"])
            for row in by_player.values()
            if row["position"] in {"RB", "WR"}
        ),
        default=0,
    )
    bowers_value = _float(bowers["dynasty_asset_value"]) if bowers else 0
    status = "review" if bowers and bowers_value >= top_skill else "ready"
    return {
        "inspection": "TE suppression",
        "status": status,
        "finding": (
            "Brock Bowers remains below the top named RB/WR benchmark."
            if status == "ready"
            else "Brock Bowers equals/exceeds the top named RB/WR benchmark."
        ),
        "evidence": (
            f"Bowers={bowers_value:.2f}; top named RB/WR={top_skill:.2f}."
            if bowers
            else "Brock Bowers missing from named review."
        ),
        "next_action": "Inspect TE no-premium receipt before any TE exception change.",
    }


def _aging_dropoff_row(by_player: dict[str, dict[str, object]]) -> dict[str, object]:
    keenan = by_player.get("Keenan Allen")
    cmc = by_player.get("Christian McCaffrey")
    cornerstone_rbs = [
        by_player[name]
        for name in ("Bijan Robinson", "Jahmyr Gibbs", "De'Von Achane")
        if name in by_player
    ]
    min_cornerstone_rb = min(
        (_float(row["dynasty_asset_value"]) for row in cornerstone_rbs),
        default=0,
    )
    keenan_value = _float(keenan["dynasty_asset_value"]) if keenan else 0
    status = "review" if keenan and keenan_value >= min_cornerstone_rb else "ready"
    return {
        "inspection": "Aging veteran dropoff",
        "status": status,
        "finding": (
            "Aging veteran sanity check is contained in this preview."
            if status == "ready"
            else "Keenan Allen is above a young cornerstone RB; inspect age/dropoff."
        ),
        "evidence": (
            f"Keenan={keenan_value:.2f}; CMC={_float(cmc['dynasty_asset_value']):.2f}; "
            f"lowest named young cornerstone RB={min_cornerstone_rb:.2f}."
            if keenan and cmc
            else "Keenan or CMC missing from named review."
        ),
        "next_action": "Inspect age/dropoff and production receipts before any formula change.",
    }


def _separation_row(receipt_lookup: dict[str, list[dict[str, str]]]) -> dict[str, object]:
    forbidden_rows = []
    for rows in receipt_lookup.values():
        for row in rows:
            haystack = " ".join(
                str(row.get(field) or "").lower()
                for field in ("component", "raw_fields_used", "source_status", "warning")
            )
            if any(token in haystack for token in FORBIDDEN_PRIVATE_COMPONENT_TOKENS):
                forbidden_rows.append(row)
    status = "review" if forbidden_rows else "ready"
    return {
        "inspection": "Market and league-rank separation",
        "status": status,
        "finding": (
            "No market/trade/liquidity/league-rank components appear in v4 private receipts."
            if status == "ready"
            else "Forbidden context token appears in v4 private receipts."
        ),
        "evidence": (
            "Receipt components scanned clean."
            if status == "ready"
            else f"{len(forbidden_rows)} receipt rows need inspection."
        ),
        "next_action": (
            "No patch needed."
            if status == "ready"
            else "Quarantine forbidden context before using any private value."
        ),
    }


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
    for rows in lookup.values():
        rows.sort(key=lambda row: _float(row.get("contribution")), reverse=True)
    return dict(lookup)


def _top_positive_drivers(rows: list[dict[str, str]], limit: int = 5) -> str:
    positives = [row for row in rows if _float(row.get("contribution")) > 0]
    positives.sort(key=lambda row: _float(row.get("contribution")), reverse=True)
    return " | ".join(_driver(row) for row in positives[:limit])


def _top_negative_drivers(rows: list[dict[str, str]], limit: int = 5) -> str:
    negatives = [row for row in rows if _float(row.get("contribution")) < 0]
    if negatives:
        negatives.sort(key=lambda row: _float(row.get("contribution")))
        return " | ".join(_driver(row) for row in negatives[:limit])
    warning_rows = [
        row
        for row in rows
        if str(row.get("warning") or "").strip()
        or str(row.get("unavailable_reason") or "").strip()
    ]
    warning_rows.sort(key=lambda row: _float(row.get("contribution")))
    if warning_rows:
        return (
            "No negative component contributions; caution rows: "
            + " | ".join(_driver(row) for row in warning_rows[:limit])
        )
    low_rows = sorted(rows, key=lambda row: _float(row.get("contribution")))
    if low_rows:
        return (
            "No negative component contributions; lowest contributions: "
            + " | ".join(_driver(row) for row in low_rows[:limit])
        )
    return "No receipt rows available."


def _driver(row: dict[str, str]) -> str:
    component = _label(row.get("component"))
    contribution = _float(row.get("contribution"))
    warning = str(row.get("warning") or row.get("unavailable_reason") or "").strip()
    if warning:
        return f"{component} {contribution:+.2f} ({warning})"
    return f"{component} {contribution:+.2f}"


def _component_summary(value: object) -> str:
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return ""
    parts = [
        f"{_label(component)}={_format_number(score)}"
        for component, score in sorted(parsed.items())
    ]
    return " | ".join(parts)


def _review_notes(
    row: dict[str, object],
    warnings: tuple[str, ...],
    unavailable: tuple[str, ...],
    receipts: list[dict[str, str]],
) -> str:
    notes: list[str] = []
    lifecycle = str(row.get("lifecycle") or "").lower()
    actionable_unavailable = [
        section
        for section in unavailable
        if not (section == "young_player_prior" and "established" in lifecycle)
    ]
    if str(row.get("confidence_label") or "") in {"weak", "blocked"}:
        notes.append("Weak confidence; treat as review finding.")
    if actionable_unavailable:
        notes.append("Unavailable sections: " + ", ".join(actionable_unavailable))
    route_warning = any("route" in warning for warning in warnings)
    if route_warning:
        notes.append("Route metrics remain unavailable/proxy-only.")
    if "young_player_prior" in unavailable and "established" in lifecycle:
        notes.append("Young-player prior is not applicable for established veterans.")
    if not receipts:
        notes.append("Missing receipt rows.")
    if not notes:
        notes.append("Receipt-backed review row; no automatic patch.")
    return " ".join(notes)


def _summary(
    rows: tuple[dict[str, object], ...],
    inspection_rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    matched = [row for row in rows if row["match_status"] == "matched"]
    review_rows = [
        row
        for row in matched
        if "Weak confidence" in str(row["review_notes"])
        or "Unavailable sections" in str(row["review_notes"])
    ]
    return {
        "review_status": "review_only",
        "requested_players": len(rows),
        "matched_players": len(matched),
        "missing_players": len(rows) - len(matched),
        "player_review_rows": len(review_rows),
        "inspection_rows": len(inspection_rows),
        "inspection_review_rows": sum(
            1 for row in inspection_rows if row["status"] == "review"
        ),
        "decision_ready_unlocked": False,
        "score_changes_applied": False,
    }


def _markdown(
    summary: dict[str, object],
    rows: tuple[dict[str, object], ...],
    inspection_rows: tuple[dict[str, object], ...],
    report_title: str,
) -> str:
    lines = [
        f"# {report_title}",
        "",
        "This report audits named Model v4 review-only preview rows. It does not "
        "change weights, promote rankings, or unlock decision readiness.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Inspection Findings", ""])
    lines.extend(_markdown_table(INSPECTION_HEADER, inspection_rows))
    lines.extend(["", "## Named Players", ""])
    player_table_header = (
        "matched_player",
        "position",
        "overall_rank",
        "position_rank",
        "dynasty_asset_value",
        "confidence_label",
        "lifecycle",
        "review_notes",
    )
    lines.extend(_markdown_table(player_table_header, rows))
    lines.extend(["", "## Receipt Driver Detail", ""])
    detail_header = (
        "matched_player",
        "top_positive_receipt_drivers",
        "top_negative_receipt_drivers",
        "warnings",
        "unavailable_sections",
    )
    lines.extend(_markdown_table(detail_header, rows))
    lines.append("")
    return "\n".join(lines)


def _markdown_table(
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
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


def _top_rows(rows: list[dict[str, object]], *, limit: int) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: _float(row["dynasty_asset_value"]),
        reverse=True,
    )[:limit]


def _row_list(rows: list[dict[str, object]]) -> str:
    return ", ".join(
        f"{row['matched_player']} {_float(row['dynasty_asset_value']):.2f}"
        for row in rows
    )


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


def _split(value: object) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split("|") if part.strip())


def _label(value: object) -> str:
    return str(value or "").replace("_", " ").title()


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
    number = _float(value)
    return f"{number:.2f}"


def _md_cell(value: object) -> str:
    text = str(value or "")
    return text.replace("|", "<br>").replace("\n", " ")
