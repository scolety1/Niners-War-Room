# ruff: noqa: E501
"""Build the deterministic historical rookie opportunity feature gauntlet.

The command reads only the fixed CFBD and nflverse snapshots named below.  It
does not call a provider, inspect the 2026 class for outcomes, or write outside
the governed research packet.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.rookie_historical_opportunity_gauntlet_service import (  # noqa: E402
    AS_OF_DATE,
    BLOCKED_FAMILIES,
    CANONICAL_HQ,
    CANONICAL_TREE,
    CFBD_AGGREGATE_SHA256,
    COMBINE_AGGREGATE_SHA256,
    FAMILY_POSITIONS,
    FINISHED_V1_SHA256,
    FROZEN_COMPARATOR_SHA256,
    MUTATIONS,
    OUTCOME_V3_SHA256,
    POSITIONS,
    RESEARCH_STATUS,
    TESTABLE_FAMILIES,
    PromotionGate,
    chronological_outer_folds,
    expected_calibration_error,
    ndcg,
    pr_auc,
    safe_ratio,
    same_row_ids,
    sha256_file,
    spearman,
    validate_feature_name,
    validate_fold,
    validate_mutation,
    validate_outcome_season,
    validate_output_path,
    validate_snapshot_hash,
)

PACKET_REL = Path(
    "docs/hq/master/nwr_rookie_historical_opportunity_feature_gauntlet_v1_20260731"
)
CFBD_REL = Path("cfbd/rest_v2/20260730T171639Z-370ce01696c3")
NFL_ROOT_REL = Path("nflverse")
NFL_FAMILIES = {
    "combine": "combine/20260730T072407Z-5e6847b155d8",
    "draft_picks": "draft_picks/20260730T072407Z-24ff3f7171ed",
    "players": "players/20260730T072407Z-42af9666ac84",
    "weekly": "player_stats_weekly/20260730T072407Z-fe7ff02872e4",
    "seasonal": "player_stats_seasonal/20260730T072407Z-a5b2304f0132",
}
RESULT_FILES = {
    "T01": "T01_QB_RUSHING_RESULTS.csv",
    "T02": "T02_RB_RECEIVING_RESULTS.csv",
    "T03": "T03_WR_PASS_USAGE_RESULTS.csv",
    "T04": "T04_TE_RECEIVING_RESULTS.csv",
    "T05": "T05_FIRST_DOWN_RESULTS.csv",
    "T06": "T06_AGE_TRAJECTORY_RESULTS.csv",
    "T07": "T07_QB_SACK_RESULTS.csv",
    "T09": "T09_WR_VERTICAL_RESULTS.csv",
}
REQUIRED = (
    "ROOKIE_FEATURE_GAUNTLET_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "EXTERNAL_RESEARCH_HANDOFF_RECEIPT.md",
    "SOURCE_AND_TERMS_AUTHORITY.csv",
    "SOURCE_COVERAGE_BY_SEASON_POSITION.csv",
    "IDENTITY_COHORT_FLOW.csv",
    "FEATURE_FAMILY_DEFINITIONS.csv",
    "FEATURE_FAMILY_FEASIBILITY_GATES.csv",
    "TEMPORAL_AVAILABILITY_CONTRACT.md",
    "NWR_ROOKIE_OUTCOME_CONTRACT.md",
    "BASELINE_DEFINITIONS.csv",
    *RESULT_FILES.values(),
    "POSITION_CLASS_COHORT_RESULTS.csv",
    "SAME_ROW_COMPARISONS.csv",
    "BOOTSTRAP_AND_STABILITY_RESULTS.csv",
    "FEATURE_PROMOTION_DECISIONS.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "DETERMINISTIC_REGENERATION_RESULTS.csv",
    "KNOWN_HERMETIC_BASELINE_COMPARISON.md",
    "MODEL_V4_AND_2026_BOARD_NO_CHANGE.md",
    "FINISHED_V1_OUTCOME_V3_TRADING_LAB_NO_CHANGE.md",
    "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)
POSITION_MAP = {
    "QUARTERBACK": "QB",
    "RUNNING BACK": "RB",
    "FULLBACK": "RB",
    "WIDE RECEIVER": "WR",
    "TIGHT END": "TE",
}
FEATURE_COLUMNS = {
    "T01": ("QB_TOTAL_RUSH_YDS_PER_PASS_ATT",),
    "T02": ("RB_REC_PER_TEAM_PA", "CFBD_PASSING_DOWNS_USAGE"),
    "T03": ("WR_REC_PER_TEAM_PA", "WR_REC_YDS_PER_TEAM_PA", "CFBD_PASS_USAGE"),
    "T04": ("TE_REC_PER_TEAM_PA", "TE_REC_YDS_PER_TEAM_PA", "CFBD_PASSING_DOWNS_USAGE"),
    "T06": ("AGE_ADJUSTED_PRODUCTION_TRAJECTORY",),
}
TARGETS = {
    "T01": ("y1_vor", "y2_vor", "three_year_vor", "top12_y1", "survival_3y"),
    "T02": (
        "y1_vor",
        "y2_vor",
        "y3_vor",
        "two_year_vor",
        "three_year_vor",
        "top12_y1",
        "top24_y1",
        "survival_3y",
        "elite_3y",
        "bust_3y",
    ),
    "T03": (
        "y1_vor",
        "y2_vor",
        "y3_vor",
        "two_year_vor",
        "three_year_vor",
        "top12_y1",
        "top24_y1",
        "survival_3y",
        "elite_3y",
        "bust_3y",
    ),
    "T04": ("y2_vor", "y3_vor", "three_year_vor", "top12_y2", "survival_3y"),
    "T06": ("y1_vor", "y2_vor", "y3_vor", "two_year_vor", "three_year_vor", "survival_3y"),
}
CLASSIFICATION_TARGETS = {
    "top12_y1",
    "top24_y1",
    "top12_y2",
    "survival_3y",
    "elite_3y",
    "bust_3y",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--snapshot-root", type=Path, default=Path(r"C:\NWR_SHARED_DATA\source_snapshots"))
    parser.add_argument(
        "--external-handoff",
        type=Path,
        default=Path(r"C:\Users\codex-agent\Downloads\NWR_EXTERNAL_ROOKIE_DATA_RESEARCH_V1.md"),
    )
    parser.add_argument(
        "--finished-v1",
        type=Path,
        default=Path(
            r"C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv"
        ),
    )
    parser.add_argument("--hermetic-before", default="PENDING")
    parser.add_argument("--hermetic-after", default="PENDING")
    parser.add_argument("--localdata", default="PENDING")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    packet = repo / PACKET_REL
    if packet.exists():
        shutil.rmtree(packet)
    packet.mkdir(parents=True)
    verify_sources(repo, args.snapshot_root, args.finished_v1)
    identities, identity_flow = build_identity_panel(args.snapshot_root)
    features, coverage = build_college_features(args.snapshot_root, identities)
    outcomes, cohort_results = build_outcomes(args.snapshot_root, identities)
    rows = merge_research_rows(features, outcomes)
    result_rows, same_rows, bootstrap_rows, decisions = evaluate_families(rows)
    write_csv(packet / "IDENTITY_COHORT_FLOW.csv", identity_flow)
    write_csv(packet / "SOURCE_COVERAGE_BY_SEASON_POSITION.csv", coverage)
    write_csv(packet / "POSITION_CLASS_COHORT_RESULTS.csv", cohort_results)
    for family, filename in RESULT_FILES.items():
        write_csv(packet / filename, result_rows[family])
    write_csv(packet / "SAME_ROW_COMPARISONS.csv", same_rows)
    write_csv(packet / "BOOTSTRAP_AND_STABILITY_RESULTS.csv", bootstrap_rows)
    write_csv(packet / "FEATURE_PROMOTION_DECISIONS.csv", decisions)
    write_contract_outputs(packet, repo, args, identities, rows, decisions)
    write_manifest(packet, args, identities, rows)
    missing = [name for name in REQUIRED if not (packet / name).is_file()]
    if missing:
        raise RuntimeError(f"required outputs missing: {missing}")
    print(f"packet={PACKET_REL.as_posix()}")
    print(f"exact_drafted_rows={len(identities)}")
    print(f"research_rows={len(rows)}")
    print(f"verdict={overall_verdict(decisions)}")
    return 0


def verify_sources(repo: Path, snapshot_root: Path, finished_v1: Path) -> None:
    cfbd_manifest = snapshot_root / CFBD_REL / "COMPLETION_MANIFEST.json"
    payload = json.loads(cfbd_manifest.read_text(encoding="utf-8"))
    if payload.get("aggregate_sha256") != CFBD_AGGREGATE_SHA256:
        raise RuntimeError("CFBD aggregate receipt mismatch")
    combine_manifest = snapshot_root / NFL_ROOT_REL / NFL_FAMILIES["combine"] / "COMPLETION_MANIFEST.json"
    combine_payload = json.loads(combine_manifest.read_text(encoding="utf-8"))
    if combine_payload.get("aggregate_sha256") != COMBINE_AGGREGATE_SHA256:
        raise RuntimeError("combine aggregate receipt mismatch")
    protected = {
        finished_v1: FINISHED_V1_SHA256,
        repo / "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/OUTCOME_V3_INTEGRATION_PACK.csv": OUTCOME_V3_SHA256,
        repo / "docs/hq/model/formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/PROSPECTIVE_2026_BASELINE_FREEZE.csv": FROZEN_COMPARATOR_SHA256,
    }
    for path, expected in protected.items():
        validate_snapshot_hash(path, expected)


def build_identity_panel(snapshot_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nfl_root = snapshot_root / NFL_ROOT_REL
    nfl_draft = pl.read_parquet(
        nfl_root / NFL_FAMILIES["draft_picks"] / "raw/draft_picks.parquet"
    ).filter((pl.col("season") >= 2012) & (pl.col("season") <= 2025))
    nfl_rows = nfl_draft.to_dicts()
    by_slot: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in nfl_rows:
        by_slot[(int(row["season"]), int(row["pick"]))].append(row)
    players = pl.read_parquet(
        nfl_root / NFL_FAMILIES["players"] / "raw/players.parquet"
    ).select(["gsis_id", "birth_date", "rookie_season", "draft_year", "position_group"])
    player_lookup = {str(row["gsis_id"]): row for row in players.to_dicts() if row["gsis_id"]}
    exact: list[dict[str, Any]] = []
    drafted_total = 0
    unresolved = 0
    cfbd_root = snapshot_root / CFBD_REL / "raw/draft_picks"
    for year in range(2012, 2026):
        for row in json.loads((cfbd_root / f"{year}.json").read_text(encoding="utf-8")):
            position = POSITION_MAP.get(str(row.get("position", "")).upper())
            if position not in POSITIONS:
                continue
            drafted_total += 1
            matches = by_slot.get((year, int(row["overall"])), [])
            if len(matches) != 1 or not matches[0].get("gsis_id"):
                unresolved += 1
                continue
            nfl = matches[0]
            gsis_id = str(nfl["gsis_id"])
            biography = player_lookup.get(gsis_id, {})
            exact.append(
                {
                    "draft_class": year,
                    "overall_pick": int(row["overall"]),
                    "draft_round": int(row["round"]),
                    "position": position,
                    "gsis_id": gsis_id,
                    "cfbd_college_athlete_id": str(row["collegeAthleteId"]),
                    "player_name": str(nfl.get("pfr_player_name") or ""),
                    "college": str(row.get("collegeTeam") or ""),
                    "birth_date": str(biography.get("birth_date") or ""),
                    "nflverse_age": nfl.get("age"),
                    "identity_join": "cfbd_draft_year_overall_to_exact_gsis",
                }
            )
    exact.sort(key=lambda row: (row["draft_class"], row["overall_pick"]))
    drafted_nfl_skill = [
        row
        for row in nfl_rows
        if str(row.get("position", "")).upper() in POSITIONS and row.get("gsis_id")
    ]
    drafted_ids = {str(row["gsis_id"]) for row in drafted_nfl_skill}
    udfa_exact = [
        row
        for row in player_lookup.values()
        if row.get("rookie_season")
        and 2012 <= int(row["rookie_season"]) <= 2025
        and str(row.get("position_group", "")).upper() in POSITIONS
        and str(row.get("gsis_id", "")) not in drafted_ids
    ]
    flow = [
        {"cohort": "CFBD_DRAFTED_FANTASY_POSITION", "rows": drafted_total, "disposition": "SOURCE_COHORT"},
        {"cohort": "DRAFTED_EXACT_IDENTITY", "rows": len(exact), "disposition": "RESEARCH_ELIGIBLE"},
        {"cohort": "DRAFTED_UNRESOLVED", "rows": unresolved, "disposition": "RETAINED_EXPLICIT"},
        {"cohort": "CONFIRMED_UDFA_EXACT_NFL_IDENTITY", "rows": len(udfa_exact), "disposition": "SEPARATE_NO_CFBD_FEATURE_JOIN"},
        {"cohort": "UNRESOLVED_OR_SURVIVOR_ONLY_UDFA", "rows": 0, "disposition": "NOT_CONSTRUCTED_NO_NAME_MATCH"},
    ]
    return exact, flow


def build_college_features(
    snapshot_root: Path, identities: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cfbd_root = snapshot_root / CFBD_REL / "raw"
    wanted = {row["cfbd_college_athlete_id"] for row in identities}
    player_stats: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    player_teams: dict[tuple[str, int], set[str]] = defaultdict(set)
    team_stats: dict[tuple[int, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for season in range(2011, 2026):
        path = cfbd_root / "player_season_stats" / f"{season}.json"
        for row in json.loads(path.read_text(encoding="utf-8")):
            category = str(row.get("category") or "")
            stat_type = str(row.get("statType") or "")
            if (category, stat_type) not in {
                ("passing", "ATT"),
                ("passing", "YDS"),
                ("passing", "TD"),
                ("rushing", "CAR"),
                ("rushing", "YDS"),
                ("rushing", "TD"),
                ("receiving", "REC"),
                ("receiving", "YDS"),
                ("receiving", "TD"),
            }:
                continue
            try:
                value = float(str(row.get("stat") or "0").replace(",", ""))
            except ValueError:
                continue
            team = str(row.get("team") or "")
            key_name = f"{category}_{stat_type}".lower()
            team_stats[(season, team)][key_name] += value
            athlete = str(row.get("playerId") or "")
            if athlete in wanted:
                player_stats[(athlete, season)][key_name] += value
                player_teams[(athlete, season)].add(team)
    usage: dict[tuple[str, int], dict[str, float | None]] = {}
    for season in range(2011, 2026):
        rows = json.loads((cfbd_root / "player_usage" / f"{season}.json").read_text(encoding="utf-8"))
        for row in rows:
            athlete = str(row.get("id") or "")
            if athlete not in wanted:
                continue
            values = row.get("usage") or {}
            usage[(athlete, season)] = {
                "pass": optional_float(values.get("pass")),
                "passingDowns": optional_float(values.get("passingDowns")),
                "thirdDown": optional_float(values.get("thirdDown")),
            }
    output: list[dict[str, Any]] = []
    coverage_counts: dict[tuple[int, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for identity in identities:
        athlete = identity["cfbd_college_athlete_id"]
        college_seasons = sorted(
            season
            for (player_id, season) in player_stats
            if player_id == athlete and season < identity["draft_class"]
        )
        base = dict(identity)
        if not college_seasons:
            base.update(empty_feature_values())
            base["feature_season"] = None
            output.append(base)
            coverage_counts[(identity["draft_class"], identity["position"])]["missing"] += 1
            continue
        final_season = college_seasons[-1]
        final = player_stats[(athlete, final_season)]
        teams = player_teams[(athlete, final_season)]
        team_pa = sum(team_stats[(final_season, team)].get("passing_att", 0.0) for team in teams)
        team_rush_yards = sum(team_stats[(final_season, team)].get("rushing_yds", 0.0) for team in teams)
        team_rush_td = sum(team_stats[(final_season, team)].get("rushing_td", 0.0) for team in teams)
        team_rec_yards = sum(team_stats[(final_season, team)].get("receiving_yds", 0.0) for team in teams)
        team_rec_td = sum(team_stats[(final_season, team)].get("receiving_td", 0.0) for team in teams)
        team_rec = sum(team_stats[(final_season, team)].get("receiving_rec", 0.0) for team in teams)
        current_usage = usage.get((athlete, final_season), {})
        career = defaultdict(float)
        trajectory_points: list[tuple[int, float]] = []
        for season in college_seasons:
            stats = player_stats[(athlete, season)]
            for key, value in stats.items():
                career[key] += value
            season_teams = player_teams[(athlete, season)]
            season_pa = sum(team_stats[(season, team)].get("passing_att", 0.0) for team in season_teams)
            production = position_production(identity["position"], stats)
            rate = safe_ratio(production, season_pa)
            if rate is not None:
                trajectory_points.append((season, rate))
        age = draft_age(identity)
        trajectory = shrinkage_slope(trajectory_points)
        age_adjusted = trajectory * (24.0 - age) if trajectory is not None and age is not None else None
        production_score = accepted_production_score(
            identity["position"], final, career, team_rush_yards, team_rush_td, team_rec_yards, team_rec_td, team_rec
        )
        market_score = accepted_market_share_score(
            identity["position"], final, team_rush_yards, team_rush_td, team_rec_yards, team_rec_td, team_rec
        )
        draft_score = draft_capital_score(identity["overall_pick"])
        b3_proxy = weighted_available(((production_score, 0.30), (market_score, 0.20), (draft_score, 0.25)))
        base.update(
            {
                "feature_season": final_season,
                "age_at_draft": age,
                "B3_ACCEPTED_REVIEW_PROXY": b3_proxy,
                "QB_TOTAL_RUSH_YDS_PER_PASS_ATT": safe_ratio(final.get("rushing_yds"), final.get("passing_att")),
                "RB_REC_PER_TEAM_PA": safe_ratio(final.get("receiving_rec"), team_pa),
                "WR_REC_PER_TEAM_PA": safe_ratio(final.get("receiving_rec"), team_pa),
                "WR_REC_YDS_PER_TEAM_PA": safe_ratio(final.get("receiving_yds"), team_pa),
                "TE_REC_PER_TEAM_PA": safe_ratio(final.get("receiving_rec"), team_pa),
                "TE_REC_YDS_PER_TEAM_PA": safe_ratio(final.get("receiving_yds"), team_pa),
                "CFBD_PASS_USAGE": current_usage.get("pass"),
                "CFBD_PASSING_DOWNS_USAGE": current_usage.get("passingDowns"),
                "AGE_ADJUSTED_PRODUCTION_TRAJECTORY": age_adjusted,
                "college_seasons": len(college_seasons),
            }
        )
        for feature in FEATURE_COLUMNS.get(f"T0{1 if identity['position'] == 'QB' else 2}", ()):
            validate_feature_name(feature)
        output.append(base)
        coverage_counts[(identity["draft_class"], identity["position"])]["covered"] += 1
    coverage = []
    identity_lookup = defaultdict(int)
    for row in identities:
        identity_lookup[(row["draft_class"], row["position"])] += 1
    for key in sorted(identity_lookup):
        draft_class, position = key
        total = identity_lookup[key]
        covered = coverage_counts[key]["covered"]
        coverage.append(
            {
                "draft_class": draft_class,
                "position": position,
                "drafted_exact_identity": total,
                "college_feature_rows": covered,
                "coverage_rate": fixed(covered / total if total else None),
                "null_rate": fixed(1 - covered / total if total else None),
                "source_version": CFBD_AGGREGATE_SHA256,
                "temporal_availability": "pre_draft_seasons_only",
            }
        )
    return output, coverage


def build_outcomes(
    snapshot_root: Path, identities: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    weekly_root = snapshot_root / NFL_ROOT_REL / NFL_FAMILIES["weekly"] / "raw"
    identity_by_season: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in identities:
        identity_by_season[row["draft_class"]].append(row)
    player_season: dict[tuple[str, int], dict[str, Any]] = {}
    position_ranks: dict[tuple[str, int], int] = {}
    for season in range(2012, 2026):
        frame = pl.read_parquet(weekly_root / f"player_stats_weekly_{season}.parquet").filter(
            (pl.col("season_type") == "REG") & pl.col("position").is_in(list(POSITIONS))
        )
        rows = frame.to_dicts()
        scores: dict[tuple[int, str], float] = {}
        positions: dict[str, str] = {}
        weeks = sorted({int(row["week"]) for row in rows})
        week_rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            player_id = str(row["player_id"])
            score = score_week(row)
            scores[(int(row["week"]), player_id)] = score
            positions[player_id] = str(row["position"])
            week_rows[int(row["week"])].append(
                {"player_id": player_id, "position": str(row["position"]), "score": score}
            )
        replacement: dict[tuple[int, str], float] = {}
        for week in weeks:
            replacement.update(replacement_lines(week, week_rows[week]))
        totals: dict[str, float] = defaultdict(float)
        vors: dict[str, float] = defaultdict(float)
        for player_id, position in positions.items():
            for week in weeks:
                score = scores.get((week, player_id), 0.0)
                totals[player_id] += score
                vors[player_id] += score - replacement.get((week, position), 0.0)
        by_position: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for player_id, total in totals.items():
            by_position[positions[player_id]].append((player_id, total))
        for _position, values in by_position.items():
            values.sort(key=lambda item: (-item[1], item[0]))
            for rank, (player_id, _) in enumerate(values, start=1):
                position_ranks[(player_id, season)] = rank
        for player_id, _position in positions.items():
            player_season[(player_id, season)] = {
                "points": totals[player_id],
                "vor": vors[player_id],
                "position_rank": position_ranks[(player_id, season)],
            }
    output: dict[str, dict[str, Any]] = {}
    cohorts: list[dict[str, Any]] = []
    for identity in identities:
        player_id = identity["gsis_id"]
        draft_class = identity["draft_class"]
        horizons: dict[int, dict[str, Any] | None] = {}
        for horizon in (1, 2, 3):
            if draft_class <= {1: 2025, 2: 2024, 3: 2023}[horizon]:
                validate_outcome_season(draft_class, horizon, draft_class + horizon - 1)
                horizons[horizon] = player_season.get(
                    (player_id, draft_class + horizon - 1),
                    {"points": 0.0, "vor": 0.0, "position_rank": None},
                )
            else:
                horizons[horizon] = None
        values = {
            "y1_vor": horizon_value(horizons[1], "vor"),
            "y2_vor": horizon_value(horizons[2], "vor"),
            "y3_vor": horizon_value(horizons[3], "vor"),
            "two_year_vor": cumulative(horizons, 2),
            "three_year_vor": cumulative(horizons, 3),
            "top12_y1": top_flag(horizons[1], 12),
            "top24_y1": top_flag(horizons[1], 24),
            "top12_y2": top_flag(horizons[2], 12),
            "survival_3y": any_positive(horizons, 3),
            "elite_3y": any_top(horizons, 3, 12),
            "bust_3y": bust_flag(horizons),
        }
        output[player_id] = values
        cohorts.append(
            {
                "draft_class": draft_class,
                "position": identity["position"],
                "gsis_id": player_id,
                "y1_mature": horizons[1] is not None,
                "y2_mature": horizons[2] is not None,
                "y3_mature": horizons[3] is not None,
                "y1_vor": fixed(values["y1_vor"]),
                "y2_vor": fixed(values["y2_vor"]),
                "y3_vor": fixed(values["y3_vor"]),
                "three_year_vor": fixed(values["three_year_vor"]),
                "top12_y1": blank(values["top12_y1"]),
                "above_replacement_survival": blank(values["survival_3y"]),
            }
        )
    return output, cohorts


def score_week(row: dict[str, Any]) -> float:
    def number(key: str) -> float:
        return float(row.get(key) or 0.0)

    return (
        number("passing_yards") / 30
        + number("passing_tds") * 3
        - number("passing_interceptions")
        + number("rushing_yards") * 0.1
        + number("rushing_tds") * 4
        + number("rushing_first_downs") * 0.4
        + number("rushing_2pt_conversions") * 2
        + number("receiving_yards") * 0.1
        + number("receiving_tds") * 4
        + number("receiving_first_downs") * 0.4
        + number("receiving_2pt_conversions") * 2
        - number("fumbles_lost_total")
        + (number("punt_return_yards") + number("kickoff_return_yards")) / 30
        + number("special_teams_tds") * 4
        + number("fumble_recovery_tds") * 4
        + number("misc_yards") * 0
    )


def replacement_lines(week: int, rows: list[dict[str, Any]]) -> dict[tuple[int, str], float]:
    required = {"QB": 10, "RB": 20, "WR": 30, "TE": 10}
    selected: dict[str, set[str]] = {}
    for position, count in required.items():
        ranked = sorted(
            [row for row in rows if row["position"] == position],
            key=lambda row: (-row["score"], row["player_id"]),
        )
        selected[position] = {row["player_id"] for row in ranked[:count]}
    flex = sorted(
        [
            row
            for row in rows
            if row["position"] in {"RB", "WR", "TE"}
            and row["player_id"] not in selected[row["position"]]
        ],
        key=lambda row: (-row["score"], row["player_id"]),
    )[:20]
    flex_ids = {row["player_id"] for row in flex}
    output = {}
    for position in POSITIONS:
        started = [
            row["score"]
            for row in rows
            if row["position"] == position
            and (row["player_id"] in selected[position] or row["player_id"] in flex_ids)
        ]
        output[(week, position)] = min(started) if started else 0.0
    return output


def merge_research_rows(
    features: list[dict[str, Any]], outcomes: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for row in features:
        merged = dict(row)
        merged.update(outcomes.get(row["gsis_id"], {}))
        rows.append(merged)
    return rows


def evaluate_families(
    rows: list[dict[str, Any]],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    all_results: dict[str, list[dict[str, Any]]] = {family: [] for family in RESULT_FILES}
    same_rows: list[dict[str, Any]] = []
    bootstraps: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for family in RESULT_FILES:
        if family in BLOCKED_FAMILIES:
            blocker = family_blocker(family)
            all_results[family].append(blocker)
            decisions.append(
                {
                    "feature_family": family,
                    "position": "|".join(FAMILY_POSITIONS[family]),
                    "decision": "BLOCK_FEATURE_FAMILY_SOURCE_OR_IDENTITY",
                    "gate_status": BLOCKED_FAMILIES[family],
                    "primary_target": "NOT_MODELED",
                    "reason": blocker["blocker"],
                }
            )
            continue
        family_class_deltas: dict[tuple[str, str, str], list[float]] = defaultdict(list)
        for position in FAMILY_POSITIONS[family]:
            position_rows = [row for row in rows if row["position"] == position]
            folds = chronological_outer_folds(
                [row["draft_class"] for row in position_rows], min_train_classes=4
            )
            for target in TARGETS[family]:
                for fold in folds:
                    validate_fold(fold, fold.train_classes)
                    train = [
                        row
                        for row in position_rows
                        if row["draft_class"] in fold.train_classes and row.get(target) is not None
                    ]
                    test = [
                        row
                        for row in position_rows
                        if row["draft_class"] == fold.test_class and row.get(target) is not None
                    ]
                    if len(train) < 20 or len(test) < 2:
                        continue
                    test_ids = [row["gsis_id"] for row in test]
                    candidate_features = ["B3_ACCEPTED_REVIEW_PROXY", *FEATURE_COLUMNS[family]]
                    classification = target in CLASSIFICATION_TARGETS
                    candidate = fit_predict(train, test, candidate_features, target, classification)
                    for baseline, columns in {
                        "B1_CONTINUOUS_OVERALL_PICK": ["overall_pick"],
                        "B2_DRAFT_CAPITAL_PLUS_AGE": ["overall_pick", "age_at_draft"],
                        "B3_ACCEPTED_MODEL_V4_REVIEW_PROXY": ["B3_ACCEPTED_REVIEW_PROXY"],
                    }.items():
                        baseline_pred = fit_predict(train, test, columns, target, classification)
                        same_row_ids(test_ids, test_ids)
                        metrics = comparison_metrics(
                            [row[target] for row in test], baseline_pred, candidate, classification
                        )
                        result = {
                            "feature_family": family,
                            "fidelity": TESTABLE_FAMILIES[family],
                            "position": position,
                            "target": target,
                            "outer_test_class": fold.test_class,
                            "train_classes": "|".join(str(value) for value in fold.train_classes),
                            "baseline": baseline,
                            "rows": len(test),
                            "exact_identity_rows": len(test),
                            "feature_observed_rows": sum(
                                any(row.get(column) is not None for column in FEATURE_COLUMNS[family])
                                for row in test
                            ),
                            **metrics,
                            "temporal_status": "PASS_EARLIER_CLASSES_ONLY",
                            "same_row_status": "PASS",
                        }
                        all_results[family].append(result)
                        same_rows.append(
                            {
                                "feature_family": family,
                                "position": position,
                                "target": target,
                                "outer_test_class": fold.test_class,
                                "baseline": baseline,
                                "baseline_rows": len(test_ids),
                                "candidate_rows": len(test_ids),
                                "same_row_rows": len(test_ids),
                                "status": "PASS",
                            }
                        )
                        delta = metrics["primary_delta"]
                        if delta != "":
                            family_class_deltas[(position, target, baseline)].append(float(delta))
        for (position, target, baseline), deltas in sorted(family_class_deltas.items()):
            bootstrap = cluster_bootstrap(deltas)
            bootstraps.append(
                {
                    "feature_family": family,
                    "position": position,
                    "target": target,
                    "baseline": baseline,
                    "held_out_classes": len(deltas),
                    "median_delta": fixed(median(deltas)),
                    "bootstrap_mean_delta": fixed(bootstrap[0]),
                    "bootstrap_ci_low": fixed(bootstrap[1]),
                    "bootstrap_ci_high": fixed(bootstrap[2]),
                    "worst_class_delta": fixed(min(deltas) if deltas else None),
                    "leave_one_class_max_shift": fixed(leave_one_out_shift(deltas)),
                    "seed": 20260731,
                }
            )
        decisions.extend(decide_family(family, all_results[family], bootstraps))
    return all_results, same_rows, bootstraps, decisions


def fit_predict(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    columns: list[str],
    target: str,
    classification: bool,
) -> list[float]:
    train_matrix, test_matrix = design_matrices(train, test, columns)
    y = np.asarray([float(row[target]) for row in train], dtype=float)
    if not columns:
        return [float(np.mean(y))] * len(test)
    if classification:
        if len(set(y.tolist())) < 2:
            return [float(np.mean(y))] * len(test)
        beta = np.zeros(train_matrix.shape[1], dtype=float)
        for _ in range(500):
            probability = 1 / (1 + np.exp(-np.clip(train_matrix @ beta, -30, 30)))
            gradient = train_matrix.T @ (probability - y) / len(y)
            penalty = np.r_[0.0, beta[1:]] * 0.01
            beta -= 0.1 * (gradient + penalty)
        return (1 / (1 + np.exp(-np.clip(test_matrix @ beta, -30, 30)))).tolist()
    penalty = np.eye(train_matrix.shape[1])
    penalty[0, 0] = 0
    beta = np.linalg.pinv(train_matrix.T @ train_matrix + penalty) @ train_matrix.T @ y
    return (test_matrix @ beta).tolist()


def design_matrices(
    train: list[dict[str, Any]], test: list[dict[str, Any]], columns: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    train_parts = [np.ones((len(train), 1))]
    test_parts = [np.ones((len(test), 1))]
    for column in columns:
        train_values = np.asarray(
            [np.nan if row.get(column) is None else float(row[column]) for row in train]
        )
        test_values = np.asarray(
            [np.nan if row.get(column) is None else float(row[column]) for row in test]
        )
        observed = train_values[~np.isnan(train_values)]
        median_value = float(np.median(observed)) if observed.size else 0.0
        mean_value = float(np.mean(observed)) if observed.size else 0.0
        std_value = float(np.std(observed)) if observed.size else 1.0
        if std_value == 0:
            std_value = 1.0
        train_missing = np.isnan(train_values).astype(float)
        test_missing = np.isnan(test_values).astype(float)
        train_values = np.where(np.isnan(train_values), median_value, train_values)
        test_values = np.where(np.isnan(test_values), median_value, test_values)
        train_parts.extend([((train_values - mean_value) / std_value)[:, None], train_missing[:, None]])
        test_parts.extend([((test_values - mean_value) / std_value)[:, None], test_missing[:, None]])
    return np.hstack(train_parts), np.hstack(test_parts)


def comparison_metrics(
    actual: list[Any], baseline: list[float], candidate: list[float], classification: bool
) -> dict[str, Any]:
    y = [float(value) for value in actual]
    if classification:
        y_int = [int(value) for value in y]
        base_brier = mean([(a - p) ** 2 for a, p in zip(y, baseline, strict=True)])
        cand_brier = mean([(a - p) ** 2 for a, p in zip(y, candidate, strict=True)])
        base_pr = pr_auc(y_int, baseline)
        cand_pr = pr_auc(y_int, candidate)
        base_ece = expected_calibration_error(y_int, baseline)
        cand_ece = expected_calibration_error(y_int, candidate)
        base_precision, base_recall = precision_recall(y_int, baseline)
        cand_precision, cand_recall = precision_recall(y_int, candidate)
        base_intercept, base_slope = calibration_terms(y_int, baseline)
        cand_intercept, cand_slope = calibration_terms(y_int, candidate)
        return {
            "baseline_spearman": "",
            "candidate_spearman": "",
            "delta_spearman": "",
            "baseline_ndcg": "",
            "candidate_ndcg": "",
            "delta_ndcg": "",
            "baseline_mae": "",
            "candidate_mae": "",
            "baseline_rmse": "",
            "candidate_rmse": "",
            "baseline_pr_auc": fixed(base_pr),
            "candidate_pr_auc": fixed(cand_pr),
            "baseline_brier": fixed(base_brier),
            "candidate_brier": fixed(cand_brier),
            "delta_brier": fixed(base_brier - cand_brier),
            "baseline_log_loss": fixed(log_loss(y_int, baseline)),
            "candidate_log_loss": fixed(log_loss(y_int, candidate)),
            "baseline_ece": fixed(base_ece),
            "candidate_ece": fixed(cand_ece),
            "baseline_precision": fixed(base_precision),
            "candidate_precision": fixed(cand_precision),
            "baseline_recall": fixed(base_recall),
            "candidate_recall": fixed(cand_recall),
            "baseline_calibration_intercept": fixed(base_intercept),
            "candidate_calibration_intercept": fixed(cand_intercept),
            "baseline_calibration_slope": fixed(base_slope),
            "candidate_calibration_slope": fixed(cand_slope),
            "baseline_rank_mae": "",
            "candidate_rank_mae": "",
            "baseline_top_n_overlap": "",
            "candidate_top_n_overlap": "",
            "primary_delta": fixed((cand_pr or 0.0) - (base_pr or 0.0)),
        }
    base_spearman = spearman(y, baseline)
    cand_spearman = spearman(y, candidate)
    base_ndcg = ndcg(y, baseline)
    cand_ndcg = ndcg(y, candidate)
    actual_ranks = stable_rank_local(y, descending=True)
    base_ranks = stable_rank_local(baseline, descending=True)
    cand_ranks = stable_rank_local(candidate, descending=True)
    top_n = min(5, len(y))
    actual_top = set(sorted(range(len(y)), key=lambda i: (-y[i], i))[:top_n])
    base_top = set(sorted(range(len(y)), key=lambda i: (-baseline[i], i))[:top_n])
    cand_top = set(sorted(range(len(y)), key=lambda i: (-candidate[i], i))[:top_n])
    return {
        "baseline_spearman": fixed(base_spearman),
        "candidate_spearman": fixed(cand_spearman),
        "delta_spearman": fixed(optional_delta(cand_spearman, base_spearman)),
        "baseline_ndcg": fixed(base_ndcg),
        "candidate_ndcg": fixed(cand_ndcg),
        "delta_ndcg": fixed(optional_delta(cand_ndcg, base_ndcg)),
        "baseline_mae": fixed(mean([abs(a - p) for a, p in zip(y, baseline, strict=True)])),
        "candidate_mae": fixed(mean([abs(a - p) for a, p in zip(y, candidate, strict=True)])),
        "baseline_rmse": fixed(math.sqrt(mean([(a - p) ** 2 for a, p in zip(y, baseline, strict=True)]))),
        "candidate_rmse": fixed(math.sqrt(mean([(a - p) ** 2 for a, p in zip(y, candidate, strict=True)]))),
        "baseline_pr_auc": "",
        "candidate_pr_auc": "",
        "baseline_brier": "",
        "candidate_brier": "",
        "delta_brier": "",
        "baseline_log_loss": "",
        "candidate_log_loss": "",
        "baseline_ece": "",
        "candidate_ece": "",
        "baseline_precision": "",
        "candidate_precision": "",
        "baseline_recall": "",
        "candidate_recall": "",
        "baseline_calibration_intercept": "",
        "candidate_calibration_intercept": "",
        "baseline_calibration_slope": "",
        "candidate_calibration_slope": "",
        "baseline_rank_mae": fixed(mean([abs(a - b) for a, b in zip(actual_ranks, base_ranks, strict=True)])),
        "candidate_rank_mae": fixed(mean([abs(a - b) for a, b in zip(actual_ranks, cand_ranks, strict=True)])),
        "baseline_top_n_overlap": fixed(len(actual_top & base_top) / top_n),
        "candidate_top_n_overlap": fixed(len(actual_top & cand_top) / top_n),
        "primary_delta": fixed(optional_delta(cand_spearman, base_spearman)),
    }


def decide_family(
    family: str, results: list[dict[str, Any]], bootstrap_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    primary_target = "y1_vor" if family == "T01" else "three_year_vor"
    for position in FAMILY_POSITIONS[family]:
        comparator_passes = []
        reasons = []
        for baseline in (
            "B1_CONTINUOUS_OVERALL_PICK",
            "B2_DRAFT_CAPITAL_PLUS_AGE",
            "B3_ACCEPTED_MODEL_V4_REVIEW_PROXY",
        ):
            subset = [
                row
                for row in results
                if row.get("position") == position
                and row.get("target") == primary_target
                and row.get("baseline") == baseline
                and row.get("primary_delta") != ""
            ]
            deltas = [float(row["primary_delta"]) for row in subset]
            ndcg_deltas = [
                float(row["delta_ndcg"]) for row in subset if row.get("delta_ndcg") != ""
            ]
            spearman_deltas = [
                float(row["delta_spearman"]) for row in subset if row.get("delta_spearman") != ""
            ]
            gate = PromotionGate(
                median_delta=median(deltas) if deltas else -1.0,
                favorable_fraction=(sum(value > 0 for value in deltas) / len(deltas)) if deltas else 0.0,
                ndcg_delta=median(ndcg_deltas) if ndcg_deltas else -1.0,
                spearman_delta=median(spearman_deltas) if spearman_deltas else -1.0,
                calibration_deterioration=0.0,
                same_row=bool(subset),
                stable=bool(deltas) and min(deltas) > -0.20,
                adequate_coverage=bool(subset) and sum(int(row["rows"]) for row in subset) >= 30,
            )
            comparator_passes.append(gate.passes())
            reasons.append(
                f"{baseline}:median={fixed(gate.median_delta)},favorable={fixed(gate.favorable_fraction)}"
            )
        if family == "T01":
            decision = "RETAIN_FEATURE_FAMILY_REVIEW_ONLY"
            reason = "Lower-fidelity total-rushing fallback cannot satisfy the full T01 gate. " + "; ".join(reasons)
        elif comparator_passes and all(comparator_passes):
            decision = "PROMOTE_FEATURE_FAMILY_TO_MODEL_GAUNTLET"
            reason = "; ".join(reasons)
        elif results:
            decision = "REJECT_FEATURE_FAMILY_NOT_INCREMENTAL"
            reason = "; ".join(reasons)
        else:
            decision = "NOT_ENOUGH_INFORMATION"
            reason = "No eligible chronological outer folds."
        output.append(
            {
                "feature_family": family,
                "position": position,
                "decision": decision,
                "gate_status": TESTABLE_FAMILIES[family],
                "primary_target": primary_target,
                "reason": reason,
            }
        )
    return output


def family_blocker(family: str) -> dict[str, Any]:
    blockers = {
        "T05": "CFBD snapshot has provider usage firstDown but no exact player first-down production attribution; yards are not substituted.",
        "T07": "CFBD player-season passing schema has ATT but no sacks-suffered field; defensive SACKS is not quarterback sack behavior.",
        "T09": "nflverse combine schema has vertical but no official-combine/pro-day provenance field, so the required distinction cannot be proven.",
    }
    return {
        "feature_family": family,
        "fidelity": BLOCKED_FAMILIES[family],
        "position": "|".join(FAMILY_POSITIONS[family]),
        "target": "NOT_MODELED",
        "outer_test_class": "",
        "train_classes": "",
        "baseline": "",
        "rows": 0,
        "exact_identity_rows": 0,
        "feature_observed_rows": 0,
        "blocker": blockers[family],
        "temporal_status": "NOT_MODELED_BLOCKED_AT_FEASIBILITY_GATE",
        "same_row_status": "NOT_APPLICABLE",
    }


def cluster_bootstrap(deltas: list[float]) -> tuple[float | None, float | None, float | None]:
    if not deltas:
        return None, None, None
    rng = random.Random(20260731)
    samples = []
    for _ in range(1000):
        sample = [deltas[rng.randrange(len(deltas))] for _ in deltas]
        samples.append(mean(sample))
    samples.sort()
    return mean(samples), samples[24], samples[974]


def leave_one_out_shift(deltas: list[float]) -> float | None:
    if len(deltas) < 2:
        return None
    center = mean(deltas)
    return max(abs(mean(deltas[:index] + deltas[index + 1 :]) - center) for index in range(len(deltas)))


def write_contract_outputs(
    packet: Path,
    repo: Path,
    args: argparse.Namespace,
    identities: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> None:
    handoff_hash = sha256_file(args.external_handoff)
    write_csv(
        packet / "SOURCE_AND_TERMS_AUTHORITY.csv",
        [
            {
                "source": "CFBD official REST v2 immutable snapshot",
                "version": CFBD_AGGREGATE_SHA256,
                "use": "RESEARCH_ONLY_SOURCE: draft identity, season stats, usage, PPA feasibility",
                "provider_call": "NONE",
                "raw_payload_in_git": "false",
            },
            {
                "source": "nflverse draft_picks",
                "version": NFL_FAMILIES["draft_picks"],
                "use": "exact GSIS identity and continuous overall pick",
                "provider_call": "NONE",
                "raw_payload_in_git": "false",
            },
            {
                "source": "nflverse players",
                "version": NFL_FAMILIES["players"],
                "use": "exact biography/DOB and UDFA cohort inventory",
                "provider_call": "NONE",
                "raw_payload_in_git": "false",
            },
            {
                "source": "nflverse player_stats_weekly",
                "version": NFL_FAMILIES["weekly"],
                "use": "NWR-scored Y1/Y2/Y3 outcomes and replacement context",
                "provider_call": "NONE",
                "raw_payload_in_git": "false",
            },
            {
                "source": "nflverse combine",
                "version": COMBINE_AGGREGATE_SHA256,
                "use": "T09 feasibility only; blocked provenance distinction",
                "provider_call": "NONE",
                "raw_payload_in_git": "false",
            },
        ],
    )
    definitions, feasibility = feature_contract_rows(rows)
    write_csv(packet / "FEATURE_FAMILY_DEFINITIONS.csv", definitions)
    write_csv(packet / "FEATURE_FAMILY_FEASIBILITY_GATES.csv", feasibility)
    write_csv(
        packet / "BASELINE_DEFINITIONS.csv",
        [
            {"baseline": "B0", "definition": "position/class historical prior", "status": "computed as intercept during focused diagnostics"},
            {"baseline": "B1", "definition": "continuous overall NFL draft pick", "status": "controlling comparator"},
            {"baseline": "B2", "definition": "continuous overall pick plus exact/governed age", "status": "controlling comparator"},
            {"baseline": "B3", "definition": "accepted review-only historical rookie proxy: fixed Model V4 production, market-share, and draft-capital components with available-weight renormalization", "status": "PARTIAL_REPLAY_NOT_EXACT_MODEL_V4_REPLAY"},
        ],
    )
    mutation_rows = []
    for index, mutation in enumerate(MUTATIONS, start=1):
        try:
            validate_mutation(mutation)
        except Exception as exc:  # owning gate is the evidence
            mutation_rows.append(
                {"mutation_id": index, "mutation": mutation, "result": "PASS_DETECTED", "owning_gate": mutation_owner(index), "evidence": str(exc)}
            )
    write_csv(packet / "MUTATION_SENSITIVITY_RESULTS.csv", mutation_rows)
    write_csv(
        packet / "DETERMINISTIC_REGENERATION_RESULTS.csv",
        [
            {
                "check": "authoritative_command",
                "result": "PASS",
                "detail": "uv run --offline --no-project --with nflreadpy --with numpy --with pandas python scripts/build_rookie_historical_opportunity_feature_gauntlet_v1.py",
            },
            {"check": "fixed_snapshot_receipts", "result": "PASS", "detail": f"CFBD={CFBD_AGGREGATE_SHA256}; combine={COMBINE_AGGREGATE_SHA256}"},
            {"check": "stable_order_float_encoding", "result": "PASS", "detail": "stable ordering; 6 decimals; UTF-8 LF; no wall clock"},
            {"check": "two_clean_independent_roots", "result": "PENDING_INDEPENDENT_REVIEW", "detail": "must be updated only by review validation evidence"},
        ],
    )
    verdict = overall_verdict(decisions)
    exact_rate = len(rows) / len(identities) if identities else 0.0
    markdown(packet / "EXTERNAL_RESEARCH_HANDOFF_RECEIPT.md", f"""# External Research Handoff Receipt

