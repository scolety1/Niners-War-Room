from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.utils.scoring import clamp_score

DEFAULT_TOP_N = 20
NO_FUTURE_STATS_POLICY = "pre_nfl_as_of_draft_only"
OUTCOME_JOIN_POLICY = "display_after_ranking_only"
HIT_RATE_WINDOWS = (5, 10, 20)
POSITIVE_OUTCOME_CATEGORIES = {"hit", "starter", "fantasy_difference_maker"}
OUTCOME_CATEGORY_VALUES = (
    "fantasy_difference_maker",
    "starter",
    "hit",
    "miss",
    "bust",
)

REQUIRED_PREDRAFT_COLUMNS = (
    "draft_year",
    "prospect_id",
    "player_name",
    "position",
    "school",
    "as_of_date",
    "source",
    "draft_capital_score",
    "age_trajectory_score",
    "production_score",
    "efficiency_score",
    "target_earning_score",
    "rushing_profile_score",
    "receiving_role_score",
    "athleticism_score",
    "lve_position_fit_score",
    "confidence_score",
    "source_notes",
)

REQUIRED_OUTCOME_COLUMNS = (
    "draft_year",
    "prospect_id",
    "nfl_team",
    "nfl_draft_pick",
    "rookie_year_lve_ppg",
    "year2_lve_ppg",
    "year3_lve_ppg",
    "best_lve_ppg",
    "top24_seasons",
    "hit_label",
    "outcome_notes",
)

RANKING_FEATURE_FIELDS = (
    "draft_capital_score",
    "age_trajectory_score",
    "production_score",
    "efficiency_score",
    "target_earning_score",
    "rushing_profile_score",
    "receiving_role_score",
    "athleticism_score",
    "lve_position_fit_score",
)

POSITION_WEIGHTS: dict[str, dict[str, float]] = {
    "QB": {
        "draft_capital_score": 28.0,
        "production_score": 18.0,
        "efficiency_score": 22.0,
        "rushing_profile_score": 18.0,
        "age_trajectory_score": 8.0,
        "athleticism_score": 4.0,
        "lve_position_fit_score": 2.0,
    },
    "RB": {
        "draft_capital_score": 24.0,
        "production_score": 18.0,
        "efficiency_score": 14.0,
        "receiving_role_score": 14.0,
        "age_trajectory_score": 14.0,
        "athleticism_score": 8.0,
        "lve_position_fit_score": 8.0,
    },
    "WR": {
        "draft_capital_score": 24.0,
        "production_score": 18.0,
        "efficiency_score": 18.0,
        "target_earning_score": 22.0,
        "age_trajectory_score": 12.0,
        "athleticism_score": 4.0,
        "lve_position_fit_score": 2.0,
    },
    "TE": {
        "draft_capital_score": 32.0,
        "production_score": 14.0,
        "efficiency_score": 18.0,
        "target_earning_score": 16.0,
        "receiving_role_score": 10.0,
        "age_trajectory_score": 4.0,
        "athleticism_score": 6.0,
    },
}


@dataclass(frozen=True)
class HistoricalRookiePreDraftInput:
    draft_year: int
    prospect_id: str
    player_name: str
    position: str
    school: str
    as_of_date: str
    source: str
    draft_capital_score: float
    age_trajectory_score: float
    production_score: float
    efficiency_score: float
    target_earning_score: float
    rushing_profile_score: float
    receiving_role_score: float
    athleticism_score: float
    lve_position_fit_score: float
    confidence_score: float
    source_notes: str
    row_number: int


@dataclass(frozen=True)
class HistoricalRookieOutcome:
    draft_year: int
    prospect_id: str
    nfl_team: str
    nfl_draft_pick: int | None
    rookie_year_lve_ppg: float | None
    year2_lve_ppg: float | None
    year3_lve_ppg: float | None
    best_lve_ppg: float | None
    top24_seasons: int | None
    hit_label: str
    outcome_notes: str
    row_number: int


@dataclass(frozen=True)
class HistoricalRookieReplayReport:
    top20_rows: list[dict[str, object]]
    feature_rows: list[dict[str, object]]
    outcome_rows: list[dict[str, object]]
    hit_rate_rows: list[dict[str, object]]
    position_hit_rate_rows: list[dict[str, object]]
    model_win_rows: list[dict[str, object]]
    model_miss_rows: list[dict[str, object]]
    metadata_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    years: list[int]
    positions: list[str]
    issues: list[str]
    predraft_source_path: str
    outcome_source_path: str


