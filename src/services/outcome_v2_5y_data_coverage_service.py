"""Outcome V2 extended historical label helpers.

This module is intentionally app-agnostic. It builds review-only label artifacts
from factual player-season rows and does not expose model inputs or rankings.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CORE_POSITIONS = ("QB", "RB", "WR", "TE")
POSITION_THRESHOLDS: dict[str, tuple[int, ...]] = {
    "QB": (6, 12),
    "RB": (6, 12, 24, 36),
    "WR": (6, 12, 24, 36),
    "TE": (6, 12),
}
ALL_THRESHOLDS = (6, 12, 24, 36)


@dataclass(frozen=True)
class ExtendedOutcomeBuildResult:
    season_labels_path: Path
    anchor_labels_path: Path
    manifest_path: Path
    coverage_summary_path: Path
    season_label_rows: int
    anchor_label_rows: int
    complete_5y_rows: int
    scoring_mode: str


def calculate_nwr_fantasy_points(frame: pd.DataFrame) -> pd.Series:
    """Calculate NWR non-PPR, first-down-aware fantasy points."""

    passing = (
        _num(frame, "passing_yards") / 30
        + _num(frame, "passing_tds") * 3
        - _num(frame, "passing_interceptions")
        + _num(frame, "passing_2pt_conversions") * 2
    )
    rushing = (
        _num(frame, "rushing_yards") / 10
        + _num(frame, "rushing_tds") * 4
        + _num(frame, "rushing_first_downs") * 0.4
        + _num(frame, "rushing_2pt_conversions") * 2
    )
    receiving = (
        _num(frame, "receiving_yards") / 10
        + _num(frame, "receiving_tds") * 4
        + _num(frame, "receiving_first_downs") * 0.4
        + _num(frame, "receiving_2pt_conversions") * 2
    )
    returns = (
        (_num(frame, "punt_return_yards") + _num(frame, "kickoff_return_yards")) / 30
        + _num(frame, "special_teams_tds") * 4
    )
    fumbles_lost = (
        _num(frame, "sack_fumbles_lost")
        + _num(frame, "rushing_fumbles_lost")
        + _num(frame, "receiving_fumbles_lost")
    )
    return passing + rushing + receiving + returns - fumbles_lost


def build_season_outcome_labels(
    season_stats: pd.DataFrame,
    *,
    scoring_mode: str = "exact_verified_first_downs",
) -> pd.DataFrame:
    labels = season_stats.copy()
    labels["position"] = labels["position"].astype(str).str.upper()
    labels = labels[labels["position"].isin(CORE_POSITIONS)].copy()
    labels["season"] = pd.to_numeric(labels["season"], errors="coerce")
    labels = labels.dropna(subset=["season", "player_id", "position"]).copy()
    labels["season"] = labels["season"].astype(int)
    labels["fantasy_points"] = calculate_nwr_fantasy_points(labels).round(4)
    labels["games_played"] = _num(labels, "games").round(2)
    labels["player_name"] = labels.get(
        "player_display_name", labels.get("player_name", "")
    )
    labels["team"] = labels.get("recent_team", labels.get("team", ""))
    labels["position_finish"] = labels.groupby(["season", "position"])[
        "fantasy_points"
    ].rank(method="first", ascending=False)
    labels["position_finish"] = labels["position_finish"].astype(int)
    for threshold in ALL_THRESHOLDS:
        labels[f"top_{threshold}_hit"] = (
            labels["position_finish"] <= threshold
        ).map({True: "hit", False: "miss"})
    labels["scoring_mode"] = scoring_mode
    labels["data_quality_status"] = "complete_factual_player_stats"
    labels["approval_status"] = "review_only_historical_labels"
    labels["model_input_allowed"] = "no"
    labels["training_allowed"] = "no"
    labels["app_wiring_allowed"] = "no"
    return labels[
        [
            "player_id",
            "player_name",
            "position",
            "season",
            "team",
            "scoring_mode",
            "fantasy_points",
            "position_finish",
            "games_played",
            "top_6_hit",
            "top_12_hit",
            "top_24_hit",
            "top_36_hit",
            "data_quality_status",
            "approval_status",
            "model_input_allowed",
            "training_allowed",
            "app_wiring_allowed",
        ]
    ].sort_values(["season", "position", "position_finish", "player_name"])


def build_anchor_horizon_labels(season_labels: pd.DataFrame) -> pd.DataFrame:
    labels = season_labels.copy()
    labels["season"] = pd.to_numeric(labels["season"], errors="coerce").astype(int)
    label_lookup = {
        (str(row.player_id), int(row.season)): row
        for row in labels.itertuples(index=False)
    }
    rows: list[dict[str, object]] = []
    for anchor in labels.itertuples(index=False):
        player_id = str(anchor.player_id)
        position = str(anchor.position)
        thresholds = POSITION_THRESHOLDS.get(position, ())
        row: dict[str, object] = {
            "player_id": player_id,
            "player_name": anchor.player_name,
            "position": position,
            "anchor_season": int(anchor.season),
            "team": anchor.team,
        }
        window_statuses: list[str] = []
        for horizon_name, offset in (("this_year", 1), ("next_year", 2)):
            target = label_lookup.get((player_id, int(anchor.season) + offset))
            complete = target is not None
            row[f"{horizon_name}_window_complete"] = complete
            if not complete:
                window_statuses.append(f"{horizon_name}_missing_target")
            for threshold in ALL_THRESHOLDS:
                row[f"{horizon_name}_top_{threshold}_hit"] = _threshold_value(
                    target, threshold, threshold in thresholds
                )

        future_targets = [
            label_lookup.get((player_id, int(anchor.season) + offset))
            for offset in range(1, 6)
        ]
        five_year_complete = all(target is not None for target in future_targets)
        row["within_5y_window_complete"] = five_year_complete
        if not five_year_complete:
            window_statuses.append("within_5y_missing_or_right_censored")
        for threshold in ALL_THRESHOLDS:
            if threshold not in thresholds:
                row[f"within_5y_top_{threshold}_hit"] = "not_applicable"
                continue
            if not five_year_complete:
                row[f"within_5y_top_{threshold}_hit"] = "Not enough information"
                continue
            values = [
                getattr(target, f"top_{threshold}_hit")
                for target in future_targets
                if target is not None
            ]
            row[f"within_5y_top_{threshold}_hit"] = (
                "hit" if "hit" in values else "miss"
            )
        row["censoring_status"] = (
            "complete" if not window_statuses else "|".join(window_statuses)
        )
        row["approval_status"] = "review_only_historical_labels"
        row["model_input_allowed"] = "no"
        row["training_allowed"] = "no"
        row["app_wiring_allowed"] = "no"
        rows.append(row)
    columns = [
        "player_id",
        "player_name",
        "position",
        "anchor_season",
        "team",
        "this_year_top_6_hit",
        "this_year_top_12_hit",
        "this_year_top_24_hit",
        "this_year_top_36_hit",
        "next_year_top_6_hit",
        "next_year_top_12_hit",
        "next_year_top_24_hit",
        "next_year_top_36_hit",
        "within_5y_top_6_hit",
        "within_5y_top_12_hit",
        "within_5y_top_24_hit",
        "within_5y_top_36_hit",
        "this_year_window_complete",
        "next_year_window_complete",
        "within_5y_window_complete",
        "censoring_status",
        "approval_status",
        "model_input_allowed",
        "training_allowed",
        "app_wiring_allowed",
    ]
    return pd.DataFrame(rows)[columns].sort_values(
        ["anchor_season", "position", "player_name"]
    )


def build_5y_coverage_summary(
    anchor_labels: pd.DataFrame,
    previous_anchor_labels: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for position, thresholds in POSITION_THRESHOLDS.items():
        position_frame = anchor_labels[anchor_labels["position"] == position]
        previous_position_frame = (
            previous_anchor_labels[previous_anchor_labels["position"] == position]
            if previous_anchor_labels is not None
            else pd.DataFrame()
        )
        for threshold in thresholds:
            column = f"within_5y_top_{threshold}_hit"
            complete = position_frame[position_frame["within_5y_window_complete"]]
            previous_complete = (
                previous_position_frame[
                    previous_position_frame["within_5y_window_complete"]
                ]
                if not previous_position_frame.empty
                else pd.DataFrame()
            )
            rows.append(
                {
                    "position": position,
                    "threshold": f"T{threshold}",
                    "complete_5y_rows_before": int(len(previous_complete)),
                    "positive_hits_before": int(
                        (
                            previous_complete.get(column, pd.Series(dtype=str))
                            == "hit"
                        ).sum()
                    ),
                    "censored_or_missing_before": int(
                        len(previous_position_frame) - len(previous_complete)
                    ),
                    "complete_5y_rows_after": int(len(complete)),
                    "positive_hits_after": int((complete[column] == "hit").sum()),
                    "misses_after": int((complete[column] == "miss").sum()),
                    "censored_or_missing_after": int(
                        len(position_frame) - len(complete)
                    ),
                    "app_validation_note": "coverage_only_not_validated",
                }
            )
    return pd.DataFrame(rows)


def write_extended_artifacts(
    season_labels: pd.DataFrame,
    anchor_labels: pd.DataFrame,
    output_root: Path,
    *,
    seasons: Iterable[int],
    source: str,
    scoring_mode: str,
    previous_anchor_labels: pd.DataFrame | None = None,
) -> ExtendedOutcomeBuildResult:
    output_root.mkdir(parents=True, exist_ok=True)
    season_path = output_root / "outcome_v2_extended_season_outcome_labels.csv"
    anchor_path = output_root / "outcome_v2_extended_anchor_horizon_labels.csv"
    manifest_path = output_root / "outcome_v2_extended_label_manifest.csv"
    coverage_path = output_root / "outcome_v2_extended_5y_coverage_summary.csv"
    coverage = build_5y_coverage_summary(
        anchor_labels,
        previous_anchor_labels=previous_anchor_labels,
    )
    season_labels.to_csv(season_path, index=False)
    anchor_labels.to_csv(anchor_path, index=False)
    coverage.to_csv(coverage_path, index=False)
    manifest = pd.DataFrame(
        [
            {
                "artifact": "outcome_v2_extended_season_outcome_labels.csv",
                "rows": len(season_labels),
                "source": source,
                "seasons": ";".join(str(season) for season in seasons),
                "scoring_mode": scoring_mode,
                "review_only": "yes",
                "model_input_allowed": "no",
                "training_allowed": "no",
                "app_wiring_allowed": "no",
            },
            {
                "artifact": "outcome_v2_extended_anchor_horizon_labels.csv",
                "rows": len(anchor_labels),
                "source": source,
                "seasons": ";".join(str(season) for season in seasons),
                "scoring_mode": scoring_mode,
                "review_only": "yes",
                "model_input_allowed": "no",
                "training_allowed": "no",
                "app_wiring_allowed": "no",
            },
            {
                "artifact": "outcome_v2_extended_5y_coverage_summary.csv",
                "rows": len(coverage),
                "source": source,
                "seasons": ";".join(str(season) for season in seasons),
                "scoring_mode": scoring_mode,
                "review_only": "yes",
                "model_input_allowed": "no",
                "training_allowed": "no",
                "app_wiring_allowed": "no",
            },
        ]
    )
    manifest.to_csv(manifest_path, index=False)
    return ExtendedOutcomeBuildResult(
        season_labels_path=season_path,
        anchor_labels_path=anchor_path,
        manifest_path=manifest_path,
        coverage_summary_path=coverage_path,
        season_label_rows=len(season_labels),
        anchor_label_rows=len(anchor_labels),
        complete_5y_rows=int(anchor_labels["within_5y_window_complete"].sum()),
        scoring_mode=scoring_mode,
    )


def _threshold_value(target: object | None, threshold: int, applicable: bool) -> str:
    if not applicable:
        return "not_applicable"
    if target is None:
        return "Not enough information"
    return str(getattr(target, f"top_{threshold}_hit"))


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)
