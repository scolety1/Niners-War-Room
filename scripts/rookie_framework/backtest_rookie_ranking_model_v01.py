"""Integrate rookie historical labels and run frozen baseline backtest v1.

This is local-only evaluation code. Outcome labels are used only as evaluation
targets and must never be merged into rookie-time features, production
rankings, private scores, probabilities, bands, hidden sort keys, or app
outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


DEFAULT_HISTORICAL = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/"
    "historical_rookie_backtest_feature_matrix.csv"
)
DEFAULT_LABELS = Path(
    "local_exports/rookie_framework/historical_outcome_labels_v1_20260615/"
    "rookie_historical_outcome_labels_v1_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/backtest_label_integration_tuning_v1_20260615")
LEGACY_OUTPUT_DIR = Path("local_exports/rookie_framework/historical_backtest_v1_20260615")

BASELINE_WEIGHTS = {
    "star_upside_index": 0.30,
    "early_role_index": 0.18,
    "long_term_value_index": 0.18,
    "scoring_fit_index": 0.14,
    "evidence_confidence_index": 0.12,
    "positional_adjustment_index": 0.08,
    "bust_risk_index": -0.28,
    "warning_penalty_index": -0.10,
}

BUCKETS = [6, 12, 24, 36]
COMPLETE_YEARS = {"2021", "2022", "2023"}
PARTIAL_YEARS = {"2024", "2025"}
MARKET_TERMS = ("adp", "market", "projection", "consensus", "trade", "rank")
LABEL_PREFIXES = ("label_", "eval_")

INVENTORY_COLUMNS = [
    "source_path",
    "exists",
    "rows",
    "draft_years",
    "positions",
    "feature_columns",
    "label_columns",
    "market_context_present",
    "leakage_guardrail",
    "backtest_runnable",
    "reason",
]

JOIN_AUDIT_COLUMNS = [
    "audit_scope",
    "draft_year",
    "rows_attempted",
    "rows_joined",
    "rows_unjoined",
    "duplicate_feature_keys",
    "duplicate_label_keys",
    "missing_identity_rows",
    "complete_window_rows",
    "partial_window_rows",
    "label_leakage_columns",
    "probability_band_leakage_columns",
    "market_context_rows",
    "join_status",
    "notes",
]

SCORED_COLUMNS = [
    "historical_prospect_key",
    "draft_year",
    "baseline_rank",
    "baseline_position_rank",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "warning_flags",
    "warning_bucket",
    "draft_round",
    "draft_pick",
    "star_upside_index",
    "bust_risk_index",
    "early_role_index",
    "long_term_value_index",
    "scoring_fit_index",
    "evidence_confidence_index",
    "positional_adjustment_index",
    "warning_penalty_index",
    "baseline_frozen_rank_score",
    "label_quality_status",
    "eval_backtest_ready_flag",
    "label_first3_total_points",
    "label_first3_best_pos_rank",
    "label_first3_starter_seasons",
    "label_star_flag",
    "label_bust_flag",
    "label_useful_flag",
    "market_overlay_status",
    "guardrails",
]

METRIC_COLUMNS = [
    "metric_scope",
    "draft_year",
    "bucket",
    "rows",
    "stars_total",
    "stars_captured",
    "star_capture_rate",
    "bust_count",
    "bust_rate",
    "avg_label_first3_total_points",
    "avg_rank_score",
    "notes",
]

MISS_COLUMNS = [
    "miss_type",
    "draft_year",
    "baseline_rank",
    "prospect_name",
    "position",
    "baseline_frozen_rank_score",
    "label_first3_total_points",
    "label_first3_best_pos_rank",
    "label_star_flag",
    "label_bust_flag",
    "warning_flags",
    "notes",
]

CALIBRATION_COLUMNS = [
    "scope_type",
    "scope_value",
    "rows",
    "avg_rank_score",
    "avg_label_first3_total_points",
    "star_count",
    "star_rate",
    "bust_count",
    "bust_rate",
    "notes",
]

FAILURE_COLUMNS = ["failure_type", "source_path", "details", "safe_next_step"]
LEGACY_RESULT_COLUMNS = ["backtest_status", "draft_year", "rows_evaluated", "star_capture_top_12", "bust_avoidance_top_12", "notes"]


class RookieBacktestError(RuntimeError):
    """Raised when historical backtest integration fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
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


