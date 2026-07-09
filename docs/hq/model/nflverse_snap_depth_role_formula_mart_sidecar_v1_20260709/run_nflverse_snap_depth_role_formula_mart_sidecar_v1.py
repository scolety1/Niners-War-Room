from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
POSITIONS = ["QB", "RB", "WR", "TE"]
CURRENT_BEST_FULL_HISTORY = 0.755
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_RECEIVING_COMMIT = "30ec8d23c8e82d2dd28a6c7b67d7391b1ca8206b"
SOURCE_CACHE = Path(r"C:\NWR_REVIEW\nflverse_snap_depth_role_source_cache_20260709")
SOURCE_SEASONS = list(range(2012, 2025))
SNAP_SEASONS_WITH_DATA = set(range(2013, 2025))

V2_ARTIFACT = Path(__file__).resolve().parents[1] / "nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
EPA_ARTIFACT = Path(__file__).resolve().parents[1] / "nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709"
REC_ARTIFACT = Path(__file__).resolve().parents[1] / "nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709"
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


def mode_text(values: pd.Series) -> str:
    clean = [str(v) for v in values.dropna().tolist() if str(v).strip() and str(v) != "nan"]
    if not clean:
        return ""
    return Counter(clean).most_common(1)[0][0]


def public_url(kind: str, season: int | None = None) -> str:
    if kind == "players":
        return "https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet"
    if kind == "snap_counts":
        return f"https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.parquet"
    if kind == "depth_charts":
        return f"https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_{season}.parquet"
    raise ValueError(kind)


def local_source_path(kind: str, season: int | None = None) -> Path:
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    if kind == "players":
        return SOURCE_CACHE / "players.parquet"
    return SOURCE_CACHE / f"{kind}_{season}.parquet"


def ensure_source(kind: str, season: int | None = None) -> tuple[Path, str, int, str]:
    path = local_source_path(kind, season)
    url = public_url(kind, season)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    return path, url, path.stat().st_size, sha256_file(path)


def load_players() -> tuple[pd.DataFrame, dict[str, dict[str, str]], dict[str, Any]]:
    path, url, size, file_hash = ensure_source("players")
    df = pd.read_parquet(path)
    pfr = df[df["pfr_id"].notna() & df["gsis_id"].notna()].copy()
    pfr["pfr_id"] = pfr["pfr_id"].astype(str)
    pfr["gsis_id"] = pfr["gsis_id"].astype(str)
    lookup = {
        str(r["pfr_id"]): {
            "player_id": str(r["gsis_id"]),
            "player_name": str(r.get("display_name") or ""),
            "position": str(r.get("position") or ""),
        }
        for r in pfr.to_dict("records")
    }
    source = {
        "source_family": "nflverse_players_identity_crosswalk",
        "feature_season": "static",
        "source_url": url,
        "local_cache_path": str(path),
        "sha256": file_hash,
        "file_size": size,
        "raw_rows": len(df),
        "regular_season_rows": "",
        "mapped_rows": len(lookup),
        "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
        "asof_status": "STATIC_IDENTITY_CROSSWALK_FOR_LAGGED_JOIN",
    }
    return df, lookup, source