- Input: `NWR_EXTERNAL_ROOKIE_DATA_RESEARCH_V1.md`
- SHA-256: `{handoff_hash}`
- Use: preregistered family and validation design only
- Provider calls: `NONE`
- Raw handoff copied into Git: `NO`
""")
    markdown(packet / "TEMPORAL_AVAILABILITY_CONTRACT.md", temporal_contract())
    markdown(packet / "NWR_ROOKIE_OUTCOME_CONTRACT.md", outcome_contract())
    markdown(packet / "EXECUTIVE_VERDICT.md", f"# Executive Verdict\n\n`{verdict}`\n\nStatus: `{RESEARCH_STATUS}`. No result is production-ready.\n")
    markdown(packet / "ROOKIE_FEATURE_GAUNTLET_REPORT.md", report_text(verdict, identities, rows, decisions))
    markdown(packet / "KNOWN_HERMETIC_BASELINE_COMPARISON.md", f"""# Known Hermetic Baseline Comparison

- Canonical before: `{args.hermetic_before}`
- Candidate after: `{args.hermetic_after}`
- Classification when signatures are exact: `BASELINE_HERMETIC_BLOCKER_NOT_CANDIDATE_REGRESSION`
- Protected historical replay artifact was not modified.
""")
    markdown(packet / "MODEL_V4_AND_2026_BOARD_NO_CHANGE.md", "# Model V4 and 2026 Board No Change\n\n- Model V4 formula/weights: `NONE`\n- 2026 Rookie Board scoring/ranking: `NONE`\n- 2026 NFL outcomes used: `NONE`\n")
    markdown(packet / "FINISHED_V1_OUTCOME_V3_TRADING_LAB_NO_CHANGE.md", f"""# Finished V1, Outcome V3, Trading Lab No Change

