from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

BOARD_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/"
    "historical_rookie_tuning_board_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_rookie_tuning/latest")
DOC_PATH = Path("docs/model_v4/MODEL_V4_3_6_ROOKIE_REPLAY_BASELINE_COMPARISON.md")
VERSION = "model_v4_3_6_rookie_replay_baseline_comparison_0.1.0"

BASELINES = (
    "current_model_score",
    "draft_capital_only",
    "production_team_share_only",
    "simple_hybrid_capital_plus_production",
)

COMPARISON_HEADER = (
    "baseline_name",
    "draft_year",
    "baseline_rank",
    "player",
    "position",
    "draft_round",
    "overall_pick",
    "baseline_score",
    "current_model_score",
    "draft_capital_score",
    "production_score",
    "college_team_share",
    "outcome_category",
    "broad_outcome_hit",
    "strict_starter_hit",
    "difference_maker",
    "score_missing",
    "formula_version",
)

SUMMARY_HEADER = (
    "baseline_name",
    "draft_year",
    "window",
    "rows",
    "broad_hits",
    "broad_hit_rate",
    "strict_starter_hits",
    "strict_starter_hit_rate",
    "difference_makers",
    "difference_maker_capture_rate",
    "verdict_context",
    "formula_version",
)

POSITION_SUMMARY_HEADER = (
    "baseline_name",
    "position",
    "window",
    "rows",
    "broad_hits",
    "broad_hit_rate",
    "strict_starter_hits",
    "strict_starter_hit_rate",
    "difference_makers",
    "difference_maker_capture_rate",
    "formula_version",
)


@dataclass(frozen=True)
class RookieReplayBaselineComparisonResult:
    comparison_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    by_position_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_rookie_replay_baseline_comparison(
    board_rows_path: str | Path = BOARD_ROWS_PATH,
) -> RookieReplayBaselineComparisonResult:
    rows = [row for row in _read_rows(Path(board_rows_path)) if _is_primary_replay_row(row)]
    comparison_rows: list[dict[str, object]] = []
    for baseline in BASELINES:
        comparison_rows.extend(_ranked_rows_for_baseline(baseline, rows))

    summary_rows = tuple(_summary_rows(comparison_rows))
    by_position_rows = tuple(_by_position_rows(comparison_rows))
    doc_text = _doc_text(rows, summary_rows, by_position_rows)
    return RookieReplayBaselineComparisonResult(
        comparison_rows=tuple(comparison_rows),
        summary_rows=summary_rows,
        by_position_rows=by_position_rows,
        doc_text=doc_text,
    )


def write_rookie_replay_baseline_comparison_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: RookieReplayBaselineComparisonResult | None = None,
) -> dict[str, Path]:
    result = result or build_rookie_replay_baseline_comparison()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    comparison_path = output / "rookie_replay_baseline_comparison_rows.csv"
    summary_path = output / "rookie_replay_baseline_summary.csv"
    position_path = output / "rookie_replay_by_position_baseline_summary.csv"
    _write_csv(comparison_path, COMPARISON_HEADER, result.comparison_rows)
    _write_csv(summary_path, SUMMARY_HEADER, result.summary_rows)
    _write_csv(position_path, POSITION_SUMMARY_HEADER, result.by_position_rows)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(result.doc_text, encoding="utf-8")
    return {
        "comparison": comparison_path,
        "summary": summary_path,
        "by_position": position_path,
        "doc": doc,
    }


