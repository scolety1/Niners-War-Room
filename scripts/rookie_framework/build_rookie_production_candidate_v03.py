"""Build Rookie Framework v0.3 production-candidate exports.

This script is candidate/export-only. It consumes the local Step 3 shadow
ranking exports and writes local-only production-candidate files. It does not
replace production rankings, change private scores, create probabilities or
bands, write app outputs, create outcome columns, or use veteran outcome heads.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT_ROOT = Path("local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03")
DEFAULT_OUTPUT_DIR = Path("local_exports/model_v4/rookie_framework_v02/production_candidate_v03")

SHADOW_FULL = Path("rookie_shadow_ranking_v03.csv")
SHADOW_PREMIUM = Path("rookie_shadow_ranking_premium_v03.csv")
SHADOW_ROUND2 = Path("rookie_shadow_ranking_round2_v03.csv")
SHADOW_5_04 = Path("rookie_shadow_ranking_5_04_watchlist_v03.csv")
SHADOW_README = Path("README_ROOKIE_SHADOW_RANKING_V03.md")

REQUIRED_INPUTS = [SHADOW_FULL, SHADOW_PREMIUM, SHADOW_ROUND2, SHADOW_5_04, SHADOW_README]

CANDIDATE_COLUMNS = [
    "candidate_rank",
    "player_id",
    "player_name",
    "position",
    "school",
    "pick_zone",
    "tag_summary",
    "production_ready_status",
    "promotion_blockers",
    "manual_warnings",
    "source_confidence",
    "evidence_basis_summary",
    "why_ranked_here",
    "why_not_higher",
    "why_not_lower",
    "production_candidate_only",
    "app_read_allowed",
    "probabilities_created",
    "source_safety_notes",
]

SOURCE_AUDIT_COLUMNS = [
    "player_id",
    "player_name",
    "pick_zone",
    "production_ready_status",
    "source_confidence",
    "prohibited_sources_detected",
    "source_conflict_status",
    "hard_caps",
    "manual_review_flags",
    "remaining_true_gaps",
    "source_safety_notes",
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

ALLOWED_WARNING_COLUMNS = {"prohibited_sources_detected"}

GROUP_ORDER = {
    "premium_shadow_review": 0,
    "round2_shadow_review": 1,
    "5_04_shadow_watchlist": 2,
    "manual_shadow_review": 3,
    "capped_shadow_review": 4,
    "unavailable_shadow_review": 5,
}
STATUS_ORDER = {"ready": 0, "manual_warning": 1, "unavailable": 2, "blocked": 3}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}
POSITION_ORDER = {"RB": 0, "WR": 1, "TE": 2, "QB": 3}


class ProductionCandidateError(RuntimeError):
    """Raised when production-candidate export validation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ProductionCandidateError(f"Missing required input: {path}")
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
        raise ProductionCandidateError("Required shadow-ranking inputs are missing:\n" + "\n".join(f"- {p}" for p in missing))


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
    return [part.strip() for part in value.split("|") if part.strip() and part.strip().lower() != "none"]


def is_blank_or_none(value: str) -> bool:
    return not value.strip() or value.strip().lower() == "none"


def production_ready_status(row: dict[str, str]) -> str:
    if not is_blank_or_none(row.get("hard_caps", "")):
        return "blocked"
    if not is_blank_or_none(row.get("source_conflict_status", "")):
        return "blocked"
    if row.get("review_status", "") in {"capped_review", "unavailable"}:
        return "blocked"
    if row.get("review_status", "") == "hold_until_roster_declaration":
        return "unavailable"
    if row.get("review_status", "") == "needs_data":
        return "unavailable"
    if row.get("source_confidence", "") == "low" and row.get("review_bucket", "") != "5_04_watchlist":
        return "unavailable"
    if not is_blank_or_none(row.get("manual_review_flags", "")):
        return "manual_warning"
    if not is_blank_or_none(row.get("remaining_true_gaps", "")):
        return "manual_warning"
    if not is_blank_or_none(row.get("prohibited_sources_detected", "")):
        return "manual_warning"
    if row.get("source_confidence", "") == "low":
        return "manual_warning"
    return "ready"