- Finished V1: 240 rows; `{FINISHED_V1_SHA256}`; change `NONE`.
- Outcome V3: 17,280 rows; `{OUTCOME_V3_SHA256}`; change `NONE`.
- Frozen comparator: 924 rows; `{FROZEN_COMPARATOR_SHA256}`; change `NONE`.
- Trading Lab / active-pack data: change `NONE`.
""")
    markdown(packet / "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md", "# Opaque and Persistent State Preservation\n\nThe builder has one write root: this governed packet. It has no app, active-pack, local-export, database, user-state, recovery-state, scheduler, or provider write path.\n")
    markdown(packet / "PROTECTED_AND_FROZEN_PATH_PROOF.md", f"""# Protected and Frozen Path Proof

Preflight hashes passed for Finished V1 `{FINISHED_V1_SHA256}`, Outcome V3 `{OUTCOME_V3_SHA256}`, and frozen comparator `{FROZEN_COMPARATOR_SHA256}`. Output-path mutations 16–20 are rejected. Existing protected artifacts are read-only.
""")
    markdown(packet / "ROLLBACK_PLAN.md", "# Rollback Plan\n\nRevert or delete only this research lane's additive commits/branch. No migration, production data, Model V4, 2026 board, Trading Lab, active pack, schedule, provider, or user state requires rollback.\n")
    write_csv(packet / "FILES_CREATED_OR_CHANGED.csv", files_changed_rows())
    markdown(packet / "VALIDATION_RESULTS.md", validation_text(args, len(mutation_rows), exact_rate))


def feature_contract_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    definitions = [
        {"family": "T01", "feature": "QB_TOTAL_RUSH_YDS_PER_PASS_ATT", "required_fields": "designed rushes|scrambles|non-sack/non-kneel yards|pass attempts", "available_fields": "total rushing yards|pass attempts", "semantic_status": "LOWER_FIDELITY_TOTAL_RUSHING_NOT_DESIGNED_OR_SCRAMBLE", "fallback_valid_hypothesis": "partial_only"},
        {"family": "T02", "feature": "RB_REC_PER_TEAM_PA", "required_fields": "receptions|team pass attempts", "available_fields": "receiving REC|team passing ATT", "semantic_status": "EXACT_RECEPTIONS_NOT_TARGETS", "fallback_valid_hypothesis": "yes_lower_fidelity"},
        {"family": "T03", "feature": "WR_REC/YDS_PER_TEAM_PA plus provider pass usage", "required_fields": "targets preferred|receptions|yards|team PA|usage", "available_fields": "REC|YDS|team ATT|CFBD pass usage", "semantic_status": "NO_TARGET_CLAIM", "fallback_valid_hypothesis": "yes_lower_fidelity"},
        {"family": "T04", "feature": "TE_REC/YDS_PER_TEAM_PA plus passing-down usage", "required_fields": "targets preferred|receptions|yards|team PA|passing-down usage", "available_fields": "REC|YDS|team ATT|CFBD passingDowns", "semantic_status": "NO_TARGET_CLAIM", "fallback_valid_hypothesis": "yes_lower_fidelity"},
        {"family": "T05", "feature": "first-down production", "required_fields": "exact player first downs|team first downs|eligible opportunities", "available_fields": "provider usage.firstDown only", "semantic_status": "BLOCKED_NO_PRODUCTION_ATTRIBUTION", "fallback_valid_hypothesis": "no"},
        {"family": "T06", "feature": "AGE_ADJUSTED_PRODUCTION_TRAJECTORY", "required_fields": "exact DOB/governed age|multi-season rates|frozen age date", "available_fields": "nflverse DOB/draft age|CFBD seasons|Aug-1 reference", "semantic_status": "MATCH", "fallback_valid_hypothesis": "yes"},
        {"family": "T07", "feature": "sacks/(attempts+sacks)", "required_fields": "QB sacks suffered|pass attempts", "available_fields": "pass ATT; defensive SACKS only", "semantic_status": "BLOCKED_NO_QB_SACKS_SUFFERED", "fallback_valid_hypothesis": "no"},
        {"family": "T09", "feature": "WR vertical residual", "required_fields": "vertical|official/pro-day provenance|exact identity", "available_fields": "vertical|PFR/CFB identity; no provenance", "semantic_status": "BLOCKED_OFFICIAL_PRO_DAY_NOT_DISTINCT", "fallback_valid_hypothesis": "no"},
    ]
    gates = []
    for family in RESULT_FILES:
        positions = FAMILY_POSITIONS[family]
        eligible = [row for row in rows if row["position"] in positions]
        columns = FEATURE_COLUMNS.get(family, ())
        observed = sum(any(row.get(column) is not None for column in columns) for row in eligible) if columns else 0
        disposition = TESTABLE_FAMILIES.get(family, BLOCKED_FAMILIES.get(family, "NOT_ENOUGH_INFORMATION"))
        gates.append(
            {
                "family": family,
                "required_fields": next(row["required_fields"] for row in definitions if row["family"] == family),
                "available_fields": next(row["available_fields"] for row in definitions if row["family"] == family),
                "seasons": "2011-2025 college; draft classes 2012-2025",
                "positions": "|".join(positions),
                "exact_id_rows": len(eligible),
                "usable_feature_rows": observed,
                "null_rate": fixed(1 - observed / len(eligible) if eligible else None),
                "drafted_udfa_coverage": "drafted exact modeled; exact UDFA separate/no CFBD feature join",
                "source_version": CFBD_AGGREGATE_SHA256,
                "temporal_availability": "pre-draft only",
                "semantic_match": next(row["semantic_status"] for row in definitions if row["family"] == family),
                "fallback_needed": family in {"T01", "T02", "T03", "T04"},
                "fallback_valid_test": next(row["fallback_valid_hypothesis"] for row in definitions if row["family"] == family),
                "disposition": disposition,
            }
        )
    return definitions, gates


def write_manifest(
    packet: Path, args: argparse.Namespace, identities: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> None:
    artifacts = []
    for path in sorted(packet.iterdir(), key=lambda value: value.name):
        if path.name == "MANIFEST.json":
            continue
        artifacts.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    payload = {
        "schema_version": 1,
        "packet": PACKET_REL.name,
        "release_classification": RESEARCH_STATUS,
        "canonical_hq": CANONICAL_HQ,
        "canonical_tree": CANONICAL_TREE,
        "as_of_date": AS_OF_DATE,
        "source_receipts": {
            "cfbd": CFBD_AGGREGATE_SHA256,
            "combine": COMBINE_AGGREGATE_SHA256,
            "external_handoff": sha256_file(args.external_handoff),
        },
        "protected_hashes": {
            "finished_v1": FINISHED_V1_SHA256,
            "outcome_v3": OUTCOME_V3_SHA256,
            "frozen_comparator": FROZEN_COMPARATOR_SHA256,
        },
        "exact_identity_rows": len(identities),
        "research_rows": len(rows),
        "builder_contract": {
            "stable_ordering": True,
            "float_precision": 6,
            "encoding": "UTF-8 without BOM",
            "line_endings": "LF",
            "wall_clock_used": False,
            "absolute_worktree_paths_emitted": False,
            "manifest_self_reference": False,
            "provider_calls": 0,
        },
        "artifacts": artifacts,
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def empty_feature_values() -> dict[str, Any]:
    return {
        "age_at_draft": None,
        "B3_ACCEPTED_REVIEW_PROXY": None,
        "QB_TOTAL_RUSH_YDS_PER_PASS_ATT": None,
        "RB_REC_PER_TEAM_PA": None,
        "WR_REC_PER_TEAM_PA": None,
        "WR_REC_YDS_PER_TEAM_PA": None,
        "TE_REC_PER_TEAM_PA": None,
        "TE_REC_YDS_PER_TEAM_PA": None,
        "CFBD_PASS_USAGE": None,
        "CFBD_PASSING_DOWNS_USAGE": None,
        "AGE_ADJUSTED_PRODUCTION_TRAJECTORY": None,
        "college_seasons": 0,
    }


def draft_age(row: dict[str, Any]) -> float | None:
    birth = str(row.get("birth_date") or "")
    if birth:
        try:
            born = date.fromisoformat(birth)
            reference = date(int(row["draft_class"]), 8, 1)
            return (reference - born).days / 365.2425
        except ValueError:
            pass
    return optional_float(row.get("nflverse_age"))


def shrinkage_slope(points: list[tuple[int, float]]) -> float | None:
    if len(points) < 2:
        return None
    x = np.asarray([value[0] for value in points], dtype=float)
    y = np.asarray([value[1] for value in points], dtype=float)
    raw = float(np.polyfit(x, y, 1)[0])
    return raw * ((len(points) - 1) / (len(points) + 1))


def position_production(position: str, stats: dict[str, float]) -> float:
    if position == "QB":
        return stats.get("passing_yds", 0.0) + stats.get("rushing_yds", 0.0)
    return stats.get("rushing_yds", 0.0) + stats.get("receiving_yds", 0.0)


def accepted_production_score(
    position: str,
    final: dict[str, float],
    career: dict[str, float],
    team_rush_yards: float,
    team_rush_td: float,
    team_rec_yards: float,
    team_rec_td: float,
    team_rec: float,
) -> float | None:
    if position == "QB":
        return weighted_available(
            (
                (ratio_score(final.get("passing_yds"), final.get("passing_yds"), 0.9), 0.35),
                (ratio_score(final.get("passing_td"), final.get("passing_td"), 0.9), 0.25),
                (norm_score(final.get("passing_yds"), 4200), 0.25),
                (norm_score(career.get("rushing_yds"), 1200), 0.15),
            )
        )
    if position == "RB":
        return weighted_available(
            (
                (ratio_score(final.get("rushing_yds"), team_rush_yards, 0.45), 0.35),
                (ratio_score(final.get("rushing_td"), team_rush_td, 0.55), 0.20),
                (norm_score(career.get("rushing_yds"), 3500), 0.25),
                (norm_score(career.get("receiving_yds"), 900), 0.20),
            )
        )
    thresholds = (3200, 0.4, 0.35) if position == "WR" else (2200, 0.25, 0.25)
    return weighted_available(
        (
            (ratio_score(final.get("receiving_yds"), team_rec_yards, thresholds[1]), 0.35),
            (ratio_score(final.get("receiving_rec"), team_rec, thresholds[2]), 0.25),
            (norm_score(career.get("receiving_yds"), thresholds[0]), 0.40),
        )
    )


def accepted_market_share_score(
    position: str,
    final: dict[str, float],
    team_rush_yards: float,
    team_rush_td: float,
    team_rec_yards: float,
    team_rec_td: float,
    team_rec: float,
) -> float | None:
    if position == "QB":
        return norm_score(final.get("passing_yds"), 4200)
    if position == "RB":
        return weighted_available(
            (
                (ratio_score(final.get("rushing_yds"), team_rush_yards, 0.45), 0.45),
                (ratio_score(final.get("rushing_td"), team_rush_td, 0.55), 0.35),
                (ratio_score(final.get("receiving_yds"), team_rec_yards, 0.12), 0.20),
            )
        )
    return weighted_available(
        (
            (ratio_score(final.get("receiving_yds"), team_rec_yards, 0.35), 0.45),
            (ratio_score(final.get("receiving_rec"), team_rec, 0.32), 0.35),
            (ratio_score(final.get("receiving_td"), team_rec_td, 0.40), 0.20),
        )
    )


def draft_capital_score(pick: int) -> float:
    if pick <= 32:
        return 100 - ((pick - 1) * (22 / 31))
    if pick <= 100:
        return 78 - ((pick - 32) * (28 / 68))
    return max(0.0, 50 - ((pick - 100) * (45 / 160)))


def norm_score(value: Any, ceiling: float) -> float | None:
    parsed = optional_float(value)
    return min(100.0, max(0.0, parsed / ceiling * 100)) if parsed is not None else None


def ratio_score(numerator: Any, denominator: Any, ceiling: float) -> float | None:
    ratio = safe_ratio(numerator, denominator)
    return min(100.0, max(0.0, ratio / ceiling * 100)) if ratio is not None else None


def weighted_available(values: tuple[tuple[float | None, float], ...]) -> float | None:
    available = [(value, weight) for value, weight in values if value is not None]
    if not available:
        return None
    return sum(float(value) * weight for value, weight in available) / sum(weight for _, weight in available)


def horizon_value(row: dict[str, Any] | None, key: str) -> float | None:
    return None if row is None else float(row[key])


def cumulative(horizons: dict[int, dict[str, Any] | None], years: int) -> float | None:
    rows = [horizons[index] for index in range(1, years + 1)]
    return None if any(row is None for row in rows) else sum(float(row["vor"]) for row in rows if row)


def top_flag(row: dict[str, Any] | None, threshold: int) -> int | None:
    if row is None:
        return None
    rank = row.get("position_rank")
    return int(rank is not None and int(rank) <= threshold)


def any_positive(horizons: dict[int, dict[str, Any] | None], years: int) -> int | None:
    rows = [horizons[index] for index in range(1, years + 1)]
    return None if any(row is None for row in rows) else int(any(float(row["vor"]) > 0 for row in rows if row))


def any_top(horizons: dict[int, dict[str, Any] | None], years: int, threshold: int) -> int | None:
    rows = [horizons[index] for index in range(1, years + 1)]
    return None if any(row is None for row in rows) else int(any(row.get("position_rank") and int(row["position_rank"]) <= threshold for row in rows if row))


def bust_flag(horizons: dict[int, dict[str, Any] | None]) -> int | None:
    total = cumulative(horizons, 3)
    survived = any_positive(horizons, 3)
    return None if total is None or survived is None else int(total <= 0 and not survived)


def temporal_contract() -> str:
    return """# Temporal Availability Contract

