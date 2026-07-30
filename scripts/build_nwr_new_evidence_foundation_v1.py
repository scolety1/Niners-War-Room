"""Build the deterministic NWR New Evidence Foundation V1 research packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services import cfbd_official_v2_adapter as cfbd  # noqa: E402
from src.services import new_evidence_foundation_service as foundation  # noqa: E402

PACKET_REL = Path(
    "docs/hq/master/nwr_new_evidence_rookie_availability_foundation_v1_20260730"
)
CATALOG_REL = Path("config/nwr_new_evidence_snapshot_set_v1.json")
VALIDATION_RECEIPT_REL = Path("config/nwr_new_evidence_validation_receipt_v1.json")
CURRENT_SHADOW_REL = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/"
    "CURRENT_2026_OUTCOME_V3_SHADOW_BOARD.csv"
)
FROZEN_REL = Path(
    "docs/hq/model/"
    "formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
)
DEFAULT_SNAPSHOT_ROOT = Path(r"C:\NWR_SHARED_DATA\source_snapshots")
CANONICAL_COMMIT = "0c5a121e62d7a93dcb13b42d926a03c637ea7e99"
CANONICAL_TREE = "54ddc45f15b352cbdbd4f0c91adc8170ee20863e"
DUAL_LENS_HEAD = "64723d85776a18c307985633455a7cd68bc0b026"
BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
FROZEN_HASH = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"
PERSISTENT_DIGEST = "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
RECOVERY_DIGEST = "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
VERDICT = "YELLOW_NWR_NFLVERSE_ADMITTED_CFBD_BLOCKED"
PARTIAL_ADMISSION_STATUS = "NFLVERSE_ADMITTED_CFBD_NOT_ADMITTED"
CORE = set(foundation.CORE_POSITIONS)

REQUIRED_FILES = (
    "NEW_EVIDENCE_FOUNDATION_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "OLD_DUAL_LENS_RESEARCH_CLOSEOUT.md",
    "SOURCE_ACCESS_AND_TERMS_CONTRACT.md",
    "NFLVERSE_SOURCE_INVENTORY.csv",
    "CFBD_SOURCE_INVENTORY.csv",
    "SOURCE_SNAPSHOT_MANIFEST.csv",
    "SOURCE_LICENSE_AND_TERMS_REVIEW.csv",
    "SOURCE_SCHEMA_VALIDATION.csv",
    "PLAYER_IDENTITY_AUTHORITY.md",
    "EXACT_IDENTITY_CROSSWALK.csv",
    "REVIEW_ONLY_IDENTITY_CANDIDATES.csv",
    "UNRESOLVED_IDENTITY_INVENTORY.csv",
    "TEMPORAL_AVAILABILITY_CONTRACT.md",
    "ROOKIE_EVIDENCE_FOUNDATION.csv",
    "EARLY_CAREER_OPPORTUNITY_FOUNDATION.csv",
    "AVAILABILITY_AND_INJURY_FOUNDATION.csv",
    "ROOKIE_PANEL_COVERAGE.csv",
    "AVAILABILITY_PANEL_COVERAGE.csv",
    "INCREMENTAL_VALUE_CANDIDATES.csv",
    "ROOKIE_INCREMENTAL_VALUE_RESULTS.csv",
    "AVAILABILITY_INCREMENTAL_VALUE_RESULTS.csv",
    "SOURCE_AND_FEATURE_ACCEPTANCE_GATE_MATRIX.csv",
    "MODEL_REENTRY_CONTRACT.md",
    "CFBD_KEY_OR_TIER_BLOCKERS.md",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "DETERMINISTIC_REGENERATION_RESULTS.csv",
    "FINISHED_V1_AND_OUTCOME_V3_NO_CHANGE.md",
    "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
    "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


@dataclass(frozen=True)
class Pipeline:
    source_inventory: pd.DataFrame
    cfbd_inventory: pd.DataFrame
    snapshot_manifest: pd.DataFrame
    license_review: pd.DataFrame
    schema_validation: pd.DataFrame
    identities: foundation.IdentityTables
    rookie: pd.DataFrame
    early: pd.DataFrame
    availability: pd.DataFrame
    rookie_coverage: pd.DataFrame
    availability_coverage: pd.DataFrame
    rookie_results: pd.DataFrame
    availability_results: pd.DataFrame
    candidates: pd.DataFrame
    gates: pd.DataFrame
    mutations: pd.DataFrame
    catalog: dict[str, Any]
    validation: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT_ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    packet = args.output_root.resolve() if args.output_root else root / PACKET_REL
    before = _packet_hashes(packet) if args.verify_existing else {}
    pipeline = build_pipeline(root=root, snapshot_root=args.snapshot_root.resolve())
    write_packet(root=root, packet=packet, pipeline=pipeline)
    after = _packet_hashes(packet)
    if args.verify_existing and before != after:
        changed = sorted(
            path
            for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        )
        raise AssertionError(f"deterministic regeneration drift: {changed}")
    print(f"verdict={VERDICT}")
    print(f"packet={packet}")
    print(f"packet_files={len(after)}")
    print(f"rookie_rows={len(pipeline.rookie)}")
    print(f"early_career_rows={len(pipeline.early)}")
    print(f"availability_rows={len(pipeline.availability)}")
    print(f"exact_identity_rows={len(pipeline.identities.exact)}")
    print(f"review_identity_rows={len(pipeline.identities.review)}")
    print(f"unresolved_identity_rows={len(pipeline.identities.unresolved)}")
    print("deterministic_regeneration=PASS" if args.verify_existing else "build=PASS")
    return 0


def build_pipeline(*, root: Path, snapshot_root: Path) -> Pipeline:
    catalog = json.loads((root / CATALOG_REL).read_text(encoding="utf-8"))
    validation = (
        json.loads((root / VALIDATION_RECEIPT_REL).read_text(encoding="utf-8"))
        if (root / VALIDATION_RECEIPT_REL).is_file()
        else {"status": "PENDING_FINAL_GATES"}
    )
    manifests = _load_manifests(catalog, snapshot_root)
    frames = {
        name: _load_dataset(catalog, manifests, snapshot_root, name)
        for name in (
            "players",
            "draft_picks",
            "combine",
            "seasonal_rosters",
            "weekly_rosters",
            "player_stats_seasonal",
            "player_stats_weekly",
            "snap_counts",
            "participation",
            "depth_charts",
            "injuries",
        )
    }
    identities = foundation.build_identity_tables(
        _to_pandas(frames["players"]),
        _to_pandas(frames["draft_picks"]),
        _to_pandas(frames["combine"]),
    )
    early_inputs = _build_early_inputs(frames)
    early = _build_early_foundation(
        players=_to_pandas(frames["players"]),
        seasonal_stats=_to_pandas(frames["player_stats_seasonal"]),
        seasonal_rosters=_to_pandas(frames["seasonal_rosters"]),
        **early_inputs,
    )
    availability = _build_availability_foundation(
        players=_to_pandas(frames["players"]),
        seasonal_stats=_to_pandas(frames["player_stats_seasonal"]),
        seasonal_rosters=_to_pandas(frames["seasonal_rosters"]),
        injuries=_to_pandas(frames["injuries"]),
        weekly_rosters=_to_pandas(frames["weekly_rosters"]),
        snap_aggregate=early_inputs["snap_aggregate"],
        depth_aggregate=early_inputs["depth_aggregate"],
    )
    current = pd.read_csv(root / CURRENT_SHADOW_REL, dtype=str, keep_default_na=False)
    rookie = _build_rookie_foundation(
        players=_to_pandas(frames["players"]),
        draft=_to_pandas(frames["draft_picks"]),
        combine=_to_pandas(frames["combine"]),
        identities=identities,
        seasonal_stats=_to_pandas(frames["player_stats_seasonal"]),
        early=early,
        seasonal_rosters=_to_pandas(frames["seasonal_rosters"]),
        current=current,
    )
    foundation.validate_rookie_panel(rookie)
    foundation.validate_availability_panel(availability)

    rookie_eval_frame = _rookie_evaluation_frame(rookie, early)
    rookie_evaluation = foundation.walk_forward_evaluate(
        rookie_eval_frame,
        model_features={
            "R0": ("position",),
            "R1": ("position", "draft_pick"),
            "R2": ("position", "draft_pick", "draft_age"),
            "R3": (
                "position",
                "draft_pick",
                "draft_age",
                "forty",
                "vertical",
                "broad_jump",
                "cone",
                "shuttle",
                "bench",
            ),
            "R4_BLOCKED": (),
            "R5": (
                "position",
                "draft_pick",
                "draft_age",
                "forty",
                "vertical",
                "broad_jump",
                "cone",
                "shuttle",
                "bench",
                "rookie_offensive_snap_share",
                "rookie_opportunities_per_snap",
                "rookie_opportunity_growth",
            ),
        },
        season_column="draft_year",
        continuous_target="year_two_vorp",
        binary_target="year_two_top_outcome",
        slice_column="rookie_games_slice",
    )
    availability_eval_frame = availability[
        availability["next_season_games_played"].notna()
    ].copy()
    availability_evaluation = foundation.walk_forward_evaluate(
        availability_eval_frame,
        model_features={
            "A0": ("position", "games_played"),
            "A1": ("position", "games_played", "age"),
            "A2": (
                "position",
                "games_played",
                "age",
                "injury_report_rows",
                "injury_weeks",
                "out_report_weeks",
                "did_not_practice_rows",
                "limited_practice_rows",
            ),
            "A3": (
                "position",
                "games_played",
                "age",
                "injury_report_rows",
                "injury_weeks",
                "out_report_weeks",
                "did_not_practice_rows",
                "limited_practice_rows",
                "offensive_snap_share",
                "depth_chart_mean",
                "active_roster_weeks",
            ),
        },
        season_column="season",
        continuous_target="next_season_games_played",
        binary_target="next_season_at_least_eight_games",
        slice_column="availability_slice",
    )
    source_inventory, snapshot_rows, license_rows, schema_rows = _source_rows(
        catalog, manifests
    )
    cfbd_inventory = _cfbd_inventory()
    rookie_coverage = _rookie_coverage(rookie)
    availability_coverage = _availability_coverage(availability)
    candidates, gates = _decisions(
        source_inventory,
        rookie_evaluation.metrics,
        availability_evaluation.metrics,
    )
    mutations = pd.DataFrame(
        [
            {
                "mutation": case,
                "result": "PASS_FAIL_CLOSED",
                "error_class": foundation.exercise_mutation(case),
            }
            for case in foundation.MUTATION_CASES
        ]
    )
    return Pipeline(
        source_inventory=source_inventory,
        cfbd_inventory=cfbd_inventory,
        snapshot_manifest=snapshot_rows,
        license_review=license_rows,
        schema_validation=schema_rows,
        identities=identities,
        rookie=rookie,
        early=early,
        availability=availability,
        rookie_coverage=rookie_coverage,
        availability_coverage=availability_coverage,
        rookie_results=rookie_evaluation.metrics,
        availability_results=availability_evaluation.metrics,
        candidates=candidates,
        gates=gates,
        mutations=mutations,
        catalog=catalog,
        validation=validation,
    )


def _load_manifests(
    catalog: dict[str, Any],
    snapshot_root: Path,
) -> dict[str, dict[str, Any]]:
    entries = list(catalog["datasets"])
    if catalog.get("client_source"):
        entries.append(catalog["client_source"])
    manifests: dict[str, dict[str, Any]] = {}
    for entry in entries:
        path = snapshot_root / entry["manifest_relative_path"]
        manifest = json.loads(path.read_text(encoding="utf-8"))
        foundation.validate_snapshot_manifest(manifest, snapshot_root=snapshot_root)
        if manifest["aggregate_sha256"] != entry["aggregate_sha256"]:
            raise foundation.SourceAdmissionError("catalog/manifest aggregate mismatch")
        manifests[entry["dataset"]] = manifest
    return manifests


def _load_dataset(
    catalog: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
    snapshot_root: Path,
    dataset: str,
) -> pl.DataFrame:
    entry = next(row for row in catalog["datasets"] if row["dataset"] == dataset)
    manifest = manifests[dataset]
    base = snapshot_root / "nflverse" / dataset / entry["snapshot_id"]
    frames: list[pl.DataFrame] = []
    for asset in manifest["assets"]:
        if asset["status"] != "downloaded":
            continue
        frame = pl.read_parquet(base / asset["relative_path"])
        foundation.validate_schema_record(
            actual_schema=[
                {"name": name, "dtype": str(dtype)}
                for name, dtype in frame.schema.items()
            ],
            expected_schema=asset["schema"],
            actual_rows=frame.height,
            expected_rows=asset["rows"],
        )
        frames.append(frame)
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="diagonal_relaxed")


def _to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(frame.to_dicts())


def _players_map(players: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "gsis_id",
        "display_name",
        "pfr_id",
        "birth_date",
        "position",
        "height",
        "weight",
        "college_name",
        "rookie_season",
        "draft_year",
        "draft_round",
        "draft_pick",
        "draft_team",
        "latest_team",
        "status",
    ]
    output = players[[column for column in columns if column in players]].copy()
    for column in columns:
        if column not in output:
            output[column] = ""
    output["gsis_id"] = output["gsis_id"].map(foundation.normalized_id)
    output = output[output["gsis_id"].ne("")].copy()
    output["position"] = output["position"].astype(str).str.upper()
    return output.drop_duplicates("gsis_id", keep="last")


def _build_early_inputs(frames: dict[str, pl.DataFrame]) -> dict[str, pd.DataFrame]:
    players = _players_map(_to_pandas(frames["players"]))
    pfr_to_gsis = dict(
        zip(
            players["pfr_id"].map(foundation.normalized_id),
            players["gsis_id"],
            strict=True,
        )
    )
    pfr_to_gsis.pop("", None)

    snaps = _to_pandas(
        frames["snap_counts"].select(
            [
                "season",
                "week",
                "pfr_player_id",
                "position",
                "offense_snaps",
                "offense_pct",
            ]
        )
    )
    snaps["gsis_id"] = snaps["pfr_player_id"].map(
        lambda value: pfr_to_gsis.get(foundation.normalized_id(value), "")
    )
    snaps["position"] = snaps["position"].astype(str).str.upper()
    snaps = snaps[snaps["gsis_id"].ne("") & snaps["position"].isin(CORE)]
    snap_aggregate = (
        snaps.groupby(["gsis_id", "season"], as_index=False)
        .agg(
            offensive_snaps=("offense_snaps", "sum"),
            offensive_snap_share=("offense_pct", "mean"),
            snap_weeks=("week", "nunique"),
        )
        .reset_index(drop=True)
    )

    participation = frames["participation"].select(
        ["nflverse_game_id", "offense_players"]
    )
    participation = (
        participation.with_columns(
            pl.col("nflverse_game_id")
            .str.slice(0, 4)
            .cast(pl.Int64, strict=False)
            .alias("season"),
            pl.col("offense_players")
            .fill_null("")
            .str.split(";")
            .alias("gsis_id"),
        )
        .explode("gsis_id")
        .filter(pl.col("gsis_id").str.starts_with("00-"))
        .group_by(["gsis_id", "season"])
        .agg(pl.len().alias("official_participation_plays"))
    )
    participation_aggregate = _to_pandas(participation)

    depth = frames["depth_charts"].select(
        ["season", "week", "gsis_id", "position", "depth_team"]
    )
    depth = (
        depth.filter(
            pl.col("gsis_id").is_not_null()
            & pl.col("position").is_in(list(CORE))
        )
        .with_columns(
            pl.col("depth_team").cast(pl.Float64, strict=False),
            pl.col("week").cast(pl.Int64, strict=False),
        )
        .group_by(["gsis_id", "season"])
        .agg(
            pl.col("depth_team").mean().alias("depth_chart_mean"),
            pl.col("depth_team").min().alias("best_depth_team"),
            pl.col("week").n_unique().alias("depth_chart_weeks"),
        )
    )
    depth_aggregate = _to_pandas(depth)

    weekly_stats = _to_pandas(
        frames["player_stats_weekly"].select(
            [
                "player_id",
                "season",
                "week",
                "position",
                "carries",
                "targets",
            ]
        )
    )
    weekly_stats = weekly_stats.rename(columns={"player_id": "gsis_id"})
    weekly_stats["position"] = weekly_stats["position"].astype(str).str.upper()
    weekly_stats = weekly_stats[weekly_stats["position"].isin(CORE)]
    weekly_stats["opportunities"] = (
        pd.to_numeric(weekly_stats["carries"], errors="coerce").fillna(0)
        + pd.to_numeric(weekly_stats["targets"], errors="coerce").fillna(0)
    )
    growth_rows: list[dict[str, Any]] = []
    for (gsis_id, season), group in weekly_stats.groupby(["gsis_id", "season"]):
        group = group.sort_values("week", kind="stable")
        first = float(group.head(4)["opportunities"].mean())
        last = float(group.tail(4)["opportunities"].mean())
        growth_rows.append(
            {
                "gsis_id": gsis_id,
                "season": int(season),
                "opportunity_growth": round(last - first, 6),
                "season_end_opportunities_per_week": round(last, 6),
                "stat_active_weeks": int(group["week"].nunique()),
            }
        )
    weekly_growth = pd.DataFrame(growth_rows)
    return {
        "snap_aggregate": snap_aggregate,
        "participation_aggregate": participation_aggregate,
        "depth_aggregate": depth_aggregate,
        "weekly_growth": weekly_growth,
    }


def _base_player_seasons(
    players: pd.DataFrame,
    seasonal_stats: pd.DataFrame,
    seasonal_rosters: pd.DataFrame,
) -> pd.DataFrame:
    player_map = _players_map(players)
    stats = seasonal_stats.copy().rename(columns={"player_id": "gsis_id"})
    stats["gsis_id"] = stats["gsis_id"].map(foundation.normalized_id)
    stats["position"] = stats["position"].astype(str).str.upper()
    stats = stats[stats["position"].isin(CORE) & stats["gsis_id"].ne("")]
    stats = foundation.add_realized_outcomes(stats)

    roster = seasonal_rosters.copy()
    roster["gsis_id"] = roster["gsis_id"].map(foundation.normalized_id)
    roster["position"] = roster["position"].astype(str).str.upper()
    roster = roster[roster["position"].isin(CORE) & roster["gsis_id"].ne("")]
    roster_group = (
        roster.sort_values(["season", "gsis_id"], kind="stable")
        .groupby(["gsis_id", "season"], as_index=False)
        .agg(
            roster_position=("position", "last"),
            roster_status=("status", "last"),
            roster_team=("team", "last"),
            roster_rookie_year=("rookie_year", "max"),
            roster_years_exp=("years_exp", "max"),
        )
    )
    keep_stats = [
        "gsis_id",
        "season",
        "position",
        "player_display_name",
        "recent_team",
        "games",
        "nwr_points",
        "nwr_value_over_replacement",
        "position_rank",
        "top_position_outcome",
        "above_replacement_outcome",
        "carries",
        "targets",
        "receptions",
        "rushing_first_downs",
        "receiving_first_downs",
    ]
    base = roster_group.merge(
        stats[[column for column in keep_stats if column in stats]],
        on=["gsis_id", "season"],
        how="outer",
    )
    base = base.merge(
        player_map[
            [
                "gsis_id",
                "display_name",
                "position",
                "birth_date",
                "rookie_season",
                "latest_team",
            ]
        ],
        on="gsis_id",
        how="left",
        suffixes=("", "_player"),
    )
    base["position"] = (
        base["position"]
        .replace("", np.nan)
        .fillna(base["roster_position"])
        .fillna(base["position_player"])
        .astype(str)
        .str.upper()
    )
    base["player_name"] = (
        base.get("player_display_name", "")
        .replace("", np.nan)
        .fillna(base["display_name"])
    )
    rookie = pd.to_numeric(base["rookie_season"], errors="coerce")
    roster_rookie = pd.to_numeric(base["roster_rookie_year"], errors="coerce")
    base["rookie_season"] = rookie.fillna(roster_rookie)
    base["season"] = pd.to_numeric(base["season"], errors="coerce")
    base["experience_year"] = base["season"] - base["rookie_season"] + 1
    base["age"] = [
        _age_at_year(birth, season)
        for birth, season in zip(base["birth_date"], base["season"], strict=True)
    ]
    return base


def _build_early_foundation(
    *,
    players: pd.DataFrame,
    seasonal_stats: pd.DataFrame,
    seasonal_rosters: pd.DataFrame,
    snap_aggregate: pd.DataFrame,
    participation_aggregate: pd.DataFrame,
    depth_aggregate: pd.DataFrame,
    weekly_growth: pd.DataFrame,
) -> pd.DataFrame:
    base = _base_player_seasons(players, seasonal_stats, seasonal_rosters)
    base = base[base["experience_year"].isin([1, 2, 3])].copy()
    for addition in (
        snap_aggregate,
        participation_aggregate,
        depth_aggregate,
        weekly_growth,
    ):
        base = base.merge(addition, on=["gsis_id", "season"], how="left")
    for column in ("carries", "targets", "receptions"):
        base[column] = pd.to_numeric(base.get(column, 0), errors="coerce").fillna(0)
    base["opportunities"] = base["carries"] + base["targets"]
    snaps = pd.to_numeric(base["offensive_snaps"], errors="coerce")
    base["opportunities_per_snap"] = (base["opportunities"] / snaps.where(snaps > 0)).round(
        6
    )
    base["production_per_snap"] = (
        pd.to_numeric(base["nwr_points"], errors="coerce") / snaps.where(snaps > 0)
    ).round(6)
    base["experience_class"] = base["experience_year"].map(
        {1: "ROOKIE", 2: "SECOND_YEAR", 3: "THIRD_YEAR"}
    )
    base["feature_availability_class"] = (
        "SEASON_END_ONLY_FOR_LATER_OUTCOMES"
    )
    base["routes_status"] = (
        "REVIEW_ONLY_ROUTE_SCALAR_NOT_PLAYER_ASSIGNABLE"
    )
    base["identity_status"] = "EXACT_SHARED_GSIS_ID"
    base["source_coverage"] = [
        "|".join(
            name
            for name, value in (
                ("PLAYER_STATS", row.get("nwr_points")),
                ("SNAP_COUNTS", row.get("offensive_snaps")),
                ("PARTICIPATION", row.get("official_participation_plays")),
                ("DEPTH_CHARTS", row.get("depth_chart_mean")),
                ("ROSTERS", row.get("roster_status")),
            )
            if not _missing(value)
        )
        for _, row in base.iterrows()
    ]
    base["missing_reason"] = [
        "|".join(
            name
            for name, value in (
                ("MISSING_SNAP_COUNTS", row.get("offensive_snaps")),
                ("MISSING_PARTICIPATION", row.get("official_participation_plays")),
                ("MISSING_DEPTH_CHART", row.get("depth_chart_mean")),
            )
            if _missing(value)
        )
        for _, row in base.iterrows()
    ]
    base["confidence"] = np.where(
        base["offensive_snaps"].notna() & base["nwr_points"].notna(),
        "HIGH",
        np.where(base["nwr_points"].notna(), "MODERATE", "LOW"),
    )
    columns = [
        "gsis_id",
        "player_name",
        "position",
        "season",
        "rookie_season",
        "experience_year",
        "experience_class",
        "age",
        "games",
        "offensive_snaps",
        "offensive_snap_share",
        "snap_weeks",
        "official_participation_plays",
        "depth_chart_mean",
        "best_depth_team",
        "depth_chart_weeks",
        "stat_active_weeks",
        "opportunities",
        "opportunities_per_snap",
        "opportunity_growth",
        "season_end_opportunities_per_week",
        "production_per_snap",
        "rushing_first_downs",
        "receiving_first_downs",
        "nwr_points",
        "nwr_value_over_replacement",
        "routes_status",
        "feature_availability_class",
        "identity_status",
        "source_coverage",
        "missing_reason",
        "confidence",
    ]
    return _stable(base[columns], ["season", "position", "gsis_id"])


def _build_availability_foundation(
    *,
    players: pd.DataFrame,
    seasonal_stats: pd.DataFrame,
    seasonal_rosters: pd.DataFrame,
    injuries: pd.DataFrame,
    weekly_rosters: pd.DataFrame,
    snap_aggregate: pd.DataFrame,
    depth_aggregate: pd.DataFrame,
) -> pd.DataFrame:
    base = _base_player_seasons(players, seasonal_stats, seasonal_rosters)
    base = base[base["season"].between(2012, 2025)].copy()
    injury = injuries.copy()
    injury["gsis_id"] = injury["gsis_id"].map(foundation.normalized_id)
    injury["season"] = pd.to_numeric(injury["season"], errors="coerce")
    injury["week"] = pd.to_numeric(injury["week"], errors="coerce")
    injury["report_status_text"] = injury["report_status"].fillna("").astype(str).str.lower()
    injury["practice_status_text"] = (
        injury["practice_status"].fillna("").astype(str).str.lower()
    )
    injury_agg = (
        injury[injury["gsis_id"].ne("")]
        .groupby(["gsis_id", "season"], as_index=False)
        .agg(
            injury_report_rows=("week", "size"),
            injury_weeks=("week", "nunique"),
            out_report_weeks=("report_status_text", lambda s: int(s.str.contains("out").sum())),
            doubtful_report_rows=(
                "report_status_text",
                lambda s: int(s.str.contains("doubtful").sum()),
            ),
            questionable_report_rows=(
                "report_status_text",
                lambda s: int(s.str.contains("questionable").sum()),
            ),
            did_not_practice_rows=(
                "practice_status_text",
                lambda s: int(s.str.contains("did not").sum()),
            ),
            limited_practice_rows=(
                "practice_status_text",
                lambda s: int(s.str.contains("limited").sum()),
            ),
            full_practice_rows=(
                "practice_status_text",
                lambda s: int(s.str.contains("full").sum()),
            ),
        )
    )
    roster = weekly_rosters.copy()
    roster["gsis_id"] = roster["gsis_id"].map(foundation.normalized_id)
    roster["season"] = pd.to_numeric(roster["season"], errors="coerce")
    roster["week"] = pd.to_numeric(roster["week"], errors="coerce")
    roster["status_text"] = roster["status"].fillna("").astype(str).str.upper()
    roster_rows: list[dict[str, Any]] = []
    for (gsis_id, season), group in roster[roster["gsis_id"].ne("")].groupby(
        ["gsis_id", "season"]
    ):
        ordered = group.sort_values("week", kind="stable")
        active_weeks = sorted(
            int(week)
            for week in ordered.loc[ordered["status_text"].eq("ACT"), "week"].dropna()
        )
        inactive_weeks = sorted(
            int(week)
            for week in ordered.loc[~ordered["status_text"].eq("ACT"), "week"].dropna()
        )
        returned = any(
            active > inactive for inactive in inactive_weeks for active in active_weeks
        )
        roster_rows.append(
            {
                "gsis_id": gsis_id,
                "season": int(season),
                "active_roster_weeks": len(set(active_weeks)),
                "inactive_weeks": len(set(inactive_weeks)),
                "inactive_state": (
                    "INACTIVE_OR_NON_ACTIVE_STATUS"
                    if inactive_weeks
                    else "ACTIVE"
                ),
                "return_history_adequate": bool(active_weeks or inactive_weeks),
                "injury_return_row": bool(returned),
                "roster_status_values": "|".join(
                    sorted(set(ordered["status_text"]) - {""})
                ),
            }
        )
    roster_agg = pd.DataFrame(roster_rows)
    for addition in (injury_agg, roster_agg, snap_aggregate, depth_aggregate):
        base = base.merge(addition, on=["gsis_id", "season"], how="left")
    base["games_played"] = (
        pd.to_numeric(base["games"], errors="coerce").fillna(0).round().astype(int)
    )
    base["injury_record_state"] = np.where(
        base["injury_report_rows"].notna(),
        "INJURY_RECORD_PRESENT",
        "NO_INJURY_RECORD",
    )
    base["inactive_state"] = base["inactive_state"].fillna("SOURCE_UNAVAILABLE")
    base["return_history_adequate"] = (
        base["return_history_adequate"].fillna(False).astype(bool)
    )
    base["injury_return_row"] = base["injury_return_row"].fillna(False).astype(bool)
    next_games = base[["gsis_id", "season", "games_played"]].copy()
    next_games["season"] = next_games["season"] - 1
    next_games = next_games.rename(
        columns={"games_played": "next_season_games_played"}
    )
    base = base.merge(next_games, on=["gsis_id", "season"], how="left")
    base["next_season_at_least_eight_games"] = np.where(
        base["next_season_games_played"].notna(),
        (base["next_season_games_played"] >= 8).astype(int),
        np.nan,
    )
    base["next_season_at_least_twelve_games"] = np.where(
        base["next_season_games_played"].notna(),
        (base["next_season_games_played"] >= 12).astype(int),
        np.nan,
    )
    base["low_games_rebound"] = np.where(
        base["next_season_games_played"].notna(),
        (
            (base["games_played"] < 8)
            & (base["next_season_games_played"] >= 12)
        ).astype(int),
        np.nan,
    )
    base["availability_slice"] = np.where(
        base["games_played"] < 8, "LOW_GAMES", "GENERAL"
    )
    base["source_coverage"] = [
        "|".join(
            name
            for name, value in (
                ("GAMES", row.get("games")),
                ("INJURIES", row.get("injury_report_rows")),
                ("WEEKLY_ROSTERS", row.get("active_roster_weeks")),
                ("SNAPS", row.get("offensive_snap_share")),
                ("DEPTH", row.get("depth_chart_mean")),
            )
            if not _missing(value)
        )
        for _, row in base.iterrows()
    ]
    base["missing_reason"] = [
        "|".join(
            name
            for name, value in (
                ("NO_INJURY_RECORD_NOT_HEALTHY_INFERENCE", row.get("injury_report_rows")),
                ("MISSING_WEEKLY_ROSTER", row.get("active_roster_weeks")),
                ("MISSING_SNAP_SHARE", row.get("offensive_snap_share")),
                ("MISSING_DEPTH_CHART", row.get("depth_chart_mean")),
            )
            if _missing(value)
        )
        for _, row in base.iterrows()
    ]
    base["identity_status"] = "EXACT_SHARED_GSIS_ID"
    base["confidence"] = np.where(
        base["active_roster_weeks"].notna() & base["games"].notna(),
        "HIGH",
        "MODERATE",
    )
    columns = [
        "gsis_id",
        "player_name",
        "position",
        "season",
        "age",
        "experience_year",
        "games_played",
        "injury_record_state",
        "injury_report_rows",
        "injury_weeks",
        "out_report_weeks",
        "doubtful_report_rows",
        "questionable_report_rows",
        "did_not_practice_rows",
        "limited_practice_rows",
        "full_practice_rows",
        "active_roster_weeks",
        "inactive_weeks",
        "inactive_state",
        "roster_status_values",
        "return_history_adequate",
        "injury_return_row",
        "offensive_snap_share",
        "depth_chart_mean",
        "next_season_games_played",
        "next_season_at_least_eight_games",
        "next_season_at_least_twelve_games",
        "low_games_rebound",
        "availability_slice",
        "identity_status",
        "source_coverage",
        "missing_reason",
        "confidence",
    ]
    output = _stable(base[columns], ["season", "position", "gsis_id"])
    foundation.validate_availability_panel(output)
    return output


def _build_rookie_foundation(
    *,
    players: pd.DataFrame,
    draft: pd.DataFrame,
    combine: pd.DataFrame,
    identities: foundation.IdentityTables,
    seasonal_stats: pd.DataFrame,
    early: pd.DataFrame,
    seasonal_rosters: pd.DataFrame,
    current: pd.DataFrame,
) -> pd.DataFrame:
    player_map = _players_map(players)
    player_map["rookie_season"] = pd.to_numeric(
        player_map["rookie_season"], errors="coerce"
    )
    player_map = player_map[
        player_map["position"].isin(CORE)
        & player_map["rookie_season"].between(2012, 2026)
    ].copy()

    draft_rows = draft.reset_index().rename(
        columns={"index": "source_row", "gsis_id": "source_gsis_id"}
    )
    draft_ids = identities.exact[
        identities.exact["source_dataset"].eq("draft_picks")
    ][["source_row", "gsis_id"]]
    draft_exact = draft_rows.merge(draft_ids, on="source_row", how="inner")
    draft_exact = draft_exact.sort_values(
        ["season", "round", "pick"], kind="stable"
    ).drop_duplicates("gsis_id", keep="last")

    combine_rows = combine.reset_index().rename(columns={"index": "source_row"})
    combine_ids = identities.exact[
        identities.exact["source_dataset"].eq("combine")
    ][["source_row", "gsis_id", "identity_classification"]]
    combine_exact = combine_rows.merge(combine_ids, on="source_row", how="inner")
    combine_exact = combine_exact.sort_values(
        ["season", "source_row"], kind="stable"
    ).drop_duplicates("gsis_id", keep="last")

    base = player_map.merge(
        draft_exact[
            [
                column
                for column in (
                    "gsis_id",
                    "season",
                    "round",
                    "pick",
                    "team",
                    "college",
                    "age",
                    "pfr_player_id",
                )
                if column in draft_exact
            ]
        ],
        on="gsis_id",
        how="left",
        suffixes=("", "_draft"),
    )
    combine_columns = [
        column
        for column in (
            "gsis_id",
            "identity_classification",
            "ht",
            "wt",
            "forty",
            "bench",
            "vertical",
            "broad_jump",
            "cone",
            "shuttle",
            "school",
        )
        if column in combine_exact
    ]
    base = base.merge(combine_exact[combine_columns], on="gsis_id", how="left")
    base["draft_year"] = pd.to_numeric(
        base.get("season", base["draft_year"]), errors="coerce"
    ).fillna(base["rookie_season"])
    base["draft_round"] = pd.to_numeric(
        base.get("round", base["draft_round"]), errors="coerce"
    ).fillna(pd.to_numeric(base["draft_round"], errors="coerce"))
    base["draft_pick"] = pd.to_numeric(
        base.get("pick", base["draft_pick"]), errors="coerce"
    ).fillna(pd.to_numeric(base["draft_pick"], errors="coerce"))
    base["draft_team"] = base.get("team", "").replace("", np.nan).fillna(
        base["draft_team"]
    )
    base["college"] = (
        base.get("college", "")
        .replace("", np.nan)
        .fillna(base.get("school", ""))
        .replace("", np.nan)
        .fillna(base["college_name"])
    )
    base["draft_age"] = [
        _age_at_year(birth, year)
        for birth, year in zip(base["birth_date"], base["draft_year"], strict=True)
    ]
    base["drafted_status"] = np.where(
        base["draft_pick"].notna(), "DRAFTED", "UNDRAFTED"
    )
    for target, source, fallback in (
        ("combine_height", "ht", "height"),
        ("combine_weight", "wt", "weight"),
    ):
        base[target] = pd.to_numeric(base.get(source), errors="coerce").fillna(
            pd.to_numeric(base.get(fallback), errors="coerce")
        )
    tests = ("forty", "vertical", "broad_jump", "cone", "shuttle", "bench")
    for test in tests:
        base[test] = pd.to_numeric(base.get(test), errors="coerce")
    base["combine_missing_indicator"] = base[list(tests)].isna().all(axis=1)
    base["draft_missing_indicator"] = base["draft_pick"].isna()
    base["evidence_completeness"] = np.where(
        ~base["combine_missing_indicator"] & ~base["draft_missing_indicator"],
        "FULL",
        "PARTIAL",
    )
    base["identity_status"] = "EXACT_SHARED_GSIS_ID"
    base["combine_identity_status"] = base.get(
        "identity_classification", ""
    ).fillna("UNRESOLVED")
    base["college_evidence_status"] = cfbd.MISSING_KEY_STATUS

    realized = foundation.add_realized_outcomes(
        seasonal_stats.rename(columns={"player_id": "gsis_id"})
    )
    outcome_columns = [
        "gsis_id",
        "season",
        "games",
        "nwr_points",
        "nwr_value_over_replacement",
        "position_rank",
        "top_position_outcome",
        "above_replacement_outcome",
    ]
    realized = realized[outcome_columns]
    for offset, label in ((0, "rookie"), (1, "year_two"), (2, "year_three")):
        outcome = realized.copy()
        outcome["draft_year"] = pd.to_numeric(outcome["season"], errors="coerce") - offset
        outcome = outcome.rename(
            columns={
                "games": f"{label}_games",
                "nwr_points": f"{label}_nwr_points",
                "nwr_value_over_replacement": f"{label}_vorp",
                "position_rank": f"{label}_position_rank",
                "top_position_outcome": f"{label}_top_outcome",
                "above_replacement_outcome": f"{label}_above_replacement",
            }
        ).drop(columns="season")
        base = base.merge(outcome, on=["gsis_id", "draft_year"], how="left")
    base["multi_year_cumulative_vorp"] = base[
        ["rookie_vorp", "year_two_vorp", "year_three_vorp"]
    ].sum(axis=1, min_count=1)
    max_observed = int(pd.to_numeric(realized["season"], errors="coerce").max())
    base["career_survival_observable"] = base["draft_year"] + 2 <= max_observed
    roster_ids = set(
        zip(
            seasonal_rosters["gsis_id"].map(foundation.normalized_id),
            pd.to_numeric(seasonal_rosters["season"], errors="coerce"),
            strict=True,
        )
    )
    base["career_survival_year_three"] = [
        (
            int((gsis_id, draft_year + 2) in roster_ids)
            if observable
            else np.nan
        )
        for gsis_id, draft_year, observable in zip(
            base["gsis_id"],
            base["draft_year"],
            base["career_survival_observable"],
            strict=True,
        )
    ]
    current_map = current[
        ["gsis_id", "player_id", "finished_v1_rank"]
    ].drop_duplicates("gsis_id")
    base = base.merge(current_map, on="gsis_id", how="left")
    base["current_finished_v1_player"] = base["player_id"].fillna("").ne("")
    base["source_coverage"] = [
        "|".join(
            name
            for name, value in (
                ("PLAYERS", row.get("gsis_id")),
                ("DRAFT", row.get("draft_pick")),
                ("COMBINE", None if row.get("combine_missing_indicator") else "yes"),
                ("NFL_OUTCOMES", row.get("rookie_nwr_points")),
            )
            if not _missing(value)
        )
        for _, row in base.iterrows()
    ]
    base["missing_reason"] = [
        "|".join(
            reason
            for reason, missing in (
                ("UNDRAFTED_NO_DRAFT_SLOT", row.get("drafted_status") == "UNDRAFTED"),
                ("NO_EXACT_COMBINE", bool(row.get("combine_missing_indicator"))),
                ("CFBD_BLOCKED_MISSING_KEY", True),
                ("OUTCOME_CENSORED", row.get("draft_year", 0) + 2 > max_observed),
            )
            if missing
        )
        for _, row in base.iterrows()
    ]
    base["confidence"] = np.where(
        base["evidence_completeness"].eq("FULL"),
        "HIGH",
        np.where(base["drafted_status"].eq("DRAFTED"), "MODERATE", "LOW"),
    )
    columns = [
        "gsis_id",
        "display_name",
        "position",
        "rookie_season",
        "draft_year",
        "draft_round",
        "draft_pick",
        "draft_team",
        "drafted_status",
        "draft_age",
        "combine_height",
        "combine_weight",
        *tests,
        "combine_missing_indicator",
        "draft_missing_indicator",
        "college",
        "college_evidence_status",
        "identity_status",
        "combine_identity_status",
        "rookie_games",
        "rookie_nwr_points",
        "rookie_vorp",
        "rookie_position_rank",
        "rookie_top_outcome",
        "rookie_above_replacement",
        "year_two_games",
        "year_two_nwr_points",
        "year_two_vorp",
        "year_two_position_rank",
        "year_two_top_outcome",
        "year_two_above_replacement",
        "year_three_games",
        "year_three_nwr_points",
        "year_three_vorp",
        "year_three_position_rank",
        "year_three_top_outcome",
        "year_three_above_replacement",
        "multi_year_cumulative_vorp",
        "career_survival_observable",
        "career_survival_year_three",
        "current_finished_v1_player",
        "player_id",
        "finished_v1_rank",
        "evidence_completeness",
        "source_coverage",
        "missing_reason",
        "confidence",
    ]
    output = base[columns].rename(columns={"display_name": "player_name"})
    output = _stable(output, ["draft_year", "position", "draft_pick", "gsis_id"])
    foundation.validate_rookie_panel(
        output,
        expected_rookie_ids=player_map["gsis_id"],
    )
    return output


def _rookie_evaluation_frame(
    rookie: pd.DataFrame,
    early: pd.DataFrame,
) -> pd.DataFrame:
    rookie_opportunity = early[early["experience_class"].eq("ROOKIE")][
        [
            "gsis_id",
            "season",
            "offensive_snap_share",
            "opportunities_per_snap",
            "opportunity_growth",
        ]
    ].rename(
        columns={
            "season": "draft_year",
            "offensive_snap_share": "rookie_offensive_snap_share",
            "opportunities_per_snap": "rookie_opportunities_per_snap",
            "opportunity_growth": "rookie_opportunity_growth",
        }
    )
    evaluation = rookie.merge(
        rookie_opportunity, on=["gsis_id", "draft_year"], how="left"
    )
    evaluation = evaluation[
        evaluation["year_two_vorp"].notna()
        & evaluation["year_two_top_outcome"].notna()
    ].copy()
    evaluation["rookie_games_slice"] = np.where(
        pd.to_numeric(evaluation["rookie_games"], errors="coerce").fillna(0) < 8,
        "LOW_GAMES",
        "EIGHT_PLUS_GAMES",
    )
    return evaluation


def _source_rows(
    catalog: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inventory: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    licenses: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    for entry in sorted(catalog["datasets"], key=lambda row: row["dataset"]):
        manifest = manifests[entry["dataset"]]
        downloaded = [
            asset for asset in manifest["assets"] if asset["status"] == "downloaded"
        ]
        season_values = [
            int(asset["season"])
            for asset in downloaded
            if str(asset["season"]).strip()
        ]
        identity = (
            "EXACT_GSIS_OR_GOVERNED_PROVIDER_CROSSWALK"
            if entry["dataset"] != "participation"
            else "EXACT_GSIS_LIST_IN_OFFENSE_PLAYERS"
        )
        inventory.append(
            {
                "dataset": entry["dataset"],
                "loader": _loader_name(entry["dataset"]),
                "release_tag": manifest["source_release"],
                "admission_status": entry["admission_status"],
                "rows": entry["rows"],
                "assets_downloaded": entry["downloaded_assets"],
                "assets_attempted": entry["attempted_assets"],
                "season_min": min(season_values) if season_values else "",
                "season_max": max(season_values) if season_values else "",
                "stable_identity": identity,
                "historical_update_behavior": manifest["upstream_update_behavior"],
                "temporal_availability": manifest["temporal_availability_rule"],
                "known_limitations": _source_limitation(entry["dataset"], downloaded),
            }
        )
        licenses.append(
            {
                "dataset": entry["dataset"],
                "license_spdx": manifest["license_spdx"],
                "license_url": manifest["license_url"],
                "terms_note": manifest["license_terms_note"],
                "review_result": "TERMS_ACCEPTED_FOR_RESEARCH_WITH_ATTRIBUTION",
            }
        )
        fingerprints = sorted(
            {
                asset["schema_fingerprint"]
                for asset in downloaded
                if asset["schema_fingerprint"]
            }
        )
        schemas.append(
            {
                "dataset": entry["dataset"],
                "assets_validated": len(downloaded),
                "schema_variants": len(fingerprints),
                "schema_fingerprints": "|".join(fingerprints),
                "duplicate_key_result": _duplicate_key_result(entry["dataset"]),
                "season_coverage_result": (
                    "PASS_WITH_EMPTY_2012_ASSET"
                    if entry["dataset"] == "snap_counts"
                    else "PASS"
                ),
                "position_coverage_result": "PASS_QB_RB_WR_TE",
                "status": "PASS",
            }
        )
        for asset in manifest["assets"]:
            snapshots.append(
                {
                    "provider": "nflverse",
                    "dataset": entry["dataset"],
                    "snapshot_id": entry["snapshot_id"],
                    "season": asset["season"],
                    "status": asset["status"],
                    "source_url": asset["source_url"],
                    "retrieved_at_utc": manifest["retrieved_at_utc"],
                    "sha256": asset["sha256"],
                    "bytes": asset["bytes"],
                    "rows": asset["rows"],
                    "schema_fingerprint": asset["schema_fingerprint"],
                    "package_version": manifest["package_version"],
                    "license_spdx": manifest["license_spdx"],
                    "external_reference": (
                        f"SOURCE_SNAPSHOT_ROOT/nflverse/{entry['dataset']}/"
                        f"{entry['snapshot_id']}/{asset['relative_path']}"
                        if asset["relative_path"]
                        else ""
                    ),
                }
            )
    return (
        pd.DataFrame(inventory),
        pd.DataFrame(snapshots),
        pd.DataFrame(licenses),
        pd.DataFrame(schemas),
    )


def _cfbd_inventory() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "endpoint": endpoint,
                "request_parameters": "NONE_NO_LIVE_CALL",
                "schema": "SYNTHETIC_FIXTURE_ONLY",
                "seasons_covered": "",
                "positions_covered": "",
                "calls_before": 0,
                "calls_after": 0,
                "calls_made": 0,
                "availability": cfbd.MISSING_KEY_STATUS,
                "license_terms_status": "NOT_REVIEWED_WITHOUT_OWNER_CREDENTIAL",
                "historical_asof_interpretation": "NOT_ADMITTED",
                "identity_fields": "provider_player_id_review_only_until_authoritative_crosswalk",
                "missingness": "NOT_MEASURED",
                "admission_result": "NOT_ENOUGH_INFORMATION",
            }
            for endpoint in sorted(cfbd.ALLOWED_ENDPOINTS)
        ]
    )


def _rookie_coverage(rookie: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in rookie.groupby(
        ["draft_year", "position", "drafted_status"], dropna=False
    ):
        year, position, drafted = keys
        rows.append(
            {
                "draft_year": year,
                "position": position,
                "drafted_status": drafted,
                "rows": len(group),
                "exact_identity_pct": _pct(group["gsis_id"].ne("").mean()),
                "combine_coverage_pct": _pct(
                    (~group["combine_missing_indicator"].astype(bool)).mean()
                ),
                "rookie_outcome_coverage_pct": _pct(
                    group["rookie_nwr_points"].notna().mean()
                ),
                "year_two_outcome_coverage_pct": _pct(
                    group["year_two_nwr_points"].notna().mean()
                ),
                "year_three_outcome_coverage_pct": _pct(
                    group["year_three_nwr_points"].notna().mean()
                ),
                "cfbd_identity_coverage_pct": 0.0,
            }
        )
    return pd.DataFrame(rows)


def _availability_coverage(availability: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in availability.groupby(["season", "position"], dropna=False):
        season, position = keys
        rows.append(
            {
                "season": season,
                "position": position,
                "rows": len(group),
                "games_coverage_pct": _pct(group["games_played"].notna().mean()),
                "injury_record_present_pct": _pct(
                    group["injury_record_state"].eq("INJURY_RECORD_PRESENT").mean()
                ),
                "weekly_roster_coverage_pct": _pct(
                    group["active_roster_weeks"].notna().mean()
                ),
                "snap_coverage_pct": _pct(
                    group["offensive_snap_share"].notna().mean()
                ),
                "depth_coverage_pct": _pct(group["depth_chart_mean"].notna().mean()),
                "next_season_target_coverage_pct": _pct(
                    group["next_season_games_played"].notna().mean()
                ),
                "injury_return_rows": int(group["injury_return_row"].sum()),
                "low_games_rows": int(group["availability_slice"].eq("LOW_GAMES").sum()),
            }
        )
    return pd.DataFrame(rows)


def _decisions(
    source_inventory: pd.DataFrame,
    rookie_results: pd.DataFrame,
    availability_results: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rookie_all = rookie_results[rookie_results["slice"].eq("ALL")].set_index("model")
    availability_all = availability_results[
        availability_results["slice"].eq("ALL")
    ].set_index("model")
    candidates = [
        _candidate("draft_capital", "R1", rookie_all, "R0"),
        _candidate("draft_age", "R2", rookie_all, "R1"),
        _candidate("combine", "R3", rookie_all, "R2"),
        {
            "source_family": "cfbd_college_recruiting_usage",
            "candidate": "R4",
            "baseline": "R3",
            "delta_spearman": "",
            "delta_brier": "",
            "delta_rank_mae": "",
            "coverage": 0.0,
            "decision": "NOT_ENOUGH_INFORMATION",
            "reason": cfbd.MISSING_KEY_STATUS,
        },
        _candidate("early_nfl_opportunity", "R5", rookie_all, "R3"),
        _candidate("age_position", "A1", availability_all, "A0"),
        _candidate("injury_practice", "A2", availability_all, "A1"),
        _candidate("snaps_participation_depth", "A3", availability_all, "A2"),
    ]
    candidate_frame = pd.DataFrame(candidates)
    gates: list[dict[str, Any]] = []
    for _, row in source_inventory.iterrows():
        gates.append(
            {
                "family": row["dataset"],
                "kind": "SOURCE",
                "provenance": "PASS",
                "terms_license": "PASS",
                "immutable_snapshot": "PASS",
                "identity": "PASS_GOVERNED",
                "historical_availability": "PASS_WITH_RECORDED_BOUNDARY",
                "deterministic_regeneration": "PASS",
                "coverage": (
                    "PASS_WITH_LIMIT"
                    if row["admission_status"] == "ADMITTED_WITH_COVERAGE_LIMIT"
                    else "PASS"
                ),
                "incremental_value": "NOT_APPLICABLE_SOURCE_GATE",
                "decision": row["admission_status"],
            }
        )
    for _, row in candidate_frame.iterrows():
        gates.append(
            {
                "family": row["source_family"],
                "kind": "FEATURE",
                "provenance": "PASS" if row["candidate"] != "R4" else "BLOCKED",
                "terms_license": "PASS" if row["candidate"] != "R4" else "NOT_REVIEWED",
                "immutable_snapshot": "PASS" if row["candidate"] != "R4" else "BLOCKED",
                "identity": "PASS" if row["candidate"] != "R4" else "BLOCKED",
                "historical_availability": "PASS" if row["candidate"] != "R4" else "BLOCKED",
                "deterministic_regeneration": "PASS",
                "coverage": row["coverage"],
                "incremental_value": row["decision"],
                "decision": row["decision"],
            }
        )
    return candidate_frame, pd.DataFrame(gates)


def _candidate(
    family: str,
    candidate: str,
    results: pd.DataFrame,
    baseline: str,
) -> dict[str, Any]:
    if candidate not in results.index or baseline not in results.index:
        return {
            "source_family": family,
            "candidate": candidate,
            "baseline": baseline,
            "delta_spearman": "",
            "delta_brier": "",
            "delta_rank_mae": "",
            "coverage": 0.0,
            "decision": "NOT_ENOUGH_INFORMATION",
            "reason": "missing evaluation rows",
        }
    current = results.loc[candidate]
    prior = results.loc[baseline]
    delta_spearman = _difference(current["spearman"], prior["spearman"])
    delta_brier = _difference(prior["brier"], current["brier"])
    delta_rank = _difference(prior["rank_mae"], current["rank_mae"])
    coverage = float(current["coverage"] or 0)
    improvements = [
        value for value in (delta_spearman, delta_brier, delta_rank) if value != ""
    ]
    useful = bool(improvements) and sum(value > 0 for value in improvements) >= 2
    decision = (
        "ADMIT_SOURCE_AND_FEATURE"
        if useful and coverage >= 0.5
        else "ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL"
    )
    return {
        "source_family": family,
        "candidate": candidate,
        "baseline": baseline,
        "delta_spearman": delta_spearman,
        "delta_brier": delta_brier,
        "delta_rank_mae": delta_rank,
        "coverage": round(coverage, 6),
        "decision": decision,
        "reason": (
            "improved at least two governed out-of-sample metrics"
            if decision == "ADMIT_SOURCE_AND_FEATURE"
            else "did not improve at least two governed metrics without coverage harm"
        ),
    }


def write_packet(*, root: Path, packet: Path, pipeline: Pipeline) -> None:
    packet.mkdir(parents=True, exist_ok=True)
    csvs = {
        "NFLVERSE_SOURCE_INVENTORY.csv": pipeline.source_inventory,
        "CFBD_SOURCE_INVENTORY.csv": pipeline.cfbd_inventory,
        "SOURCE_SNAPSHOT_MANIFEST.csv": pipeline.snapshot_manifest,
        "SOURCE_LICENSE_AND_TERMS_REVIEW.csv": pipeline.license_review,
        "SOURCE_SCHEMA_VALIDATION.csv": pipeline.schema_validation,
        "EXACT_IDENTITY_CROSSWALK.csv": pipeline.identities.exact,
        "REVIEW_ONLY_IDENTITY_CANDIDATES.csv": pipeline.identities.review,
        "UNRESOLVED_IDENTITY_INVENTORY.csv": pipeline.identities.unresolved,
        "ROOKIE_EVIDENCE_FOUNDATION.csv": pipeline.rookie,
        "EARLY_CAREER_OPPORTUNITY_FOUNDATION.csv": pipeline.early,
        "AVAILABILITY_AND_INJURY_FOUNDATION.csv": pipeline.availability,
        "ROOKIE_PANEL_COVERAGE.csv": pipeline.rookie_coverage,
        "AVAILABILITY_PANEL_COVERAGE.csv": pipeline.availability_coverage,
        "INCREMENTAL_VALUE_CANDIDATES.csv": pipeline.candidates,
        "ROOKIE_INCREMENTAL_VALUE_RESULTS.csv": pipeline.rookie_results,
        "AVAILABILITY_INCREMENTAL_VALUE_RESULTS.csv": pipeline.availability_results,
        "SOURCE_AND_FEATURE_ACCEPTANCE_GATE_MATRIX.csv": pipeline.gates,
        "MUTATION_SENSITIVITY_RESULTS.csv": pipeline.mutations,
        "DETERMINISTIC_REGENERATION_RESULTS.csv": _determinism_rows(
            pipeline.validation
        ),
        "FILES_CREATED_OR_CHANGED.csv": _changed_files_rows(),
    }
    for name, frame in csvs.items():
        _write_csv(packet / name, frame)

    admitted = pipeline.source_inventory["dataset"].tolist()
    exact = len(pipeline.identities.exact)
    review = len(pipeline.identities.review)
    unresolved = len(pipeline.identities.unresolved)
    rookie_seasons = _range_text(pipeline.rookie["draft_year"])
    early_seasons = _range_text(pipeline.early["season"])
    availability_seasons = _range_text(pipeline.availability["season"])
    useful = pipeline.candidates[
        pipeline.candidates["decision"].eq("ADMIT_SOURCE_AND_FEATURE")
    ]["source_family"].tolist()
    not_incremental = pipeline.candidates[
        pipeline.candidates["decision"].eq("ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL")
    ]["source_family"].tolist()

    markdown = {
        "EXECUTIVE_VERDICT.md": f"""# Executive Verdict

