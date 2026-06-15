"""Build Rookie Framework v0.3 review-board exports.

This script is intentionally review-only. It reads local v0.3 candidate
artifacts and writes human-review CSVs under local_exports. It does not compute
rankings, probabilities, bands, private scores, or app-readable outputs.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT_ROOT = Path("local_exports/model_v4/rookie_framework_v02")
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_ROOT / "review_board_v03"

PLAYER_BOARD = Path("v03_candidate_01/v03_candidate_player_review_board.csv")
PREMIUM_BOARD = Path("v03_candidate_01/v03_candidate_premium_pick_board.csv")
ROUND2_BOARD = Path("v03_candidate_01/v03_candidate_round2_board.csv")
WATCH_504_BOARD = Path("v03_candidate_01/v03_candidate_5_04_board.csv")
MANUAL_FLAGS = Path("deep_research_intake_pass_04/deep_research_manual_review_flags.csv")
REMAINING_GAPS = Path("deep_research_intake_pass_04/deep_research_remaining_gaps_after_pass04.csv")
SOURCE_SAFETY = Path("deep_research_intake_pass_04/deep_research_source_safety_audit.csv")
CONFLICT_REVIEW = Path("deep_research_intake_pass_04/deep_research_conflict_review.csv")
ADVERSARIAL_FINDINGS = Path("v03_adversarial_audit_01/v03_adversarial_findings.csv")
PATCH_QUEUE = Path("v03_adversarial_audit_01/v03_patch_queue.csv")
OVERNIGHT_SUMMARY = Path("OVERNIGHT_QUEUE_FINAL_SUMMARY_20260612.md")
REPAIR_TAGS = Path(
    "deep_research_intake_pass_04/applied_framework_after_deep_research_pass04/"
    "rookie_framework_v02_tags_after_deep_research_pass04.csv"
)
REPAIR_SOURCE_HITS = Path("local_source_search_01/local_source_hit_inventory.csv")

REQUIRED_INPUTS = [
    PLAYER_BOARD,
    PREMIUM_BOARD,
    ROUND2_BOARD,
    WATCH_504_BOARD,
    MANUAL_FLAGS,
    REMAINING_GAPS,
    SOURCE_SAFETY,
    CONFLICT_REVIEW,
    ADVERSARIAL_FINDINGS,
    PATCH_QUEUE,
    OVERNIGHT_SUMMARY,
]

REVIEW_COLUMNS = [
    "player_id",
    "player_name",
    "position",
    "school",
    "current_pick_zone",
    "v03_candidate_pick_zone",
    "review_bucket",
    "position_group",
    "tag_summary",
    "hard_caps",
    "soft_flags",
    "manual_review_flags",
    "urgent_manual_questions",
    "source_confidence",
    "best_source_safe_evidence_summary",
    "remaining_true_gaps",
    "prohibited_sources_detected",
    "source_conflict_status",
    "review_status",
    "notes",
]

MANUAL_FLAG_COLUMNS = [
    "player_id",
    "player_name",
    "position",
    "school",
    "review_bucket",
    "framework_field",
    "flag_type",
    "review_priority",
    "urgent_manual_question",
    "source_name",
    "source_url",
    "prohibited_sources_detected",
    "source_conflict_status",
    "reason",
]

GAP_COLUMNS = [
    "player_id",
    "player_name",
    "position",
    "school",
    "review_bucket",
    "missing_field",
    "marked_value",
    "recommended_next_source",
    "severity",
    "source_conflict_status",
    "reason_missing",
]

REVIEW_STATUS_VALUES = {
    "review_needed",
    "needs_data",
    "capped_review",
    "watchlist_review",
    "hold_until_roster_declaration",
    "unavailable",
}

PROHIBITED_INPUT_FIELD_TOKENS = {
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
}

PROHIBITED_OUTPUT_NAME_TOKENS = {"rank", "ranking", "score", "probability", "band"}
POSITION_ORDER = {"RB": 0, "WR": 1, "TE": 2, "QB": 3}
BUCKET_ORDER = {
    "premium_review": 0,
    "round2_review": 1,
    "5_04_watchlist": 2,
    "manual_review": 3,
    "capped": 4,
    "unavailable": 5,
}
CONFIDENCE_ORDER = {"": 0, "low": 1, "medium": 2, "high": 3}
REPAIR_PRIORITY_PLAYER_IDS = {
    "prospect:2026:carnelltate:WR",
    "prospect:2026:nicholassingleton:RB",
    "prospect:2026:barionbrown:WR",
    "prospect:2026:antoniowilliams:WR",
    "prospect:2026:jadarianprice:RB",
    "prospect:2026:kenyonsadiq:TE",
    "prospect:2026:maxklare:TE",
    "prospect:2026:jackvelling:TE",
    "prospect:2026:elistowers:TE",
    "prospect:2026:omarcooper:WR",
}
FIELD_REPAIR_ALIASES = {
    "target_command_projection": "target_command_context",
    "projected_team_target_rank": "manual_target_path_context",
}


class ReviewBoardError(RuntimeError):
    """Raised when strict validation or required input checks fail."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ReviewBoardError(f"Missing required input: {path}")
    if path.stat().st_size <= 2:
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size <= 2:
        return []
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
    missing = [str(input_root / relative) for relative in REQUIRED_INPUTS if not (input_root / relative).exists()]
    if missing:
        joined = "\n".join(f"- {path}" for path in missing)
        raise ReviewBoardError(f"Required local export inputs are missing:\n{joined}")


