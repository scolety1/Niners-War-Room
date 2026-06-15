"""Build rookie-only manual draft ranking v1 exports.

The output is a local manual draft board for Tim's 10-team 1QB non-PPR,
first-down-sensitive league. It is not a production ranking, private score,
probability, band, app output, or promoted artifact.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


DEFAULT_ANALYZER = Path("local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03/rookie_analyzer_v03.csv")
DEFAULT_FEATURES = Path("local_exports/model_v4/rookie_framework_v02/normalization_pass_02/normalized_feature_view_v02_pass02.csv")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/draft_ranking_model_v1_20260615")

RANKING_COLUMNS = [
    "rookie_rank",
    "position_rank",
    "player_id",
    "player_name",
    "normalized_name",
    "alias_info",
    "position",
    "school",
    "nfl_team",
    "draft_capital",
    "status",
    "draft_action",
    "warning_flags",
    "why_ranked_here",
    "star_case",
    "bust_case",
    "confidence_note",
    "manual_question",
    "ranking_component_summary",
    "league_scoring_fit_note",
    "star_upside_index",
    "bust_risk_index",
    "early_role_index",
    "long_term_value_index",
    "scoring_fit_index",
    "evidence_confidence_index",
    "positional_adjustment_index",
    "warning_penalty_index",
    "final_rookie_rank_score",
    "market_overlay_status",
    "market_rank_display_only",
    "market_delta_display_only",
    "draft_window_note_display_only",
    "export_guardrails",
]

MARKET_COLUMNS = [
    "rookie_rank",
    "player_id",
    "player_name",
    "position",
    "nwr_rank",
    "market_data_status",
    "market_rank_display_only",
    "market_delta_display_only",
    "draft_window_note_display_only",
    "market_overlay_notes",
]

PROHIBITED_PRIVATE_INPUT_TERMS = {
    "adp",
    "market",
    "projection",
    "projections",
    "ranking",
    "rankings",
    "consensus",
    "trade",
    "trade_value",
    "private_score",
}


class DraftRankingError(RuntimeError):
    """Raised when draft ranking export validation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise DraftRankingError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def normalize_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def by_player_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("player_id", ""): row for row in rows if row.get("player_id")}


def pipe_count(value: str) -> int:
    return len([part for part in (value or "").split("|") if part.strip() and part.strip().lower() != "none"])