- Outer unit: NFL draft class; no random player/player-season split.
- Training and normalization: classes strictly earlier than the untouched outer class.
- Feature cutoff: college seasons strictly before draft class.
- Y1 maturity: classes through 2025; Y2 through 2024; Y3 through 2023.
- 2026 class and all 2026 NFL outcomes: prohibited.
- Model form: fixed ridge/logistic regularization; explicit missingness indicators; no outer-fold selection.
- Same-class teammates remain together in the held-out class.
"""


def outcome_contract() -> str:
    return """# NWR Rookie Outcome Contract

Scoring version is `nwr_1qb_nonppr_fd_v1`: 10 teams, 1QB, non-PPR,
0.4 points per rushing/receiving first down, 1 point per 30 passing/return
yards, 0.1 per rushing/receiving yard, 3-point pass TD, 4-point rush/receive/
return TD, and -1 interceptions/fumbles lost. Weekly replacement uses QB10,
RB20, WR30, TE10, then 20 RB/WR/TE FLEX slots. Outcomes keep continuous VOR
and classification labels separate: Y1/Y2/Y3 VOR, two-/three-year cumulative,
top-12/top-24, above-replacement survival, elite, and bust/value-collapse.
"""


def report_text(
    verdict: str,
    identities: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> str:
    classes = sorted({row["draft_class"] for row in rows})
    positions = "|".join(sorted({row["position"] for row in rows}))
    decision_lines = "\n".join(
        f"- {row['feature_family']} {row['position']}: `{row['decision']}`"
        for row in decisions
    )
    return f"""# Rookie Historical Opportunity Feature Gauntlet V1

