"""Build a local-only rookie WR feature quality improvement pass.

This pass engineers WR-specific source-safe features from the existing CFBD
cache and repaired joins, then compares fixed WR-feature candidates against the
current CFBD-enriched baseline. It does not call live APIs, tune on names, build
production rankings, or promote artifacts.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.tune_rookie_model_runway_v1_1 import (  # noqa: E402
    BASELINE_CONFIG,
    BUCKETS,
    DEFAULT_LABELS,
    DEFAULT_REPAIRED_JOIN,
    FINAL_YEARS,
    YEARS,
    assign_ranks,
    load_runway_rows,
    metric_row,
    rate,
    score_rows_v1_1,
    safe_int,
    to_float,
    write_csv,
)


DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/wr_feature_quality_improvement_pass_20260615")
DEFAULT_PLAYER_FEATURES = Path(
    "local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615/"
    "cfbd_player_season_features_v1_20260615.csv"
)
DEFAULT_PLAYER_FEATURES_2009 = Path(
    "local_exports/rookie_framework/cfbd_identity_join_repair_20260615/"
    "cfbd_2009_player_season_features_20260615.csv"
)
DEFAULT_CURRENT_BOARD = Path(
    "local_exports/rookie_framework/draft_ranking_model_v1_20260615/"
    "rookie_draft_ranking_v1_20260615.csv"
)

WR_CANDIDATES = {
    "wr_feature_enhanced_conservative": {
        "description": "fixed WR feature-quality adjustment with capped production/share bonuses and visible warnings",
        "positive_scale": 0.10,
        "penalty_scale": 0.65,
        "max_bonus": 5.5,
        "max_penalty": -5.5,
    },
    "wr_feature_enhanced_assertive": {
        "description": "fixed stronger WR feature-quality adjustment for sensitivity only",
        "positive_scale": 0.16,
        "penalty_scale": 0.85,
        "max_bonus": 8.0,
        "max_penalty": -8.0,
    },
}

FEATURE_COLUMNS = [
    "historical_label_key",
    "draft_year",
    "player_name",
    "position",
    "draft_round",
    "overall_pick",
    "star_label",
    "bust_label",
    "three_year_points",
    "cfbd_feature_status",
    "cfbd_duplicate_selected",
    "cfbd_manual_review_flag",
    "wr_feature_status",
    "wr_denominator_status",
    "wr_career_seasons_found",
    "wr_final_receiving_yards",
    "wr_final_receptions",
    "wr_final_receiving_tds",
    "wr_final_yards_per_reception",
    "wr_final_receiving_yard_share",
    "wr_final_reception_share",
    "wr_final_receiving_td_share",
    "wr_best_receiving_yards",
    "wr_best_receptions",
    "wr_best_receiving_tds",
    "wr_best_receiving_yard_share",
    "wr_best_reception_share",
    "wr_best_receiving_td_share",
    "wr_career_receiving_yards",
    "wr_career_receptions",
    "wr_career_receiving_tds",
    "wr_productive_seasons",
    "wr_meaningful_share_seasons",
    "wr_one_year_spike_flag",
    "wr_late_capital_strong_profile_flag",
    "wr_early_capital_weak_profile_warning",
    "wr_no_meaningful_production_warning",
    "wr_denominator_missing_warning",
    "wr_identity_join_warning",
    "wr_feature_signal_score",
    "wr_warning_penalty",
    "wr_feature_adjustment_conservative",
    "wr_feature_adjustment_assertive",
]

METRIC_COLUMNS = [
    "model",
    "metric_scope",
    "scope_value",
    "bucket",
    "row_count",
    "selected_rows",
    "stars_total",
    "stars_captured",
    "star_capture_rate",
    "bust_total",
    "busts_selected",
    "bust_rate_selected",
    "avg_selected_points",
    "notes",
]

QUALITY_COLUMNS = [
    "audit_scope",
    "scope_value",
    "row_count",
    "feature_ready_rows",
    "missing_feature_rows",
    "denominator_ready_rows",
    "duplicate_selected_rows",
    "manual_review_rows",
    "one_year_spike_rows",
    "weak_early_capital_warning_rows",
    "no_meaningful_production_warning_rows",
    "verdict",
]

CANDIDATE_DECISION_COLUMNS = [
    "candidate_name",
    "decision",
    "reason",
    "wr_final_top12_star_delta",
    "wr_final_top24_star_delta",
    "wr_final_top36_star_delta",
    "wr_final_top12_bust_delta",
    "wr_final_top24_bust_delta",
    "wr_final_top36_bust_delta",
    "overall_final_top24_star_delta",
    "overall_final_top24_bust_delta",
    "experimental_candidate_output",
]

DIAG_COLUMNS = [
    "candidate_name",
    "diagnostic_type",
    "draft_year",
    "player_name",
    "position",
    "draft_round",
    "overall_pick",
    "candidate_score",
    "candidate_class_rank",
    "star_label",
    "bust_label",
    "three_year_points",
    "wr_feature_status",
    "diagnosis",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value: float) -> str:
    return f"{value:.3f}"


def has_value(value: str) -> bool:
    return value is not None and str(value).strip() != ""


def load_player_seasons(paths: list[Path]) -> dict[str, list[dict[str, str]]]:
    by_id: dict[str, list[dict[str, str]]] = {}
    for path in paths:
        for row in read_csv(path):
            player_id = row.get("cfbd_player_id", "").strip()
            if not player_id:
                continue
            by_id.setdefault(player_id, []).append(row)
    for rows in by_id.values():
        rows.sort(key=lambda row: safe_int(row.get("season")))
    return by_id


def wr_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("position") == "WR"]


def feature_ready(row: dict[str, str]) -> bool:
    return row.get("cfbd_feature_status") == "deterministic_joined" and has_value(cfbd_player_id(row))


def cfbd_player_id(row: dict[str, str]) -> str:
    return (row.get("cfbd_player_id") or row.get("cfbd_cfbd_player_id") or "").strip()


def career_rows_for(row: dict[str, str], by_id: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    draft_year = safe_int(row.get("draft_year"))
    player_id = cfbd_player_id(row)
    return [
        season
        for season in by_id.get(player_id, [])
        if safe_int(season.get("season")) < draft_year and safe_int(season.get("season")) >= draft_year - 5
    ]


def denominator_ready(row: dict[str, str]) -> bool:
    return (
        has_value(row.get("cfbd_receiving_yard_share", ""))
        and has_value(row.get("cfbd_reception_share", ""))
        and has_value(row.get("cfbd_receiving_td_share", ""))
    )


def build_feature_row(row: dict[str, str], by_id: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    ready = feature_ready(row)
    career = career_rows_for(row, by_id) if ready else []
    receiving_yards = [to_float(item.get("receiving_yards")) for item in career]
    receptions = [to_float(item.get("receptions")) for item in career]
    receiving_tds = [to_float(item.get("receiving_tds")) for item in career]
    yard_shares = [to_float(item.get("receiving_yard_share")) for item in career if has_value(item.get("receiving_yard_share", ""))]
    reception_shares = [to_float(item.get("reception_share")) for item in career if has_value(item.get("reception_share", ""))]
    td_shares = [to_float(item.get("receiving_td_share")) for item in career if has_value(item.get("receiving_td_share", ""))]
    final_receptions = to_float(row.get("cfbd_receptions"))
    ypr = to_float(row.get("cfbd_receiving_yards")) / final_receptions if final_receptions >= 20 else 0.0
    productive_seasons = sum(1 for item in career if to_float(item.get("receiving_yards")) >= 500 or to_float(item.get("receiving_yard_share")) >= 0.18)
    meaningful_share_seasons = sum(1 for item in career if to_float(item.get("receiving_yard_share")) >= 0.20 or to_float(item.get("reception_share")) >= 0.18)
    best_yards = max(receiving_yards) if receiving_yards else 0.0
    best_receptions = max(receptions) if receptions else 0.0
    best_tds = max(receiving_tds) if receiving_tds else 0.0
    best_yard_share = max(yard_shares) if yard_shares else 0.0
    best_reception_share = max(reception_shares) if reception_shares else 0.0
    best_td_share = max(td_shares) if td_shares else 0.0
    draft_round = safe_int(row.get("draft_round"))
    one_year_spike = ready and productive_seasons == 1 and (best_yards >= 800 or best_yard_share >= 0.25)
    strong_late = ready and draft_round >= 3 and (best_yards >= 900 or best_yard_share >= 0.28) and productive_seasons >= 1
    weak_early = ready and draft_round <= 2 and best_yards < 650 and best_yard_share < 0.20
    no_production = ready and best_yards < 350 and best_yard_share < 0.12
    denominator_missing = ready and not denominator_ready(row)
    identity_warning = row.get("cfbd_duplicate_selected") == "yes" or row.get("cfbd_manual_review_flag") == "yes"
    signal = wr_signal_score(
        final_yards=to_float(row.get("cfbd_receiving_yards")),
        final_receptions=final_receptions,
        final_tds=to_float(row.get("cfbd_receiving_tds")),
        final_yard_share=to_float(row.get("cfbd_receiving_yard_share")),
        final_reception_share=to_float(row.get("cfbd_reception_share")),
        final_td_share=to_float(row.get("cfbd_receiving_td_share")),
        ypr=ypr,
        best_yards=best_yards,
        best_yard_share=best_yard_share,
        best_reception_share=best_reception_share,
        best_td_share=best_td_share,
        career_yards=sum(receiving_yards),
        career_receptions=sum(receptions),
        career_tds=sum(receiving_tds),
        productive_seasons=productive_seasons,
        meaningful_share_seasons=meaningful_share_seasons,
        strong_late=strong_late,
    )
    penalty = wr_warning_penalty(
        one_year_spike=one_year_spike,
        weak_early=weak_early,
        no_production=no_production,
        denominator_missing=denominator_missing,
        identity_warning=identity_warning,
    )
    if not ready:
        status = "missing_or_unresolved_cfbd_features"
        signal = 0.0
        penalty = 2.5
    else:
        status = "wr_features_ready"
    conservative = capped(signal * WR_CANDIDATES["wr_feature_enhanced_conservative"]["positive_scale"] - penalty * WR_CANDIDATES["wr_feature_enhanced_conservative"]["penalty_scale"], -5.5, 5.5)
    assertive = capped(signal * WR_CANDIDATES["wr_feature_enhanced_assertive"]["positive_scale"] - penalty * WR_CANDIDATES["wr_feature_enhanced_assertive"]["penalty_scale"], -8.0, 8.0)
    return {
        "historical_label_key": row.get("historical_label_key", ""),
        "draft_year": row.get("draft_year", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "draft_round": row.get("draft_round", ""),
        "overall_pick": row.get("overall_pick", ""),
        "star_label": row.get("star_label", ""),
        "bust_label": row.get("bust_label", ""),
        "three_year_points": row.get("three_year_points", ""),
        "cfbd_feature_status": row.get("cfbd_feature_status", ""),
        "cfbd_duplicate_selected": row.get("cfbd_duplicate_selected", ""),
        "cfbd_manual_review_flag": row.get("cfbd_manual_review_flag", ""),
        "wr_feature_status": status,
        "wr_denominator_status": "denominator_ready" if ready and not denominator_missing else "denominator_missing" if ready else "not_applicable",
        "wr_career_seasons_found": str(len(career)),
        "wr_final_receiving_yards": fmt(to_float(row.get("cfbd_receiving_yards"))) if ready else "",
        "wr_final_receptions": fmt(final_receptions) if ready else "",
        "wr_final_receiving_tds": fmt(to_float(row.get("cfbd_receiving_tds"))) if ready else "",
        "wr_final_yards_per_reception": fmt(ypr) if ready and final_receptions >= 20 else "",
        "wr_final_receiving_yard_share": row.get("cfbd_receiving_yard_share", "") if ready else "",
        "wr_final_reception_share": row.get("cfbd_reception_share", "") if ready else "",
        "wr_final_receiving_td_share": row.get("cfbd_receiving_td_share", "") if ready else "",
        "wr_best_receiving_yards": fmt(best_yards) if ready else "",
        "wr_best_receptions": fmt(best_receptions) if ready else "",
        "wr_best_receiving_tds": fmt(best_tds) if ready else "",
        "wr_best_receiving_yard_share": fmt(best_yard_share) if ready and yard_shares else "",
        "wr_best_reception_share": fmt(best_reception_share) if ready and reception_shares else "",
        "wr_best_receiving_td_share": fmt(best_td_share) if ready and td_shares else "",
        "wr_career_receiving_yards": fmt(sum(receiving_yards)) if ready else "",
        "wr_career_receptions": fmt(sum(receptions)) if ready else "",
        "wr_career_receiving_tds": fmt(sum(receiving_tds)) if ready else "",
        "wr_productive_seasons": str(productive_seasons) if ready else "",
        "wr_meaningful_share_seasons": str(meaningful_share_seasons) if ready else "",
        "wr_one_year_spike_flag": "yes" if one_year_spike else "no",
        "wr_late_capital_strong_profile_flag": "yes" if strong_late else "no",
        "wr_early_capital_weak_profile_warning": "yes" if weak_early else "no",
        "wr_no_meaningful_production_warning": "yes" if no_production else "no",
        "wr_denominator_missing_warning": "yes" if denominator_missing else "no",
        "wr_identity_join_warning": "yes" if identity_warning else "no",
        "wr_feature_signal_score": fmt(signal) if ready else "",
        "wr_warning_penalty": fmt(penalty),
        "wr_feature_adjustment_conservative": fmt(conservative),
        "wr_feature_adjustment_assertive": fmt(assertive),
    }


def capped(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def wr_signal_score(
    *,
    final_yards: float,
    final_receptions: float,
    final_tds: float,
    final_yard_share: float,
    final_reception_share: float,
    final_td_share: float,
    ypr: float,
    best_yards: float,
    best_yard_share: float,
    best_reception_share: float,
    best_td_share: float,
    career_yards: float,
    career_receptions: float,
    career_tds: float,
    productive_seasons: int,
    meaningful_share_seasons: int,
    strong_late: bool,
) -> float:
    score = 0.0
    score += capped(final_yards / 22.0, 0.0, 32.0)
    score += capped(final_receptions / 4.0, 0.0, 16.0)
    score += capped(final_tds * 1.6, 0.0, 14.0)
    score += capped(final_yard_share * 46.0, 0.0, 20.0)
    score += capped(final_reception_share * 36.0, 0.0, 14.0)
    score += capped(final_td_share * 28.0, 0.0, 10.0)
    if final_receptions >= 20:
        score += capped((ypr - 10.0) * 0.8, 0.0, 6.0)
    score += capped(best_yards / 55.0, 0.0, 16.0)
    score += capped(best_yard_share * 24.0, 0.0, 10.0)
    score += capped(best_reception_share * 18.0, 0.0, 7.0)
    score += capped(best_td_share * 14.0, 0.0, 6.0)
    score += capped(career_yards / 260.0, 0.0, 12.0)
    score += capped(career_receptions / 32.0, 0.0, 6.0)
    score += capped(career_tds / 4.5, 0.0, 5.0)
    score += min(productive_seasons, 3) * 3.0
    score += min(meaningful_share_seasons, 3) * 2.0
    if strong_late:
        score += 4.0
    return capped(score, 0.0, 100.0)


def wr_warning_penalty(
    *,
    one_year_spike: bool,
    weak_early: bool,
    no_production: bool,
    denominator_missing: bool,
    identity_warning: bool,
) -> float:
    penalty = 0.0
    if one_year_spike:
        penalty += 2.5
    if weak_early:
        penalty += 5.0
    if no_production:
        penalty += 6.0
    if denominator_missing:
        penalty += 4.0
    if identity_warning:
        penalty += 2.5
    return penalty


def apply_candidate_scores(
    baseline_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
    candidate_name: str,
) -> list[dict[str, str]]:
    feature_by_key = {row["historical_label_key"]: row for row in feature_rows}
    adjustment_field = "wr_feature_adjustment_conservative" if candidate_name.endswith("conservative") else "wr_feature_adjustment_assertive"
    scored = []
    for row in baseline_rows:
        out = dict(row)
        out["candidate_name"] = candidate_name
        out["candidate_score"] = out["baseline_score_v1_1"]
        if out.get("position") == "WR":
            feature = feature_by_key.get(out["historical_label_key"], {})
            out["candidate_score"] = fmt(to_float(out["baseline_score_v1_1"]) + to_float(feature.get(adjustment_field)))
            out["wr_feature_status"] = feature.get("wr_feature_status", "missing_feature_row")
        scored.append(out)
    assign_ranks(scored, "candidate_score")
    return scored


def baseline_rows_scored(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    baseline = score_rows_v1_1(rows, BASELINE_CONFIG, "baseline_score_v1_1")
    for row in baseline:
        row["candidate_score"] = row["baseline_score_v1_1"]
        row["candidate_name"] = BASELINE_CONFIG.name
    assign_ranks(baseline, "candidate_score")
    return baseline


def selected_by_year(rows: list[dict[str, str]], years: set[str], bucket: int) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("draft_year") in years and safe_int(row.get("candidate_score_class_rank", "999999")) <= bucket
    ]


def selected_wr(rows: list[dict[str, str]], years: set[str], bucket: int) -> list[dict[str, str]]:
    scoped = [row for row in rows if row.get("position") == "WR" and row.get("draft_year") in years]
    scoped.sort(key=lambda row: (-to_float(row.get("candidate_score")), safe_int(row.get("overall_pick")), row.get("player_name", "")))
    return scoped[:bucket]


def metrics_for_candidate(rows: list[dict[str, str]], candidate_name: str, notes: str) -> list[dict[str, str]]:
    output = []
    for scope, years in [
        ("train_dev_2010_2021", {str(year) for year in range(2010, 2022)}),
        ("validation_2022_2023", FINAL_YEARS),
        ("full_2010_2023", YEARS),
    ]:
        scoped = [row for row in rows if row.get("draft_year") in years]
        for bucket in BUCKETS:
            output.append(metric_row(candidate_name, "year_class", scope, scoped, selected_by_year(scoped, years, bucket), bucket, notes))
            wr_scoped = [row for row in scoped if row.get("position") == "WR"]
            output.append(metric_row(candidate_name, "wr_only", scope, wr_scoped, selected_wr(scoped, years, bucket), bucket, notes))
    for position in ["QB", "RB", "TE"]:
        scoped = [row for row in rows if row.get("position") == position]
        sorted_pos = sorted(scoped, key=lambda row: (-to_float(row.get("candidate_score")), safe_int(row.get("overall_pick")), row.get("player_name", "")))
        for bucket in BUCKETS:
            output.append(metric_row(candidate_name, "non_wr_position_sanity", position, scoped, sorted_pos[:bucket], bucket, notes))
    return output


def quality_rows(features: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    rows.append(quality_row("overall", "all", features))
    for year in sorted({row["draft_year"] for row in features}, key=safe_int):
        rows.append(quality_row("year", year, [row for row in features if row["draft_year"] == year]))
    for draft_round in sorted({row["draft_round"] for row in features}, key=safe_int):
        rows.append(quality_row("draft_round", draft_round, [row for row in features if row["draft_round"] == draft_round]))
    return rows


def quality_row(scope: str, value: str, rows: list[dict[str, str]]) -> dict[str, str]:
    ready = sum(1 for row in rows if row["wr_feature_status"] == "wr_features_ready")
    denominator = sum(1 for row in rows if row["wr_denominator_status"] == "denominator_ready")
    duplicates = sum(1 for row in rows if row["cfbd_duplicate_selected"] == "yes")
    manual = sum(1 for row in rows if row["cfbd_manual_review_flag"] == "yes")
    spikes = sum(1 for row in rows if row["wr_one_year_spike_flag"] == "yes")
    weak = sum(1 for row in rows if row["wr_early_capital_weak_profile_warning"] == "yes")
    no_prod = sum(1 for row in rows if row["wr_no_meaningful_production_warning"] == "yes")
    ready_rate = ready / len(rows) if rows else 0.0
    denominator_rate = denominator / len(rows) if rows else 0.0
    if ready_rate >= 0.85 and denominator_rate >= 0.80:
        verdict = "GREEN"
    elif ready_rate >= 0.70:
        verdict = "YELLOW"
    else:
        verdict = "RED"
    return {
        "audit_scope": scope,
        "scope_value": value,
        "row_count": str(len(rows)),
        "feature_ready_rows": str(ready),
        "missing_feature_rows": str(len(rows) - ready),
        "denominator_ready_rows": str(denominator),
        "duplicate_selected_rows": str(duplicates),
        "manual_review_rows": str(manual),
        "one_year_spike_rows": str(spikes),
        "weak_early_capital_warning_rows": str(weak),
        "no_meaningful_production_warning_rows": str(no_prod),
        "verdict": verdict,
    }


def coverage_rows(features: list[dict[str, str]], scope: str) -> list[dict[str, str]]:
    rows = []
    values = sorted({row["draft_year"] for row in features}, key=safe_int) if scope == "year" else sorted({row["draft_round"] for row in features}, key=safe_int)
    for value in values:
        scoped = [row for row in features if row["draft_year" if scope == "year" else "draft_round"] == value]
        ready = sum(1 for row in scoped if row["wr_feature_status"] == "wr_features_ready")
        denom = sum(1 for row in scoped if row["wr_denominator_status"] == "denominator_ready")
        rows.append(
            {
                "scope": scope,
                "scope_value": value,
                "wr_rows": str(len(scoped)),
                "feature_ready_rows": str(ready),
                "feature_ready_rate": rate(ready, len(scoped)),
                "denominator_ready_rows": str(denom),
                "denominator_ready_rate": rate(denom, len(scoped)),
            }
        )
    return rows


COVERAGE_COLUMNS = [
    "scope",
    "scope_value",
    "wr_rows",
    "feature_ready_rows",
    "feature_ready_rate",
    "denominator_ready_rows",
    "denominator_ready_rate",
]


def metric_lookup(metrics: list[dict[str, str]], model: str, scope: str, bucket: str, metric_scope: str) -> dict[str, str]:
    for row in metrics:
        if row["model"] == model and row["scope_value"] == scope and row["bucket"] == bucket and row["metric_scope"] == metric_scope:
            return row
    raise KeyError((model, scope, bucket, metric_scope))


def candidate_decisions(metrics: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    baseline = BASELINE_CONFIG.name
    for candidate_name, config in WR_CANDIDATES.items():
        deltas = {}
        for bucket in ["top_12", "top_24", "top_36"]:
            wr_base = metric_lookup(metrics, baseline, "validation_2022_2023", bucket, "wr_only")
            wr_candidate = metric_lookup(metrics, candidate_name, "validation_2022_2023", bucket, "wr_only")
            deltas[f"wr_{bucket}_star"] = to_float(wr_candidate["star_capture_rate"]) - to_float(wr_base["star_capture_rate"])
            deltas[f"wr_{bucket}_bust"] = to_float(wr_candidate["bust_rate_selected"]) - to_float(wr_base["bust_rate_selected"])
        overall_base = metric_lookup(metrics, baseline, "validation_2022_2023", "top_24", "year_class")
        overall_candidate = metric_lookup(metrics, candidate_name, "validation_2022_2023", "top_24", "year_class")
        overall_star_delta = to_float(overall_candidate["star_capture_rate"]) - to_float(overall_base["star_capture_rate"])
        overall_bust_delta = to_float(overall_candidate["bust_rate_selected"]) - to_float(overall_base["bust_rate_selected"])
        wr_improved = deltas["wr_top_12_star"] > 0 or deltas["wr_top_24_star"] > 0 or deltas["wr_top_36_star"] > 0 or deltas["wr_top_24_bust"] <= -0.04
        overall_ok = overall_star_delta >= -0.025 and overall_bust_delta <= 0.050
        bust_ok = deltas["wr_top_24_bust"] <= 0.050 and deltas["wr_top_36_bust"] <= 0.050
        if wr_improved and overall_ok and bust_ok:
            decision = "eligible_for_local_experimental_candidate"
            reason = "WR validation improved without material overall regression"
            output = "yes"
        else:
            decision = "not_created"
            reason = "WR validation/overall sanity did not clear candidate output gates"
            output = "no"
        rows.append(
            {
                "candidate_name": candidate_name,
                "decision": decision,
                "reason": reason,
                "wr_final_top12_star_delta": fmt(deltas["wr_top_12_star"]),
                "wr_final_top24_star_delta": fmt(deltas["wr_top_24_star"]),
                "wr_final_top36_star_delta": fmt(deltas["wr_top_36_star"]),
                "wr_final_top12_bust_delta": fmt(deltas["wr_top_12_bust"]),
                "wr_final_top24_bust_delta": fmt(deltas["wr_top_24_bust"]),
                "wr_final_top36_bust_delta": fmt(deltas["wr_top_36_bust"]),
                "overall_final_top24_star_delta": fmt(overall_star_delta),
                "overall_final_top24_bust_delta": fmt(overall_bust_delta),
                "experimental_candidate_output": output,
            }
        )
    return rows


def diagnostics(rows_by_candidate: dict[str, list[dict[str, str]]], decision_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    best_name = next((row["candidate_name"] for row in decision_rows if row["experimental_candidate_output"] == "yes"), BASELINE_CONFIG.name)
    rows = rows_by_candidate[best_name]
    wr = [row for row in rows if row.get("position") == "WR"]
    selected_top36 = selected_wr(rows, YEARS, 36)
    missed = [row for row in wr if row.get("star_label") == "1" and row not in selected_top36]
    missed.sort(key=lambda row: (-to_float(row.get("three_year_points")), row.get("draft_year", ""), row.get("player_name", "")))
    busts = [row for row in selected_top36 if row.get("bust_label") == "1"]
    busts.sort(key=lambda row: (row.get("draft_year", ""), safe_int(row.get("candidate_score_class_rank", "999999"))))
    return [diag_row(best_name, row, "missed_wr_star") for row in missed[:50]], [diag_row(best_name, row, "high_ranked_wr_bust") for row in busts[:75]]


def diag_row(candidate_name: str, row: dict[str, str], kind: str) -> dict[str, str]:
    return {
        "candidate_name": candidate_name,
        "diagnostic_type": kind,
        "draft_year": row.get("draft_year", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "draft_round": row.get("draft_round", ""),
        "overall_pick": row.get("overall_pick", ""),
        "candidate_score": row.get("candidate_score", ""),
        "candidate_class_rank": row.get("candidate_score_class_rank", ""),
        "star_label": row.get("star_label", ""),
        "bust_label": row.get("bust_label", ""),
        "three_year_points": row.get("three_year_points", ""),
        "wr_feature_status": row.get("wr_feature_status", ""),
        "diagnosis": "diagnostic_names_only_no_player_specific_tuning",
    }


def write_readme(output_dir: Path, decision_rows: list[dict[str, str]]) -> None:
    created = any(row["experimental_candidate_output"] == "yes" for row in decision_rows)
    text = [
        "# Rookie WR Feature Quality Improvement Pass",
        "",
        "Local-only WR feature-quality exports. These are not production rankings or app-readable artifacts.",
        "",
        f"- experimental candidate output created: {'yes' if created else 'no'}",
        "- features: final-season receiving profile, best-season profile, career/multi-year profile, market-share robustness, draft-capital interaction warnings",
        "- labels: evaluation-only",
        "- names: diagnostics only",
        "",
        "No live CFBD request was made by this script.",
    ]
    (output_dir / "README_WR_FEATURE_QUALITY_IMPROVEMENT_PASS_20260615.md").write_text("\n".join(text), encoding="utf-8")


def current_wr_coverage(current_board: Path) -> list[dict[str, str]]:
    rows = [row for row in read_csv(current_board) if row.get("position") == "WR"]
    return [
        {
            "scope": "current_2026",
            "scope_value": "current_board",
            "wr_rows": str(len(rows)),
            "feature_ready_rows": "0",
            "feature_ready_rate": "0.000",
            "denominator_ready_rows": "0",
            "denominator_ready_rate": "0.000",
            "note": "current 2026 multi-year CFBD WR feature cache not present; historical feature logic not applied to current board",
        }
    ]


CURRENT_COVERAGE_COLUMNS = [*COVERAGE_COLUMNS, "note"]


def build_exports(
    labels: Path,
    repaired_join: Path,
    player_features: Path,
    player_features_2009: Path,
    current_board: Path,
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = load_runway_rows(labels, repaired_join)
    baseline = baseline_rows_scored(rows)
    by_id = load_player_seasons([player_features, player_features_2009])
    features = [build_feature_row(row, by_id) for row in wr_rows(baseline)]
    rows_by_candidate = {BASELINE_CONFIG.name: baseline}
    metrics = metrics_for_candidate(baseline, BASELINE_CONFIG.name, "baseline reference")
    for candidate_name, config in WR_CANDIDATES.items():
        scored = apply_candidate_scores(baseline, features, candidate_name)
        rows_by_candidate[candidate_name] = scored
        metrics.extend(metrics_for_candidate(scored, candidate_name, config["description"]))
    decisions = candidate_decisions(metrics)
    missed, busts = diagnostics(rows_by_candidate, decisions)
    write_csv(output_dir / "wr_feature_table_historical_20260615.csv", features, FEATURE_COLUMNS)
    write_csv(output_dir / "wr_feature_coverage_by_year_20260615.csv", coverage_rows(features, "year"), COVERAGE_COLUMNS)
    write_csv(output_dir / "wr_feature_coverage_by_round_20260615.csv", coverage_rows(features, "draft_round"), COVERAGE_COLUMNS)
    write_csv(output_dir / "wr_feature_current_coverage_20260615.csv", current_wr_coverage(current_board), CURRENT_COVERAGE_COLUMNS)
    write_csv(output_dir / "wr_feature_quality_audit_20260615.csv", quality_rows(features), QUALITY_COLUMNS)
    write_csv(output_dir / "wr_feature_baseline_comparison_20260615.csv", metrics, METRIC_COLUMNS)
    write_csv(output_dir / "wr_missed_star_diagnostics_20260615.csv", missed, DIAG_COLUMNS)
    write_csv(output_dir / "wr_high_ranked_bust_diagnostics_20260615.csv", busts, DIAG_COLUMNS)
    write_csv(output_dir / "wr_feature_candidate_decision_20260615.csv", decisions, CANDIDATE_DECISION_COLUMNS)
    write_readme(output_dir, decisions)
    return {
        "rows": rows,
        "wr_features": features,
        "metrics": metrics,
        "decisions": decisions,
        "candidate_created": any(row["experimental_candidate_output"] == "yes" for row in decisions),
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--repaired-join", type=Path, default=DEFAULT_REPAIRED_JOIN)
    parser.add_argument("--player-features", type=Path, default=DEFAULT_PLAYER_FEATURES)
    parser.add_argument("--player-features-2009", type=Path, default=DEFAULT_PLAYER_FEATURES_2009)
    parser.add_argument("--current-board", type=Path, default=DEFAULT_CURRENT_BOARD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(
        args.labels,
        args.repaired_join,
        args.player_features,
        args.player_features_2009,
        args.current_board,
        args.output_dir,
    )
    status_counts = Counter(row["wr_feature_status"] for row in result["wr_features"])
    print(f"historical_rows={len(result['rows'])}")
    print(f"historical_wr_rows={len(result['wr_features'])}")
    print(f"wr_features_ready={status_counts['wr_features_ready']}")
    print(f"candidate_created={'yes' if result['candidate_created'] else 'no'}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
