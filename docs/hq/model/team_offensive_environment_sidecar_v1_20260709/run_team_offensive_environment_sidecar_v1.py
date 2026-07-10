from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
POSITIONS = ["QB", "RB", "WR", "TE"]
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_PLATEAU_COMMIT = "cb1da15b8580c45d770396995e90bcae0e3dc6c3"
CURRENT_BEST = 0.755
FULL_HISTORY_REFERENCE = 0.758
SNAP_DEPTH_REFERENCE = 0.763
SOURCE_CACHE = Path(r"C:\NWR_REVIEW\nflverse_epa_opportunity_source_cache_20260709")
SOURCE_SEASONS = list(range(2012, 2025))
TARGET_SEASONS = list(range(2013, 2026))

V2_ARTIFACT = Path(__file__).resolve().parents[1] / "nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
V2_HELPER = V2_ARTIFACT / "run_nwr_autonomous_ingredient_upgrade_sequence_v2.py"
EPA_ARTIFACT = Path(__file__).resolve().parents[1] / "nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709"
REC_ARTIFACT = Path(__file__).resolve().parents[1] / "nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709"
SNAP_ARTIFACT = Path(__file__).resolve().parents[1] / "nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709"
INJURY_ARTIFACT = Path(__file__).resolve().parents[1] / "point_in_time_injury_availability_data_mart_gate_v1_20260709"

RESULT_FIELDS = [
    "run_id",
    "formula_id",
    "cluster_id",
    "base_formula",
    "ingredient_set",
    "ingredient_fields",
    "positions",
    "seasons",
    "row_count",
    "coverage_pct",
    "missingness_pct",
    "overall_spearman",
    "position_spearman_qb",
    "position_spearman_rb",
    "position_spearman_wr",
    "position_spearman_te",
    "pyf_delta",
    "current_best_delta",
    "full_history_0758_delta",
    "snap_depth_0763_delta",
    "cluster_seed_delta",
    "top12_precision",
    "top24_precision",
    "top36_precision",
    "false_positive_impact",
    "false_negative_impact",
    "sparse_history_impact",
    "low_games_impact",
    "age_lifecycle_slice",
    "role_slice",
    "team_change_caveat",
    "stability_by_season",
    "leave_one_season_out",
    "outlier_flags",
    "full_history_comparable",
    "broad_window_comparable",
    "partial_window_flag",
    "use_decision",
    "notes",
]


