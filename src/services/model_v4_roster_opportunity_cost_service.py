from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "roster_opportunity_cost/latest"
DOC_PATH = Path("docs/model_v4/ROSTER_OPPORTUNITY_COST_ENGINE.md")
VERSION = "model_v4_roster_opportunity_cost_0.1.0"

ROSTER_STATE_ROWS = MODEL_ROOT / "decision_calibration/latest/niners_roster_state_review.csv"
CUT_KEEP_ROWS = MODEL_ROOT / "decision_pressure/latest/cut_keep_pressure_review_rows.csv"
TRADE_AWAY_ROWS = MODEL_ROOT / "trade_review/latest/trade_away_candidate_review_rows.csv"
STARTUP_SLOT_ROWS = MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_review_rows.csv"
PICK_BASELINE_ROWS = MODEL_ROOT / "pick_values/latest/pick_value_baselines_review.csv"
PICK_INVENTORY_ROWS = MODEL_ROOT / "pick_trade_defer/latest/niners_pick_inventory_review_rows.csv"
ROOKIE_BOARD_ROWS = MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
CURRENT_VALUE_ROWS = MODEL_ROOT / "current_value/latest/current_player_value_review_rows.csv"

REVIEW_ONLY_USE = "review_only_roster_opportunity_cost_not_cut_keep_recommendation"
BLOCKED_USE = "do_not_use_as_cut_keep_trade_roster_or_draft_recommendation"
MANUAL_ONLY_NO_BASELINE = "manual_only_no_exact_model_baseline"

