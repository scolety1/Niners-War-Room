"""Build Rookie Framework v0.3 shadow ordering exports.

This script is shadow/export-only. It consumes the Step 2 rookie review-board
exports and writes local-only shadow files. It does not change production
rankings, private scores, formulas, app outputs, probabilities, bands, outcome
columns, or veteran outcome heads.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT_ROOT = Path("local_exports/model_v4/rookie_framework_v02/review_board_v03")
DEFAULT_OUTPUT_DIR = Path("local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03")

REVIEW_BOARD = Path("rookie_review_board_v03.csv")
PREMIUM_REVIEW = Path("rookie_review_board_premium_review_v03.csv")
ROUND2_REVIEW = Path("rookie_review_board_round2_v03.csv")
WATCH_504 = Path("rookie_review_board_5_04_watchlist_v03.csv")
MANUAL_FLAGS = Path("rookie_review_board_manual_flags_v03.csv")
REMAINING_GAPS = Path("rookie_review_board_remaining_gaps_v03.csv")
REVIEW_README = Path("README_ROOKIE_REVIEW_BOARD_V03.md")

REQUIRED_INPUTS = [
    REVIEW_BOARD,
    PREMIUM_REVIEW,
    ROUND2_REVIEW,
    WATCH_504,
    MANUAL_FLAGS,
    REMAINING_GAPS,
    REVIEW_README,
]

SHADOW_COLUMNS = [
    "shadow_order",
    "player_id",
    "player_name",
    "position",
    "school",
    "current_pick_zone",
    "v03_candidate_pick_zone",
    "review_bucket",
    "shadow_review_group",
    "shadow_order_basis",
    "promotion_status",
    "production_allowed",
    "source_confidence",
    "review_status",
    "hard_caps",
    "soft_flags",
    "manual_review_flags",
    "manual_flag_count",
    "remaining_gap_count",
    "prohibited_sources_detected",
    "source_conflict_status",
    "best_source_safe_evidence_summary",
    "remaining_true_gaps",
    "notes",
]

BUCKET_ORDER = {
    "premium_review": 0,
    "round2_review": 1,
    "5_04_watchlist": 2,
    "manual_review": 3,
    "capped": 4,
    "unavailable": 5,
}
STATUS_ORDER = {
    "review_needed": 0,
    "needs_data": 1,
    "watchlist_review": 2,
    "hold_until_roster_declaration": 3,
    "capped_review": 4,
    "unavailable": 5,
}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}
POSITION_ORDER = {"RB": 0, "WR": 1, "TE": 2, "QB": 3}

PROHIBITED_PRIVATE_INPUT_COLUMNS = {
    "adp",
    "rank",
    "ranking",
    "rankings",
    "projection",
    "projections",
    "consensus",
    "market",
    "trade",
    "trade_value",
    "draft_kit",
    "league_rank",
    "private_score",
    "fantasy_forecast",
    "fantasy_forecasts",
    "probability",
    "band",
}

ALLOWED_WARNING_COLUMNS = {"prohibited_sources_detected"}


class ShadowExportError(RuntimeError):
    """Raised when shadow export validation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ShadowExportError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def require_inputs(input_root: Path) -> None:
    missing = [str(input_root / rel_path) for rel_path in REQUIRED_INPUTS if not (input_root / rel_path).exists()]
    if missing:
        raise ShadowExportError("Required Step 2 review-board inputs are missing:\n" + "\n".join(f"- {p}" for p in missing))


def normalized_field_tokens(field_name: str) -> set[str]:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in field_name.lower())
    tokens = {token for token in normalized.split("_") if token}
    tokens.add(normalized)
    return tokens


def find_prohibited_private_input_columns(fieldnames: Iterable[str]) -> list[str]:
    bad = []
    for field in fieldnames:
        if field in ALLOWED_WARNING_COLUMNS:
            continue
        if normalized_field_tokens(field) & PROHIBITED_PRIVATE_INPUT_COLUMNS:
            bad.append(field)
    return sorted(set(bad))


def count_pipe(value: str) -> int:
    return len([part for part in value.split("|") if part.strip()])


