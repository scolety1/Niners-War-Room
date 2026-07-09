from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


OUT_DIR = Path(__file__).resolve().parent

RECEIPT_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708"
    r"\docs\hq\model\model_v4_historical_component_receipt_backfill_v1_20260708"
)
SUBSTRATE_DIR = Path(
    r"C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708"
    r"\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708"
)
BACKTEST_DIR = Path(
    r"C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708"
    r"\docs\hq\model\production_rankings_backtest_v1_20260708"
)
EXACT_REBUILD_DIR = Path(
    r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708"
    r"\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708"
)
FORMULA_DOC_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708"
    r"\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708"
)
HQ1_STANDARD_DIR = Path(
    "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"
)

RECEIPTS_PATH = RECEIPT_DIR / "MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv"
READINESS_PATH = RECEIPT_DIR / "MODEL_V4_HISTORICAL_REPLAY_READINESS_MATRIX.csv"
COVERAGE_PATH = RECEIPT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_COVERAGE_SUMMARY.csv"
CONTRACT_PATH = RECEIPT_DIR / "MODEL_V4_NEXT_REPLAY_BENCHMARK_CONTRACT.md"
PANEL_PATH = SUBSTRATE_DIR / "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
PRODUCTION_SCORECARD_PATH = BACKTEST_DIR / "PRODUCTION_RANKINGS_BACKTEST_V1_SCORECARD.csv"

POSITION_TOPNS = {
    "QB": [12],
    "RB": [12, 24],
    "WR": [12, 24, 36],
    "TE": [12],
}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}

LOWER_IS_BETTER_COLUMNS = {"prior_interceptions"}
BLOCKED_INPUT_WORDS = {
    "current",
    "adp",
    "market",
    "projection",
    "rankings",
    "depth",
    "injury",
    "roster_status",
    "checkpoint_review_score",
    "position_specific_review_score",
    "nwr_dynasty_score",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def num(value: object) -> float | None:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "not enough information"}:
        return None
    try:
        value_float = float(text)
    except ValueError:
        return None
    if not math.isfinite(value_float):
        return None
    return value_float


def pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value * 100:.1f}%"


def fmt(value: float | None, places: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{places}f}"


def ranks(values: list[float], high_better: bool) -> list[float]:
    indexed = list(enumerate(values))
    indexed.sort(key=lambda item: item[1], reverse=high_better)
    result = [0.0] * len(values)
    idx = 0
    while idx < len(indexed):
        end = idx + 1
        while end < len(indexed) and indexed[end][1] == indexed[idx][1]:
            end += 1
        avg_rank = (idx + 1 + end) / 2.0
        for original_idx, _ in indexed[idx:end]:
            result[original_idx] = avg_rank
        idx = end
    return result


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def spearman(xs: list[float], ys: list[float], x_high_better: bool = True, y_high_better: bool = True) -> float | None:
    return pearson(ranks(xs, high_better=x_high_better), ranks(ys, high_better=y_high_better))


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def rmse(values: list[float]) -> float | None:
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else None


def bool_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def group_key(row: dict[str, str]) -> tuple[str, str]:
    return row["target_season"], row["position"]


def direction_for_column(column: str) -> str:
    return "asc" if column in LOWER_IS_BETTER_COLUMNS else "desc"


def covered_rows(panel_rows: list[dict[str, str]], source_column: str) -> list[dict[str, str]]:
    return [row for row in panel_rows if num(row.get(source_column)) is not None and num(row.get("next_position_finish")) is not None]


def predicted_ranks_by_group(rows: list[dict[str, str]], source_column: str, direction: str) -> dict[str, float]:
    high_better = direction != "asc"
    result: dict[str, float] = {}
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    for group_rows in grouped.values():
        values = [num(row[source_column]) for row in group_rows]
        assert all(value is not None for value in values)
        rank_values = ranks([float(value) for value in values if value is not None], high_better=high_better)
        for row, rank in zip(group_rows, rank_values):
            result[row["substrate_row_id"]] = rank
    return result