ROW_HEADER = (
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "current_model_score",
    "source_path",
    "source_column",
    "lineage_class",
    "startup_slot_rank",
    "rookie_pick_equivalent",
    "pick_baseline_status",
    "pick_equivalent_confidence",
    "pick_equivalent_warning",
    "nearest_rookies_above",
    "nearest_rookies_below",
    "replacement_options_nearby",
    "pressure_status",
    "trade_context_status",
    "opportunity_cost_label",
    "opportunity_cost_note",
    "warning_flags",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPONENT_HEADER = (
    "component_key",
    "player_name",
    "component_layer",
    "component_name",
    "component_value",
    "component_context",
    "allowed_input_file",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

WARNING_HEADER = (
    "warning_key",
    "player_name",
    "warning_layer",
    "warning_code",
    "warning_detail",
    "next_action",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class RosterOpportunityCostResult:
    rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_roster_opportunity_cost() -> RosterOpportunityCostResult:
    roster_rows = _read_rows(ROSTER_STATE_ROWS)
    pressure_rows = _read_rows(CUT_KEEP_ROWS)
    trade_rows = _read_rows(TRADE_AWAY_ROWS)
    startup_rows = _read_rows(STARTUP_SLOT_ROWS)
    pick_rows = _read_rows(PICK_INVENTORY_ROWS)
    rookie_rows = _read_rows(ROOKIE_BOARD_ROWS)
    current_rows = _read_rows(CURRENT_VALUE_ROWS)

    pressure_lookup = {_normalize(row.get("player_name")): row for row in pressure_rows}
    trade_lookup = {_normalize(row.get("player_name")): row for row in trade_rows}
    startup_lookup = {
        _normalize(row.get("player_or_asset")): row
        for row in startup_rows
        if row.get("entity_type") in {"current_rostered_player", "potential_drop_player"}
    }
    current_lookup = {_normalize(row.get("player_name")): row for row in current_rows}
    pick_baselines = _pick_baselines(pick_rows)
    rookie_candidates = _rookie_candidates(rookie_rows)
    startup_candidates = _startup_replacement_candidates(startup_rows)

    rows: list[dict[str, object]] = []
    for roster in roster_rows:
        name = roster.get("player_name", "")
        norm = _normalize(name)
        pressure = pressure_lookup.get(norm, {})
        trade = trade_lookup.get(norm, {})
        startup = startup_lookup.get(norm, {})
        current = current_lookup.get(norm, {})
        score = _first_float(
            startup.get("model_score"),
            roster.get("dynasty_asset_value_review_score"),
            current.get("checkpoint_review_score"),
        )
        source_path, source_column, lineage_class = _score_source(startup, roster, current)
        rank = startup.get("startup_slot_rank", "")
        (
            equivalent,
            baseline_status,
            equivalent_confidence,
            equivalent_warning,
        ) = _rookie_pick_equivalent(score, pick_baselines)
        above, below = _nearest_rookies(score, rookie_candidates)
        replacements = _nearby_replacements(score, startup_candidates, norm)
        pressure_status = pressure.get("pressure_band") or "rostered_review"
        trade_status = trade.get("trade_away_review_band") or "no_trade_context_row"
        label = _opportunity_label(score, pressure_status, trade_status, equivalent_warning)
        warnings = _join_present(
            roster.get("warning_flags", ""),
            pressure.get("warning_flags", ""),
            trade.get("warning_flags", ""),
            startup.get("warning_flags", ""),
            equivalent_warning,
            "review_only_no_cut_keep_recommendation",
        )
        rows.append(
            {
                "player_name": name,
                "normalized_player_name": roster.get("normalized_player_name", norm),
                "position": roster.get("position", ""),
                "nfl_team": roster.get("nfl_team", ""),
                "current_model_score": _blank(score),
                "source_path": source_path,
                "source_column": source_column,
                "lineage_class": lineage_class,
                "startup_slot_rank": rank,
                "rookie_pick_equivalent": equivalent,
                "pick_baseline_status": baseline_status,
                "pick_equivalent_confidence": equivalent_confidence,
                "pick_equivalent_warning": equivalent_warning,
                "nearest_rookies_above": above,
                "nearest_rookies_below": below,
                "replacement_options_nearby": replacements,
                "pressure_status": pressure_status,
                "trade_context_status": trade_status,
                "opportunity_cost_label": label,
                "opportunity_cost_note": _opportunity_note(name, score, equivalent, label),
                "warning_flags": warnings,
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )

    rows = sorted(
        rows,
        key=lambda row: (
            _label_order(str(row["opportunity_cost_label"])),
            -float(row["current_model_score"] or 0),
            str(row["player_name"]).lower(),
        ),
    )
    component_rows = _component_rows(rows)
    warning_rows = _warning_rows(rows)
    return RosterOpportunityCostResult(
        rows=tuple(rows),
        component_rows=tuple(component_rows),
        warning_rows=tuple(warning_rows),
        doc_text=_doc_text(rows),
    )


def _score_source(
    startup: dict[str, str],
    roster: dict[str, str],
    current: dict[str, str],
) -> tuple[str, str, str]:
    if _float(startup.get("model_score")) is not None:
        return str(STARTUP_SLOT_ROWS), "model_score", "review_v4_startup_slot_context"
    if _float(roster.get("dynasty_asset_value_review_score")) is not None:
        return (
            str(ROSTER_STATE_ROWS),
            "dynasty_asset_value_review_score",
            "review_v4_roster_state_context",
        )
    if _float(current.get("checkpoint_review_score")) is not None:
        return str(CURRENT_VALUE_ROWS), "checkpoint_review_score", "review_v4_current_player"
    return "", "", "unknown_no_primary_score"


def write_roster_opportunity_cost_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: RosterOpportunityCostResult | None = None,
) -> dict[str, Path]:
    result = result or build_roster_opportunity_cost()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "rows": output / "roster_opportunity_cost_rows.csv",
        "component_rows": output / "roster_opportunity_cost_component_rows.csv",
        "warnings": output / "roster_opportunity_cost_warnings.csv",
        "doc": Path(doc_path),
    }
    _write_csv(paths["rows"], ROW_HEADER, result.rows)
    _write_csv(paths["component_rows"], COMPONENT_HEADER, result.component_rows)
    _write_csv(paths["warnings"], WARNING_HEADER, result.warning_rows)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _pick_baselines(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        score = _float(row.get("pick_value_review_score"))
        if score is None:
            continue
        if row.get("baseline_match_status") not in {"", "matched_pick_value_baseline"}:
            continue
        output.append(
            {
                "pick_label": row.get("pick_label", ""),
                "score": score,
                "tier_label": row.get("tier_label", ""),
            }
        )
    return sorted(output, key=lambda row: -float(row["score"]))


def _rookie_candidates(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        if row.get("evidence_status") not in {"draftable_review", "manual_scout_source_review"}:
            continue
        score = _float(row.get("league_format_adjusted_score"))
        if score is None:
            continue
        output.append(
            {
                "name": row.get("prospect_name", ""),
                "position": row.get("position", ""),
                "score": score,
                "rank": _int(row.get("board_rank")) or 999,
            }
        )
    return sorted(output, key=lambda row: -float(row["score"]))


def _startup_replacement_candidates(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        if row.get("entity_type") == "owned_rookie_pick":
            continue
        score = _float(row.get("model_score"))
        if score is None:
            continue
        output.append(
            {
                "name": row.get("player_or_asset", ""),
                "position": row.get("position", ""),
                "score": score,
                "norm": _normalize(row.get("player_or_asset")),
            }
        )
    return output


def _rookie_pick_equivalent(
    score: float | None,
    pick_baselines: list[dict[str, object]],
) -> tuple[str, str, str, str]:
    if score is None:
        return (
            "rookie_pick_equivalent_uncertain",
            "score_missing",
            "rookie_pick_equivalent_uncertain",
            "rookie_pick_equivalent_uncertain",
        )
    if not pick_baselines:
        return (
            "rookie_pick_equivalent_uncertain",
            "pick_value_baseline_missing",
            "rookie_pick_equivalent_uncertain",
            "pick_value_baseline_missing",
        )
    closest = min(pick_baselines, key=lambda row: abs(float(row["score"]) - score))
    gap = abs(float(closest["score"]) - score)
    lowest = min(pick_baselines, key=lambda row: float(row["score"]))
    highest = max(pick_baselines, key=lambda row: float(row["score"]))
    if score < float(lowest["score"]) - 12:
        return (
            f"below admitted owned pick baseline floor ({lowest['pick_label']})",
            MANUAL_ONLY_NO_BASELINE,
            "no_exact_model_equivalent",
            f"rookie_pick_equivalent_uncertain|{MANUAL_ONLY_NO_BASELINE}",
        )
    if score > float(highest["score"]) + 12:
        return (
            f"above owned pick baseline ceiling ({highest['pick_label']})",
            "above_owned_pick_baseline_ceiling",
            "rookie_pick_equivalent_uncertain",
            "rookie_pick_equivalent_uncertain",
        )
    warning = "rookie_pick_equivalent_uncertain" if gap > 8 else ""
    confidence = "low_gap_uncertain" if warning else "closest_owned_pick_context"
    return (
        f"around owned {closest['pick_label']} ({closest['tier_label']})",
        "matched_owned_pick_baseline",
        confidence,
        warning,
    )


def _nearest_rookies(
    score: float | None,
    rookies: list[dict[str, object]],
) -> tuple[str, str]:
    if score is None:
        return "", ""
    above = [
        f"{row['name']} {row['position']} ({row['score']})"
        for row in sorted(
            [row for row in rookies if float(row["score"]) >= score],
            key=lambda row: float(row["score"]) - score,
        )[:3]
    ]
    below = [
        f"{row['name']} {row['position']} ({row['score']})"
        for row in sorted(
            [row for row in rookies if float(row["score"]) < score],
            key=lambda row: score - float(row["score"]),
        )[:3]
    ]
    return " | ".join(above), " | ".join(below)


def _nearby_replacements(
    score: float | None,
    candidates: list[dict[str, object]],
    player_norm: str,
) -> str:
    if score is None:
        return ""
    nearby = sorted(
        [row for row in candidates if row["norm"] != player_norm],
        key=lambda row: abs(float(row["score"]) - score),
    )[:5]
    return " | ".join(f"{row['name']} {row['position']} ({row['score']})" for row in nearby)


def _opportunity_label(
    score: float | None,
    pressure_status: str,
    trade_status: str,
    equivalent_warning: str,
) -> str:
    if score is None:
        return "manual_review_required"
    if "missing" in pressure_status or "source" in pressure_status:
        return "injury_or_source_uncertain"
    if score >= 50:
        return "expensive_to_cut"
    if pressure_status == "required_pressure_zone_review" and (
        "shop" in trade_status or "liquidity" in trade_status
    ):
        return "trade_context_before_cut_review"
    if score < 20 and pressure_status in {
        "required_pressure_zone_review",
        "protectable_depth_review",
    }:
        return "replaceable_depth"
    if equivalent_warning:
        return "rookie_pick_equivalent_uncertain"
    return "manual_review_required"


def _opportunity_note(name: str, score: float | None, equivalent: str, label: str) -> str:
    if score is None:
        return f"{name} has no exact startup-slot score; review manually."
    if label == "expensive_to_cut":
        return (
            f"Dropping {name} would remove a model asset near {equivalent}; "
            "review trade and replacement context first."
        )
    if label == "replaceable_depth":
        return (
            f"{name} sits in a lower internal slot band; compare replacement options, "
            "but this is not a cut instruction."
        )
    if label == "trade_context_before_cut_review":
        return f"{name} has roster pressure; review trade context before any cut logic."
    return f"{name} requires human review; opportunity cost is {equivalent}."


def _component_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        base = _normalize(row["player_name"])
        for name, value, context, source in (
            (
                "current_model_score",
                row["current_model_score"],
                "Current model score used for opportunity-cost slotting.",
                str(ROSTER_STATE_ROWS),
            ),
            (
                "startup_slot_rank",
                row["startup_slot_rank"],
                "Internal startup slot rank from review-only simulator.",
                str(STARTUP_SLOT_ROWS),
            ),
            (
                "rookie_pick_equivalent",
                row["rookie_pick_equivalent"],
                "Closest owned rookie pick baseline; review-only.",
                str(PICK_INVENTORY_ROWS),
            ),
            (
                "pick_baseline_status",
                row["pick_baseline_status"],
                "Whether exact pick-equivalent math is admitted or blocked.",
                str(PICK_INVENTORY_ROWS),
            ),
            (
                "pick_equivalent_confidence",
                row["pick_equivalent_confidence"],
                "Confidence label for the review-only pick equivalent.",
                str(PICK_INVENTORY_ROWS),
            ),
            (
                "pressure_status",
                row["pressure_status"],
                "Roster pressure context, not cut instruction.",
                str(CUT_KEEP_ROWS),
            ),
            (
                "trade_context_status",
                row["trade_context_status"],
                "Trade-away context, not sell instruction.",
                str(TRADE_AWAY_ROWS),
            ),
        ):
            output.append(
                {
                    "component_key": f"{base}:{name}",
                    "player_name": row["player_name"],
                    "component_layer": "roster_opportunity_cost",
                    "component_name": name,
                    "component_value": value,
                    "component_context": context,
                    "allowed_input_file": source,
                    "allowed_use": REVIEW_ONLY_USE,
                    "blocked_use": BLOCKED_USE,
                    "formula_version": VERSION,
                }
            )
    return output


def _warning_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        for warning in str(row.get("warning_flags", "")).split("|"):
            if not warning:
                continue
            output.append(
                {
                    "warning_key": f"{_normalize(row['player_name'])}:{warning}",
                    "player_name": row["player_name"],
                    "warning_layer": "roster_opportunity_cost",
                    "warning_code": warning,
                    "warning_detail": warning.replace("_", " "),
                    "next_action": "Use as review-only context; human decision required.",
                    "allowed_use": REVIEW_ONLY_USE,
                    "blocked_use": BLOCKED_USE,
                    "formula_version": VERSION,
                }
            )
    return output


def _doc_text(rows: list[dict[str, object]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["opportunity_cost_label"])] = (
            counts.get(str(row["opportunity_cost_label"]), 0) + 1
        )
    lines = [
        "# Roster Cut Opportunity-Cost Engine",
        "",
        "## Scope",
        "",
        "This review-only engine translates Niners roster players into internal "
        "startup slots, nearby rookies, and rookie pick-equivalent context. It does "
        "not create cut, keep, trade, or draft recommendations.",
        "",
        "## Label Counts",
        "",
        "| Label | Rows |",
        "|---|---:|",
    ]
    for label, count in sorted(counts.items()):
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Review-only outputs only.",
            "- No My Team, War Board, active rankings, app promotion, or readiness gates changed.",
            "- Rookie pick equivalents are context, not exact market prices.",
            "- Pick equivalents are anchored to owned Niners picks, not the whole market curve.",
            "- Missing, floor, ceiling, or distant pick baselines are marked uncertain.",
            "- ADP, market rankings, projections, mock drafts, and consensus are not used.",
        ]
    )
    return "\n".join(lines) + "\n"


def _label_order(label: str) -> int:
    order = {
        "expensive_to_cut": 0,
        "trade_context_before_cut_review": 1,
        "injury_or_source_uncertain": 2,
        "rookie_pick_equivalent_uncertain": 3,
        "manual_review_required": 4,
        "replaceable_depth": 5,
    }
    return order.get(label, 99)


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _normalize(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", text)
    return re.sub(r"[^a-z0-9]", "", text)


def _join_present(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        for part in str(value or "").split("|"):
            clean = part.strip()
            if clean and clean not in parts:
                parts.append(clean)
    return "|".join(parts)


def _first_float(*values: object) -> float | None:
    for value in values:
        parsed = _float(value)
        if parsed is not None:
            return parsed
    return None


def _float(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _int(value: object) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _blank(value: float | None) -> str | float:
    return "" if value is None else round(value, 4)