def promotion_blockers(row: dict[str, str], status: str) -> str:
    blockers: list[str] = []
    if not is_blank_or_none(row.get("hard_caps", "")):
        blockers.append(f"hard_caps={row.get('hard_caps')}")
    if not is_blank_or_none(row.get("source_conflict_status", "")):
        blockers.append(f"source_conflict_status={row.get('source_conflict_status')}")
    if row.get("review_status", "") in {"capped_review", "unavailable", "needs_data", "hold_until_roster_declaration"}:
        blockers.append(f"review_status={row.get('review_status')}")
    if status == "unavailable" and row.get("source_confidence", "") == "low":
        blockers.append("low_source_confidence")
    if not is_blank_or_none(row.get("remaining_true_gaps", "")):
        blockers.append("remaining_gaps_present")
    if not blockers:
        return "none"
    return "|".join(blockers)


def manual_warnings(row: dict[str, str]) -> str:
    warnings: list[str] = []
    warnings.extend(f"manual={item}" for item in split_pipe(row.get("manual_review_flags", "")))
    if not is_blank_or_none(row.get("soft_flags", "")):
        warnings.append(f"soft_flags={row.get('soft_flags')}")
    if not is_blank_or_none(row.get("prohibited_sources_detected", "")):
        warnings.append(f"quarantined_sources={row.get('prohibited_sources_detected')}")
    if not is_blank_or_none(row.get("remaining_true_gaps", "")):
        warnings.append(f"remaining_gaps={row.get('remaining_true_gaps')}")
    return "|".join(warnings) if warnings else "none"


def source_safety_notes(row: dict[str, str], status: str) -> str:
    notes = [
        "candidate/export-only",
        "not_app_read",
        "no_probabilities_or_bands",
        "no_veteran_outcome_heads",
    ]
    if not is_blank_or_none(row.get("prohibited_sources_detected", "")):
        notes.append("prohibited source context is warning-only")
    if "manual_review_only" in row.get("manual_review_flags", ""):
        notes.append("manual-only evidence is not private value")
    if status in {"blocked", "unavailable"}:
        notes.append("not eligible for promotion movement")
    return "; ".join(notes)


def order_key(row: dict[str, str]) -> tuple:
    status = production_ready_status(row)
    return (
        GROUP_ORDER.get(row.get("shadow_review_group", ""), 99),
        STATUS_ORDER.get(status, 99),
        CONFIDENCE_ORDER.get(row.get("source_confidence", ""), 99),
        int(row.get("remaining_gap_count", "99") or "99"),
        int(row.get("manual_flag_count", "99") or "99"),
        POSITION_ORDER.get(row.get("position", ""), 99),
        int(row.get("shadow_order", "9999") or "9999"),
        row.get("player_name", "").lower(),
    )


def why_ranked_here(row: dict[str, str], status: str) -> str:
    return (
        f"Candidate order from shadow group={row.get('shadow_review_group')}, "
        f"production_ready_status={status}, source_confidence={row.get('source_confidence')}, "
        f"remaining_gap_count={row.get('remaining_gap_count')}, manual_flag_count={row.get('manual_flag_count')}; "
        "no market/rank/projection/private-score/probability/band inputs."
    )


def why_not_higher(row: dict[str, str], status: str) -> str:
    if row.get("current_pick_zone") == "1.04":
        return "1.03 remains empty; premium row still carries manual-review/source-safety gates."
    if status == "blocked":
        return "Blocked by hard cap, source conflict, or capped/unavailable review status."
    if status == "unavailable":
        return "Needs data or roster declaration context before promotion movement."
    if status == "manual_warning":
        return "Manual warnings, gaps, soft flags, or quarantined source terms remain visible."
    return "Higher rows have earlier pick-zone context or stronger source confidence."


def why_not_lower(row: dict[str, str], status: str) -> str:
    if status == "ready":
        return "No manual warnings, blockers, or prohibited source caveats are present in the row."
    if row.get("shadow_review_group") == "premium_shadow_review":
        return "Premium manual-review context remains ahead of later pick-zone candidates."
    if row.get("shadow_review_group") == "round2_shadow_review":
        return "Round 2 review context remains ahead of 5.04 watchlist rows."
    if row.get("shadow_review_group") == "5_04_shadow_watchlist":
        return "Uncapped 5.04 watchlist context remains ahead of capped/manual parking-lot rows."
    return "Candidate remains in source-preserved shadow group order."


