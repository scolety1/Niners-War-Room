from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
POSITIONS = ["QB", "RB", "WR", "TE"]
CURRENT_BEST_FULL_HISTORY = 0.755
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_V2_COMMIT = "8a384e12a36736a27a4365ea3bc6337bfde91825"
PUBLIC_PBP_CACHE = Path(r"C:\NWR_REVIEW\nflverse_epa_opportunity_source_cache_20260709")
V3_HANDOFF_DIR = Path(
    r"C:\NWR\_handoff_unpack\nwr_autonomous_improvement_handoff_v3_20260709"
    r"\nwr_autonomous_improvement_handoff_v3_20260709"
)
V2_ARTIFACT = Path(
    r"C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709"
    r"\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
)
V2_HELPER = (
    Path(__file__).resolve().parents[1]
    / "nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
    / "run_nwr_autonomous_ingredient_upgrade_sequence_v2.py"
)

SOURCE_SEASONS = list(range(2012, 2025))
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


def safe_div(nume: float | None, denom: float | None) -> float | None:
    if nume is None or denom is None or denom == 0:
        return None
    return float(nume) / float(denom)


def clean_float(value: Any) -> float:
    val = num(value)
    return float(val) if val is not None else 0.0


def mode_text(values: pd.Series) -> str:
    clean = [str(v) for v in values.dropna().tolist() if str(v).strip()]
    if not clean:
        return ""
    return Counter(clean).most_common(1)[0][0]


def public_pbp_url(season: int) -> str:
    return f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"


def ensure_public_pbp(season: int) -> tuple[Path, str, int, str]:
    PUBLIC_PBP_CACHE.mkdir(parents=True, exist_ok=True)
    path = PUBLIC_PBP_CACHE / f"play_by_play_{season}.parquet"
    url = public_pbp_url(season)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    file_hash = sha256_file(path)
    return path, url, path.stat().st_size, file_hash


def load_pbp_year(path: Path) -> pd.DataFrame:
    cols = [
        "season",
        "week",
        "season_type",
        "play_type",
        "posteam",
        "passer_player_id",
        "passer_player_name",
        "rusher_player_id",
        "rusher_player_name",
        "receiver_player_id",
        "receiver_player_name",
        "epa",
        "success",
        "air_epa",
        "yac_epa",
        "yards_gained",
    ]
    return pd.read_parquet(path, columns=cols)


def aggregate_role(df: pd.DataFrame, id_col: str, name_col: str, role: str) -> pd.DataFrame:
    if role == "pass":
        mask = df["play_type"].eq("pass") & df[id_col].notna()
        count_name = "pass_dropbacks"
    elif role == "rush":
        mask = df["play_type"].eq("run") & df[id_col].notna()
        count_name = "rush_attempts"
    elif role == "rec":
        mask = df["play_type"].eq("pass") & df[id_col].notna()
        count_name = "targets"
    else:
        raise ValueError(role)
    sub = df.loc[mask].copy()
    if sub.empty:
        return pd.DataFrame(columns=["player_id", "feature_season"])
    sub["player_id"] = sub[id_col].astype(str)
    sub["player_name"] = sub[name_col].astype("string")
    grouped = sub.groupby(["player_id", "season"], dropna=False)
    out = grouped.agg(
        player_name=("player_name", mode_text),
        team=("posteam", mode_text),
        epa=("epa", "sum"),
        plays=("epa", "count"),
        success_sum=("success", "sum"),
        air_epa=("air_epa", "sum"),
        yac_epa=("yac_epa", "sum"),
        yards=("yards_gained", "sum"),
    ).reset_index()
    out = out.rename(
        columns={
            "season": "feature_season",
            "epa": f"{role}_epa_total",
            "plays": count_name,
            "success_sum": f"{role}_success_sum",
            "air_epa": f"{role}_air_epa_total",
            "yac_epa": f"{role}_yac_epa_total",
            "yards": f"{role}_yards_total",
        }
    )
    return out