def build_historical_rookie_replay_report(
    predraft_input_path: str | Path,
    outcome_path: str | Path | None = None,
    *,
    top_n: int = DEFAULT_TOP_N,
) -> HistoricalRookieReplayReport:
    predraft_rows = load_historical_rookie_predraft_inputs(predraft_input_path)
    outcome_rows = (
        load_historical_rookie_outcomes(outcome_path)
        if outcome_path and Path(outcome_path).exists()
        else []
    )
    ranked_rows = rank_historical_rookie_prospects(predraft_rows)
    outcome_lookup = {
        (outcome.draft_year, outcome.prospect_id): outcome for outcome in outcome_rows
    }
    top_rows = [
        _top20_row(row, outcome_lookup.get((row["draft_year"], row["prospect_id"])))
        for row in ranked_rows
        if int(row["model_rank"]) <= top_n
    ]
    return HistoricalRookieReplayReport(
        top20_rows=top_rows,
        feature_rows=_feature_rows(ranked_rows),
        outcome_rows=_outcome_display_rows(ranked_rows, outcome_lookup),
        hit_rate_rows=_hit_rate_rows(ranked_rows, outcome_lookup, scope="overall"),
        position_hit_rate_rows=_position_hit_rate_rows(ranked_rows, outcome_lookup),
        model_win_rows=_model_win_rows(ranked_rows, outcome_lookup),
        model_miss_rows=_model_miss_rows(ranked_rows, outcome_lookup),
        metadata_rows=_metadata_rows(predraft_input_path, outcome_path),
        summary_rows=_summary_rows(top_rows),
        years=sorted({row.draft_year for row in predraft_rows}),
        positions=sorted({row.position for row in predraft_rows}),
        issues=[],
        predraft_source_path=str(predraft_input_path),
        outcome_source_path=str(outcome_path or ""),
    )


def load_historical_rookie_predraft_inputs(
    path: str | Path,
) -> list[HistoricalRookiePreDraftInput]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, REQUIRED_PREDRAFT_COLUMNS, csv_path.name)
        rows = [
            _predraft_input_from_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        ]
    return sorted(rows, key=lambda row: (row.draft_year, row.player_name.lower()))


def load_historical_rookie_outcomes(path: str | Path) -> list[HistoricalRookieOutcome]:
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, REQUIRED_OUTCOME_COLUMNS, csv_path.name)
        rows = [
            _outcome_from_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        ]
    return sorted(rows, key=lambda row: (row.draft_year, row.prospect_id))


def rank_historical_rookie_prospects(
    predraft_rows: list[HistoricalRookiePreDraftInput],
) -> list[dict[str, object]]:
    grouped: dict[int, list[dict[str, object]]] = {}
    for row in predraft_rows:
        score, weights = _prospect_score(row)
        grouped.setdefault(row.draft_year, []).append(
            {
                "draft_year": row.draft_year,
                "prospect_id": row.prospect_id,
                "player_name": row.player_name,
                "position": row.position,
                "school": row.school,
                "as_of_date": row.as_of_date,
                "source": row.source,
                "model_score": round(score, 2),
                "confidence_score": round(clamp_score(row.confidence_score), 2),
                "ranking_policy": NO_FUTURE_STATS_POLICY,
                "future_nfl_stats_used": False,
                "source_notes": row.source_notes,
                "_weights": weights,
                "_input": row,
            }
        )

    ranked: list[dict[str, object]] = []
    for draft_year in sorted(grouped):
        year_rows = sorted(
            grouped[draft_year],
            key=lambda item: (
                -float(item["model_score"]),
                -float(item["confidence_score"]),
                str(item["player_name"]).lower(),
                str(item["prospect_id"]),
            ),
        )
        for rank, item in enumerate(year_rows, start=1):
            item["model_rank"] = rank
            ranked.append(item)
    return ranked


def _prospect_score(row: HistoricalRookiePreDraftInput) -> tuple[float, dict[str, float]]:
    weights = POSITION_WEIGHTS.get(row.position)
    if weights is None:
        raise ValueError(f"Unsupported historical rookie position: {row.position}.")
    numerator = 0.0
    denominator = 0.0
    for feature_name, weight in weights.items():
        numerator += _feature_value(row, feature_name) * weight
        denominator += weight
    if denominator <= 0:
        return 50.0, weights
    return clamp_score(numerator / denominator), weights