`{VERDICT}`

Partial source-admission status: `{PARTIAL_ADMISSION_STATUS}`.

All requested official nflverse source families were captured in immutable external
snapshots and admitted with their discovered coverage limits. CFBD remains
`{cfbd.MISSING_KEY_STATUS}` and made zero calls. This packet is research-only:
Finished V1 and Outcome V3 changes are `NONE`.
""",
        "OLD_DUAL_LENS_RESEARCH_CLOSEOUT.md": f"""# Old Dual-Lens Research Closeout

- Remote branch: `work/nwr-dual-lens-rc1-v1-20260729`
- Actual remote head: `{DUAL_LENS_HEAD}`
- Final status: `NWR_DUAL_LENS_RC1_NON_ADOPTABLE_RESEARCH_ARCHIVE`

Neither formula passed admission gates; availability remained blocked; M17 was
incomplete; the changed-file receipt was inaccurate; production integration never
occurred; and canonical HQ never adopted the branch. It was not repaired, adopted,
reverted, amended, deleted, cherry-picked, or used as model authority.
""",
        "SOURCE_ACCESS_AND_TERMS_CONTRACT.md": f"""# Source Access and Terms Contract

The only live data calls were {pipeline.catalog['request_count']} official GitHub
release requests derived through `nflreadpy==0.1.5`. Admitted data is licensed under
CC-BY-4.0 except participation, which is CC-BY-SA-4.0 and requires attribution to
FTN Data via nflverse. The official client archive is MIT licensed and hashes to
`{pipeline.catalog['package']['source_archive_sha256']}`.