def build_epa_player_feature_rows() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    source_rows: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        path, url, size, file_hash = ensure_public_pbp(season)
        df = load_pbp_year(path)
        reg = df[df["season_type"].eq("REG")].copy()
        source_rows.append(
            {
                "source_family": "nflfastR_public_play_by_play",
                "feature_season": season,
                "source_url": url,
                "local_cache_path": str(path),
                "sha256": file_hash,
                "file_size": size,
                "raw_rows": len(df),
                "regular_season_rows": len(reg),
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
            }
        )
        pass_df = aggregate_role(reg, "passer_player_id", "passer_player_name", "pass")
        rush_df = aggregate_role(reg, "rusher_player_id", "rusher_player_name", "rush")
        rec_df = aggregate_role(reg, "receiver_player_id", "receiver_player_name", "rec")
        merged = pass_df.merge(rush_df, on=["player_id", "feature_season"], how="outer", suffixes=("_pass", "_rush"))
        merged = merged.merge(rec_df, on=["player_id", "feature_season"], how="outer", suffixes=("", "_rec"))
        merged["source_url"] = url
        merged["source_hash"] = file_hash
        frames.append(merged)
    all_rows = pd.concat(frames, ignore_index=True, sort=False).fillna(0)
    for col in ["player_name", "player_name_pass", "player_name_rush", "team", "team_pass", "team_rush"]:
        if col not in all_rows.columns:
            all_rows[col] = ""
    all_rows["player_name_final"] = all_rows.apply(
        lambda r: next((str(r[c]) for c in ["player_name", "player_name_pass", "player_name_rush"] if str(r.get(c, "")).strip() and str(r.get(c, "")) != "0"), ""),
        axis=1,
    )
    all_rows["team_final"] = all_rows.apply(
        lambda r: next((str(r[c]) for c in ["team", "team_pass", "team_rush"] if str(r.get(c, "")).strip() and str(r.get(c, "")) != "0"), ""),
        axis=1,
    )
    for col in [
        "pass_epa_total",
        "rush_epa_total",
        "rec_epa_total",
        "pass_dropbacks",
        "rush_attempts",
        "targets",
        "pass_success_sum",
        "rush_success_sum",
        "rec_success_sum",
        "pass_air_epa_total",
        "rec_air_epa_total",
        "pass_yac_epa_total",
        "rec_yac_epa_total",
        "pass_yards_total",
        "rush_yards_total",
        "rec_yards_total",
    ]:
        if col not in all_rows.columns:
            all_rows[col] = 0.0
        all_rows[col] = pd.to_numeric(all_rows[col], errors="coerce").fillna(0.0)
    all_rows["epa_total_raw"] = all_rows["pass_epa_total"] + all_rows["rush_epa_total"] + all_rows["rec_epa_total"]
    all_rows["epa_opportunities"] = all_rows["pass_dropbacks"] + all_rows["rush_attempts"] + all_rows["targets"]
    all_rows["epa_success_sum"] = all_rows["pass_success_sum"] + all_rows["rush_success_sum"] + all_rows["rec_success_sum"]
    all_rows["epa_air_total"] = all_rows["pass_air_epa_total"] + all_rows["rec_air_epa_total"]
    all_rows["epa_yac_total"] = all_rows["pass_yac_epa_total"] + all_rows["rec_yac_epa_total"]
    all_rows["epa_yards_total"] = all_rows["pass_yards_total"] + all_rows["rush_yards_total"] + all_rows["rec_yards_total"]
    all_rows["epa_per_opportunity"] = all_rows.apply(lambda r: safe_div(r["epa_total_raw"], r["epa_opportunities"]), axis=1)
    all_rows["epa_success_rate"] = all_rows.apply(lambda r: safe_div(r["epa_success_sum"], r["epa_opportunities"]), axis=1)
    all_rows["pass_epa_per_dropback"] = all_rows.apply(lambda r: safe_div(r["pass_epa_total"], r["pass_dropbacks"]), axis=1)
    all_rows["rush_epa_per_carry"] = all_rows.apply(lambda r: safe_div(r["rush_epa_total"], r["rush_attempts"]), axis=1)
    all_rows["rec_epa_per_target"] = all_rows.apply(lambda r: safe_div(r["rec_epa_total"], r["targets"]), axis=1)
    return all_rows, source_rows