def aggregate_snap_features(pfr_lookup: dict[str, dict[str, str]]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        path, url, size, file_hash = ensure_source("snap_counts", season)
        df = pd.read_parquet(path)
        reg = df[df["game_type"].astype(str).eq("REG")].copy() if "game_type" in df.columns else df.copy()
        if not reg.empty:
            reg["pfr_player_id"] = reg["pfr_player_id"].astype(str)
            reg["player_id"] = reg["pfr_player_id"].map(lambda x: pfr_lookup.get(x, {}).get("player_id"))
            reg["mapped_player_name"] = reg["pfr_player_id"].map(lambda x: pfr_lookup.get(x, {}).get("player_name", ""))
            mapped = reg[reg["player_id"].notna()].copy()
            for col in ["offense_snaps", "offense_pct"]:
                mapped[col] = pd.to_numeric(mapped[col], errors="coerce").fillna(0.0)
            mapped["offense_snap_game"] = (mapped["offense_snaps"] > 0).astype(float)
            mapped["full_snap_game"] = (mapped["offense_pct"] >= 0.70).astype(float)
            mapped["late_season"] = (pd.to_numeric(mapped["week"], errors="coerce") >= 10).astype(float)
            season_rows = (
                mapped.groupby(["player_id", "season"], dropna=False)
                .agg(
                    player_name=("mapped_player_name", mode_text),
                    team=("team", mode_text),
                    source_position=("position", mode_text),
                    snap_offensive_snaps=("offense_snaps", "sum"),
                    snap_offensive_snap_share=("offense_pct", "mean"),
                    snap_games_with_offensive_snaps=("offense_snap_game", "sum"),
                    snap_games_listed=("offense_snaps", "count"),
                    snap_full_snap_games=("full_snap_game", "sum"),
                    snap_late_season_share=("offense_pct", lambda s: s[mapped.loc[s.index, "late_season"].eq(1)].mean() if any(mapped.loc[s.index, "late_season"].eq(1)) else None),
                    snap_early_season_share=("offense_pct", lambda s: s[mapped.loc[s.index, "late_season"].eq(0)].mean() if any(mapped.loc[s.index, "late_season"].eq(0)) else None),
                )
                .reset_index()
                .rename(columns={"season": "feature_season"})
            )
            season_rows["snap_low_snap_flag"] = (
                (season_rows["snap_games_with_offensive_snaps"] > 0)
                & (season_rows["snap_offensive_snap_share"] < 0.35)
            ).astype(float)
            season_rows["snap_not_low_snap_score"] = 1.0 - season_rows["snap_low_snap_flag"]
            season_rows["snap_share_trend"] = season_rows["snap_late_season_share"].fillna(0.0) - season_rows["snap_early_season_share"].fillna(0.0)
            season_rows["snap_role_score"] = (
                season_rows["snap_offensive_snap_share"].clip(lower=0.0, upper=1.0) * 0.70
                + (season_rows["snap_games_with_offensive_snaps"] / 17.0).clip(lower=0.0, upper=1.0) * 0.30
            )
            season_rows["source_url"] = url
            season_rows["source_path"] = str(path)
            season_rows["source_hash"] = file_hash
            frames.append(season_rows)
        sources.append(
            {
                "source_family": "nflverse_snap_counts",
                "feature_season": season,
                "source_url": url,
                "local_cache_path": str(path),
                "sha256": file_hash,
                "file_size": size,
                "raw_rows": len(df),
                "regular_season_rows": len(reg),
                "mapped_rows": 0 if reg.empty else int(reg["pfr_player_id"].map(lambda x: x in pfr_lookup).sum()),
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "asof_status": "PASS_LAGGED_CLOSED_FEATURE_SEASON_ONLY",
            }
        )
    if not frames:
        return pd.DataFrame(), sources
    return pd.concat(frames, ignore_index=True, sort=False), sources


def depth_rank_score(rank: float | None) -> float:
    if rank is None or rank <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 / float(rank)))


def role_tier(starter_weeks: float, backup_weeks: float, total_weeks: float, best_rank: float | None) -> str:
    if total_weeks <= 0:
        return "NO_DEPTH_RECORD"
    starter_ratio = starter_weeks / total_weeks if total_weeks else 0.0
    if starter_weeks >= 8 or starter_ratio >= 0.50:
        return "PRIMARY_STARTER"
    if starter_weeks > 0:
        return "PARTIAL_STARTER"
    if best_rank is not None and best_rank <= 2:
        return "TOP_BACKUP"
    if backup_weeks > 0:
        return "DEPTH_BACKUP"
    return "DEPTH_LISTED"


def aggregate_depth_features() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        path, url, size, file_hash = ensure_source("depth_charts", season)
        df = pd.read_parquet(path)
        reg = df[df["game_type"].astype(str).eq("REG")].copy() if "game_type" in df.columns else df.copy()
        if not reg.empty:
            reg = reg[reg["gsis_id"].notna()].copy()
            reg["player_id"] = reg["gsis_id"].astype(str)
            reg["depth_team_num"] = pd.to_numeric(reg["depth_team"], errors="coerce")
            offense = reg[reg["formation"].astype(str).str.lower().eq("offense")].copy()
            fantasyish = offense[offense["position"].astype(str).isin(POSITIONS)].copy()
            if not fantasyish.empty:
                fantasyish["starter_week"] = (fantasyish["depth_team_num"] == 1).astype(float)
                fantasyish["backup_week"] = (fantasyish["depth_team_num"] > 1).astype(float)
                fantasyish["week_key"] = fantasyish["week"].astype(str) + "_" + fantasyish["club_code"].astype(str)
                grouped = fantasyish.groupby(["player_id", "season"], dropna=False)
                season_rows = grouped.agg(
                    player_name=("full_name", mode_text),
                    team=("club_code", mode_text),
                    source_position=("position", mode_text),
                    depth_primary_depth_rank=("depth_team_num", lambda s: Counter([int(v) for v in s.dropna().tolist()]).most_common(1)[0][0] if len(s.dropna()) else None),
                    depth_best_depth_rank=("depth_team_num", "min"),
                    depth_worst_depth_rank=("depth_team_num", "max"),
                    depth_weeks_listed=("week_key", "nunique"),
                    depth_weeks_as_starter=("starter_week", "sum"),
                    depth_weeks_as_backup=("backup_week", "sum"),
                    depth_positions=("depth_position", lambda s: "|".join(sorted({str(v) for v in s.dropna().tolist()}))),
                ).reset_index().rename(columns={"season": "feature_season"})
                season_rows["depth_role_change_flag"] = (
                    season_rows["depth_best_depth_rank"] != season_rows["depth_worst_depth_rank"]
                ).astype(float)
                season_rows["depth_role_tier"] = season_rows.apply(
                    lambda r: role_tier(
                        clean_float(r["depth_weeks_as_starter"]),
                        clean_float(r["depth_weeks_as_backup"]),
                        clean_float(r["depth_weeks_listed"]),
                        num(r["depth_best_depth_rank"]),
                    ),
                    axis=1,
                )
                season_rows["depth_role_score"] = season_rows.apply(
                    lambda r: min(
                        1.0,
                        (
                            (clean_float(r["depth_weeks_as_starter"]) / max(clean_float(r["depth_weeks_listed"]), 1.0)) * 0.75
                            + depth_rank_score(num(r["depth_best_depth_rank"])) * 0.25
                        ),
                    ),
                    axis=1,
                )
                season_rows["depth_stability_score"] = 1.0 - season_rows["depth_role_change_flag"]
                season_rows["source_url"] = url
                season_rows["source_path"] = str(path)
                season_rows["source_hash"] = file_hash
                frames.append(season_rows)
        sources.append(
            {
                "source_family": "nflverse_depth_charts",
                "feature_season": season,
                "source_url": url,
                "local_cache_path": str(path),
                "sha256": file_hash,
                "file_size": size,
                "raw_rows": len(df),
                "regular_season_rows": len(reg),
                "mapped_rows": int(reg["gsis_id"].notna().sum()) if "gsis_id" in reg.columns else 0,
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "asof_status": "PASS_LAGGED_CLOSED_FEATURE_SEASON_ONLY",
            }
        )
    if not frames:
        return pd.DataFrame(), sources
    return pd.concat(frames, ignore_index=True, sort=False), sources


