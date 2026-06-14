"""Build Rookie Framework v0.3 analyzer exports.

This script creates a rookie-only analyzer layer from local review-board,
shadow-ranking, and production-candidate exports. It is practical review
context only. It does not replace production rankings, change private scores,
create probabilities or bands, write app outputs, create outcome columns, or
use veteran outcome heads.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_REVIEW_ROOT = Path("local_exports/model_v4/rookie_framework_v02/review_board_v03")
DEFAULT_SHADOW_ROOT = Path("local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03")
DEFAULT_CANDIDATE_ROOT = Path("local_exports/model_v4/rookie_framework_v02/production_candidate_v03")
DEFAULT_OUTPUT_DIR = Path("local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03")

REVIEW_FULL = Path("rookie_review_board_v03.csv")
REVIEW_MANUAL = Path("rookie_review_board_manual_flags_v03.csv")
REVIEW_GAPS = Path("rookie_review_board_remaining_gaps_v03.csv")
REVIEW_README = Path("README_ROOKIE_REVIEW_BOARD_V03.md")

SHADOW_FULL = Path("rookie_shadow_ranking_v03.csv")
SHADOW_PREMIUM = Path("rookie_shadow_ranking_premium_v03.csv")
SHADOW_ROUND2 = Path("rookie_shadow_ranking_round2_v03.csv")
SHADOW_5_04 = Path("rookie_shadow_ranking_5_04_watchlist_v03.csv")
SHADOW_README = Path("README_ROOKIE_SHADOW_RANKING_V03.md")

CANDIDATE_FULL = Path("rookie_production_candidate_v03.csv")
CANDIDATE_PREMIUM = Path("rookie_production_candidate_premium_v03.csv")
CANDIDATE_ROUND2 = Path("rookie_production_candidate_round2_v03.csv")
CANDIDATE_5_04 = Path("rookie_production_candidate_5_04_v03.csv")
CANDIDATE_WARNINGS = Path("rookie_production_candidate_manual_warnings_v03.csv")
CANDIDATE_AUDIT = Path("rookie_production_candidate_source_safety_audit_v03.csv")
CANDIDATE_README = Path("README_ROOKIE_PRODUCTION_CANDIDATE_V03.md")

REQUIRED_REVIEW_INPUTS = [REVIEW_FULL, REVIEW_MANUAL, REVIEW_GAPS, REVIEW_README]
REQUIRED_SHADOW_INPUTS = [SHADOW_FULL, SHADOW_PREMIUM, SHADOW_ROUND2, SHADOW_5_04, SHADOW_README]
REQUIRED_CANDIDATE_INPUTS = [
    CANDIDATE_FULL,
    CANDIDATE_PREMIUM,
    CANDIDATE_ROUND2,
    CANDIDATE_5_04,
    CANDIDATE_WARNINGS,
    CANDIDATE_AUDIT,
    CANDIDATE_README,
]

ANALYZER_COLUMNS = [
    "analyzer_rank",
    "player_id",
    "player",
    "position",
    "school",
    "pick_zone",
    "production_ready_status",
    "tag_summary",
    "source_confidence",
    "warnings",
    "blockers",
    "evidence_summary",
    "remaining_gaps",
    "best_pick_fit",
    "draft_only_if",
    "do_not_draft_if",
    "why_ranked_here",
    "why_not_higher",
    "why_not_lower",
    "app_ready",
    "production_score_created",
    "probabilities_created",
    "analyzer_notes",
]

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

ALLOWED_WARNING_COLUMNS = {"candidate_rank", "prohibited_sources_detected"}

STATUS_ORDER = {
    "ready": 0,
    "rankable_with_warning": 1,
    "manual_review_required": 2,
    "unavailable": 3,
    "blocked": 4,
}
PICK_ZONE_ORDER = {"1.03": 0, "1.04": 1, "2.04": 2, "2.08": 3, "5.04": 4}
POSITION_ORDER = {"RB": 0, "WR": 1, "TE": 2, "QB": 3}


class RookieAnalyzerError(RuntimeError):
    """Raised when analyzer export validation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RookieAnalyzerError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def reject_data_path(path: Path) -> None:
    if any(part.lower() == "data" for part in path.parts):
        raise RookieAnalyzerError(f"Analyzer must not read from or write to data/: {path}")