def build_epa_sidecar(panel_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    features, sources = build_epa_player_feature_rows()
    lookup = {
        (str(r["player_id"]), int(r["feature_season"])): r
        for r in features.to_dict("records")
        if clean_float(r.get("epa_opportunities")) > 0
    }
    sidecar: list[dict[str, Any]] = []
    for row in panel_rows:
        key = (str(row["player_id"]), int(row["feature_season"]))
        feature = lookup.get(key)
        if not feature:
            continue
        sidecar.append(
            {
                "season": int(row["season"]),
                "feature_season": int(row["feature_season"]),
                "player_id": str(row["player_id"]),
                "player_name": row.get("player_name") or feature.get("player_name_final") or "",
                "position": str(row["position"]),
                "team": feature.get("team_final") or "",
                "epa_total_raw": fmt(num(feature.get("epa_total_raw")), 6),
                "epa_per_opportunity": fmt(num(feature.get("epa_per_opportunity")), 6),
                "epa_success_rate": fmt(num(feature.get("epa_success_rate")), 6),
                "epa_opportunities": fmt(num(feature.get("epa_opportunities")), 3),
                "pass_epa_total": fmt(num(feature.get("pass_epa_total")), 6),
                "pass_epa_per_dropback": fmt(num(feature.get("pass_epa_per_dropback")), 6),
                "pass_dropbacks": fmt(num(feature.get("pass_dropbacks")), 3),
                "rush_epa_total": fmt(num(feature.get("rush_epa_total")), 6),
                "rush_epa_per_carry": fmt(num(feature.get("rush_epa_per_carry")), 6),
                "rush_attempts": fmt(num(feature.get("rush_attempts")), 3),
                "rec_epa_total": fmt(num(feature.get("rec_epa_total")), 6),
                "rec_epa_per_target": fmt(num(feature.get("rec_epa_per_target")), 6),
                "targets": fmt(num(feature.get("targets")), 3),
                "epa_air_total": fmt(num(feature.get("epa_air_total")), 6),
                "epa_yac_total": fmt(num(feature.get("epa_yac_total")), 6),
                "epa_yards_total": fmt(num(feature.get("epa_yards_total")), 3),
                "source_url": feature.get("source_url") or "",
                "source_hash": feature.get("source_hash") or "",
                "join_key": "player_id + feature_season + position",
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "asof_status": "PASS_LAGGED_N_TO_N_PLUS_1",
                "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
                "caveat": "public_nflfastR_pbp_aggregated_regular_season_lagged_review_only",
            }
        )
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


def load_prior_sidecar(name: str) -> list[dict[str, Any]]:
    path = V2_ARTIFACT / name
    if not path.exists():
        raise RuntimeError(f"Missing prior V2 sidecar: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def attach_prior_v2_sidecars(rows: list[dict[str, Any]]) -> dict[str, int]:
    ff_rows = load_prior_sidecar("FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv")
    ngs_rows = load_prior_sidecar("NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv")
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
    return {"ffop_joined": ff["joined"], "ngs_joined": ngs["joined"]}


def denominator(rows: list[dict[str, Any]], source_seasons: set[int], positions: set[str] | None = None) -> int:
    if positions is None:
        positions = set(POSITIONS)
    return len([r for r in rows if int(r["feature_season"]) in source_seasons and str(r["position"]) in positions])


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


def register(registry: list[dict[str, Any]], run_id: str, test_type: str, formula_id: str, cluster_id: str, base_formula: str, ingredient_set: str, fields: str, weighting: str) -> None:
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
        }
    )