def _ranked_rows_for_baseline(
    baseline: str,
    rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    years = sorted(
        {_int(row.get("Draft Year")) for row in rows if _int(row.get("Draft Year"))}
    )
    for year in years:
        year_rows = [row for row in rows if _int(row.get("Draft Year")) == year]
        scored = [
            (row, _baseline_score(baseline, row))
            for row in year_rows
        ]
        ranked = sorted(
            scored,
            key=lambda item: (
                item[1] is None,
                -float(item[1] or 0.0),
                _int(item[0].get("Overall Pick")) or 999,
                str(item[0].get("Player", "")).lower(),
            ),
        )
        for rank, (row, score) in enumerate(ranked, start=1):
            output.append(
                {
                    "baseline_name": baseline,
                    "draft_year": year,
                    "baseline_rank": rank,
                    "player": row.get("Player", ""),
                    "position": row.get("Pos", ""),
                    "draft_round": row.get("Draft Round", ""),
                    "overall_pick": row.get("Overall Pick", ""),
                    "baseline_score": _blank(score),
                    "current_model_score": row.get("Final Score", ""),
                    "draft_capital_score": row.get("NFL Draft Pick Signal", ""),
                    "production_score": row.get("Production Score", ""),
                    "college_team_share": row.get("College Team Share", ""),
                    "outcome_category": row.get("Outcome Category", ""),
                    "broad_outcome_hit": row.get("Broad Outcome Hit?", ""),
                    "strict_starter_hit": row.get("Strict Starter Hit?", ""),
                    "difference_maker": row.get("Difference Maker?", ""),
                    "score_missing": score is None,
                    "formula_version": VERSION,
                }
            )
    return output


def _baseline_score(baseline: str, row: dict[str, str]) -> float | None:
    current = _float_or_none(row.get("Final Score"))
    draft = _float_or_none(row.get("NFL Draft Pick Signal"))
    production = _float_or_none(row.get("Production Score"))
    team_share = _float_or_none(row.get("College Team Share"))
    if baseline == "current_model_score":
        return current
    if baseline == "draft_capital_only":
        return draft
    if baseline == "production_team_share_only":
        return _weighted_available(((production, 0.6), (team_share, 0.4)))
    if baseline == "simple_hybrid_capital_plus_production":
        return _weighted_available(((draft, 0.55), (production, 0.3), (team_share, 0.15)))
    raise ValueError(f"Unknown baseline: {baseline}")


def _weighted_available(values: tuple[tuple[float | None, float], ...]) -> float | None:
    available = [(value, weight) for value, weight in values if value is not None]
    if not available:
        return None
    total_weight = sum(weight for _, weight in available)
    return round(sum(float(value) * weight for value, weight in available) / total_weight, 4)


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    years = sorted({int(row["draft_year"]) for row in rows})
    for baseline in BASELINES:
        baseline_rows = [row for row in rows if row["baseline_name"] == baseline]
        for year_key, year_rows in [("all_mature_years", baseline_rows)] + [
            (year, [row for row in baseline_rows if row["draft_year"] == year])
            for year in years
        ]:
            for window in (5, 10, 20):
                top = [row for row in year_rows if int(row["baseline_rank"]) <= window]
                if not top:
                    continue
                output.append(_summary_row(baseline, year_key, f"Top {window}", top))
    return output


def _summary_row(
    baseline: str,
    draft_year: int | str,
    window: str,
    rows: list[dict[str, object]],
) -> dict[str, object]:
    broad = [row for row in rows if _bool(row["broad_outcome_hit"])]
    strict = [row for row in rows if _bool(row["strict_starter_hit"])]
    difference = [row for row in rows if _bool(row["difference_maker"])]
    return {
        "baseline_name": baseline,
        "draft_year": draft_year,
        "window": window,
        "rows": len(rows),
        "broad_hits": len(broad),
        "broad_hit_rate": _rate(len(broad), len(rows)),
        "strict_starter_hits": len(strict),
        "strict_starter_hit_rate": _rate(len(strict), len(rows)),
        "difference_makers": len(difference),
        "difference_maker_capture_rate": _rate(len(difference), len(rows)),
        "verdict_context": "review_only_baseline_not_formula_tuning",
        "formula_version": VERSION,
    }


def _by_position_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for baseline in BASELINES:
        baseline_rows = [row for row in rows if row["baseline_name"] == baseline]
        for position in sorted({str(row["position"]) for row in baseline_rows}):
            position_rows = [row for row in baseline_rows if row["position"] == position]
            for window in (10, 20, 50):
                top = [row for row in position_rows if int(row["baseline_rank"]) <= window]
                if not top:
                    continue
                summary = _summary_row(baseline, "all_mature_years", f"Top {window}", top)
                output.append(
                    {
                        "baseline_name": baseline,
                        "position": position,
                        "window": f"Top {window}",
                        "rows": summary["rows"],
                        "broad_hits": summary["broad_hits"],
                        "broad_hit_rate": summary["broad_hit_rate"],
                        "strict_starter_hits": summary["strict_starter_hits"],
                        "strict_starter_hit_rate": summary["strict_starter_hit_rate"],
                        "difference_makers": summary["difference_makers"],
                        "difference_maker_capture_rate": summary["difference_maker_capture_rate"],
                        "formula_version": VERSION,
                    }
                )
    return output


def _doc_text(
    primary_rows: list[dict[str, str]],
    summary_rows: tuple[dict[str, object], ...],
    by_position_rows: tuple[dict[str, object], ...],
) -> str:
    verdict = _verdict(summary_rows)
    lines = [
        "# Model v4.3.6 Rookie Replay Baseline Comparison",
        "",
        "## Scope",
        "",
        "Primary analysis uses mature 2021-2023 rows only where "
        "`Fantasy-Relevant Replay Pool == True` and outcome maturity is "
        "`three_year_window_available`.",
        "",
        "No formula weights were changed.",
        "",
        "## Dataset",
        "",
        f"- Mature fantasy-relevant rows: {len(primary_rows)}",
        "- Baselines: current model, draft capital only, production/team-share only, "
        "simple hybrid capital plus production",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Aggregate Summary",
        "",
        "| Baseline | Window | Broad Hit Rate | Strict Starter Hit Rate | Difference Makers |",
        "|---|---|---:|---:|---:|",
    ]
    aggregate_rows = [row for row in summary_rows if row["draft_year"] == "all_mature_years"]
    for row in aggregate_rows:
        lines.append(
            "| {baseline_name} | {window} | {broad_hit_rate} | "
            "{strict_starter_hit_rate} | {difference_makers} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## By-Position Notes",
            "",
            "| Baseline | Position | Window | Broad Hit Rate | Strict Starter Hit Rate |",
            "|---|---|---|---:|---:|",
        ]
    )
    for row in by_position_rows:
        if row["window"] != "Top 20":
            continue
        lines.append(
            "| {baseline_name} | {position} | {window} | {broad_hit_rate} | "
            "{strict_starter_hit_rate} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This is a replay evaluation layer, not formula tuning.",
            "- Market-only baseline is future work and is not used for private value.",
            "- No active rankings, My Team, War Board, readiness gates, or app promotion changed.",
        ]
    )
    return "\n".join(lines) + "\n"


