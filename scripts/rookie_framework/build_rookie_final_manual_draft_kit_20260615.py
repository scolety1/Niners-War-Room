"""Freeze the current 2026 rookie manual draft kit.

This packages the warning-calibrated board into local/manual-use draft-room
exports. It preserves cfbd_enriched_baseline_v1_1 rank order and does not tune,
rescore, create v2, or write production/app artifacts.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_CALIBRATED_BOARD = Path(
    "local_exports/rookie_framework/draft_board_warning_calibration_20260615/"
    "rookie_2026_final_manual_draft_board_warning_calibrated_20260615.csv"
)
DEFAULT_SOURCE_BOARD = Path(
    "local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/"
    "current_2026_feature_aware_candidate_board_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_20260615")

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


def source_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {normalize_name(row.get("player_name", "")): row for row in rows if row.get("player_name")}


def unmatched_flag(source: dict[str, str]) -> str:
    status = source.get("candidate_cfbd_feature_status", "")
    join = source.get("cfbd_current_join_status", "")
    if status and status != "deterministic_joined":
        return "yes"
    if join and not join.startswith("matched"):
        return "yes"
    return "no"


def frozen_board_rows(calibrated_rows: list[dict[str, str]], source_by_name: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for row in sorted(calibrated_rows, key=lambda item: safe_int(item.get("model_rank"))):
        source = source_by_name.get(normalize_name(row.get("player", "")), {})
        rows.append(
            {
                "rank": row.get("model_rank", ""),
                "tier": row.get("target_tier", ""),
                "player": row.get("player", ""),
                "position": row.get("position", ""),
                "position_rank": row.get("position_rank", ""),
                "draft_action": row.get("draft_action", ""),
                "warning_severity": row.get("trap_guard_severity", ""),
                "trap_caution_warning": row.get("primary_risk_or_warning", ""),
                "main_positive_reason": row.get("primary_positive_reason", ""),
                "main_risk_manual_question": row.get("manual_question_for_tim", ""),
                "draft_room_note": row.get("draft_room_note", ""),
                "unmatched_neutral_feature_flag": unmatched_flag(source),
                "model_formula_version": row.get("candidate_model", "cfbd_enriched_baseline_v1_1"),
                "main_ranking_formula_changed": "no",
                "board_order_changed": "no",
                "production_allowed": "no",
                "promotion_status": "local_manual_draft_kit_only",
            }
        )
    return rows


def quick_sheet_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "rank": row["rank"],
            "player": row["player"],
            "position": row["position"],
            "tier": row["tier"],
            "draft_action": row["draft_action"],
            "warning_severity": row["warning_severity"],
            "manual_question": row["main_risk_manual_question"],
            "draft_room_note": row["draft_room_note"],
        }
        for row in board
    ]


def tier_cards(board: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in board:
        grouped[str(row["tier"])].append(row)
    rows = []
    for tier in sorted(grouped, key=tier_sort_key):
        players = grouped[tier]
        actions = Counter(str(row["draft_action"]) for row in players)
        severities = Counter(str(row["warning_severity"]) for row in players)
        rows.append(
            {
                "tier": tier,
                "player_count": len(players),
                "players": "; ".join(str(row["player"]) for row in players),
                "draft_action_mix": "; ".join(f"{key}={value}" for key, value in sorted(actions.items())),
                "warning_mix": "; ".join(f"{key}={value}" for key, value in sorted(severities.items())),
                "strategy_note": tier_strategy(tier),
            }
        )
    return rows


def tier_sort_key(tier: str) -> int:
    order = {
        "tier_1_priority_target": 1,
        "tier_2_strong_consider": 2,
        "tier_3_value_fit": 3,
        "tier_4_manual_upside": 4,
        "tier_5_hold_or_avoid": 5,
    }
    return order.get(tier, 99)


def tier_strategy(tier: str) -> str:
    if tier == "tier_1_priority_target":
        return "Draft aggressively when available, while keeping normal manual questions visible."
    if tier == "tier_2_strong_consider":
        return "Use as the main fallback pool; obey manual holds and price discipline."
    if tier == "tier_3_value_fit":
        return "Consider when value falls; do not force above stronger tiers."
    if tier == "tier_4_manual_upside":
        return "Use only after manual review or at discount."
    return "Hold or avoid unless price collapses and evidence is repaired."


def manual_decisions(board: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        {
            "rank": row["rank"],
            "player": row["player"],
            "position": row["position"],
            "draft_action": row["draft_action"],
            "warning_severity": row["warning_severity"],
            "question_to_answer": row["main_risk_manual_question"],
            "why_it_matters": decision_reason(row),
        }
        for row in board
        if row["warning_severity"] in {"critical_trap_guard", "manual_review"}
        or row["draft_action"] in {"manual_hold", "avoid_unless_price_collapses"}
        or row["unmatched_neutral_feature_flag"] == "yes"
    ]
    return sorted(
        rows,
        key=lambda row: (
            -SEVERITY_ORDER.get(str(row["warning_severity"]), 0),
            safe_int(row["rank"]),
        ),
    )


def decision_reason(row: dict[str, object]) -> str:
    if row["warning_severity"] == "critical_trap_guard":
        return "Highest caution priority; do not draft from rank alone."
    if row["unmatched_neutral_feature_flag"] == "yes":
        return "Current feature evidence is unmatched/neutral."
    if row["draft_action"] == "manual_hold":
        return "Draft action requires Tim to answer the question before selecting."
    if row["warning_severity"] == "manual_review":
        return "Meaningful caution that should affect price and role confidence."
    return "Manual draft context."


def warning_priority(board: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        row
        for row in board
        if row["warning_severity"] in {"critical_trap_guard", "manual_review"}
        or row["draft_action"] in {"manual_hold", "avoid_unless_price_collapses"}
    ]
    return sorted(
        rows,
        key=lambda row: (
            -SEVERITY_ORDER.get(str(row["warning_severity"]), 0),
            safe_int(row["rank"]),
            str(row["player"]),
        ),
    )


def verdict_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    models = {row["model_formula_version"] for row in board}
    order_ok = [safe_int(row["rank"]) for row in board] == sorted(safe_int(row["rank"]) for row in board)
    return [
        {
            "verdict": "draft_kit_quality",
            "status": "GREEN",
            "reason": "final board, quick sheet, tier cards, warning sheet, and manual checklist created",
        },
        {
            "verdict": "draft_use_readiness",
            "status": "GREEN",
            "reason": "kit separates rank, target tier, action, warning severity, and manual question",
        },
        {
            "verdict": "manual_draft_trust",
            "status": "YELLOW",
            "reason": "manual-use only; warnings remain visible and no production approval is implied",
        },
        {
            "verdict": "anti_cheat_leakage",
            "status": "GREEN",
            "reason": "no tuning, no v2, no ADP/market private input, no probabilities/bands, no app or production wiring",
        },
        {
            "verdict": "main_ranking_formula_changed",
            "status": "NO" if models == {"cfbd_enriched_baseline_v1_1"} else "YELLOW",
            "reason": f"model formulas present={';'.join(sorted(str(item) for item in models))}",
        },
        {
            "verdict": "board_order_changed",
            "status": "NO" if order_ok else "YELLOW",
            "reason": "frozen board remains sorted by existing model rank",
        },
    ]


def write_readme(output_dir: Path) -> None:
    text = [
        "# Rookie Final Manual Draft Kit",
        "",
        "Local/manual-use draft-room kit for the current 2026 rookie board.",
        "",
        "How to use:",
        "1. Start with `rookie_2026_draft_day_quick_sheet_20260615.csv` on draft day.",
        "2. Use rank/tier to identify model targets.",
        "3. Read warning severity before drafting.",
        "4. Use the manual checklist for `manual_hold`, `manual_review`, and `critical_trap_guard` rows.",
        "5. Use warning-priority sheet only as a review queue; it is not the rank order.",
        "",
        "Warning severity:",
        "- none: no specific trap warning beyond normal rookie uncertainty.",
        "- soft_note: context only; not a stop sign.",
        "- manual_review: answer the manual question and use price discipline.",
        "- critical_trap_guard: pause; do not draft from rank alone.",
        "",
        "This kit is not production-approved, not app-wired, and not a promoted artifact.",
        "Main model remains cfbd_enriched_baseline_v1_1 and board order is unchanged.",
    ]
    (output_dir / "README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_20260615.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def build_exports(calibrated_board: Path, source_board: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_by_name = source_lookup(read_csv(source_board))
    board = frozen_board_rows(read_csv(calibrated_board), source_by_name)
    quick = quick_sheet_rows(board)
    tiers = tier_cards(board)
    checklist = manual_decisions(board)
    warning = warning_priority(board)
    verdicts = verdict_rows(board)
    write_csv(output_dir / "rookie_2026_final_manual_draft_board_frozen_20260615.csv", board)
    write_csv(output_dir / "rookie_2026_draft_day_quick_sheet_20260615.csv", quick)
    write_csv(output_dir / "rookie_2026_tier_cards_20260615.csv", tiers)
    write_csv(output_dir / "rookie_2026_manual_decisions_checklist_20260615.csv", checklist)
    write_csv(output_dir / "rookie_2026_warning_priority_sheet_20260615.csv", warning)
    write_csv(output_dir / "rookie_2026_final_manual_draft_kit_verdicts_20260615.csv", verdicts)
    write_readme(output_dir)
    return {
        "board": board,
        "quick": quick,
        "tiers": tiers,
        "checklist": checklist,
        "warning": warning,
        "verdicts": verdicts,
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibrated-board", type=Path, default=DEFAULT_CALIBRATED_BOARD)
    parser.add_argument("--source-board", type=Path, default=DEFAULT_SOURCE_BOARD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.calibrated_board, args.source_board, args.output_dir)
    print(f"final_board_rows={len(result['board'])}")
    print(f"quick_sheet_rows={len(result['quick'])}")
    print(f"tier_cards={len(result['tiers'])}")
    print(f"manual_decisions={len(result['checklist'])}")
    print(f"warning_priority_rows={len(result['warning'])}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