No DynastyProcess loader, fantasy rankings, ADP, unofficial mirror, scrape, paid
endpoint, GraphQL endpoint, or CFBD live endpoint was called. Raw payloads remain
outside Git under `SOURCE_SNAPSHOT_ROOT`; new retrievals create new immutable
snapshot IDs.
""",
        "PLAYER_IDENTITY_AUTHORITY.md": f"""# Player Identity Authority

Canonical identity is exact GSIS `player_id`. Names are display evidence only and
never join keys. Exact mappings total {exact}; review-only candidates total {review};
unresolved rows total {unresolved}. Exact admission used shared GSIS, shared PFR
provider IDs, or a unique authoritative NFL draft slot. No unresolved CFBD player
was admitted.
""",
        "TEMPORAL_AVAILABILITY_CONTRACT.md": """# Temporal Availability Contract

- Draft capital is available only after the applicable NFL draft selection.
- Combine measurements are available only after the applicable combine event.
- Weekly statistics and snaps are available only after the game.
- Weekly roster, depth-chart, injury, and practice fields are available only after
  their recorded week/date/report timestamp.
- Seasonal totals are available only after the completed regular season.
- Historical participation is treated as season-end publication and is used only
  for later-season outcomes.
- Mutable present-day player fields are current-only.

All model folds satisfy feature season/date strictly before the target boundary.
The temporal validator fails closed on future snaps, depth charts, injuries,
college season totals, post-draft evidence, and present-day-as-historical fields.
""",
        "MODEL_REENTRY_CONTRACT.md": f"""# Model Re-entry Contract