def source_map(sources: list[dict[str, Any]], family: str) -> dict[int, dict[str, str]]:
    out: dict[int, dict[str, str]] = {}
    for row in sources:
        if row["source_family"] == family and str(row["feature_season"]).isdigit():
            out[int(row["feature_season"])] = {
                "path": str(row["local_cache_path"]),
                "url": str(row["source_url"]),
                "hash": str(row["sha256"]),
            }
    return out


def value_or_none(row: dict[str, Any] | None, key: str) -> float | None:
    if not row:
        return None
    return num(row.get(key))


def build_sidecar(panel_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _players, pfr_lookup, player_source = load_players()
    snap, snap_sources = aggregate_snap_features(pfr_lookup)
    depth, depth_sources = aggregate_depth_features()
    all_sources = [player_source, *snap_sources, *depth_sources]
    snap_lookup = {
        (str(r["player_id"]), int(r["feature_season"])): r
        for r in snap.to_dict("records")
    } if not snap.empty else {}
    depth_lookup = {
        (str(r["player_id"]), int(r["feature_season"])): r
        for r in depth.to_dict("records")
    } if not depth.empty else {}
    snap_sources_by_season = source_map(all_sources, "nflverse_snap_counts")
    depth_sources_by_season = source_map(all_sources, "nflverse_depth_charts")
    sidecar: list[dict[str, Any]] = []
    for row in panel_rows:
        feature_season = int(row["feature_season"])
        key = (str(row["player_id"]), feature_season)
        srow = snap_lookup.get(key)
        drow = depth_lookup.get(key)
        snap_source = snap_sources_by_season.get(feature_season, {})
        depth_source = depth_sources_by_season.get(feature_season, {})
        snap_source_has_rows = feature_season in SNAP_SEASONS_WITH_DATA
        snap_joined = srow is not None
        depth_joined = drow is not None
        if snap_joined and depth_joined:
            join_status = "JOINED_SNAP_AND_DEPTH"
        elif snap_joined:
            join_status = "JOINED_SNAP_ONLY"
        elif depth_joined:
            join_status = "JOINED_DEPTH_ONLY"
        elif not snap_source_has_rows:
            join_status = "SNAP_SOURCE_EMPTY_DEPTH_MISSING"
        else:
            join_status = "NO_SNAP_DEPTH_RECORD_SOURCE_AVAILABLE"
        snap_share = value_or_none(srow, "snap_offensive_snap_share")
        snap_games = value_or_none(srow, "snap_games_with_offensive_snaps")
        snap_role_score = value_or_none(srow, "snap_role_score")
        if snap_source_has_rows and snap_role_score is None:
            snap_role_score = 0.0
        depth_role_score = value_or_none(drow, "depth_role_score")
        if depth_role_score is None:
            depth_role_score = 0.0
        snap_depth_role_score = None
        if snap_role_score is not None:
            snap_depth_role_score = (snap_role_score * 0.55) + (depth_role_score * 0.45)
        elif depth_role_score is not None:
            snap_depth_role_score = depth_role_score
        low_snap = value_or_none(srow, "snap_low_snap_flag")
        if snap_source_has_rows and low_snap is None:
            low_snap = 1.0
        not_low = None if low_snap is None else 1.0 - low_snap
        depth_change = value_or_none(drow, "depth_role_change_flag")
        depth_stability = 0.0 if drow is None else (1.0 - clean_float(depth_change))
        source_paths = "|".join(
            p for p in [snap_source.get("path", ""), depth_source.get("path", ""), str(local_source_path("players"))] if p
        )
        source_hashes = "|".join(
            h for h in [snap_source.get("hash", ""), depth_source.get("hash", ""), sha256_file(local_source_path("players"))] if h
        )
        sidecar.append(
            {
                "season": int(row["season"]),
                "feature_season": feature_season,
                "player_id": str(row["player_id"]),
                "player_name": row.get("player_name") or (srow or drow or {}).get("player_name", ""),
                "position": str(row["position"]),
                "team": (srow or drow or {}).get("team", ""),
                "snap_offensive_snaps": fmt(value_or_none(srow, "snap_offensive_snaps"), 3),
                "snap_offensive_snap_share": fmt(snap_share, 6),
                "snap_games_with_offensive_snaps": fmt(snap_games, 3),
                "snap_low_snap_flag": fmt(low_snap, 3),
                "snap_not_low_snap_score": fmt(not_low, 6),
                "snap_role_score": fmt(snap_role_score, 6),
                "snap_share_trend": fmt(value_or_none(srow, "snap_share_trend"), 6),
                "depth_primary_depth_rank": fmt(value_or_none(drow, "depth_primary_depth_rank"), 3),
                "depth_best_depth_rank": fmt(value_or_none(drow, "depth_best_depth_rank"), 3),
                "depth_weeks_as_starter": fmt(value_or_none(drow, "depth_weeks_as_starter"), 3),
                "depth_weeks_as_backup": fmt(value_or_none(drow, "depth_weeks_as_backup"), 3),
                "depth_weeks_listed": fmt(value_or_none(drow, "depth_weeks_listed"), 3),
                "depth_role_tier": (drow or {}).get("depth_role_tier", "NO_DEPTH_RECORD"),
                "depth_role_change_flag": fmt(depth_change, 3),
                "depth_role_score": fmt(depth_role_score, 6),
                "depth_stability_score": fmt(depth_stability, 6),
                "snap_depth_role_score": fmt(snap_depth_role_score, 6),
                "snap_depth_source_path": source_paths,
                "snap_depth_source_hash": source_hashes,
                "join_status": join_status,
                "coverage_status": "SOURCE_SEASON_AVAILABLE" if depth_source else "SOURCE_SEASON_MISSING",
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "decision_date_safe": "PASS_LAGGED_N_TO_N_PLUS_1",
                "leakage_flag": "PASS_FEATURE_SEASON_N_TO_TARGET_SEASON_N_PLUS_1",
                "identity_flag": "PASS_GSIS_DIRECT_OR_PUBLIC_PLAYERS_PFR_TO_GSIS_CROSSWALK",
                "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
                "caveat": "Snap/depth context is lagged closed-season public nflverse data; 2012 snap counts are effectively unavailable; no same-season use.",
            }
        )
    return sidecar, all_sources


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
    rec_rows = load_csv(REC_ARTIFACT / "NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv")
    ff = attach_sidecar(
        rows,
        ff_rows,
        "ffop",
        ["ffop_xfp_total"],
        {"ffop_xfp_total": "ffop_total_fantasy_points_exp"},
    )
    ngs = attach_sidecar(rows, ngs_rows, "ngs", ["ngs_position_signal_raw"])
    epa = attach_sidecar(rows, epa_rows, "epa", ["epa_total_raw"])
    rec = attach_sidecar(rows, rec_rows, "recopp", ["rec_opp_wopr"])
    return {
        "ffop_joined": ff["joined"],
        "ngs_joined": ngs["joined"],
        "epa_joined": epa["joined"],
        "rec_joined": rec["joined"],
    }


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


def result_row(
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
        ("INGREDIENT_ONLY_SNAP_OFFENSIVE_SNAPS", "snapdepth_snap_offensive_snaps_pct", "snap_offensive_snaps"),
        ("INGREDIENT_ONLY_SNAP_OFFENSIVE_SNAP_SHARE", "snapdepth_snap_offensive_snap_share_pct", "snap_offensive_snap_share"),
        ("INGREDIENT_ONLY_SNAP_GAMES_WITH_OFFENSIVE_SNAPS", "snapdepth_snap_games_with_offensive_snaps_pct", "snap_games_with_offensive_snaps"),
        ("INGREDIENT_ONLY_SNAP_NOT_LOW_SNAP_SCORE", "snapdepth_snap_not_low_snap_score_pct", "snap_not_low_snap_score"),
        ("INGREDIENT_ONLY_SNAP_ROLE_SCORE", "snapdepth_snap_role_score_pct", "snap_role_score"),
        ("INGREDIENT_ONLY_DEPTH_WEEKS_AS_STARTER", "snapdepth_depth_weeks_as_starter_pct", "depth_weeks_as_starter"),
        ("INGREDIENT_ONLY_DEPTH_ROLE_SCORE", "snapdepth_depth_role_score_pct", "depth_role_score"),
        ("INGREDIENT_ONLY_DEPTH_STABILITY_SCORE", "snapdepth_depth_stability_score_pct", "depth_stability_score"),
        ("INGREDIENT_ONLY_SNAP_DEPTH_ROLE_SCORE", "snapdepth_snap_depth_role_score_pct", "snap_depth_role_score"),
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
            "nflverse_snap_depth_role",
            raw_field,
            "ingredient percentile rank only",
            "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025" if len(selected) > 5000 else "PARTIAL_FIELD_COVERAGE",
        )
        results.append(
            result_row(
                run_id,
                run_id,
                "INGREDIENT_ONLY",
                "none",
                "nflverse_snap_depth_role",
                raw_field,
                "QB/RB/WR/TE",
                selected,
                score_col,
                full_denom,
                None,
                "Snap/depth ingredient alone; public nflverse sources aggregated regular season and lagged N-to-N+1 review-only.",
            )
        )

    formula_ingredients = [
        ("SNAP_SNAPS", "snapdepth_snap_offensive_snaps_pct"),
        ("SNAP_SHARE", "snapdepth_snap_offensive_snap_share_pct"),
        ("SNAP_GAMES", "snapdepth_snap_games_with_offensive_snaps_pct"),
        ("SNAP_NOT_LOW", "snapdepth_snap_not_low_snap_score_pct"),
        ("SNAP_ROLE", "snapdepth_snap_role_score_pct"),
        ("DEPTH_STARTER_WEEKS", "snapdepth_depth_weeks_as_starter_pct"),
        ("DEPTH_ROLE", "snapdepth_depth_role_score_pct"),
        ("DEPTH_STABILITY", "snapdepth_depth_stability_score_pct"),
        ("SNAP_DEPTH_ROLE", "snapdepth_snap_depth_role_score_pct"),
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
                score_col = f"{seed_col}__SNAPDEPTH_{suffix}_PCT{pct_label}"
                materialize_combo_score(rows, score_col, [(seed_col, 1.0 - weight), (ingredient_col, weight)])
                selected = selected_rows(rows, scope, [score_col])
                run_id = f"{seed['candidate_id']}__PLUS_SNAPDEPTH_{suffix}_PCT{pct_label}"
                register(
                    registry,
                    run_id,
                    "formula_x_ingredient",
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "nflverse_snap_depth_role",
                    ingredient_col.replace("snapdepth_", ""),
                    f"seed_percentile={1.0 - weight:.3f};ingredient_percentile={weight:.3f}",
                    "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025" if len(selected) > 5000 else "PARTIAL_BY_POSITION_OR_FIELD_COVERAGE",
                )
                results.append(
                    result_row(
                        run_id,
                        seed["candidate_id"],
                        seed["cluster_id"],
                        seed["formula_definition"],
                        "nflverse_snap_depth_role",
                        ingredient_col.replace("snapdepth_", ""),
                        seed["position_scope"],
                        selected,
                        score_col,
                        denom,
                        seed_metrics,
                        "Fixed predeclared snap/depth additive variant; no dynamic tuning.",
                    )
                )

    combo_specs = [
        ("SNAPDEPTH_FFOP_PCT025_025", [("snapdepth_snap_depth_role_score_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("SNAPDEPTH_FFOP_PCT050_050", [("snapdepth_snap_depth_role_score_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("SNAPDEPTH_FFOP_PCT050_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("SNAPDEPTH_FFOP_PCT025_050", [("snapdepth_snap_depth_role_score_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("SNAPDEPTH_NGS_PCT025_025", [("snapdepth_snap_depth_role_score_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("SNAPDEPTH_NGS_PCT050_050", [("snapdepth_snap_depth_role_score_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.050)]),
        ("SNAPDEPTH_NGS_PCT050_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("SNAPDEPTH_NGS_PCT025_050", [("snapdepth_snap_depth_role_score_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.050)]),
        ("SNAPDEPTH_EPA_PCT025_025", [("snapdepth_snap_depth_role_score_pct", 0.025), ("epa_epa_total_raw_pct", 0.025)]),
        ("SNAPDEPTH_EPA_PCT050_050", [("snapdepth_snap_depth_role_score_pct", 0.050), ("epa_epa_total_raw_pct", 0.050)]),
        ("SNAPDEPTH_EPA_PCT050_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("epa_epa_total_raw_pct", 0.025)]),
        ("SNAPDEPTH_EPA_PCT025_050", [("snapdepth_snap_depth_role_score_pct", 0.025), ("epa_epa_total_raw_pct", 0.050)]),
        ("SNAPDEPTH_RECOPP_PCT025_025", [("snapdepth_snap_depth_role_score_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.025)]),
        ("SNAPDEPTH_RECOPP_PCT050_050", [("snapdepth_snap_depth_role_score_pct", 0.050), ("recopp_rec_opp_wopr_pct", 0.050)]),
        ("SNAPDEPTH_RECOPP_PCT050_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("recopp_rec_opp_wopr_pct", 0.025)]),
        ("SNAPDEPTH_RECOPP_PCT025_050", [("snapdepth_snap_depth_role_score_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.050)]),
        ("SNAPDEPTH_FFOP_NGS_PCT025_050_025", [("snapdepth_snap_depth_role_score_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("SNAPDEPTH_FFOP_NGS_PCT050_025_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("SNAPDEPTH_RECOPP_FFOP_PCT025_025_050", [("snapdepth_snap_depth_role_score_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("SNAPDEPTH_RECOPP_FFOP_PCT050_025_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("recopp_rec_opp_wopr_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("SNAPDEPTH_EPA_RECOPP_PCT025_025_050", [("snapdepth_snap_depth_role_score_pct", 0.025), ("epa_epa_total_raw_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.050)]),
        ("SNAPDEPTH_EPA_RECOPP_PCT050_025_025", [("snapdepth_snap_depth_role_score_pct", 0.050), ("epa_epa_total_raw_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.025)]),
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
                "nflverse_snap_depth_role+prior_sidecars",
                fields,
                f"seed_percentile={1.0 - total_weight:.3f};" + ";".join(f"{col}={weight:.3f}" for col, weight in ingredients),
                "PARTIAL_WINDOW_PRIOR_V2_SIDE_CAR" if partial else "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025",
            )
            results.append(
                result_row(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "nflverse_snap_depth_role+prior_sidecars",
                    fields,
                    seed["position_scope"],
                    selected,
                    score_col,
                    denom,
                    seed_metrics,
                    "Bounded predeclared snap/depth combination; prior ffop/NGS sidecars retain partial-window caveats when used.",
                )
            )
    return registry, results


def join_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ingredients = [
        ("nflverse_snap_depth_role", "snapdepth_snap_depth_role_score", set(SOURCE_SEASONS)),
        ("nflverse_snap_counts", "snapdepth_snap_role_score", SNAP_SEASONS_WITH_DATA),
        ("nflverse_depth_charts", "snapdepth_depth_role_score", set(SOURCE_SEASONS)),
        ("ffopportunity_prior_v2", "ffop_ffop_xfp_total", {2021, 2022, 2023, 2024}),
        ("nflverse_ngs_prior_v2", "ngs_ngs_position_signal_raw", {2021, 2022, 2023, 2024}),
        ("nflverse_epa_prior_lane", "epa_epa_total_raw", set(SOURCE_SEASONS)),
        ("nflverse_receiving_opportunity_prior_lane", "recopp_rec_opp_wopr", set(SOURCE_SEASONS)),
    ]
    out = []
    for ingredient, prefix, seasons in ingredients:
        for pos in ["ALL", *POSITIONS]:
            eligible = [
                r for r in rows if int(r["feature_season"]) in seasons and (pos == "ALL" or str(r["position"]) == pos)
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
        "player_id",
        "player_name",
        "position",
        "team",
        "snap_offensive_snaps",
        "snap_offensive_snap_share",
        "snap_games_with_offensive_snaps",
        "snap_low_snap_flag",
        "depth_primary_depth_rank",
        "depth_best_depth_rank",
        "depth_weeks_as_starter",
        "depth_weeks_as_backup",
        "depth_role_tier",
        "depth_role_change_flag",
        "snap_depth_source_path",
        "snap_depth_source_hash",
        "join_status",
        "coverage_status",
        "review_only_status",
    }
    fields = set(sidecar[0].keys()) if sidecar else set()
    duplicate_keys = len(sidecar) - len({(r["player_id"], r["season"], r["position"]) for r in sidecar})
    snap_joined = len([r for r in sidecar if r["join_status"] in {"JOINED_SNAP_AND_DEPTH", "JOINED_SNAP_ONLY"}])
    depth_joined = len([r for r in sidecar if r["join_status"] in {"JOINED_SNAP_AND_DEPTH", "JOINED_DEPTH_ONLY"}])
    schema = [
        {
            "artifact": "nflverse_snap_depth_role",
            "row_count": len(sidecar),
            "required_columns_present": "yes" if required.issubset(fields) else "no",
            "missing_columns": "|".join(sorted(required - fields)),
            "duplicate_keys": duplicate_keys,
            "rows_with_snap_record": snap_joined,
            "rows_with_depth_record": depth_joined,
            "review_only_status": "PASS"
            if sidecar and duplicate_keys == 0 and all("REVIEW_ONLY" in r["review_only_status"] and "NOT_MODEL_USE" in r["review_only_status"] for r in sidecar)
            else "FAIL",
        }
    ]
    joined = [r for r in rows if r.get("snapdepth_snap_depth_role_score") is not None]
    bad_lag = [r for r in joined if int(r["feature_season"]) >= int(r["season"])]
    leakage = [
        {
            "ingredient": "nflverse_snap_depth_role",
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
    return [
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
        for row in results
    ]


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
    snap_depth_cov = next(r for r in coverage if r["ingredient"] == "nflverse_snap_depth_role" and r["position"] == "ALL")
    snap_cov = next(r for r in coverage if r["ingredient"] == "nflverse_snap_counts" and r["position"] == "ALL")
    depth_cov = next(r for r in coverage if r["ingredient"] == "nflverse_depth_charts" and r["position"] == "ALL")
    verdict = "YELLOW_NFLVERSE_SNAP_DEPTH_ROLE_PARTIAL_WITH_CAVEATS"
    if b_formula and float(b_formula["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY and float(b_formula["pyf_delta"]) > 0 and int(b_formula["row_count"]) > 5000:
        verdict = "GREEN_NFLVERSE_SNAP_DEPTH_ROLE_ADDS_REVIEW_ONLY_SIGNAL"
    if b_formula and float(b_formula["overall_spearman"]) <= CURRENT_BEST_FULL_HISTORY and b_combo and float(b_combo["overall_spearman"]) <= CURRENT_BEST_FULL_HISTORY:
        verdict = "RED_NFLVERSE_SNAP_DEPTH_ROLE_NO_INCREMENTAL_SIGNAL"
    top_all = sorted([r for r in results if r["overall_spearman"]], key=lambda r: float(r["overall_spearman"]), reverse=True)[:15]
    write_md(
        OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_FORMULA_MART_SIDECAR_V1_REPORT.md",
        f"""
# nflverse Snap Counts / Depth Chart Role Formula Mart Sidecar V1 Report

## Verdict

`{verdict}`

## Scope

This lane built a review-only snap-count and depth-chart role sidecar from public no-key nflverse parquet assets. It used feature season N to target season N+1 only. It did not mutate the canonical Formula Data Mart, canonical `local_exports`, app/runtime code, rankings, or production model behavior.

## Source And Sidecar

- Source families: public nflverse `snap_counts`, `depth_charts`, and `players` identity crosswalk.
- Feature seasons requested: `{min(SOURCE_SEASONS)}-{max(SOURCE_SEASONS)}`.
- Target seasons: `{min(int(r['season']) for r in sidecar)}-{max(int(r['season']) for r in sidecar)}`.
- Sidecar rows: `{len(sidecar)}`.
- Snap/depth role join coverage: `{snap_depth_cov['joined_rows']} / {snap_depth_cov['eligible_rows']}` or `{snap_depth_cov['join_coverage_pct']}`.
- Snap-count coverage: `{snap_cov['joined_rows']} / {snap_cov['eligible_rows']}` or `{snap_cov['join_coverage_pct']}`.
- Depth-chart coverage: `{depth_cov['joined_rows']} / {depth_cov['eligible_rows']}` or `{depth_cov['join_coverage_pct']}`.
- Source files hashed: `{len(sources)}`.

## Ingredients Loaded

- `snap_offensive_snaps`
- `snap_offensive_snap_share`
- `snap_games_with_offensive_snaps`
- `snap_low_snap_flag`
- `snap_not_low_snap_score`
- `snap_role_score`
- `snap_share_trend`
- `depth_primary_depth_rank`
- `depth_best_depth_rank`
- `depth_weeks_as_starter`
- `depth_weeks_as_backup`
- `depth_role_tier`
- `depth_role_change_flag`
- `depth_role_score`
- `depth_stability_score`
- `snap_depth_role_score`

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

{chr(10).join(f"- `{row['run_id']}` Spearman `{row['overall_spearman']}` rows `{row['row_count']}` PYF delta `{row['pyf_delta']}` use `{row['use_decision']}`" for row in top_all)}

## Material Beat Of `.755`

- All result rows above `.755`: `{all_above}`.
- Broad lagged non-V2 snap/depth result rows above `.755`: `{full_history_above}`.

The strongest non-V2 snap-count rows are broad lagged results, not complete `2013-2025` results, because public 2012 snap counts are effectively unavailable and snap-only scores begin with target season `2014`. Any result using prior ffopportunity or NGS sidecars is partial-window only and cannot be used to claim a complete full-history `.755` plateau break.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane unless Master HQ separately approves a ranking-simulation design packet. Snap/depth role context remains review-only evidence.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
""",
    )
    write_md(
        OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_NEXT_USE_DECISION.md",
        f"""
# Snap / Depth Role Next Use Decision

Decision: `AVAILABLE_REVIEW_ONLY_ROLE_CONTEXT`.

Snap/depth role data was loaded from public no-key nflverse assets and is valid for lagged review-only Formula Mart sidecar use. It may support role/opportunity stability review, interaction checks, and guardrail/slice reporting. It is not approved for production/model-use, direct ranking input, hidden sort logic, source promotion, or review-only ranking simulation.

Best component: `{b_component['run_id'] if b_component else ''}` Spearman `{b_component['overall_spearman'] if b_component else ''}`.

Best formula x ingredient: `{b_formula['run_id'] if b_formula else ''}` Spearman `{b_formula['overall_spearman'] if b_formula else ''}`.

Best combination: `{b_combo['run_id'] if b_combo else ''}` Spearman `{b_combo['overall_spearman'] if b_combo else ''}`.

Recommended next step: `Point-in-Time Injury Availability Data Mart Gate V1` or `Historical Market / ADP Source Gate and Data Mart Join V1`, with Master HQ choosing whether availability context or market baseline is the next highest-value data upgrade.
""",
    )
    write_md(
        OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_BLOCKERS_AND_CAVEATS.md",
        """
# Blockers And Caveats

- This is review-only evidence, not production/model-use.
- Same-season/future context was not used; all tests use feature season N to target season N+1.
- Snap counts use public `players.parquet` PFR-to-GSIS identity mapping; this is review-only and not source promotion.
- 2012 snap-count data is effectively unavailable, so snap-only fields have lower 2013 target coverage. Depth-chart fields cover the full target window through feature season 2012.
- Combo tests using prior ffopportunity or NGS inherit partial-window V2 sidecar caveats.
- Partial-window results cannot be used to claim the full-history `.755` plateau was broken.
- Review-only ranking simulation remains blocked.
""",
    )
    csv_paths = [
        "NFLVERSE_SNAP_DEPTH_ROLE_SOURCE_LEDGER.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_SCHEMA_VALIDATION.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_JOIN_COVERAGE.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_COMPONENT_TEST_RESULTS.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_FORMULA_X_INGREDIENT_RESULTS.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_INGREDIENT_COMBINATION_RESULTS.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_ALL_RESULTS_REQUIRED_SCHEMA.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_SLICE_GUARDRAILS.csv",
        "NFLVERSE_SNAP_DEPTH_ROLE_STABILITY_BY_SEASON.csv",
    ]
    write_md(
        OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_SOURCE_TRACE.md",
        "\n".join(
            [
                "# nflverse Snap / Depth Role Source Trace",
                "",
                f"- Prior receiving opportunity commit verified by request/preflight context: `{PRIOR_RECEIVING_COMMIT}`",
                f"- Current remote HQ expected and verified before work: `{REMOTE_HEAD}`",
                f"- Public source cache used outside repo: `{SOURCE_CACHE}`",
                "- Public source families: nflverse-data GitHub release `snap_counts/snap_counts_YYYY.parquet`, `depth_charts/depth_charts_YYYY.parquet`, and `players/players.parquet`.",
                f"- Prior V2 ffop/NGS artifacts used for bounded partial-window combos: `{V2_ARTIFACT}`",
                f"- Prior EPA sidecar used for bounded EPA combo checks: `{EPA_ARTIFACT}`",
                f"- Prior receiving sidecar used for bounded receiving combo checks: `{REC_ARTIFACT}`",
                "",
                "## Result CSVs",
                *[f"- `{OUT_DIR / p}`" for p in csv_paths],
            ]
        ),
    )


def main() -> None:
    rows = v2.load_formula_panel()
    sidecar, sources = build_sidecar(rows)
    raw_cols = [
        "snap_offensive_snaps",
        "snap_offensive_snap_share",
        "snap_games_with_offensive_snaps",
        "snap_not_low_snap_score",
        "snap_role_score",
        "depth_weeks_as_starter",
        "depth_role_score",
        "depth_stability_score",
        "snap_depth_role_score",
    ]
    snap_join = attach_sidecar(rows, sidecar, "snapdepth", raw_cols)
    prior_join = attach_prior_sidecars(rows)
    seeds = v2.load_seed_registry()
    registry, results = build_tests(rows, seeds)
    coverage = join_coverage(rows)
    schema, leakage = validation_rows(sidecar, rows)
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]

    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_SOURCE_LEDGER.csv", sources)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv", sidecar)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_JOIN_COVERAGE.csv", coverage)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_PREDECLARED_TEST_REGISTRY.csv", registry)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_COMPONENT_TEST_RESULTS.csv", component, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_FORMULA_X_INGREDIENT_RESULTS.csv", formula_x, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_INGREDIENT_COMBINATION_RESULTS.csv", combos, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_ALL_RESULTS_REQUIRED_SCHEMA.csv", results, RESULT_FIELDS)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_SLICE_GUARDRAILS.csv", guardrail_rows(results))
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_STABILITY_BY_SEASON.csv", stability_rows(results))
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_SCHEMA_VALIDATION.csv", schema)
    write_csv(OUT_DIR / "NFLVERSE_SNAP_DEPTH_ROLE_LEAKAGE_ASOF_VALIDATION.csv", leakage)
    make_reports(sidecar, sources, coverage, results, seeds)
    print(
        {
            "sidecar_rows": len(sidecar),
            "tests": len(results),
            "seeds": len(seeds),
            "snap_depth_joined": snap_join["joined"],
            "ffop_joined": prior_join["ffop_joined"],
            "ngs_joined": prior_join["ngs_joined"],
            "epa_joined": prior_join["epa_joined"],
            "rec_joined": prior_join["rec_joined"],
        }
    )


if __name__ == "__main__":
    main()
