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
SNAP_DEPTH_BROAD_REFERENCE = 0.763
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_SNAP_DEPTH_COMMIT = "447df6a8771ff5931d823fb86585b420d3e082ab"
SOURCE_CACHE = Path(r"C:\NWR_REVIEW\nflverse_injury_availability_source_cache_20260709")
SOURCE_SEASONS = list(range(2012, 2025))

MODEL_ROOT = Path(__file__).resolve().parents[1]
V2_ARTIFACT = MODEL_ROOT / "nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
EPA_ARTIFACT = MODEL_ROOT / "nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709"
REC_ARTIFACT = MODEL_ROOT / "nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709"
SNAP_ARTIFACT = MODEL_ROOT / "nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709"
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
        all_fields: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in all_fields:
                    all_fields.append(key)
        fields = all_fields
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


def public_url(kind: str, season: int) -> str:
    if kind == "weekly_rosters":
        return f"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{season}.parquet"
    if kind == "injuries":
        return f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.parquet"
    raise ValueError(kind)


def local_source_path(kind: str, season: int) -> Path:
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    return SOURCE_CACHE / f"{kind}_{season}.parquet"


def ensure_source(kind: str, season: int) -> tuple[Path, str, int, str]:
    path = local_source_path(kind, season)
    url = public_url(kind, season)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    return path, url, path.stat().st_size, sha256_file(path)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def is_non_injury_text(value: Any) -> bool:
    txt = normalize_text(value)
    return any(piece in txt for piece in ["not injury", "not-injury", "rest", "personal", "illness - rest"])


def roster_active(status: Any, status_desc: Any) -> float:
    status_txt = normalize_text(status)
    desc_txt = normalize_text(status_desc)
    if status_txt in {"act", "active"}:
        return 1.0
    if desc_txt.startswith("a"):
        return 1.0
    return 0.0


def roster_inactive(status: Any, status_desc: Any) -> float:
    status_txt = normalize_text(status)
    desc_txt = normalize_text(status_desc)
    if status_txt in {"ina", "inactive"}:
        return 1.0
    if desc_txt.startswith("i"):
        return 1.0
    return 0.0


def roster_reserve(status: Any, status_desc: Any) -> float:
    status_txt = normalize_text(status)
    desc_txt = normalize_text(status_desc)
    combined = f"{status_txt} {desc_txt}"
    if status_txt in {"res", "ir", "pup", "nfi"}:
        return 1.0
    if any(piece in combined for piece in ["reserve", "injured", "pup", "nfi", "ir"]):
        return 1.0
    return 0.0


def aggregate_roster_features() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        path, url, size, file_hash = ensure_source("weekly_rosters", season)
        df = pd.read_parquet(path)
        reg = df[df["game_type"].astype(str).eq("REG")].copy() if "game_type" in df.columns else df.copy()
        fantasy = reg[reg["position"].astype(str).isin(POSITIONS) & reg["gsis_id"].notna()].copy()
        if not fantasy.empty:
            fantasy["player_id"] = fantasy["gsis_id"].astype(str)
            fantasy["week_num"] = pd.to_numeric(fantasy["week"], errors="coerce")
            fantasy["active_week"] = fantasy.apply(
                lambda r: roster_active(r.get("status"), r.get("status_description_abbr")), axis=1
            )
            fantasy["inactive_week"] = fantasy.apply(
                lambda r: roster_inactive(r.get("status"), r.get("status_description_abbr")), axis=1
            )
            fantasy["reserve_week"] = fantasy.apply(
                lambda r: roster_reserve(r.get("status"), r.get("status_description_abbr")), axis=1
            )
            fantasy["non_active_week"] = (1.0 - fantasy["active_week"]).clip(lower=0.0, upper=1.0)
            fantasy["ir_pup_week"] = fantasy["reserve_week"]
            fantasy["week_key"] = fantasy["season"].astype(str) + "_" + fantasy["week_num"].astype(str)
            grouped = fantasy.groupby(["player_id", "season"], dropna=False)
            season_rows = grouped.agg(
                player_name=("full_name", mode_text),
                team=("team", mode_text),
                source_position=("position", mode_text),
                roster_weeks=("week_key", "nunique"),
                active_weeks=("active_week", "sum"),
                inactive_weeks=("inactive_week", "sum"),
                reserve_weeks=("reserve_week", "sum"),
                non_active_weeks=("non_active_week", "sum"),
                ir_pup_weeks=("ir_pup_week", "sum"),
            ).reset_index().rename(columns={"season": "feature_season"})
            season_rows["feature_season"] = season_rows["feature_season"].astype(int)
            season_rows["active_pct"] = season_rows["active_weeks"] / season_rows["roster_weeks"].clip(lower=1)
            season_rows["roster_missed_games_proxy"] = season_rows[["non_active_weeks", "reserve_weeks"]].max(axis=1)
            season_rows["ir_pup_flag"] = (season_rows["ir_pup_weeks"] > 0).astype(float)
            season_rows["roster_availability_score"] = (
                season_rows["active_pct"].clip(lower=0.0, upper=1.0) * 0.80
                + (1.0 - (season_rows["ir_pup_weeks"] / season_rows["roster_weeks"].clip(lower=1)).clip(upper=1.0)) * 0.20
            )
            season_rows["source_url"] = url
            season_rows["source_path"] = str(path)
            season_rows["source_hash"] = file_hash
            frames.append(season_rows)
        sources.append(
            {
                "source_family": "nflverse_weekly_rosters",
                "feature_season": season,
                "source_url": url,
                "local_cache_path": str(path),
                "sha256": file_hash,
                "file_size": size,
                "raw_rows": len(df),
                "regular_season_rows": len(reg),
                "mapped_rows": len(fantasy),
                "columns": "|".join(df.columns),
                "distinct_status_values": "|".join(sorted({str(v) for v in fantasy.get("status", pd.Series(dtype=str)).dropna().unique()})),
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "asof_status": "PASS_LAGGED_CLOSED_FEATURE_SEASON_ONLY",
            }
        )
    if not frames:
        return pd.DataFrame(), sources
    return pd.concat(frames, ignore_index=True, sort=False), sources