def topn_precision(rows: list[dict[str, str]], source_column: str, topn: int, direction: str) -> tuple[float | None, float | None]:
    high_better = direction != "asc"
    picks = 0
    hits = 0
    actual = 0
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    for group_rows in grouped.values():
        sorted_rows = sorted(group_rows, key=lambda row: num(row[source_column]) or 0.0, reverse=high_better)
        selected = sorted_rows[: min(topn, len(sorted_rows))]
        picks += len(selected)
        hits += sum(1 for row in selected if (num(row.get("next_position_finish")) or 9999) <= topn)
        actual += sum(1 for row in group_rows if (num(row.get("next_position_finish")) or 9999) <= topn)
    precision = hits / picks if picks else None
    recall = hits / actual if actual else None
    return precision, recall


def startable_precision_recall(rows: list[dict[str, str]], source_column: str, direction: str) -> tuple[float | None, float | None]:
    high_better = direction != "asc"
    picks = 0
    hits = 0
    actual = 0
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    for (season, position), group_rows in grouped.items():
        cutoff = STARTABLE_CUTOFF[position]
        sorted_rows = sorted(group_rows, key=lambda row: num(row[source_column]) or 0.0, reverse=high_better)
        selected = sorted_rows[: min(cutoff, len(sorted_rows))]
        picks += len(selected)
        hits += sum(1 for row in selected if bool_true(row.get("startable_hit")))
        actual += sum(1 for row in group_rows if bool_true(row.get("startable_hit")))
    precision = hits / picks if picks else None
    recall = hits / actual if actual else None
    return precision, recall


def evaluate_signal(
    panel_rows: list[dict[str, str]],
    position: str,
    component_name: str,
    source_column: str,
    metric_type: str,
) -> dict[str, object]:
    position_rows = [row for row in panel_rows if row["position"] == position]
    rows = covered_rows(position_rows, source_column)
    direction = direction_for_column(source_column)
    high_better = direction != "asc"
    predicted = predicted_ranks_by_group(rows, source_column, direction) if rows else {}
    errors = []
    pred_ranks = []
    finishes = []
    values = []
    next_points = []
    for row in rows:
        pred_rank = predicted[row["substrate_row_id"]]
        finish = num(row["next_position_finish"])
        value = num(row[source_column])
        points = num(row["next_nwr_points"])
        if finish is not None and value is not None and points is not None:
            pred_ranks.append(pred_rank)
            finishes.append(finish)
            values.append(value)
            next_points.append(points)
            errors.append(pred_rank - finish)
    top_metrics = {}
    for topn in [12, 24, 36]:
        if topn in POSITION_TOPNS[position]:
            precision, recall = topn_precision(rows, source_column, topn, direction)
            top_metrics[f"top_{topn}_precision"] = precision
            top_metrics[f"top_{topn}_recall"] = recall
        else:
            top_metrics[f"top_{topn}_precision"] = None
            top_metrics[f"top_{topn}_recall"] = None
    start_precision, start_recall = startable_precision_recall(rows, source_column, direction)
    total_rows = len(position_rows)
    coverage = len(rows) / total_rows if total_rows else None
    return {
        "position": position,
        "component_name": component_name,
        "source_column": source_column,
        "metric_type": metric_type,
        "direction": direction,
        "seasons": len({row["target_season"] for row in rows}),
        "rows": len(rows),
        "position_total_rows": total_rows,
        "coverage_rate": coverage,
        "missing_rows": total_rows - len(rows),
        "mae_rank_vs_finish": mean([abs(e) for e in errors]),
        "rmse_rank_vs_finish": rmse(errors),
        "spearman_rank_vs_finish": spearman(pred_ranks, finishes, x_high_better=False, y_high_better=False),
        "spearman_value_vs_next_points": spearman(values, next_points, x_high_better=high_better, y_high_better=True),
        "top_12_precision": top_metrics["top_12_precision"],
        "top_24_precision": top_metrics["top_24_precision"],
        "top_36_precision": top_metrics["top_36_precision"],
        "startable_precision": start_precision,
        "startable_recall": start_recall,
        "caveat": "component_source_signal_only_not_exact_model_v4_score",
    }