def build_tests(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    v2.materialize_formula_scores(rows, seeds)
    registry: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    source_seasons = set(SOURCE_SEASONS)
    all_positions = set(POSITIONS)
    epa_denom = denominator(rows, source_seasons, all_positions)
    component_specs = [
        ("INGREDIENT_ONLY_EPA_TOTAL", "epa_total_raw", "nflverse_epa_epa_total_raw_pct", "nflverse_epa_epa_total_raw"),
        ("INGREDIENT_ONLY_EPA_PER_OPPORTUNITY", "epa_per_opportunity", "nflverse_epa_epa_per_opportunity_pct", "nflverse_epa_epa_per_opportunity"),
        ("INGREDIENT_ONLY_EPA_SUCCESS_RATE", "epa_success_rate", "nflverse_epa_epa_success_rate_pct", "nflverse_epa_epa_success_rate"),
        ("INGREDIENT_ONLY_PASS_EPA_PER_DROPBACK", "pass_epa_per_dropback", "nflverse_epa_pass_epa_per_dropback_pct", "nflverse_epa_pass_epa_per_dropback"),
        ("INGREDIENT_ONLY_RUSH_EPA_PER_CARRY", "rush_epa_per_carry", "nflverse_epa_rush_epa_per_carry_pct", "nflverse_epa_rush_epa_per_carry"),
        ("INGREDIENT_ONLY_REC_EPA_PER_TARGET", "rec_epa_per_target", "nflverse_epa_rec_epa_per_target_pct", "nflverse_epa_rec_epa_per_target"),
    ]
    for run_id, raw_field, score_col, field_col in component_specs:
        selected = selected_rows(rows, all_positions, [score_col])
        register(registry, run_id, "ingredient_alone", run_id, "INGREDIENT_ONLY", "none", "nflverse_epa_opportunity", raw_field, "ingredient percentile rank only")
        results.append(
            v2.result_row(
                run_id,
                run_id,
                "INGREDIENT_ONLY",
                "none",
                "nflverse_epa_opportunity",
                raw_field,
                "QB/RB/WR/TE",
                selected,
                score_col,
                epa_denom,
                notes="EPA/opportunity ingredient alone; public nflfastR PBP lagged N-to-N+1 review-only.",
            )
        )
    formula_x_specs = [
        ("EPA_TOTAL_PCT05", "nflverse_epa_epa_total_raw_pct", 0.05),
        ("EPA_TOTAL_PCT10", "nflverse_epa_epa_total_raw_pct", 0.10),
        ("EPA_PER_OPPORTUNITY_PCT05", "nflverse_epa_epa_per_opportunity_pct", 0.05),
        ("EPA_SUCCESS_PCT05", "nflverse_epa_epa_success_rate_pct", 0.05),
    ]
    for seed in seeds:
        seed_col = f"formula__{seed['candidate_id']}__pct"
        seed_rows = selected_rows(rows, v2.scope_positions(seed["position_scope"]), [seed_col])
        seed_metrics = v2.metrics_for_run(seed_rows, seed_col)
        for suffix, ingredient_col, weight in formula_x_specs:
            score_col = f"{seed_col}__{suffix}"
            materialize_combo_score(rows, score_col, [(seed_col, 1.0 - weight), (ingredient_col, weight)])
            selected = selected_rows(rows, v2.scope_positions(seed["position_scope"]), [score_col])
            run_id = f"{seed['candidate_id']}__PLUS_{suffix}"
            register(
                registry,
                run_id,
                "formula_x_ingredient",
                seed["candidate_id"],
                seed["cluster_id"],
                seed["formula_definition"],
                "nflverse_epa_opportunity",
                ingredient_col.replace("nflverse_epa_", ""),
                f"seed_percentile={1.0 - weight:.2f};ingredient_percentile={weight:.2f}",
            )
            results.append(
                v2.result_row(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "nflverse_epa_opportunity",
                    ingredient_col.replace("nflverse_epa_", ""),
                    seed["position_scope"],
                    selected,
                    score_col,
                    epa_denom,
                    seed_metrics=seed_metrics,
                    notes="Fixed predeclared EPA/opportunity additive variant; no dynamic tuning.",
                )
            )
    combo_specs = [
        ("EPA_FFOP_PCT05_05", [("nflverse_epa_epa_total_raw_pct", 0.05), ("ffop_ffop_xfp_total_pct", 0.05)]),
        ("EPA_NGS_PCT05_05", [("nflverse_epa_epa_total_raw_pct", 0.05), ("ngs_ngs_position_signal_raw_pct", 0.05)]),
        ("EPA_FFOP_NGS_PCT04_04_02", [("nflverse_epa_epa_total_raw_pct", 0.04), ("ffop_ffop_xfp_total_pct", 0.04), ("ngs_ngs_position_signal_raw_pct", 0.02)]),
    ]
    for seed in seeds:
        seed_col = f"formula__{seed['candidate_id']}__pct"
        seed_rows = selected_rows(rows, v2.scope_positions(seed["position_scope"]), [seed_col])
        seed_metrics = v2.metrics_for_run(seed_rows, seed_col)
        for suffix, ingredients in combo_specs:
            total_ing_weight = sum(weight for _, weight in ingredients)
            score_col = f"{seed_col}__{suffix}"
            materialize_combo_score(rows, score_col, [(seed_col, 1.0 - total_ing_weight), *ingredients])
            selected = selected_rows(rows, v2.scope_positions(seed["position_scope"]), [score_col])
            run_id = f"{seed['candidate_id']}__PLUS_{suffix}"
            fields = "|".join(col for col, _ in ingredients)
            register(
                registry,
                run_id,
                "ingredient_combination",
                seed["candidate_id"],
                seed["cluster_id"],
                seed["formula_definition"],
                "nflverse_epa_opportunity+prior_v2_sidecars",
                fields,
                f"seed_percentile={1.0 - total_ing_weight:.2f};"
                + ";".join(f"{col}={weight:.2f}" for col, weight in ingredients),
            )
            results.append(
                v2.result_row(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "nflverse_epa_opportunity+prior_v2_sidecars",
                    fields,
                    seed["position_scope"],
                    selected,
                    score_col,
                    epa_denom,
                    seed_metrics=seed_metrics,
                    notes="Bounded predeclared EPA plus prior V2 sidecar combination; partial-window caveats apply where prior sidecars are required.",
                )
            )
    return registry, results


def join_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for ingredient, prefix, seasons in [
        ("nflverse_epa_opportunity", "nflverse_epa_epa_total_raw", set(SOURCE_SEASONS)),
        ("ffopportunity_prior_v2", "ffop_ffop_xfp_total", {2021, 2022, 2023, 2024}),
        ("nflverse_ngs_prior_v2", "ngs_ngs_position_signal_raw", {2021, 2022, 2023, 2024}),
    ]:
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
        "position",
        "epa_total_raw",
        "epa_per_opportunity",
        "epa_success_rate",
        "source_url",
        "source_hash",
        "source_gate_status",
        "asof_status",
        "review_only_status",
    }
    fields = set(sidecar[0].keys()) if sidecar else set()
    duplicate_keys = len(sidecar) - len({(r["player_id"], r["season"], r["position"]) for r in sidecar})
    schema = [
        {
            "artifact": "nflverse_epa_opportunity",
            "row_count": len(sidecar),
            "required_columns_present": "yes" if required.issubset(fields) else "no",
            "missing_columns": "|".join(sorted(required - fields)),
            "duplicate_keys": duplicate_keys,
            "review_only_status": "PASS"
            if sidecar and duplicate_keys == 0 and all("REVIEW_ONLY" in r["review_only_status"] and "NOT_MODEL_USE" in r["review_only_status"] for r in sidecar)
            else "FAIL",
        }
    ]
    joined = [r for r in rows if r.get("nflverse_epa_epa_total_raw") is not None]
    bad_lag = [r for r in joined if int(r["feature_season"]) >= int(r["season"])]
    leakage = [
        {
            "ingredient": "nflverse_epa_opportunity",
            "joined_rows": len(joined),
            "bad_lag_rows": len(bad_lag),
            "asof_result": "PASS" if not bad_lag else "FAIL",
            "rule": "feature_season must be less than target season",
        }
    ]
    return schema, leakage