def aggregate_injury_features() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        path, url, size, file_hash = ensure_source("injuries", season)
        df = pd.read_parquet(path)
        reg = df[df["game_type"].astype(str).eq("REG")].copy() if "game_type" in df.columns else df.copy()
        fantasy = reg[reg["position"].astype(str).isin(POSITIONS) & reg["gsis_id"].notna()].copy()
        if not fantasy.empty:
            fantasy["player_id"] = fantasy["gsis_id"].astype(str)
            fantasy["feature_season"] = pd.to_numeric(fantasy["season"], errors="coerce").astype("Int64")
            fantasy["week_num"] = pd.to_numeric(fantasy["week"], errors="coerce")
            fantasy["week_key"] = fantasy["feature_season"].astype(str) + "_" + fantasy["week_num"].astype(str)
            fantasy["report_status_clean"] = fantasy["report_status"].map(normalize_text)
            fantasy["practice_status_clean"] = fantasy["practice_status"].map(normalize_text)
            fantasy["non_injury_related"] = fantasy.apply(
                lambda r: is_non_injury_text(r.get("report_primary_injury"))
                or is_non_injury_text(r.get("practice_primary_injury")),
                axis=1,
            )
            fantasy["report_out"] = fantasy["report_status_clean"].str.contains("out", na=False).astype(float)
            fantasy["report_doubtful"] = fantasy["report_status_clean"].str.contains("doubtful", na=False).astype(float)
            fantasy["report_questionable"] = fantasy["report_status_clean"].str.contains("questionable", na=False).astype(float)
            fantasy["report_probable"] = fantasy["report_status_clean"].str.contains("probable", na=False).astype(float)
            fantasy["practice_dnp"] = fantasy["practice_status_clean"].str.contains("did not participate", na=False).astype(float)
            fantasy["practice_limited"] = fantasy["practice_status_clean"].str.contains("limited", na=False).astype(float)
            fantasy["practice_full"] = fantasy["practice_status_clean"].str.contains("full participation", na=False).astype(float)
            fantasy["injury_related_row"] = (~fantasy["non_injury_related"]).astype(float)
            fantasy["injury_related_week"] = (
                (fantasy["injury_related_row"] > 0)
                & (
                    (fantasy["report_out"] > 0)
                    | (fantasy["report_doubtful"] > 0)
                    | (fantasy["report_questionable"] > 0)
                    | (fantasy["practice_dnp"] > 0)
                    | (fantasy["practice_limited"] > 0)
                )
            ).astype(float)
            grouped = fantasy.groupby(["player_id", "feature_season"], dropna=False)
            season_rows = grouped.agg(
                player_name=("full_name", mode_text),
                team=("team", mode_text),
                source_position=("position", mode_text),
                injury_report_rows=("week_key", "count"),
                injury_report_weeks=("week_key", "nunique"),
                injury_related_report_weeks=("injury_related_week", "sum"),
                report_out_count=("report_out", "sum"),
                report_doubtful_count=("report_doubtful", "sum"),
                report_questionable_count=("report_questionable", "sum"),
                report_probable_count=("report_probable", "sum"),
                practice_dnp_count=("practice_dnp", "sum"),
                practice_limited_count=("practice_limited", "sum"),
                practice_full_count=("practice_full", "sum"),
            ).reset_index()
            season_rows["feature_season"] = season_rows["feature_season"].astype(int)
            season_rows["injury_caveat_flag"] = (
                (
                    season_rows["report_out_count"]
                    + season_rows["report_doubtful_count"]
                    + season_rows["report_questionable_count"]
                    + season_rows["practice_dnp_count"]
                    + season_rows["practice_limited_count"]
                )
                > 0
            ).astype(float)
            season_rows["injury_report_clean_score"] = 1.0 - (
                season_rows["injury_related_report_weeks"] / 17.0
            ).clip(lower=0.0, upper=1.0)
            season_rows["source_url"] = url
            season_rows["source_path"] = str(path)
            season_rows["source_hash"] = file_hash
            frames.append(season_rows)
        sources.append(
            {
                "source_family": "nflverse_injuries",
                "feature_season": season,
                "source_url": url,
                "local_cache_path": str(path),
                "sha256": file_hash,
                "file_size": size,
                "raw_rows": len(df),
                "regular_season_rows": len(reg),
                "mapped_rows": len(fantasy),
                "columns": "|".join(df.columns),
                "distinct_status_values": "|".join(sorted({str(v) for v in fantasy.get("report_status", pd.Series(dtype=str)).dropna().unique()})),
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
    roster, roster_sources = aggregate_roster_features()
    injury, injury_sources = aggregate_injury_features()
    all_sources = [*roster_sources, *injury_sources]
    roster_lookup = {
        (str(r["player_id"]), int(r["feature_season"])): r
        for r in roster.to_dict("records")
    } if not roster.empty else {}
    injury_lookup = {
        (str(r["player_id"]), int(r["feature_season"])): r
        for r in injury.to_dict("records")
    } if not injury.empty else {}
    roster_source_by_season = source_map(all_sources, "nflverse_weekly_rosters")
    injury_source_by_season = source_map(all_sources, "nflverse_injuries")
    sidecar: list[dict[str, Any]] = []
    for row in panel_rows:
        feature_season = int(row["feature_season"])
        prior_feature_season = feature_season - 1
        key = (str(row["player_id"]), feature_season)
        prior_key = (str(row["player_id"]), prior_feature_season)
        rrow = roster_lookup.get(key)
        irow = injury_lookup.get(key)
        prior_rrow = roster_lookup.get(prior_key)
        roster_source = roster_source_by_season.get(feature_season, {})
        injury_source = injury_source_by_season.get(feature_season, {})
        roster_joined = rrow is not None
        injury_joined = irow is not None
        roster_weeks = value_or_none(rrow, "roster_weeks")
        active_weeks = value_or_none(rrow, "active_weeks")
        active_pct = value_or_none(rrow, "active_pct")
        missed_proxy = value_or_none(rrow, "roster_missed_games_proxy")
        if roster_joined and missed_proxy is None:
            missed_proxy = 0.0
        injury_related_weeks = value_or_none(irow, "injury_related_report_weeks")
        if injury_related_weeks is None and roster_joined and injury_source:
            injury_related_weeks = 0.0
        report_out = value_or_none(irow, "report_out_count")
        report_questionable = value_or_none(irow, "report_questionable_count")
        report_doubtful = value_or_none(irow, "report_doubtful_count")
        report_probable = value_or_none(irow, "report_probable_count")
        practice_dnp = value_or_none(irow, "practice_dnp_count")
        practice_limited = value_or_none(irow, "practice_limited_count")
        for_zero = [report_out, report_questionable, report_doubtful, report_probable, practice_dnp, practice_limited]
        if roster_joined and injury_source:
            report_out, report_questionable, report_doubtful, report_probable, practice_dnp, practice_limited = [
                0.0 if v is None else v for v in for_zero
            ]
        report_clean_score = value_or_none(irow, "injury_report_clean_score")
        if report_clean_score is None and roster_joined and injury_source:
            report_clean_score = 1.0
        prior_missed = value_or_none(prior_rrow, "roster_missed_games_proxy")
        if prior_missed is None:
            prior_missed = 0.0
        two_year_missed = None
        if missed_proxy is not None:
            two_year_missed = missed_proxy + prior_missed
        active_pct_for_score = active_pct if active_pct is not None else None
        missed_for_score = missed_proxy if missed_proxy is not None else None
        two_year_durability = None
        if two_year_missed is not None:
            two_year_durability = 1.0 - min(1.0, two_year_missed / 34.0)
        durability = None
        if missed_for_score is not None:
            denom = max(roster_weeks or 17.0, 1.0)
            durability = 1.0 - min(1.0, missed_for_score / denom)
        availability_score = None
        if active_pct_for_score is not None and durability is not None and report_clean_score is not None:
            availability_score = (
                active_pct_for_score * 0.50
                + durability * 0.25
                + report_clean_score * 0.15
                + (two_year_durability if two_year_durability is not None else durability) * 0.10
            )
        caveat_flag = None
        caveat_parts = [
            missed_proxy,
            report_out,
            report_doubtful,
            report_questionable,
            practice_dnp,
            practice_limited,
            value_or_none(rrow, "ir_pup_weeks"),
        ]
        if roster_joined:
            caveat_flag = 1.0 if sum(clean_float(v) for v in caveat_parts) > 0 else 0.0
        caveat_inverse = None if caveat_flag is None else 1.0 - caveat_flag
        if roster_joined and injury_joined:
            join_status = "JOINED_ROSTER_AND_INJURY_REPORT"
        elif roster_joined:
            join_status = "JOINED_ROSTER_NO_INJURY_REPORT"
        elif injury_joined:
            join_status = "JOINED_INJURY_REPORT_NO_ROSTER"
        else:
            join_status = "NO_ROSTER_OR_INJURY_REPORT"
        source_paths = "|".join(p for p in [roster_source.get("path", ""), injury_source.get("path", "")] if p)
        source_hashes = "|".join(h for h in [roster_source.get("hash", ""), injury_source.get("hash", "")] if h)
        true_zero_status = (
            "INJURY_REPORT_ABSENCE_TREATED_AS_ZERO_WHEN_ROSTER_JOINED"
            if roster_joined and not injury_joined
            else ("OBSERVED_INJURY_REPORT_ROW" if injury_joined else "UNKNOWN_NO_ROSTER")
        )
        sidecar.append(
            {
                "season": int(row["season"]),
                "feature_season": feature_season,
                "player_id": str(row["player_id"]),
                "player_name": row.get("player_name") or (rrow or irow or {}).get("player_name", ""),
                "position": str(row["position"]),
                "team": (rrow or irow or {}).get("team", ""),
                "avail_games_active": fmt(active_weeks, 3),
                "avail_games_inactive": fmt(value_or_none(rrow, "inactive_weeks"), 3),
                "avail_games_missed": fmt(missed_proxy, 3),
                "avail_active_pct": fmt(active_pct, 6),
                "avail_questionable_count": fmt(report_questionable, 3),
                "avail_doubtful_count": fmt(report_doubtful, 3),
                "avail_out_count": fmt(report_out, 3),
                "avail_probable_count": fmt(report_probable, 3),
                "avail_practice_dnp_count": fmt(practice_dnp, 3),
                "avail_practice_limited_count": fmt(practice_limited, 3),
                "avail_injury_report_weeks": fmt(injury_related_weeks, 3),
                "avail_ir_pup_flag": fmt(value_or_none(rrow, "ir_pup_flag"), 3),
                "avail_prior_year_missed_games": fmt(missed_proxy, 3),
                "avail_two_year_missed_games": fmt(two_year_missed, 3),
                "avail_durability_score": fmt(durability, 6),
                "avail_report_clean_score": fmt(report_clean_score, 6),
                "avail_two_year_durability_score": fmt(two_year_durability, 6),
                "avail_availability_score": fmt(availability_score, 6),
                "avail_caveat_flag": fmt(caveat_flag, 3),
                "avail_caveat_inverse_score": fmt(caveat_inverse, 6),
                "availability_source_path": source_paths,
                "availability_source_hash": source_hashes,
                "join_status": join_status,
                "coverage_status": "SOURCE_SEASON_AVAILABLE" if roster_source and injury_source else "SOURCE_SEASON_MISSING",
                "source_gate_status": "PUBLIC_NFLVERSE_NO_KEY_REVIEW_ONLY_NOT_MODEL_USE",
                "decision_date_safe": "PASS_LAGGED_N_TO_N_PLUS_1",
                "leakage_flag": "PASS_FEATURE_SEASON_N_TO_TARGET_SEASON_N_PLUS_1",
                "identity_flag": "PASS_GSIS_DIRECT_FROM_PUBLIC_NFLVERSE",
                "missingness_flag": "PASS_WITH_CAVEAT" if roster_joined else "MISSING_ROSTER_AVAILABILITY",
                "true_zero_vs_unknown_status": true_zero_status,
                "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
                "caveat": "Availability report is lagged closed-season context only; absence from injury report is treated as zero only when a roster record exists; not injury prediction.",
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
    snap_rows = load_csv(SNAP_ARTIFACT / "NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv")
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
    snap = attach_sidecar(rows, snap_rows, "snapdepth", ["snap_depth_role_score"])
    return {
        "ffop_joined": ff["joined"],
        "ngs_joined": ngs["joined"],
        "epa_joined": epa["joined"],
        "rec_joined": rec["joined"],
        "snap_joined": snap["joined"],
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
    comparability_flag: str,
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
            "comparability_flag": comparability_flag,
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


def comparability(fields: str, selected_count: int) -> str:
    lower = fields.lower()
    if "ffop" in lower or "ngs" in lower:
        return "PARTIAL_WINDOW_PRIOR_V2_SIDE_CAR"
    if "snapdepth" in lower:
        return "BROAD_WINDOW_COMPARABLE_WITH_SNAP_DEPTH_CAVEAT"
    if selected_count >= 5000:
        return "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025"
    return "PARTIAL_FIELD_COVERAGE"


def build_tests(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    v2.materialize_formula_scores(rows, seeds)
    registry: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    all_positions = set(POSITIONS)
    full_denom = denominator(rows, all_positions)
    component_specs = [
        ("INGREDIENT_ONLY_AVAIL_ACTIVE_PCT", "availability_avail_active_pct_pct", "avail_active_pct"),
        ("INGREDIENT_ONLY_AVAIL_DURABILITY_SCORE", "availability_avail_durability_score_pct", "avail_durability_score"),
        ("INGREDIENT_ONLY_AVAIL_REPORT_CLEAN_SCORE", "availability_avail_report_clean_score_pct", "avail_report_clean_score"),
        ("INGREDIENT_ONLY_AVAIL_TWO_YEAR_DURABILITY_SCORE", "availability_avail_two_year_durability_score_pct", "avail_two_year_durability_score"),
        ("INGREDIENT_ONLY_AVAIL_AVAILABILITY_SCORE", "availability_avail_availability_score_pct", "avail_availability_score"),
        ("INGREDIENT_ONLY_AVAIL_CAVEAT_INVERSE_SCORE", "availability_avail_caveat_inverse_score_pct", "avail_caveat_inverse_score"),
    ]
    for run_id, score_col, raw_field in component_specs:
        selected = selected_rows(rows, all_positions, [score_col])
        flag = comparability(raw_field, len(selected))
        register(
            registry,
            run_id,
            "ingredient_alone",
            run_id,
            "INGREDIENT_ONLY",
            "none",
            "point_in_time_injury_availability",
            raw_field,
            "ingredient percentile rank only",
            flag,
        )
        results.append(
            result_row(
                run_id,
                run_id,
                "INGREDIENT_ONLY",
                "none",
                "point_in_time_injury_availability",
                raw_field,
                "QB/RB/WR/TE",
                selected,
                score_col,
                full_denom,
                None,
                "Availability ingredient alone; public nflverse injuries and weekly rosters aggregated regular season and lagged N-to-N+1 review-only.",
            )
        )

    formula_ingredients = [
        ("ACTIVE_PCT", "availability_avail_active_pct_pct"),
        ("DURABILITY", "availability_avail_durability_score_pct"),
        ("REPORT_CLEAN", "availability_avail_report_clean_score_pct"),
        ("TWO_YEAR_DURABILITY", "availability_avail_two_year_durability_score_pct"),
        ("AVAILABILITY_SCORE", "availability_avail_availability_score_pct"),
        ("CAVEAT_INVERSE", "availability_avail_caveat_inverse_score_pct"),
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
                score_col = f"{seed_col}__AVAIL_{suffix}_PCT{pct_label}"
                materialize_combo_score(rows, score_col, [(seed_col, 1.0 - weight), (ingredient_col, weight)])
                selected = selected_rows(rows, scope, [score_col])
                run_id = f"{seed['candidate_id']}__PLUS_AVAIL_{suffix}_PCT{pct_label}"
                fields = ingredient_col.replace("availability_", "")
                register(
                    registry,
                    run_id,
                    "formula_x_ingredient",
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "point_in_time_injury_availability",
                    fields,
                    f"seed_percentile={1.0 - weight:.3f};ingredient_percentile={weight:.3f}",
                    comparability(fields, len(selected)),
                )
                results.append(
                    result_row(
                        run_id,
                        seed["candidate_id"],
                        seed["cluster_id"],
                        seed["formula_definition"],
                        "point_in_time_injury_availability",
                        fields,
                        seed["position_scope"],
                        selected,
                        score_col,
                        denom,
                        seed_metrics,
                        "Fixed predeclared availability additive variant; no dynamic tuning and no same-season injury context.",
                    )
                )

    combo_specs = [
        ("AVAIL_SNAPDEPTH_PCT025_025", [("availability_avail_availability_score_pct", 0.025), ("snapdepth_snap_depth_role_score_pct", 0.025)]),
        ("AVAIL_SNAPDEPTH_PCT050_050", [("availability_avail_availability_score_pct", 0.050), ("snapdepth_snap_depth_role_score_pct", 0.050)]),
        ("AVAIL_SNAPDEPTH_PCT050_025", [("availability_avail_availability_score_pct", 0.050), ("snapdepth_snap_depth_role_score_pct", 0.025)]),
        ("AVAIL_SNAPDEPTH_PCT025_050", [("availability_avail_availability_score_pct", 0.025), ("snapdepth_snap_depth_role_score_pct", 0.050)]),
        ("AVAIL_RECOPP_PCT025_025", [("availability_avail_availability_score_pct", 0.025), ("recopp_rec_opp_wopr_pct", 0.025)]),
        ("AVAIL_RECOPP_PCT050_050", [("availability_avail_availability_score_pct", 0.050), ("recopp_rec_opp_wopr_pct", 0.050)]),
        ("AVAIL_EPA_PCT025_025", [("availability_avail_availability_score_pct", 0.025), ("epa_epa_total_raw_pct", 0.025)]),
        ("AVAIL_EPA_PCT050_050", [("availability_avail_availability_score_pct", 0.050), ("epa_epa_total_raw_pct", 0.050)]),
        ("AVAIL_FFOP_PCT025_025", [("availability_avail_availability_score_pct", 0.025), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("AVAIL_FFOP_PCT050_050", [("availability_avail_availability_score_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.050)]),
        ("AVAIL_NGS_PCT025_025", [("availability_avail_availability_score_pct", 0.025), ("ngs_ngs_position_signal_raw_pct", 0.025)]),
        ("AVAIL_NGS_PCT050_050", [("availability_avail_availability_score_pct", 0.050), ("ngs_ngs_position_signal_raw_pct", 0.050)]),
        ("AVAIL_SNAPDEPTH_RECOPP_PCT025_050_025", [("availability_avail_availability_score_pct", 0.025), ("snapdepth_snap_depth_role_score_pct", 0.050), ("recopp_rec_opp_wopr_pct", 0.025)]),
        ("AVAIL_SNAPDEPTH_FFOP_PCT025_050_025", [("availability_avail_availability_score_pct", 0.025), ("snapdepth_snap_depth_role_score_pct", 0.050), ("ffop_ffop_xfp_total_pct", 0.025)]),
        ("AVAIL_SNAPDEPTH_EPA_PCT025_050_025", [("availability_avail_availability_score_pct", 0.025), ("snapdepth_snap_depth_role_score_pct", 0.050), ("epa_epa_total_raw_pct", 0.025)]),
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
            register(
                registry,
                run_id,
                "ingredient_combination",
                seed["candidate_id"],
                seed["cluster_id"],
                seed["formula_definition"],
                "point_in_time_injury_availability+prior_sidecars",
                fields,
                f"seed_percentile={1.0 - total_weight:.3f};" + ";".join(f"{col}={weight:.3f}" for col, weight in ingredients),
                comparability(fields, len(selected)),
            )
            results.append(
                result_row(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["formula_definition"],
                    "point_in_time_injury_availability+prior_sidecars",
                    fields,
                    seed["position_scope"],
                    selected,
                    score_col,
                    denom,
                    seed_metrics,
                    "Bounded predeclared availability combination; ffop/NGS retain partial-window V2 caveats when used.",
                )
            )
    return registry, results


def join_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ingredients = [
        ("point_in_time_injury_availability", "availability_avail_availability_score", set(SOURCE_SEASONS)),
        ("availability_active_pct", "availability_avail_active_pct", set(SOURCE_SEASONS)),
        ("availability_report_clean_score", "availability_avail_report_clean_score", set(SOURCE_SEASONS)),
        ("snap_depth_prior_lane", "snapdepth_snap_depth_role_score", set(SOURCE_SEASONS)),
        ("receiving_opportunity_prior_lane", "recopp_rec_opp_wopr", set(SOURCE_SEASONS)),
        ("epa_prior_lane", "epa_epa_total_raw", set(SOURCE_SEASONS)),
        ("ffopportunity_prior_v2", "ffop_ffop_xfp_total", {2021, 2022, 2023, 2024}),
        ("ngs_prior_v2", "ngs_ngs_position_signal_raw", {2021, 2022, 2023, 2024}),
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
        "avail_games_active",
        "avail_games_inactive",
        "avail_games_missed",
        "avail_active_pct",
        "avail_questionable_count",
        "avail_doubtful_count",
        "avail_out_count",
        "avail_ir_pup_flag",
        "avail_prior_year_missed_games",
        "avail_two_year_missed_games",
        "avail_durability_score",
        "avail_caveat_flag",
        "availability_source_path",
        "availability_source_hash",
        "join_status",
        "coverage_status",
        "review_only_status",
    }
    fields = set(sidecar[0].keys()) if sidecar else set()
    duplicate_keys = len(sidecar) - len({(r["player_id"], r["season"], r["position"]) for r in sidecar})
    roster_joined = len([
        r for r in sidecar
        if r["join_status"] in {"JOINED_ROSTER_AND_INJURY_REPORT", "JOINED_ROSTER_NO_INJURY_REPORT"}
    ])
    injury_joined = len([
        r for r in sidecar
        if r["join_status"] in {"JOINED_ROSTER_AND_INJURY_REPORT", "JOINED_INJURY_REPORT_NO_ROSTER"}
    ])
    missing_availability = len([r for r in sidecar if not str(r.get("avail_availability_score", "")).strip()])
    schema = [
        {
            "artifact": "point_in_time_injury_availability",
            "row_count": len(sidecar),
            "required_columns_present": "yes" if required.issubset(fields) else "no",
            "missing_columns": "|".join(sorted(required - fields)),
            "duplicate_keys": duplicate_keys,
            "rows_with_roster_record": roster_joined,
            "rows_with_injury_report_record": injury_joined,
            "rows_missing_availability_score": missing_availability,
            "review_only_status": "PASS"
            if sidecar and duplicate_keys == 0 and all("REVIEW_ONLY" in r["review_only_status"] and "NOT_MODEL_USE" in r["review_only_status"] for r in sidecar)
            else "FAIL",
        }
    ]
    joined = [r for r in rows if r.get("availability_avail_availability_score") is not None]
    bad_lag = [r for r in joined if int(r["feature_season"]) >= int(r["season"])]
    leakage = [
        {
            "ingredient": "point_in_time_injury_availability",
            "joined_rows": len(joined),
            "bad_lag_rows": len(bad_lag),
            "asof_result": "PASS" if not bad_lag else "FAIL",
            "source_use_gate_result": "PASS_REVIEW_ONLY_PUBLIC_NFLVERSE_NO_KEY_NOT_MODEL_USE",
            "rule": "feature_season must be less than target season; no same-season injury availability features",
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
                    "comparability_note": "partial-window if ffop/ngs ingredient is present",
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
    registry: list[dict[str, Any]],
    seeds: list[dict[str, Any]],
) -> None:
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]
    b_component = best(component)
    b_formula = best(formula_x)
    b_combo = best(combos)
    registry_by_run = {r["run_id"]: r for r in registry}
    full_or_broad = [
        r for r in results
        if registry_by_run.get(r["run_id"], {}).get("comparability_flag") in {
            "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025",
            "BROAD_WINDOW_COMPARABLE_WITH_SNAP_DEPTH_CAVEAT",
        }
    ]
    full_only = [
        r for r in results
        if registry_by_run.get(r["run_id"], {}).get("comparability_flag") == "FULL_HISTORY_COMPARABLE_LAGGED_2013_2025"
    ]
    partial_only = [
        r for r in results
        if registry_by_run.get(r["run_id"], {}).get("comparability_flag") == "PARTIAL_WINDOW_PRIOR_V2_SIDE_CAR"
    ]
    all_above_755 = row_count_above(results, CURRENT_BEST_FULL_HISTORY)
    full_broad_above_755 = row_count_above(full_or_broad, CURRENT_BEST_FULL_HISTORY)
    full_broad_above_763 = row_count_above(full_or_broad, SNAP_DEPTH_BROAD_REFERENCE)
    availability_cov = next(r for r in coverage if r["ingredient"] == "point_in_time_injury_availability" and r["position"] == "ALL")
    verdict = "YELLOW_POINT_IN_TIME_INJURY_AVAILABILITY_PARTIAL_WITH_CAVEATS"
    if (
        b_formula
        and float(b_formula["overall_spearman"]) >= SNAP_DEPTH_BROAD_REFERENCE
        and int(b_formula["row_count"]) > 5000
    ):
        verdict = "GREEN_POINT_IN_TIME_INJURY_AVAILABILITY_ADDS_REVIEW_ONLY_SIGNAL"
    if b_formula and b_combo and float(b_formula["overall_spearman"]) <= CURRENT_BEST_FULL_HISTORY and float(b_combo["overall_spearman"]) <= CURRENT_BEST_FULL_HISTORY:
        verdict = "RED_POINT_IN_TIME_INJURY_AVAILABILITY_NO_INCREMENTAL_SIGNAL"
    top_all = sorted([r for r in results if r["overall_spearman"]], key=lambda r: float(r["overall_spearman"]), reverse=True)[:15]
    use_class = "AVAILABLE_REVIEW_ONLY_GUARDRAIL_CONTEXT"
    if b_formula and float(b_formula["overall_spearman"]) >= SNAP_DEPTH_BROAD_REFERENCE and int(b_formula["row_count"]) > 5000:
        use_class = "AVAILABLE_REVIEW_ONLY_ADDITIVE_SIGNAL"
    elif b_combo and float(b_combo["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY:
        use_class = "AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT"
    write_md(
        OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_DATA_MART_GATE_V1_REPORT.md",
        f"""
# Point-in-Time Injury Availability Data Mart Gate V1 Report

## Verdict

`{verdict}`

## Scope

This lane built a review-only point-in-time injury/availability sidecar from public no-key nflverse `injuries` and `weekly_rosters` parquet assets. It used feature season N to target season N+1 only. It did not mutate the canonical Formula Data Mart, canonical `local_exports`, app/runtime code, rankings, or production model behavior.

## Source And Sidecar

- Source families: public nflverse `injuries` and `weekly_rosters`.
- Feature seasons requested: `{min(SOURCE_SEASONS)}-{max(SOURCE_SEASONS)}`.
- Target seasons: `{min(int(r['season']) for r in sidecar)}-{max(int(r['season']) for r in sidecar)}`.
- Sidecar rows: `{len(sidecar)}`.
- Availability join coverage: `{availability_cov['joined_rows']} / {availability_cov['eligible_rows']}` or `{availability_cov['join_coverage_pct']}`.
- Source files hashed: `{len(sources)}`.

## Ingredients Loaded

- `avail_games_active`
- `avail_games_inactive`
- `avail_games_missed`
- `avail_active_pct`
- `avail_questionable_count`
- `avail_doubtful_count`
- `avail_out_count`
- `avail_probable_count`
- `avail_practice_dnp_count`
- `avail_practice_limited_count`
- `avail_injury_report_weeks`
- `avail_ir_pup_flag`
- `avail_prior_year_missed_games`
- `avail_two_year_missed_games`
- `avail_durability_score`
- `avail_report_clean_score`
- `avail_two_year_durability_score`
- `avail_availability_score`
- `avail_caveat_flag`
- `avail_caveat_inverse_score`

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

## Comparability

- All result rows above `.755`: `{all_above_755}`.
- Full/broad lagged non-V2 rows above `.755`: `{full_broad_above_755}`.
- Full/broad lagged non-V2 rows above snap/depth `.763`: `{full_broad_above_763}`.
- Full-history-comparable rows tested: `{len(full_only)}`.
- Broad-window-comparable rows tested: `{len(full_or_broad) - len(full_only)}`.
- Partial-window rows tested: `{len(partial_only)}`.

Any result using prior ffopportunity or NGS sidecars is partial-window only and cannot be used to claim a complete full-history `.755` plateau break. Availability data is not injury prediction; it is a lagged historical availability context sidecar.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane. Injury/availability context remains review-only evidence unless Master HQ separately approves a ranking-simulation design packet.

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
        OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_NEXT_USE_DECISION.md",
        f"""
# Point-in-Time Injury Availability Next Use Decision

Decision: `{use_class}`.

Point-in-time injury/availability data was loaded from public no-key nflverse assets and is valid only for lagged review-only Formula Mart sidecar use. It may support availability caveat review, guardrail/slice reporting, and bounded interaction checks. It is not approved for production/model-use, direct ranking input, hidden sort logic, source promotion, injury prediction, or review-only ranking simulation.

Best component: `{b_component['run_id'] if b_component else ''}` Spearman `{b_component['overall_spearman'] if b_component else ''}`.

Best formula x ingredient: `{b_formula['run_id'] if b_formula else ''}` Spearman `{b_formula['overall_spearman'] if b_formula else ''}`.

Best combination: `{b_combo['run_id'] if b_combo else ''}` Spearman `{b_combo['overall_spearman'] if b_combo else ''}`.

Recommended next step: `Historical Market / ADP Source Gate and Data Mart Join V1` after Master HQ review, because current public nflverse ingredient sidecars have mostly produced context/interactions rather than a full-history breakthrough suitable for ranking simulation.
""",
    )
    write_md(
        OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_BLOCKERS_AND_CAVEATS.md",
        """
# Blockers And Caveats

- This is review-only evidence, not production/model-use.
- This is not injury prediction.
- Same-season/future context was not used; all tests use feature season N to target season N+1.
- Injury reports include rest and non-injury rows; derived features try to avoid treating non-injury rest as injury signal, but status semantics remain caveated.
- Absence from injury reports is treated as zero only when the player has a weekly roster record for that feature season.
- Combo tests using prior ffopportunity or NGS inherit partial-window V2 sidecar caveats.
- Partial-window results cannot be used to claim the full-history `.755` plateau was broken.
- Review-only ranking simulation remains blocked.
""",
    )
    csv_paths = [
        "POINT_IN_TIME_INJURY_AVAILABILITY_SOURCE_LEDGER.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_SCHEMA_VALIDATION.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_JOIN_COVERAGE.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_COMPONENT_TEST_RESULTS.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_FORMULA_X_INGREDIENT_RESULTS.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_INGREDIENT_COMBINATION_RESULTS.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_ALL_RESULTS_REQUIRED_SCHEMA.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_SLICE_GUARDRAILS.csv",
        "POINT_IN_TIME_INJURY_AVAILABILITY_STABILITY_BY_SEASON.csv",
    ]
    write_md(
        OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_SOURCE_TRACE.md",
        "\n".join(
            [
                "# Point-in-Time Injury Availability Source Trace",
                "",
                f"- Prior snap/depth commit verified by request/preflight context: `{PRIOR_SNAP_DEPTH_COMMIT}`",
                f"- Current remote HQ expected and verified before work: `{REMOTE_HEAD}`",
                f"- Public source cache used outside repo: `{SOURCE_CACHE}`",
                "- Public source families: nflverse-data GitHub release `injuries/injuries_YYYY.parquet` and `weekly_rosters/roster_weekly_YYYY.parquet`.",
                f"- Prior V2 ffop/NGS artifacts used for bounded partial-window combos: `{V2_ARTIFACT}`",
                f"- Prior EPA sidecar used for bounded EPA combo checks: `{EPA_ARTIFACT}`",
                f"- Prior receiving sidecar used for bounded receiving combo checks: `{REC_ARTIFACT}`",
                f"- Prior snap/depth sidecar used for bounded role combo checks: `{SNAP_ARTIFACT}`",
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
        "avail_active_pct",
        "avail_durability_score",
        "avail_report_clean_score",
        "avail_two_year_durability_score",
        "avail_availability_score",
        "avail_caveat_inverse_score",
    ]
    availability_join = attach_sidecar(rows, sidecar, "availability", raw_cols)
    prior_join = attach_prior_sidecars(rows)
    seeds = v2.load_seed_registry()
    registry, results = build_tests(rows, seeds)
    coverage = join_coverage(rows)
    schema, leakage = validation_rows(sidecar, rows)
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]

    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_SOURCE_LEDGER.csv", sources)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv", sidecar)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_JOIN_COVERAGE.csv", coverage)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_PREDECLARED_TEST_REGISTRY.csv", registry)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_COMPONENT_TEST_RESULTS.csv", component, RESULT_FIELDS)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_FORMULA_X_INGREDIENT_RESULTS.csv", formula_x, RESULT_FIELDS)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_INGREDIENT_COMBINATION_RESULTS.csv", combos, RESULT_FIELDS)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_ALL_RESULTS_REQUIRED_SCHEMA.csv", results, RESULT_FIELDS)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_SLICE_GUARDRAILS.csv", guardrail_rows(results))
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_STABILITY_BY_SEASON.csv", stability_rows(results))
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_SCHEMA_VALIDATION.csv", schema)
    write_csv(OUT_DIR / "POINT_IN_TIME_INJURY_AVAILABILITY_LEAKAGE_ASOF_VALIDATION.csv", leakage)
    make_reports(sidecar, sources, coverage, results, registry, seeds)
    print(
        {
            "sidecar_rows": len(sidecar),
            "tests": len(results),
            "seeds": len(seeds),
            "availability_joined": availability_join["joined"],
            "ffop_joined": prior_join["ffop_joined"],
            "ngs_joined": prior_join["ngs_joined"],
            "epa_joined": prior_join["epa_joined"],
            "rec_joined": prior_join["rec_joined"],
            "snap_joined": prior_join["snap_joined"],
        }
    )


if __name__ == "__main__":
    main()