def normalized_field_tokens(field_name: str) -> set[str]:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in field_name.lower())
    pieces = {piece for piece in normalized.split("_") if piece}
    pieces.add(normalized)
    return pieces


def find_prohibited_input_columns(fieldnames: Iterable[str]) -> list[str]:
    bad = []
    for field in fieldnames:
        tokens = normalized_field_tokens(field)
        if tokens & PROHIBITED_INPUT_FIELD_TOKENS:
            bad.append(field)
    return sorted(set(bad))


def validate_output_columns(columns: Iterable[str]) -> None:
    bad = []
    for column in columns:
        tokens = normalized_field_tokens(column)
        if tokens & PROHIBITED_OUTPUT_NAME_TOKENS:
            bad.append(column)
    if bad:
        raise ReviewBoardError(f"Prohibited output column names: {', '.join(sorted(bad))}")


def strict_validate_input_columns(named_rows: dict[str, list[dict[str, str]]]) -> None:
    problems = []
    for name, rows in named_rows.items():
        if not rows:
            continue
        bad = find_prohibited_input_columns(rows[0].keys())
        if bad:
            problems.append(f"{name}: {', '.join(bad)}")
    if problems:
        raise ReviewBoardError("Prohibited input columns detected:\n" + "\n".join(problems))


def build_source_warnings(source_rows: list[dict[str, str]]) -> tuple[dict[str, str], list[str]]:
    by_player: dict[str, set[str]] = defaultdict(set)
    blockers = []
    for row in source_rows:
        player_id = row.get("player_id", "")
        terms = row.get("detected_forbidden_context_terms", "").replace(";", "|")
        blocker = row.get("market_contamination_blocker", "").strip().lower()
        if terms and player_id:
            for term in terms.split("|"):
                cleaned = term.strip()
                if cleaned:
                    by_player[player_id].add(cleaned)
        if blocker in {"yes", "true", "1"}:
            blockers.append(
                f"{player_id or row.get('player_name', 'unknown')}: {row.get('framework_field', 'unknown_field')}"
            )
    warnings = {
        player_id: "|".join(sorted(values)) if values else "none"
        for player_id, values in by_player.items()
    }
    return warnings, blockers


