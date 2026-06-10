from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BOARD_ROWS = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/"
    "historical_rookie_tuning_board_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/model_edge/latest")

HARNESS_VERSION = "model_edge_evaluation_harness_0.1.0"
EVALUATION_LANE = "historical_rookie_replay"
OUTCOME_USE_POLICY = "outcomes_joined_after_ranking_for_review_only"

REQUIRED_BOARD_COLUMNS = (
    "Draft Year",
    "Rank",
    "Player",
    "Pos",
    "Final Score",
    "Production Score",
    "College Team Share",
    "NFL Draft Pick Signal",
    "Athletic Score",
    "Confidence Cap",
    "Evidence Available",
    "Trust Level",
    "Draft Round",
    "Overall Pick",
    "Fantasy-Relevant Replay Pool",
    "Outcome Loaded",
    "Outcome Category",
    "Outcome Maturity",
    "Broad Outcome Hit?",
    "Strict Starter Hit?",
    "Difference Maker?",
    "Formula Version",
)

HARNESS_ROW_HEADER = (
    "evaluation_lane",
    "draft_year",
    "draft_class",
    "player",
    "position",
    "draft_round",
    "overall_pick",
    "model_rank",
    "position_model_rank",
    "private_score_at_eval",
    "confidence_cap",
    "evidence_available",
    "trust_level",
    "pre_draft_profile_features",
    "outcome_label",
    "league_outcome_label",
    "hit_bust_classification",
    "outcome_maturity",
    "broad_outcome_hit",
    "strict_starter_hit",
    "difference_maker",
    "rank_bucket",
    "pick_range_bucket",
    "position_rank_bucket",
    "leakage_risk_flags",
    "feature_leakage_status",
    "outcome_use_policy",
    "data_needed",
    "allowed_use",
    "blocked_use",
    "source_path",
    "formula_version",
    "harness_version",
)

SUMMARY_HEADER = (
    "metric",
    "value",
    "notes",
    "harness_version",
)

POSITION_SUMMARY_HEADER = (
    "position",
    "rows",
    "mature_rows",
    "outcome_loaded_rows",
    "difference_makers",
    "strong_starters",
    "useful_starter_flex",
    "replacement_or_bust",
    "too_early_or_missing",
    "strict_starter_hit_rate",
    "difference_maker_rate",
    "primary_read",
    "harness_version",
)


@dataclass(frozen=True)
class ModelEdgeEvaluationHarnessResult:
    rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    position_summary_rows: tuple[dict[str, object], ...]
    source_path: str


def build_model_edge_evaluation_harness(
    board_rows_path: str | Path = DEFAULT_BOARD_ROWS,
) -> ModelEdgeEvaluationHarnessResult:
    source = Path(board_rows_path)
    source_rows = _read_rows(source)
    _require_columns(source_rows.fieldnames, REQUIRED_BOARD_COLUMNS, source)
    board_rows = list(source_rows.rows)
    position_ranks = _position_ranks(board_rows)
    rows = tuple(
        _harness_row(row, position_ranks[(row["Draft Year"], row["Pos"], row["Player"])], source)
        for row in board_rows
        if row.get("Pos") in {"QB", "RB", "WR", "TE"}
    )
    summary_rows = tuple(_summary_rows(rows, source))
    position_summary_rows = tuple(_position_summary_rows(rows))
    return ModelEdgeEvaluationHarnessResult(
        rows=rows,
        summary_rows=summary_rows,
        position_summary_rows=position_summary_rows,
        source_path=str(source),
    )


def write_model_edge_evaluation_harness_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: ModelEdgeEvaluationHarnessResult | None = None,
) -> dict[str, Path]:
    result = result or build_model_edge_evaluation_harness()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    rows_path = output / "model_edge_evaluation_harness_review_rows.csv"
    summary_path = output / "model_edge_evaluation_harness_summary.csv"
    position_path = output / "model_edge_evaluation_position_summary.csv"
    _write_csv(rows_path, HARNESS_ROW_HEADER, result.rows)
    _write_csv(summary_path, SUMMARY_HEADER, result.summary_rows)
    _write_csv(position_path, POSITION_SUMMARY_HEADER, result.position_summary_rows)
    return {"rows": rows_path, "summary": summary_path, "position_summary": position_path}


