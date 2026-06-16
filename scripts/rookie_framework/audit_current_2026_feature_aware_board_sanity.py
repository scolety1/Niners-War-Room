"""Audit the current 2026 feature-aware rookie board for manual draft use.

This script reads the local/manual-use feature-aware rescore candidate board,
creates rank sanity exports, and builds a clean draft sheet. It does not tune,
rescore, promote artifacts, or write app/production outputs.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


DEFAULT_BOARD = Path(
    "local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/"
    "current_2026_feature_aware_candidate_board_20260615.csv"
)
DEFAULT_MOVEMENT = Path(
    "local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/"
    "current_2026_feature_aware_rank_movement_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/current_2026_board_sanity_audit_20260615")
POSITIONS = ("RB", "WR", "TE", "QB")
FOCUS_PLAYERS = {
    "Carnell Tate",
    "Antonio Williams",
    "Jonah Coleman",
    "Barion Brown",
    "Kentrel Bullock",
    "Jordyn Tyson",
    "Hank Beatty",
    "Chase Roberts",
    "Donaven Mcculley",
    "Donaven McCulley",
    "Reggie Virgil",
    "Ja'Mori Maclin",
    "Ryan Niblett",
    "Chip Trayanum",
    "Mike Washington",
    "Jam Miller",
    "Jaydn Ott",
    "DJ Rogers",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def safe_int(value: object, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value)))
    except ValueError:
        return default


def to_float(value: object) -> float:
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(str(value))
    except ValueError:
        return 0.0


def top_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, object]]:
    return [summary_row(row) for row in sorted(rows, key=lambda row: safe_int(row.get("candidate_rank"), 9999))[:limit]]


def position_top_rows(rows: list[dict[str, str]], limit: int = 12) -> list[dict[str, object]]:
    output = []
    for position in POSITIONS:
        scoped = sorted(
            [row for row in rows if row.get("position") == position],
            key=lambda row: safe_int(row.get("candidate_rank"), 9999),
        )[:limit]
        for row in scoped:
            out = summary_row(row)
            out["position_list"] = position
            output.append(out)
    return output


def summary_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "candidate_rank": row.get("candidate_rank", ""),
        "candidate_position_rank": row.get("candidate_position_rank", ""),
        "old_rank": row.get("rookie_rank", ""),
        "rank_delta": row.get("rank_delta", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "school": row.get("school", ""),
        "status": row.get("status", ""),
        "candidate_feature_aware_score": row.get("candidate_feature_aware_score", ""),
        "production_component": row.get("candidate_production_component", ""),
        "market_share_component": row.get("candidate_market_share_component", ""),
        "cfbd_join_status": row.get("cfbd_current_join_status", ""),
        "cfbd_warning_flags": row.get("cfbd_warning_flags", ""),
        "manual_review_flag": manual_review_reason(row),
        "feature_reason": feature_reason(row),
    }


def feature_reason(row: dict[str, str]) -> str:
    if row.get("candidate_cfbd_feature_status") != "deterministic_joined":
        return "neutral CFBD context because current identity was unmatched"
    if row.get("cfbd_denominator_status") != "denominator_ready":
        return "matched production with denominator warning"
    production = to_float(row.get("candidate_production_component"))
    market = to_float(row.get("candidate_market_share_component"))
    if production >= 80 and market >= 45:
        return "elite source-safe CFBD production plus strong share context"
    if production >= 70:
        return "strong source-safe CFBD production profile"
    if market >= 45:
        return "strong source-safe CFBD market-share/dominator context"
    return "fixed-formula draft/position/CFBD blend; no standout CFBD edge"


def manual_review_reason(row: dict[str, str]) -> str:
    reasons = []
    warnings = "|".join(
        [
            row.get("warning_flags", ""),
            row.get("cfbd_warning_flags", ""),
        ]
    )
    if row.get("status") != "rankable_with_warning":
        reasons.append(f"status={row.get('status')}")
    if "manual=" in warnings:
        reasons.append("manual evidence flags remain")
    if "SOURCE_LIMITED" in warnings:
        reasons.append("source-limited profile")
    if "injury" in warnings.lower() or row.get("player_name") == "Jordyn Tyson":
        reasons.append("injury review before draft use")
    if "CFBD_UNMATCHED_CURRENT_IDENTITY" in warnings:
        reasons.append("unmatched current CFBD identity")
    if "CFBD_DENOMINATOR_MISSING" in warnings:
        reasons.append("CFBD denominator missing")
    if "CFBD_NO_2025_PROFILE_SELECTED" in warnings:
        reasons.append("no 2025 CFBD profile selected")
    return "; ".join(dict.fromkeys(reasons)) if reasons else "warnings visible; no extra audit flag"


def focus_player_rows(board_rows: list[dict[str, str]], movement_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_name = {row.get("player_name", ""): row for row in board_rows}
    by_norm_name = {normalize_name(row.get("player_name", "")): row for row in board_rows}
    movement_by_name = {row.get("player_name", ""): row for row in movement_rows}
    movement_by_norm_name = {normalize_name(row.get("player_name", "")): row for row in movement_rows}
    output = []
    for name in sorted(FOCUS_PLAYERS):
        row = by_name.get(name) or by_norm_name.get(normalize_name(name))
        move = movement_by_name.get(name, {}) or movement_by_norm_name.get(normalize_name(name), {})
        if not row:
            output.append({"player_name": name, "audit_status": "not_found_in_candidate_board"})
            continue
        out = summary_row(row)
        out["audit_status"] = "found"
        out["movement_explanation"] = move.get("movement_explanation", feature_reason(row))
        output.append(out)
    return output


def normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def unmatched_rows(board_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        summary_row(row)
        for row in sorted(board_rows, key=lambda item: safe_int(item.get("candidate_rank"), 9999))
        if not row.get("cfbd_current_join_status", "").startswith("matched")
    ]


def manual_review_top36(board_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    top36 = sorted(board_rows, key=lambda row: safe_int(row.get("candidate_rank"), 9999))[:36]
    output = []
    for row in top36:
        reason = manual_review_reason(row)
        if reason != "warnings visible; no extra audit flag":
            out = summary_row(row)
            out["manual_review_before_draft_use"] = "yes"
            out["manual_review_reason"] = reason
            output.append(out)
    return output


def clean_draft_sheet(board_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for row in sorted(board_rows, key=lambda item: safe_int(item.get("candidate_rank"), 9999)):
        if row.get("status") not in {"rankable_with_warning", "manual_review_required"}:
            continue
        output.append(
            {
                "overall_rank": row.get("candidate_rank", ""),
                "position_rank": row.get("candidate_position_rank", ""),
                "player": row.get("player_name", ""),
                "position": row.get("position", ""),
                "draft_action": draft_action(row),
                "feature_reason": feature_reason(row),
                "warning_manual_review_reason": manual_review_reason(row),
                "unmatched_neutral_flag": "yes"
                if row.get("candidate_cfbd_feature_status") != "deterministic_joined"
                else "no",
                "production_allowed": "no",
                "app_wiring_allowed": "no",
                "promotion_status": "local_manual_draft_sheet_only",
            }
        )
    return output


def draft_action(row: dict[str, str]) -> str:
    rank = safe_int(row.get("candidate_rank"), 9999)
    reason = manual_review_reason(row)
    if rank <= 12:
        action = "premium target"
    elif rank <= 24:
        action = "draft-window target"
    elif rank <= 36:
        action = "watch / value if sliding"
    else:
        action = "deep watch only"
    if reason != "warnings visible; no extra audit flag":
        action += " with manual review"
    return action


def balance_rows(board_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for limit in [12, 24, 36]:
        scoped = sorted(board_rows, key=lambda row: safe_int(row.get("candidate_rank"), 9999))[:limit]
        counts = Counter(row.get("position", "") for row in scoped)
        output.append(
            {
                "slice": f"top_{limit}",
                "RB": counts["RB"],
                "WR": counts["WR"],
                "TE": counts["TE"],
                "QB": counts["QB"],
                "sanity_note": balance_note(counts, limit),
            }
        )
    return output


def balance_note(counts: Counter[str], limit: int) -> str:
    if counts["QB"] > 0 and limit <= 36:
        return "YELLOW: 1QB league should usually avoid QB in premium rookie window unless exceptional"
    if counts["TE"] > 2 and limit <= 24:
        return "YELLOW: TE count high for non-PPR unless role is exceptional"
    if counts["RB"] == 0:
        return "YELLOW: no RB exposure despite first-down/non-PPR scoring"
    return "GREEN: RB/WR emphasis is plausible for 10-team 1QB non-PPR first-down scoring"


def verdict_rows(board_rows: list[dict[str, str]], manual_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    top36 = sorted(board_rows, key=lambda row: safe_int(row.get("candidate_rank"), 9999))[:36]
    unmatched_top36 = [row for row in top36 if row.get("candidate_cfbd_feature_status") != "deterministic_joined"]
    qb_top36 = [row for row in top36 if row.get("position") == "QB"]
    return [
        {"verdict": "board_sanity", "status": "YELLOW", "reason": "candidate is coherent for manual use but needs top-36 manual review"},
        {"verdict": "draft_use_readiness", "status": "YELLOW", "reason": "clean draft sheet created; not production-ready"},
        {"verdict": "manual_draft_trust", "status": "YELLOW", "reason": "use as advisory board with visible warnings, not blind ranking"},
        {"verdict": "anti_cheat_leakage", "status": "GREEN", "reason": "audit-only; no tuning, ADP/private market input, probabilities, bands, or app wiring"},
        {"verdict": "top36_manual_review_count", "status": str(len(manual_rows)), "reason": "players flagged before draft use"},
        {"verdict": "top36_unmatched_count", "status": str(len(unmatched_top36)), "reason": "unmatched rows in top 36"},
        {"verdict": "top36_qb_count", "status": str(len(qb_top36)), "reason": "1QB balance check"},
    ]


def write_readme(output_dir: Path) -> None:
    text = [
        "# Current 2026 Board Sanity Audit",
        "",
        "Local-only manual draft sanity exports. No tuning, production ranking, app output, probabilities, or bands.",
        "",
        "Use the clean draft sheet as review context only.",
    ]
    (output_dir / "README_CURRENT_2026_BOARD_SANITY_AUDIT_20260615.md").write_text("\n".join(text), encoding="utf-8")


def build_exports(board_path: Path, movement_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    board = read_csv(board_path)
    movement = read_csv(movement_path)
    top12 = top_rows(board, 12)
    top24 = top_rows(board, 24)
    top36 = top_rows(board, 36)
    position_tops = position_top_rows(board)
    focus = focus_player_rows(board, movement)
    unmatched = unmatched_rows(board)
    manual = manual_review_top36(board)
    draft_sheet = clean_draft_sheet(board)
    balance = balance_rows(board)
    verdicts = verdict_rows(board, manual)
    write_csv(output_dir / "current_2026_board_top12_20260615.csv", top12, list(top12[0].keys()) if top12 else [])
    write_csv(output_dir / "current_2026_board_top24_20260615.csv", top24, list(top24[0].keys()) if top24 else [])
    write_csv(output_dir / "current_2026_board_top36_20260615.csv", top36, list(top36[0].keys()) if top36 else [])
    write_csv(output_dir / "current_2026_position_top_lists_20260615.csv", position_tops, list(position_tops[0].keys()) if position_tops else [])
    write_csv(output_dir / "current_2026_focus_player_sanity_20260615.csv", focus, all_columns(focus))
    write_csv(output_dir / "current_2026_unmatched_neutral_rows_20260615.csv", unmatched, all_columns(unmatched))
    write_csv(output_dir / "current_2026_top36_manual_review_flags_20260615.csv", manual, all_columns(manual))
    write_csv(output_dir / "current_2026_clean_draft_use_sheet_20260615.csv", draft_sheet, list(draft_sheet[0].keys()) if draft_sheet else [])
    write_csv(output_dir / "current_2026_position_balance_sanity_20260615.csv", balance, list(balance[0].keys()) if balance else [])
    write_csv(output_dir / "current_2026_board_sanity_verdicts_20260615.csv", verdicts, list(verdicts[0].keys()) if verdicts else [])
    write_readme(output_dir)
    return {
        "board": board,
        "top12": top12,
        "top24": top24,
        "top36": top36,
        "focus": focus,
        "unmatched": unmatched,
        "manual": manual,
        "draft_sheet": draft_sheet,
        "balance": balance,
        "verdicts": verdicts,
    }


def all_columns(rows: list[dict[str, object]]) -> list[str]:
    columns = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--movement", type=Path, default=DEFAULT_MOVEMENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.board, args.movement, args.output_dir)
    print(f"board_rows={len(result['board'])}")
    print(f"top36_manual_review_rows={len(result['manual'])}")
    print(f"unmatched_rows={len(result['unmatched'])}")
    print(f"draft_sheet_rows={len(result['draft_sheet'])}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