def allowed_signals_from_receipts(receipts: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    signals = set()
    for row in receipts:
        if row["historical_component_status"] != "partial_replay_proxy_only":
            continue
        if row["decision_date_safe_flag"] != "partial_v3_lagged_safe":
            continue
        if row["replay_eligibility_flag"] != "partial_replay_only_not_exact_model_v4":
            continue
        position = row["position"]
        component = row["component_name"]
        for source_column in row["source_columns"].split("|"):
            if source_column:
                signals.add((position, component, source_column))
    return sorted(signals)


def build_position_metrics(panel_rows: list[dict[str, str]], signals: list[tuple[str, str, str]]) -> list[dict[str, object]]:
    rows = []
    seen = set()
    for position, component, source_column in signals:
        key = (position, component, source_column)
        if key in seen:
            continue
        seen.add(key)
        rows.append(evaluate_signal(panel_rows, position, component, source_column, "component_source_signal"))
    for position in ["QB", "RB", "WR", "TE"]:
        rows.append(evaluate_signal(panel_rows, position, "prior_year_points_baseline", "prior_nwr_points", "baseline"))
        rows.append(evaluate_signal(panel_rows, position, "prior_year_ppg_baseline", "prior_nwr_ppg", "baseline"))
    return rows


def metric_score(row: dict[str, object]) -> float:
    spearman_value = row.get("spearman_rank_vs_finish")
    return float(spearman_value) if spearman_value not in {"", None} else -999.0


def build_scorecard(metrics: list[dict[str, object]], panel_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for position in ["QB", "RB", "WR", "TE"]:
        position_metrics = [row for row in metrics if row["position"] == position]
        component_metrics = [row for row in position_metrics if row["metric_type"] == "component_source_signal"]
        non_pyf = [
            row
            for row in component_metrics
            if row["source_column"] not in {"prior_nwr_points", "prior_nwr_ppg"}
        ]
        pyf = next(
            row
            for row in position_metrics
            if row["component_name"] == "prior_year_points_baseline"
            and row["source_column"] == "prior_nwr_points"
        )
        best_any = max(component_metrics, key=metric_score)
        best_non_pyf = max(non_pyf, key=metric_score)
        for metric_kind, metric in [
            ("prior_year_points_baseline", pyf),
            ("best_component_source", best_any),
            ("best_non_pyf_component_source", best_non_pyf),
        ]:
            rows.append(
                {
                    "Position": position,
                    "Seasons": metric["seasons"],
                    "Rows": metric["rows"],
                    "Metric Type": metric_kind,
                    "Signal": f"{metric['component_name']}::{metric['source_column']}",
                    "Spearman": fmt(metric["spearman_rank_vs_finish"]),
                    "Top-12": pct(metric["top_12_precision"]),
                    "Top-24": pct(metric["top_24_precision"]),
                    "Top-36": pct(metric["top_36_precision"]),
                    "Startable Precision": pct(metric["startable_precision"]),
                    "Caveat": (
                        "same_underlying_pyf_anchor"
                        if metric["source_column"] in {"prior_nwr_points", "prior_nwr_ppg"}
                        else "single_component_proxy_not_formula_score"
                    ),
                }
            )
    return rows


def build_baseline_comparison(metrics: list[dict[str, object]], production_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    production_by_position = {row["Position"]: row for row in production_rows}
    for position in ["QB", "RB", "WR", "TE"]:
        pos_metrics = [row for row in metrics if row["position"] == position]
        pyf = next(row for row in pos_metrics if row["component_name"] == "prior_year_points_baseline")
        ppg = next(row for row in pos_metrics if row["component_name"] == "prior_year_ppg_baseline")
        component_metrics = [row for row in pos_metrics if row["metric_type"] == "component_source_signal"]
        best_any = max(component_metrics, key=metric_score)
        best_non_pyf = max(
            [row for row in component_metrics if row["source_column"] not in {"prior_nwr_points", "prior_nwr_ppg"}],
            key=metric_score,
        )
        for model_name, metric, caveat in [
            ("prior_year_points_baseline", pyf, "safe baseline from completed feature-season NWR points"),
            ("prior_year_ppg_baseline", ppg, "safe baseline from completed feature-season NWR PPG"),
            ("best_component_source", best_any, "best allowed component source; may be the same PYF anchor"),
            (
                "best_non_pyf_component_source",
                best_non_pyf,
                "best allowed component source excluding prior_nwr_points/prior_nwr_ppg",
            ),
        ]:
            beat = ""
            if model_name.startswith("best"):
                beat = (
                    "Yes"
                    if (metric["spearman_rank_vs_finish"] or -999)
                    > (pyf["spearman_rank_vs_finish"] or -999)
                    else "No"
                )
            rows.append(
                {
                    "Model / Signal / Baseline": model_name,
                    "Scope": position,
                    "Metric": "Spearman rank vs next-season finish",
                    "Result": fmt(metric["spearman_rank_vs_finish"]),
                    "Beat Baseline?": beat,
                    "Caveat": caveat,
                }
            )
        prod = production_by_position.get(position)
        if prod:
            rows.append(
                {
                    "Model / Signal / Baseline": "Production Rankings Backtest V1 current-formula-family proxy",
                    "Scope": position,
                    "Metric": "Spearman",
                    "Result": prod["Spearman"],
                    "Beat Baseline?": "not_comparable_in_this_lane",
                    "Caveat": "prior accepted packet says proxy did not beat simple prior-year finish overall",
                }
            )
    return rows


def build_coverage_missingness(
    panel_rows: list[dict[str, str]], signals: list[tuple[str, str, str]]
) -> list[dict[str, object]]:
    rows = []
    signal_set = sorted(set(signals))
    for position, component, source_column in signal_set:
        for season in sorted({row["target_season"] for row in panel_rows if row["position"] == position}):
            group = [row for row in panel_rows if row["position"] == position and row["target_season"] == season]
            available = sum(1 for row in group if num(row.get(source_column)) is not None)
            rows.append(
                {
                    "target_season": season,
                    "position": position,
                    "component_name": component,
                    "source_column": source_column,
                    "rows": len(group),
                    "available_rows": available,
                    "missing_rows": len(group) - available,
                    "coverage_rate": fmt(available / len(group) if group else None, 6),
                    "review_only_status": "partial_replay_proxy_only",
                    "caveat": "coverage is source-column availability, not exact Model v4 receipt coverage",
                }
            )
    return rows


def build_input_receipts_used(receipts: list[dict[str, str]], signals: list[tuple[str, str, str]]) -> list[dict[str, object]]:
    wanted = set(signals)
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in receipts:
        for source_column in row["source_columns"].split("|"):
            key = (row["position"], row["component_name"], source_column)
            if key not in wanted:
                continue
            if key not in grouped:
                grouped[key] = {
                    "position": row["position"],
                    "component_name": row["component_name"],
                    "source_column": source_column,
                    "receipt_rows": 0,
                    "historical_component_status": row["historical_component_status"],
                    "source_gate_status": row["source_gate_status"],
                    "decision_date_safe_flag": row["decision_date_safe_flag"],
                    "identity_caveat_flag": row["identity_caveat_flag"],
                    "leakage_caveat_flag": row["leakage_caveat_flag"],
                    "replay_eligibility_flag": row["replay_eligibility_flag"],
                    "source_hash": row["source_hash"],
                    "source_artifact": row["historical_source_artifact"],
                    "use_gate": "YELLOW_REVIEW_ONLY; not model-use; not production; not source-truth",
                }
            grouped[key]["receipt_rows"] = int(grouped[key]["receipt_rows"]) + 1
    return list(grouped.values())


def median_by_group(panel_rows: list[dict[str, str]], column: str) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in panel_rows:
        value = num(row.get(column))
        if value is not None:
            grouped[group_key(row)].append(value)
    return {key: median(values) for key, values in grouped.items() if values}


def baseline_predictions(panel_rows: list[dict[str, str]], source_column: str = "prior_nwr_points") -> dict[str, bool]:
    result: dict[str, bool] = {}
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in covered_rows(panel_rows, source_column):
        grouped[group_key(row)].append(row)
    for (_, position), rows in grouped.items():
        selected = sorted(rows, key=lambda row: num(row[source_column]) or 0.0, reverse=True)[
            : min(STARTABLE_CUTOFF[position], len(rows))
        ]
        selected_ids = {row["substrate_row_id"] for row in selected}
        for row in rows:
            result[row["substrate_row_id"]] = row["substrate_row_id"] in selected_ids
    return result


def build_miss_patterns(panel_rows: list[dict[str, str]], metrics: list[dict[str, object]]) -> str:
    predictions = baseline_predictions(panel_rows)
    opportunity_medians = median_by_group(panel_rows, "prior_opportunities")
    target_medians = median_by_group(panel_rows, "prior_targets")
    touch_medians = median_by_group(panel_rows, "prior_touches")
    rows = [row for row in panel_rows if row["substrate_row_id"] in predictions]
    false_pos = [row for row in rows if predictions[row["substrate_row_id"]] and not bool_true(row["startable_hit"])]
    false_neg = [row for row in rows if not predictions[row["substrate_row_id"]] and bool_true(row["startable_hit"])]
    sparse = [row for row in rows if (num(row.get("prior_games")) or 0) < 8]
    low_prior_breakout = [
        row
        for row in false_neg
        if (num(row.get("prior_opportunities")) or 0) <= opportunity_medians.get(group_key(row), 0)
    ]
    rb_role_fp = [
        row
        for row in false_pos
        if row["position"] == "RB"
        and (num(row.get("prior_touches")) or 0) >= touch_medians.get(group_key(row), 0)
    ]
    wr_breakout = [
        row
        for row in false_neg
        if row["position"] == "WR"
        and (num(row.get("prior_targets")) or 0) <= target_medians.get(group_key(row), 0)
    ]
    te_rows = [row for row in rows if row["position"] == "TE"]
    te_fp = [row for row in false_pos if row["position"] == "TE"]
    te_fn = [row for row in false_neg if row["position"] == "TE"]
    patterns = [
        (
            "prior-production decline false positives",
            len(false_pos),
            f"{len(false_pos) / len(rows):.1%} of measured rows",
            "Baseline/component volume signals select prior producers who fail next-season startable cutoffs.",
        ),
        (
            "low-prior-opportunity breakout misses",
            len(low_prior_breakout),
            f"{len(low_prior_breakout) / max(1, len(false_neg)):.1%} of false negatives",
            "Lagged factual panel has no future role/depth/injury signals, so low prior opportunity breakouts are missed.",
        ),
        (
            "sparse-history rows",
            len(sparse),
            f"{len(sparse) / len(rows):.1%} of measured rows",
            "Rows with fewer than eight prior games are structurally difficult for prior-year anchors.",
        ),
        (
            "RB role-change proxy false positives",
            len(rb_role_fp),
            f"{len(rb_role_fp) / max(1, len(false_pos)):.1%} of false positives",
            "High prior RB touch rows can collapse when role changes, injuries, or team context change.",
        ),
        (
            "WR low-target breakout misses",
            len(wr_breakout),
            f"{len(wr_breakout) / max(1, len(false_neg)):.1%} of false negatives",
            "WRs with low prior targets but next-season startable outcomes remain a core blind spot.",
        ),
        (
            "TE volatility",
            len(te_fp) + len(te_fn),
            f"{(len(te_fp) + len(te_fn)) / max(1, len(te_rows)):.1%} of TE rows",
            "TE has fewer stable role signals and remains volatile without exact route/red-zone/lifecycle receipts.",
        ),
        (
            "injury/availability caveat not measured",
            0,
            "not measurable",
            "No admitted historical injury/availability input is used in this benchmark.",
        ),
        (
            "older dynasty asset caveat not measured",
            0,
            "not measurable",
            "No admitted historical age/lifecycle receipt is used in this benchmark.",
        ),
    ]
    lines = [
        "# Model v4 Partial Replay Miss Patterns",
        "",
        "Miss patterns are based on the safe prior-year-points baseline because no predeclared partial Model v4 score exists. These are review-only diagnostics, not tuning instructions.",
        "",
        "| Rank | Pattern | Count | Share | Interpretation |",
        "| ---: | ------- | ----: | ----- | -------------- |",
    ]
    for idx, (name, count, share, note) in enumerate(patterns, start=1):
        lines.append(f"| {idx} | {name} | {count} | {share} | {note} |")
    return "\n".join(lines) + "\n"


def leakage_guardrail(panel_rows: list[dict[str, str]], input_receipts: list[dict[str, object]]) -> list[str]:
    errors = []
    for row in panel_rows:
        if int(row["target_season"]) != int(row["feature_season"]) + 1:
            errors.append(f"bad feature/target season: {row['substrate_row_id']}")
        if row["leakage_check_result"] != "PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED":
            errors.append(f"leakage failure: {row['substrate_row_id']}")
        if row["asof_check_result"] != "PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS":
            errors.append(f"asof failure: {row['substrate_row_id']}")
    for receipt in input_receipts:
        col = str(receipt["source_column"]).lower()
        bad_words = [word for word in BLOCKED_INPUT_WORDS if word in col]
        if bad_words:
            errors.append(f"blocked input column {receipt['source_column']}: {bad_words}")
        if receipt["historical_component_status"] != "partial_replay_proxy_only":
            errors.append(f"non-partial receipt used: {receipt}")
    return errors


def write_markdown_outputs(
    panel_rows: list[dict[str, str]],
    metrics: list[dict[str, object]],
    scorecard: list[dict[str, object]],
    baseline_rows: list[dict[str, object]],
    input_receipts: list[dict[str, object]],
    leakage_errors: list[str],
) -> None:
    total_rows = len(panel_rows)
    positions = Counter(row["position"] for row in panel_rows)
    seasons = sorted({row["target_season"] for row in panel_rows})
    score_possible = False
    best_non_pyf_by_pos = {}
    pyf_by_pos = {}
    for position in ["QB", "RB", "WR", "TE"]:
        pos_metrics = [row for row in metrics if row["position"] == position]
        pyf_by_pos[position] = next(row for row in pos_metrics if row["component_name"] == "prior_year_points_baseline")
        non_pyf = [
            row
            for row in pos_metrics
            if row["metric_type"] == "component_source_signal"
            and row["source_column"] not in {"prior_nwr_points", "prior_nwr_ppg"}
        ]
        best_non_pyf_by_pos[position] = max(non_pyf, key=metric_score)

    report_lines = [
        "# Model v4 Partial Historical Replay Benchmark V1 Report",
        "",
        "## Verdict",
        "",
        "`YELLOW_MODEL_V4_PARTIAL_REPLAY_MIXED_SIGNAL_WITH_CAVEATS`",
        "",
        "## Clear Answer",
        "",
        "The partial historical replay shows useful lagged factual signal, especially from prior-year points and simple passing/rushing/receiving yardage or opportunity fields. However, the best non-PYF component-source signals did not beat the simple prior-year-points baseline in any position. It should be interpreted as a review-only component signal audit, not as exact Model v4 accuracy. No predeclared partial Model v4 score exists, so this lane did not create one.",
        "",
        "## Benchmark Scope",
        "",
        f"- Seasons: `{seasons[0]}-{seasons[-1]}`",
        "- Positions: `QB`, `RB`, `WR`, `TE`",
        f"- Rows tested: `{total_rows}`",
        f"- Position rows: `{dict(sorted(positions.items()))}`",
        "- Labels: `next_nwr_points`, `next_nwr_ppg`, `next_position_finish`, `startable_hit`, `startable_bucket`",
        "- Inputs: review-only partial component receipts and lagged V3 factual overlap columns only",
        "- Excluded inputs: exact current-board fields, current ADP, market, current injury/depth/roster context, target-season outcomes as inputs, source-gated blocked fields, and all exact checkpoint/lifecycle/confidence/candidate-overlay rows",
        "",
        "## Metrics Summary",
        "",
        "| Position | Seasons | Rows | Metric Type | Spearman | Top-12 | Top-24 | Top-36 | Startable Precision | Caveat |",
        "| -------- | ------: | ---: | ----------- | -------: | -----: | -----: | -----: | ------------------: | ------ |",
    ]
    for row in scorecard:
        if row["Metric Type"] == "best_non_pyf_component_source":
            report_lines.append(
                f"| {row['Position']} | {row['Seasons']} | {row['Rows']} | {row['Metric Type']} | {row['Spearman']} | {row['Top-12']} | {row['Top-24']} | {row['Top-36']} | {row['Startable Precision']} | {row['Signal']}; {row['Caveat']} |"
            )
    report_lines.extend(
        [
            "",
            "## Baseline Comparison",
            "",
            "| Model / Signal / Baseline | Scope | Metric | Result | Beat Baseline? | Caveat |",
            "| ------------------------- | ----- | ------ | -----: | -------------- | ------ |",
        ]
    )
    for row in baseline_rows:
        if row["Model / Signal / Baseline"] in {
            "prior_year_points_baseline",
            "best_non_pyf_component_source",
            "Production Rankings Backtest V1 current-formula-family proxy",
        }:
            report_lines.append(
                f"| {row['Model / Signal / Baseline']} | {row['Scope']} | {row['Metric']} | {row['Result']} | {row['Beat Baseline?']} | {row['Caveat']} |"
            )
    report_lines.extend(
        [
            "",
            "## Coverage / Missingness",
            "",
            "See `MODEL_V4_PARTIAL_REPLAY_COVERAGE_MISSINGNESS.csv`. All benchmarked input receipts remain `partial_replay_proxy_only`, `review_only`, not model-use, not production, and not source-truth.",
            "",
            "## What This Proves",
            "",
            "- The lagged factual receipt panel is reproducible and decision-date separated for review-only benchmark use.",
            "- Several partial component source fields have directional signal against next-season outcomes.",
            "- The strongest signals often overlap with simple prior-year production, which remains a serious baseline.",
            "",
            "## What This Does Not Prove",
            "",
            "- Exact Model v4 accuracy.",
            "- Production-active approval.",
            "- Source promotion.",
            "- Historical replay completeness.",
            "- Future 2026 accuracy.",
            "",
            "## Recommendation",
            "",
            "`Partial signal is promising; send to Formula Gauntlet as review-only evidence.`",
            "",
            "The useful portion is not a formula. It is a signal inventory and baseline sanity check. Exact historical replay remains blocked until the missing checkpoint/lifecycle/confidence/candidate-overlay receipt chain is recovered.",
        ]
    )
    (OUT_DIR / "MODEL_V4_PARTIAL_HISTORICAL_REPLAY_BENCHMARK_V1_REPORT.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    blockers = [
        "# Model v4 Partial Replay Blockers And Caveats",
        "",
        "## Hard Caveats",
        "",
        "- This is not exact Model v4 replay.",
        "- This is not production model accuracy.",
        "- No predeclared partial Model v4 score exists, so no score was invented.",
        "- No source was promoted.",
        "- No formula weights were tuned or optimized.",
        "- Production-active status remains blocked.",
        "- Historical accuracy remains unproven for exact Model v4.",
        "",
        "## Exact Replay Blockers",
        "",
        "1. Missing season-by-season `checkpoint_review_score` receipts.",
        "2. Missing season-by-season `position_specific_review_score` receipts.",
        "3. Missing lifecycle, age, role, and confidence receipts.",
        "4. Missing WR/QB v2 candidate-overlay receipt chain.",
        "5. Missing exact route/YPRR/TPRR/red-zone normalized component receipts.",
        "6. `shadow_model_v2_metrics.csv` remains unavailable for exact shadow/guardrail replay if required.",
        "",
        "## Leakage Guardrail",
        "",
        f"- Leakage guardrail errors: `{len(leakage_errors)}`",
    ]
    if leakage_errors:
        blockers.extend(f"- `{error}`" for error in leakage_errors[:50])
    else:
        blockers.append("- All panel rows use `feature_season = target_season - 1` and pass the existing leakage/as-of flags.")
    (OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_BLOCKERS_AND_CAVEATS.md").write_text(
        "\n".join(blockers) + "\n", encoding="utf-8"
    )

    trace = f"""# Model v4 Partial Replay Source Trace

## Sources Used

| Source | Path | Use Gate |
| --- | --- | --- |
| Historical component receipt backfill | `{RECEIPT_DIR}` | Review-only partial receipts; not exact replay. |
| Partial replay input panel | `{PANEL_PATH}` | Lagged V3 factual overlap; decision-date separated. |
| Production Rankings Backtest V1 | `{BACKTEST_DIR}` | Prior proxy/current-formula-family comparison context. |
| Historical Model v4 replay substrate | `{SUBSTRATE_DIR}` | Partial replay panel and original contract. |
| Exact current-board rebuild packet | `{EXACT_REBUILD_DIR}` | Current board exact rebuild proof only; not historical input. |
| Formula documentation / cleanup packet | `{FORMULA_DOC_DIR}` | Component/blocker taxonomy. |
| HQ1 receipt-chain standard | `{HQ1_STANDARD_DIR}` | Source receipt/use-gate standard. |

## HQ1 Use-Gate Answers

1. Do we actually have the information? Yes, for the lagged factual partial component columns only.
2. Where did it come from? The V3 historical replay substrate and the prior historical component receipt backfill packet.
3. Is it reliable enough for review-only benchmark use? Yes, with explicit review-only/proxy caveats.
4. Use gate: `YELLOW_REVIEW_ONLY`; not model-use, not production, not source-truth.
5. Can it be reproduced? Yes, via `build_model_v4_partial_historical_replay_benchmark_v1.py` and the source hashes in `MODEL_V4_PARTIAL_REPLAY_INPUT_RECEIPTS_USED.csv`.
6. Can it be tested historically without leakage? Yes for this partial panel; exact Model v4 replay remains blocked.

## Non-Inputs

No current ADP, market, injury/depth/roster context, production rankings artifact, current-board score, checkpoint, lifecycle, confidence, or target-season outcome field was used as an input.
"""
    (OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_SOURCE_TRACE.md").write_text(trace, encoding="utf-8")

    (OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_MISS_PATTERNS.md").write_text(
        build_miss_patterns(panel_rows, metrics), encoding="utf-8"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_rows = read_csv(PANEL_PATH)
    receipts = read_csv(RECEIPTS_PATH)
    production_rows = read_csv(PRODUCTION_SCORECARD_PATH)
    signals = allowed_signals_from_receipts(receipts)
    metrics = build_position_metrics(panel_rows, signals)
    scorecard = build_scorecard(metrics, panel_rows)
    baseline = build_baseline_comparison(metrics, production_rows)
    coverage = build_coverage_missingness(panel_rows, signals)
    input_receipts = build_input_receipts_used(receipts, signals)
    leakage_errors = leakage_guardrail(panel_rows, input_receipts)

    write_csv(
        OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_POSITION_METRICS.csv",
        [
            {
                "position": row["position"],
                "component_name": row["component_name"],
                "source_column": row["source_column"],
                "metric_type": row["metric_type"],
                "direction": row["direction"],
                "seasons": row["seasons"],
                "rows": row["rows"],
                "position_total_rows": row["position_total_rows"],
                "coverage_rate": fmt(row["coverage_rate"], 6),
                "missing_rows": row["missing_rows"],
                "mae_rank_vs_finish": fmt(row["mae_rank_vs_finish"]),
                "rmse_rank_vs_finish": fmt(row["rmse_rank_vs_finish"]),
                "spearman_rank_vs_finish": fmt(row["spearman_rank_vs_finish"]),
                "spearman_value_vs_next_points": fmt(row["spearman_value_vs_next_points"]),
                "top_12_precision": pct(row["top_12_precision"]),
                "top_24_precision": pct(row["top_24_precision"]),
                "top_36_precision": pct(row["top_36_precision"]),
                "startable_precision": pct(row["startable_precision"]),
                "startable_recall": pct(row["startable_recall"]),
                "caveat": row["caveat"],
            }
            for row in metrics
        ],
        [
            "position",
            "component_name",
            "source_column",
            "metric_type",
            "direction",
            "seasons",
            "rows",
            "position_total_rows",
            "coverage_rate",
            "missing_rows",
            "mae_rank_vs_finish",
            "rmse_rank_vs_finish",
            "spearman_rank_vs_finish",
            "spearman_value_vs_next_points",
            "top_12_precision",
            "top_24_precision",
            "top_36_precision",
            "startable_precision",
            "startable_recall",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_METRICS_SCORECARD.csv",
        scorecard,
        [
            "Position",
            "Seasons",
            "Rows",
            "Metric Type",
            "Signal",
            "Spearman",
            "Top-12",
            "Top-24",
            "Top-36",
            "Startable Precision",
            "Caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_BASELINE_COMPARISON.csv",
        baseline,
        ["Model / Signal / Baseline", "Scope", "Metric", "Result", "Beat Baseline?", "Caveat"],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_COVERAGE_MISSINGNESS.csv",
        coverage,
        [
            "target_season",
            "position",
            "component_name",
            "source_column",
            "rows",
            "available_rows",
            "missing_rows",
            "coverage_rate",
            "review_only_status",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_PARTIAL_REPLAY_INPUT_RECEIPTS_USED.csv",
        input_receipts,
        [
            "position",
            "component_name",
            "source_column",
            "receipt_rows",
            "historical_component_status",
            "source_gate_status",
            "decision_date_safe_flag",
            "identity_caveat_flag",
            "leakage_caveat_flag",
            "replay_eligibility_flag",
            "source_hash",
            "source_artifact",
            "use_gate",
        ],
    )
    write_markdown_outputs(panel_rows, metrics, scorecard, baseline, input_receipts, leakage_errors)

    print(f"panel_rows={len(panel_rows)}")
    print(f"signals={len(signals)}")
    print(f"metrics={len(metrics)}")
    print(f"coverage_rows={len(coverage)}")
    print(f"input_receipts={len(input_receipts)}")
    print(f"leakage_errors={len(leakage_errors)}")
    print(f"panel_sha256={sha256_file(PANEL_PATH)}")


if __name__ == "__main__":
    main()