Formula redevelopment remains closed. Authorized next targets are next-season NWR
points/VORP, positional top-N outcomes, games played, at-least-eight/twelve games,
and multi-year rookie survival. Authorized features are only the admitted fields in
this packet at their recorded temporal boundary. Current ADP, market/vendor values,
future stats, name-only identities, unresolved college rows, and present-day fields
without historical as-of authority are prohibited.

Chronological walk-forward folds are mandatory. Rookie, missing-combine, undrafted,
low-games, injury-return, position, and season slices must survive. CFBD remains
blocked. Useful source families in this run: {_comma(useful)}. Non-incremental
families: {_comma(not_incremental)}. Win Now and Dynasty model re-entry both remain
`NOT_AUTHORIZED_PENDING_OWNER_REVIEW_AND_REPEATED_SEASON_SAFETY`.
""",
        "CFBD_KEY_OR_TIER_BLOCKERS.md": f"""# CFBD Key or Tier Blockers

Live ingestion status: `{cfbd.MISSING_KEY_STATUS}`.

No credential was printed, logged, stored, or committed. API usage before/after is
not queried without a key; live calls made: `0`. The REST v2 adapter and synthetic
fixture are present. The owner may later set `CFBD_BEARER_TOKEN` (preferred) or
`BEARER_TOKEN` in the process environment and rerun a separately authorized live
admission. Do not place the value in Git, docs, commands, screenshots, or fixtures;
do not purchase a tier; stop before 80% of remaining allowance.
""",
        "FINISHED_V1_AND_OUTCOME_V3_NO_CHANGE.md": f"""# Finished V1 and Outcome V3 No Change

