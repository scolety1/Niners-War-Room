from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_sprint12_13_review_service import (
    _athletic_score,
    _draft_capital_score,
    _json,
    _market_share_score,
    _normalize_name,
    _production_score,
    _recruiting_score,
    _rookie_formula_balance_adjustment,
    _weighted_score,
)

HISTORICAL_BACKTEST_MATRIX = Path(
    "local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv"
)
HISTORICAL_OUTCOMES = Path(
    "local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv"
)
REPLAY_YEARS = (2021, 2022, 2023, 2024, 2025)
POSITION_FORMAT_FACTORS = {"RB": 1.08, "WR": 1.0, "TE": 0.86, "QB": 0.72}
COMPONENT_WEIGHTS = {
    "production": 0.30,
    "market_share": 0.20,
    "draft_capital": 0.25,
    "athletic_prior": 0.12,
    "recruiting_prior": 0.05,
    "age_lifecycle": 0.08,
}
VERSION = "model_v4_3_3_historical_rookie_tuning_0.1.0"


@dataclass(frozen=True)
class HistoricalRookieTuningReport:
    board_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    years: tuple[int, ...]
    source_path: str
    outcome_path: str


def build_historical_rookie_tuning_report(
    matrix_path: str | Path = HISTORICAL_BACKTEST_MATRIX,
    outcome_path: str | Path = HISTORICAL_OUTCOMES,
    *,
    years: tuple[int, ...] = REPLAY_YEARS,
) -> HistoricalRookieTuningReport:
    matrix = _read_rows(Path(matrix_path))
    outcome_lookup = _outcome_lookup(Path(outcome_path))
    rows: list[dict[str, object]] = []
    components: list[dict[str, object]] = []
    for row in matrix:
        draft_year = _int(row.get("draft_year"))
        position = str(row.get("position", ""))
        if draft_year not in years or position not in {"QB", "RB", "WR", "TE"}:
            continue
        scored = _score_historical_row(row, outcome_lookup)
        rows.append(scored["board_row"])
        components.extend(scored["component_rows"])

    ranked: list[dict[str, object]] = []
    for year in years:
        year_rows = [row for row in rows if row["Draft Year"] == year]
        year_rows = sorted(
            year_rows,
            key=lambda item: (
                -_float(item.get("Final Score"), 0.0),
                -_float(item.get("NFL Draft Pick Signal"), 0.0),
                str(item.get("Player", "")).lower(),
            ),
        )
        for rank, item in enumerate(year_rows, start=1):
            item["Rank"] = rank
            ranked.append(item)

    return HistoricalRookieTuningReport(
        board_rows=tuple(ranked),
        component_rows=tuple(components),
        summary_rows=tuple(_summary_rows(ranked, years)),
        years=years,
        source_path=str(matrix_path),
        outcome_path=str(outcome_path),
    )