def _verdict(summary_rows: tuple[dict[str, object], ...]) -> str:
    aggregate = {
        (row["baseline_name"], row["window"]): row
        for row in summary_rows
        if row["draft_year"] == "all_mature_years"
    }
    current = aggregate.get(("current_model_score", "Top 20"))
    draft = aggregate.get(("draft_capital_only", "Top 20"))
    if not current or not draft:
        return "Inconclusive because aggregate Top 20 rows are missing."
    current_strict = _float_or_none(current["strict_starter_hit_rate"]) or 0.0
    draft_strict = _float_or_none(draft["strict_starter_hit_rate"]) or 0.0
    current_diff = int(current["difference_makers"])
    draft_diff = int(draft["difference_makers"])
    if current_strict > draft_strict and current_diff >= draft_diff:
        return "Current model is better than draft capital only in aggregate Top 20 replay."
    if current_strict < draft_strict and current_diff <= draft_diff:
        return "Current model is worse than draft capital only in aggregate Top 20 replay."
    return "Current model is mixed versus draft capital only; inspect by-position summaries."


def _is_primary_replay_row(row: dict[str, str]) -> bool:
    return (
        _int(row.get("Draft Year")) in {2021, 2022, 2023}
        and _bool(row.get("Fantasy-Relevant Replay Pool"))
        and row.get("Outcome Maturity") == "three_year_window_available"
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _blank(value: float | None) -> float | str:
    return "" if value is None else round(value, 4)


def _bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def _int(value: object) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _float_or_none(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _rate(numerator: int, denominator: int) -> float | str:
    return round(numerator / denominator, 3) if denominator else ""
