from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

BOARD_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/"
    "historical_rookie_tuning_board_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_rookie_tuning/latest")
DOC_PATH = Path("docs/model_v4/MODEL_V4_3_7_ROOKIE_SHADOW_FORMULA_EXPERIMENT.md")
VERSION = "model_v4_3_7_rookie_shadow_formula_experiment_0.1.0"

VARIANTS = (
    "current_model",
    "capital_anchor_variant",
    "confidence_cap_variant",
    "day_three_wr_skepticism_variant",
    "te_no_premium_cap_variant",
    "combined_conservative_variant",
    "draft_capital_only_benchmark",
    "simple_hybrid_benchmark",
)

ROW_HEADER = (
    "cohort",
    "draft_year",
    "variant_name",
    "variant_rank",
    "player",
    "position",
    "draft_round",
    "overall_pick",
    "variant_score",
    "current_model_score",
    "draft_capital_score",
    "production_score",
    "college_team_share",
    "athletic_score",
    "confidence_cap",
    "evidence_available",
    "outcome_category",
    "outcome_maturity",
    "broad_outcome_hit",
    "strict_starter_hit",
    "difference_maker",
    "variant_notes",
    "promoted_to_active_model",
    "formula_version",
)

SUMMARY_HEADER = (
    "cohort",
    "variant_name",
    "window",
    "rows",
    "broad_hits",
    "broad_hit_rate",
    "strict_starter_hits",
    "strict_starter_hit_rate",
    "difference_makers",
    "difference_maker_capture_rate",
    "benchmark_read",
    "promoted_to_active_model",
    "formula_version",
)

MOVEMENT_HEADER = (
    "cohort",
    "draft_year",
    "variant_name",
    "player",
    "position",
    "current_rank",
    "variant_rank",
    "rank_delta",
    "current_model_score",
    "variant_score",
    "outcome_category",
    "movement_reason",
    "formula_version",
)


@dataclass(frozen=True)
class RookieShadowFormulaExperimentResult:
    variant_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    movement_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_rookie_shadow_formula_experiment(
    board_rows_path: str | Path = BOARD_ROWS_PATH,
) -> RookieShadowFormulaExperimentResult:
    source_rows = [row for row in _read_rows(Path(board_rows_path)) if _cohort(row)]
    variant_rows: list[dict[str, object]] = []
    for variant in VARIANTS:
        variant_rows.extend(_ranked_variant_rows(variant, source_rows))
    summary_rows = tuple(_summary_rows(variant_rows))
    movement_rows = tuple(_movement_rows(variant_rows))
    doc_text = _doc_text(summary_rows)
    return RookieShadowFormulaExperimentResult(
        variant_rows=tuple(variant_rows),
        summary_rows=summary_rows,
        movement_rows=movement_rows,
        doc_text=doc_text,
    )


def write_rookie_shadow_formula_experiment_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: RookieShadowFormulaExperimentResult | None = None,
) -> dict[str, Path]:
    result = result or build_rookie_shadow_formula_experiment()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    rows_path = output / "rookie_shadow_formula_variant_rows.csv"
    summary_path = output / "rookie_shadow_formula_variant_summary.csv"
    movement_path = output / "rookie_shadow_formula_player_movement.csv"
    _write_csv(rows_path, ROW_HEADER, result.variant_rows)
    _write_csv(summary_path, SUMMARY_HEADER, result.summary_rows)
    _write_csv(movement_path, MOVEMENT_HEADER, result.movement_rows)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(result.doc_text, encoding="utf-8")
    return {"rows": rows_path, "summary": summary_path, "movement": movement_path, "doc": doc}


