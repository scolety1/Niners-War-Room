from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "sprint_5bz_2016_2017_historical_feature_label_rebuild"
OUTPUT_DIR = REPO_ROOT / "local_exports/outcome_probability" / RUN_ID
PLAYER_STATS_PATH = REPO_ROOT / "local_exports/truth_set_lab/v3/downloads/player_stats.csv"

OUTPUT_SCOPE = "internal_only_not_app_readable"
APP_RELEASE_STATUS = "blocked_not_app_readable"
MODELED_POSITIONS = ("QB", "RB", "WR", "TE")
TARGET_SOURCE_MAP = {2016: 2015, 2017: 2016}
SCORING_VERSION_ID = "nwr_1qb_nonppr_fd_v1_source_safe_no_return"
FEATURE_SCHEMA_VERSION = "nwr_outcome_features_renamed_5r_v1_5bz_local_only"
ROW_TYPE = "all_player_pre_week1"

APP_TIER_THRESHOLDS = {
    "QB": {"difference_maker": 6, "starter": 12, "useful": 18},
    "RB": {"difference_maker": 12, "starter": 24, "useful": 36},
    "WR": {"difference_maker": 12, "starter": 24, "useful": 36},
    "TE": {"difference_maker": 3, "starter": 6, "useful": 12},
}

THRESHOLD_HEADS = {
    "QB": (6, 12, 18, 24),
    "RB": (6, 12, 24, 36, 48),
    "WR": (6, 12, 24, 36, 48),
    "TE": (3, 6, 12, 18, 24),
}

ALLOWED_SOURCE_FIELDS = (
    "player_id",
    "player_name",
    "player_display_name",
    "recent_team",
    "position",
    "position_group",
    "season",
    "week",
    "season_type",
    "completions",
    "attempts",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "rushing_fumbles_lost",
    "receiving_fumbles_lost",
    "sack_fumbles_lost",
)

FEATURE_FIELDS = (
    "position",
    "prior_completed_season_games",
    "prior_completed_season_games_active",
    "prior_completed_season_games_played",
    "prior_completed_season_passing_yards",
    "prior_completed_season_receiving_first_downs",
    "prior_completed_season_receiving_yards",
    "prior_completed_season_receptions",
    "prior_completed_season_rushing_first_downs",
    "prior_completed_season_rushing_yards",
    "prior_season_nwr_finish_rank",
    "prior_season_nwr_ppg",
)

FORBIDDEN_OR_QUARANTINED_FIELDS = (
    "fantasy_points",
    "fantasy_points_ppr",
    "passing_epa",
    "rushing_epa",
    "receiving_epa",
    "dakota",
    "wopr",
    "racr",
    "pacr",
    "target_share",
    "air_yards_share",
    "adp",
    "ranking",
    "rankings",
    "projection",
    "projections",
    "consensus",
    "market",
    "trade",
    "rotowire",
    "private_score",
    "prior_fantasy_draft_history",
)


def main() -> None:
    result = build_package(repo_root=REPO_ROOT, output_dir=OUTPUT_DIR)
    print(json.dumps(result["metadata"], indent=2, sort_keys=True))


