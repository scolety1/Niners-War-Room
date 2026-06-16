"""Build a narrow draft-capital trap guard overlay for the current 2026 board.

The overlay is warning/manual-review only. It keeps the existing
cfbd_enriched_baseline_v1_1 rank order and does not tune weights, create a v2
formula, or write production/app outputs.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_BOARD = Path(
    "local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/"
    "current_2026_feature_aware_candidate_board_20260615.csv"
)
DEFAULT_DECISION_SHEET = Path(
    "local_exports/rookie_framework/current_2026_top36_draft_decision_review_20260615/"
    "draft_day_decision_sheet_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/draft_capital_trap_guard_overlay_20260615")
TOP_N = 54


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


def normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def tier_for_rank(rank: int, status: str, unmatched: bool) -> str:
    if unmatched or status in {"blocked", "unavailable"}:
        return "Tier 5 avoid/hold unless price drops"
    if rank <= 9:
        return "Tier 1 priority targets"
    if rank <= 24:
        return "Tier 2 strong considers"
    if rank <= 36:
        return "Tier 3 value/fit targets"
    if rank <= TOP_N:
        return "Tier 4 manual-review upside"
    return "outside_top54"


def draft_action(row: dict[str, str], decision_by_name: dict[str, dict[str, str]]) -> str:
    key = normalize_name(row.get("player_name", ""))
    if key in decision_by_name:
        return decision_by_name[key].get("draft_action", "")
    status = row.get("status", "")
    if row.get("candidate_cfbd_feature_status") != "deterministic_joined" or status in {"blocked", "unavailable"}:
        return "avoid"
    if status == "manual_review_required":
        return "manual hold"
    return "wait"


def feature_reason(row: dict[str, str], decision_by_name: dict[str, dict[str, str]]) -> str:
    key = normalize_name(row.get("player_name", ""))
    if key in decision_by_name:
        return decision_by_name[key].get("feature_reason", "")
    production = to_float(row.get("candidate_production_component"))
    share = to_float(row.get("candidate_market_share_component"))
    if row.get("candidate_cfbd_feature_status") != "deterministic_joined":
        return "neutral CFBD context because current identity/features are unmatched"
    if production >= 80 and share >= 45:
        return "elite source-safe CFBD production plus strong share context"
    if production >= 70:
        return "strong source-safe CFBD production profile"
    if share >= 45:
        return "strong source-safe CFBD market-share/dominator context"
    return "fixed-formula draft/position/CFBD blend; no standout CFBD edge"


def manual_question(row: dict[str, str], decision_by_name: dict[str, dict[str, str]], warning: str) -> str:
    key = normalize_name(row.get("player_name", ""))
    if key in decision_by_name:
        base = decision_by_name[key].get("manual_question", "")
    else:
        base = row.get("manual_question", "")
    if warning == "none":
        return base or "Does Tim actively prefer this player over nearby alternatives at this tier?"
    return (
        f"{base} Confirm the player is not a draft-capital trap: does the role/film/CFBD evidence justify "
        "his current board slot despite draft-capital risk?"
    ).strip()


def trap_guard(row: dict[str, str]) -> tuple[str, str]:
    rank = safe_int(row.get("candidate_rank"))
    draft_round = safe_int(row.get("candidate_draft_round_used"), 0)
    overall_pick = safe_int(row.get("candidate_overall_pick_used"), 0)
    evidence = to_float(row.get("evidence_confidence_index"))
    bust = to_float(row.get("bust_risk_index"))
    production = to_float(row.get("candidate_production_component"))
    share = to_float(row.get("candidate_market_share_component"))
    warnings = "|".join([row.get("warning_flags", ""), row.get("cfbd_warning_flags", "")])
    reasons: list[str] = []

    if rank > TOP_N:
        return "none", ""
    if draft_round == 0:
        reasons.append("unknown_or_missing_draft_capital_inside_top54")
    elif draft_round >= 6:
        reasons.append(f"late_day3_draft_capital_round_{draft_round}")
    elif draft_round >= 4:
        reasons.append(f"day3_draft_capital_round_{draft_round}")
    elif draft_round == 3 and rank <= 24:
        reasons.append("round3_player_in_top24_manual_check")
    elif draft_round == 3 and (evidence < 60 or bust >= 75 or production < 60):
        reasons.append("round3_profile_with_fragility_flags")

    if not reasons:
        return "none", ""

    if evidence < 60:
        reasons.append("low_or_limited_evidence_confidence")
    if bust >= 75:
        reasons.append("high_bust_risk_index")
    if "SOURCE_LIMITED" in warnings:
        reasons.append("source_limited_warning_visible")
    if "CFBD_DENOMINATOR_MISSING" in warnings:
        reasons.append("cfbd_denominator_missing")
    if "CFBD_NO_2025_PROFILE_SELECTED" in warnings:
        reasons.append("no_current_cfbd_profile_selected")
    if row.get("candidate_cfbd_feature_status") != "deterministic_joined":
        reasons.append("unmatched_current_cfbd_features")
    if production < 60 and share < 35:
        reasons.append("no_standout_cfbd_production_or_share_edge")
    if overall_pick >= 150:
        reasons.append("very_late_overall_pick")

    severity = "watch"
    if (
        draft_round == 0
        or draft_round >= 6
        or row.get("candidate_cfbd_feature_status") != "deterministic_joined"
        or bust >= 90
        or (draft_round >= 4 and evidence < 50)
    ):
        severity = "hard_manual_review"
    elif draft_round >= 4 or (draft_round == 3 and rank <= 24) or evidence < 60 or bust >= 75:
        severity = "manual_review"
    return severity, "; ".join(dict.fromkeys(reasons))


def build_exports(board_path: Path, decision_sheet_path: Path, output_dir: Path) -> dict[str, object]:
    board_rows = sorted(read_csv(board_path), key=lambda row: safe_int(row.get("candidate_rank")))
    decision_rows = read_csv(decision_sheet_path)
    decision_by_name = {normalize_name(row.get("player", "")): row for row in decision_rows}
    top54 = [row for row in board_rows if safe_int(row.get("candidate_rank")) <= TOP_N]
    overlay_rows: list[dict[str, object]] = []
    flagged_rows: list[dict[str, object]] = []

    for row in top54:
        rank = safe_int(row.get("candidate_rank"))
        unmatched = row.get("candidate_cfbd_feature_status") != "deterministic_joined"
        warning, reason = trap_guard(row)
        out = {
            "rank": rank,
            "position_rank": row.get("candidate_position_rank", ""),
            "player": row.get("player_name", ""),
            "position": row.get("position", ""),
            "tier": tier_for_rank(rank, row.get("status", ""), unmatched),
            "draft_action": draft_action(row, decision_by_name),
            "trap_guard_warning": warning,
            "trap_guard_reason": reason,
            "main_positive_reason": feature_reason(row, decision_by_name),
            "main_risk_manual_question": manual_question(row, decision_by_name, warning),
            "candidate_model": row.get("candidate_model", ""),
            "main_ranking_formula_changed": "no",
            "production_allowed": "no",
            "promotion_status": "local_manual_overlay_only",
        }
        overlay_rows.append(out)
        if warning != "none":
            flagged_rows.append(out)

    verdicts = [
        {
            "verdict": "overlay_quality",
            "status": "GREEN",
            "reason": "trap guard is warning-only and uses existing draft capital, warning, and CFBD context fields",
        },
        {
            "verdict": "draft_use_readiness",
            "status": "YELLOW",
            "reason": "board is clearer for manual use but remains warning/manual-review only",
        },
        {
            "verdict": "manual_draft_trust",
            "status": "YELLOW",
            "reason": "use as advisory board with trap warnings visible; not a blind ranking",
        },
        {
            "verdict": "anti_cheat_leakage",
            "status": "GREEN",
            "reason": "no new tuning, no ADP/market private input, no probabilities/bands, no app or production wiring",
        },
        {
            "verdict": "main_ranking_formula_changed",
            "status": "NO",
            "reason": "rank order remains cfbd_enriched_baseline_v1_1",
        },
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "draft_capital_trap_guard_top54_overlay_20260615.csv", overlay_rows)
    write_csv(output_dir / "draft_capital_trap_guard_flagged_players_20260615.csv", flagged_rows)
    write_csv(
        output_dir / "draft_capital_trap_guard_final_draft_board_20260615.csv",
        overlay_rows,
        [
            "rank",
            "tier",
            "draft_action",
            "player",
            "position",
            "position_rank",
            "trap_guard_warning",
            "main_positive_reason",
            "main_risk_manual_question",
            "production_allowed",
            "promotion_status",
        ],
    )
    write_csv(output_dir / "draft_capital_trap_guard_verdicts_20260615.csv", verdicts)
    write_readme(output_dir)
    return {
        "top54": overlay_rows,
        "flagged": flagged_rows,
        "verdicts": verdicts,
        "output_dir": output_dir,
    }


def write_readme(output_dir: Path) -> None:
    text = [
        "# Draft Capital Trap Guard Overlay",
        "",
        "Local/manual-use warning overlay for the current 2026 feature-aware board.",
        "Rank order is unchanged and remains cfbd_enriched_baseline_v1_1.",
        "No production ranking, app output, probabilities, bands, hidden sort keys, or promoted artifacts.",
    ]
    (output_dir / "README_DRAFT_CAPITAL_TRAP_GUARD_OVERLAY_20260615.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--decision-sheet", type=Path, default=DEFAULT_DECISION_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.board, args.decision_sheet, args.output_dir)
    print(f"top54_rows={len(result['top54'])}")
    print(f"flagged_rows={len(result['flagged'])}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