def require_inputs(review_root: Path, shadow_root: Path, candidate_root: Path) -> None:
    for root in [review_root, shadow_root, candidate_root]:
        reject_data_path(root)
    missing = []
    missing.extend(str(review_root / rel_path) for rel_path in REQUIRED_REVIEW_INPUTS if not (review_root / rel_path).exists())
    missing.extend(str(shadow_root / rel_path) for rel_path in REQUIRED_SHADOW_INPUTS if not (shadow_root / rel_path).exists())
    missing.extend(
        str(candidate_root / rel_path) for rel_path in REQUIRED_CANDIDATE_INPUTS if not (candidate_root / rel_path).exists()
    )
    if missing:
        raise RookieAnalyzerError("Required analyzer inputs are missing:\n" + "\n".join(f"- {p}" for p in missing))


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


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip() and part.strip().lower() != "none"]


def clean_or_none(*values: str) -> str:
    parts: list[str] = []
    for value in values:
        parts.extend(split_pipe(value))
    return "|".join(parts) if parts else "none"


def by_player_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("player_id", ""): row for row in rows if row.get("player_id", "")}


def strict_validate_inputs(named_inputs: dict[str, list[dict[str, str]]]) -> None:
    problems = []
    for name, rows in named_inputs.items():
        if not rows:
            continue
        bad = find_prohibited_private_input_columns(rows[0].keys())
        if bad:
            problems.append(f"{name}: {', '.join(bad)}")
    if problems:
        raise RookieAnalyzerError("Prohibited private input columns detected:\n" + "\n".join(problems))


def best_pick_fit(candidate: dict[str, str], review: dict[str, str]) -> str:
    pick_zone = candidate.get("pick_zone", "")
    status = candidate.get("production_ready_status", "")
    tags = candidate.get("tag_summary", "")
    position = candidate.get("position", "")
    if pick_zone == "1.03":
        return "1.03_manual_trade_down_review"
    if status == "manual_review_required":
        return f"{pick_zone}_manual_review_hold"
    if status in {"blocked", "unavailable"}:
        return f"{pick_zone}_not_actionable"
    if pick_zone == "1.04":
        return "1.04_premium_warning_visible"
    if pick_zone in {"2.04", "2.08"}:
        if position == "RB":
            return "round2_rb_survival_profile"
        if position == "WR":
            return "round2_wr_evidence_profile"
        return "round2_exception_review"
    if pick_zone == "5.04":
        if "SOURCE_LIMITED_REVIEW" in tags:
            return "5.04_source_limited_stash_review"
        if review.get("review_status") == "hold_until_roster_declaration":
            return "5.04_roster_declaration_hold"
        return "5.04_asymmetric_dart"
    return "manual_context_only"


def draft_only_if(candidate: dict[str, str], review: dict[str, str]) -> str:
    status = candidate.get("production_ready_status", "")
    position = candidate.get("position", "")
    pick_zone = candidate.get("pick_zone", "")
    if status == "ready":
        return "source-safe evidence remains intact and no late manual blocker appears"
    if status == "rankable_with_warning":
        if pick_zone == "1.04":
            return "premium warning review is acceptable and visible warnings stay attached to the row"
        if position == "RB":
            return "RB survival questions are acceptable after pass-pro/contact/fumble/role review"
        if position == "WR":
            return "WR route/separation/press/YAC and target-earning questions are acceptable"
        return "exception case has a clear role path and visible warnings remain acceptable"
    if status == "manual_review_required":
        return "Tim clears the named manual-review question before the pick"
    if status == "unavailable":
        return "missing source-safe evidence arrives before draft decision"
    return "blocker is removed in a later approved review pass"