def to_float(value: str, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def bounded(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def source_safe_value(feature: dict[str, str], field: str) -> float:
    status = feature.get(f"{field}_field_status", "")
    if any(term in status.lower() for term in ["projection", "market", "ranking", "adp"]):
        return 0.0
    return to_float(feature.get(field, ""))


def draft_capital_points(feature: dict[str, str]) -> float:
    round_no = to_float(feature.get("nfl_draft_round", ""))
    pick = to_float(feature.get("nfl_draft_pick", ""))
    if round_no <= 0:
        return 0.0
    round_points = {1: 24, 2: 18, 3: 13, 4: 8, 5: 5, 6: 3, 7: 1}.get(int(round_no), 0)
    pick_bonus = max(0.0, 8.0 - (pick / 12.0)) if pick > 0 else 0.0
    return round_points + pick_bonus


def tag_bonus(tags: str, needles: Iterable[str], points: float) -> float:
    return points if any(needle in tags for needle in needles) else 0.0


def confidence_index(value: str, evidence_summary: str) -> float:
    base = {"high": 92.0, "medium": 72.0, "low": 42.0}.get(value, 35.0)
    if "No Deep Research evidence matched" in evidence_summary:
        base -= 12.0
    if "reconciliation_repair_context:" in evidence_summary:
        base += 8.0
    return bounded(base)


def component_scores(analyzer: dict[str, str], feature: dict[str, str]) -> dict[str, float]:
    position = analyzer.get("position", "")
    tags = analyzer.get("tag_summary", "")
    warnings = analyzer.get("warnings", "")
    blockers = analyzer.get("blockers", "")
    status = analyzer.get("production_ready_status", "")
    gaps = analyzer.get("remaining_gaps", "")
    evidence = analyzer.get("evidence_summary", "")
    pick_zone = analyzer.get("pick_zone", "")

    draft_points = draft_capital_points(feature)
    target_share = source_safe_value(feature, "final_year_target_share")
    touch_share = source_safe_value(feature, "final_year_touch_share")
    rush_yards = source_safe_value(feature, "cfbd_rushing_yards")
    receiving_yards = source_safe_value(feature, "cfbd_receiving_yards")
    rushing_tds = source_safe_value(feature, "cfbd_rushing_tds")
    receiving_tds = source_safe_value(feature, "cfbd_receiving_tds")
    passing_yards = source_safe_value(feature, "cfbd_passing_yards")
    passing_tds = source_safe_value(feature, "cfbd_passing_tds")

    status_base = {
        "rankable_with_warning": 58.0,
        "manual_review_required": 38.0,
        "unavailable": 12.0,
        "blocked": 0.0,
        "ready": 72.0,
    }.get(status, 10.0)
    production_signal = min(24.0, (rush_yards / 70.0) + (receiving_yards / 80.0) + (passing_yards / 500.0))
    td_signal = min(12.0, (rushing_tds + receiving_tds) * 1.4 + passing_tds * 0.45)

    star = status_base + draft_points + production_signal + td_signal
    star += tag_bonus(tags, ["PREMIUM", "THREE_DOWN", "TRUE_ALPHA", "TARGET_COMMANDING"], 10.0)
    star += tag_bonus(tags, ["RECEIVING_BACK", "INTERMEDIATE_TARGET_EARNER", "EARLY_DOWN_WORKHORSE"], 6.0)
    if pick_zone == "5.04" and "SOURCE_LIMITED_REVIEW" in tags:
        star -= 8.0

    role = 30.0 + draft_points + min(18.0, max(target_share, touch_share) * 80.0)
    role += tag_bonus(tags, ["THREE_DOWN", "RECEIVING_BACK", "EARLY_DOWN_WORKHORSE", "TARGET_COMMANDING"], 14.0)
    role += 8.0 if feature.get("nfl_team") else 0.0

    long_term = star * 0.55 + role * 0.25 + draft_points * 0.9
    scoring_fit = 50.0
    if position == "RB":
        scoring_fit += 14.0 + tag_bonus(tags, ["GOAL_LINE", "EARLY_DOWN", "RECEIVING_BACK"], 8.0)
    elif position == "WR":
        scoring_fit += 10.0 + tag_bonus(tags, ["TARGET", "ROUTE", "INTERMEDIATE"], 8.0)
    elif position == "TE":
        scoring_fit -= 8.0
        scoring_fit += tag_bonus(tags, ["TOP_TWO_TARGET_PATH", "TARGET_COMMANDING"], 8.0)
    elif position == "QB":
        scoring_fit -= 28.0
        scoring_fit += tag_bonus(tags, ["RUSHING"], 8.0)
    if "first_down" in (warnings + gaps).lower():
        scoring_fit += 4.0

    evidence_index = confidence_index(analyzer.get("source_confidence", ""), evidence)
    positional = {"RB": 72.0, "WR": 70.0, "TE": 42.0, "QB": 24.0}.get(position, 40.0)

    warning_count = pipe_count(warnings) + pipe_count(gaps)
    warning_penalty = min(42.0, warning_count * 1.7)
    bust = 18.0 + warning_penalty
    if analyzer.get("source_confidence") == "low":
        bust += 16.0
    if status == "manual_review_required":
        bust += 22.0
    if status == "unavailable":
        bust += 45.0
    if status == "blocked":
        bust += 75.0
    if blockers and blockers.lower() != "none":
        bust += 18.0
    if position == "TE" and "TE_REPLACEABLE" in tags:
        bust += 15.0
    if position == "QB":
        bust += 22.0
    if pick_zone == "5.04" and "SOURCE_LIMITED_REVIEW" in tags:
        bust += 18.0

    return {
        "star_upside_index": bounded(star),
        "bust_risk_index": bounded(bust),
        "early_role_index": bounded(role),
        "long_term_value_index": bounded(long_term),
        "scoring_fit_index": bounded(scoring_fit),
        "evidence_confidence_index": bounded(evidence_index),
        "positional_adjustment_index": bounded(positional),
        "warning_penalty_index": bounded(warning_penalty),
    }


def final_rank_score(components: dict[str, float]) -> float:
    score = (
        components["star_upside_index"] * 0.30
        + components["early_role_index"] * 0.18
        + components["long_term_value_index"] * 0.18
        + components["scoring_fit_index"] * 0.14
        + components["evidence_confidence_index"] * 0.12
        + components["positional_adjustment_index"] * 0.08
        - components["bust_risk_index"] * 0.28
        - components["warning_penalty_index"] * 0.10
    )
    return round(score, 3)


def draft_action(row: dict[str, str], score: float) -> str:
    status = row.get("production_ready_status", "")
    if status == "blocked":
        return "do_not_draft"
    if status == "unavailable":
        return "do_not_draft_until_evidence_refresh"
    if status == "manual_review_required":
        return "manual_stop_before_pick"
    if row.get("pick_zone") == "1.04" and score >= 50:
        return "draft_candidate_with_visible_warnings"
    if row.get("pick_zone") in {"2.04", "2.08"}:
        return "round2_candidate_with_visible_warnings"
    if row.get("pick_zone") == "5.04":
        return "late_dart_or_stash_only"
    return "manual_context_only"


def build_rows(analyzer_rows: list[dict[str, str]], feature_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    features = by_player_id(feature_rows)
    scored = []
    for analyzer in analyzer_rows:
        feature = features.get(analyzer.get("player_id", ""), {})
        components = component_scores(analyzer, feature)
        score = final_rank_score(components)
        scored.append((score, analyzer, feature, components))

    scored.sort(key=lambda item: (-item[0], item[1].get("position", ""), item[1].get("player", "")))
    position_counts: Counter = Counter()
    rows = []
    for rank, (score, analyzer, feature, components) in enumerate(scored, start=1):
        position = analyzer.get("position", "")
        position_counts[position] += 1
        draft_capital = "unavailable"
        if feature.get("nfl_draft_round") or feature.get("nfl_draft_pick"):
            draft_capital = f"round={feature.get('nfl_draft_round') or 'unknown'}; pick={feature.get('nfl_draft_pick') or 'unknown'}"
        warning_flags = analyzer.get("warnings", "")
        manual_question = analyzer.get("draft_only_if", "")
        if analyzer.get("production_ready_status") == "manual_review_required":
            manual_question = analyzer.get("draft_only_if", "Tim must clear manual review before pick.")
        summary = (
            f"star={components['star_upside_index']:.1f}; bust_risk={components['bust_risk_index']:.1f}; "
            f"role={components['early_role_index']:.1f}; long_term={components['long_term_value_index']:.1f}; "
            f"fit={components['scoring_fit_index']:.1f}; evidence={components['evidence_confidence_index']:.1f}; "
            "ADP/market excluded from score"
        )
        rows.append(
            {
                "rookie_rank": str(rank),
                "position_rank": f"{position}{position_counts[position]}",
                "player_id": analyzer.get("player_id", ""),
                "player_name": analyzer.get("player", ""),
                "normalized_name": normalize_name(analyzer.get("player", "")),
                "alias_info": "Omar Cooper Jr. alias maps to Omar Cooper" if analyzer.get("player") == "Omar Cooper" else "none",
                "position": position,
                "school": analyzer.get("school", ""),
                "nfl_team": feature.get("nfl_team", ""),
                "draft_capital": draft_capital,
                "status": analyzer.get("production_ready_status", ""),
                "draft_action": draft_action(analyzer, score),
                "warning_flags": warning_flags,
                "why_ranked_here": analyzer.get("why_ranked_here", ""),
                "star_case": star_case(analyzer, feature, components),
                "bust_case": bust_case(analyzer, components),
                "confidence_note": f"source_confidence={analyzer.get('source_confidence', '')}; evidence_index={components['evidence_confidence_index']:.1f}",
                "manual_question": manual_question,
                "ranking_component_summary": summary,
                "league_scoring_fit_note": league_fit_note(position, analyzer.get("tag_summary", "")),
                **{key: f"{value:.1f}" for key, value in components.items()},
                "final_rookie_rank_score": f"{score:.3f}",
                "market_overlay_status": "schema_only_no_player_level_market_source_loaded",
                "market_rank_display_only": "",
                "market_delta_display_only": "",
                "draft_window_note_display_only": "market/ADP unavailable locally; do not infer draft price",
                "export_guardrails": "manual_use_only; local_export_only; not_production; no_app; no_private_score; no_prob_or_band",
            }
        )
    return rows


def star_case(analyzer: dict[str, str], feature: dict[str, str], components: dict[str, float]) -> str:
    tags = analyzer.get("tag_summary", "")
    pieces = []
    if components["star_upside_index"] >= 75:
        pieces.append("high star-upside index")
    if any(token in tags for token in ["THREE_DOWN", "TRUE_ALPHA", "TARGET_COMMANDING", "PREMIUM"]):
        pieces.append(f"role/archetype tags={tags}")
    if feature.get("nfl_draft_round"):
        pieces.append(f"draft capital round {feature.get('nfl_draft_round')}")
    return "; ".join(pieces) if pieces else "star case is limited by current evidence"


def bust_case(analyzer: dict[str, str], components: dict[str, float]) -> str:
    pieces = []
    if components["bust_risk_index"] >= 70:
        pieces.append("high bust-risk index")
    if analyzer.get("blockers", "none") != "none":
        pieces.append(f"blockers={analyzer.get('blockers')}")
    if analyzer.get("remaining_gaps", "none") != "none":
        pieces.append(f"gaps={analyzer.get('remaining_gaps')}")
    if analyzer.get("source_confidence") == "low":
        pieces.append("low source confidence")
    return "; ".join(pieces) if pieces else "no hard blocker; warnings still visible"


def league_fit_note(position: str, tags: str) -> str:
    if position == "QB":
        return "10-team 1QB devalues rookie QB unless rushing/job-security exception is manually cleared"
    if position == "RB":
        return "non-PPR and 0.4 first-down scoring reward stable rush/receiving first-down and goal-line paths"
    if position == "WR":
        return "non-PPR rewards target quality, first-down earning, route stability, and TD path over empty reception volume"
    if position == "TE":
        return "TEs require target-command exception; replacement-level TE tags remain heavily discounted"
    return "manual review only"


def market_overlay_rows(ranking_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "rookie_rank": row["rookie_rank"],
            "player_id": row["player_id"],
            "player_name": row["player_name"],
            "position": row["position"],
            "nwr_rank": row["rookie_rank"],
            "market_data_status": "unavailable_no_player_level_adp_or_market_source_loaded",
            "market_rank_display_only": "",
            "market_delta_display_only": "",
            "draft_window_note_display_only": "No local player-level ADP/market rank was admitted for display; do not infer price.",
            "market_overlay_notes": "ADP/market is isolated from final_rookie_rank_score and unavailable in this export.",
        }
        for row in ranking_rows
    ]


def validate_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise DraftRankingError("No ranking rows created.")
    ids = [row["player_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise DraftRankingError("Duplicate rookie IDs in ranking export.")
    missing = [row["player_id"] for row in rows if not row["player_name"] or not row["position"] or not row["status"]]
    if missing:
        raise DraftRankingError("Rows missing names, positions, or status labels: " + ", ".join(missing[:10]))
    hidden_market = [
        row["player_id"]
        for row in rows
        if any(term in row["ranking_component_summary"].lower() for term in PROHIBITED_PRIVATE_INPUT_TERMS)
        and "ADP/market excluded from score" not in row["ranking_component_summary"]
    ]
    if hidden_market:
        raise DraftRankingError("Market terms appear as private score inputs: " + ", ".join(hidden_market[:10]))
    hidden_warnings = [
        row["player_id"]
        for row in rows
        if row["status"] in {"rankable_with_warning", "manual_review_required"} and not row["warning_flags"]
    ]
    if hidden_warnings:
        raise DraftRankingError("Warning/manual rows missing visible warnings: " + ", ".join(hidden_warnings[:10]))


def write_readme(output_dir: Path, rows: list[dict[str, str]]) -> None:
    counts = Counter(row["status"] for row in rows)
    text = f"""# Rookie Draft Ranking Model v1

Status: local-only manual draft ranking export.

Rows: {len(rows)}

Status counts:

- ready: {counts.get('ready', 0)}
- rankable_with_warning: {counts.get('rankable_with_warning', 0)}
- manual_review_required: {counts.get('manual_review_required', 0)}
- unavailable: {counts.get('unavailable', 0)}
- blocked: {counts.get('blocked', 0)}

Guardrails:

- ADP/market fields are display-only and unavailable in this run.
- `final_rookie_rank_score` is an experimental rookie-only local ordering score, not a production private score.
- No production ranking, app output, probability, band, hidden sort key, or promoted artifact was created.
"""
    (output_dir / "README_ROOKIE_DRAFT_RANKING_MODEL_V1_20260615.md").write_text(text, encoding="utf-8")


def build_exports(analyzer_path: Path, features_path: Path, output_dir: Path) -> dict[str, int]:
    analyzer_rows = read_csv(analyzer_path)
    feature_rows = read_csv(features_path)
    rows = build_rows(analyzer_rows, feature_rows)
    validate_rows(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_draft_ranking_v1_20260615.csv", rows, RANKING_COLUMNS)
    for position in ["RB", "WR", "TE", "QB"]:
        write_csv(
            output_dir / f"rookie_draft_ranking_v1_{position.lower()}_20260615.csv",
            [row for row in rows if row["position"] == position],
            RANKING_COLUMNS,
        )
    write_csv(output_dir / "rookie_star_watchlist_v1_20260615.csv", [row for row in rows if to_float(row["star_upside_index"]) >= 70], RANKING_COLUMNS)
    write_csv(output_dir / "rookie_bust_risk_watchlist_v1_20260615.csv", [row for row in rows if to_float(row["bust_risk_index"]) >= 70], RANKING_COLUMNS)
    write_csv(
        output_dir / "rookie_manual_review_before_pick_v1_20260615.csv",
        [row for row in rows if row["status"] in {"manual_review_required", "unavailable", "blocked"}],
        RANKING_COLUMNS,
    )
    write_csv(output_dir / "rookie_market_overlay_v1_20260615.csv", market_overlay_rows(rows), MARKET_COLUMNS)
    write_readme(output_dir, rows)
    counts = Counter(row["status"] for row in rows)
    return {
        "ranking_rows": len(rows),
        "rankable_with_warning_rows": counts.get("rankable_with_warning", 0),
        "manual_review_required_rows": counts.get("manual_review_required", 0),
        "unavailable_rows": counts.get("unavailable", 0),
        "blocked_rows": counts.get("blocked", 0),
        "star_watchlist_rows": sum(1 for row in rows if to_float(row["star_upside_index"]) >= 70),
        "market_overlay_rows": len(rows),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build rookie-only manual draft ranking model v1.")
    parser.add_argument("--analyzer", type=Path, default=DEFAULT_ANALYZER)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.analyzer, args.features, args.output_dir)
    except DraftRankingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