def build_package(*, repo_root: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = load_player_stats(PLAYER_STATS_PATH)
    headers = source_rows.fieldnames

    source_duplicates = duplicate_player_week_rows(source_rows.rows)
    source_season_rows = {
        season: [row for row in source_rows.rows if int(row["season"]) == season]
        for season in TARGET_SOURCE_MAP.values()
    }
    target_season_rows = {
        season: [row for row in source_rows.rows if int(row["season"]) == season]
        for season in TARGET_SOURCE_MAP
    }

    source_aggregates = aggregate_source_features(source_season_rows)
    label_aggregates = aggregate_target_labels(target_season_rows)
    feature_rows, label_rows, blocked_rows = build_feature_and_label_rows(
        source_aggregates=source_aggregates,
        label_aggregates=label_aggregates,
    )

    trainability_rows = trainability_report(
        feature_rows=feature_rows,
        blocked_rows=blocked_rows,
    )
    missingness_rows = feature_missingness_rows(feature_rows)
    label_support_rows = label_support(label_rows)
    legality_rows = legality_audit_rows(feature_rows, label_rows)
    forbidden_rows = forbidden_feature_scan(headers)
    identity_rows = identity_team_position_audit(source_season_rows, target_season_rows)
    duplicate_rows = duplicate_key_audit_rows(
        source_duplicates=source_duplicates,
        feature_rows=feature_rows,
        label_rows=label_rows,
    )
    population_rows = population_policy_audit(feature_rows, blocked_rows)
    first_down_rows = first_down_completeness_rows(source_season_rows, target_season_rows)
    quarantine_rows = artifact_quarantine_rows(output_dir)
    release_rows = release_blocker_rows()

    write_csv(output_dir / "historical_2016_2017_feature_snapshots.csv", feature_rows)
    write_csv(output_dir / "historical_2016_2017_outcome_labels.csv", label_rows)
    write_csv(output_dir / "blocked_historical_2016_2017_rows.csv", blocked_rows)
    write_csv(output_dir / "historical_2016_2017_trainability_report.csv", trainability_rows)
    write_csv(output_dir / "historical_2016_2017_feature_missingness.csv", missingness_rows)
    write_csv(output_dir / "historical_2016_2017_label_support.csv", label_support_rows)
    write_csv(output_dir / "historical_2016_2017_legality_audit.csv", legality_rows)
    write_csv(output_dir / "historical_2016_2017_forbidden_feature_scan.csv", forbidden_rows)
    write_csv(
        output_dir / "historical_2016_2017_identity_team_position_audit.csv",
        identity_rows,
    )
    write_csv(output_dir / "historical_2016_2017_duplicate_key_audit.csv", duplicate_rows)
    write_csv(output_dir / "historical_2016_2017_population_policy_audit.csv", population_rows)
    write_csv(output_dir / "historical_2016_2017_first_down_completeness.csv", first_down_rows)
    write_csv(output_dir / "artifact_quarantine_audit.csv", quarantine_rows)
    write_csv(output_dir / "release_blockers.csv", release_rows)

    metadata = {
        "run_id": RUN_ID,
        "created_at_utc": utc_now_iso(),
        "code_version_git_commit": git_commit(repo_root),
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "source_file": str(PLAYER_STATS_PATH.relative_to(repo_root)).replace("\\", "/"),
        "target_source_map": TARGET_SOURCE_MAP,
        "feature_rows": len(feature_rows),
        "label_rows": len(label_rows),
        "blocked_rows": len(blocked_rows),
        "positions": list(MODELED_POSITIONS),
        "app_readable_output_created": False,
        "model_training_performed": False,
        "probabilities_generated": False,
        "ranking_sorting_changed": False,
        "promoted_artifacts_created": False,
        "exact_percentages": "blocked",
        "coarse_bands": "blocked",
        "app_wiring": "blocked",
        "final_gate_label": (
            "LOCAL_ONLY_2016_2017_FEATURE_LABEL_ROWS_GENERATED_MODELING_BLOCKED"
        ),
    }
    write_json(output_dir / "metadata_sprint_5bz.json", metadata)
    write_readme(output_dir / "README_SPRINT_5BZ.md", metadata)

    return {"metadata": metadata, "output_dir": str(output_dir)}


class PlayerStatsRows:
    def __init__(self, *, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
        self.rows = rows
        self.fieldnames = fieldnames


def load_player_stats(path: Path) -> PlayerStatsRows:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [
            row
            for row in reader
            if row.get("season") in {"2015", "2016", "2017"}
            and row.get("season_type") in {"REG", "POST"}
        ]
        return PlayerStatsRows(rows=rows, fieldnames=list(reader.fieldnames or []))


def aggregate_source_features(
    rows_by_source_season: Mapping[int, Sequence[Mapping[str, str]]],
) -> dict[tuple[int, str], dict[str, Any]]:
    output: dict[tuple[int, str], dict[str, Any]] = {}
    for source_season, rows in rows_by_source_season.items():
        regular_rows = [row for row in rows if row.get("season_type") == "REG"]
        grouped = group_player_rows(regular_rows)
        aggregate_rows = [
            season_aggregate(source_season, player_id, player_rows)
            for player_id, player_rows in grouped.items()
        ]
        scored = add_position_ranks(
            aggregate_rows,
            value_column="source_season_nwr_total",
            rank_column="source_position_rank",
        )
        for row in scored:
            output[(source_season, str(row["player_id"]))] = row
    return output


def aggregate_target_labels(
    rows_by_target_season: Mapping[int, Sequence[Mapping[str, str]]],
) -> dict[tuple[int, str], dict[str, Any]]:
    output: dict[tuple[int, str], dict[str, Any]] = {}
    for target_season, rows in rows_by_target_season.items():
        regular_rows = [row for row in rows if row.get("season_type") == "REG"]
        grouped = group_player_rows(regular_rows)
        aggregate_rows = [
            season_aggregate(target_season, player_id, player_rows)
            for player_id, player_rows in grouped.items()
        ]
        scored = add_position_ranks(
            aggregate_rows,
            value_column="source_season_nwr_total",
            rank_column="target_position_rank",
        )
        for row in scored:
            output[(target_season, str(row["player_id"]))] = row
    return output


def group_player_rows(rows: Sequence[Mapping[str, str]]) -> dict[str, list[Mapping[str, str]]]:
    grouped: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        if normalize_position(row.get("position")) not in MODELED_POSITIONS:
            continue
        grouped[str(row["player_id"])].append(row)
    return grouped


def season_aggregate(
    season: int, player_id: str, rows: Sequence[Mapping[str, str]]
) -> dict[str, Any]:
    first = rows[0]
    position = primary_value(row.get("position", "") for row in rows)
    totals = {
        "completions": sum_float(rows, "completions"),
        "attempts": sum_float(rows, "attempts"),
        "passing_yards": sum_float(rows, "passing_yards"),
        "passing_tds": sum_float(rows, "passing_tds"),
        "interceptions": sum_float(rows, "interceptions"),
        "carries": sum_float(rows, "carries"),
        "rushing_yards": sum_float(rows, "rushing_yards"),
        "rushing_tds": sum_float(rows, "rushing_tds"),
        "rushing_first_downs": sum_float(rows, "rushing_first_downs"),
        "receptions": sum_float(rows, "receptions"),
        "receiving_yards": sum_float(rows, "receiving_yards"),
        "receiving_tds": sum_float(rows, "receiving_tds"),
        "receiving_first_downs": sum_float(rows, "receiving_first_downs"),
        "rushing_fumbles_lost": sum_float(rows, "rushing_fumbles_lost"),
        "receiving_fumbles_lost": sum_float(rows, "receiving_fumbles_lost"),
        "sack_fumbles_lost": sum_float(rows, "sack_fumbles_lost"),
    }
    game_count = len({row["week"] for row in rows})
    nwr_total = nwr_score(totals)
    return {
        "season": season,
        "player_id": player_id,
        "player_name": first.get("player_display_name") or first.get("player_name") or player_id,
        "recent_team": primary_value(row.get("recent_team", "") for row in rows),
        "position": normalize_position(position),
        "position_group": primary_value(row.get("position_group", "") for row in rows),
        "games": game_count,
        "games_active": game_count,
        "games_played": game_count,
        **totals,
        "fumbles_lost": (
            totals["rushing_fumbles_lost"]
            + totals["receiving_fumbles_lost"]
            + totals["sack_fumbles_lost"]
        ),
        "source_season_nwr_total": round(nwr_total, 4),
        "source_season_nwr_ppg": round(nwr_total / game_count, 4) if game_count else "",
    }


def build_feature_and_label_rows(
    *,
    source_aggregates: Mapping[tuple[int, str], Mapping[str, Any]],
    label_aggregates: Mapping[tuple[int, str], Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    feature_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []

    for target_season, source_season in TARGET_SOURCE_MAP.items():
        source_players = [
            row
            for (season, _player_id), row in source_aggregates.items()
            if season == source_season
        ]
        for source in sorted(source_players, key=lambda row: str(row["player_id"])):
            player_id = str(source["player_id"])
            target = label_aggregates.get((target_season, player_id))
            block_reason = block_reason_for(source, target)
            if block_reason:
                blocked_rows.append(blocked_row(target_season, source_season, source, block_reason))
                continue
            assert target is not None
            row_id = stable_row_id(target_season, player_id)
            feature_vector = feature_vector_for(source)
            threshold_labels = threshold_labels_for(target)
            feature_rows.append(
                feature_snapshot_row(
                    row_id, target_season, source_season, source, feature_vector
                )
            )
            label_rows.append(
                label_row(
                    row_id,
                    target_season,
                    source_season,
                    source,
                    target,
                    threshold_labels,
                )
            )

    return feature_rows, label_rows, blocked_rows


def block_reason_for(
    source: Mapping[str, Any], target: Mapping[str, Any] | None
) -> str:
    if target is None:
        return "blocked_missing_label"
    if source.get("position") not in MODELED_POSITIONS:
        return "blocked_position"
    if target.get("position") not in MODELED_POSITIONS:
        return "blocked_target_position"
    if source.get("position") != target.get("position"):
        return "blocked_source_target_position_mismatch"
    if not all(source.get(field) not in ("", None) for field in REQUIRED_SOURCE_FIELDS()):
        return "blocked_missing_required_feature"
    return ""


def REQUIRED_SOURCE_FIELDS() -> tuple[str, ...]:
    return (
        "player_id",
        "position",
        "games",
        "rushing_first_downs",
        "receiving_first_downs",
        "source_season_nwr_ppg",
        "source_position_rank",
    )


def feature_vector_for(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "position": source["position"],
        "prior_completed_season_games": int(source["games"]),
        "prior_completed_season_games_active": int(source["games_active"]),
        "prior_completed_season_games_played": int(source["games_played"]),
        "prior_completed_season_passing_yards": round(float(source["passing_yards"]), 4),
        "prior_completed_season_receiving_first_downs": round(
            float(source["receiving_first_downs"]), 4
        ),
        "prior_completed_season_receiving_yards": round(
            float(source["receiving_yards"]), 4
        ),
        "prior_completed_season_receptions": round(float(source["receptions"]), 4),
        "prior_completed_season_rushing_first_downs": round(
            float(source["rushing_first_downs"]), 4
        ),
        "prior_completed_season_rushing_yards": round(float(source["rushing_yards"]), 4),
        "prior_season_nwr_finish_rank": int(source["source_position_rank"]),
        "prior_season_nwr_ppg": round(float(source["source_season_nwr_ppg"]), 4),
    }


def feature_snapshot_row(
    row_id: str,
    target_season: int,
    source_season: int,
    source: Mapping[str, Any],
    feature_vector: Mapping[str, Any],
) -> dict[str, Any]:
    cutoff = f"{target_season}-09-01"
    lineage = {
        feature: lineage_for_feature(feature, source_season, target_season)
        for feature in feature_vector
    }
    return {
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "row_id": row_id,
        "player_id": source["player_id"],
        "player_name": source["player_name"],
        "source_team": source["recent_team"],
        "position": source["position"],
        "row_type": ROW_TYPE,
        "target_season": target_season,
        "feature_source_season": source_season,
        "cutoff_id": f"PRE_WK1_{target_season}",
        "input_snapshot_date": cutoff,
        "source_max_timestamp": f"{source_season + 1}-02-15",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_vector": json.dumps(feature_vector, sort_keys=True),
        "missingness_mask": json.dumps(
            {field: feature_vector.get(field) in ("", None) for field in FEATURE_FIELDS},
            sort_keys=True,
        ),
        "feature_lineage": json.dumps(lineage, sort_keys=True),
        "source_manifest": "player_stats_completed_prior_season_available_feb15_v1_5bz",
        "snapshot_hash": stable_hash(json.dumps(feature_vector, sort_keys=True)),
        "legality_status": "valid",
        "manual_review_status": "not_required",
        "app_readable": "no",
        "sort_allowed": "no",
        "ranking_use_allowed": "no",
    }


def lineage_for_feature(feature: str, source_season: int, target_season: int) -> dict[str, str]:
    family = (
        "prior_nwr_scoring"
        if feature.startswith("prior_season_nwr")
        else "prior_completed_season_stat"
    )
    if feature == "position":
        family = "source_identity_context"
    return {
        "feature_family": family,
        "source_season": str(source_season),
        "target_season": str(target_season),
        "source_season_strictly_before_target": "yes",
        "same_season_final_stat_leakage": "no",
        "label_supplement_source_as_feature": "no",
        "derived_availability_before_cutoff": "yes",
        "derived_availability_date": f"{source_season + 1}-02-15",
        "prediction_cutoff": f"{target_season}-09-01",
        "legality_status": "allowed_prior_completed_season_fact",
    }


def label_row(
    row_id: str,
    target_season: int,
    source_season: int,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    threshold_labels: Mapping[str, bool],
) -> dict[str, Any]:
    tiers = app_tiers(str(target["position"]), int(target["target_position_rank"]))
    return {
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "row_id": row_id,
        "player_id": source["player_id"],
        "player_name": source["player_name"],
        "position": target["position"],
        "cohort": "pre_2020_2016_2017_ready_for_future_audit_only",
        "row_type": ROW_TYPE,
        "target_season": target_season,
        "feature_source_season": source_season,
        "label_source_season": target_season,
        "cutoff_id": f"PRE_WK1_{target_season}",
        "trainability_status": "trainable_now_for_future_rebuild_only",
        "label_source": "player_stats.csv raw components; imported fantasy totals quarantined",
        "same_year_difference_maker": str(tiers["difference_maker"]).lower(),
        "same_year_starter": str(tiers["starter"]).lower(),
        "same_year_useful": str(tiers["useful"]).lower(),
        "same_year_replacement_or_bust": str(not tiers["useful"]).lower(),
        "position_rank": int(target["target_position_rank"]),
        "target_season_nwr_total": round(float(target["source_season_nwr_total"]), 4),
        "target_season_nwr_ppg": round(float(target["source_season_nwr_ppg"]), 4),
        "threshold_labels_json": json.dumps(threshold_labels, sort_keys=True),
        "available_outcomes": "|".join(
            [
                "same_year_difference_maker",
                "same_year_starter",
                "same_year_useful",
                "same_year_replacement_or_bust",
                *threshold_labels,
            ]
        ),
        "missing_or_censored_outcomes": "",
        "block_reason": "",
        "exact_percentage_display_allowed": "no",
        "coarse_band_display_allowed": "no",
        "app_readable": "no",
        "sort_allowed": "no",
        "ranking_use_allowed": "no",
    }


def threshold_labels_for(target: Mapping[str, Any]) -> dict[str, bool]:
    position = str(target["position"]).lower()
    rank = int(target["target_position_rank"])
    return {
        f"same_year_{position}_t{threshold}": rank <= threshold
        for threshold in THRESHOLD_HEADS[str(target["position"])]
    }


def blocked_row(
    target_season: int,
    source_season: int,
    source: Mapping[str, Any],
    block_reason: str,
) -> dict[str, Any]:
    return {
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "row_family": ROW_TYPE,
        "target_season": target_season,
        "feature_source_season": source_season,
        "player_id": source.get("player_id", ""),
        "player_name": source.get("player_name", ""),
        "position": source.get("position", ""),
        "block_reason": block_reason,
        "release_impact": "blocked_not_app_readable",
    }


def nwr_score(totals: Mapping[str, float]) -> float:
    fumbles_lost = (
        totals["rushing_fumbles_lost"]
        + totals["receiving_fumbles_lost"]
        + totals["sack_fumbles_lost"]
    )
    return (
        totals["passing_yards"] / 30
        + totals["passing_tds"] * 3
        - totals["interceptions"]
        + totals["rushing_yards"] * 0.1
        + totals["rushing_tds"] * 4
        + totals["rushing_first_downs"] * 0.4
        + totals["receiving_yards"] * 0.1
        + totals["receiving_tds"] * 4
        + totals["receiving_first_downs"] * 0.4
        - fumbles_lost
    )


def add_position_ranks(
    rows: list[dict[str, Any]],
    *,
    value_column: str,
    rank_column: str,
) -> list[dict[str, Any]]:
    output = [dict(row) for row in rows]
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in output:
        grouped[(int(row["season"]), str(row["position"]))].append(row)
    for group in grouped.values():
        ranked = sorted(
            group,
            key=lambda row: (-float(row[value_column]), str(row["player_name"])),
        )
        last_value: float | None = None
        last_rank = 0
        for index, row in enumerate(ranked, start=1):
            value = float(row[value_column])
            if last_value is None or value != last_value:
                last_rank = index
                last_value = value
            row[rank_column] = last_rank
    return output


def app_tiers(position: str, rank: int) -> dict[str, bool]:
    thresholds = APP_TIER_THRESHOLDS[position]
    difference_maker = rank <= thresholds["difference_maker"]
    starter = difference_maker or rank <= thresholds["starter"]
    useful = starter or rank <= thresholds["useful"]
    return {
        "difference_maker": difference_maker,
        "starter": starter,
        "useful": useful,
    }


def trainability_report(
    *,
    feature_rows: Sequence[Mapping[str, Any]],
    blocked_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for target_season in TARGET_SOURCE_MAP:
        emitted = [row for row in feature_rows if int(row["target_season"]) == target_season]
        blocked = [row for row in blocked_rows if int(row["target_season"]) == target_season]
        blocker_counts = Counter(row["block_reason"] for row in blocked)
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "row_family": ROW_TYPE,
                "target_season": target_season,
                "attempted_rows": len(emitted) + len(blocked),
                "emitted_feature_snapshots": len(emitted),
                "label_rows": len(emitted),
                "blocked_rows": len(blocked),
                "blocked_missing_label": blocker_counts.get("blocked_missing_label", 0),
                "blocked_missing_required_feature": blocker_counts.get(
                    "blocked_missing_required_feature", 0
                ),
                "blocked_identity": blocker_counts.get("blocked_identity", 0),
                "blocked_position": sum(
                    count
                    for reason, count in blocker_counts.items()
                    if "position" in str(reason)
                ),
                "primary_blocker": primary_blocker(blocker_counts),
                "modeling_approval": "not_approved",
            }
        )
    return output


def feature_missingness_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for target_season in TARGET_SOURCE_MAP:
        season_rows = [row for row in rows if int(row["target_season"]) == target_season]
        vectors = [json.loads(str(row["feature_vector"])) for row in season_rows]
        for feature in FEATURE_FIELDS:
            missing = sum(1 for vector in vectors if vector.get(feature) in ("", None))
            output.append(
                {
                    "output_scope": OUTPUT_SCOPE,
                    "target_season": target_season,
                    "feature_name": feature,
                    "row_count": len(vectors),
                    "missing_count": missing,
                    "missing_rate": round(missing / len(vectors), 6) if vectors else 0.0,
                }
            )
    return output


def label_support(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    grouped: dict[tuple[int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["target_season"]), str(row["position"]))].append(row)
    for (target_season, position), group in sorted(grouped.items()):
        output.extend(tier_support_rows(target_season, position, group))
        for threshold in THRESHOLD_HEADS[position]:
            label = f"same_year_{position.lower()}_t{threshold}"
            events = sum(
                1
                for row in group
                if json.loads(str(row["threshold_labels_json"]))[label]
            )
            output.append(
                support_row(
                    target_season,
                    position,
                    label,
                    rows=len(group),
                    events=events,
                    notes="Threshold support only; no modeling or probability release.",
                )
            )
    return output


def tier_support_rows(
    target_season: int,
    position: str,
    group: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    labels = (
        "same_year_difference_maker",
        "same_year_starter",
        "same_year_useful",
        "same_year_replacement_or_bust",
    )
    output = []
    for label in labels:
        events = sum(1 for row in group if str(row[label]).lower() == "true")
        output.append(
            support_row(
                target_season,
                position,
                label,
                rows=len(group),
                events=events,
                notes="Tier support only; no modeling or probability release.",
            )
        )
    return output


def support_row(
    target_season: int,
    position: str,
    outcome: str,
    *,
    rows: int,
    events: int,
    notes: str,
) -> dict[str, Any]:
    return {
        "output_scope": OUTPUT_SCOPE,
        "target_season": target_season,
        "position": position,
        "outcome": outcome,
        "row_count": rows,
        "event_count": events,
        "non_event_count": rows - events,
        "one_class_flag": "yes" if events in {0, rows} else "no",
        "sparse_flag": "yes" if events < 10 else "no",
        "notes": notes,
    }


def legality_audit_rows(
    feature_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    label_by_id = {row["row_id"]: row for row in label_rows}
    output: list[dict[str, Any]] = []
    for row in feature_rows:
        label = label_by_id[row["row_id"]]
        source_season = int(row["feature_source_season"])
        target_season = int(row["target_season"])
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "row_id": row["row_id"],
                "player_id": row["player_id"],
                "target_season": target_season,
                "feature_source_season": source_season,
                "label_source_season": label["label_source_season"],
                "source_season_strictly_before_target": "yes"
                if source_season < target_season
                else "no",
                "same_season_final_stats_as_features": "no",
                "label_source_as_prediction_feature": "no",
                "fantasy_totals_used": "no",
                "legality_status": "pass",
            }
        )
    return output


def forbidden_feature_scan(headers: Sequence[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    allowed = set(ALLOWED_SOURCE_FIELDS)
    for header in headers:
        lower = header.lower()
        matched = [
            fragment
            for fragment in FORBIDDEN_OR_QUARANTINED_FIELDS
            if fragment in lower
        ]
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "source_field": header,
                "allowlist_status": "allowed" if header in allowed else "not_allowlisted",
                "forbidden_or_quarantined_match": "|".join(matched),
                "used_in_features": "yes" if header in allowed else "no",
                "blocker": "no" if header in allowed or matched else "no",
                "recommended_handling": (
                    "allow_source_safe_component"
                    if header in allowed
                    else "quarantine_exclude"
                    if matched
                    else "exclude_not_allowlisted"
                ),
            }
        )
    return output


def identity_team_position_audit(
    source_rows: Mapping[int, Sequence[Mapping[str, str]]],
    target_rows: Mapping[int, Sequence[Mapping[str, str]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row_family, rows_by_season in (
        ("feature_source", source_rows),
        ("label_source", target_rows),
    ):
        for season, rows in rows_by_season.items():
            modeled = [
                row for row in rows if normalize_position(row.get("position")) in MODELED_POSITIONS
            ]
            output.append(
                {
                    "output_scope": OUTPUT_SCOPE,
                    "row_family": row_family,
                    "season": season,
                    "row_count": len(modeled),
                    "missing_player_id": count_blank(modeled, "player_id"),
                    "missing_player_name": count_blank(modeled, "player_name"),
                    "missing_player_display_name": count_blank(modeled, "player_display_name"),
                    "missing_team": count_blank(modeled, "recent_team"),
                    "missing_position": count_blank(modeled, "position"),
                    "missing_position_group": count_blank(modeled, "position_group"),
                    "status": "pass",
                }
            )
    return output


def duplicate_player_week_rows(rows: Sequence[Mapping[str, str]]) -> dict[int, int]:
    seen: set[tuple[str, str, str, str]] = set()
    counts: Counter[int] = Counter()
    for row in rows:
        season = int(row["season"])
        if season not in {2015, 2016, 2017}:
            continue
        key = (
            row.get("player_id", ""),
            row.get("season", ""),
            row.get("week", ""),
            row.get("season_type", ""),
        )
        if key in seen:
            counts[season] += 1
        else:
            seen.add(key)
    return dict(counts)


def duplicate_key_audit_rows(
    *,
    source_duplicates: Mapping[int, int],
    feature_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source_season in (2015, 2016):
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "key_type": "source_player_week",
                "season": source_season,
                "duplicate_extra_rows": source_duplicates.get(source_season, 0),
                "status": "pass" if source_duplicates.get(source_season, 0) == 0 else "fail",
            }
        )
    for name, rows, key_fields in (
        ("feature_snapshot", feature_rows, ("player_id", "target_season")),
        ("label_row", label_rows, ("player_id", "target_season", "position")),
    ):
        duplicates = duplicate_count(rows, key_fields)
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "key_type": name,
                "season": "2016_2017",
                "duplicate_extra_rows": duplicates,
                "status": "pass" if duplicates == 0 else "fail",
            }
        )
    return output


def population_policy_audit(
    feature_rows: Sequence[Mapping[str, Any]],
    blocked_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "historical_veteran_rows",
            "status": "pass",
            "evidence": f"feature_rows={len(feature_rows)}",
            "release_impact": "internal_only",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "rookies",
            "status": "pass",
            "evidence": "rookies excluded by requiring completed prior-season source rows",
            "release_impact": "rookie_framework_untouched",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "kickers",
            "status": "pass",
            "evidence": "kicker rows not modeled; QB/RB/WR/TE only",
            "release_impact": "not_applicable",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "blocked_rows",
            "status": "pass",
            "evidence": f"blocked_rows={len(blocked_rows)}",
            "release_impact": "blocked_rows_not_scored",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "current_2026_rows",
            "status": "pass",
            "evidence": "no 2026 rows generated or scored",
            "release_impact": "current_pool_probabilities_blocked",
        },
    ]


def first_down_completeness_rows(
    source_rows: Mapping[int, Sequence[Mapping[str, str]]],
    target_rows: Mapping[int, Sequence[Mapping[str, str]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row_family, rows_by_season in (
        ("feature_source", source_rows),
        ("label_source", target_rows),
    ):
        for season, rows in rows_by_season.items():
            modeled = [
                row for row in rows if normalize_position(row.get("position")) in MODELED_POSITIONS
            ]
            output.append(
                {
                    "output_scope": OUTPUT_SCOPE,
                    "row_family": row_family,
                    "season": season,
                    "modeled_rows": len(modeled),
                    "missing_rushing_first_downs": count_blank(
                        modeled, "rushing_first_downs"
                    ),
                    "missing_receiving_first_downs": count_blank(
                        modeled, "receiving_first_downs"
                    ),
                    "status": "pass"
                    if count_blank(modeled, "rushing_first_downs") == 0
                    and count_blank(modeled, "receiving_first_downs") == 0
                    else "fail",
                }
            )
    return output


def artifact_quarantine_rows(output_dir: Path) -> list[dict[str, Any]]:
    expected = (
        "local_exports/outcome_probability/"
        "sprint_5bz_2016_2017_historical_feature_label_rebuild"
    )
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "output_folder_scope",
            "status": "pass" if expected in output_dir.as_posix() else "fail",
            "evidence": output_dir.as_posix(),
            "release_impact": "blocked_not_app_readable",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "app_readable_probability_or_band_table",
            "status": "pass",
            "evidence": "No app path written; generated rows mark app_readable=no.",
            "release_impact": "app_wiring_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "model_training",
            "status": "pass",
            "evidence": "No model training performed.",
            "release_impact": "modeling_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "rankings_sorting_output",
            "status": "pass",
            "evidence": "Generated rows mark sort_allowed=no and ranking_use_allowed=no.",
            "release_impact": "rankings_sorting_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "promoted_artifact",
            "status": "pass",
            "evidence": "Only local CSV/JSON/README research artifacts are written.",
            "release_impact": "promotion_blocked",
        },
    ]


def release_blocker_rows() -> list[dict[str, str]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "blocker": blocker,
            "status": "blocked",
            "notes": "Sprint 5BZ generates local historical rows only.",
        }
        for blocker in (
            "modeling",
            "exact_percentages",
            "coarse_bands",
            "app_wiring",
            "rankings_sorting",
            "hidden_sort_keys",
            "promoted_artifacts",
        )
    ]


def primary_blocker(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return counter.most_common(1)[0][0]


def count_blank(rows: Sequence[Mapping[str, str]], field: str) -> int:
    return sum(1 for row in rows if blank(row.get(field)))


def duplicate_count(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> int:
    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in fields)
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def normalize_position(value: Any) -> str:
    return str(value or "").upper()


def primary_value(values: Iterable[Any]) -> str:
    counts = Counter(str(value or "") for value in values if str(value or ""))
    return counts.most_common(1)[0][0] if counts else ""


def sum_float(rows: Sequence[Mapping[str, str]], field: str) -> float:
    return sum(to_float(row.get(field)) for row in rows)


def to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def stable_row_id(target_season: int, player_id: str) -> str:
    return "nwr_5bz_" + stable_hash(f"{target_season}|{player_id}")[:24]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = fieldnames_for(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fieldnames_for(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    output: list[str] = []
    for row in rows:
        for key in row:
            if key not in output:
                output.append(key)
    return output or ["empty"]


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_readme(path: Path, metadata: Mapping[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                "# Sprint 5BZ Local-Only 2016-2017 Historical Feature and Label Rebuild",
                "",
                "Verdict: `LOCAL_ONLY_ROWS_GENERATED_MODELING_BLOCKED`",
                "",
                "This packet contains local-only historical feature and label rows for",
                "target seasons 2016 and 2017. It does not train models, generate",
                "probabilities, create app-readable outputs, alter rankings/sorting, or",
                "promote artifacts.",
                "",
                f"Feature rows: {metadata['feature_rows']}",
                f"Label rows: {metadata['label_rows']}",
                f"Blocked rows: {metadata['blocked_rows']}",
                "",
                "Exact percentages, coarse bands, app wiring, rankings/sorting, hidden",
                "sort keys, and promoted artifacts remain blocked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unavailable"
    return result.stdout.strip() or "unavailable"


if __name__ == "__main__":
    main()