def _harness_row(
    row: dict[str, str],
    position_rank: int,
    source: Path,
) -> dict[str, object]:
    outcome = row.get("Outcome Category", "")
    league_outcome = _league_outcome_label(outcome, row.get("Outcome Maturity", ""))
    future_used = _bool(row.get("Future Stats Used In Ranking"))
    leakage_flags = _leakage_flags(row, future_used)
    return {
        "evaluation_lane": EVALUATION_LANE,
        "draft_year": row.get("Draft Year", ""),
        "draft_class": f"{row.get('Draft Year', '')}_rookies",
        "player": row.get("Player", ""),
        "position": row.get("Pos", ""),
        "draft_round": row.get("Draft Round", ""),
        "overall_pick": row.get("Overall Pick", ""),
        "model_rank": row.get("Rank", ""),
        "position_model_rank": position_rank,
        "private_score_at_eval": row.get("Final Score", ""),
        "confidence_cap": row.get("Confidence Cap", ""),
        "evidence_available": row.get("Evidence Available", ""),
        "trust_level": row.get("Trust Level", ""),
        "pre_draft_profile_features": _profile_summary(row),
        "outcome_label": outcome,
        "league_outcome_label": league_outcome,
        "hit_bust_classification": _hit_bust_classification(league_outcome),
        "outcome_maturity": row.get("Outcome Maturity", ""),
        "broad_outcome_hit": _bool(row.get("Broad Outcome Hit?")),
        "strict_starter_hit": _bool(row.get("Strict Starter Hit?")),
        "difference_maker": _bool(row.get("Difference Maker?")),
        "rank_bucket": _rank_bucket(_int(row.get("Rank"))),
        "pick_range_bucket": _pick_range_bucket(_int(row.get("Overall Pick"))),
        "position_rank_bucket": _position_rank_bucket(position_rank),
        "leakage_risk_flags": "|".join(leakage_flags),
        "feature_leakage_status": "blocked" if future_used else "no_future_outcome_inputs_detected",
        "outcome_use_policy": OUTCOME_USE_POLICY,
        "data_needed": _data_needed(row, league_outcome, leakage_flags),
        "allowed_use": (
            "model_evaluation_replay|hit_bust_pattern_research|"
            "shadow_formula_planning|human_review"
        ),
        "blocked_use": (
            "active_private_score_input|active_rank_input|draft_recommendation|"
            "market_targeting|decision_board_action"
        ),
        "source_path": str(source),
        "formula_version": row.get("Formula Version", ""),
        "harness_version": HARNESS_VERSION,
    }


def _position_ranks(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], int]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("Draft Year", ""), row.get("Pos", ""))].append(row)
    output: dict[tuple[str, str, str], int] = {}
    for key, group_rows in grouped.items():
        ranked = sorted(
            group_rows,
            key=lambda item: (_int(item.get("Rank")) or 999, item.get("Player", "")),
        )
        for rank, item in enumerate(ranked, start=1):
            output[(key[0], key[1], item.get("Player", ""))] = rank
    return output


def _league_outcome_label(outcome: str, maturity: str) -> str:
    label = outcome.lower()
    if not label or label == "not_loaded":
        return "outcome_missing"
    if "rookie_year_only" in maturity or label.startswith("too_early_"):
        return "Too early to call"
    if "partial_two_year_window" in maturity or label.startswith("partial_"):
        return "Too early to call"
    if "difference_maker" in label:
        return "Difference-maker"
    if "starter" in label:
        return "Strong starter"
    if "usable" in label or "hit" in label:
        return "Useful starter/flex"
    if "miss" in label or "bust" in label:
        return "Bust"
    return "Injury/uncertain"


def _hit_bust_classification(league_outcome: str) -> str:
    if league_outcome == "Difference-maker":
        return "high_end_hit"
    if league_outcome == "Strong starter":
        return "starter_hit"
    if league_outcome == "Useful starter/flex":
        return "usable_hit"
    if league_outcome in {"Bust", "Replacement-level"}:
        return "bust_or_replacement"
    if league_outcome == "Too early to call":
        return "too_early"
    return "uncertain"


def _profile_summary(row: dict[str, str]) -> str:
    pieces = (
        ("production", row.get("Production Score", "")),
        ("team_share", row.get("College Team Share", "")),
        ("draft_capital", row.get("NFL Draft Pick Signal", "")),
        ("athletic", row.get("Athletic Score", "")),
        ("confidence_cap", row.get("Confidence Cap", "")),
        ("evidence_available", row.get("Evidence Available", "")),
    )
    return "|".join(f"{name}={value or '-'}" for name, value in pieces)


def _leakage_flags(row: dict[str, str], future_used: bool) -> tuple[str, ...]:
    flags = []
    if future_used:
        flags.append("future_outcome_flagged_as_ranking_input")
    else:
        flags.append("no_future_stats_used_in_rank")
    flags.append("outcome_columns_present_for_after_the_fact_review")
    if row.get("Outcome Loaded", "").lower() in {"true", "1", "yes"}:
        flags.append("outcome_joined_after_rank")
    return tuple(flags)


def _data_needed(row: dict[str, str], league_outcome: str, leakage_flags: tuple[str, ...]) -> str:
    needs: list[str] = []
    if row.get("Outcome Loaded", "").lower() not in {"true", "1", "yes"}:
        needs.append("Need loaded league-scoring outcome label.")
    if league_outcome == "Too early to call":
        needs.append("Need mature 3-year outcome window before calibration.")
    if _float(row.get("Evidence Available")) < 0.7:
        needs.append("Need fuller pre-draft evidence before formula tuning.")
    if "future_outcome_flagged_as_ranking_input" in leakage_flags:
        needs.append("Block row until leakage is repaired.")
    return " | ".join(needs)