def build_conflicts(conflict_rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> dict[str, str]:
    conflicts: dict[str, set[str]] = defaultdict(set)
    for row in conflict_rows:
        player_id = row.get("player_id", "")
        field = row.get("framework_field") or row.get("field") or "source_conflict"
        if player_id:
            conflicts[player_id].add(field)
    for row in source_rows:
        if row.get("allowed_status", "").strip() == "conflict_review":
            player_id = row.get("player_id", "")
            field = row.get("framework_field", "source_conflict")
            if player_id:
                conflicts[player_id].add(field)
    return {
        player_id: "conflict_review:" + "|".join(sorted(fields))
        for player_id, fields in conflicts.items()
    }


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def merge_pipe(*values: str) -> str:
    parts: list[str] = []
    seen = set()
    for value in values:
        for part in split_pipe(value):
            if part.lower() == "none":
                continue
            if part not in seen:
                parts.append(part)
                seen.add(part)
    return "|".join(parts)


def stronger_confidence(current: str, repaired: str) -> str:
    if CONFIDENCE_ORDER.get(repaired, 0) > CONFIDENCE_ORDER.get(current, 0):
        return repaired
    return current


def safe_framework_field_name(field_name: str) -> str:
    return FIELD_REPAIR_ALIASES.get(field_name, field_name)


def review_field_from_tag(tag: str) -> str:
    cleaned = tag.strip()
    if cleaned.endswith("_review"):
        cleaned = cleaned[: -len("_review")]
    return safe_framework_field_name(cleaned)


def evidence_is_empty(value: str) -> bool:
    cleaned = (value or "").strip().lower()
    return not cleaned or cleaned == "no deep research evidence matched."


def summarize_repair_source_hits(source_hit_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    by_player: dict[str, list[str]] = defaultdict(list)
    for row in source_hit_rows:
        player_id = row.get("player_id", "")
        if player_id not in REPAIR_PRIORITY_PLAYER_IDS:
            continue
        if row.get("extraction_candidate", "").strip().lower() not in {"yes", "true", "1"}:
            continue
        if row.get("display_only_allowed", "").strip().lower() not in {"yes", "true", "1"}:
            continue
        field = safe_framework_field_name(row.get("framework_field", "source_safe_context"))
        status = row.get("suggested_field_status", "review_context")
        sample = row.get("source_snippet_or_sample_value", "").strip()
        note = row.get("notes", "").strip()
        summary = f"{field}: {status}"
        if sample:
            summary += f" ({sample})"
        if note:
            summary += f"; {note}"
        by_player[player_id].append(summary)
    return by_player


def build_repair_context(
    repair_tag_rows: list[dict[str, str]],
    repair_source_hit_rows: list[dict[str, str]],
) -> dict[str, dict[str, object]]:
    tag_by_player = {
        row.get("player_id", ""): row
        for row in repair_tag_rows
        if row.get("player_id", "") in REPAIR_PRIORITY_PLAYER_IDS
    }
    source_hits_by_player = summarize_repair_source_hits(repair_source_hit_rows)
    repair_context: dict[str, dict[str, object]] = {}
    for player_id in sorted(set(tag_by_player) | set(source_hits_by_player)):
        repair_context[player_id] = {
            "tag_row": tag_by_player.get(player_id, {}),
            "source_hit_summaries": source_hits_by_player.get(player_id, []),
        }
    return repair_context


def apply_repair_context(row: dict[str, str], repair_context: dict[str, object]) -> dict[str, str]:
    if not repair_context:
        return row

    tag_row = repair_context.get("tag_row", {})
    source_hit_summaries = repair_context.get("source_hit_summaries", [])
    if not isinstance(tag_row, dict):
        tag_row = {}
    if not isinstance(source_hit_summaries, list):
        source_hit_summaries = []

    tag_evidence = tag_row.get("evidence_summary", "").strip()
    source_hit_text = " | ".join(str(item) for item in source_hit_summaries if item)
    if tag_evidence:
        repair_evidence = f"reconciliation_repair_context: {tag_evidence}"
        if evidence_is_empty(row.get("best_source_safe_evidence_summary", "")):
            row["best_source_safe_evidence_summary"] = repair_evidence
        elif repair_evidence not in row.get("best_source_safe_evidence_summary", ""):
            row["best_source_safe_evidence_summary"] = f"{row['best_source_safe_evidence_summary']} | {repair_evidence}"
    if source_hit_text:
        source_evidence = f"source_hit_context: {source_hit_text}"
        if evidence_is_empty(row.get("best_source_safe_evidence_summary", "")):
            row["best_source_safe_evidence_summary"] = source_evidence
        elif source_evidence not in row.get("best_source_safe_evidence_summary", ""):
            row["best_source_safe_evidence_summary"] = f"{row['best_source_safe_evidence_summary']} | {source_evidence}"

    manual_tags = [
        f"{review_field_from_tag(tag)}: repair_context_review_only"
        for tag in split_pipe(tag_row.get("manual_review_tags", ""))
    ]
    source_hit_flags = []
    for summary in source_hit_summaries:
        field, _, status = str(summary).partition(":")
        if field:
            source_hit_flags.append(f"{field.strip()}: {status.strip().split(';')[0] or 'repair_context_review_only'}")

    row["manual_review_flags"] = merge_pipe(row.get("manual_review_flags", ""), "|".join(manual_tags), "|".join(source_hit_flags))
    row["remaining_true_gaps"] = merge_pipe(row.get("remaining_true_gaps", ""), tag_row.get("missing_data_tags", ""))
    row["soft_flags"] = merge_pipe(row.get("soft_flags", ""), tag_row.get("soft_flag_tags", ""), "SOURCE_SAFE_REPAIR_CONTEXT")
    row["source_confidence"] = stronger_confidence(row.get("source_confidence", ""), tag_row.get("tag_confidence", ""))

    if not row.get("tag_summary") and tag_row.get("applied_tags"):
        row["tag_summary"] = tag_row["applied_tags"]
    row["notes"] = append_note(
        row.get("notes", ""),
        "Reconciliation repair carried approved source-safe local context into review fields; no production promotion.",
    )
    if row.get("player_id") == "prospect:2026:omarcooper:WR":
        row["notes"] = append_note(row["notes"], "Alias repaired: Omar Cooper Jr. maps to Omar Cooper.")
    return row


def pick_zone(row: dict[str, str]) -> str:
    return row.get("v03_candidate_pick_zone") or row.get("current_pick_zone") or "unavailable"


def review_bucket_for(row: dict[str, str]) -> str:
    zone = pick_zone(row)
    action = row.get("v03_candidate_action", "").strip().lower()
    if zone in {"1.03", "1.04"}:
        return "premium_review"
    if zone in {"2.04", "2.08"}:
        return "round2_review"
    if zone == "5.04":
        return "5_04_watchlist"
    if action in {"cap", "capped"} or row.get("hard_caps"):
        return "capped"
    if zone in {"pass/manual_add", "manual_review"}:
        return "manual_review"
    return "unavailable"


def review_status_for(row: dict[str, str]) -> str:
    zone = pick_zone(row)
    action = row.get("v03_candidate_action", "").strip().lower()
    hard_caps = row.get("hard_caps", "").strip()
    manual_flags = row.get("urgent_manual_flags", "").strip()
    gaps = row.get("remaining_true_gaps", "").strip()
    if action in {"cap", "capped"} or hard_caps:
        return "capped_review"
    if zone == "5.04":
        return "watchlist_review"
    if zone == "pass/manual_add":
        return "hold_until_roster_declaration"
    if zone == "unavailable":
        return "unavailable"
    if gaps and not manual_flags:
        return "needs_data"
    return "review_needed"


def urgent_questions_for(row: dict[str, str]) -> str:
    flags = split_pipe(row.get("urgent_manual_flags", ""))
    questions = []
    for flag in flags:
        field, _, status = flag.partition(":")
        field = field.strip()
        status = status.strip()
        if field:
            questions.append(f"{field} requires {status or 'manual review'}")
    if row.get("player_name", "").strip().lower() == "jordyn tyson":
        questions.append("premium injury context requires human review before any premium-zone decision")
    return " | ".join(dict.fromkeys(questions))


def normalize_review_row(
    row: dict[str, str],
    source_warnings: dict[str, str],
    conflicts: dict[str, str],
    repair_context: dict[str, dict[str, object]],
) -> dict[str, str]:
    player_id = row.get("player_id", "")
    bucket = review_bucket_for(row)
    notes = row.get("notes", "")
    if bucket == "premium_review":
        notes = append_note(notes, "1.03 remains empty unless source artifacts change; 1.04 remains manual-review only; no automatic promotion.")
    normalized = {
        "player_id": player_id,
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "school": row.get("school", ""),
        "current_pick_zone": row.get("current_pick_zone", ""),
        "v03_candidate_pick_zone": row.get("v03_candidate_pick_zone", ""),
        "review_bucket": bucket,
        "position_group": row.get("position", ""),
        "tag_summary": row.get("tag_summary", ""),
        "hard_caps": row.get("hard_caps", ""),
        "soft_flags": row.get("soft_flags", ""),
        "manual_review_flags": row.get("urgent_manual_flags", ""),
        "urgent_manual_questions": urgent_questions_for(row),
        "source_confidence": row.get("source_confidence", ""),
        "best_source_safe_evidence_summary": row.get("best_source_safe_evidence_summary", ""),
        "remaining_true_gaps": row.get("remaining_true_gaps", ""),
        "prohibited_sources_detected": source_warnings.get(player_id, "none"),
        "source_conflict_status": conflicts.get(player_id, "none"),
        "review_status": review_status_for(row),
        "notes": notes,
    }
    return apply_repair_context(normalized, repair_context.get(player_id, {}))


def append_note(existing: str, addition: str) -> str:
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing} {addition}"


def stable_sort(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (
            BUCKET_ORDER.get(row.get("review_bucket", ""), 99),
            POSITION_ORDER.get(row.get("position", ""), 99),
            row.get("player_name", "").lower(),
            row.get("player_id", ""),
        ),
    )


def rows_by_player(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("player_id", ""): row for row in rows if row.get("player_id")}


def build_review_rows(
    player_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    conflict_rows: list[dict[str, str]],
    repair_context: dict[str, dict[str, object]],
) -> tuple[list[dict[str, str]], list[str]]:
    source_warnings, blockers = build_source_warnings(source_rows)
    conflicts = build_conflicts(conflict_rows, source_rows)
    rows = [normalize_review_row(row, source_warnings, conflicts, repair_context) for row in player_rows]
    invalid_statuses = sorted({row["review_status"] for row in rows} - REVIEW_STATUS_VALUES)
    if invalid_statuses:
        raise ReviewBoardError(f"Unexpected review_status values: {', '.join(invalid_statuses)}")
    validate_output_columns(REVIEW_COLUMNS)
    return stable_sort(rows), blockers


def build_manual_flag_rows(
    manual_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
    source_warnings: dict[str, str],
    conflicts: dict[str, str],
) -> list[dict[str, str]]:
    review_by_player = rows_by_player(review_rows)
    output = []
    seen = set()

    for review in review_rows:
        for flag in split_pipe(review.get("manual_review_flags", "")):
            field, _, status = flag.partition(":")
            field = field.strip()
            if not field:
                continue
            priority = "high" if "injury" in field.lower() or "manual_review_only" in status else "medium"
            key = (review["player_id"], field, status.strip())
            seen.add(key)
            output.append(
                {
                    "player_id": review["player_id"],
                    "player_name": review["player_name"],
                    "position": review["position"],
                    "school": review["school"],
                    "review_bucket": review["review_bucket"],
                    "framework_field": field,
                    "flag_type": status.strip() or "manual_review_only",
                    "review_priority": priority,
                    "urgent_manual_question": f"{field} requires {status.strip() or 'manual review'}",
                    "source_name": "",
                    "source_url": "",
                    "prohibited_sources_detected": review["prohibited_sources_detected"],
                    "source_conflict_status": review["source_conflict_status"],
                    "reason": "candidate urgent_manual_flags",
                }
            )

    for manual in manual_rows:
        player_id = manual.get("player_id", "")
        review = review_by_player.get(player_id, {})
        field = manual.get("framework_field", "")
        status = manual.get("flag_type", "")
        key = (player_id, field, status)
        if key in seen:
            continue
        output.append(
            {
                "player_id": player_id,
                "player_name": manual.get("player_name", ""),
                "position": manual.get("position", ""),
                "school": manual.get("school", ""),
                "review_bucket": review.get("review_bucket", review_bucket_for(manual)),
                "framework_field": field,
                "flag_type": status,
                "review_priority": manual.get("review_priority", ""),
                "urgent_manual_question": f"{field} requires {status}" if field else status,
                "source_name": manual.get("source_name", ""),
                "source_url": manual.get("source_url", ""),
                "prohibited_sources_detected": source_warnings.get(player_id, review.get("prohibited_sources_detected", "none")),
                "source_conflict_status": conflicts.get(player_id, review.get("source_conflict_status", "none")),
                "reason": manual.get("reason", ""),
            }
        )

    return sorted(
        output,
        key=lambda row: (
            {"high": 0, "medium": 1, "low": 2}.get(row.get("review_priority", ""), 9),
            BUCKET_ORDER.get(row.get("review_bucket", ""), 99),
            row.get("player_name", "").lower(),
            row.get("framework_field", ""),
        ),
    )


def build_gap_rows(gap_rows: list[dict[str, str]], review_rows: list[dict[str, str]], conflicts: dict[str, str]) -> list[dict[str, str]]:
    review_by_player = rows_by_player(review_rows)
    output = []
    for row in gap_rows:
        player_id = row.get("player_id", "")
        review = review_by_player.get(player_id, {})
        output.append(
            {
                "player_id": player_id,
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "school": row.get("school", ""),
                "review_bucket": review.get("review_bucket", review_bucket_for(row)),
                "missing_field": row.get("missing_field", ""),
                "marked_value": row.get("marked_value", "unavailable"),
                "recommended_next_source": row.get("recommended_next_source", ""),
                "severity": row.get("severity", ""),
                "source_conflict_status": conflicts.get(player_id, review.get("source_conflict_status", "none")),
                "reason_missing": row.get("reason_missing", ""),
            }
        )
    return sorted(
        output,
        key=lambda row: (
            {"high": 0, "medium": 1, "low": 2}.get(row.get("severity", ""), 9),
            BUCKET_ORDER.get(row.get("review_bucket", ""), 99),
            row.get("player_name", "").lower(),
            row.get("missing_field", ""),
        ),
    )


def load_named_inputs(input_root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "player_board": read_csv(input_root / PLAYER_BOARD),
        "premium_board": read_csv(input_root / PREMIUM_BOARD),
        "round2_board": read_csv(input_root / ROUND2_BOARD),
        "watch_5_04_board": read_csv(input_root / WATCH_504_BOARD),
        "manual_flags": read_csv(input_root / MANUAL_FLAGS),
        "remaining_gaps": read_csv(input_root / REMAINING_GAPS),
        "source_safety": read_csv(input_root / SOURCE_SAFETY),
        "conflict_review": read_csv(input_root / CONFLICT_REVIEW),
        "adversarial_findings": read_csv(input_root / ADVERSARIAL_FINDINGS),
        "patch_queue": read_csv(input_root / PATCH_QUEUE),
        "repair_tags": read_optional_csv(input_root / REPAIR_TAGS),
        "repair_source_hits": read_optional_csv(input_root / REPAIR_SOURCE_HITS),
    }


def write_readme(output_dir: Path, review_rows: list[dict[str, str]], manual_rows: list[dict[str, str]], gap_rows: list[dict[str, str]]) -> None:
    premium_count = sum(1 for row in review_rows if row["review_bucket"] == "premium_review")
    round2_count = sum(1 for row in review_rows if row["review_bucket"] == "round2_review")
    watch_count = sum(1 for row in review_rows if row["review_bucket"] == "5_04_watchlist" and row["review_status"] == "watchlist_review")
    text = f"""# Rookie Review Board v0.3

Status: review-only local export.

## Outputs

- `rookie_review_board_v03.csv`
- `rookie_review_board_premium_review_v03.csv`
- `rookie_review_board_round2_v03.csv`
- `rookie_review_board_5_04_watchlist_v03.csv`
- `rookie_review_board_manual_flags_v03.csv`
- `rookie_review_board_remaining_gaps_v03.csv`

## Counts

- Full review rows: {len(review_rows)}
- Premium review rows: {premium_count}
- Round 2 review rows: {round2_count}
- 5.04 watchlist rows: {watch_count}
- Manual flag rows: {len(manual_rows)}
- Remaining gap rows: {len(gap_rows)}

## Guardrails

- 1.03 remains empty unless the underlying artifacts say otherwise.
- 1.04 remains manual-review only.
- Jordyn Tyson injury review is surfaced in the premium/manual review context.
- No player is automatically promoted.
- No final rankings, probabilities, bands, app-readable outputs, production scoring, private scores, formulas, Streamlit wiring, outcome-column files, or veteran outcome-head inputs were created.
"""
    (output_dir / "README_ROOKIE_REVIEW_BOARD_V03.md").write_text(text, encoding="utf-8")


def build_exports(input_root: Path, output_dir: Path, strict: bool = False) -> dict[str, int]:
    require_inputs(input_root)
    named = load_named_inputs(input_root)
    if strict:
        strict_validate_input_columns(
            {
                key: named[key]
                for key in ["player_board", "premium_board", "round2_board", "watch_5_04_board"]
            }
        )
    source_warnings, blockers = build_source_warnings(named["source_safety"])
    if strict and blockers:
        raise ReviewBoardError("Market contamination blockers detected:\n" + "\n".join(blockers))
    conflicts = build_conflicts(named["conflict_review"], named["source_safety"])
    repair_context = build_repair_context(named["repair_tags"], named["repair_source_hits"])
    review_rows, blockers_from_build = build_review_rows(
        named["player_board"],
        named["source_safety"],
        named["conflict_review"],
        repair_context,
    )
    if strict and blockers_from_build:
        raise ReviewBoardError("Market contamination blockers detected:\n" + "\n".join(blockers_from_build))

    premium_rows = [row for row in review_rows if row["review_bucket"] == "premium_review"]
    round2_rows = [row for row in review_rows if row["review_bucket"] == "round2_review"]
    watch_rows = [
        row
        for row in review_rows
        if row["review_bucket"] == "5_04_watchlist" and row["review_status"] == "watchlist_review"
    ]
    manual_flag_rows = build_manual_flag_rows(named["manual_flags"], review_rows, source_warnings, conflicts)
    gap_rows = build_gap_rows(named["remaining_gaps"], review_rows, conflicts)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_review_board_v03.csv", review_rows, REVIEW_COLUMNS)
    write_csv(output_dir / "rookie_review_board_premium_review_v03.csv", premium_rows, REVIEW_COLUMNS)
    write_csv(output_dir / "rookie_review_board_round2_v03.csv", round2_rows, REVIEW_COLUMNS)
    write_csv(output_dir / "rookie_review_board_5_04_watchlist_v03.csv", watch_rows, REVIEW_COLUMNS)
    write_csv(output_dir / "rookie_review_board_manual_flags_v03.csv", manual_flag_rows, MANUAL_FLAG_COLUMNS)
    write_csv(output_dir / "rookie_review_board_remaining_gaps_v03.csv", gap_rows, GAP_COLUMNS)
    write_readme(output_dir, review_rows, manual_flag_rows, gap_rows)

    return {
        "review_rows": len(review_rows),
        "premium_rows": len(premium_rows),
        "round2_rows": len(round2_rows),
        "watch_rows": len(watch_rows),
        "manual_flag_rows": len(manual_flag_rows),
        "gap_rows": len(gap_rows),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Rookie Framework v0.3 review-board exports.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_root = args.input_root
    output_dir = args.output_dir or input_root / "review_board_v03"
    try:
        counts = build_exports(input_root=input_root, output_dir=output_dir, strict=args.strict)
    except ReviewBoardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