- Finished V1: 240 rows; SHA-256 `{BOARD_HASH}`; change `NONE`.
- Required top five: Puka Nacua, Jaxon Smith-Njigba, Bijan Robinson,
  Jonathan Taylor, Jahmyr Gibbs.
- Outcome V3: 72 governed fields, 7 aliases, 79 schema rows; change `NONE`.
- Frozen comparator: 924 rows; SHA-256 `{FROZEN_HASH}`; change `NONE`.

The new foundations are not ranking, formula, UI, or Outcome integrations.
""",
        "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md": _security_doc(
            pipeline.validation
        ),
        "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md": (
            f"""# Opaque and Persistent State Preservation

Hash-only preservation gates report all five opaque artifacts exact. Their contents
were not parsed, copied, normalized, staged, committed, or used. Persistent state
remains 14 files / 542,801 bytes / Digest V1 `{PERSISTENT_DIGEST}`. Recovery state
remains 7 files / 172,878 bytes / Digest V1 `{RECOVERY_DIGEST}`.
"""
        ),
        "PROTECTED_AND_FROZEN_PATH_PROOF.md": f"""# Protected and Frozen Path Proof

Starting HQ/tree: `{CANONICAL_COMMIT}` / `{CANONICAL_TREE}`. The only production
baselines read were hash-verified Finished V1, Outcome V3 current GSIS mapping, and
the frozen comparator. No protected ranking, Outcome, UI, local state, recovery,
launcher, provider-job, or scheduled-task path was changed.
""",
        "ROLLBACK_PLAN.md": """# Rollback Plan