def _ranked_variant_rows(variant: str, rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for cohort in ("mature_2021_2023", "partial_2024", "rookie_shadow_2025"):
        cohort_rows = [row for row in rows if _cohort(row) == cohort]
        years = sorted({_int(row.get("Draft Year")) for row in cohort_rows})
        for year in years:
            year_rows = [row for row in cohort_rows if _int(row.get("Draft Year")) == year]
            scored = [(row, *_variant_score(variant, row)) for row in year_rows]
            ranked = sorted(
                scored,
                key=lambda item: (
                    item[1] is None,
                    -float(item[1] or 0.0),
                    _int(item[0].get("Overall Pick")) or 999,
                    str(item[0].get("Player", "")).lower(),
                ),
            )
            for rank, (row, score, notes) in enumerate(ranked, start=1):
                output.append(_variant_row(cohort, year, variant, rank, row, score, notes))
    return output


def _variant_score(variant: str, row: dict[str, str]) -> tuple[float | None, str]:
    current = _float_or_none(row.get("Final Score"))
    draft = _float_or_none(row.get("NFL Draft Pick Signal"))
    production = _float_or_none(row.get("Production Score"))
    share = _float_or_none(row.get("College Team Share"))
    athletic = _float_or_none(row.get("Athletic Score"))
    evidence = _float(row.get("Evidence Available"))
    confidence = _float(row.get("Confidence Cap"), 1.0)
    position = str(row.get("Pos", ""))
    draft_round = _int(row.get("Draft Round")) or 99
    notes: list[str] = []

    if variant == "current_model":
        return current, "current_model_reference"
    if variant == "draft_capital_only_benchmark":
        return draft, "benchmark_not_formula_variant"
    if variant == "simple_hybrid_benchmark":
        return _weighted_available(((draft, 0.55), (production, 0.3), (share, 0.15))), (
            "benchmark_not_formula_variant"
        )
    if current is None:
        return None, "missing_current_model_score"

    score = current
    if variant in {"capital_anchor_variant", "combined_conservative_variant"}:
        anchored = _weighted_available(
            ((draft, 0.58), (production, 0.18), (share, 0.09), (athletic, 0.08), (current, 0.07))
        )
        if anchored is not None:
            score = anchored
            notes.append("capital_anchor_applied")

    if variant in {"confidence_cap_variant", "combined_conservative_variant"}:
        new_confidence = _shadow_confidence_cap(evidence, confidence)
        if confidence > 0:
            score = score / confidence * new_confidence
        notes.append(f"shadow_confidence_cap={new_confidence}")

    if variant in {"day_three_wr_skepticism_variant", "combined_conservative_variant"}:
        if position == "WR" and draft_round >= 4:
            score -= 10.0 if draft_round == 4 else 14.0
            notes.append("day_three_wr_skepticism_applied")

    if variant in {"te_no_premium_cap_variant", "combined_conservative_variant"}:
        if position == "TE":
            pick = _int(row.get("Overall Pick")) or 999
            cap = 52.0 if pick <= 40 else 44.0 if pick <= 80 else 36.0
            if score > cap:
                score = cap
                notes.append(f"no_premium_te_cap={cap}")

    return round(max(score, 0.0), 4), "|".join(notes) or "shadow_variant_no_adjustment"


def _shadow_confidence_cap(evidence: float, current_confidence: float) -> float:
    cap = current_confidence
    if evidence < 0.4:
        cap = min(cap, 0.62)
    elif evidence < 0.7:
        cap = min(cap, 0.68)
    return cap


def _variant_row(
    cohort: str,
    year: int | None,
    variant: str,
    rank: int,
    row: dict[str, str],
    score: float | None,
    notes: str,
) -> dict[str, object]:
    return {
        "cohort": cohort,
        "draft_year": year,
        "variant_name": variant,
        "variant_rank": rank,
        "player": row.get("Player", ""),
        "position": row.get("Pos", ""),
        "draft_round": row.get("Draft Round", ""),
        "overall_pick": row.get("Overall Pick", ""),
        "variant_score": _blank(score),
        "current_model_score": row.get("Final Score", ""),
        "draft_capital_score": row.get("NFL Draft Pick Signal", ""),
        "production_score": row.get("Production Score", ""),
        "college_team_share": row.get("College Team Share", ""),
        "athletic_score": row.get("Athletic Score", ""),
        "confidence_cap": row.get("Confidence Cap", ""),
        "evidence_available": row.get("Evidence Available", ""),
        "outcome_category": row.get("Outcome Category", ""),
        "outcome_maturity": row.get("Outcome Maturity", ""),
        "broad_outcome_hit": row.get("Broad Outcome Hit?", ""),
        "strict_starter_hit": row.get("Strict Starter Hit?", ""),
        "difference_maker": row.get("Difference Maker?", ""),
        "variant_notes": notes,
        "promoted_to_active_model": False,
        "formula_version": VERSION,
    }


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for cohort in sorted({str(row["cohort"]) for row in rows}):
        cohort_rows = [row for row in rows if row["cohort"] == cohort]
        for variant in VARIANTS:
            variant_rows = [row for row in cohort_rows if row["variant_name"] == variant]
            for window in (5, 10, 20):
                top = [row for row in variant_rows if int(row["variant_rank"]) <= window]
                if top:
                    output.append(_summary_row(cohort, variant, f"Top {window}", top))
    return output


def _summary_row(
    cohort: str, variant: str, window: str, rows: list[dict[str, object]]
) -> dict[str, object]:
    broad = [row for row in rows if _bool(row["broad_outcome_hit"])]
    strict = [row for row in rows if _bool(row["strict_starter_hit"])]
    diff = [row for row in rows if _bool(row["difference_maker"])]
    return {
        "cohort": cohort,
        "variant_name": variant,
        "window": window,
        "rows": len(rows),
        "broad_hits": len(broad),
        "broad_hit_rate": _rate(len(broad), len(rows)),
        "strict_starter_hits": len(strict),
        "strict_starter_hit_rate": _rate(len(strict), len(rows)),
        "difference_makers": len(diff),
        "difference_maker_capture_rate": _rate(len(diff), len(rows)),
        "benchmark_read": _benchmark_read(cohort, variant, window),
        "promoted_to_active_model": False,
        "formula_version": VERSION,
    }


def _movement_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    current_rank = {
        (row["cohort"], row["draft_year"], row["player"]): int(row["variant_rank"])
        for row in rows
        if row["variant_name"] == "current_model"
    }
    output: list[dict[str, object]] = []
    for row in rows:
        variant = str(row["variant_name"])
        if variant == "current_model":
            continue
        key = (row["cohort"], row["draft_year"], row["player"])
        old_rank = current_rank.get(key)
        if old_rank is None:
            continue
        new_rank = int(row["variant_rank"])
        delta = old_rank - new_rank
        if abs(delta) < 5:
            continue
        output.append(
            {
                "cohort": row["cohort"],
                "draft_year": row["draft_year"],
                "variant_name": variant,
                "player": row["player"],
                "position": row["position"],
                "current_rank": old_rank,
                "variant_rank": new_rank,
                "rank_delta": delta,
                "current_model_score": row["current_model_score"],
                "variant_score": row["variant_score"],
                "outcome_category": row["outcome_category"],
                "movement_reason": row["variant_notes"],
                "formula_version": VERSION,
            }
        )
    return sorted(
        output,
        key=lambda item: (
            str(item["cohort"]),
            str(item["variant_name"]),
            -abs(int(item["rank_delta"])),
        ),
    )


def _doc_text(summary_rows: tuple[dict[str, object], ...]) -> str:
    mature_top20 = [
        row
        for row in summary_rows
        if row["cohort"] == "mature_2021_2023" and row["window"] == "Top 20"
    ]
    best = max(
        mature_top20,
        key=lambda row: (
            float(row["strict_starter_hit_rate"]),
            int(row["difference_makers"]),
            float(row["broad_hit_rate"]),
        ),
    )
    lines = [
        "# Model v4.3.7 Rookie Shadow Formula Experiment",
        "",
        "## Scope",
        "",
        "This is a shadow-only experiment. No variant is promoted and no Draft Room "
        "rankings changed.",
        "",
        "## Mature Top 20 Read",
        "",
        f"Best mature Top 20 variant by strict starter rate: `{best['variant_name']}`.",
        "",
        "| Variant | Broad Hit Rate | Strict Starter Hit Rate | Difference Makers |",
        "|---|---:|---:|---:|",
    ]
    for row in mature_top20:
        lines.append(
            "| {variant_name} | {broad_hit_rate} | {strict_starter_hit_rate} | "
            "{difference_makers} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Shadow-only outputs.",
            "- No active rankings, My Team, War Board, readiness gates, or app promotion changed.",
            "- Benchmarks are included for evaluation only.",
            "- 2024 and 2025 are shadow cohorts and should not drive final tuning alone.",
        ]
    )
    return "\n".join(lines) + "\n"