def _score_historical_row(
    row: dict[str, str],
    outcome_lookup: dict[tuple[int, str], Any],
) -> dict[str, object]:
    position = str(row.get("position", ""))
    factual = _json(row.get("factual_evidence_json"))
    derived = _json(row.get("derived_evidence_json"))
    prior = _json(row.get("prospect_prior_evidence_json"))
    draft_capital = {
        "overall_pick": row.get("draft_pick", ""),
        "round": row.get("draft_round", ""),
    }
    production = _production_score(position, factual)
    market_share = _market_share_score(position, derived)
    draft_score = _draft_capital_score(draft_capital)
    athletic = _athletic_score(position, prior)
    recruiting = _recruiting_score(prior)
    age_score = None
    components = {
        "production": (production, COMPONENT_WEIGHTS["production"]),
        "market_share": (market_share, COMPONENT_WEIGHTS["market_share"]),
        "draft_capital": (draft_score, COMPONENT_WEIGHTS["draft_capital"]),
        "athletic_prior": (athletic, COMPONENT_WEIGHTS["athletic_prior"]),
        "recruiting_prior": (recruiting, COMPONENT_WEIGHTS["recruiting_prior"]),
        "age_lifecycle": (age_score, COMPONENT_WEIGHTS["age_lifecycle"]),
    }
    available = {name: value for name, value in components.items() if value[0] is not None}
    raw = _weighted_score(available) if available else None
    adjusted, labels = _rookie_formula_balance_adjustment(
        position=position,
        base_score=raw,
        production=production,
        market_share=market_share,
        draft_capital=draft_score,
        athletic=athletic,
        draft_capital_row=draft_capital,
    )
    confidence_cap = _confidence_cap(row, available)
    format_factor = POSITION_FORMAT_FACTORS.get(position, 1.0)
    final_score = (
        round(adjusted * confidence_cap * format_factor, 4)
        if adjusted is not None
        else None
    )
    outcome = outcome_lookup.get(
        (_int(row.get("draft_year")) or 0, _normalize_name(str(row.get("prospect_name", ""))))
    )
    outcome_category = _outcome_category(outcome)
    board_row = {
        "Draft Year": _int(row.get("draft_year")),
        "Rank": "",
        "Player": row.get("prospect_name", ""),
        "Pos": position,
        "NFL Team": row.get("nfl_team", ""),
        "College": row.get("college", ""),
        "Final Score": _blank_none(final_score),
        "Production Score": _blank_none(production),
        "College Team Share": _blank_none(market_share),
        "NFL Draft Pick Signal": _blank_none(draft_score),
        "Athletic Score": _blank_none(athletic),
        "Recruiting": _blank_none(recruiting),
        "Age Score": "",
        "Confidence Cap": confidence_cap,
        "Evidence Available": round(sum(weight for _, weight in available.values()), 4),
        "Trust Level": _trust_level(row, available),
        "Draft Round": row.get("draft_round", ""),
        "Overall Pick": row.get("draft_pick", ""),
        "Model Edge / Source Warning": "|".join(labels),
        "Fantasy-Relevant Replay Pool": _fantasy_relevant_replay_pool(position, draft_capital),
        "Outcome Loaded": outcome is not None,
        "Outcome Category": outcome_category,
        "Outcome Maturity": outcome.get("outcome_maturity", "") if outcome else "",
        "Broad Outcome Hit?": _broad_outcome_hit(outcome_category),
        "Strict Starter Hit?": _strict_starter_hit(outcome_category),
        "Difference Maker?": _difference_maker_hit(outcome_category),
        "Outcome Hit?": _broad_outcome_hit(outcome_category),
        "Best LVE PPG": outcome.get("best_3yr_ppg", "") if outcome else "",
        "Starter-Level Seasons": outcome.get("starter_level_seasons", "") if outcome else "",
        "Why This Rank": _why_text(
            row.get("prospect_name", ""),
            production,
            market_share,
            draft_score,
            athletic,
            labels,
            outcome is not None,
        ),
        "Warning Flags": row.get("warning_flags", ""),
        "Formula Version": VERSION,
    }
    component_rows = tuple(
        {
            "draft_year": _int(row.get("draft_year")),
            "player": row.get("prospect_name", ""),
            "position": position,
            "component": name,
            "score": _blank_none(value),
            "weight": weight,
            "available": value is not None,
            "source": "historical_rookie_backtest_feature_matrix",
            "formula_version": VERSION,
        }
        for name, (value, weight) in components.items()
    )
    return {"board_row": board_row, "component_rows": component_rows}


def _outcome_lookup(path: Path) -> dict[tuple[int, str], dict[str, str]]:
    if not path.exists():
        return {}
    return {
        (_int(row.get("draft_year")) or 0, _normalize_name(str(row.get("player", "")))): row
        for row in _read_rows(path)
    }


def _outcome_category(outcome: dict[str, str] | None) -> str:
    if outcome is None:
        return "not_loaded"
    return str(outcome.get("outcome_label", "not_loaded"))


def _broad_outcome_hit(category: str) -> bool:
    return any(marker in category for marker in ("usable", "starter", "difference_maker"))


def _strict_starter_hit(category: str) -> bool:
    return any(marker in category for marker in ("starter", "difference_maker"))


def _difference_maker_hit(category: str) -> bool:
    return "difference_maker" in category