def normalize_candidate_rows(shadow_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ordered = sorted(shadow_rows, key=order_key)
    output: list[dict[str, str]] = []
    for index, row in enumerate(ordered, start=1):
        status = production_ready_status(row)
        output.append(
            {
                "candidate_rank": str(index),
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "school": row.get("school", ""),
                "pick_zone": row.get("current_pick_zone", ""),
                "tag_summary": row.get("tag_summary", ""),
                "production_ready_status": status,
                "promotion_blockers": promotion_blockers(row, status),
                "manual_warnings": manual_warnings(row),
                "source_confidence": row.get("source_confidence", ""),
                "evidence_basis_summary": row.get("best_source_safe_evidence_summary", ""),
                "why_ranked_here": why_ranked_here(row, status),
                "why_not_higher": why_not_higher(row, status),
                "why_not_lower": why_not_lower(row, status),
                "production_candidate_only": "yes",
                "app_read_allowed": "no",
                "probabilities_created": "no",
                "source_safety_notes": source_safety_notes(row, status),
            }
        )
    return output


def source_audit_rows(shadow_rows: list[dict[str, str]], candidate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["player_id"]: row for row in candidate_rows}
    rows = []
    for row in shadow_rows:
        candidate = by_id.get(row.get("player_id", ""), {})
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "pick_zone": row.get("current_pick_zone", ""),
                "production_ready_status": candidate.get("production_ready_status", ""),
                "source_confidence": row.get("source_confidence", ""),
                "prohibited_sources_detected": row.get("prohibited_sources_detected", "none"),
                "source_conflict_status": row.get("source_conflict_status", "none"),
                "hard_caps": row.get("hard_caps", ""),
                "manual_review_flags": row.get("manual_review_flags", ""),
                "remaining_true_gaps": row.get("remaining_true_gaps", ""),
                "source_safety_notes": candidate.get("source_safety_notes", ""),
            }
        )
    return rows


def strict_validate_inputs(named_inputs: dict[str, list[dict[str, str]]]) -> None:
    problems = []
    for name, rows in named_inputs.items():
        if not rows:
            continue
        bad = find_prohibited_private_input_columns(rows[0].keys())
        if bad:
            problems.append(f"{name}: {', '.join(bad)}")
    if problems:
        raise ProductionCandidateError("Prohibited private input columns detected:\n" + "\n".join(problems))


def validate_candidate_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ProductionCandidateError("No production-candidate rows were produced.")
    if any(row.get("pick_zone") == "1.03" for row in rows):
        raise ProductionCandidateError("1.03 was unexpectedly populated; it must remain empty unless supported.")
    bad_candidate = [row["player_id"] for row in rows if row.get("production_candidate_only") != "yes"]
    bad_app = [row["player_id"] for row in rows if row.get("app_read_allowed") != "no"]
    bad_prob = [row["player_id"] for row in rows if row.get("probabilities_created") != "no"]
    if bad_candidate:
        raise ProductionCandidateError("Rows missing production_candidate_only=yes: " + ", ".join(bad_candidate[:10]))
    if bad_app:
        raise ProductionCandidateError("Rows missing app_read_allowed=no: " + ", ".join(bad_app[:10]))
    if bad_prob:
        raise ProductionCandidateError("Rows missing probabilities_created=no: " + ", ".join(bad_prob[:10]))