def _cohort(row: dict[str, str]) -> str:
    if not _bool(row.get("Fantasy-Relevant Replay Pool")):
        return ""
    year = _int(row.get("Draft Year"))
    maturity = row.get("Outcome Maturity")
    if year in {2021, 2022, 2023} and maturity == "three_year_window_available":
        return "mature_2021_2023"
    if year == 2024 and maturity == "partial_two_year_window":
        return "partial_2024"
    if year == 2025 and maturity == "rookie_year_only":
        return "rookie_shadow_2025"
    return ""


def _benchmark_read(cohort: str, variant: str, window: str) -> str:
    if variant.endswith("_benchmark"):
        return "benchmark_not_candidate"
    if cohort != "mature_2021_2023":
        return "shadow_context_not_final_judgment"
    return f"candidate_evaluated_against_benchmarks_{window.lower().replace(' ', '_')}"


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


def _weighted_available(values: tuple[tuple[float | None, float], ...]) -> float | None:
    available = [(value, weight) for value, weight in values if value is not None]
    if not available:
        return None
    total_weight = sum(weight for _, weight in available)
    return round(sum(float(value) * weight for value, weight in available) / total_weight, 4)


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


def _float(value: object, default: float = 0.0) -> float:
    value_or_none = _float_or_none(value)
    return default if value_or_none is None else value_or_none


def _float_or_none(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _rate(numerator: int, denominator: int) -> float | str:
    return round(numerator / denominator, 3) if denominator else ""