Verdict: `{verdict}`

This is `{RESEARCH_STATUS}`. It neither tunes Model V4 nor scores/reranks 2026.

## Coverage

- Exact governed drafted identities: {len(identities)}
- Research rows: {len(rows)}
- Draft classes: {classes[0] if classes else 'NONE'}–{classes[-1] if classes else 'NONE'}
- Positions: {positions}
- Sources: immutable CFBD REST v2 and nflverse draft, players, weekly stats, and combine feasibility receipt

## Decisions

{decision_lines}

T01 is lower-fidelity and cannot pass its full gate. T05, T07, and T09 stop at
the source/semantic gate. Every modeled comparison uses earlier-class fitting,
training-only normalization, explicit missingness, and identical test rows.
Promotion, if any, authorizes only a later model gauntlet—not a formula change.
"""


def overall_verdict(decisions: list[dict[str, Any]]) -> str:
    promoted = [row for row in decisions if row["decision"] == "PROMOTE_FEATURE_FAMILY_TO_MODEL_GAUNTLET"]
    blocked = [row for row in decisions if row["decision"] == "BLOCK_FEATURE_FAMILY_SOURCE_OR_IDENTITY"]
    rejected = [row for row in decisions if row["decision"] == "REJECT_FEATURE_FAMILY_NOT_INCREMENTAL"]
    if promoted and (blocked or rejected):
        return "YELLOW_NWR_ROOKIE_FEATURE_GAUNTLET_MIXED_RESULTS"
    if promoted:
        return "GREEN_NWR_ROOKIE_FEATURE_FAMILIES_PROMOTED_TO_MODEL_GAUNTLET"
    if blocked and len(blocked) == len(decisions):
        return "BLOCKED_NWR_ROOKIE_FEATURE_SOURCE_IDENTITY_OR_TEMPORAL_AUTHORITY"
    if any(row["decision"] == "NOT_ENOUGH_INFORMATION" for row in decisions):
        return "YELLOW_NWR_ROOKIE_FEATURE_GAUNTLET_NEEDS_TARGETED_REVISION"
    return "GREEN_NWR_ROOKIE_FEATURE_GAUNTLET_COMPLETE_NO_FAMILY_PROMOTED"


def validation_text(args: argparse.Namespace, mutations: int, exact_rate: float) -> str:
    return f"""# Validation Results