def _summary_rows(rows: list[dict[str, object]], years: tuple[int, ...]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for year in years:
        year_rows = [row for row in rows if row["Draft Year"] == year]
        for universe, universe_rows in (
            ("all_offensive_drafted", year_rows),
            (
                "fantasy_relevant_replay_pool",
                [row for row in year_rows if row["Fantasy-Relevant Replay Pool"]],
            ),
        ):
            for window in (5, 10, 20, 40, 50):
                top = [row for row in universe_rows if int(row["Rank"]) <= window]
                if not top:
                    continue
                loaded = [row for row in top if row["Outcome Loaded"]]
                broad_hits = [row for row in loaded if row["Broad Outcome Hit?"]]
                strict_hits = [row for row in loaded if row["Strict Starter Hit?"]]
                difference_makers = [row for row in loaded if row["Difference Maker?"]]
                mature = [
                    row
                    for row in loaded
                    if row.get("Outcome Maturity") == "three_year_window_available"
                ]
                mature_strict_hits = [row for row in mature if row["Strict Starter Hit?"]]
                output.append(
                    {
                        "Draft Year": year,
                        "Universe": universe,
                        "Window": f"Top {window}",
                        "Rows": len(top),
                        "Outcome Loaded": len(loaded),
                        "Broad Hits": len(broad_hits),
                        "Broad Hit Rate": round(len(broad_hits) / len(loaded), 3)
                        if loaded
                        else "",
                        "Strict Starter Hits": len(strict_hits),
                        "Strict Starter Hit Rate": round(len(strict_hits) / len(loaded), 3)
                        if loaded
                        else "",
                        "Difference Makers": len(difference_makers),
                        "Mature Loaded": len(mature),
                        "Mature Strict Hit Rate": round(len(mature_strict_hits) / len(mature), 3)
                        if mature
                        else "",
                        "Future Stats Used In Ranking": False,
                        "Notes": _summary_note(loaded),
                    }
                )
    return output


def _fantasy_relevant_replay_pool(position: str, draft_capital: dict[str, object]) -> bool:
    pick = _int(draft_capital.get("overall_pick"))
    if pick is None:
        return False
    if position in {"RB", "WR"}:
        return pick <= 180
    if position == "TE":
        return pick <= 100
    if position == "QB":
        return pick <= 64
    return False


def _summary_note(loaded: list[dict[str, object]]) -> str:
    if not loaded:
        return "outcomes_not_loaded"
    maturities = {str(row.get("Outcome Maturity", "")) for row in loaded}
    if maturities == {"three_year_window_available"}:
        return "mature_outcomes_display_only"
    if "rookie_year_only" in maturities:
        return "immature_2025_outcomes_display_only"
    if "partial_two_year_window" in maturities:
        return "partial_2024_outcomes_display_only"
    return "outcomes_display_only"


def _confidence_cap(row: dict[str, str], available: dict[str, tuple[float | None, float]]) -> float:
    cap = 0.9
    warnings = str(row.get("warning_flags", ""))
    if "source_limited" in warnings or "third_party_combine" in warnings:
        cap = min(cap, 0.82)
    if "missing_pre_draft" in warnings:
        cap = min(cap, 0.78)
    if sum(weight for _, weight in available.values()) < 0.7:
        cap = min(cap, 0.72)
    return cap


def _trust_level(row: dict[str, str], available: dict[str, tuple[float | None, float]]) -> str:
    warnings = str(row.get("warning_flags", ""))
    if sum(weight for _, weight in available.values()) < 0.7:
        return "Low Evidence"
    if "missing_pre_draft" in warnings:
        return "Partial Evidence"
    if "source_limited" in warnings or "third_party_combine" in warnings:
        return "Source-Limited Review"
    return "Historical Review"


def _why_text(
    player: object,
    production: float | None,
    market_share: float | None,
    draft_score: float | None,
    athletic: float | None,
    labels: tuple[str, ...],
    outcome_loaded: bool,
) -> str:
    pieces = []
    for label, value in (
        ("production", production),
        ("team share", market_share),
        ("draft pick", draft_score),
        ("athletic", athletic),
    ):
        if value is not None:
            pieces.append(f"{label} {value:.1f}")
    label_text = f" Guardrail: {'|'.join(labels)}." if labels else ""
    outcome_text = " Outcome loaded for review only." if outcome_loaded else " Outcome not loaded."
    return f"{player} ranks from " + ", ".join(pieces[:4]) + f".{label_text}{outcome_text}"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _blank_none(value: float | None) -> float | str:
    return "" if value is None else round(value, 4)


def _int(value: object) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(str(value))
    except ValueError:
        return default