def manual_flag_counts(rows: list[dict[str, str]]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        player_id = row.get("player_id", "")
        if player_id:
            counts[player_id] += 1
    return counts


def remaining_gap_counts(rows: list[dict[str, str]]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        player_id = row.get("player_id", "")
        if player_id:
            counts[player_id] += 1
    return counts


def shadow_group(row: dict[str, str]) -> str:
    bucket = row.get("review_bucket", "")
    if row.get("review_status") == "capped_review":
        return "capped_shadow_review"
    if row.get("review_status") == "unavailable":
        return "unavailable_shadow_review"
    if bucket == "premium_review":
        return "premium_shadow_review"
    if bucket == "round2_review":
        return "round2_shadow_review"
    if bucket == "5_04_watchlist":
        return "5_04_shadow_watchlist"
    return "manual_shadow_review"


def order_key(row: dict[str, str], manual_counts: Counter, gap_counts: Counter) -> tuple:
    player_id = row.get("player_id", "")
    return (
        BUCKET_ORDER.get(row.get("review_bucket", ""), 99),
        STATUS_ORDER.get(row.get("review_status", ""), 99),
        CONFIDENCE_ORDER.get(row.get("source_confidence", ""), 99),
        1 if row.get("hard_caps", "").strip() else 0,
        min(gap_counts[player_id], 99),
        min(manual_counts[player_id], 99),
        POSITION_ORDER.get(row.get("position", ""), 99),
        row.get("player_name", "").lower(),
        player_id,
    )


def basis_for(row: dict[str, str], manual_count: int, gap_count: int) -> str:
    return (
        "deterministic shadow-only order from review_bucket, review_status, "
        f"source_confidence, hard_caps_present={bool(row.get('hard_caps', '').strip())}, "
        f"remaining_gap_count={gap_count}, manual_flag_count={manual_count}, position, player_name; "
        "no market/rank/projection/private-score/probability/band inputs"
    )


def normalize_shadow_rows(
    review_rows: list[dict[str, str]],
    manual_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    manual_counts = manual_flag_counts(manual_rows)
    gap_counts = remaining_gap_counts(gap_rows)
    ordered = sorted(review_rows, key=lambda row: order_key(row, manual_counts, gap_counts))
    output = []
    for index, row in enumerate(ordered, start=1):
        player_id = row.get("player_id", "")
        manual_count = manual_counts[player_id] or count_pipe(row.get("manual_review_flags", ""))
        gap_count = gap_counts[player_id] or count_pipe(row.get("remaining_true_gaps", ""))
        output.append(
            {
                "shadow_order": str(index),
                "player_id": player_id,
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "school": row.get("school", ""),
                "current_pick_zone": row.get("current_pick_zone", ""),
                "v03_candidate_pick_zone": row.get("v03_candidate_pick_zone", ""),
                "review_bucket": row.get("review_bucket", ""),
                "shadow_review_group": shadow_group(row),
                "shadow_order_basis": basis_for(row, manual_count, gap_count),
                "promotion_status": "shadow_only",
                "production_allowed": "no",
                "source_confidence": row.get("source_confidence", ""),
                "review_status": row.get("review_status", ""),
                "hard_caps": row.get("hard_caps", ""),
                "soft_flags": row.get("soft_flags", ""),
                "manual_review_flags": row.get("manual_review_flags", ""),
                "manual_flag_count": str(manual_count),
                "remaining_gap_count": str(gap_count),
                "prohibited_sources_detected": row.get("prohibited_sources_detected", "none"),
                "source_conflict_status": row.get("source_conflict_status", "none"),
                "best_source_safe_evidence_summary": row.get("best_source_safe_evidence_summary", ""),
                "remaining_true_gaps": row.get("remaining_true_gaps", ""),
                "notes": append_note(
                    row.get("notes", ""),
                    "Shadow-only export; production_allowed=no; no automatic promotion.",
                ),
            }
        )
    return output


def append_note(existing: str, addition: str) -> str:
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing} {addition}"


def validate_shadow_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ShadowExportError("No shadow rows were produced.")
    bad_promotion = [row.get("player_id", "") for row in rows if row.get("promotion_status") != "shadow_only"]
    bad_production = [row.get("player_id", "") for row in rows if row.get("production_allowed") != "no"]
    if bad_promotion:
        raise ShadowExportError("Rows missing promotion_status=shadow_only: " + ", ".join(bad_promotion[:10]))
    if bad_production:
        raise ShadowExportError("Rows missing production_allowed=no: " + ", ".join(bad_production[:10]))


def strict_validate_inputs(named_inputs: dict[str, list[dict[str, str]]]) -> None:
    problems = []
    for name, rows in named_inputs.items():
        if not rows:
            continue
        bad = find_prohibited_private_input_columns(rows[0].keys())
        if bad:
            problems.append(f"{name}: {', '.join(bad)}")
    if problems:
        raise ShadowExportError("Prohibited private input columns detected:\n" + "\n".join(problems))


def write_readme(output_dir: Path, rows: list[dict[str, str]]) -> None:
    counts = Counter(row["shadow_review_group"] for row in rows)
    text = f"""# Rookie Shadow Ranking v0.3

Status: shadow-only local export.

## Outputs

- `rookie_shadow_ranking_v03.csv`
- `rookie_shadow_ranking_premium_v03.csv`
- `rookie_shadow_ranking_round2_v03.csv`
- `rookie_shadow_ranking_5_04_watchlist_v03.csv`
- `README_ROOKIE_SHADOW_RANKING_V03.md`

## Counts

- Total shadow rows: {len(rows)}
- Premium shadow rows: {counts.get('premium_shadow_review', 0)}
- Round 2 shadow rows: {counts.get('round2_shadow_review', 0)}
- 5.04 watchlist shadow rows: {counts.get('5_04_shadow_watchlist', 0)}
- Capped shadow rows: {counts.get('capped_shadow_review', 0)}

## Guardrails

- Every row has `promotion_status=shadow_only`.
- Every row has `production_allowed=no`.
- This is not a production ranking file.
- No private scores, formulas, app outputs, probabilities, bands, outcome columns, or veteran outcome-head inputs were created.
- Ordering is deterministic from Step 2 review metadata only.
"""
    (output_dir / "README_ROOKIE_SHADOW_RANKING_V03.md").write_text(text, encoding="utf-8")


def build_exports(input_root: Path, output_dir: Path, strict: bool = False) -> dict[str, int]:
    require_inputs(input_root)
    named_inputs = {
        "review_board": read_csv(input_root / REVIEW_BOARD),
        "premium_review": read_csv(input_root / PREMIUM_REVIEW),
        "round2_review": read_csv(input_root / ROUND2_REVIEW),
        "watch_5_04": read_csv(input_root / WATCH_504),
        "manual_flags": read_csv(input_root / MANUAL_FLAGS),
        "remaining_gaps": read_csv(input_root / REMAINING_GAPS),
    }
    if strict:
        strict_validate_inputs(named_inputs)
    rows = normalize_shadow_rows(
        named_inputs["review_board"],
        named_inputs["manual_flags"],
        named_inputs["remaining_gaps"],
    )
    validate_shadow_rows(rows)

    premium = [row for row in rows if row["shadow_review_group"] == "premium_shadow_review"]
    round2 = [row for row in rows if row["shadow_review_group"] == "round2_shadow_review"]
    watch = [row for row in rows if row["shadow_review_group"] == "5_04_shadow_watchlist"]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_shadow_ranking_v03.csv", rows, SHADOW_COLUMNS)
    write_csv(output_dir / "rookie_shadow_ranking_premium_v03.csv", premium, SHADOW_COLUMNS)
    write_csv(output_dir / "rookie_shadow_ranking_round2_v03.csv", round2, SHADOW_COLUMNS)
    write_csv(output_dir / "rookie_shadow_ranking_5_04_watchlist_v03.csv", watch, SHADOW_COLUMNS)
    write_readme(output_dir, rows)

    return {
        "shadow_rows": len(rows),
        "premium_rows": len(premium),
        "round2_rows": len(round2),
        "watch_rows": len(watch),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Rookie Framework v0.3 shadow ranking exports.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    try:
        counts = build_exports(input_root=args.input_root, output_dir=output_dir, strict=args.strict)
    except ShadowExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