def do_not_draft_if(candidate: dict[str, str], review: dict[str, str]) -> str:
    status = candidate.get("production_ready_status", "")
    gaps = review.get("remaining_true_gaps", "")
    if status == "blocked":
        return "hard cap, source conflict, or capped review status remains active"
    if status == "unavailable":
        return "profile still depends on missing or low-confidence evidence"
    if "injury" in (candidate.get("manual_warnings", "") + "|" + gaps).lower():
        return "injury review remains unresolved"
    if candidate.get("pick_zone") == "1.04":
        return "premium case depends on hidden warnings, market/rank/projection context, or unresolved role proof"
    if "SOURCE_LIMITED" in review.get("soft_flags", ""):
        return "source-limited profile lacks a clear role path"
    return "warnings cannot be explained clearly at the pick"


def analyzer_order_key(row: dict[str, str]) -> tuple:
    return (
        PICK_ZONE_ORDER.get(row.get("pick_zone", ""), 99),
        STATUS_ORDER.get(row.get("production_ready_status", ""), 99),
        POSITION_ORDER.get(row.get("position", ""), 99),
        int(row.get("candidate_rank", "9999") or "9999"),
        row.get("player_name", "").lower(),
    )


def normalize_analyzer_rows(
    candidate_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
    shadow_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    review_by_id = by_player_id(review_rows)
    shadow_by_id = by_player_id(shadow_rows)
    missing_review = [row.get("player_id", "") for row in candidate_rows if row.get("player_id", "") not in review_by_id]
    missing_shadow = [row.get("player_id", "") for row in candidate_rows if row.get("player_id", "") not in shadow_by_id]
    if missing_review:
        raise RookieAnalyzerError("Candidate rows missing review-board context: " + ", ".join(missing_review[:10]))
    if missing_shadow:
        raise RookieAnalyzerError("Candidate rows missing shadow context: " + ", ".join(missing_shadow[:10]))

    ordered = sorted(candidate_rows, key=analyzer_order_key)
    output: list[dict[str, str]] = []
    for index, candidate in enumerate(ordered, start=1):
        player_id = candidate.get("player_id", "")
        review = review_by_id[player_id]
        shadow = shadow_by_id[player_id]
        warnings = clean_or_none(
            candidate.get("manual_warnings", ""),
            review.get("manual_review_flags", ""),
            review.get("soft_flags", ""),
        )
        blockers = clean_or_none(candidate.get("promotion_blockers", ""), review.get("hard_caps", ""), review.get("source_conflict_status", ""))
        remaining_gaps = clean_or_none(review.get("remaining_true_gaps", ""))
        output.append(
            {
                "analyzer_rank": str(index),
                "player_id": player_id,
                "player": candidate.get("player_name", ""),
                "position": candidate.get("position", ""),
                "school": candidate.get("school", ""),
                "pick_zone": candidate.get("pick_zone", ""),
                "production_ready_status": candidate.get("production_ready_status", ""),
                "tag_summary": candidate.get("tag_summary", ""),
                "source_confidence": candidate.get("source_confidence", ""),
                "warnings": warnings,
                "blockers": blockers,
                "evidence_summary": candidate.get("evidence_basis_summary", ""),
                "remaining_gaps": remaining_gaps,
                "best_pick_fit": best_pick_fit(candidate, review),
                "draft_only_if": draft_only_if(candidate, review),
                "do_not_draft_if": do_not_draft_if(candidate, review),
                "why_ranked_here": candidate.get("why_ranked_here", ""),
                "why_not_higher": candidate.get("why_not_higher", ""),
                "why_not_lower": candidate.get("why_not_lower", ""),
                "app_ready": "no",
                "production_score_created": "no",
                "probabilities_created": "no",
                "analyzer_notes": (
                    f"Analyzer-only from candidate_rank={candidate.get('candidate_rank')}, "
                    f"shadow_order={shadow.get('shadow_order')}; no production score, app output, probability, band, "
                    "private_score, market, rank, projection, or veteran outcome head."
                ),
            }
        )
    return output


def validate_analyzer_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RookieAnalyzerError("No analyzer rows were produced.")
    if any(row.get("pick_zone") == "1.03" for row in rows):
        raise RookieAnalyzerError("1.03 was unexpectedly populated; it must remain not forced open.")
    bad_app = [row["player_id"] for row in rows if row.get("app_ready") != "no"]
    bad_score = [row["player_id"] for row in rows if row.get("production_score_created") != "no"]
    bad_prob = [row["player_id"] for row in rows if row.get("probabilities_created") != "no"]
    if bad_app:
        raise RookieAnalyzerError("Rows missing app_ready=no: " + ", ".join(bad_app[:10]))
    if bad_score:
        raise RookieAnalyzerError("Rows missing production_score_created=no: " + ", ".join(bad_score[:10]))
    if bad_prob:
        raise RookieAnalyzerError("Rows missing probabilities_created=no: " + ", ".join(bad_prob[:10]))
    missing_warning = [
        row["player_id"]
        for row in rows
        if row.get("production_ready_status") == "rankable_with_warning" and row.get("warnings", "none") == "none"
    ]
    if missing_warning:
        raise RookieAnalyzerError("rankable_with_warning rows missing visible warnings: " + ", ".join(missing_warning[:10]))


def write_readme(output_dir: Path, rows: list[dict[str, str]]) -> None:
    status_counts = Counter(row["production_ready_status"] for row in rows)
    zone_counts = Counter(row["pick_zone"] for row in rows)
    text = f"""# Rookie Analyzer v0.3

Status: analyzer-only local export.

This analyzer is practical manual-context output. It does not replace production
rankings, does not create private scores, does not create app-readable output,
does not create probabilities or bands, and does not use veteran outcome heads.

## Outputs

- `rookie_analyzer_v03.csv`
- `rookie_analyzer_premium_v03.csv`
- `rookie_analyzer_round2_v03.csv`
- `rookie_analyzer_5_04_v03.csv`
- `rookie_analyzer_manual_review_v03.csv`
- `rookie_analyzer_blocked_v03.csv`
- `rookie_analyzer_readme.md`

## Counts

- Total analyzer rows: {len(rows)}
- Ready rows: {status_counts.get('ready', 0)}
- Rankable-with-warning rows: {status_counts.get('rankable_with_warning', 0)}
- Manual-review-required rows: {status_counts.get('manual_review_required', 0)}
- Blocked rows: {status_counts.get('blocked', 0)}
- Unavailable rows: {status_counts.get('unavailable', 0)}
- 1.03 rows: {zone_counts.get('1.03', 0)}
- 1.04 rows: {zone_counts.get('1.04', 0)}
- Round 2 rows: {zone_counts.get('2.04', 0) + zone_counts.get('2.08', 0)}
- 5.04 rows: {zone_counts.get('5.04', 0)}

## Guardrails

- Every row has `app_ready=no`.
- Every row has `production_score_created=no`.
- Every row has `probabilities_created=no`.
- `1.03` remains not forced open when unsupported.
- `rankable_with_warning` rows keep visible warnings.
- Generated local exports must not be committed.
"""
    (output_dir / "rookie_analyzer_readme.md").write_text(text, encoding="utf-8")


def build_exports(
    review_root: Path,
    shadow_root: Path,
    candidate_root: Path,
    output_dir: Path,
    strict: bool = False,
) -> dict[str, int]:
    reject_data_path(output_dir)
    require_inputs(review_root, shadow_root, candidate_root)
    named_inputs = {
        "review_full": read_csv(review_root / REVIEW_FULL),
        "review_manual": read_csv(review_root / REVIEW_MANUAL),
        "review_gaps": read_csv(review_root / REVIEW_GAPS),
        "shadow_full": read_csv(shadow_root / SHADOW_FULL),
        "shadow_premium": read_csv(shadow_root / SHADOW_PREMIUM),
        "shadow_round2": read_csv(shadow_root / SHADOW_ROUND2),
        "shadow_5_04": read_csv(shadow_root / SHADOW_5_04),
        "candidate_full": read_csv(candidate_root / CANDIDATE_FULL),
        "candidate_premium": read_csv(candidate_root / CANDIDATE_PREMIUM),
        "candidate_round2": read_csv(candidate_root / CANDIDATE_ROUND2),
        "candidate_5_04": read_csv(candidate_root / CANDIDATE_5_04),
        "candidate_warnings": read_csv(candidate_root / CANDIDATE_WARNINGS),
        "candidate_audit": read_csv(candidate_root / CANDIDATE_AUDIT),
    }
    if strict:
        strict_validate_inputs(named_inputs)
    rows = normalize_analyzer_rows(
        named_inputs["candidate_full"],
        named_inputs["review_full"],
        named_inputs["shadow_full"],
    )
    validate_analyzer_rows(rows)

    premium_ids = {row["player_id"] for row in named_inputs["candidate_premium"]}
    round2_ids = {row["player_id"] for row in named_inputs["candidate_round2"]}
    watch_ids = {row["player_id"] for row in named_inputs["candidate_5_04"]}

    premium = [row for row in rows if row["player_id"] in premium_ids]
    round2 = [row for row in rows if row["player_id"] in round2_ids or row["pick_zone"] in {"2.04", "2.08"}]
    watch = [row for row in rows if row["player_id"] in watch_ids]
    manual_review = [row for row in rows if row["production_ready_status"] == "manual_review_required"]
    blocked = [row for row in rows if row["production_ready_status"] in {"blocked", "unavailable"}]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_analyzer_v03.csv", rows, ANALYZER_COLUMNS)
    write_csv(output_dir / "rookie_analyzer_premium_v03.csv", premium, ANALYZER_COLUMNS)
    write_csv(output_dir / "rookie_analyzer_round2_v03.csv", round2, ANALYZER_COLUMNS)
    write_csv(output_dir / "rookie_analyzer_5_04_v03.csv", watch, ANALYZER_COLUMNS)
    write_csv(output_dir / "rookie_analyzer_manual_review_v03.csv", manual_review, ANALYZER_COLUMNS)
    write_csv(output_dir / "rookie_analyzer_blocked_v03.csv", blocked, ANALYZER_COLUMNS)
    write_readme(output_dir, rows)

    status_counts = Counter(row["production_ready_status"] for row in rows)
    return {
        "analyzer_rows": len(rows),
        "premium_rows": len(premium),
        "round2_rows": len(round2),
        "watch_rows": len(watch),
        "manual_review_rows": len(manual_review),
        "blocked_or_unavailable_rows": len(blocked),
        "ready_rows": status_counts.get("ready", 0),
        "rankable_with_warning_rows": status_counts.get("rankable_with_warning", 0),
        "manual_review_required_rows": status_counts.get("manual_review_required", 0),
        "blocked_rows": status_counts.get("blocked", 0),
        "unavailable_rows": status_counts.get("unavailable", 0),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Rookie Framework v0.3 analyzer exports.")
    parser.add_argument("--review-root", type=Path, default=DEFAULT_REVIEW_ROOT)
    parser.add_argument("--shadow-root", type=Path, default=DEFAULT_SHADOW_ROOT)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    try:
        counts = build_exports(
            review_root=args.review_root,
            shadow_root=args.shadow_root,
            candidate_root=args.candidate_root,
            output_dir=output_dir,
            strict=args.strict,
        )
    except RookieAnalyzerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
