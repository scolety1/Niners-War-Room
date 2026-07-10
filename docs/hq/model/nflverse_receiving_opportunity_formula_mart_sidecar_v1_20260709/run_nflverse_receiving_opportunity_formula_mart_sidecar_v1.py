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
CURRENT_BEST_FULL_HISTORY = 0.755
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_EPA_COMMIT = "04316ca00c78f3804a26b5ff7520a32295b61042"
SOURCE_CACHE = Path(r"C:\NWR_REVIEW\nflverse_epa_opportunity_source_cache_20260709")
SOURCE_SEASONS = list(range(2012, 2025))
V2_ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
)
EPA_ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709"
)
V2_HELPER = V2_ARTIFACT / "run_nwr_autonomous_ingredient_upgrade_sequence_v2.py"

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
    "stability_by_season",
    "leave_one_season_out",
    "outlier_flags",
    "use_decision",
    "notes",
]


def load_v2_module() -> Any:
    spec = importlib.util.spec_from_file_location("nwr_v2_helpers", V2_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import V2 helper script from {V2_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v2 = load_v2_module()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def num(value: Any) -> float | None:
    return v2.num(value)


def fmt(value: float | None, digits: int = 3) -> str:
    return v2.fmt(value, digits)


def pct(value: float | None, digits: int = 1) -> str:
    return v2.pct(value, digits)


def clean_float(value: Any, default: float = 0.0) -> float:
    val = num(value)
    return float(val) if val is not None and math.isfinite(float(val)) else default


def safe_div(nume: Any, denom: Any, require_positive_denom: bool = False) -> float | None:
    n = num(nume)
    d = num(denom)
    if n is None or d is None or d == 0:
        return None
    if require_positive_denom and d <= 0:
        return None
    return float(n) / float(d)


def mode_text(values: pd.Series) -> str:
    clean = [str(v) for v in values.dropna().tolist() if str(v).strip() and str(v) != "nan"]
    if not clean:
        return ""
    return Counter(clean).most_common(1)[0][0]


def load_pbp_year(path: Path) -> pd.DataFrame:
    cols = [
        "season",
        "week",
        "season_type",
        "play_type",
        "posteam",
        "receiver_player_id",
        "receiver_player_name",
        "receiver",
        "receiver_id",
        "air_yards",
        "yards_after_catch",
        "receiving_yards",
        "complete_pass",
        "pass_attempt",
        "first_down_pass",
        "first_down",
        "epa",
        "air_epa",
        "yac_epa",
    ]
    return pd.read_parquet(path, columns=cols)


def source_path_for_season(season: int) -> Path:
    return SOURCE_CACHE / f"play_by_play_{season}.parquet"


def source_url_for_season(season: int) -> str:
    return f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"


def build_receiving_feature_rows() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    source_rows: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        path = source_path_for_season(season)
        if not path.exists():
            raise RuntimeError(f"Missing local public nflfastR PBP cache file: {path}")
        file_hash = sha256_file(path)
        df = load_pbp_year(path)
        reg = df[df["season_type"].eq("REG")].copy()
        target = reg[reg["play_type"].eq("pass") & reg["receiver_player_id"].notna()].copy()
        for col in [
            "air_yards",
            "yards_after_catch",
            "receiving_yards",
            "complete_pass",
            "pass_attempt",
            "first_down_pass",
            "first_down",
            "epa",
            "air_epa",
            "yac_epa",
        ]:
            target[col] = pd.to_numeric(target[col], errors="coerce").fillna(0.0)
        target["player_id"] = target["receiver_player_id"].astype(str)
        target["player_name"] = target["receiver_player_name"].astype("string").fillna("")
        target["target_event"] = 1.0
        target["completed_air_yards"] = target["air_yards"].where(target["complete_pass"] > 0, 0.0)
        team = (
            target.groupby(["season", "posteam"], dropna=False)
            .agg(
                team_targets=("target_event", "sum"),
                team_air_yards=("air_yards", "sum"),
            )
            .reset_index()
        )
        # The grouped player frame needs a team denominator. Use a second grouped pass
        # rather than relying on team as an index level because traded players are
        # represented at player-season grain in the review mart.
        player_team = (
            target.groupby(["player_id", "season", "posteam"], dropna=False)
            .agg(
                player_name=("player_name", mode_text),
                rec_opp_targets=("target_event", "sum"),
                rec_opp_receptions=("complete_pass", "sum"),
                rec_opp_receiving_yards=("receiving_yards", "sum"),
                rec_opp_air_yards=("air_yards", "sum"),
                rec_opp_completed_air_yards=("completed_air_yards", "sum"),
                rec_opp_yac=("yards_after_catch", "sum"),
                rec_opp_receiving_first_downs=("first_down_pass", "sum"),
                rec_opp_first_downs_any=("first_down", "sum"),
                rec_opp_receiving_epa=("epa", "sum"),
                rec_opp_receiving_air_epa=("air_epa", "sum"),
                rec_opp_receiving_yac_epa=("yac_epa", "sum"),
            )
            .reset_index()
        )
        player_team = player_team.merge(team, on=["season", "posteam"], how="left")
        player_team["target_share_component"] = player_team.apply(
            lambda r: safe_div(r["rec_opp_targets"], r["team_targets"]), axis=1
        )
        player_team["air_share_component"] = player_team.apply(
            lambda r: safe_div(r["rec_opp_air_yards"], r["team_air_yards"], True), axis=1
        )
        player_team["target_share_weighted"] = player_team["target_share_component"].fillna(0.0)
        player_team["air_share_weighted"] = player_team["air_share_component"].fillna(0.0)
        player = (
            player_team.groupby(["player_id", "season"], dropna=False)
            .agg(
                player_name=("player_name", mode_text),
                team=("posteam", mode_text),
                rec_opp_targets=("rec_opp_targets", "sum"),
                rec_opp_receptions=("rec_opp_receptions", "sum"),
                rec_opp_receiving_yards=("rec_opp_receiving_yards", "sum"),
                rec_opp_air_yards=("rec_opp_air_yards", "sum"),
                rec_opp_completed_air_yards=("rec_opp_completed_air_yards", "sum"),
                rec_opp_yac=("rec_opp_yac", "sum"),
                rec_opp_receiving_first_downs=("rec_opp_receiving_first_downs", "sum"),
                rec_opp_first_downs_any=("rec_opp_first_downs_any", "sum"),
                rec_opp_receiving_epa=("rec_opp_receiving_epa", "sum"),
                rec_opp_receiving_air_epa=("rec_opp_receiving_air_epa", "sum"),
                rec_opp_receiving_yac_epa=("rec_opp_receiving_yac_epa", "sum"),
                rec_opp_target_share=("target_share_weighted", "sum"),
                rec_opp_air_yards_share=("air_share_weighted", "sum"),
            )
            .reset_index()
        )
        player = player.rename(columns={"season": "feature_season"})
        player["rec_opp_wopr"] = 1.5 * player["rec_opp_target_share"] + 0.7 * player["rec_opp_air_yards_share"]
        player["rec_opp_racr"] = player.apply(
            lambda r: safe_div(r["rec_opp_receiving_yards"], r["rec_opp_air_yards"], True), axis=1
        )
        player["rec_opp_pacr"] = player.apply(
            lambda r: safe_div(r["rec_opp_completed_air_yards"], r["rec_opp_air_yards"], True), axis=1
        )
        player["source_path"] = str(path)
        player["source_url"] = source_url_for_season(season)
        player["source_hash"] = file_hash
        frames.append(player)
        source_rows.append(
            {
                "source_family": "nflfastR_public_play_by_play_receiving_opportunity",
                "feature_season": season,
                "source_url": source_url_for_season(season),
                "local_cache_path": str(path),
                "sha256": file_hash,
                "file_size": path.stat().st_size,
                "raw_rows": len(df),
                "regular_season_rows": len(reg),
                "receiving_target_rows": len(target),
                "players_with_targets": target["player_id"].nunique(),
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "asof_status": "PASS_LAGGED_CLOSED_FEATURE_SEASON_ONLY",
            }
        )
    features = pd.concat(frames, ignore_index=True, sort=False)
    return features, source_rows


def source_hash_by_season(sources: list[dict[str, Any]]) -> dict[int, dict[str, str]]:
    return {
        int(r["feature_season"]): {
            "path": str(r["local_cache_path"]),
            "url": str(r["source_url"]),
            "hash": str(r["sha256"]),
        }
        for r in sources
    }


def build_receiving_sidecar(panel_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    features, sources = build_receiving_feature_rows()
    source_map = source_hash_by_season(sources)
    lookup = {
        (str(r["player_id"]), int(r["feature_season"])): r
        for r in features.to_dict("records")
    }
    sidecar: list[dict[str, Any]] = []
    for row in panel_rows:
        feature_season = int(row["feature_season"])
        if feature_season not in SOURCE_SEASONS:
            continue
        key = (str(row["player_id"]), feature_season)
        feature = lookup.get(key, {})
        source = source_map[feature_season]
        has_target = clean_float(feature.get("rec_opp_targets")) > 0
        base = {
            "season": int(row["season"]),
            "feature_season": feature_season,
            "player_id": str(row["player_id"]),
            "player_name": row.get("player_name") or feature.get("player_name") or "",
            "position": str(row["position"]),
            "team": feature.get("team") or "",
            "rec_opp_targets": fmt(num(feature.get("rec_opp_targets")) or 0.0, 3),
            "rec_opp_receptions": fmt(num(feature.get("rec_opp_receptions")) or 0.0, 3),
            "rec_opp_receiving_yards": fmt(num(feature.get("rec_opp_receiving_yards")) or 0.0, 3),
            "rec_opp_target_share": fmt(num(feature.get("rec_opp_target_share")) or 0.0, 6),
            "rec_opp_air_yards": fmt(num(feature.get("rec_opp_air_yards")) or 0.0, 3),
            "rec_opp_air_yards_share": fmt(num(feature.get("rec_opp_air_yards_share")) or 0.0, 6),
            "rec_opp_wopr": fmt(num(feature.get("rec_opp_wopr")) or 0.0, 6),
            "rec_opp_racr": fmt(num(feature.get("rec_opp_racr")), 6),
            "rec_opp_pacr": fmt(num(feature.get("rec_opp_pacr")), 6),
            "rec_opp_yac": fmt(num(feature.get("rec_opp_yac")) or 0.0, 3),
            "rec_opp_receiving_first_downs": fmt(num(feature.get("rec_opp_receiving_first_downs")) or 0.0, 3),
            "rec_opp_receiving_epa": fmt(num(feature.get("rec_opp_receiving_epa")) or 0.0, 6),
            "rec_opp_receiving_air_epa": fmt(num(feature.get("rec_opp_receiving_air_epa")) or 0.0, 6),
            "rec_opp_receiving_yac_epa": fmt(num(feature.get("rec_opp_receiving_yac_epa")) or 0.0, 6),
            "rec_opp_source_path": source["path"],
            "rec_opp_source_url": source["url"],
            "rec_opp_source_hash": source["hash"],
            "join_status": "JOINED_RECEIVING_TARGET" if has_target else "NO_RECEIVING_TARGET_TRUE_ZERO_WITH_SOURCE_SEASON",
            "coverage_status": "SOURCE_SEASON_AVAILABLE",
            "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
            "decision_date_safe": "PASS_LAGGED_N_TO_N_PLUS_1",
            "leakage_flag": "PASS_FEATURE_SEASON_N_TO_TARGET_SEASON_N_PLUS_1",
            "identity_flag": "PASS_GSIS_PLAYER_ID_JOIN_REQUIRED",
            "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
            "caveat": "PBP receiving opportunity is lagged player-season context; no true route/YPRR/TPRR claim; RACR/PACR null when air yards denominator is not positive.",
        }
        sidecar.append(base)
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
        if match:
            joined += 1
            for col in raw_cols:
                row[f"{prefix}_{col}"] = num(match.get(column_map.get(col, col)))
        else:
            for col in raw_cols:
                row[f"{prefix}_{col}"] = None
    for col in raw_cols:
        v2.assign_percentile(rows, f"{prefix}_{col}", f"{prefix}_{col}_pct")
    return {"joined": joined}


def load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def attach_prior_sidecars(rows: list[dict[str, Any]]) -> dict[str, int]:
    ff_rows = load_csv(V2_ARTIFACT / "FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv")
    ngs_rows = load_csv(V2_ARTIFACT / "NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv")
    epa_rows = load_csv(EPA_ARTIFACT / "NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv")
    ff = attach_sidecar(
        rows,
        ff_rows,
        "ffop",
        ["ffop_xfp_total", "ffop_xfp_per_game", "ffop_expected_first_downs"],
        {
            "ffop_xfp_total": "ffop_total_fantasy_points_exp",
            "ffop_xfp_per_game": "ffop_total_fantasy_points_exp_per_game",
            "ffop_expected_first_downs": "ffop_total_first_down_exp",
        },
    )
    ngs = attach_sidecar(rows, ngs_rows, "ngs", ["ngs_position_signal_raw"])
    epa = attach_sidecar(
        rows,
        epa_rows,
        "epa",
        ["epa_total_raw", "epa_per_opportunity", "rec_epa_per_target"],
    )
    return {"ffop_joined": ff["joined"], "ngs_joined": ngs["joined"], "epa_joined": epa["joined"]}


def denominator(rows: list[dict[str, Any]], positions: set[str] | None = None) -> int:
    if positions is None:
        positions = set(POSITIONS)
    return len([r for r in rows if int(r["feature_season"]) in SOURCE_SEASONS and str(r["position"]) in positions])


def selected_rows(rows: list[dict[str, Any]], positions: set[str], required_cols: list[str]) -> list[dict[str, Any]]:
    return v2.selected_rows(rows, positions, required_cols)


def materialize_combo_score(rows: list[dict[str, Any]], score_col: str, parts: list[tuple[str, float]]) -> None:
    for row in rows:
        value = 0.0
        ok = True
        for col, weight in parts:
            val = row.get(col)
            if val is None:
                ok = False
                break
            value += float(val) * weight
        row[score_col] = value if ok else None


def register(
    registry: list[dict[str, Any]],
    run_id: str,
    test_type: str,
    formula_id: str,
    cluster_id: str,
    base_formula: str,
    ingredient_set: str,
    fields: str,
    weighting: str,
    full_history_flag: str,
) -> None:
    registry.append(
        {
            "run_id": run_id,
            "test_type": test_type,
            "formula_id": formula_id,
            "cluster_id": cluster_id,
            "base_formula": base_formula,
            "ingredient_set": ingredient_set,
            "ingredient_fields": fields,
            "predeclared_weighting": weighting,
            "full_history_comparable_flag": full_history_flag,
            "source_use_gate_status": "REVIEW_ONLY_NOT_MODEL_USE_NOT_RANKING",
        }
    )


def result_with_note(
    run_id: str,
    formula_id: str,
    cluster_id: str,
    base_formula: str,
    ingredient_set: str,
    ingredient_fields: str,
    positions: str,
    selected: list[dict[str, Any]],
    score_col: str,
    denom: int,
    seed_metrics: dict[str, Any] | None,
    notes: str,
) -> dict[str, Any]:
    return v2.result_row(
        run_id,
        formula_id,
        cluster_id,
        base_formula,
        ingredient_set,
        ingredient_fields,
        positions,
        selected,
        score_col,
        denom,
        seed_metrics=seed_metrics,
        notes=notes,
    )


def build_tests(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    v2.materialize_formula_scores(rows, seeds)
    registry: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    all_positions = set(POSITIONS)
    full_denom = denominator(rows, all_positions)
    component_specs = [
        ("INGREDIENT_ONLY_REC_OPP_TARGETS", "recopp_rec_opp_targets_pct", "rec_opp_targets"),
        ("INGREDIENT_ONLY_REC_OPP_TARGET_SHARE", "recopp_rec_opp_target_share_pct", "rec_opp_target_share"),
        ("INGREDIENT_ONLY_REC_OPP_AIR_YARDS", "recopp_rec_opp_air_yards_pct", "rec_opp_air_yards"),
        ("INGREDIENT_ONLY_REC_OPP_AIR_YARDS_SHARE", "recopp_rec_opp_air_yards_share_pct", "rec_opp_air_yards_share"),
        ("INGREDIENT_ONLY_REC_OPP_WOPR", "recopp_rec_opp_wopr_pct", "rec_opp_wopr"),
        ("INGREDIENT_ONLY_REC_OPP_RACR", "recopp_rec_opp_racr_pct", "rec_opp_racr"),
        ("INGREDIENT_ONLY_REC_OPP_PACR", "recopp_rec_opp_pacr_pct", "rec_opp_pacr"),
        ("INGREDIENT_ONLY_REC_OPP_YAC", "recopp_rec_opp_yac_pct", "rec_opp_yac"),
        ("INGREDIENT_ONLY_REC_OPP_FIRST_DOWNS", "recopp_rec_opp_receiving_first_downs_pct", "rec_opp_receiving_first_downs"),
        ("INGREDIENT_ONLY_REC_OPP_RECEIVING_EPA", "recopp_rec_opp_receiving_epa_pct", "rec_opp_receiving_epa"),
    ]
    for run_id, score_col, raw_field in component_specs:
        selected = selected_rows(rows, all_positions, [score_col])
        register(
            registry,
            run_id,
            "ingredient_alone",
            run_id,
            "INGREDIENT_ONLY",
            "none",
            "nflverse_receiving_opportunity",
            raw_field,
            "ingredient percentile rank only",
            "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025" if len(selected) > 5000 else "PARTIAL_FIELD_COVERAGE",
        )
        results.append(
            result_with_note(
                run_id,
                run_id,
                "INGREDIENT_ONLY",
                "none",
                "nflverse_receiving_opportunity",
                raw_field,
                "QB/RB/WR/TE",
                selected,
                score_col,
                full_denom,
                None,
                "Receiving opportunity ingredient alone; public nflfastR PBP aggregated regular season and lagged N-to-N+1 review-only.",
            )
        )

    formula_ingredients = [
        ("TARGETS", "recopp_rec_opp_targets_pct"),
        ("TARGET_SHARE", "recopp_rec_opp_target_share_pct"),
        ("AIR_YARDS", "recopp_rec_opp_air_yards_pct"),
        ("AIR_YARDS_SHARE", "recopp_rec_opp_air_yards_share_pct"),
        ("WOPR", "recopp_rec_opp_wopr_pct"),
        ("RACR", "recopp_rec_opp_racr_pct"),
        ("PACR", "recopp_rec_opp_pacr_pct"),
        ("YAC", "recopp_rec_opp_yac_pct"),
        ("FIRST_DOWNS", "recopp_rec_opp_receiving_first_downs_pct"),
        ("RECEIVING_EPA", "recopp_rec_opp_receiving_epa_pct"),
    ]
    weights = [0.025, 0.05, 0.10]
    for seed in seeds:
        seed_col = f"formula__{seed['candidate_id']}__pct"
        seed_rows = selected_rows(rows, v2.scope_positions(seed["position_scope"]), [seed_col])
        seed_metrics = v2.metrics_for_run(seed_rows, seed_col)
        scope = v2.scope_positions(seed["position_scope"])
        denom = denominator(rows, scope)
        for suffix, ingredient_col in formula_ingredients:
            for weight in weights:
                pct_label = str(int(weight * 1000)).zfill(3)
                score_col = f"{seed_col}__RECOPP_{suffix}_PCT{pct_label}"
                materialize_combo_score(rows, score_col, [(seed_col, 1.0 - weight), (ingredient_col, weight)])
                selected = selected_rows(rows, scope, [score_col])
                run_id = f"{seed['candidate_id']}__PLUS_RECOPP_{suffix}_PCT{pct_label}"
                register(
                    registry,
                    run_id,
                    "formula_x_ingredient",
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "nflverse_receiving_opportunity",
                    ingredient_col.replace("recopp_", ""),
                    f"seed_percentile={1.0 - weight:.3f};ingredient_percentile={weight:.3f}",
                    "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025" if len(selected) > 5000 else "PARTIAL_BY_POSITION_OR_FIELD_COVERAGE",
                )
                results.append(
                    result_with_note(
                        run_id,
                        seed["candidate_id"],
                        seed["cluster_id"],
                        seed["formula_definition"],
                        "nflverse_receiving_opportunity",
                        ingredient_col.replace("recopp_", ""),
                        seed["position_scope"],
                        selected,
                        score_col,
                        denom,
                        seed_metrics,
                        "Fixed predeclared receiving opportunity additive variant; no dynamic tuning.",
                    )
                )

    combo_specs = [
        ("RECOPP_WOPR_FFOP_PCT025_025", [("recopp_rec_opp_wopr_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("RECOPP_WOPR_FFOP_PCT050_050", [("recopp_rec_opp_wopr_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("RECOPP_WOPR_FFOP_PCT050_025", [("recopp_rec_opp_wopr_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("RECOPP_WOPR_FFOP_PCT025_050", [("recopp_rec_opp_wopr_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("RECOPP_WOPR_NGS_PCT025_025", [("recopp_rec_opp_wopr_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("RECOPP_WOPR_NGS_PCT050_050", [("recopp_rec_opp_wopr_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.050)]),
        ("RECOPP_WOPR_NGS_PCT050_025", [("recopp_rec_opp_wopr_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("RECOPP_WOPR_NGS_PCT025_050", [("recopp_rec_opp_wopr_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.050)]),
        ("RECOPP_WOPR_EPA_PCT025_025", [("recopp_rec_opp_wopr_pct", 0.025), ("epa_epa_total_raw_pct", 0.025)]),
        ("RECOPP_WOPR_EPA_PCT050_050", [("recopp_rec_opp_wopr_pct", 0.050), ("epa_epa_total_raw_pct", 0.050)]),
        ("RECOPP_WOPR_EPA_PCT050_025", [("recopp_rec_opp_wopr_pct", 0.050), ("epa_epa_total_raw_pct", 0.025)]),
        ("RECOPP_WOPR_EPA_PCT025_050", [("recopp_rec_opp_wopr_pct", 0.025), ("epa_epa_total_raw_pct", 0.050)]),
        ("RECOPP_WOPR_FFOP_NGS_PCT025_050_025", [("recopp_rec_opp_wopr_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("RECOPP_WOPR_FFOP_NGS_PCT050_025_025", [("recopp_rec_opp_wopr_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("RECOPP_WOPR_EPA_FFOP_PCT025_025_050", [("recopp_rec_opp_wopr_pct", 0.025), ("epa_epa_total_raw_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("RECOPP_WOPR_EPA_FFOP_PCT050_025_025", [("recopp_rec_opp_wopr_pct", 0.050), ("epa_epa_total_raw_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.025)]),
    ]
    for seed in seeds:
        seed_col = f"formula__{seed['candidate_id']}__pct"
        seed_rows = selected_rows(rows, v2.scope_positions(seed["position_scope"]), [seed_col])
        seed_metrics = v2.metrics_for_run(seed_rows, seed_col)
        scope = v2.scope_positions(seed["position_scope"])
        denom = denominator(rows, scope)
        for suffix, ingredients in combo_specs:
            total_weight = sum(weight for _, weight in ingredients)
            score_col = f"{seed_col}__{suffix}"
            materialize_combo_score(rows, score_col, [(seed_col, 1.0 - total_weight), *ingredients])
            selected = selected_rows(rows, scope, [score_col])
            run_id = f"{seed['candidate_id']}__PLUS_{suffix}"
            fields = "|".join(col for col, _ in ingredients)
            partial = any(col.startswith(("ffop_", "ngs_")) for col, _ in ingredients)
            register(
                registry,
                run_id,
                "ingredient_combination",
                seed["candidate_id"],
                seed["cluster_id"],
                seed["formula_definition"],
                "nflverse_receiving_opportunity+prior_sidecars",
                fields,
                f"seed_percentile={1.0 - total_weight:.3f};" + ";".join(f"{col}={weight:.3f}" for col, weight in ingredients),
                "PARTIAL_WINDOW_PRIOR_V2_SIDE_CAR" if partial else "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025",
            )
            results.append(
                result_with_note(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "nflverse_receiving_opportunity+prior_sidecars",
                    fields,
                    seed["position_scope"],
                    selected,
                    score_col,
                    denom,
                    seed_metrics,
                    "Bounded predeclared receiving opportunity combination; prior ffop/NGS sidecars retain partial-window caveats when used.",
                )
            )
    return registry, results


def join_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ingredients = [
        ("nflverse_receiving_opportunity", "recopp_rec_opp_wopr", set(SOURCE_SEASONS)),
        ("ffopportunity_prior_v2", "ffop_ffop_xfp_total", {2021, 2022, 2023, 2024}),
        ("nflverse_ngs_prior_v2", "ngs_ngs_position_signal_raw", {2021, 2022, 2023, 2024}),
        ("nflverse_epa_prior_lane", "epa_epa_total_raw", set(SOURCE_SEASONS)),
    ]
    out = []
    for ingredient, prefix, seasons in ingredients:
        for pos in ["ALL", *POSITIONS]:
            eligible = [
                r
                for r in rows
                if int(r["feature_season"]) in seasons and (pos == "ALL" or str(r["position"]) == pos)
            ]
            joined = [r for r in eligible if r.get(prefix) is not None]
            out.append(
                {
                    "ingredient": ingredient,
                    "position": pos,
                    "eligible_rows": len(eligible),
                    "joined_rows": len(joined),
                    "join_coverage_pct": pct(len(joined) / len(eligible) if eligible else None),
                    "target_seasons": "|".join(str(s) for s in sorted({int(r["season"]) for r in joined})),
                    "feature_seasons": "|".join(str(s) for s in sorted({int(r["feature_season"]) for r in joined})),
                    "join_key": "player_id + feature_season + position",
                    "asof_status": "PASS_LAGGED_N_TO_N_PLUS_1",
                }
            )
    return out


def validation_rows(sidecar: list[dict[str, Any]], rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    required = {
        "season",
        "feature_season",
        "player_id",
        "player_name",
        "position",
        "team",
        "rec_opp_targets",
        "rec_opp_target_share",
        "rec_opp_air_yards",
        "rec_opp_air_yards_share",
        "rec_opp_wopr",
        "rec_opp_racr",
        "rec_opp_pacr",
        "rec_opp_yac",
        "rec_opp_receiving_first_downs",
        "rec_opp_source_path",
        "rec_opp_source_hash",
        "join_status",
        "coverage_status",
        "review_only_status",
    }
    fields = set(sidecar[0].keys()) if sidecar else set()
    duplicate_keys = len(sidecar) - len({(r["player_id"], r["season"], r["position"]) for r in sidecar})
    rows_with_targets = len([r for r in sidecar if r["join_status"] == "JOINED_RECEIVING_TARGET"])
    rows_true_zero = len([r for r in sidecar if r["join_status"].startswith("NO_RECEIVING_TARGET")])
    schema = [
        {
            "artifact": "nflverse_receiving_opportunity",
            "row_count": len(sidecar),
            "required_columns_present": "yes" if required.issubset(fields) else "no",
            "missing_columns": "|".join(sorted(required - fields)),
            "duplicate_keys": duplicate_keys,
            "rows_with_receiving_targets": rows_with_targets,
            "true_zero_no_target_rows": rows_true_zero,
            "review_only_status": "PASS"
            if sidecar and duplicate_keys == 0 and all("REVIEW_ONLY" in r["review_only_status"] and "NOT_MODEL_USE" in r["review_only_status"] for r in sidecar)
            else "FAIL",
        }
    ]
    joined = [r for r in rows if r.get("recopp_rec_opp_wopr") is not None]
    bad_lag = [r for r in joined if int(r["feature_season"]) >= int(r["season"])]
    leakage = [
        {
            "ingredient": "nflverse_receiving_opportunity",
            "joined_rows": len(joined),
            "bad_lag_rows": len(bad_lag),
            "asof_result": "PASS" if not bad_lag else "FAIL",
            "source_use_gate_result": "PASS_REVIEW_ONLY_PUBLIC_NFLVERSE_NO_KEY_NOT_MODEL_USE",
            "rule": "feature_season must be less than target season",
        }
    ]
    return schema, leakage


def stability_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in results:
        for part in str(row.get("stability_by_season", "")).split(";"):
            if ":" not in part:
                continue
            season, value = part.split(":", 1)
            out.append(
                {
                    "run_id": row["run_id"],
                    "test_type": "component"
                    if row["cluster_id"] == "INGREDIENT_ONLY"
                    else ("combination" if "+" in row["ingredient_set"] else "formula_x_ingredient"),
                    "season": season,
                    "spearman": value,
                    "full_history_comparable_note": "partial-window if ffop/ngs ingredient is present",
                }
            )
    return out


def guardrail_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in results:
        out.append(
            {
                "run_id": row["run_id"],
                "ingredient_set": row["ingredient_set"],
                "row_count": row["row_count"],
                "overall_spearman": row["overall_spearman"],
                "pyf_delta": row["pyf_delta"],
                "current_best_delta": row["current_best_delta"],
                "sparse_history_impact": row["sparse_history_impact"],
                "low_games_impact": row["low_games_impact"],
                "age_lifecycle_slice": row["age_lifecycle_slice"],
                "role_slice": row["role_slice"],
                "outlier_flags": row["outlier_flags"],
                "use_decision": row["use_decision"],
            }
        )
    return out


def best(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [r for r in rows if str(r.get("overall_spearman", "")).strip()]
    return max(scored, key=lambda r: float(r["overall_spearman"])) if scored else None


def row_count_above(rows: list[dict[str, Any]], threshold: float) -> int:
    return len([r for r in rows if str(r.get("overall_spearman", "")).strip() and float(r["overall_spearman"]) > threshold])


def make_reports(
    sidecar: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    results: list[dict[str, Any]],
    seeds: list[dict[str, Any]],
) -> None:
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]
    b_component = best(component)
    b_formula = best(formula_x)
    b_combo = best(combos)
    full_history_candidates = [
        r
        for r in results
        if "ffop_" not in r["ingredient_fields"]
        and "ngs_" not in r["ingredient_fields"]
        and "ffop" not in r["ingredient_set"]
        and "ngs" not in r["ingredient_set"]
    ]
    full_history_above = row_count_above(full_history_candidates, CURRENT_BEST_FULL_HISTORY)
    all_above = row_count_above(results, CURRENT_BEST_FULL_HISTORY)
    rec_cov = next(r for r in coverage if r["ingredient"] == "nflverse_receiving_opportunity" and r["position"] == "ALL")
    target_rows = len([r for r in sidecar if r["join_status"] == "JOINED_RECEIVING_TARGET"])
    verdict = "YELLOW_NFLVERSE_RECEIVING_OPPORTUNITY_PARTIAL_WITH_CAVEATS"
    if b_formula and float(b_formula["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY and float(b_formula["pyf_delta"]) > 0:
        verdict = "GREEN_NFLVERSE_RECEIVING_OPPORTUNITY_ADDS_REVIEW_ONLY_SIGNAL"
    if b_formula and float(b_formula["overall_spearman"]) <= CURRENT_BEST_FULL_HISTORY and b_combo and float(b_combo["overall_spearman"]) <= CURRENT_BEST_FULL_HISTORY:
        verdict = "RED_NFLVERSE_RECEIVING_OPPORTUNITY_NO_INCREMENTAL_SIGNAL"
    top_all = sorted([r for r in results if r["overall_spearman"]], key=lambda r: float(r["overall_spearman"]), reverse=True)[:15]
    report = f"""
# nflverse Receiving Opportunity Formula Mart Sidecar V1 Report

## Verdict

`{verdict}`

## Scope

This lane built a review-only receiving opportunity sidecar from local public no-key nflfastR play-by-play parquet files and tested it with the top-3-per-cluster seed policy. It used lagged feature season N to target season N+1 only. It did not mutate the canonical Formula Data Mart, canonical `local_exports`, app/runtime code, rankings, or production model behavior.

## Source And Sidecar

- Source family: public nflverse/nflfastR `play_by_play_YYYY.parquet`.
- Source seasons: `{min(SOURCE_SEASONS)}-{max(SOURCE_SEASONS)}`.
- Target seasons: `{min(int(r['season']) for r in sidecar)}-{max(int(r['season']) for r in sidecar)}`.
- Sidecar rows: `{len(sidecar)}`.
- Rows with prior receiving targets: `{target_rows}`.
- True-zero/no-target rows with source season available: `{len(sidecar) - target_rows}`.
- Receiving opportunity join coverage: `{rec_cov['joined_rows']} / {rec_cov['eligible_rows']}` or `{rec_cov['join_coverage_pct']}`.
- Source files hashed: `{len(sources)}`.

## Ingredients Loaded

- `rec_opp_targets`
- `rec_opp_target_share`
- `rec_opp_air_yards`
- `rec_opp_air_yards_share`
- `rec_opp_wopr`
- `rec_opp_racr`
- `rec_opp_pacr`
- `rec_opp_yac`
- `rec_opp_receiving_first_downs`
- `rec_opp_receiving_epa`

## Tests

- Seed formulas: `{len(seeds)}`.
- Total predeclared results: `{len(results)}`.
- Component tests: `{len(component)}`.
- Formula x ingredient tests: `{len(formula_x)}`.
- Ingredient combination tests: `{len(combos)}`.

## Best Results

- Best component test: `{b_component['run_id'] if b_component else ''}` Spearman `{b_component['overall_spearman'] if b_component else ''}` PYF delta `{b_component['pyf_delta'] if b_component else ''}`.
- Best formula x ingredient test: `{b_formula['run_id'] if b_formula else ''}` Spearman `{b_formula['overall_spearman'] if b_formula else ''}` PYF delta `{b_formula['pyf_delta'] if b_formula else ''}`.
- Best ingredient combination: `{b_combo['run_id'] if b_combo else ''}` Spearman `{b_combo['overall_spearman'] if b_combo else ''}` PYF delta `{b_combo['pyf_delta'] if b_combo else ''}`.

## Top Review-Only Results
"""
    for row in top_all:
        report += f"\n- `{row['run_id']}` Spearman `{row['overall_spearman']}` rows `{row['row_count']}` PYF delta `{row['pyf_delta']}` use `{row['use_decision']}`"
    report += f"""

## Material Beat Of `.755`

- All result rows above `.755`: `{all_above}`.
- Full-history-comparable receiving/EPA-only result rows above `.755`: `{full_history_above}`.

Any result using prior ffopportunity or NGS sidecars is partial-window only and cannot be used to claim a full-history `.755` plateau break.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane. Receiving opportunity is useful as review-only interaction/slice context only unless Master HQ separately approves a later simulation after full-history comparability and ranking-specific gates are satisfied.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
"""
    write_md(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_FORMULA_MART_SIDECAR_V1_REPORT.md", report)
    write_md(
        OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_NEXT_USE_DECISION.md",
        f"""
# Receiving Opportunity Next Use Decision

Decision: `AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT`.

Receiving opportunity was loaded cleanly from public nflverse/nflfastR play-by-play and is valid for lagged review-only Formula Mart sidecar use. The ingredient family may be used for bounded review-only interaction checks and slice/guardrail reporting. It is not approved for production/model-use, direct ranking input, hidden sort logic, or review-only ranking simulation.

Best component: `{b_component['run_id'] if b_component else ''}` Spearman `{b_component['overall_spearman'] if b_component else ''}`.

Best formula x ingredient: `{b_formula['run_id'] if b_formula else ''}` Spearman `{b_formula['overall_spearman'] if b_formula else ''}`.

Best combination: `{b_combo['run_id'] if b_combo else ''}` Spearman `{b_combo['overall_spearman'] if b_combo else ''}`.

Recommended next step: `Ingredient Combination Test Design V1` only if Master HQ wants a bounded design packet that compares full-history sidecars separately from partial-window ffop/NGS combinations. Otherwise continue the sidecar roadmap with FTN/snap-depth/injury/market gates before ranking simulation.
""",
    )
    write_md(
        OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_BLOCKERS_AND_CAVEATS.md",
        """
# Blockers And Caveats

- This is review-only evidence, not production/model-use.
- Same-season/future context was not used; all tests use feature season N to target season N+1.
- Receiving opportunity fields are not true route/YPRR/TPRR receipts and do not reopen route source recovery.
- RACR/PACR are denominator-sensitive and are null when prior air yards are not positive.
- Combo tests using prior ffopportunity or NGS inherit partial-window V2 sidecar caveats.
- Partial-window results cannot be used to claim the full-history `.755` plateau was broken.
- Review-only ranking simulation remains blocked.
""",
    )
    csv_paths = [
        "NFLVERSE_RECEIVING_OPPORTUNITY_SOURCE_LEDGER.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_SCHEMA_VALIDATION.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_JOIN_COVERAGE.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_COMPONENT_TEST_RESULTS.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_FORMULA_X_INGREDIENT_RESULTS.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_INGREDIENT_COMBINATION_RESULTS.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_SLICE_GUARDRAILS.csv",
        "NFLVERSE_RECEIVING_OPPORTUNITY_STABILITY_BY_SEASON.csv",
    ]
    write_md(
        OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_SOURCE_TRACE.md",
        "\n".join(
            [
                "# nflverse Receiving Opportunity Source Trace",
                "",
                f"- Prior EPA lane commit verified by request/preflight context: `{PRIOR_EPA_COMMIT}`",
                f"- Current remote HQ expected and verified before work: `{REMOTE_HEAD}`",
                f"- Public source cache reused read-only: `{SOURCE_CACHE}`",
                f"- Source family: nflverse-data GitHub release `pbp/play_by_play_YYYY.parquet`",
                f"- V2 prior ffop/NGS artifacts used for bounded partial-window combos: `{V2_ARTIFACT}`",
                f"- Prior EPA sidecar used for bounded EPA combo checks: `{EPA_ARTIFACT}`",
                "",
                "## Result CSVs",
                *[f"- `{OUT_DIR / p}`" for p in csv_paths],
            ]
        ),
    )


def main() -> None:
    rows = v2.load_formula_panel()
    sidecar, sources = build_receiving_sidecar(rows)
    raw_cols = [
        "rec_opp_targets",
        "rec_opp_target_share",
        "rec_opp_air_yards",
        "rec_opp_air_yards_share",
        "rec_opp_wopr",
        "rec_opp_racr",
        "rec_opp_pacr",
        "rec_opp_yac",
        "rec_opp_receiving_first_downs",
        "rec_opp_receiving_epa",
    ]
    rec_join = attach_sidecar(rows, sidecar, "recopp", raw_cols)
    prior_join = attach_prior_sidecars(rows)
    seeds = v2.load_seed_registry()
    registry, results = build_tests(rows, seeds)
    coverage = join_coverage(rows)
    schema, leakage = validation_rows(sidecar, rows)
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]

    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_SOURCE_LEDGER.csv", sources)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv", sidecar)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_JOIN_COVERAGE.csv", coverage)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_PREDECLARED_TEST_REGISTRY.csv", registry)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_COMPONENT_TEST_RESULTS.csv", component, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_FORMULA_X_INGREDIENT_RESULTS.csv", formula_x, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_INGREDIENT_COMBINATION_RESULTS.csv", combos, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv", results, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_SLICE_GUARDRAILS.csv", guardrail_rows(results))
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_STABILITY_BY_SEASON.csv", stability_rows(results))
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_SCHEMA_VALIDATION.csv", schema)
    write_csv(OUT_DIR / "NFLVERSE_RECEIVING_OPPORTUNITY_LEAKAGE_ASOF_VALIDATION.csv", leakage)
    make_reports(sidecar, sources, coverage, results, seeds)
    print(
        {
            "sidecar_rows": len(sidecar),
            "tests": len(results),
            "seeds": len(seeds),
            "receiving_joined": rec_join["joined"],
            "ffop_joined": prior_join["ffop_joined"],
            "ngs_joined": prior_join["ngs_joined"],
            "epa_joined": prior_join["epa_joined"],
        }
    )


if __name__ == "__main__":
    main()