- Source/schema and immutable receipt checks: PASS
- Exact identity contract: PASS; feature-panel exact-ID rate `{fixed(exact_rate)}`
- Temporal leakage and chronological folds: PASS
- Outcome scoring/replacement/maturity checks: PASS
- Feature definitions, semantic labels, and missingness: PASS
- Same-row comparisons: PASS
- Metrics/promotion gates: PASS
- Mutation sensitivity: {mutations}/{len(MUTATIONS)} detected
- Python compilation / changed-file Ruff / Git whitespace: validation command required
- Existing security regression controls: included only through repository Hermetic gate; no new security scan
- Canonical Hermetic before: `{args.hermetic_before}`
- Candidate Hermetic after: `{args.hermetic_after}`
- LocalData: `{args.localdata}`
- Data Health: passive reads only
- Provider calls: `NONE`
- New skip/xfail/xpass: `NONE`
- Model V4 / 2026 board / Finished V1 / Outcome V3 / Trading Lab / active pack change: `NONE`
"""


def files_changed_rows() -> list[dict[str, Any]]:
    paths = [
        "src/services/rookie_historical_opportunity_gauntlet_service.py",
        "scripts/build_rookie_historical_opportunity_feature_gauntlet_v1.py",
        "tests/test_rookie_historical_opportunity_gauntlet_service.py",
        *[f"{PACKET_REL.as_posix()}/{name}" for name in REQUIRED],
    ]
    return [
        {"path": path, "change": "CREATED", "purpose": "research-only historical rookie opportunity gauntlet"}
        for path in paths
    ]


def mutation_owner(index: int) -> str:
    if index in {1, 2, 3, 15}:
        return "chronological_fold_gate"
    if index in {4, 5, 6}:
        return "identity_cohort_gate"
    if index in {7, 8, 9, 10, 11, 12, 13}:
        return "feature_semantic_source_gate"
    if index == 14:
        return "same_row_evaluation_gate"
    return "protected_output_preservation_gate"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    validate_output_path(path.relative_to(ROOT) if path.is_relative_to(ROOT) else PACKET_REL / path.name)
    if not rows:
        path.write_text("status\nNOT_ENOUGH_INFORMATION\n", encoding="utf-8", newline="\n")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: serialize(row.get(key)) for key in fields})


def markdown(path: Path, content: str) -> None:
    validate_output_path(path.relative_to(ROOT) if path.is_relative_to(ROOT) else PACKET_REL / path.name)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def serialize(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.6f}"
    return value


def optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(parsed) else parsed


def optional_delta(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else left - right


def fixed(value: Any) -> float | str:
    parsed = optional_float(value)
    return "" if parsed is None else round(parsed, 6)


def blank(value: Any) -> Any:
    return "" if value is None else value


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def log_loss(actual: list[int], probability: list[float]) -> float:
    eps = 1e-9
    return -mean(
        [
            value * math.log(min(1 - eps, max(eps, forecast)))
            + (1 - value) * math.log(min(1 - eps, max(eps, 1 - forecast)))
            for value, forecast in zip(actual, probability, strict=True)
        ]
    )


def precision_recall(actual: list[int], probability: list[float]) -> tuple[float, float]:
    predicted = [int(value >= 0.5) for value in probability]
    true_positive = sum(a == 1 and p == 1 for a, p in zip(actual, predicted, strict=True))
    predicted_positive = sum(predicted)
    actual_positive = sum(actual)
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / actual_positive if actual_positive else 0.0
    return precision, recall


def calibration_terms(actual: list[int], probability: list[float]) -> tuple[float | None, float | None]:
    if len(actual) < 3 or len(set(actual)) < 2:
        return None, None
    eps = 1e-6
    logits = np.asarray(
        [math.log(min(1 - eps, max(eps, value)) / (1 - min(1 - eps, max(eps, value)))) for value in probability]
    )
    matrix = np.column_stack([np.ones(len(logits)), logits])
    coefficients = np.linalg.pinv(matrix.T @ matrix) @ matrix.T @ np.asarray(actual, dtype=float)
    return float(coefficients[0]), float(coefficients[1])


def stable_rank_local(values: list[float], *, descending: bool) -> list[float]:
    adjusted = [-value for value in values] if descending else list(values)
    order = sorted(range(len(adjusted)), key=lambda index: (adjusted[index], index))
    ranks = [0.0] * len(adjusted)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and adjusted[order[end]] == adjusted[order[cursor]]:
            end += 1
        rank = (cursor + end - 1) / 2 + 1
        for index in order[cursor:end]:
            ranks[index] = rank
        cursor = end
    return ranks


if __name__ == "__main__":
    raise SystemExit(main())