def _summary_rows(
    rows: tuple[dict[str, object], ...],
    source: Path,
) -> list[dict[str, object]]:
    years = sorted({str(row["draft_year"]) for row in rows})
    outcome_loaded = [row for row in rows if row["league_outcome_label"] != "outcome_missing"]
    mature = [row for row in rows if row["outcome_maturity"] == "three_year_window_available"]
    labels = Counter(str(row["league_outcome_label"]) for row in rows)
    leakage_blocked = [
        row for row in rows if str(row["feature_leakage_status"]) == "blocked"
    ]
    summary = [
        (
            "source_path",
            str(source),
            "Historical rookie tuning board normalized into evaluation rows.",
        ),
        ("rows", len(rows), "QB/RB/WR/TE rookie replay rows."),
        ("draft_years", "|".join(years), "Historical classes available in the harness."),
        ("mature_three_year_rows", len(mature), "Rows safe for mature outcome calibration review."),
        ("outcome_loaded_rows", len(outcome_loaded), "Rows with after-the-fact outcome labels."),
        (
            "future_stats_used_in_ranking_rows",
            len(leakage_blocked),
            "Must be zero before trusting replay.",
        ),
        (
            "active_scores_changed",
            False,
            "Harness is read-only and does not alter active NWR scores.",
        ),
    ]
    summary.extend(
        (f"league_outcome_label_{label}", count, "League-specific outcome label count.")
        for label, count in sorted(labels.items())
    )
    return [
        {
            "metric": metric,
            "value": value,
            "notes": notes,
            "harness_version": HARNESS_VERSION,
        }
        for metric, value, notes in summary
    ]


def _position_summary_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for position in sorted({str(row["position"]) for row in rows}):
        position_rows = [row for row in rows if row["position"] == position]
        mature = [
            row
            for row in position_rows
            if row["outcome_maturity"] == "three_year_window_available"
        ]
        strict_hits = [row for row in mature if row["strict_starter_hit"]]
        difference = [row for row in mature if row["difference_maker"]]
        counts = Counter(str(row["league_outcome_label"]) for row in position_rows)
        output.append(
            {
                "position": position,
                "rows": len(position_rows),
                "mature_rows": len(mature),
                "outcome_loaded_rows": sum(
                    1 for row in position_rows if row["league_outcome_label"] != "outcome_missing"
                ),
                "difference_makers": counts["Difference-maker"],
                "strong_starters": counts["Strong starter"],
                "useful_starter_flex": counts["Useful starter/flex"],
                "replacement_or_bust": counts["Bust"] + counts["Replacement-level"],
                "too_early_or_missing": counts["Too early to call"] + counts["outcome_missing"],
                "strict_starter_hit_rate": _rate(len(strict_hits), len(mature)),
                "difference_maker_rate": _rate(len(difference), len(mature)),
                "primary_read": _position_primary_read(position),
                "harness_version": HARNESS_VERSION,
            }
        )
    return output


def _position_primary_read(position: str) -> str:
    if position == "QB":
        return "Use for 1QB over/under-promotion review; do not tune to public QB ranks."
    if position == "TE":
        return "Use for no-TE-premium exception/cap review."
    if position == "RB":
        return "Use to separate short-window upside from fragile false positives."
    if position == "WR":
        return "Use to protect multi-year target-earning profiles and identify traps."
    return "Position-specific review."


def _rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "rank_missing"
    if rank <= 5:
        return "top_5"
    if rank <= 10:
        return "top_10"
    if rank <= 20:
        return "top_20"
    if rank <= 40:
        return "top_40"
    return "outside_top_40"


def _position_rank_bucket(rank: int) -> str:
    if rank <= 3:
        return "position_top_3"
    if rank <= 5:
        return "position_top_5"
    if rank <= 10:
        return "position_top_10"
    return "position_outside_top_10"


def _pick_range_bucket(pick: int | None) -> str:
    if pick is None:
        return "pick_missing"
    if pick <= 32:
        return "round_1"
    if pick <= 64:
        return "round_2"
    if pick <= 96:
        return "round_3"
    return "day_3_or_later"


def _rate(numerator: int, denominator: int) -> float | str:
    if denominator <= 0:
        return ""
    return round(numerator / denominator, 3)


@dataclass(frozen=True)
class _Rows:
    fieldnames: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _read_rows(path: Path) -> _Rows:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return _Rows(
            fieldnames=tuple(reader.fieldnames or ()),
            rows=tuple(reader),
        )


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})


def _require_columns(fieldnames: tuple[str, ...], required: tuple[str, ...], path: Path) -> None:
    missing = [column for column in required if column not in fieldnames]
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _float(value: object) -> float:
    try:
        text = str(value).strip()
        if not text:
            return 0.0
        return float(text)
    except (TypeError, ValueError):
        return 0.0