def to_float(value: str, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def bounded(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def parse_json(value: str) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def nested_dicts(value: object) -> Iterable[dict]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nested_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_dicts(child)


def first_numeric(*values: object) -> float:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.strip():
            try:
                return float(value)
            except ValueError:
                continue
    return 0.0


def evidence_values(feature: dict[str, str]) -> dict[str, float]:
    factual = parse_json(feature.get("factual_evidence_json", ""))
    derived = parse_json(feature.get("derived_evidence_json", ""))
    prior = parse_json(feature.get("prospect_prior_evidence_json", ""))
    values = {
        "passing_yards": 0.0,
        "passing_tds": 0.0,
        "rushing_yards": 0.0,
        "rushing_tds": 0.0,
        "receiving_yards": 0.0,
        "receiving_tds": 0.0,
        "receptions": 0.0,
        "targets": 0.0,
        "games": 0.0,
        "target_share": 0.0,
        "touch_share": 0.0,
        "draft_round": to_float(feature.get("draft_round", "")),
        "draft_pick": to_float(feature.get("draft_pick", "")),
    }
    for item in nested_dicts(factual):
        values["passing_yards"] = max(values["passing_yards"], first_numeric(item.get("passing_yards")))
        values["passing_tds"] = max(values["passing_tds"], first_numeric(item.get("passing_tds")))
        values["rushing_yards"] = max(values["rushing_yards"], first_numeric(item.get("rushing_yards")))
        values["rushing_tds"] = max(values["rushing_tds"], first_numeric(item.get("rushing_tds")))
        values["receiving_yards"] = max(values["receiving_yards"], first_numeric(item.get("receiving_yards")))
        values["receiving_tds"] = max(values["receiving_tds"], first_numeric(item.get("receiving_tds")))
        values["receptions"] = max(values["receptions"], first_numeric(item.get("receptions")))
        values["targets"] = max(values["targets"], first_numeric(item.get("targets")))
        values["games"] = max(values["games"], first_numeric(item.get("games")))
    for item in nested_dicts(derived):
        values["target_share"] = max(values["target_share"], first_numeric(item.get("target_share"), item.get("target_share_pct")))
        values["touch_share"] = max(values["touch_share"], first_numeric(item.get("touch_share"), item.get("touch_share_pct")))
    for item in nested_dicts(prior):
        values["draft_round"] = values["draft_round"] or first_numeric(item.get("draft_round"))
        values["draft_pick"] = values["draft_pick"] or first_numeric(item.get("draft_pick"))
    if values["target_share"] > 1.0:
        values["target_share"] /= 100.0
    if values["touch_share"] > 1.0:
        values["touch_share"] /= 100.0
    return values


def pipe_count(value: str) -> int:
    return len([part for part in (value or "").split("|") if part.strip() and part.strip().lower() != "none"])


def draft_capital_points(round_no: float, pick: float) -> float:
    if round_no <= 0:
        return 0.0
    round_points = {1: 24, 2: 18, 3: 13, 4: 8, 5: 5, 6: 3, 7: 1}.get(int(round_no), 0)
    pick_bonus = max(0.0, 8.0 - (pick / 12.0)) if pick > 0 else 0.0
    return round_points + pick_bonus


def component_scores(feature: dict[str, str]) -> dict[str, float]:
    position = feature.get("position", "")
    warning_flags = feature.get("warning_flags", "")
    values = evidence_values(feature)
    draft_points = draft_capital_points(values["draft_round"], values["draft_pick"])
    production_signal = min(
        26.0,
        values["rushing_yards"] / 75.0
        + values["receiving_yards"] / 85.0
        + values["passing_yards"] / 520.0,
    )
    td_signal = min(14.0, (values["rushing_tds"] + values["receiving_tds"]) * 1.25 + values["passing_tds"] * 0.42)
    target_touch_signal = min(18.0, max(values["target_share"], values["touch_share"]) * 90.0)
    if not target_touch_signal and values["games"] > 0:
        target_touch_signal = min(14.0, (values["targets"] + values["receptions"]) / max(values["games"], 1.0) * 0.85)

    status_base = 44.0 if feature.get("excluded_reason") else 58.0
    star = status_base + draft_points + production_signal + td_signal + target_touch_signal * 0.35
    role = 30.0 + draft_points + target_touch_signal + min(14.0, (values["rushing_yards"] + values["receiving_yards"]) / 150.0)
    long_term = star * 0.55 + role * 0.25 + draft_points * 0.9
    scoring_fit = 50.0
    if position == "RB":
        scoring_fit += 14.0 + min(10.0, values["rushing_yards"] / 140.0)
    elif position == "WR":
        scoring_fit += 10.0 + min(10.0, values["receiving_yards"] / 140.0)
    elif position == "TE":
        scoring_fit -= 8.0
        scoring_fit += min(8.0, values["receiving_yards"] / 130.0)
    elif position == "QB":
        scoring_fit -= 28.0
        scoring_fit += min(8.0, values["rushing_yards"] / 80.0)

    source_status = parse_json(feature.get("source_status_json", ""))
    present_sources = sum(1 for value in source_status.values() if value in {"present", "not_applicable"})
    evidence_confidence = 42.0 + min(42.0, present_sources * 8.0)
    if feature.get("identity_status") == "draft_result_canonical":
        evidence_confidence += 10.0
    if feature.get("excluded_reason"):
        evidence_confidence -= 16.0

    positional = {"RB": 72.0, "WR": 70.0, "TE": 42.0, "QB": 24.0}.get(position, 40.0)
    warning_penalty = min(42.0, pipe_count(warning_flags) * 4.0)
    bust = 18.0 + warning_penalty
    if feature.get("excluded_reason"):
        bust += 34.0
    if position == "TE":
        bust += 10.0
    if position == "QB":
        bust += 22.0
    if evidence_confidence < 58.0:
        bust += 12.0
    if draft_points < 6.0:
        bust += 14.0

    return {
        "star_upside_index": bounded(star),
        "bust_risk_index": bounded(bust),
        "early_role_index": bounded(role),
        "long_term_value_index": bounded(long_term),
        "scoring_fit_index": bounded(scoring_fit),
        "evidence_confidence_index": bounded(evidence_confidence),
        "positional_adjustment_index": bounded(positional),
        "warning_penalty_index": bounded(warning_penalty),
    }


def score_with_weights(components: dict[str, float], weights: dict[str, float]) -> float:
    return round(sum(components[key] * weight for key, weight in weights.items()), 3)


def duplicate_count(rows: list[dict[str, str]], key: str) -> int:
    values = [row.get(key, "") for row in rows if row.get(key)]
    return len(values) - len(set(values))


def leakage_columns(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    if not rows:
        return [], []
    names = list(rows[0].keys())
    label_leaks = [name for name in names if name.startswith(LABEL_PREFIXES)]
    prob_band = [name for name in names if "probability" in name.lower() or name.lower().endswith("_band") or " band" in name.lower()]
    return label_leaks, prob_band


def market_context_rows(rows: list[dict[str, str]]) -> int:
    count = 0
    for row in rows:
        raw = row.get("market_context_fields_json", "")
        if raw and raw.strip() not in {"{}", "null", ""}:
            count += 1
    return count


def join_rows(feature_rows: list[dict[str, str]], label_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    labels = {row["historical_prospect_key"]: row for row in label_rows if row.get("historical_prospect_key")}
    joined = []
    unjoined = []
    for feature in feature_rows:
        key = feature.get("historical_prospect_key", "")
        label = labels.get(key)
        if not label:
            unjoined.append(feature)
            continue
        merged = dict(feature)
        for name, value in label.items():
            if name not in {"prospect_name", "normalized_player_name", "position", "college", "nfl_team"}:
                merged[name] = value
        joined.append(merged)
    return joined, unjoined


def build_join_audit(feature_rows: list[dict[str, str]], label_rows: list[dict[str, str]], joined: list[dict[str, str]], unjoined: list[dict[str, str]]) -> list[dict[str, str]]:
    label_leaks, prob_band = leakage_columns(feature_rows)
    output = []
    for year in ["overall", "2021", "2022", "2023", "2024", "2025"]:
        scoped_features = feature_rows if year == "overall" else [row for row in feature_rows if row.get("draft_year") == year]
        scoped_labels = label_rows if year == "overall" else [row for row in label_rows if row.get("rookie_class_year") == year]
        scoped_joined = joined if year == "overall" else [row for row in joined if row.get("draft_year") == year]
        scoped_unjoined = unjoined if year == "overall" else [row for row in unjoined if row.get("draft_year") == year]
        complete = [row for row in scoped_joined if row.get("eval_backtest_ready_flag") == "yes"]
        partial = [row for row in scoped_joined if row.get("eval_backtest_ready_flag") == "partial"]
        duplicates = duplicate_count(scoped_features, "historical_prospect_key")
        label_duplicates = duplicate_count(scoped_labels, "historical_prospect_key")
        missing_identity = sum(1 for row in scoped_features if not row.get("prospect_name") or not row.get("position") or not row.get("draft_year"))
        status = "GREEN" if not scoped_unjoined and not duplicates and not label_duplicates and not missing_identity and not label_leaks and not prob_band else "RED"
        if year in PARTIAL_YEARS and status == "GREEN":
            status = "YELLOW_PARTIAL_LABELS"
        output.append(
            {
                "audit_scope": "overall" if year == "overall" else "year",
                "draft_year": year,
                "rows_attempted": str(len(scoped_features)),
                "rows_joined": str(len(scoped_joined)),
                "rows_unjoined": str(len(scoped_unjoined)),
                "duplicate_feature_keys": str(duplicates),
                "duplicate_label_keys": str(label_duplicates),
                "missing_identity_rows": str(missing_identity),
                "complete_window_rows": str(len(complete)),
                "partial_window_rows": str(len(partial)),
                "label_leakage_columns": "|".join(label_leaks),
                "probability_band_leakage_columns": "|".join(prob_band),
                "market_context_rows": str(market_context_rows(scoped_features)),
                "join_status": status,
                "notes": "historical_prospect_key join; market context display-only/not used in score",
            }
        )
    return output


def warning_bucket(row: dict[str, str]) -> str:
    count = pipe_count(row.get("warning_flags", ""))
    if count == 0:
        return "none"
    if count <= 2:
        return "low"
    return "heavy"


def score_rows(rows: list[dict[str, str]], weights: dict[str, float] | None = None) -> list[dict[str, str]]:
    weights = weights or BASELINE_WEIGHTS
    scoped = [row for row in rows if row.get("draft_year") in COMPLETE_YEARS and row.get("eval_backtest_ready_flag") == "yes"]
    scored = []
    for row in scoped:
        components = component_scores(row)
        score = score_with_weights(components, weights)
        scored.append((score, row, components))
    scored.sort(key=lambda item: (-item[0], to_float(item[1].get("draft_pick", ""), 999), item[1].get("prospect_name", "")))

    position_counts: Counter[str] = Counter()
    output = []
    for rank, (score, row, components) in enumerate(scored, start=1):
        position = row.get("position", "")
        position_counts[position] += 1
        output.append(
            {
                "historical_prospect_key": row.get("historical_prospect_key", ""),
                "draft_year": row.get("draft_year", ""),
                "baseline_rank": str(rank),
                "baseline_position_rank": f"{position}{position_counts[position]}",
                "prospect_name": row.get("prospect_name", ""),
                "normalized_player_name": row.get("normalized_player_name", ""),
                "position": position,
                "college": row.get("college", ""),
                "nfl_team": row.get("nfl_team", ""),
                "warning_flags": row.get("warning_flags", ""),
                "warning_bucket": warning_bucket(row),
                "draft_round": row.get("draft_round", ""),
                "draft_pick": row.get("draft_pick", ""),
                **{key: f"{value:.1f}" for key, value in components.items()},
                "baseline_frozen_rank_score": f"{score:.3f}",
                "label_quality_status": row.get("label_quality_status", ""),
                "eval_backtest_ready_flag": row.get("eval_backtest_ready_flag", ""),
                "label_first3_total_points": row.get("label_first3_total_points", ""),
                "label_first3_best_pos_rank": row.get("label_first3_best_pos_rank", ""),
                "label_first3_starter_seasons": row.get("label_first3_starter_seasons", ""),
                "label_star_flag": row.get("label_star_flag", ""),
                "label_bust_flag": row.get("label_bust_flag", ""),
                "label_useful_flag": row.get("label_useful_flag", ""),
                "market_overlay_status": "display_only_not_used; no admitted player-level market source",
                "guardrails": "baseline_backtest_only; no_production; no_app; no_probability; no_band; no_hidden_sort_key",
            }
        )
    return output


def avg(values: list[float]) -> str:
    return f"{(sum(values) / len(values)):.3f}" if values else ""


def bucket_metrics(scored_rows: list[dict[str, str]], scope: str, year: str = "overall") -> list[dict[str, str]]:
    rows = scored_rows if year == "overall" else [row for row in scored_rows if row.get("draft_year") == year]
    if year != "overall":
        rows = sorted(
            rows,
            key=lambda row: (-to_float(row.get("baseline_frozen_rank_score", "")), to_float(row.get("draft_pick", ""), 999), row.get("prospect_name", "")),
        )
        for index, row in enumerate(rows, start=1):
            row = dict(row)
            row["class_rank"] = str(index)
            rows[index - 1] = row
    stars_total = sum(1 for row in rows if row.get("label_star_flag") == "1")
    output = []
    for bucket in BUCKETS:
        rank_field = "baseline_rank" if year == "overall" else "class_rank"
        top = [row for row in rows if int(row.get(rank_field, "999999")) <= bucket]
        stars = sum(1 for row in top if row.get("label_star_flag") == "1")
        busts = sum(1 for row in top if row.get("label_bust_flag") == "1")
        output.append(
            {
                "metric_scope": scope,
                "draft_year": year,
                "bucket": f"top_{bucket}",
                "rows": str(len(top)),
                "stars_total": str(stars_total),
                "stars_captured": str(stars),
                "star_capture_rate": avg([stars / stars_total]) if stars_total else "",
                "bust_count": str(busts),
                "bust_rate": avg([busts / len(top)]) if top else "",
                "avg_label_first3_total_points": avg([to_float(row.get("label_first3_total_points", "")) for row in top]),
                "avg_rank_score": avg([to_float(row.get("baseline_frozen_rank_score", "")) for row in top]),
                "notes": "frozen baseline; complete-window rows only",
            }
        )
    return output


def rank_bucket(value: int) -> str:
    if value <= 6:
        return "top_6"
    if value <= 12:
        return "top_12"
    if value <= 24:
        return "top_24"
    if value <= 36:
        return "top_36"
    return "outside_top_36"


def aggregate_metrics(scored_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    metrics = bucket_metrics(scored_rows, "overall", "overall")
    for year in sorted({row["draft_year"] for row in scored_rows}):
        metrics.extend(bucket_metrics(scored_rows, "year", year))
    by_rank_bucket: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in scored_rows:
        by_rank_bucket[rank_bucket(int(row["baseline_rank"]))].append(row)
    for bucket, rows in sorted(by_rank_bucket.items()):
        metrics.append(
            {
                "metric_scope": "rank_bucket",
                "draft_year": "overall",
                "bucket": bucket,
                "rows": str(len(rows)),
                "stars_total": str(sum(1 for row in scored_rows if row.get("label_star_flag") == "1")),
                "stars_captured": str(sum(1 for row in rows if row.get("label_star_flag") == "1")),
                "star_capture_rate": "",
                "bust_count": str(sum(1 for row in rows if row.get("label_bust_flag") == "1")),
                "bust_rate": avg([sum(1 for row in rows if row.get("label_bust_flag") == "1") / len(rows)]) if rows else "",
                "avg_label_first3_total_points": avg([to_float(row.get("label_first3_total_points", "")) for row in rows]),
                "avg_rank_score": avg([to_float(row.get("baseline_frozen_rank_score", "")) for row in rows]),
                "notes": "rank bucket outcome gradient",
            }
        )
    high_busts = [
        {
            "miss_type": "high_ranked_bust",
            "draft_year": row["draft_year"],
            "baseline_rank": row["baseline_rank"],
            "prospect_name": row["prospect_name"],
            "position": row["position"],
            "baseline_frozen_rank_score": row["baseline_frozen_rank_score"],
            "label_first3_total_points": row["label_first3_total_points"],
            "label_first3_best_pos_rank": row["label_first3_best_pos_rank"],
            "label_star_flag": row["label_star_flag"],
            "label_bust_flag": row["label_bust_flag"],
            "warning_flags": row["warning_flags"],
            "notes": "top-36 baseline player with bust label",
        }
        for row in scored_rows
        if int(row["baseline_rank"]) <= 36 and row["label_bust_flag"] == "1"
    ]
    low_stars = [
        {
            "miss_type": "low_ranked_star",
            "draft_year": row["draft_year"],
            "baseline_rank": row["baseline_rank"],
            "prospect_name": row["prospect_name"],
            "position": row["position"],
            "baseline_frozen_rank_score": row["baseline_frozen_rank_score"],
            "label_first3_total_points": row["label_first3_total_points"],
            "label_first3_best_pos_rank": row["label_first3_best_pos_rank"],
            "label_star_flag": row["label_star_flag"],
            "label_bust_flag": row["label_bust_flag"],
            "warning_flags": row["warning_flags"],
            "notes": "star outside top-36 baseline",
        }
        for row in scored_rows
        if int(row["baseline_rank"]) > 36 and row["label_star_flag"] == "1"
    ]
    misses = sorted(high_busts, key=lambda row: int(row["baseline_rank"])) + sorted(low_stars, key=lambda row: int(row["baseline_rank"]))
    warning = calibration_rows(scored_rows, "warning_bucket")
    position = calibration_rows(scored_rows, "position")
    return metrics, misses, warning, position


def calibration_rows(rows: list[dict[str, str]], field: str) -> list[dict[str, str]]:
    output = []
    by_value: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_value[row.get(field, "") or "missing"].append(row)
    for value, scoped in sorted(by_value.items()):
        stars = sum(1 for row in scoped if row.get("label_star_flag") == "1")
        busts = sum(1 for row in scoped if row.get("label_bust_flag") == "1")
        output.append(
            {
                "scope_type": field,
                "scope_value": value,
                "rows": str(len(scoped)),
                "avg_rank_score": avg([to_float(row.get("baseline_frozen_rank_score", "")) for row in scoped]),
                "avg_label_first3_total_points": avg([to_float(row.get("label_first3_total_points", "")) for row in scoped]),
                "star_count": str(stars),
                "star_rate": avg([stars / len(scoped)]) if scoped else "",
                "bust_count": str(busts),
                "bust_rate": avg([busts / len(scoped)]) if scoped else "",
                "notes": "complete-window rows only",
            }
        )
    return output


def build_inventory(feature_rows: list[dict[str, str]], label_rows: list[dict[str, str]], historical_path: Path) -> list[dict[str, str]]:
    years = sorted({row.get("draft_year", "") for row in feature_rows if row.get("draft_year")})
    positions = sorted({row.get("position", "") for row in feature_rows if row.get("position")})
    labels = [name for name in label_rows[0].keys() if name.startswith("label_")] if label_rows else []
    return [
        {
            "source_path": str(historical_path),
            "exists": "yes" if feature_rows else "no",
            "rows": str(len(feature_rows)),
            "draft_years": "|".join(years),
            "positions": "|".join(positions),
            "feature_columns": str(len(feature_rows[0])) if feature_rows else "0",
            "label_columns": "|".join(labels),
            "market_context_present": "yes" if market_context_rows(feature_rows) else "no",
            "leakage_guardrail": "labels joined as eval targets only; market display-only/not used",
            "backtest_runnable": "yes" if feature_rows and label_rows else "no",
            "reason": "label package joined by historical_prospect_key" if feature_rows and label_rows else "missing feature or label rows",
        }
    ]


def write_readme(output_dir: Path, counts: dict[str, int], join_status: str) -> None:
    text = f"""# Rookie Backtest Label Integration + Tuning v1

Status: local-only baseline backtest package.

- Join status: {join_status}
- Historical feature rows: {counts.get('historical_rows', 0)}
- Historical label rows: {counts.get('label_rows', 0)}
- Joined rows: {counts.get('joined_rows', 0)}
- Complete-window baseline rows: {counts.get('baseline_rows', 0)}
- Partial rows held out: {counts.get('partial_rows', 0)}

Outcome labels are evaluation targets only. This package does not create
production rankings, private scores, probabilities, bands, hidden sort keys, app
outputs, Outcome HQ files, or promoted artifacts.
"""
    (output_dir / "README_ROOKIE_BACKTEST_LABEL_INTEGRATION_AND_TUNING_V1_20260615.md").write_text(text, encoding="utf-8")


def write_legacy_outputs(legacy_dir: Path, inventory: list[dict[str, str]], metrics: list[dict[str, str]], failures: list[dict[str, str]]) -> None:
    result_rows = []
    for year in ["2021", "2022", "2023"]:
        top12 = next((row for row in metrics if row["draft_year"] == year and row["bucket"] == "top_12"), {})
        if top12:
            result_rows.append(
                {
                    "backtest_status": "label_integrated_baseline",
                    "draft_year": year,
                    "rows_evaluated": top12.get("rows", ""),
                    "star_capture_top_12": top12.get("star_capture_rate", ""),
                    "bust_avoidance_top_12": str(round(1 - to_float(top12.get("bust_rate", "0")), 3)),
                    "notes": "complete-window labels consumed by v1 integration",
                }
            )
    write_csv(legacy_dir / "rookie_historical_backtest_inventory_20260615.csv", inventory, INVENTORY_COLUMNS)
    write_csv(legacy_dir / "rookie_historical_backtest_results_v1_20260615.csv", result_rows, LEGACY_RESULT_COLUMNS)
    write_csv(legacy_dir / "rookie_historical_backtest_metrics_v1_20260615.csv", metrics, METRIC_COLUMNS)
    write_csv(legacy_dir / "rookie_historical_backtest_failures_v1_20260615.csv", failures, FAILURE_COLUMNS)


def validate_join(join_audit: list[dict[str, str]], scored_rows: list[dict[str, str]]) -> str:
    overall = next(row for row in join_audit if row["draft_year"] == "overall")
    if overall["join_status"] == "RED":
        return "RED"
    complete_rows = [row for row in join_audit if row["draft_year"] in COMPLETE_YEARS]
    if any(row["join_status"] == "RED" for row in complete_rows):
        return "RED"
    if not scored_rows:
        return "RED"
    return "GREEN"


def build_exports(historical_path: Path, labels_path: Path, output_dir: Path, legacy_output_dir: Path = LEGACY_OUTPUT_DIR) -> dict[str, int]:
    feature_rows = read_csv(historical_path)
    label_rows = read_csv(labels_path)
    if not feature_rows:
        raise RookieBacktestError(f"Missing historical feature rows: {historical_path}")
    if not label_rows:
        raise RookieBacktestError(f"Missing historical label rows: {labels_path}")

    joined, unjoined = join_rows(feature_rows, label_rows)
    join_audit = build_join_audit(feature_rows, label_rows, joined, unjoined)
    scored_rows = score_rows(joined)
    metrics, misses, warning, position = aggregate_metrics(scored_rows)
    inventory = build_inventory(feature_rows, label_rows, historical_path)
    join_status = validate_join(join_audit, scored_rows)
    failures = []
    if join_status == "RED":
        failures.append(
            {
                "failure_type": "label_join_not_usable",
                "source_path": str(labels_path),
                "details": "Join audit failed or no complete-window baseline rows were available.",
                "safe_next_step": "repair label/feature identity join before tuning",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_backtest_join_audit_20260615.csv", join_audit, JOIN_AUDIT_COLUMNS)
    write_csv(output_dir / "rookie_baseline_scored_rows_20260615.csv", scored_rows, SCORED_COLUMNS)
    write_csv(output_dir / "rookie_baseline_backtest_metrics_20260615.csv", metrics, METRIC_COLUMNS)
    write_csv(output_dir / "rookie_baseline_top_misses_20260615.csv", misses, MISS_COLUMNS)
    write_csv(output_dir / "rookie_warning_calibration_20260615.csv", warning, CALIBRATION_COLUMNS)
    write_csv(output_dir / "rookie_position_calibration_20260615.csv", position, CALIBRATION_COLUMNS)
    write_readme(output_dir, {
        "historical_rows": len(feature_rows),
        "label_rows": len(label_rows),
        "joined_rows": len(joined),
        "baseline_rows": len(scored_rows),
        "partial_rows": sum(1 for row in joined if row.get("eval_backtest_ready_flag") == "partial"),
    }, join_status)
    write_legacy_outputs(legacy_output_dir, inventory, metrics, failures)
    return {
        "historical_rows": len(feature_rows),
        "label_rows": len(label_rows),
        "joined_rows": len(joined),
        "unjoined_rows": len(unjoined),
        "baseline_rows": len(scored_rows),
        "partial_rows": sum(1 for row in joined if row.get("eval_backtest_ready_flag") == "partial"),
        "join_status_green": 1 if join_status == "GREEN" else 0,
        "metric_rows": len(metrics),
        "miss_rows": len(misses),
        "warning_calibration_rows": len(warning),
        "position_calibration_rows": len(position),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rookie historical label integration baseline backtest v1.")
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--legacy-output-dir", type=Path, default=LEGACY_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.historical, args.labels, args.output_dir, args.legacy_output_dir)
    except RookieBacktestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