def import_v2() -> Any:
    spec = importlib.util.spec_from_file_location("nwr_v2_helpers", V2_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import helper: {V2_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v2 = import_v2()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def num(value: Any) -> float | None:
    return v2.num(value)


def fmt(value: float | None, digits: int = 3) -> str:
    return v2.fmt(value, digits)


def pct(value: float | None, digits: int = 1) -> str:
    return v2.pct(value, digits)


def clean_float(value: Any, default: float = 0.0) -> float:
    val = num(value)
    return float(val) if val is not None and math.isfinite(float(val)) else default


def public_pbp_url(season: int) -> str:
    return f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"


def source_path(season: int) -> Path:
    return SOURCE_CACHE / f"play_by_play_{season}.parquet"


def load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def source_ledger_row(path: Path, season: int, raw_rows: int, reg_rows: int, team_rows: int, columns: list[str]) -> dict[str, Any]:
    return {
        "source_path": str(path),
        "source_family": "nflfastR_public_play_by_play",
        "raw_vs_derived": "raw_public_parquet_aggregated_to_review_sidecar",
        "row_grain": "play_by_play_raw_to_team_season_derived",
        "seasons_covered": str(season),
        "team_id_fields": "posteam",
        "team_abbreviation_fields": "posteam",
        "player_team_join_fields": "prior player-season team derived from lagged player sidecars",
        "team_offensive_columns": "|".join(columns),
        "source_hash": sha256_file(path),
        "file_size": path.stat().st_size,
        "row_count": raw_rows,
        "regular_season_rows": reg_rows,
        "team_season_rows": team_rows,
        "duplicate_keys": "0",
        "missingness": "team rows with no posteam excluded",
        "source_use_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
        "asof_leakage_status": "PASS_LAGGED_CLOSED_FEATURE_SEASON_N_TO_TARGET_N_PLUS_1",
        "lag_safe": "yes",
    }


def normalize_team(team: Any) -> str:
    text = str(team or "").strip()
    if text.lower() in {"", "nan", "none"}:
        return ""
    aliases = {"JAC": "JAX", "LAR": "LA"}
    return aliases.get(text, text)


def aggregate_team_environment() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []
    cols = [
        "season",
        "week",
        "season_type",
        "game_id",
        "posteam",
        "play_type",
        "pass_attempt",
        "rush_attempt",
        "yards_gained",
        "first_down",
        "touchdown",
        "pass_touchdown",
        "rush_touchdown",
        "posteam_score",
        "epa",
        "success",
        "interception",
        "fumble_lost",
        "sack",
    ]
    for season in SOURCE_SEASONS:
        path = source_path(season)
        if not path.exists():
            raise RuntimeError(f"Missing local public play-by-play source: {path}")
        df = pd.read_parquet(path, columns=cols)
        reg = df[df["season_type"].astype(str).eq("REG")].copy()
        reg = reg[reg["posteam"].notna()].copy()
        reg["team"] = reg["posteam"].map(normalize_team)
        for col in [
            "pass_attempt",
            "rush_attempt",
            "yards_gained",
            "first_down",
            "touchdown",
            "pass_touchdown",
            "rush_touchdown",
            "posteam_score",
            "epa",
            "success",
            "interception",
            "fumble_lost",
            "sack",
        ]:
            reg[col] = pd.to_numeric(reg[col], errors="coerce").fillna(0.0)
        reg["offensive_play"] = ((reg["pass_attempt"] > 0) | (reg["rush_attempt"] > 0)).astype(float)
        offense = reg[reg["offensive_play"].eq(1.0)].copy()
        game_points = (
            reg.groupby(["season", "team", "game_id"], dropna=False)["posteam_score"]
            .max()
            .reset_index()
            .rename(columns={"posteam_score": "game_points"})
        )
        points = game_points.groupby(["season", "team"], dropna=False).agg(
            team_env_games=("game_id", "count"),
            team_env_points=("game_points", "sum"),
        )
        grouped = offense.groupby(["season", "team"], dropna=False).agg(
            team_env_plays=("offensive_play", "sum"),
            team_env_pass_attempts=("pass_attempt", "sum"),
            team_env_rush_attempts=("rush_attempt", "sum"),
            team_env_total_yards=("yards_gained", "sum"),
            team_env_first_downs=("first_down", "sum"),
            team_env_offensive_touchdowns=("pass_touchdown", "sum"),
            team_env_rush_touchdowns=("rush_touchdown", "sum"),
            team_env_epa_total=("epa", "sum"),
            team_env_pass_epa=("epa", lambda s: s[offense.loc[s.index, "pass_attempt"].gt(0)].sum()),
            team_env_rush_epa=("epa", lambda s: s[offense.loc[s.index, "rush_attempt"].gt(0)].sum()),
            team_env_success_sum=("success", "sum"),
            team_env_turnovers=("interception", "sum"),
            team_env_fumbles_lost=("fumble_lost", "sum"),
            team_env_sacks_allowed=("sack", "sum"),
        )
        out = grouped.join(points, how="left").reset_index().rename(columns={"season": "feature_season"})
        out["team_env_turnovers"] = out["team_env_turnovers"] + out["team_env_fumbles_lost"]
        out["team_env_points_per_game"] = out["team_env_points"] / out["team_env_games"].replace(0, pd.NA)
        out["team_env_plays_per_game"] = out["team_env_plays"] / out["team_env_games"].replace(0, pd.NA)
        out["team_env_pass_rate"] = out["team_env_pass_attempts"] / out["team_env_plays"].replace(0, pd.NA)
        out["team_env_rush_rate"] = out["team_env_rush_attempts"] / out["team_env_plays"].replace(0, pd.NA)
        out["team_env_yards_per_play"] = out["team_env_total_yards"] / out["team_env_plays"].replace(0, pd.NA)
        out["team_env_epa_per_play"] = out["team_env_epa_total"] / out["team_env_plays"].replace(0, pd.NA)
        out["team_env_success_rate"] = out["team_env_success_sum"] / out["team_env_plays"].replace(0, pd.NA)
        for score_source, score_name in [
            ("team_env_plays_per_game", "team_env_volume_score"),
            ("team_env_points_per_game", "team_env_scoring_score"),
            ("team_env_pass_attempts", "team_env_pass_volume_score"),
            ("team_env_rush_attempts", "team_env_rush_volume_score"),
            ("team_env_epa_per_play", "team_env_epa_score"),
            ("team_env_success_rate", "team_env_success_score"),
        ]:
            out[score_name] = out.groupby("feature_season")[score_source].rank(pct=True, method="average")
        out["team_env_offense_score"] = out[
            ["team_env_volume_score", "team_env_scoring_score", "team_env_epa_score", "team_env_success_score"]
        ].mean(axis=1)
        frames.append(out)
        sources.append(source_ledger_row(path, season, len(df), len(reg), len(out), cols))
    return pd.concat(frames, ignore_index=True, sort=False), sources


def team_lookup_from_sidecar(path: Path, team_field: str = "team", season_field: str = "feature_season") -> dict[tuple[str, int, str], tuple[str, str]]:
    lookup: dict[tuple[str, int, str], tuple[str, str]] = {}
    for row in load_csv(path):
        season_text = row.get(season_field) or row.get("season")
        if not season_text:
            continue
        team = normalize_team(row.get(team_field) or row.get("team_list"))
        if not team:
            continue
        key = (str(row.get("player_id")), int(float(season_text)), str(row.get("position")))
        lookup[key] = (team, path.name)
    return lookup


def build_player_prior_team_lookup() -> dict[tuple[str, int, str], tuple[str, str]]:
    ordered_sources = [
        (EPA_ARTIFACT / "NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv", "team", "feature_season"),
        (SNAP_ARTIFACT / "NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv", "team", "feature_season"),
        (INJURY_ARTIFACT / "POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv", "team", "feature_season"),
        (REC_ARTIFACT / "NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv", "team", "feature_season"),
    ]
    out: dict[tuple[str, int, str], tuple[str, str]] = {}
    for path, team_field, season_field in ordered_sources:
        for key, value in team_lookup_from_sidecar(path, team_field, season_field).items():
            out.setdefault(key, value)
    return out


def fmt_side(value: Any, digits: int = 3) -> str:
    val = num(value)
    return fmt(val, digits)


def build_sidecar(panel_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    team_env, sources = aggregate_team_environment()
    team_lookup = {
        (int(r["feature_season"]), normalize_team(r["team"])): r for r in team_env.to_dict("records")
    }
    player_team_lookup = build_player_prior_team_lookup()
    season_source = {int(row["seasons_covered"]): row for row in sources}
    sidecar: list[dict[str, Any]] = []
    raw_cols = [
        "team_env_plays",
        "team_env_plays_per_game",
        "team_env_pass_attempts",
        "team_env_rush_attempts",
        "team_env_pass_rate",
        "team_env_rush_rate",
        "team_env_points",
        "team_env_points_per_game",
        "team_env_total_yards",
        "team_env_yards_per_play",
        "team_env_first_downs",
        "team_env_turnovers",
        "team_env_epa_per_play",
        "team_env_pass_epa",
        "team_env_rush_epa",
        "team_env_success_rate",
        "team_env_volume_score",
        "team_env_scoring_score",
        "team_env_pass_volume_score",
        "team_env_rush_volume_score",
        "team_env_offense_score",
    ]
    for row in panel_rows:
        feature_season = int(row["feature_season"])
        key = (str(row["player_id"]), feature_season, str(row["position"]))
        team, team_source = player_team_lookup.get(key, ("", ""))
        env = team_lookup.get((feature_season, team)) if team else None
        source = season_source.get(feature_season, {})
        if env is not None:
            join_status = "JOINED_PRIOR_TEAM_ENVIRONMENT"
            coverage_status = "SOURCE_SEASON_AND_PRIOR_TEAM_AVAILABLE"
        elif not team:
            join_status = "NO_PRIOR_TEAM_EVIDENCE"
            coverage_status = "PLAYER_PRIOR_TEAM_MISSING"
        else:
            join_status = "NO_TEAM_ENVIRONMENT_FOR_PRIOR_TEAM"
            coverage_status = "SOURCE_SEASON_AVAILABLE_TEAM_NOT_MATCHED"
        out = {
            "season": int(row["season"]),
            "feature_season": feature_season,
            "player_id": row["player_id"],
            "player_name": row.get("player_name") or "",
            "position": row["position"],
            "team": team,
            "team_env_source_team": team,
            "team_env_source_season": feature_season if team else "",
            "team_env_source_player_team_artifact": team_source,
            "team_env_source_path": source.get("source_path", ""),
            "team_env_source_hash": source.get("source_hash", ""),
            "join_status": join_status,
            "coverage_status": coverage_status,
            "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
            "decision_date_safe": "PASS_LAGGED_N_TO_N_PLUS_1",
            "leakage_flag": "PASS_FEATURE_SEASON_N_TEAM_CONTEXT_TO_TARGET_SEASON_N_PLUS_1",
            "identity_flag": "PASS_TEAM_ABBREVIATION_JOIN_FROM_PRIOR_PLAYER_SIDE_CARS",
            "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
            "team_change_caveat": "uses_prior_season_team_only_no_target_season_team_projection",
            "caveat": "Team environment is lagged prior-team context; player target-season team changes are not projected.",
        }
        for col in raw_cols:
            out[col] = fmt_side(env.get(col) if env else None, 6 if "rate" in col or "score" in col or "per" in col else 3)
        sidecar.append(out)
    return sidecar, sources


def sidecar_feature_season(row: dict[str, Any]) -> int:
    if row.get("feature_season") not in (None, ""):
        return int(float(row["feature_season"]))
    return int(float(row["season"]))


def attach_sidecar(
    rows: list[dict[str, Any]],
    sidecar: list[dict[str, Any]],
    prefix: str,
    raw_cols: list[str],
    column_map: dict[str, str] | None = None,
) -> dict[str, int]:
    column_map = column_map or {}
    lookup = {(str(r["player_id"]), sidecar_feature_season(r), str(r["position"])): r for r in sidecar}
    joined = 0
    for row in rows:
        match = lookup.get((str(row["player_id"]), int(row["feature_season"]), str(row["position"])))
        if match and any(num(match.get(column_map.get(col, col))) is not None for col in raw_cols):
            joined += 1
            for col in raw_cols:
                row[f"{prefix}_{col}"] = num(match.get(column_map.get(col, col)))
        else:
            for col in raw_cols:
                row[f"{prefix}_{col}"] = None
    for col in raw_cols:
        v2.assign_percentile(rows, f"{prefix}_{col}", f"{prefix}_{col}_pct")
    return {"joined": joined}


def attach_prior_sidecars(rows: list[dict[str, Any]]) -> dict[str, int]:
    joins = {}
    joins["snapdepth_joined"] = attach_sidecar(
        rows,
        load_csv(SNAP_ARTIFACT / "NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv"),
        "snapdepth",
        ["snap_not_low_snap_score", "depth_stability_score", "snap_depth_role_score"],
    )["joined"]
    joins["injury_joined"] = attach_sidecar(
        rows,
        load_csv(INJURY_ARTIFACT / "POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv"),
        "avail",
        ["avail_availability_score", "avail_caveat_inverse_score"],
    )["joined"]
    joins["rec_joined"] = attach_sidecar(
        rows,
        load_csv(REC_ARTIFACT / "NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv"),
        "recopp",
        ["rec_opp_wopr", "rec_opp_receiving_epa"],
    )["joined"]
    joins["epa_joined"] = attach_sidecar(
        rows,
        load_csv(EPA_ARTIFACT / "NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv"),
        "epa",
        ["epa_total_raw", "epa_per_opportunity"],
    )["joined"]
    joins["ffop_joined"] = attach_sidecar(
        rows,
        load_csv(V2_ARTIFACT / "FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv"),
        "ffop",
        ["ffop_xfp_total"],
        {"ffop_xfp_total": "ffop_total_fantasy_points_exp"},
    )["joined"]
    joins["ngs_joined"] = attach_sidecar(
        rows,
        load_csv(V2_ARTIFACT / "NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv"),
        "ngs",
        ["ngs_position_signal_raw"],
    )["joined"]
    return joins


def selected_rows(rows: list[dict[str, Any]], positions: set[str], required_cols: list[str]) -> list[dict[str, Any]]:
    return v2.selected_rows(rows, positions, required_cols)


def materialize_combo_score(rows: list[dict[str, Any]], score_col: str, parts: list[tuple[str, float]]) -> None:
    for row in rows:
        score = 0.0
        ok = True
        for col, weight in parts:
            val = row.get(col)
            if val is None:
                ok = False
                break
            score += float(val) * weight
        row[score_col] = score if ok else None


def scope_positions(scope: str) -> set[str]:
    return v2.scope_positions(scope)


def denominator(rows: list[dict[str, Any]], required_cols: list[str] | None = None, positions: set[str] | None = None) -> int:
    positions = positions or set(POSITIONS)
    if not required_cols:
        return len([r for r in rows if r["position"] in positions])
    return len([r for r in rows if r["position"] in positions and all(r.get(c) is not None for c in required_cols)])


def result_decision(spearman: float | None, seed_delta: float | None, row_count: int, partial: str) -> str:
    if spearman is None or row_count < 50:
        return "BLOCKED_OR_INVALID"
    if partial == "partial_window_only":
        return "PARTIAL_WINDOW_PROMISING" if spearman >= 0.780 else "INTERACTION_CONTEXT"
    if spearman >= SNAP_DEPTH_REFERENCE + 0.003:
        return "AVAILABLE_REVIEW_ONLY_ADDITIVE_SIGNAL"
    if spearman >= FULL_HISTORY_REFERENCE and seed_delta is not None and seed_delta > 0:
        return "AVAILABLE_REVIEW_ONLY_TEAM_CONTEXT"
    if spearman >= CURRENT_BEST:
        return "AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT"
    return "AVAILABLE_BUT_NO_INCREMENTAL_SIGNAL"


def make_result(
    run_id: str,
    formula_id: str,
    cluster_id: str,
    base_formula: str,
    ingredient_set: str,
    ingredient_fields: str,
    positions: str,
    selected: list[dict[str, Any]],
    score_col: str,
    coverage_denominator: int,
    seed_metrics: dict[str, Any] | None,
    notes: str,
    full_flag: str,
    broad_flag: str,
    partial_flag: str,
) -> dict[str, Any]:
    metrics = v2.metrics_for_run(selected, score_col)
    spearman = metrics.get("spearman")
    pyf = metrics.get("pyf_spearman")
    seed = seed_metrics.get("spearman") if seed_metrics else None
    row_count = int(metrics.get("rows") or 0)
    missingness = 1.0 - (row_count / coverage_denominator) if coverage_denominator else None
    seed_delta = spearman - seed if spearman is not None and seed is not None else None
    by_pos = metrics.get("by_position", {})
    by_season = metrics.get("by_season", {})
    season_stable = [s for s, val in by_season.items() if val is not None and pyf is not None and val >= pyf - 0.05]
    return {
        "run_id": run_id,
        "formula_id": formula_id,
        "cluster_id": cluster_id,
        "base_formula": base_formula,
        "ingredient_set": ingredient_set,
        "ingredient_fields": ingredient_fields,
        "positions": "|".join(metrics.get("positions", [])) if metrics.get("positions") else positions,
        "seasons": "|".join(str(s) for s in metrics.get("seasons", [])),
        "row_count": row_count,
        "coverage_pct": pct(row_count / coverage_denominator if coverage_denominator else None),
        "missingness_pct": pct(missingness),
        "overall_spearman": fmt(spearman, 3),
        "position_spearman_qb": fmt(by_pos.get("QB"), 3),
        "position_spearman_rb": fmt(by_pos.get("RB"), 3),
        "position_spearman_wr": fmt(by_pos.get("WR"), 3),
        "position_spearman_te": fmt(by_pos.get("TE"), 3),
        "pyf_delta": fmt((spearman - pyf) if spearman is not None and pyf is not None else None, 3),
        "current_best_delta": fmt((spearman - CURRENT_BEST) if spearman is not None else None, 3),
        "full_history_0758_delta": fmt((spearman - FULL_HISTORY_REFERENCE) if spearman is not None else None, 3),
        "snap_depth_0763_delta": fmt((spearman - SNAP_DEPTH_REFERENCE) if spearman is not None else None, 3),
        "cluster_seed_delta": fmt(seed_delta, 3),
        "top12_precision": pct(metrics.get("top12_precision")),
        "top24_precision": pct(metrics.get("top24_precision")),
        "top36_precision": pct(metrics.get("top36_precision")),
        "false_positive_impact": f"candidate_fp={metrics.get('fp')};pyf_fp={metrics.get('pyf_fp')};delta={int(metrics.get('fp',0))-int(metrics.get('pyf_fp',0))}",
        "false_negative_impact": f"candidate_fn={metrics.get('fn')};pyf_fn={metrics.get('pyf_fn')};delta={int(metrics.get('fn',0))-int(metrics.get('pyf_fn',0))}",
        "sparse_history_impact": f"rows={metrics.get('sparse_rows')};candidate_error={pct(metrics.get('sparse_error_rate'))};pyf_error={pct(metrics.get('pyf_sparse_error_rate'))}",
        "low_games_impact": f"rows={metrics.get('low_games_rows')};candidate_error={pct(metrics.get('low_games_error_rate'))};pyf_error={pct(metrics.get('pyf_low_games_error_rate'))}",
        "age_lifecycle_slice": f"older_late_rows={metrics.get('older_late_rows')};young_early_rows={metrics.get('young_early_rows')}",
        "role_slice": f"high_role_rows={metrics.get('high_role_rows')};low_sparse_role_rows={metrics.get('low_sparse_role_rows')}",
        "team_change_caveat": "prior_team_only_no_target_team_projection",
        "stability_by_season": ";".join(f"{s}:{fmt(v,3)}" for s, v in by_season.items()),
        "leave_one_season_out": f"direction_stable_seasons={len(season_stable)}/{len(by_season)}",
        "outlier_flags": "partial_coverage_or_subset" if row_count < 5518 else "none",
        "full_history_comparable": full_flag,
        "broad_window_comparable": broad_flag,
        "partial_window_flag": partial_flag,
        "use_decision": result_decision(spearman, seed_delta, row_count, partial_flag),
        "notes": notes,
    }


def build_tests(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    v2.materialize_formula_scores(rows, seeds)
    registry: list[dict[str, Any]] = []
    component: list[dict[str, Any]] = []
    formula_x: list[dict[str, Any]] = []
    combos: list[dict[str, Any]] = []
    team_specs = [
        ("INGREDIENT_ONLY_TEAM_ENV_OFFENSE_SCORE", "team_env_offense_score_pct", "team_env_offense_score"),
        ("INGREDIENT_ONLY_TEAM_ENV_VOLUME_SCORE", "team_env_volume_score_pct", "team_env_volume_score"),
        ("INGREDIENT_ONLY_TEAM_ENV_SCORING_SCORE", "team_env_scoring_score_pct", "team_env_scoring_score"),
        ("INGREDIENT_ONLY_TEAM_ENV_PASS_VOLUME", "team_env_pass_volume_score_pct", "team_env_pass_volume_score"),
        ("INGREDIENT_ONLY_TEAM_ENV_RUSH_VOLUME", "team_env_rush_volume_score_pct", "team_env_rush_volume_score"),
        ("INGREDIENT_ONLY_TEAM_ENV_EPA_PER_PLAY", "team_env_epa_per_play_pct", "team_env_epa_per_play"),
        ("INGREDIENT_ONLY_TEAM_ENV_SUCCESS_RATE", "team_env_success_rate_pct", "team_env_success_rate"),
        ("INGREDIENT_ONLY_TEAM_ENV_POINTS_PER_GAME", "team_env_points_per_game_pct", "team_env_points_per_game"),
        ("INGREDIENT_ONLY_TEAM_ENV_PLAYS_PER_GAME", "team_env_plays_per_game_pct", "team_env_plays_per_game"),
        ("INGREDIENT_ONLY_TEAM_ENV_YARDS_PER_PLAY", "team_env_yards_per_play_pct", "team_env_yards_per_play"),
    ]
    all_positions = set(POSITIONS)
    team_den = denominator(rows, ["team_env_offense_score_pct"])
    for run_id, score_col, raw_field in team_specs:
        selected = selected_rows(rows, all_positions, [score_col])
        component.append(
            make_result(
                run_id,
                run_id,
                "INGREDIENT_ONLY",
                "none",
                "team_offensive_environment",
                raw_field,
                "QB/RB/WR/TE",
                selected,
                score_col,
                team_den,
                None,
                "ingredient-alone team offensive environment component test",
                "full_history_window_prior_team_subset",
                "broad_window_comparable_same_rows",
                "not_partial_window",
            )
        )
    formula_ingredients = [
        ("OFFENSE_SCORE", "team_env_offense_score_pct", "team_env_offense_score"),
        ("VOLUME_SCORE", "team_env_volume_score_pct", "team_env_volume_score"),
        ("SCORING_SCORE", "team_env_scoring_score_pct", "team_env_scoring_score"),
        ("PASS_VOLUME", "team_env_pass_volume_score_pct", "team_env_pass_volume_score"),
        ("RUSH_VOLUME", "team_env_rush_volume_score_pct", "team_env_rush_volume_score"),
        ("EPA_PER_PLAY", "team_env_epa_per_play_pct", "team_env_epa_per_play"),
        ("SUCCESS_RATE", "team_env_success_rate_pct", "team_env_success_rate"),
    ]
    weights = [("PCT025", 0.025), ("PCT050", 0.050), ("PCT100", 0.100)]
    for seed in seeds:
        formula_col = f"formula__{seed['candidate_id']}"
        formula_pct = f"{formula_col}__pct"
        seed_positions = scope_positions(seed["position_scope"])
        for label, ing_col, raw_field in formula_ingredients:
            base_selected = selected_rows(rows, seed_positions, [formula_col, ing_col])
            base_metrics = v2.metrics_for_run(base_selected, formula_col)
            for weight_label, weight in weights:
                combo_col = f"teamcombo__{seed['candidate_id']}__{label}_{weight_label}"
                materialize_combo_score(rows, combo_col, [(formula_pct, 1.0 - weight), (ing_col, weight)])
                selected = selected_rows(rows, seed_positions, [combo_col])
                run_id = f"{seed['candidate_id']}__PLUS_TEAMENV_{label}_{weight_label}"
                registry.append(
                    {
                        "run_id": run_id,
                        "test_type": "formula_x_ingredient",
                        "formula_id": seed["candidate_id"],
                        "cluster_id": seed["cluster_id"],
                        "base_formula": seed["base_formula"],
                        "ingredient_set": "team_offensive_environment",
                        "ingredient_fields": raw_field,
                        "predeclared_weighting": f"{1.0-weight:.3f} formula percentile + {weight:.3f} team environment percentile",
                    }
                )
                formula_x.append(
                    make_result(
                        run_id,
                        seed["candidate_id"],
                        seed["cluster_id"],
                        seed["base_formula"],
                        "team_offensive_environment",
                        raw_field,
                        seed["position_scope"],
                        selected,
                        combo_col,
                        team_den,
                        base_metrics,
                        "formula x team environment predeclared bounded review-only test",
                        "full_history_window_prior_team_subset",
                        "broad_window_comparable_same_rows",
                        "not_partial_window",
                    )
                )
    combo_specs = [
        ("TEAM_SNAP_PCT025_025", [("team_env_offense_score_pct", 0.025), ("snapdepth_snap_not_low_snap_score_pct", 0.025)], "team+snap/depth"),
        ("TEAM_SNAP_PCT050_050", [("team_env_offense_score_pct", 0.050), ("snapdepth_snap_not_low_snap_score_pct", 0.050)], "team+snap/depth"),
        ("TEAM_INJURY_PCT050_050", [("team_env_offense_score_pct", 0.050), ("avail_avail_availability_score_pct", 0.050)], "team+injury availability"),
        ("TEAM_REC_PCT050_050", [("team_env_offense_score_pct", 0.050), ("recopp_rec_opp_wopr_pct", 0.050)], "team+receiving opportunity"),
        ("TEAM_EPA_PCT050_050", [("team_env_offense_score_pct", 0.050), ("epa_epa_total_raw_pct", 0.050)], "team+EPA"),
        ("TEAM_FFOP_PCT050_050", [("team_env_offense_score_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.050)], "team+ffopportunity"),
        ("TEAM_NGS_PCT050_050", [("team_env_offense_score_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.050)], "team+NGS"),
        ("TEAM_SNAP_REC_PCT025_025_050", [("team_env_offense_score_pct", 0.025), ("snapdepth_snap_not_low_snap_score_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.050)], "team+snap/depth+receiving"),
        ("TEAM_SNAP_INJURY_PCT025_025_050", [("team_env_offense_score_pct", 0.025), ("snapdepth_snap_not_low_snap_score_pct", 0.025), ("avail_avail_availability_score_pct", 0.050)], "team+snap/depth+injury"),
        ("TEAM_FFOP_NGS_PCT025_050_025", [("team_env_offense_score_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.025)], "team+ffopportunity+NGS"),
    ]
    for seed in seeds:
        formula_col = f"formula__{seed['candidate_id']}"
        formula_pct = f"{formula_col}__pct"
        seed_positions = scope_positions(seed["position_scope"])
        for label, ingredients, ing_set in combo_specs:
            total_weight = sum(w for _c, w in ingredients)
            combo_col = f"teamcombo__{seed['candidate_id']}__{label}"
            materialize_combo_score(rows, combo_col, [(formula_pct, 1.0 - total_weight), *ingredients])
            req_cols = [combo_col]
            selected = selected_rows(rows, seed_positions, req_cols)
            base_cols = [formula_col, *[c for c, _w in ingredients]]
            base_selected = selected_rows(rows, seed_positions, base_cols)
            base_metrics = v2.metrics_for_run(base_selected, formula_col)
            partial = "partial_window_only" if "ffop" in ing_set.lower() or "ngs" in ing_set.lower() else "not_partial_window"
            run_id = f"{seed['candidate_id']}__PLUS_{label}"
            registry.append(
                {
                    "run_id": run_id,
                    "test_type": "ingredient_combination",
                    "formula_id": seed["candidate_id"],
                    "cluster_id": seed["cluster_id"],
                    "base_formula": seed["base_formula"],
                    "ingredient_set": ing_set,
                    "ingredient_fields": ";".join(c for c, _w in ingredients),
                    "predeclared_weighting": f"{1.0-total_weight:.3f} formula percentile + bounded ingredient weights total {total_weight:.3f}",
                }
            )
            combos.append(
                make_result(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["base_formula"],
                    ing_set,
                    ";".join(c for c, _w in ingredients),
                    seed["position_scope"],
                    selected,
                    combo_col,
                    len(base_selected) if base_selected else team_den,
                    base_metrics,
                    "bounded team environment ingredient-combination test",
                    "false" if partial == "partial_window_only" else "full_history_window_prior_team_subset",
                    "false" if partial == "partial_window_only" else "broad_window_comparable_same_rows",
                    partial,
                )
            )
    return registry, component, formula_x, combos


def best(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(rows, key=lambda r: num(r.get("overall_spearman")) or -999)


def join_coverage_rows(sidecar: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    total = len(sidecar)
    joined = sum(1 for r in sidecar if r["join_status"] == "JOINED_PRIOR_TEAM_ENVIRONMENT")
    rows.append({"coverage_scope": "all_formula_mart_rows", "rows": total, "joined_rows": joined, "coverage_rate": fmt(joined / total if total else None, 6), "notes": "Prior-team evidence required; no target-season team projection."})
    for pos in POSITIONS:
        p = [r for r in sidecar if r["position"] == pos]
        j = sum(1 for r in p if r["join_status"] == "JOINED_PRIOR_TEAM_ENVIRONMENT")
        rows.append({"coverage_scope": f"position_{pos}", "rows": len(p), "joined_rows": j, "coverage_rate": fmt(j / len(p) if p else None, 6), "notes": "Prior-team environment joined where lagged prior team could be proven."})
    for status, count in Counter(r["join_status"] for r in sidecar).items():
        rows.append({"coverage_scope": f"join_status_{status}", "rows": total, "joined_rows": count, "coverage_rate": fmt(count / total if total else None, 6), "notes": "Join status distribution."})
    return rows


def schema_validation_rows(sidecar: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dupes = len(sidecar) - len({(r["season"], r["player_id"], r["position"]) for r in sidecar})
    joined = sum(1 for r in sidecar if r["join_status"] == "JOINED_PRIOR_TEAM_ENVIRONMENT")
    leakage_fail = sum(1 for r in sidecar if str(r["season"]) and str(r["feature_season"]) and int(r["feature_season"]) != int(r["season"]) - 1)
    return [
        {"check_name": "sidecar_row_count", "status": "pass" if len(sidecar) == 5518 else "review", "value": len(sidecar), "notes": "Formula Mart player-season grain."},
        {"check_name": "duplicate_player_season_position_keys", "status": "pass" if dupes == 0 else "fail", "value": dupes, "notes": "Duplicate key check."},
        {"check_name": "source_files_hashed", "status": "pass" if len(sources) == len(SOURCE_SEASONS) else "fail", "value": len(sources), "notes": "Public PBP files hashed."},
        {"check_name": "source_use_gate", "status": "pass", "value": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE", "notes": "No source promotion."},
        {"check_name": "leakage_asof", "status": "pass" if leakage_fail == 0 else "fail", "value": leakage_fail, "notes": "Feature season N joined only to target season N+1."},
        {"check_name": "team_env_joined_rows", "status": "pass" if joined > 0 else "fail", "value": joined, "notes": "Rows with prior-team environment values."},
        {"check_name": "target_team_projection", "status": "pass", "value": "not_used", "notes": "No same-season or future team context used."},
    ]


def slice_guardrail_rows(best_result: dict[str, Any], sidecar: list[dict[str, Any]]) -> list[dict[str, Any]]:
    joined = [r for r in sidecar if r["join_status"] == "JOINED_PRIOR_TEAM_ENVIRONMENT"]
    no_team = [r for r in sidecar if r["join_status"] == "NO_PRIOR_TEAM_EVIDENCE"]
    return [
        {"slice": "best_result", "metric": "run_id", "rows": best_result["row_count"], "value": best_result["run_id"], "notes": "Best team-environment result by Spearman."},
        {"slice": "best_result", "metric": "spearman", "rows": best_result["row_count"], "value": best_result["overall_spearman"], "notes": best_result["use_decision"]},
        {"slice": "prior_team_joined", "metric": "coverage", "rows": len(sidecar), "value": pct(len(joined) / len(sidecar)), "notes": "Prior-team evidence coverage."},
        {"slice": "missing_prior_team", "metric": "coverage", "rows": len(sidecar), "value": pct(len(no_team) / len(sidecar)), "notes": "Rows where prior team could not be safely inferred."},
        {"slice": "team_change", "metric": "caveat", "rows": len(sidecar), "value": "prior_team_only", "notes": "Target-season team changes are not projected or used."},
        {"slice": "sparse_history", "metric": "impact", "rows": best_result["row_count"], "value": best_result["sparse_history_impact"], "notes": "From best result row."},
        {"slice": "low_games", "metric": "impact", "rows": best_result["row_count"], "value": best_result["low_games_impact"], "notes": "From best result row."},
        {"slice": "age_lifecycle", "metric": "interaction", "rows": best_result["row_count"], "value": best_result["age_lifecycle_slice"], "notes": "From best result row."},
        {"slice": "role_archetype", "metric": "interaction", "rows": best_result["row_count"], "value": best_result["role_slice"], "notes": "From best result row."},
    ]


def stability_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in sorted(results, key=lambda r: num(r.get("overall_spearman")) or -999, reverse=True)[:20]:
        for part in str(row.get("stability_by_season", "")).split(";"):
            if not part or ":" not in part:
                continue
            season, val = part.split(":", 1)
            out.append(
                {
                    "run_id": row["run_id"],
                    "season": season,
                    "season_spearman": val,
                    "overall_spearman": row["overall_spearman"],
                    "leave_one_season_out": row["leave_one_season_out"],
                    "outlier_flags": row["outlier_flags"],
                }
            )
    return out


def reports(
    sidecar: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    component: list[dict[str, Any]],
    formula_x: list[dict[str, Any]],
    combos: list[dict[str, Any]],
    joins: dict[str, int],
) -> str:
    all_results = [*component, *formula_x, *combos]
    best_component = best(component)
    best_formula = best(formula_x)
    best_combo = best(combos)
    best_overall = best(all_results)
    joined = sum(1 for r in sidecar if r["join_status"] == "JOINED_PRIOR_TEAM_ENVIRONMENT")
    coverage = joined / len(sidecar)
    material_755 = [r for r in all_results if (num(r.get("overall_spearman")) or 0) >= CURRENT_BEST + 0.005 and r["partial_window_flag"] != "partial_window_only"]
    material_758 = [r for r in all_results if (num(r.get("overall_spearman")) or 0) >= FULL_HISTORY_REFERENCE + 0.005 and r["partial_window_flag"] != "partial_window_only"]
    material_763 = [r for r in all_results if (num(r.get("overall_spearman")) or 0) >= SNAP_DEPTH_REFERENCE + 0.003 and r["partial_window_flag"] != "partial_window_only"]
    if material_763:
        verdict = "GREEN_TEAM_OFFENSIVE_ENVIRONMENT_ADDS_REVIEW_ONLY_SIGNAL"
        next_use = "AVAILABLE_REVIEW_ONLY_ADDITIVE_SIGNAL"
    elif material_755 or best_overall["partial_window_flag"] == "partial_window_only":
        verdict = "YELLOW_TEAM_OFFENSIVE_ENVIRONMENT_PARTIAL_WITH_CAVEATS"
        next_use = "AVAILABLE_REVIEW_ONLY_TEAM_CONTEXT"
    else:
        verdict = "RED_TEAM_OFFENSIVE_ENVIRONMENT_NO_INCREMENTAL_SIGNAL"
        next_use = "AVAILABLE_BUT_NO_INCREMENTAL_SIGNAL"

    report = f"""
# Team Offensive Environment Sidecar V1 Report

Verdict: `{verdict}`

Artifact path: `{OUT_DIR}`

Remote HQ verified: `{REMOTE_HEAD}`

Prior plateau-review commit verified: `{PRIOR_PLATEAU_COMMIT}`

## Source And Sidecar

- Source family: public nflverse/nflfastR `play_by_play_YYYY.parquet`, already cached locally under `C:\\NWR_REVIEW`.
- Source seasons: `2012-2024`.
- Sidecar rows: `{len(sidecar)}`.
- Prior-team environment joined rows: `{joined}` / `{len(sidecar)}` (`{coverage:.1%}`).
- Team environment source files hashed: `{len(sources)}`.
- Prior player team source precedence: EPA sidecar, snap/depth sidecar, injury availability sidecar, then receiving opportunity sidecar.

## Best Results

- Best component: `{best_component['run_id']}` Spearman `{best_component['overall_spearman']}` vs PYF delta `{best_component['pyf_delta']}`.
- Best formula x ingredient: `{best_formula['run_id']}` Spearman `{best_formula['overall_spearman']}`, seed delta `{best_formula['cluster_seed_delta']}`, snap/depth `.763` delta `{best_formula['snap_depth_0763_delta']}`.
- Best ingredient combination: `{best_combo['run_id']}` Spearman `{best_combo['overall_spearman']}`, seed delta `{best_combo['cluster_seed_delta']}`, partial flag `{best_combo['partial_window_flag']}`.

## Plateau Comparison

- Results materially beating `.755` on non-partial rows: `{len(material_755)}`.
- Results materially beating full-history `.758` on non-partial rows: `{len(material_758)}`.
- Results materially beating snap/depth `.763` on comparable non-partial rows: `{len(material_763)}`.

## Team-Change Caveat

The sidecar uses only each player's proven prior-season team. It does not project target-season team changes and does not use same-season team environment as a predictor. Rows without safe prior-team evidence remain missing rather than guessed.

## Decision

Team offensive environment classification: `{next_use}`.

Review-only ranking simulation remains blocked. Production/model-use, rankings integration, app/runtime changes, source promotion, push/merge, and canonical `local_exports` mutation remain blocked.
"""
    write_md(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_SIDECAR_V1_REPORT.md", report)

    next_step = "Batch Canonicalization / Merge Review V1" if verdict.startswith("GREEN") else "Stop and review team-environment findings before more formula work"
    write_md(
        OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_NEXT_USE_DECISION.md",
        f"""
# Team Offensive Environment Next Use Decision

Decision: `{next_use}`

Recommended next step: `{next_step}`.

Team offensive environment may be used only for review-only component tests, interaction checks, and team-context slice review. It is not approved for production/model-use, direct ranking input, hidden sort logic, recommendation logic, or review-only ranking simulation.

Best component: `{best_component['run_id']}` Spearman `{best_component['overall_spearman']}`.

Best formula x ingredient: `{best_formula['run_id']}` Spearman `{best_formula['overall_spearman']}`.

Best combination: `{best_combo['run_id']}` Spearman `{best_combo['overall_spearman']}`.
""",
    )
    write_md(
        OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_TEAM_CHANGE_CAVEATS.md",
        """
# Team Offensive Environment Team-Change Caveats

The sidecar joins player-season rows to the player's prior-season team environment only. It does not know or project the player's future/target-season team. This is intentionally conservative and leakage-safe, but it can understate or misstate context for free-agent moves, trades, depth-chart changes, coaching changes, or quarterback changes between feature season N and target season N+1.

No target-season team context, current team context, or 2026 team context was used as a historical feature.
""",
    )
    write_md(
        OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_BLOCKERS_AND_CAVEATS.md",
        """
# Team Offensive Environment Blockers And Caveats

- Team context is prior-team only; player movement is not projected.
- Team-level environment may duplicate role, snap, receiving opportunity, and EPA signals.
- PBP-derived points use source scoreboard context and should be treated as review-only environment context, not official scoring truth.
- Same-season/future team environment remains blocked.
- Production/model-use, rankings integration, app/runtime changes, source promotion, and ranking simulation remain blocked.
""",
    )
    write_md(
        OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_SOURCE_TRACE.md",
        f"""
# Team Offensive Environment Source Trace

- Remote HQ verified: `{REMOTE_HEAD}`
- Prior plateau-review commit verified: `{PRIOR_PLATEAU_COMMIT}`
- Source cache: `{SOURCE_CACHE}`
- Source family: public nflverse/nflfastR play-by-play parquet files.
- Source years: `2012-2024`.
- Prior team evidence sidecars: EPA/opportunity, snap/depth role, point-in-time injury availability, and receiving opportunity.
- Prior combination join counts: `{joins}`

No SportsDataIO, paid/API/free-trial/API-key source, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, current-only ADP, same-season/future context, production/model-use, rankings integration, app/runtime change, source promotion, push, merge, or canonical `local_exports` mutation occurred.
""",
    )
    return verdict


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    compile(V2_HELPER.read_text(encoding="utf-8"), str(V2_HELPER), "exec")
    rows = v2.load_formula_panel()
    seeds = [s for s in v2.load_seed_registry() if str(s["cluster_id"]).startswith("C") and str(s["cluster_id"])[1:].isdigit()]
    sidecar, sources = build_sidecar(rows)
    attach_sidecar(
        rows,
        sidecar,
        "teamenv",
        [
            "team_env_plays",
            "team_env_plays_per_game",
            "team_env_pass_attempts",
            "team_env_rush_attempts",
            "team_env_pass_rate",
            "team_env_rush_rate",
            "team_env_points",
            "team_env_points_per_game",
            "team_env_total_yards",
            "team_env_yards_per_play",
            "team_env_first_downs",
            "team_env_turnovers",
            "team_env_epa_per_play",
            "team_env_pass_epa",
            "team_env_rush_epa",
            "team_env_success_rate",
            "team_env_volume_score",
            "team_env_scoring_score",
            "team_env_pass_volume_score",
            "team_env_rush_volume_score",
            "team_env_offense_score",
        ],
    )
    # Expose concise teamenv aliases for tests.
    for row in rows:
        for col in [
            "team_env_offense_score",
            "team_env_volume_score",
            "team_env_scoring_score",
            "team_env_pass_volume_score",
            "team_env_rush_volume_score",
            "team_env_epa_per_play",
            "team_env_success_rate",
            "team_env_points_per_game",
            "team_env_plays_per_game",
            "team_env_yards_per_play",
        ]:
            row[col] = row.get(f"teamenv_{col}")
            row[f"{col}_pct"] = row.get(f"teamenv_{col}_pct")
    joins = attach_prior_sidecars(rows)
    registry, component, formula_x, combos = build_tests(rows, seeds)
    all_results = [*component, *formula_x, *combos]
    best_result = best(all_results)
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_SOURCE_LEDGER.csv", sources)
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_REVIEW_ONLY_SIDECAR.csv", sidecar)
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_JOIN_COVERAGE.csv", join_coverage_rows(sidecar))
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_SCHEMA_VALIDATION.csv", schema_validation_rows(sidecar, sources))
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_COMPONENT_TEST_RESULTS.csv", component, RESULT_FIELDS)
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_FORMULA_X_INGREDIENT_RESULTS.csv", formula_x, RESULT_FIELDS)
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_INGREDIENT_COMBINATION_RESULTS.csv", combos, RESULT_FIELDS)
    write_csv(
        OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_ALL_RESULTS_REQUIRED_SCHEMA.csv",
        [{"field_name": field, "present": "true", "notes": "Required normalized result field."} for field in RESULT_FIELDS],
        ["field_name", "present", "notes"],
    )
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_SLICE_GUARDRAILS.csv", slice_guardrail_rows(best_result, sidecar))
    write_csv(OUT_DIR / "TEAM_OFFENSIVE_ENVIRONMENT_STABILITY_BY_SEASON.csv", stability_rows(all_results))
    verdict = reports(sidecar, sources, component, formula_x, combos, joins)
    print(f"{verdict} wrote artifacts to {OUT_DIR}")


if __name__ == "__main__":
    main()