def write_readme(output_dir: Path, rows: list[dict[str, str]]) -> None:
    status_counts = Counter(row["production_ready_status"] for row in rows)
    zone_counts = Counter(row["pick_zone"] for row in rows)
    text = f"""# Rookie Production-Candidate v0.3

Status: production-candidate-only local export.

This export does not replace production rankings, does not create app-readable
tables, does not create probabilities or bands, and does not use veteran outcome
heads.

## Outputs

- `rookie_production_candidate_v03.csv`
- `rookie_production_candidate_premium_v03.csv`
- `rookie_production_candidate_round2_v03.csv`
- `rookie_production_candidate_5_04_v03.csv`
- `rookie_production_candidate_manual_warnings_v03.csv`
- `rookie_production_candidate_source_safety_audit_v03.csv`
- `README_ROOKIE_PRODUCTION_CANDIDATE_V03.md`

## Counts

- Total candidate rows: {len(rows)}
- Ready rows: {status_counts.get('ready', 0)}
- Manual-warning rows: {status_counts.get('manual_warning', 0)}
- Blocked rows: {status_counts.get('blocked', 0)}
- Unavailable rows: {status_counts.get('unavailable', 0)}
- 1.03 rows: {zone_counts.get('1.03', 0)}
- 1.04 rows: {zone_counts.get('1.04', 0)}
- Round 2 rows: {zone_counts.get('2.08', 0)}
- 5.04 rows: {zone_counts.get('5.04', 0)}

## Guardrails

- Every row has `production_candidate_only=yes`.
- Every row has `app_read_allowed=no`.
- Every row has `probabilities_created=no`.
- `1.03` remains empty when unsupported.
- Manual warnings and promotion blockers remain visible.
"""
    (output_dir / "README_ROOKIE_PRODUCTION_CANDIDATE_V03.md").write_text(text, encoding="utf-8")


def build_exports(input_root: Path, output_dir: Path, strict: bool = False) -> dict[str, int]:
    require_inputs(input_root)
    named_inputs = {
        "shadow_full": read_csv(input_root / SHADOW_FULL),
        "shadow_premium": read_csv(input_root / SHADOW_PREMIUM),
        "shadow_round2": read_csv(input_root / SHADOW_ROUND2),
        "shadow_5_04": read_csv(input_root / SHADOW_5_04),
    }
    if strict:
        strict_validate_inputs(named_inputs)
    rows = normalize_candidate_rows(named_inputs["shadow_full"])
    validate_candidate_rows(rows)

    premium_ids = {row["player_id"] for row in named_inputs["shadow_premium"]}
    round2_ids = {row["player_id"] for row in named_inputs["shadow_round2"]}
    watch_ids = {row["player_id"] for row in named_inputs["shadow_5_04"]}

    premium = [row for row in rows if row["player_id"] in premium_ids]
    round2 = [row for row in rows if row["player_id"] in round2_ids]
    watch = [row for row in rows if row["player_id"] in watch_ids]
    warnings = [row for row in rows if row["production_ready_status"] != "ready" or row["manual_warnings"] != "none"]
    audit = source_audit_rows(named_inputs["shadow_full"], rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_production_candidate_v03.csv", rows, CANDIDATE_COLUMNS)
    write_csv(output_dir / "rookie_production_candidate_premium_v03.csv", premium, CANDIDATE_COLUMNS)
    write_csv(output_dir / "rookie_production_candidate_round2_v03.csv", round2, CANDIDATE_COLUMNS)
    write_csv(output_dir / "rookie_production_candidate_5_04_v03.csv", watch, CANDIDATE_COLUMNS)
    write_csv(output_dir / "rookie_production_candidate_manual_warnings_v03.csv", warnings, CANDIDATE_COLUMNS)
    write_csv(output_dir / "rookie_production_candidate_source_safety_audit_v03.csv", audit, SOURCE_AUDIT_COLUMNS)
    write_readme(output_dir, rows)

    status_counts = Counter(row["production_ready_status"] for row in rows)
    return {
        "candidate_rows": len(rows),
        "premium_rows": len(premium),
        "round2_rows": len(round2),
        "watch_rows": len(watch),
        "manual_warning_rows": len(warnings),
        "source_audit_rows": len(audit),
        "ready_rows": status_counts.get("ready", 0),
        "blocked_rows": status_counts.get("blocked", 0),
        "unavailable_rows": status_counts.get("unavailable", 0),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Rookie Framework v0.3 production-candidate exports.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    try:
        counts = build_exports(input_root=args.input_root, output_dir=output_dir, strict=args.strict)
    except ProductionCandidateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