def _feature_rows(ranked_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ranked in ranked_rows:
        source_input = ranked["_input"]
        weights = ranked["_weights"]
        for feature_name, weight in weights.items():
            normalized = _feature_value(source_input, feature_name)
            rows.append(
                {
                    "draft_year": ranked["draft_year"],
                    "model_rank": ranked["model_rank"],
                    "prospect_id": ranked["prospect_id"],
                    "player_name": ranked["player_name"],
                    "position": ranked["position"],
                    "feature_name": feature_name,
                    "raw_value": normalized,
                    "normalized_score": normalized,
                    "feature_weight": weight,
                    "model_score_contribution": round(normalized * weight / 100.0, 4),
                    "component": "pre_nfl_prospect_score",
                    "source": ranked["source"],
                    "as_of_date": ranked["as_of_date"],
                    "future_nfl_stats_used": False,
                }
            )
    return rows


def _top20_row(
    ranked: dict[str, object],
    outcome: HistoricalRookieOutcome | None,
) -> dict[str, object]:
    outcome_category = classify_historical_rookie_outcome(
        str(ranked["position"]),
        outcome,
    )
    return {
        "draft_year": ranked["draft_year"],
        "model_rank": ranked["model_rank"],
        "player_name": ranked["player_name"],
        "position": ranked["position"],
        "school": ranked["school"],
        "pre_nfl_model_score": ranked["model_score"],
        "confidence_score": ranked["confidence_score"],
        "as_of_date": ranked["as_of_date"],
        "ranking_policy": ranked["ranking_policy"],
        "future_nfl_stats_used": False,
        "outcome_label": outcome.hit_label if outcome else "not_loaded",
        "outcome_category": outcome_category,
        "outcome_is_hit": outcome_category in POSITIVE_OUTCOME_CATEGORIES,
        "best_lve_ppg_after_draft": outcome.best_lve_ppg if outcome else None,
        "top24_seasons_after_draft": outcome.top24_seasons if outcome else None,
        "source": ranked["source"],
        "source_notes": ranked["source_notes"],
    }


def _outcome_display_rows(
    ranked_rows: list[dict[str, object]],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ranked in ranked_rows:
        outcome = outcome_lookup.get((int(ranked["draft_year"]), str(ranked["prospect_id"])))
        if outcome is None:
            rows.append(
                {
                    "draft_year": ranked["draft_year"],
                    "model_rank": ranked["model_rank"],
                    "player_name": ranked["player_name"],
                    "position": ranked["position"],
                    "outcome_loaded": False,
                "hit_label": "not_loaded",
                "outcome_category": "not_loaded",
                "outcome_is_hit": False,
                "best_lve_ppg": "",
                "top24_seasons": "",
                    "outcome_notes": "",
                    "ranking_input": False,
                    "join_policy": OUTCOME_JOIN_POLICY,
                }
            )
            continue
        rows.append(
            {
                "draft_year": ranked["draft_year"],
                "model_rank": ranked["model_rank"],
                "player_name": ranked["player_name"],
                "position": ranked["position"],
                "outcome_loaded": True,
                "nfl_team": outcome.nfl_team,
                "nfl_draft_pick": outcome.nfl_draft_pick,
                "rookie_year_lve_ppg": outcome.rookie_year_lve_ppg,
                "year2_lve_ppg": outcome.year2_lve_ppg,
                "year3_lve_ppg": outcome.year3_lve_ppg,
                "best_lve_ppg": outcome.best_lve_ppg,
                "top24_seasons": outcome.top24_seasons,
                "hit_label": outcome.hit_label,
                "outcome_category": classify_historical_rookie_outcome(
                    str(ranked["position"]),
                    outcome,
                ),
                "outcome_is_hit": classify_historical_rookie_outcome(
                    str(ranked["position"]),
                    outcome,
                )
                in POSITIVE_OUTCOME_CATEGORIES,
                "outcome_notes": outcome.outcome_notes,
                "ranking_input": False,
                "join_policy": OUTCOME_JOIN_POLICY,
            }
        )
    return rows


def classify_historical_rookie_outcome(
    position: str,
    outcome: HistoricalRookieOutcome | None,
) -> str:
    if outcome is None:
        return "not_loaded"
    best_ppg = outcome.best_lve_ppg
    top24 = outcome.top24_seasons or 0
    label = outcome.hit_label.lower()
    if any(marker in label for marker in ("difference", "elite", "smash")):
        return "fantasy_difference_maker"
    if "bust" in label:
        return "bust"
    if "miss" in label:
        return "bust" if best_ppg is not None and best_ppg <= 3.0 else "miss"

    if position == "QB":
        if best_ppg is not None and best_ppg >= 18.0:
            return "fantasy_difference_maker"
        if best_ppg is not None and best_ppg >= 15.0:
            return "starter"
        if best_ppg is not None and best_ppg >= 12.0:
            return "hit"
        if best_ppg is not None and best_ppg <= 6.0:
            return "bust"
        return "miss"

    if position == "TE":
        if top24 >= 2 or (best_ppg is not None and best_ppg >= 10.5):
            return "fantasy_difference_maker"
        if top24 >= 1 or (best_ppg is not None and best_ppg >= 8.0):
            return "starter"
        if best_ppg is not None and best_ppg >= 5.5:
            return "hit"
        if best_ppg is not None and best_ppg <= 2.5:
            return "bust"
        return "miss"

    if top24 >= 2 or (best_ppg is not None and best_ppg >= 13.0):
        return "fantasy_difference_maker"
    if top24 >= 1 or (best_ppg is not None and best_ppg >= 10.0):
        return "starter"
    if best_ppg is not None and best_ppg >= 7.5:
        return "hit"
    if best_ppg is not None and best_ppg <= 3.0:
        return "bust"
    return "miss"


def _hit_rate_rows(
    ranked_rows: list[dict[str, object]],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
    *,
    scope: str,
    position: str = "ALL",
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    years = sorted({int(row["draft_year"]) for row in ranked_rows})
    for year in years:
        year_rows = [
            row
            for row in ranked_rows
            if int(row["draft_year"]) == year
            and (position == "ALL" or str(row["position"]) == position)
        ]
        output.extend(_window_hit_rate_rows(year, position, scope, year_rows, outcome_lookup))
    all_rows = [
        row
        for row in ranked_rows
        if position == "ALL" or str(row["position"]) == position
    ]
    output.extend(_window_hit_rate_rows("ALL", position, scope, all_rows, outcome_lookup))
    return output


def _position_hit_rate_rows(
    ranked_rows: list[dict[str, object]],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    positions = sorted({str(row["position"]) for row in ranked_rows})
    for position in positions:
        output.extend(
            _hit_rate_rows(
                ranked_rows,
                outcome_lookup,
                scope="position",
                position=position,
            )
        )
    return output


def _window_hit_rate_rows(
    draft_year: int | str,
    position: str,
    scope: str,
    ranked_rows: list[dict[str, object]],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    sorted_rows = sorted(
        ranked_rows,
        key=lambda row: (
            int(row["model_rank"]),
            -float(row["model_score"]),
            str(row["player_name"]).lower(),
        ),
    )
    for window in HIT_RATE_WINDOWS:
        rows = sorted_rows[:window]
        outcome_rows = [_outcome_evaluation_row(row, outcome_lookup) for row in rows]
        labeled = [row for row in outcome_rows if row["outcome_loaded"]]
        hit_count = sum(1 for row in labeled if row["outcome_is_hit"])
        output.append(
            {
                "draft_year": draft_year,
                "position": position,
                "scope": scope,
                "rank_window": f"top_{window}",
                "ranked_count": len(rows),
                "labeled_count": len(labeled),
                "hit_count": hit_count,
                "hit_rate": round(hit_count / len(labeled), 3) if labeled else None,
                "fantasy_difference_maker_count": _category_count(
                    labeled,
                    "fantasy_difference_maker",
                ),
                "starter_count": _category_count(labeled, "starter"),
                "hit_only_count": _category_count(labeled, "hit"),
                "miss_count": _category_count(labeled, "miss"),
                "bust_count": _category_count(labeled, "bust"),
                "ranking_input": False,
                "join_policy": OUTCOME_JOIN_POLICY,
            }
        )
    return output


def _outcome_evaluation_row(
    ranked: dict[str, object],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
) -> dict[str, object]:
    outcome = outcome_lookup.get((int(ranked["draft_year"]), str(ranked["prospect_id"])))
    category = classify_historical_rookie_outcome(str(ranked["position"]), outcome)
    return {
        "draft_year": ranked["draft_year"],
        "model_rank": ranked["model_rank"],
        "prospect_id": ranked["prospect_id"],
        "player_name": ranked["player_name"],
        "position": ranked["position"],
        "model_score": ranked["model_score"],
        "outcome_loaded": outcome is not None,
        "outcome_category": category,
        "outcome_is_hit": category in POSITIVE_OUTCOME_CATEGORIES,
        "outcome_value": _outcome_value(category),
        "best_lve_ppg": outcome.best_lve_ppg if outcome else None,
        "top24_seasons": outcome.top24_seasons if outcome else None,
        "hit_label": outcome.hit_label if outcome else "not_loaded",
    }


def _model_win_rows(
    ranked_rows: list[dict[str, object]],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
) -> list[dict[str, object]]:
    rows = [_outcome_evaluation_row(row, outcome_lookup) for row in ranked_rows]
    wins = [
        _win_miss_row(row, "model_win")
        for row in rows
        if row["outcome_is_hit"] and int(row["model_rank"]) <= 10
    ]
    return sorted(
        wins,
        key=lambda row: (
            int(row["draft_year"]),
            -float(row["review_score"]),
            int(row["model_rank"]),
        ),
    )


def _model_miss_rows(
    ranked_rows: list[dict[str, object]],
    outcome_lookup: dict[tuple[int, str], HistoricalRookieOutcome],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in [_outcome_evaluation_row(item, outcome_lookup) for item in ranked_rows]:
        rank = int(row["model_rank"])
        category = str(row["outcome_category"])
        if category in {"miss", "bust"} and rank <= 10:
            output.append(_win_miss_row(row, "model_overrated_miss"))
        elif category in {"starter", "fantasy_difference_maker"} and rank > 10:
            output.append(_win_miss_row(row, "model_underrated_miss"))
    return sorted(
        output,
        key=lambda row: (
            int(row["draft_year"]),
            -float(row["review_score"]),
            int(row["model_rank"]),
        ),
    )


def _win_miss_row(row: dict[str, object], review_type: str) -> dict[str, object]:
    rank = int(row["model_rank"])
    outcome_value = float(row["outcome_value"])
    if review_type == "model_win":
        review_score = outcome_value + ((21 - rank) * 2.0)
        note = "Model ranked this player highly and the outcome supported it."
    elif review_type == "model_overrated_miss":
        review_score = (21 - rank) * 3.0 + (100.0 - outcome_value)
        note = "Model ranked this player highly, but the outcome missed."
    else:
        review_score = rank * 2.0 + outcome_value
        note = "Model ranked this later than the eventual outcome deserved."
    return {
        "draft_year": row["draft_year"],
        "review_type": review_type,
        "player_name": row["player_name"],
        "position": row["position"],
        "model_rank": row["model_rank"],
        "model_score": row["model_score"],
        "outcome_category": row["outcome_category"],
        "best_lve_ppg": row["best_lve_ppg"],
        "top24_seasons": row["top24_seasons"],
        "review_score": round(review_score, 2),
        "ranking_input": False,
        "review_note": note,
    }


def _category_count(rows: list[dict[str, object]], category: str) -> int:
    return sum(1 for row in rows if row["outcome_category"] == category)


def _outcome_value(category: str) -> float:
    return {
        "fantasy_difference_maker": 100.0,
        "starter": 80.0,
        "hit": 62.0,
        "miss": 30.0,
        "bust": 0.0,
    }.get(category, 0.0)


def _metadata_rows(
    predraft_input_path: str | Path,
    outcome_path: str | Path | None,
) -> list[dict[str, object]]:
    return [
        {
            "metadata_key": "ranking_input_scope",
            "metadata_value": NO_FUTURE_STATS_POLICY,
            "meaning": "Rankings use college/as-of-draft prospect inputs only.",
        },
        {
            "metadata_key": "future_nfl_stats_used_in_ranking",
            "metadata_value": False,
            "meaning": "NFL production outcomes are excluded from model score calculation.",
        },
        {
            "metadata_key": "outcome_join_policy",
            "metadata_value": OUTCOME_JOIN_POLICY,
            "meaning": "Post-draft results are joined only after ranks are assigned.",
        },
        {
            "metadata_key": "predraft_input_file",
            "metadata_value": str(predraft_input_path),
            "meaning": "Only this file feeds the replay ranking.",
        },
        {
            "metadata_key": "outcome_file",
            "metadata_value": str(outcome_path or ""),
            "meaning": "Outcome labels are review-only and never ranking inputs.",
        },
    ]


def _summary_rows(top_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    years = sorted({int(row["draft_year"]) for row in top_rows})
    for year in years:
        rows = [row for row in top_rows if int(row["draft_year"]) == year]
        output.append(
            {
                "draft_year": year,
                "top_prospect_rows": len(rows),
                "positions": "|".join(sorted({str(row["position"]) for row in rows})),
                "avg_confidence": round(
                    sum(float(row["confidence_score"]) for row in rows) / len(rows),
                    2,
                )
                if rows
                else 0.0,
                "future_nfl_stats_used": False,
                "ranking_policy": NO_FUTURE_STATS_POLICY,
            }
        )
    return output


def _predraft_input_from_row(
    row: dict[str, str],
    row_number: int,
) -> HistoricalRookiePreDraftInput:
    return HistoricalRookiePreDraftInput(
        draft_year=_required_int(row, "draft_year", row_number),
        prospect_id=_required_text(row, "prospect_id", row_number),
        player_name=_required_text(row, "player_name", row_number),
        position=_required_text(row, "position", row_number),
        school=_required_text(row, "school", row_number),
        as_of_date=_required_text(row, "as_of_date", row_number),
        source=_required_text(row, "source", row_number),
        draft_capital_score=_score(row, "draft_capital_score", row_number),
        age_trajectory_score=_score(row, "age_trajectory_score", row_number),
        production_score=_score(row, "production_score", row_number),
        efficiency_score=_score(row, "efficiency_score", row_number),
        target_earning_score=_score(row, "target_earning_score", row_number),
        rushing_profile_score=_score(row, "rushing_profile_score", row_number),
        receiving_role_score=_score(row, "receiving_role_score", row_number),
        athleticism_score=_score(row, "athleticism_score", row_number),
        lve_position_fit_score=_score(row, "lve_position_fit_score", row_number),
        confidence_score=_score(row, "confidence_score", row_number),
        source_notes=_required_text(row, "source_notes", row_number),
        row_number=row_number,
    )


def _outcome_from_row(row: dict[str, str], row_number: int) -> HistoricalRookieOutcome:
    return HistoricalRookieOutcome(
        draft_year=_required_int(row, "draft_year", row_number),
        prospect_id=_required_text(row, "prospect_id", row_number),
        nfl_team=_optional_text(row, "nfl_team") or "",
        nfl_draft_pick=_optional_int(row, "nfl_draft_pick", row_number),
        rookie_year_lve_ppg=_optional_float(row, "rookie_year_lve_ppg", row_number),
        year2_lve_ppg=_optional_float(row, "year2_lve_ppg", row_number),
        year3_lve_ppg=_optional_float(row, "year3_lve_ppg", row_number),
        best_lve_ppg=_optional_float(row, "best_lve_ppg", row_number),
        top24_seasons=_optional_int(row, "top24_seasons", row_number),
        hit_label=_optional_text(row, "hit_label") or "unknown",
        outcome_notes=_optional_text(row, "outcome_notes") or "",
        row_number=row_number,
    )


def _feature_value(row: HistoricalRookiePreDraftInput, feature_name: str) -> float:
    value = getattr(row, feature_name)
    return clamp_score(float(value))


def _score(row: dict[str, str], column: str, row_number: int) -> float:
    return clamp_score(_required_float(row, column, row_number))


def _require_columns(
    fieldnames: list[str] | None,
    required_columns: tuple[str, ...],
    file_name: str,
) -> None:
    missing_columns = [
        column for column in required_columns if column not in (fieldnames or ())
    ]
    if missing_columns:
        raise ValueError(
            f"Missing historical rookie replay columns in {file_name}: "
            + ", ".join(missing_columns)
            + "."
        )


def _required_int(row: dict[str, str], column: str, row_number: int) -> int:
    text = _required_text(row, column, row_number)
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(
            f"Historical rookie replay row {row_number} has non-integer {column}."
        ) from exc


def _optional_int(row: dict[str, str], column: str, row_number: int) -> int | None:
    value = _optional_text(row, column)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Historical rookie replay row {row_number} has non-integer {column}."
        ) from exc


def _required_float(row: dict[str, str], column: str, row_number: int) -> float:
    text = _required_text(row, column, row_number)
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(
            f"Historical rookie replay row {row_number} has non-numeric {column}."
        ) from exc


def _optional_float(
    row: dict[str, str],
    column: str,
    row_number: int,
) -> float | None:
    value = _optional_text(row, column)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"Historical rookie replay row {row_number} has non-numeric {column}."
        ) from exc


def _required_text(row: dict[str, str], column: str, row_number: int) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"Historical rookie replay row {row_number} is missing {column}.")
    return value


def _optional_text(row: dict[str, str], column: str) -> str | None:
    value = (row.get(column) or "").strip()
    return value or None
