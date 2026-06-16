"""Build a current 2026 top-36 draft decision review packet.

This is a local/manual-use export builder. It reads the feature-aware sanity
audit outputs and converts visible warnings into draft actions and manual
questions. It does not tune, rescore, promote, or write app/production files.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


DEFAULT_SANITY_DIR = Path("local_exports/rookie_framework/current_2026_board_sanity_audit_20260615")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/current_2026_top36_draft_decision_review_20260615")

FOCUS_NAMES = {
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
    "Jam Miller",
    "Jaydn Ott",
}

UNMATCHED_RELEVANT = {
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


def normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def tier_for_rank(rank: int, model_clearance: str, in_top36: bool) -> tuple[str, str]:
    if model_clearance == "not_model_cleared":
        return "Tier 5", "avoid/hold unless price drops"
    if rank <= 9:
        return "Tier 1", "priority targets"
    if rank <= 24:
        return "Tier 2", "strong considers"
    if rank <= 36:
        return "Tier 3", "value/fit targets"
    if in_top36:
        return "Tier 3", "value/fit targets"
    return "Tier 4", "manual-review upside"


def draft_action(rank: int, warning_reason: str, unmatched: bool, status: str) -> str:
    if unmatched or status in {"blocked", "unavailable"}:
        return "avoid"
    if status == "manual_review_required":
        return "manual hold"
    if rank <= 12:
        return "target"
    if rank <= 24:
        return "consider"
    return "wait"


def model_clearance(warning_reason: str, unmatched: bool, status: str) -> str:
    if unmatched or status in {"blocked", "unavailable"}:
        return "not_model_cleared"
    if status == "manual_review_required" or warning_reason != "warnings visible; no extra audit flag":
        return "draftable_only_with_review"
    return "safe_to_draft_from_model"


def manual_question(row: dict[str, str], clearance: str) -> str:
    player = row.get("player_name") or row.get("player") or "player"
    reason = row.get("manual_review_flag") or row.get("warning_manual_review_reason", "")
    if clearance == "not_model_cleared":
        return f"Is {player}'s missing/unmatched evidence repaired enough to move from avoid/hold to a draftable bucket?"
    if "injury" in reason.lower():
        return f"Is {player}'s injury/source review clean enough to trust at this draft cost?"
    if "source-limited" in reason:
        return f"Is {player}'s source-limited profile supported by enough film/role evidence to draft here?"
    if "manual evidence" in reason:
        return f"Did manual review confirm {player}'s role/archetype and warning flags?"
    return f"Does Tim actively prefer {player} over nearby alternatives at this tier?"


def review_row(row: dict[str, str], in_top36: bool) -> dict[str, object]:
    rank = safe_int(row.get("candidate_rank") or row.get("overall_rank"))
    pos_rank = row.get("candidate_position_rank") or row.get("position_rank", "")
    name = row.get("player_name") or row.get("player", "")
    position = row.get("position", "")
    status = row.get("status", "rankable_with_warning")
    warning = row.get("manual_review_flag") or row.get("warning_manual_review_reason", "")
    unmatched = (
        row.get("unmatched_neutral_flag") == "yes"
        or row.get("cfbd_join_status") == "unmatched_current_identity"
        or "unmatched current CFBD identity" in warning
    )
    clearance = model_clearance(warning, unmatched, status)
    tier_code, tier_name = tier_for_rank(rank, clearance, in_top36)
    action = draft_action(rank, warning, unmatched, status)
    return {
        "model_rank": rank if rank != 9999 else "",
        "position_rank": pos_rank,
        "player": name,
        "position": position,
        "draft_action": action,
        "tier": tier_code,
        "tier_name": tier_name,
        "main_positive_feature_reason": row.get("feature_reason", ""),
        "main_risk_warning": warning,
        "manual_question": manual_question(row, clearance),
        "model_clearance": clearance,
        "production_allowed": "no",
        "promotion_status": "local_manual_review_only",
        "source": "top36" if in_top36 else "focus_or_unmatched",
    }


def build_exports(sanity_dir: Path, output_dir: Path) -> dict[str, list[dict[str, object]]]:
    top36 = read_csv(sanity_dir / "current_2026_board_top36_20260615.csv")
    focus = read_csv(sanity_dir / "current_2026_focus_player_sanity_20260615.csv")
    unmatched = read_csv(sanity_dir / "current_2026_unmatched_neutral_rows_20260615.csv")

    top36_rows = [review_row(row, True) for row in top36]
    seen_names = {normalize_name(str(row.get("player", ""))) for row in top36_rows}

    by_name: dict[str, dict[str, str]] = {}
    for row in focus + unmatched:
        name = row.get("player_name", "")
        if name:
            by_name[normalize_name(name)] = row

    focus_rows = []
    focus_seen: set[str] = set()
    for name in sorted(FOCUS_NAMES | UNMATCHED_RELEVANT):
        key = normalize_name(name)
        if key in seen_names or key in focus_seen:
            continue
        row = by_name.get(key)
        if row:
            focus_rows.append(review_row(row, False))
            focus_seen.add(key)

    all_review = sorted(top36_rows + focus_rows, key=lambda row: safe_int(row.get("model_rank")))
    tier_rows = build_tier_rows(all_review)
    question_rows = [
        {
            "model_rank": row["model_rank"],
            "player": row["player"],
            "position": row["position"],
            "draft_action": row["draft_action"],
            "manual_question": row["manual_question"],
            "model_clearance": row["model_clearance"],
            "main_risk_warning": row["main_risk_warning"],
        }
        for row in all_review
        if row["model_clearance"] != "safe_to_draft_from_model" or safe_int(row["model_rank"]) <= 36
    ]
    focus_export = [row for row in all_review if normalize_name(str(row["player"])) in {normalize_name(n) for n in FOCUS_NAMES}]
    unmatched_export = [row for row in all_review if normalize_name(str(row["player"])) in {normalize_name(n) for n in UNMATCHED_RELEVANT}]
    draft_sheet = [
        {
            "overall_rank": row["model_rank"],
            "position_rank": row["position_rank"],
            "player": row["player"],
            "position": row["position"],
            "draft_action": row["draft_action"],
            "feature_reason": row["main_positive_feature_reason"],
            "warning_manual_review_reason": row["main_risk_warning"],
            "manual_question": row["manual_question"],
            "model_clearance": row["model_clearance"],
            "production_allowed": "no",
            "promotion_status": "local_manual_review_only",
        }
        for row in top36_rows
    ]
    verdicts = [
        {
            "verdict": "draft_use_clarity",
            "status": "GREEN",
            "reason": "top-36 ranks converted into draft actions and manual questions",
        },
        {
            "verdict": "manual_review_burden",
            "status": "YELLOW",
            "reason": "most top-36 rows still require warning/source/injury review",
        },
        {
            "verdict": "ranking_trust",
            "status": "YELLOW",
            "reason": "usable as a manual draft board, not as a blind or production ranking",
        },
        {
            "verdict": "anti_cheat_leakage",
            "status": "GREEN",
            "reason": "no tuning, ADP/private market input, probabilities, bands, app wiring, or promoted artifacts",
        },
        {
            "verdict": "draft_day_usable",
            "status": "YES_WITH_MANUAL_REVIEW",
            "reason": "use only with warnings and manual questions visible",
        },
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "top36_draft_decision_review_20260615.csv", top36_rows)
    write_csv(output_dir / "top36_tiers_20260615.csv", tier_rows)
    write_csv(output_dir / "top_manual_review_questions_20260615.csv", question_rows)
    write_csv(output_dir / "focus_player_decision_review_20260615.csv", focus_export)
    write_csv(output_dir / "unmatched_relevant_names_review_20260615.csv", unmatched_export)
    write_csv(output_dir / "draft_day_decision_sheet_20260615.csv", draft_sheet)
    write_csv(output_dir / "decision_review_verdicts_20260615.csv", verdicts)
    write_readme(output_dir)
    return {
        "top36": top36_rows,
        "tiers": tier_rows,
        "questions": question_rows,
        "focus": focus_export,
        "unmatched": unmatched_export,
        "draft_sheet": draft_sheet,
        "verdicts": verdicts,
    }


def build_tier_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["tier"]), str(row["tier_name"]))].append(str(row["player"]))
    tier_order = {
        "Tier 1": 1,
        "Tier 2": 2,
        "Tier 3": 3,
        "Tier 4": 4,
        "Tier 5": 5,
    }
    output = []
    for (tier, tier_name), names in sorted(grouped.items(), key=lambda item: tier_order.get(item[0][0], 99)):
        output.append(
            {
                "tier": tier,
                "tier_name": tier_name,
                "players": "; ".join(names),
                "player_count": len(names),
                "production_allowed": "no",
            }
        )
    return output


def write_readme(output_dir: Path) -> None:
    text = [
        "# Current 2026 Top-36 Draft Decision Review",
        "",
        "Local-only manual draft decision exports built from the feature-aware sanity audit.",
        "No tuning, production ranking, app output, probabilities, bands, hidden sort keys, or promoted artifacts.",
    ]
    (output_dir / "README_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanity-dir", type=Path, default=DEFAULT_SANITY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.sanity_dir, args.output_dir)
    print(f"top36_rows={len(result['top36'])}")
    print(f"tier_rows={len(result['tiers'])}")
    print(f"question_rows={len(result['questions'])}")
    print(f"focus_rows={len(result['focus'])}")
    print(f"unmatched_rows={len(result['unmatched'])}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