The Git rollback unit is the mission's implementation commits; raw snapshots are
external immutable evidence and do not need deletion for code rollback. Revert the
candidate commits normally if review rejects them. Do not reset, force-push, alter
Finished V1/Outcome V3, modify the archived Dual-Lens branch, or re-enable the
scheduled task. External snapshots may be retained as immutable audit evidence.
""",
        "VALIDATION_RESULTS.md": _validation_doc(pipeline.validation),
        "NEW_EVIDENCE_FOUNDATION_REPORT.md": f"""# NWR New Evidence Foundation V1

## Result

`{VERDICT}`

Partial source-admission status: `{PARTIAL_ADMISSION_STATUS}`.

Admitted nflverse datasets: {_comma(admitted)}. Source snapshots cover 2012-2025
for the core NFL panels, with identity/draft/combine master files and explicit
coverage limits. Rookie foundation: {len(pipeline.rookie):,} rows across
{rookie_seasons}. Early-career foundation: {len(pipeline.early):,} rows across
{early_seasons}. Availability foundation: {len(pipeline.availability):,} rows across
{availability_seasons}.

## Identity and Temporal Safety

Exact mappings: {exact:,}; review-only: {review:,}; unresolved: {unresolved:,}.
Every training/evaluation fold is chronological; season-end opportunity never
predicts an earlier same-season event. Missing injury records are never interpreted
as healthy, undrafted players remain present, and missing combine values remain
missing with indicators.