def best(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [r for r in rows if str(r.get("overall_spearman", "")).strip()]
    return max(scored, key=lambda r: float(r["overall_spearman"])) if scored else None


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
    top_all = sorted([r for r in results if r["overall_spearman"]], key=lambda r: float(r["overall_spearman"]), reverse=True)[:12]
    b_component = best(component)
    b_formula = best(formula_x)
    b_combo = best(combos)
    above = [r for r in results if r["overall_spearman"] and float(r["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY]
    epa_only_above = [
        r
        for r in formula_x
        if r["overall_spearman"] and float(r["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY
    ]
    partial_combo_above = [
        r
        for r in combos
        if r["overall_spearman"] and float(r["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY
    ]
    epa_cov = next(r for r in coverage if r["ingredient"] == "nflverse_epa_opportunity" and r["position"] == "ALL")
    max_target_season = max(int(r["season"]) for r in sidecar) if sidecar else ""
    min_target_season = min(int(r["season"]) for r in sidecar) if sidecar else ""
    verdict = "YELLOW_NFLVERSE_EPA_OPPORTUNITY_PARTIAL_WITH_CAVEATS"
    if b_formula and float(b_formula["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY and b_formula["pyf_delta"] and float(b_formula["pyf_delta"]) > 0:
        verdict = "GREEN_NFLVERSE_EPA_OPPORTUNITY_ADDITIVE_REVIEW_ONLY_PARTIAL"
    report = f"""
# nflverse EPA / Opportunity Formula Mart Sidecar V1 Report

## Verdict

`{verdict}`

## Scope

This lane built a review-only EPA/opportunity sidecar from public no-key nflfastR play-by-play parquet files and tested it with the V3 top-3-per-cluster seed policy. It did not rerun the completed ffopportunity/NGS sidecar builds; prior V2 sidecar outputs were used only for bounded combination tests.

## Source And Sidecar

- Source family: public nflverse/nflfastR `play_by_play_YYYY.parquet`.
- Source seasons: `{min(SOURCE_SEASONS)}-{max(SOURCE_SEASONS)}`.
- Sidecar rows: `{len(sidecar)}`.
- Target seasons covered: `{min_target_season}-{max_target_season}`.
- EPA join coverage: `{epa_cov['joined_rows']} / {epa_cov['eligible_rows']}` or `{epa_cov['join_coverage_pct']}`.
- Source files hashed: `{len(sources)}`.

## Tests

- Seed formulas: `{len(seeds)}`.
- Total predeclared tests: `{len(results)}`.
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
        report += f"\n- `{row['run_id']}` `{row['overall_spearman']}` rows `{row['row_count']}` use `{row['use_decision']}`"
    report += f"""

## Material Beat Of `.755`

Rows above `.755`: `{len(above)}`.

- EPA-only formula x ingredient rows above `.755`: `{len(epa_only_above)}`.
- Partial-window EPA + prior V2 sidecar combination rows above `.755`: `{len(partial_combo_above)}`.

No EPA-only near-full-history-comparable result materially beat `.755`. The `.755+` rows are review-only partial-window combinations because they require prior V2 ffopportunity or NGS sidecars, whose target window is lagged `2022-2025`.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane. The only `.755+` results are partial-window combinations, not full-history-comparable evidence.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
"""
    write_md(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_FORMULA_MART_SIDECAR_V1_REPORT.md", report)
    csv_paths = [
        "NFLVERSE_EPA_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv",
        "NFLVERSE_EPA_OPPORTUNITY_COMPONENT_TEST_RESULTS.csv",
        "NFLVERSE_EPA_OPPORTUNITY_FORMULA_X_INGREDIENT_RESULTS.csv",
        "NFLVERSE_EPA_OPPORTUNITY_INGREDIENT_COMBINATION_RESULTS.csv",
        "NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv",
    ]
    write_md(
        OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_SOURCE_TRACE.md",
        "\n".join(
            [
                "# nflverse EPA / Opportunity Source Trace",
                "",
                f"- V3 handoff: `{V3_HANDOFF_DIR}`",
                f"- Prior V2 commit verified by lane preflight: `{PRIOR_V2_COMMIT}`",
                f"- Prior V2 artifact used for ffop/NGS combo inputs: `{V2_ARTIFACT}`",
                f"- Public source cache: `{PUBLIC_PBP_CACHE}`",
                f"- Public source family: nflverse-data GitHub release `pbp/play_by_play_YYYY.parquet`",
                f"- Remote HQ expected and verified before worktree creation: `{REMOTE_HEAD}`",
                "",
                "## Result CSVs",
                *[f"- `{OUT_DIR / p}`" for p in csv_paths],
            ]
        ),
    )
    write_md(
        OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_BLOCKERS_AND_GATES.md",
        """
# Blockers And Gates

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changes remain blocked.
- Source promotion remains blocked.
- No SportsDataIO, paid API, API-key, PFF Elusive Rating, or `nwr_elusive_proxy_review_only` source was used.
- Raw public nflfastR play-by-play parquet files were cached outside the repo under `C:\\NWR_REVIEW`; raw source files were not committed.
- Combination tests involving ffopportunity or NGS inherit the prior V2 partial-window caveat.
""",
    )
    write_md(
        OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_NEXT_STEP_RECOMMENDATION.md",
        """
# Next Step Recommendation

Recommended next lane: `nflverse Receiving Opportunity Formula Mart Sidecar V1`.

Reason: EPA/opportunity can be cleanly loaded as review-only data, but receiving opportunity fields such as target share, air-yards share, WOPR, RACR, and PACR remain a separate high-value source family. Ranking simulation should wait for Master HQ review and broader sidecar context.
""",
    )


def main() -> None:
    rows = v2.load_formula_panel()
    epa_sidecar, epa_sources = build_epa_sidecar(rows)
    epa_raw_cols = [
        "epa_total_raw",
        "epa_per_opportunity",
        "epa_success_rate",
        "pass_epa_per_dropback",
        "rush_epa_per_carry",
        "rec_epa_per_target",
        "epa_opportunities",
    ]
    epa_join = attach_sidecar(rows, epa_sidecar, "nflverse_epa", epa_raw_cols)
    prior_join = attach_prior_v2_sidecars(rows)
    seeds = v2.load_seed_registry()
    registry, results = build_tests(rows, seeds)
    coverage = join_coverage(rows)
    schema, leakage = validation_rows(epa_sidecar, rows)
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]

    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_SOURCE_LEDGER.csv", epa_sources)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv", epa_sidecar)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_JOIN_COVERAGE.csv", coverage)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_PREDECLARED_TEST_REGISTRY.csv", registry)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_COMPONENT_TEST_RESULTS.csv", component, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_FORMULA_X_INGREDIENT_RESULTS.csv", formula_x, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_INGREDIENT_COMBINATION_RESULTS.csv", combos, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv", results, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_SCHEMA_VALIDATION.csv", schema)
    write_csv(OUT_DIR / "NFLVERSE_EPA_OPPORTUNITY_LEAKAGE_ASOF_VALIDATION.csv", leakage)
    make_reports(epa_sidecar, epa_sources, coverage, results, seeds)
    print(
        {
            "epa_sidecar_rows": len(epa_sidecar),
            "tests": len(results),
            "seeds": len(seeds),
            "epa_joined": epa_join["joined"],
            "ffop_joined": prior_join["ffop_joined"],
            "ngs_joined": prior_join["ngs_joined"],
        }
    )


if __name__ == "__main__":
    main()
