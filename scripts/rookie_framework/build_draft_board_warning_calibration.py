"""Calibrate current 2026 rookie draft-board warning labels.

This is a display-label repair pass only. It preserves the existing
cfbd_enriched_baseline_v1_1 order, keeps model target tiers separate from
trap/caution severity, and writes local/manual-use exports only.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


DEFAULT_TRAP_BOARD = Path(
    "local_exports/rookie_framework/draft_capital_trap_guard_overlay_20260615/"
    "draft_capital_trap_guard_top54_overlay_20260615.csv"
)
DEFAULT_SOURCE_BOARD = Path(
    "local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/"
    "current_2026_feature_aware_candidate_board_20260615.csv"
)
DEFAULT_FOCUS = Path(
    "local_exports/rookie_framework/current_2026_top36_draft_decision_review_20260615/"
    "focus_player_decision_review_20260615.csv"
)
DEFAULT_UNMATCHED = Path(
    "local_exports/rookie_framework/current_2026_top36_draft_decision_review_20260615/"
    "unmatched_relevant_names_review_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/draft_board_warning_calibration_20260615")

FOCUS_PLAYERS = {
    "Jeremiyah Love",
    "Makai Lemon",
    "Carnell Tate",
    "KC Concepcion",
    "Jadarian Price",
    "Denzel Boston",
    "Germie Bernard",
    "Chris Bell",
    "Zachariah Branch",
    "Antonio Williams",
    "Jonah Coleman",
    "Barion Brown",
    "Kentrel Bullock",
    "Jordyn Tyson",
    "Jam Miller",
    "Jaydn Ott",
}

SEVERITY_ORDER = {
    "critical_trap_guard": 4,
    "manual_review": 3,
    "soft_note": 2,
    "none": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = columns or all_columns(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in fieldnames})


def all_columns(rows: list[dict[str, object]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def safe_int(value: object, default: int = 9999) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value)))
    except ValueError:
        return default


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value))
    except ValueError:
        return default


def target_tier(raw_tier: str, rank: int) -> str:
    if "Tier 1" in raw_tier or rank <= 9:
        return "tier_1_priority_target"
    if "Tier 2" in raw_tier or rank <= 24:
        return "tier_2_strong_consider"
    if "Tier 3" in raw_tier or rank <= 36:
        return "tier_3_value_fit"
    if "Tier 4" in raw_tier or rank <= 54:
        return "tier_4_manual_upside"
    return "tier_5_hold_or_avoid"


def source_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {normalize_name(row.get("player_name", "")): row for row in rows if row.get("player_name")}


def calibrated_severity(row: dict[str, str], source: dict[str, str]) -> tuple[str, str]:
    prior = row.get("trap_guard_warning", "none")
    reason = row.get("trap_guard_reason", "")
    rank = safe_int(row.get("rank"))
    status = source.get("status", "")
    evidence = to_float(source.get("evidence_confidence_index"))
    bust = to_float(source.get("bust_risk_index"))
    production = to_float(source.get("candidate_production_component"))
    share = to_float(source.get("candidate_market_share_component"))
    draft_round = safe_int(source.get("candidate_draft_round_used"), 0)
    unmatched = "unmatched_current_cfbd_features" in reason or source.get("candidate_cfbd_feature_status") != "deterministic_joined"
    no_profile = "no_current_cfbd_profile_selected" in reason
    no_edge = "no_standout_cfbd_production_or_share_edge" in reason or (production < 60 and share < 35)
    low_evidence = "low_or_limited_evidence_confidence" in reason or evidence < 60
    high_bust = "high_bust_risk_index" in reason or bust >= 85
    very_late = "very_late_overall_pick" in reason or draft_round >= 6
    missing_capital = "unknown_or_missing_draft_capital_inside_top54" in reason

    if prior == "none":
        if status == "manual_review_required" and (high_bust or low_evidence):
            return "manual_review", "manual status remains important, but no draft-capital trap overlay was added"
        return "none", "no specific draft-capital-trap warning beyond ordinary rookie uncertainty"

    if unmatched or no_profile:
        return "critical_trap_guard", "missing or unmatched current evidence can make the rank unreliable"
    if rank <= 24 and high_bust and no_edge:
        return "critical_trap_guard", "premium-window rank with high bust risk and no standout CFBD edge"
    if very_late and no_edge and (low_evidence or high_bust):
        return "critical_trap_guard", "very late draft-capital profile with weak support signals"
    if missing_capital and rank <= 24 and (high_bust or low_evidence):
        return "critical_trap_guard", "missing draft-capital context in the top 24 with fragility flags"

    if rank <= 24 and (draft_round >= 4 or missing_capital):
        return "manual_review", "draft-window player needs price/role confirmation because draft capital is late or missing"
    if high_bust and (low_evidence or no_edge):
        return "manual_review", "bust-risk and evidence/production context require a real check"
    if status == "manual_review_required":
        return "manual_review", "existing manual-review status should stay visible"
    if prior in {"manual_review", "hard_manual_review"}:
        return "soft_note", "context preserved as caution, but not a draft-room stop"
    return "soft_note", "low-specificity caution preserved without overwhelming the draft sheet"


def calibrated_action(tier: str, severity: str, status: str) -> str:
    if tier == "tier_5_hold_or_avoid":
        return "avoid_unless_price_collapses"
    if severity == "critical_trap_guard":
        return "manual_hold" if tier in {"tier_1_priority_target", "tier_2_strong_consider"} else "avoid_unless_price_collapses"
    if status == "manual_review_required":
        return "manual_hold"
    if tier == "tier_1_priority_target":
        return "target"
    if tier == "tier_2_strong_consider":
        return "strong_consider" if severity in {"none", "soft_note"} else "consider_at_value"
    if tier == "tier_3_value_fit":
        return "consider_at_value" if severity in {"none", "soft_note"} else "wait_for_discount"
    if tier == "tier_4_manual_upside":
        return "wait_for_discount"
    return "avoid_unless_price_collapses"


def risk_text(severity: str, calibration_reason: str, original_reason: str) -> str:
    if severity == "none":
        return "No specific draft-capital trap flag; keep normal rookie/manual warnings visible."
    if severity == "soft_note":
        return f"Context note: {calibration_reason}."
    if severity == "manual_review":
        return f"Manual review: {calibration_reason}."
    return f"Critical trap guard: {calibration_reason}."


def draft_room_note(action: str, severity: str, tier: str) -> str:
    if severity == "critical_trap_guard":
        return "Warning priority is not target priority; pause unless Tim clears the manual question."
    if action == "target":
        return "Model target; warning context should inform price, not hide target status."
    if action == "strong_consider":
        return "Strong model consider; draft if the tier and role fit the room."
    if action == "consider_at_value":
        return "Value/fit player; use price discipline."
    if action == "wait_for_discount":
        return "Let the room discount this player before acting."
    if action == "manual_hold":
        return "Hold until the manual question is answered."
    if tier == "tier_5_hold_or_avoid":
        return "Not model-cleared; do not confuse name value with draft target status."
    return "Use only as manual context."


def manual_question(row: dict[str, str], source: dict[str, str], severity: str) -> str:
    base = row.get("main_risk_manual_question") or source.get("manual_question", "")
    if severity == "critical_trap_guard":
        return f"{base} Does the evidence clearly beat the draft-capital trap risk at this price?".strip()
    if severity == "manual_review":
        return f"{base} Is the draft cost low enough for the remaining caution?".strip()
    if severity == "soft_note":
        return f"{base} Is this just context, or a reason to discount?".strip()
    return base or "Does Tim prefer this player over nearby alternatives?"


def calibrated_row(row: dict[str, str], source: dict[str, str]) -> dict[str, object]:
    rank = safe_int(row.get("rank"))
    tier = target_tier(row.get("tier", ""), rank)
    severity, calibration_reason = calibrated_severity(row, source)
    action = calibrated_action(tier, severity, source.get("status", ""))
    return {
        "model_rank": rank,
        "target_tier": tier,
        "draft_action": action,
        "trap_guard_severity": severity,
        "player": row.get("player", ""),
        "position": row.get("position", ""),
        "position_rank": row.get("position_rank", ""),
        "primary_positive_reason": row.get("main_positive_reason", ""),
        "primary_risk_or_warning": risk_text(severity, calibration_reason, row.get("trap_guard_reason", "")),
        "manual_question_for_tim": manual_question(row, source, severity),
        "draft_room_note": draft_room_note(action, severity, tier),
        "original_trap_guard_warning": row.get("trap_guard_warning", ""),
        "original_trap_guard_reason": row.get("trap_guard_reason", ""),
        "candidate_model": source.get("candidate_model", row.get("candidate_model", "")),
        "main_ranking_formula_changed": "no",
        "board_order_changed": "no",
        "production_allowed": "no",
        "promotion_status": "local_manual_warning_calibration_only",
    }


def focus_hold_rows(
    final_rows: list[dict[str, object]],
    focus_rows: list[dict[str, str]],
    unmatched_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    existing = {normalize_name(str(row.get("player", ""))) for row in final_rows}
    extras: list[dict[str, object]] = []
    by_name = {
        normalize_name(row.get("player", "")): row
        for row in [*focus_rows, *unmatched_rows]
        if row.get("player")
    }
    for name in sorted(FOCUS_PLAYERS):
        key = normalize_name(name)
        if key in existing or key not in by_name:
            continue
        row = by_name[key]
        extras.append(
            {
                "model_rank": row.get("model_rank", ""),
                "target_tier": "tier_5_hold_or_avoid",
                "draft_action": "avoid_unless_price_collapses",
                "trap_guard_severity": "critical_trap_guard" if row.get("model_clearance") == "not_model_cleared" else "manual_review",
                "player": row.get("player", ""),
                "position": row.get("position", ""),
                "position_rank": row.get("position_rank", ""),
                "primary_positive_reason": row.get("main_positive_feature_reason", ""),
                "primary_risk_or_warning": row.get("main_risk_warning", ""),
                "manual_question_for_tim": row.get("manual_question", ""),
                "draft_room_note": "Outside top-54 focus hold; warning priority is separate from target priority.",
                "source_view": "outside_top54_focus",
            }
        )
    return extras


def top_model_targets(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if row["target_tier"] in {"tier_1_priority_target", "tier_2_strong_consider"}
        and row["draft_action"] in {"target", "strong_consider", "consider_at_value", "manual_hold"}
    ][:24]


def highest_warning_priority(rows: list[dict[str, object]], extra_focus: list[dict[str, object]]) -> list[dict[str, object]]:
    combined = [*rows, *extra_focus]
    warning_rows = [row for row in combined if row.get("trap_guard_severity") in {"critical_trap_guard", "manual_review"}]
    return sorted(
        warning_rows,
        key=lambda row: (
            -SEVERITY_ORDER.get(str(row.get("trap_guard_severity")), 0),
            safe_int(row.get("model_rank")),
            str(row.get("player", "")),
        ),
    )[:30]


def change_rows(old_rows: list[dict[str, str]], new_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    old_by_name = {normalize_name(row.get("player", "")): row for row in old_rows}
    output = []
    for row in new_rows:
        old = old_by_name.get(normalize_name(str(row.get("player", ""))), {})
        output.append(
            {
                "model_rank": row.get("model_rank", ""),
                "player": row.get("player", ""),
                "old_trap_guard_warning": old.get("trap_guard_warning", ""),
                "new_trap_guard_severity": row.get("trap_guard_severity", ""),
                "old_draft_action": old.get("draft_action", ""),
                "new_draft_action": row.get("draft_action", ""),
                "change_note": "calibrated warning display only; rank unchanged",
            }
        )
    return output


def tier_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter(str(row["target_tier"]) for row in rows)
    severity_by_tier: dict[str, Counter[str]] = {}
    for row in rows:
        severity_by_tier.setdefault(str(row["target_tier"]), Counter())[str(row["trap_guard_severity"])] += 1
    output = []
    for tier in sorted(counts):
        sev = severity_by_tier[tier]
        output.append(
            {
                "target_tier": tier,
                "player_count": counts[tier],
                "none": sev["none"],
                "soft_note": sev["soft_note"],
                "manual_review": sev["manual_review"],
                "critical_trap_guard": sev["critical_trap_guard"],
            }
        )
    return output


def position_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(rows, key=lambda row: (str(row["position"]), safe_int(row["model_rank"])))


def verdict_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    severity = Counter(str(row["trap_guard_severity"]) for row in rows)
    critical = severity["critical_trap_guard"]
    return [
        {
            "verdict": "calibration_quality",
            "status": "GREEN" if critical < len(rows) / 2 else "YELLOW",
            "reason": "critical trap guards are reserved for the highest-priority risks",
        },
        {
            "verdict": "draft_use_clarity",
            "status": "GREEN",
            "reason": "model rank, target tier, draft action, and trap severity are separate columns",
        },
        {
            "verdict": "manual_draft_trust",
            "status": "YELLOW",
            "reason": "usable as a manual draft board with warnings visible; not a blind ranking",
        },
        {
            "verdict": "anti_cheat_leakage",
            "status": "GREEN",
            "reason": "no tuning, no ADP/market private input, no probabilities/bands, no app or production wiring",
        },
        {
            "verdict": "main_ranking_formula_changed",
            "status": "NO",
            "reason": "candidate_model remains cfbd_enriched_baseline_v1_1",
        },
        {
            "verdict": "board_order_changed",
            "status": "NO",
            "reason": "final board remains sorted by existing model rank",
        },
    ]


def build_exports(
    trap_board: Path,
    source_board: Path,
    focus_path: Path,
    unmatched_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    trap_rows = sorted(read_csv(trap_board), key=lambda row: safe_int(row.get("rank")))
    source_by_name = source_lookup(read_csv(source_board))
    final_rows = [
        calibrated_row(row, source_by_name.get(normalize_name(row.get("player", "")), {}))
        for row in trap_rows
    ]
    focus_extra = focus_hold_rows(final_rows, read_csv(focus_path), read_csv(unmatched_path))
    targets = top_model_targets(final_rows)
    warning_priority = highest_warning_priority(final_rows, focus_extra)
    changes = change_rows(trap_rows, final_rows)
    summary = tier_summary(final_rows)
    positions = position_rows(final_rows)
    verdicts = verdict_rows(final_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_2026_final_manual_draft_board_warning_calibrated_20260615.csv", final_rows)
    write_csv(output_dir / "rookie_2026_top_model_targets_20260615.csv", targets)
    write_csv(output_dir / "rookie_2026_highest_warning_priority_20260615.csv", warning_priority)
    write_csv(output_dir / "rookie_2026_warning_calibration_changes_20260615.csv", changes)
    write_csv(output_dir / "rookie_2026_position_lists_warning_calibrated_20260615.csv", positions)
    write_csv(output_dir / "rookie_2026_tier_summary_warning_calibrated_20260615.csv", summary)
    write_csv(output_dir / "rookie_2026_warning_calibration_verdicts_20260615.csv", verdicts)
    write_readme(output_dir)
    return {
        "final_rows": final_rows,
        "targets": targets,
        "warning_priority": warning_priority,
        "changes": changes,
        "summary": summary,
        "verdicts": verdicts,
        "output_dir": output_dir,
    }


def write_readme(output_dir: Path) -> None:
    text = [
        "# Rookie Draft Board Warning Calibration",
        "",
        "Local/manual-use warning label repair for the current 2026 rookie draft board.",
        "Main model remains cfbd_enriched_baseline_v1_1 and board order is unchanged.",
        "Top model targets and highest warning priority are separate views.",
        "No production ranking, app output, probabilities, bands, hidden sort keys, or promoted artifacts.",
    ]
    (output_dir / "README_ROOKIE_DRAFT_BOARD_WARNING_CALIBRATION_20260615.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trap-board", type=Path, default=DEFAULT_TRAP_BOARD)
    parser.add_argument("--source-board", type=Path, default=DEFAULT_SOURCE_BOARD)
    parser.add_argument("--focus", type=Path, default=DEFAULT_FOCUS)
    parser.add_argument("--unmatched", type=Path, default=DEFAULT_UNMATCHED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.trap_board, args.source_board, args.focus, args.unmatched, args.output_dir)
    severity = Counter(str(row["trap_guard_severity"]) for row in result["final_rows"])
    print(f"final_rows={len(result['final_rows'])}")
    print(f"top_model_targets={len(result['targets'])}")
    print(f"highest_warning_priority={len(result['warning_priority'])}")
    print(f"severity_counts={dict(sorted(severity.items()))}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