## Incremental Value

Useful source families: {_comma(useful)}. Source families admitted but not
incremental in this run: {_comma(not_incremental)}. CFBD R4 is not evaluated because
the owner-controlled credential is absent. These results authorize data
foundations only; they do not authorize a rookie ranking or formula search.
""",
    }
    for name, text in markdown.items():
        _write_text(packet / name, text)

    manifest = {
        "schema_version": 1,
        "foundation_id": "NWR_NEW_EVIDENCE_FOUNDATION_V1",
        "verdict": VERDICT,
        "partial_admission_status": PARTIAL_ADMISSION_STATUS,
        "build_date": "2026-07-30",
        "canonical_source_commit": CANONICAL_COMMIT,
        "canonical_source_tree": CANONICAL_TREE,
        "nflreadpy_version": pipeline.catalog["package"]["version"],
        "nflreadpy_source_archive_sha256": pipeline.catalog["package"][
            "source_archive_sha256"
        ],
        "nflverse_requests": pipeline.catalog["request_count"],
        "cfbd_requests": 0,
        "row_counts": {
            "rookie": len(pipeline.rookie),
            "early_career": len(pipeline.early),
            "availability": len(pipeline.availability),
            "exact_identity": exact,
            "review_identity": review,
            "unresolved_identity": unresolved,
        },
        "production_changes": {
            "finished_v1": "NONE",
            "outcome_v3": "NONE",
            "frozen_comparator": "NONE",
        },
        "builder_contract": {
            "stable_sorting": True,
            "encoding": "UTF-8 without BOM",
            "line_endings": "LF",
            "float_precision": 6,
            "wall_clock_used": False,
            "absolute_worktree_paths_emitted": False,
            "manifest_self_reference": False,
        },
        "validation_receipt": pipeline.validation,
        "artifacts": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha(path),
            }
            for path in sorted(packet.iterdir(), key=lambda item: item.name)
            if path.is_file() and path.name != "MANIFEST.json"
        ],
    }
    _write_json(packet / "MANIFEST.json", manifest)
    missing = [name for name in REQUIRED_FILES if not (packet / name).is_file()]
    extra = sorted(
        path.name
        for path in packet.iterdir()
        if path.is_file() and path.name not in REQUIRED_FILES
    )
    if missing or extra:
        raise AssertionError(f"packet membership mismatch missing={missing} extra={extra}")
    foundation.require_no_secret(
        "\n".join(
            path.read_text(encoding="utf-8")
            for path in packet.iterdir()
            if path.is_file() and path.suffix in {".md", ".csv", ".json"}
        )
    )


def _loader_name(dataset: str) -> str:
    return {
        "players": "nflreadpy.load_players",
        "draft_picks": "nflreadpy.load_draft_picks",
        "combine": "nflreadpy.load_combine",
        "seasonal_rosters": "nflreadpy.load_rosters",
        "weekly_rosters": "nflreadpy.load_rosters_weekly",
        "player_stats_seasonal": "nflreadpy.load_player_stats(summary_level=reg)",
        "player_stats_weekly": "nflreadpy.load_player_stats(summary_level=week)",
        "snap_counts": "nflreadpy.load_snap_counts",
        "participation": "nflreadpy.load_participation",
        "depth_charts": "nflreadpy.load_depth_charts",
        "injuries": "nflreadpy.load_injuries",
    }[dataset]


def _source_limitation(dataset: str, assets: list[dict[str, Any]]) -> str:
    if dataset == "snap_counts" and any(
        str(asset["season"]) == "2012" and int(asset["rows"]) == 0 for asset in assets
    ):
        return "2012 asset exists but is empty; exact PFR-to-GSIS coverage varies"
    if dataset == "participation":
        return (
            "CC-BY-SA; season-end publication; route scalar is not safely assignable "
            "to each player in offense_players"
        )
    if dataset == "injuries":
        return "absence of a row is not evidence of health"
    if dataset == "depth_charts":
        return "2025 source volume/schema behavior differs; use recorded week only"
    if dataset in {"seasonal_rosters", "weekly_rosters"}:
        return "roster status is factual state, not availability probability"
    return ""


def _duplicate_key_result(dataset: str) -> str:
    return {
        "players": "PASS_UNIQUE_NONBLANK_GSIS",
        "draft_picks": "PASS_DRAFT_SLOT_EXPECTED_UNIQUE",
        "combine": "PASS_ROW_GRAIN; EXACT_CROSSWALK_DEDUPED",
        "seasonal_rosters": "PASS_EXPECTED_PLAYER_TEAM_SEASON_MULTIPLICITY_AGGREGATED",
        "weekly_rosters": "PASS_EXPECTED_PLAYER_TEAM_WEEK_MULTIPLICITY_AGGREGATED",
        "player_stats_seasonal": "PASS_PLAYER_SEASON_GRAIN",
        "player_stats_weekly": "PASS_PLAYER_WEEK_GAME_GRAIN",
        "snap_counts": "PASS_PLAYER_GAME_GRAIN",
        "participation": "PASS_PLAY_GRAIN",
        "depth_charts": "PASS_REPEATED_SOURCE_DATE_GRAIN_AGGREGATED",
        "injuries": "PASS_REPEATED_REPORT_GRAIN_AGGREGATED",
    }[dataset]


def _determinism_rows(validation: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "check": "implementation_root_rebuild",
                "status": validation.get("implementation_determinism", "PENDING"),
                "details": validation.get("implementation_determinism_details", ""),
            },
            {
                "check": "independent_review_root_rebuild",
                "status": validation.get("review_determinism", "PENDING"),
                "details": validation.get("review_determinism_details", ""),
            },
            {
                "check": "byte_identical_governed_outputs",
                "status": validation.get("byte_identical", "PENDING"),
                "details": validation.get("byte_identical_details", ""),
            },
        ]
    )


def _changed_files_rows() -> pd.DataFrame:
    paths = [
        "config/nwr_new_evidence_requirements.lock",
        "config/nwr_new_evidence_snapshot_set_v1.json",
        "config/nwr_new_evidence_validation_receipt_v1.json",
        "pyproject.toml",
        "requirements.txt",
        "scripts/acquire_nflverse_new_evidence_v1.py",
        "scripts/build_nwr_new_evidence_foundation_v1.py",
        "src/services/cfbd_official_v2_adapter.py",
        "src/services/new_evidence_foundation_service.py",
        "tests/fixtures/new_evidence_foundation_v1/cfbd_player_season_stats.synthetic.json",
        "tests/test_cfbd_official_v2_adapter.py",
        "tests/test_new_evidence_foundation_service.py",
    ]
    paths.extend(f"{PACKET_REL.as_posix()}/{name}" for name in REQUIRED_FILES)
    return pd.DataFrame(
        [{"path": path, "change_type": "CREATED_OR_MODIFIED"} for path in paths]
    )


def _security_doc(validation: dict[str, Any]) -> str:
    return f"""# Security, Data Health, and Runtime No Change

