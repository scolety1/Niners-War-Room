"""Build a current 2026 feature-aware rookie rescore candidate.

This local/manual-use script applies the fixed historically supported
cfbd_enriched_baseline_v1_1 formula to the current 2026 CFBD feature-ingested
board. It does not tune new weights, create probabilities/bands, or promote a
production/app-readable artifact.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.tune_rookie_model_runway_v1_1 import (  # noqa: E402
    BASELINE_CONFIG,
    market_share_component,
    production_component,
    score_value,
    to_float,
)


DEFAULT_INPUT = Path(
    "local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/"
    "current_2026_feature_ingested_manual_board_20260615.csv"
)
DEFAULT_COVERAGE = Path(
    "local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/"
    "current_2026_cfbd_feature_coverage_by_position_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615")
POSITIONS = ("QB", "RB", "WR", "TE")
STATUS_BUCKETS = {
    "rankable_with_warning": 0,
    "manual_review_required": 1,
    "blocked": 2,
    "unavailable": 3,
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


def parse_draft_capital(value: str) -> tuple[str, str]:
    text = value or ""
    round_match = re.search(r"round=([0-9.]+)", text)
    pick_match = re.search(r"pick=([0-9.]+)", text)
    return (
        str(safe_int(round_match.group(1))) if round_match else "",
        str(safe_int(pick_match.group(1))) if pick_match else "",
    )


def model_row(row: dict[str, str]) -> dict[str, str]:
    draft_round, overall_pick = parse_draft_capital(row.get("draft_capital", ""))
    out = {
        "position": row.get("position", ""),
        "draft_round": draft_round,
        "overall_pick": overall_pick,
        "cfbd_feature_status": "deterministic_joined"
        if row.get("cfbd_current_join_status", "").startswith("matched")
        else "unmatched_current_neutral",
    }
    for key, value in row.items():
        if key.startswith("cfbd_"):
            out[key] = value
    return out


def status_bucket(row: dict[str, str]) -> int:
    return STATUS_BUCKETS.get(row.get("status", ""), 4)


def safety_label(row: dict[str, str]) -> str:
    if row.get("status") == "rankable_with_warning":
        return "rankable_with_visible_warnings"
    if row.get("status") == "manual_review_required":
        return "manual_review_required_before_draft_use"
    if row.get("status") == "blocked":
        return "blocked_not_draftable_without_repair"
    if row.get("status") == "unavailable":
        return "unavailable_not_draftable_without_repair"
    return "unknown_status_manual_review_required"


def score_current_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    scored: list[dict[str, object]] = []
    for row in rows:
        modeled = model_row(row)
        production = production_component(modeled)
        market = market_share_component(modeled)
        candidate_score = score_value(modeled, BASELINE_CONFIG)
        if modeled["cfbd_feature_status"] != "deterministic_joined":
            cfbd_policy = "unmatched_neutral_cfbd_context_not_zero_filled_as_bad_production"
        elif row.get("cfbd_denominator_status") != "denominator_ready":
            cfbd_policy = "matched_production_with_denominator_warning_visible"
        else:
            cfbd_policy = "matched_source_safe_cfbd_context"
        out: dict[str, object] = dict(row)
        out["candidate_model"] = BASELINE_CONFIG.name
        out["candidate_scope"] = "local_manual_use_only"
        out["candidate_status_bucket"] = str(status_bucket(row))
        out["candidate_safety_label"] = safety_label(row)
        out["candidate_draft_round_used"] = modeled["draft_round"]
        out["candidate_overall_pick_used"] = modeled["overall_pick"]
        out["candidate_cfbd_feature_status"] = modeled["cfbd_feature_status"]
        out["candidate_cfbd_policy"] = cfbd_policy
        out["candidate_production_component"] = f"{production:.3f}" if modeled["cfbd_feature_status"] == "deterministic_joined" else ""
        out["candidate_market_share_component"] = f"{market:.3f}" if modeled["cfbd_feature_status"] == "deterministic_joined" else ""
        out["candidate_feature_aware_score"] = f"{candidate_score:.3f}"
        out["production_allowed"] = "no"
        out["app_wiring_allowed"] = "no"
        out["promotion_status"] = "local_manual_rescore_candidate_only"
        out["probabilities_created"] = "no"
        out["bands_created"] = "no"
        scored.append(out)
    scored.sort(
        key=lambda row: (
            safe_int(row["candidate_status_bucket"], 9),
            -to_float(row["candidate_feature_aware_score"]),
            safe_int(row.get("rookie_rank"), 9999),
            str(row.get("player_name", "")),
        )
    )
    position_counts = {position: 0 for position in POSITIONS}
    for index, row in enumerate(scored, start=1):
        row["candidate_rank"] = str(index)
        position = str(row.get("position", ""))
        position_counts[position] = position_counts.get(position, 0) + 1
        row["candidate_position_rank"] = f"{position}{position_counts[position]}"
        row["rank_delta"] = str(safe_int(row.get("rookie_rank"), 9999) - index)
    return scored


def top24_summary(old_rows: list[dict[str, str]], candidate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    old_top = {row.get("player_id", ""): row for row in old_rows if safe_int(row.get("rookie_rank")) <= 24}
    new_top = {str(row.get("player_id", "")): row for row in candidate_rows if safe_int(row.get("candidate_rank")) <= 24}
    rows = []
    for player_id in sorted(set(old_top) | set(new_top)):
        old = old_top.get(player_id, {})
        new = new_top.get(player_id, {})
        row = new or old
        if player_id in old_top and player_id in new_top:
            status = "stayed_top24"
        elif player_id in new_top:
            status = "entered_top24"
        else:
            status = "left_top24"
        rows.append(
            {
                "player_id": player_id,
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "old_rank": old.get("rookie_rank", ""),
                "candidate_rank": new.get("candidate_rank", ""),
                "top24_status": status,
                "candidate_feature_aware_score": new.get("candidate_feature_aware_score", ""),
                "candidate_cfbd_policy": new.get("candidate_cfbd_policy", ""),
            }
        )
    rows.sort(key=lambda row: safe_int(row.get("candidate_rank") or row.get("old_rank"), 9999))
    return rows


def movement_rows(candidate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in candidate_rows:
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "old_rank": row.get("rookie_rank", ""),
                "candidate_rank": row.get("candidate_rank", ""),
                "rank_delta": row.get("rank_delta", ""),
                "candidate_feature_aware_score": row.get("candidate_feature_aware_score", ""),
                "candidate_production_component": row.get("candidate_production_component", ""),
                "candidate_market_share_component": row.get("candidate_market_share_component", ""),
                "cfbd_current_join_status": row.get("cfbd_current_join_status", ""),
                "cfbd_warning_flags": row.get("cfbd_warning_flags", ""),
                "movement_explanation": movement_explanation(row),
            }
        )
    rows.sort(key=lambda row: abs(safe_int(row["rank_delta"])), reverse=True)
    return rows


def movement_explanation(row: dict[str, object]) -> str:
    delta = safe_int(row.get("rank_delta"))
    if row.get("candidate_cfbd_feature_status") != "deterministic_joined":
        cause = "unmatched current CFBD row; CFBD context stayed neutral and warning-visible"
    elif row.get("cfbd_denominator_status") != "denominator_ready":
        cause = "matched production with denominator warning; share context limited"
    elif to_float(row.get("candidate_market_share_component")) >= 45:
        cause = "strong source-safe CFBD market-share/dominator component"
    elif to_float(row.get("candidate_production_component")) >= 65:
        cause = "strong source-safe CFBD production component"
    else:
        cause = "lower fixed-formula CFBD/draft/position blend relative to peers"
    if delta > 0:
        return f"rose {delta} spots: {cause}"
    if delta < 0:
        return f"fell {abs(delta)} spots: {cause}"
    return f"unchanged: {cause}"


def unmatched_rows(candidate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "candidate_rank": row.get("candidate_rank", ""),
            "old_rank": row.get("rookie_rank", ""),
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "school": row.get("school", ""),
            "cfbd_current_join_status": row.get("cfbd_current_join_status", ""),
            "candidate_cfbd_policy": row.get("candidate_cfbd_policy", ""),
            "cfbd_warning_flags": row.get("cfbd_warning_flags", ""),
        }
        for row in candidate_rows
        if not str(row.get("cfbd_current_join_status", "")).startswith("matched")
    ]


def coverage_summary(candidate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for position in POSITIONS:
        scoped = [row for row in candidate_rows if row.get("position") == position]
        matched = [row for row in scoped if str(row.get("cfbd_current_join_status", "")).startswith("matched")]
        denominator = [row for row in matched if row.get("cfbd_denominator_status") == "denominator_ready"]
        rows.append(
            {
                "position": position,
                "rows": str(len(scoped)),
                "matched_rows": str(len(matched)),
                "unmatched_rows": str(len(scoped) - len(matched)),
                "denominator_ready_rows": str(len(denominator)),
                "matched_rate": f"{len(matched) / len(scoped):.3f}" if scoped else "0.000",
                "denominator_ready_rate": f"{len(denominator) / len(scoped):.3f}" if scoped else "0.000",
            }
        )
    return rows


def write_readme(output_dir: Path) -> None:
    text = [
        "# Current 2026 Feature-Aware Rescore Candidate",
        "",
        "Local/manual-use feature-aware rookie draft ranking candidate.",
        "",
        "- model: cfbd_enriched_baseline_v1_1",
        "- tuning: none",
        "- production_allowed: no",
        "- app_wiring_allowed: no",
        "- probabilities/bands: no",
        "",
        "Unmatched CFBD rows are neutral for CFBD context and warning-visible.",
    ]
    (output_dir / "README_CURRENT_2026_FEATURE_AWARE_RESCORE_CANDIDATE_20260615.md").write_text("\n".join(text), encoding="utf-8")


def all_columns(rows: list[dict[str, object]]) -> list[str]:
    columns = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def build_exports(input_path: Path, coverage_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    old_rows = read_csv(input_path)
    candidate = score_current_rows(old_rows)
    movement = movement_rows(candidate)
    top24 = top24_summary(old_rows, candidate)
    unmatched = unmatched_rows(candidate)
    coverage = coverage_summary(candidate)
    write_csv(output_dir / "current_2026_feature_aware_candidate_board_20260615.csv", candidate, all_columns(candidate))
    write_csv(output_dir / "current_2026_feature_aware_rank_movement_20260615.csv", movement, all_columns(movement))
    write_csv(output_dir / "current_2026_feature_aware_top24_old_vs_new_20260615.csv", top24, all_columns(top24))
    write_csv(output_dir / "current_2026_feature_aware_unmatched_policy_20260615.csv", unmatched, all_columns(unmatched))
    write_csv(output_dir / "current_2026_feature_aware_coverage_by_position_20260615.csv", coverage, all_columns(coverage))
    original_coverage = read_csv(coverage_path)
    if original_coverage:
        write_csv(output_dir / "current_2026_source_ingestion_coverage_reference_20260615.csv", original_coverage, list(original_coverage[0].keys()))
    write_readme(output_dir)
    return {
        "old_rows": old_rows,
        "candidate_rows": candidate,
        "movement_rows": movement,
        "top24_rows": top24,
        "unmatched_rows": unmatched,
        "coverage_rows": coverage,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.input, args.coverage, args.output_dir)
    print(f"candidate_rows={len(result['candidate_rows'])}")
    print(f"top24_rows={len([row for row in result['candidate_rows'] if safe_int(row.get('candidate_rank')) <= 24])}")
    print(f"unmatched_rows={len(result['unmatched_rows'])}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