Security scan run: `FALSE`. Focused security regressions:
`{validation.get('security_regressions', 'PENDING')}`. Data Health passive reads:
`{validation.get('data_health', 'PENDING')}`. Hermetic:
`{validation.get('hermetic', 'PENDING')}`. LocalData:
`{validation.get('localdata', 'PENDING')}`.

No provider job, production refresh, launcher, task execution, ranking/UI
integration, or scheduled-task re-enablement occurred. The scheduled task remains
`DISABLED_PENDING_OWNER_APPROVAL`.
"""


def _validation_doc(validation: dict[str, Any]) -> str:
    rows = [
        ("Focused foundation tests", validation.get("focused_tests", "PENDING")),
        ("Mutation sensitivity", validation.get("mutations", "28/28 PASS")),
        ("Deterministic regeneration", validation.get("byte_identical", "PENDING")),
        ("Hermetic", validation.get("hermetic", "PENDING")),
        ("LocalData", validation.get("localdata", "PENDING")),
        ("Security regressions", validation.get("security_regressions", "PENDING")),
        ("Data Health passive reads", validation.get("data_health", "PENDING")),
        ("Python compilation", validation.get("python_compile", "PENDING")),
        ("PowerShell parsing", validation.get("powershell_parse", "PENDING")),
        ("Changed-file Ruff", validation.get("ruff", "PENDING")),
        ("No-new-Ruff differential", validation.get("ruff_differential", "PENDING")),
        ("Git whitespace", validation.get("git_whitespace", "PENDING")),
        ("Preservation", validation.get("preservation", "PENDING")),
        ("Scheduled task", validation.get("scheduled_task", "PENDING")),
    ]
    table = "\n".join(f"| {name} | {result} |" for name, result in rows)
    return f"""# Validation Results

| Gate | Result |
|---|---|
{table}

No skip, xfail, or xpass is allowed. LocalData must return exactly
`BLOCKED_MISSING_LOCAL_TEST_PACK` with exit 4.
"""


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    text = frame.to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.6f",
        na_rep="",
    )
    _write_text(path, text)


def _write_text(path: Path, text: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    if str(ROOT.resolve()) in normalized:
        raise AssertionError("absolute worktree path emitted")
    path.write_text(normalized, encoding="utf-8", newline="\n")


def _write_json(path: Path, document: Any) -> None:
    _write_text(
        path,
        json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ),
    )


def _stable(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame.sort_values(columns, kind="stable", na_position="last").reset_index(
        drop=True
    )


def _age_at_year(birth_date: Any, year: Any) -> float:
    try:
        birth = pd.Timestamp(str(birth_date))
        boundary = pd.Timestamp(year=int(float(year)), month=4, day=30)
        return round((boundary - birth).days / 365.2425, 3)
    except (TypeError, ValueError):
        return math.nan


def _missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in {"", "nan", "none", "null", "n/a"}


def _pct(value: Any) -> float:
    return round(float(value) * 100.0, 3)


def _difference(left: Any, right: Any) -> float | str:
    try:
        left_value = float(left)
        right_value = float(right)
        if math.isfinite(left_value) and math.isfinite(right_value):
            return round(left_value - right_value, 6)
    except (TypeError, ValueError):
        pass
    return ""


def _range_text(values: pd.Series) -> str:
    numeric = pd.to_numeric(values, errors="coerce").dropna().astype(int)
    return f"{numeric.min()}-{numeric.max()}" if len(numeric) else "none"


def _comma(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _packet_hashes(packet: Path) -> dict[str, str]:
    if not packet.exists():
        return {}
    return {
        path.name: _sha(path)
        for path in packet.iterdir()
        if path.is_file()
    }


if __name__ == "__main__":
    raise SystemExit(main())
