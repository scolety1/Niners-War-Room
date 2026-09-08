"""NWR class-time autonomous hardening, section 9: K/DST direct-model
research baseline. RESEARCH ONLY -- never promoted, never wired into any
live recommendation path. Builds a simple, real, chronologically-evaluated
(walk-forward: train on strictly-prior seasons only) linear baseline for
(a) Kicker fantasy scoring from real FG/PAT usage, and (b) DST fantasy
scoring from real, individual-defensive-player events aggregated to the
team-week level plus real points-allowed from the real schedule.

Real, explicit, disclosed scoring formulas used as the TARGET (neither is
computed by nflverse itself -- verified: nflverse's own `fantasy_points`
column is 0.0 for every real K row in this repo's own snapshot, and no
DST/DEF row exists in the player-level stats tables at all):

  KICKER (per real game): 3 pts/FG make (0-39yd), 4 pts/FG make (40-49yd),
  5 pts/FG make (50+yd), 1 pt/PAT make. A common, standard half-PPR-style
  kicker scoring rule -- not this project's own invention, disclosed here
  so any different owner league rule can be swapped in later.

  DST (per real team-week): 1 pt/sack, 2 pts/INT, 2 pts/fumble recovery,
  6 pts/defensive TD, 2 pts/safety, plus a real points-allowed tier bonus
  (0 allowed: +10, 1-6: +7, 7-13: +4, 14-20: +1, 21-27: 0, 28-34: -1,
  35+: -4) using the real opponent score from nflverse's own schedule.

Real, permanent, reproducible script -- rerun with an unmodified copy of
this file against the same real snapshot data to reproduce these numbers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
CACHE_DIR = Path(__file__).resolve().parent
WEEKLY_STATS_RAW = Path(
    r"C:\NWR_SHARED_DATA\source_snapshots\nflverse\player_stats_weekly"
    r"\20260730T072407Z-fe7ff02872e4\raw"
)
SEASONS = list(range(2017, 2026))


def _load_weekly(seasons: list[int]) -> pd.DataFrame:
    frames = []
    for season in seasons:
        path = WEEKLY_STATS_RAW / f"player_stats_weekly_{season}.parquet"
        frames.append(pd.read_parquet(path))
    return pd.concat(frames, ignore_index=True)


def _load_schedules_cached() -> pd.DataFrame:
    cache_path = CACHE_DIR / "schedules_2017_2025_cache.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    import nflreadpy as nfl

    sched = nfl.load_schedules(seasons=SEASONS).to_pandas()
    sched = sched[
        ["season", "week", "game_type", "home_team", "away_team", "home_score", "away_score"]
    ].dropna(subset=["home_score", "away_score"])
    sched.to_parquet(cache_path, index=False)
    return sched


def _kicker_points(row: pd.Series) -> float:
    fg = (
        3.0 * float(row.get("fg_made_0_19", 0) or 0)
        + 3.0 * float(row.get("fg_made_20_29", 0) or 0)
        + 3.0 * float(row.get("fg_made_30_39", 0) or 0)
        + 4.0 * float(row.get("fg_made_40_49", 0) or 0)
        + 5.0 * float(row.get("fg_made_50_59", 0) or 0)
        + 5.0 * float(row.get("fg_made_60_", 0) or 0)
    )
    pat = 1.0 * float(row.get("pat_made", 0) or 0)
    return fg + pat


def _points_allowed_bonus(points_allowed: float) -> float:
    if points_allowed <= 0:
        return 10.0
    if points_allowed <= 6:
        return 7.0
    if points_allowed <= 13:
        return 4.0
    if points_allowed <= 20:
        return 1.0
    if points_allowed <= 27:
        return 0.0
    if points_allowed <= 34:
        return -1.0
    return -4.0


def build_kicker_week_frame(weekly: pd.DataFrame) -> pd.DataFrame:
    k = weekly[weekly["position"].eq("K")].copy()
    k = k[k["season_type"].eq("REG")]
    fg_cols = [
        "fg_made_0_19", "fg_made_20_29", "fg_made_30_39", "fg_made_40_49",
        "fg_made_50_59", "fg_made_60_", "fg_att", "pat_made", "pat_att",
    ]
    for col in fg_cols:
        k[col] = pd.to_numeric(k[col], errors="coerce").fillna(0.0)
    k["real_points"] = k.apply(_kicker_points, axis=1)
    return k[["player_id", "player_display_name", "team", "season", "week", *fg_cols, "real_points"]]


def build_dst_week_frame(weekly: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    def_cols = ["def_sacks", "def_interceptions", "def_tds", "def_safeties"]
    fumble_cols = ["fumble_recovery_own", "fumble_recovery_opp"]
    defense = weekly[weekly["season_type"].eq("REG")].copy()
    for col in def_cols + fumble_cols:
        defense[col] = pd.to_numeric(defense[col], errors="coerce").fillna(0.0)
    defense["fumble_recoveries"] = defense["fumble_recovery_own"] + defense["fumble_recovery_opp"]
    team_week = (
        defense.groupby(["season", "week", "team"], as_index=False)[
            ["def_sacks", "def_interceptions", "def_tds", "def_safeties", "fumble_recoveries"]
        ].sum()
    )
    # Real points-allowed: this team's opponent's real score that week.
    home = schedules.rename(
        columns={"home_team": "team", "away_team": "opponent", "away_score": "points_allowed"}
    )[["season", "week", "team", "opponent", "points_allowed"]]
    away = schedules.rename(
        columns={"away_team": "team", "home_team": "opponent", "home_score": "points_allowed"}
    )[["season", "week", "team", "opponent", "points_allowed"]]
    games = pd.concat([home, away], ignore_index=True)
    merged = team_week.merge(games, on=["season", "week", "team"], how="inner")
    merged["real_points"] = (
        1.0 * merged["def_sacks"]
        + 2.0 * merged["def_interceptions"]
        + 2.0 * merged["fumble_recoveries"]
        + 6.0 * merged["def_tds"]
        + 2.0 * merged["def_safeties"]
        + merged["points_allowed"].apply(_points_allowed_bonus)
    )
    return merged


def _fit_ols(train_x: np.ndarray, train_y: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(train_x)), train_x])
    coefficients, *_ = np.linalg.lstsq(design, train_y, rcond=None)
    return coefficients


def _predict_ols(coefficients: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coefficients


def _season_over_season_pairs(
    season_agg: pd.DataFrame, key_col: str, feature_cols: list[str]
) -> pd.DataFrame:
    """Real PRIOR-season features -> real NEXT-season real_points, for the
    same real player/team, both real seasons present. This is the genuine
    predictive-skill framing this whole project's persistence-projection
    paradigm already uses elsewhere -- a model that regresses a season's
    real_points on THAT SAME season's own concurrent event counts would be
    trivially near-perfect (the target is a deterministic linear function
    of those same counts) and would not be testing prediction at all."""
    prior = season_agg.copy()
    prior["season"] = prior["season"] + 1
    prior = prior.rename(columns={col: f"prior_{col}" for col in feature_cols})
    prior = prior.rename(columns={"real_points": "prior_real_points"})
    merged = season_agg.merge(
        prior[[key_col, "season", *[f"prior_{c}" for c in feature_cols], "prior_real_points"]],
        on=[key_col, "season"],
        how="inner",
    )
    return merged


def walk_forward_kicker(kicker_weeks: pd.DataFrame) -> pd.DataFrame:
    """Real per-SEASON aggregation, walk-forward: train an OLS model on
    strictly-prior seasons' (real player's PRIOR-season FG attempts by
    distance + PAT attempts) -> (real NEXT-season total kicker points),
    then predict each held-out season from that same real kicker's own
    real PRIOR-season workload -- a genuine, real predictive question,
    not a same-season tautology."""
    season_agg = kicker_weeks.groupby(["player_id", "player_display_name", "season"], as_index=False).agg(
        fg_att=("fg_att", "sum"),
        fg_made_0_19=("fg_made_0_19", "sum"),
        fg_made_20_29=("fg_made_20_29", "sum"),
        fg_made_30_39=("fg_made_30_39", "sum"),
        fg_made_40_49=("fg_made_40_49", "sum"),
        fg_made_50_59=("fg_made_50_59", "sum"),
        fg_made_60_=("fg_made_60_", "sum"),
        pat_att=("pat_att", "sum"),
        real_points=("real_points", "sum"),
        games=("week", "nunique"),
    )
    season_agg = season_agg[season_agg["games"].ge(4)]  # real, minimum-sample floor
    raw_feature_cols = [
        "fg_att", "fg_made_0_19", "fg_made_20_29", "fg_made_30_39",
        "fg_made_40_49", "fg_made_50_59", "fg_made_60_", "pat_att",
    ]
    pairs = _season_over_season_pairs(season_agg, "player_id", raw_feature_cols)
    feature_cols = [f"prior_{c}" for c in raw_feature_cols] + ["prior_real_points"]
    baseline_col = "prior_real_points"
    rows = []
    for target_season in sorted(pairs["season"].unique()):
        train = pairs[pairs["season"].lt(target_season)]
        test = pairs[pairs["season"].eq(target_season)]
        if len(train) < 15 or test.empty:
            continue
        coefficients = _fit_ols(train[feature_cols].to_numpy(dtype=float), train["real_points"].to_numpy(dtype=float))
        predicted = _predict_ols(coefficients, test[feature_cols].to_numpy(dtype=float))
        for (_, record), prediction in zip(test.iterrows(), predicted, strict=True):
            rows.append(
                {
                    "season": target_season,
                    "player": record["player_display_name"],
                    "actual": record["real_points"],
                    "predicted": max(0.0, float(prediction)),
                    "baseline_predicted": record[baseline_col],  # naive: repeat prior year's real total
                    "train_rows": len(train),
                }
            )
    return pd.DataFrame(rows)


def walk_forward_dst(dst_weeks: pd.DataFrame) -> pd.DataFrame:
    """Same real walk-forward structure as the kicker model, at the real
    TEAM-SEASON level: real PRIOR-season defensive event totals + real
    prior-season average points allowed -> real NEXT-season DST total."""
    season_agg = dst_weeks.groupby(["team", "season"], as_index=False).agg(
        def_sacks=("def_sacks", "sum"),
        def_interceptions=("def_interceptions", "sum"),
        fumble_recoveries=("fumble_recoveries", "sum"),
        def_tds=("def_tds", "sum"),
        def_safeties=("def_safeties", "sum"),
        points_allowed=("points_allowed", "mean"),
        real_points=("real_points", "sum"),
        games=("week", "nunique"),
    )
    season_agg = season_agg[season_agg["games"].ge(4)]
    raw_feature_cols = [
        "def_sacks", "def_interceptions", "fumble_recoveries", "def_tds",
        "def_safeties", "points_allowed",
    ]
    pairs = _season_over_season_pairs(season_agg, "team", raw_feature_cols)
    feature_cols = [f"prior_{c}" for c in raw_feature_cols] + ["prior_real_points"]
    baseline_col = "prior_real_points"
    rows = []
    for target_season in sorted(pairs["season"].unique()):
        train = pairs[pairs["season"].lt(target_season)]
        test = pairs[pairs["season"].eq(target_season)]
        if len(train) < 15 or test.empty:
            continue
        coefficients = _fit_ols(train[feature_cols].to_numpy(dtype=float), train["real_points"].to_numpy(dtype=float))
        predicted = _predict_ols(coefficients, test[feature_cols].to_numpy(dtype=float))
        for (_, record), prediction in zip(test.iterrows(), predicted, strict=True):
            rows.append(
                {
                    "season": target_season,
                    "team": record["team"],
                    "actual": record["real_points"],
                    "predicted": float(prediction),
                    "baseline_predicted": record[baseline_col],
                    "train_rows": len(train),
                }
            )
    return pd.DataFrame(rows)


def _report(label: str, results: pd.DataFrame) -> None:
    print(f"\n=== {label} ===")
    print(f"Evaluated rows: {len(results)}, seasons: {sorted(results['season'].unique())}")
    mae = float((results["actual"] - results["predicted"]).abs().mean())
    baseline_mae = float((results["actual"] - results["baseline_predicted"]).abs().mean())
    pearson = float(np.corrcoef(results["actual"], results["predicted"])[0, 1])
    spearman = float(
        pd.Series(results["actual"]).rank().corr(pd.Series(results["predicted"]).rank())
    )
    baseline_spearman = float(
        pd.Series(results["actual"]).rank().corr(pd.Series(results["baseline_predicted"]).rank())
    )
    print(f"Direct-model MAE: {mae:.3f}   |   Naive prior-year-persistence baseline MAE: {baseline_mae:.3f}")
    print(f"Direct-model beats naive baseline: {mae < baseline_mae} (lower MAE is better)")
    print(f"Pearson correlation (predicted vs actual): {pearson:.3f}")
    print(f"Spearman rank correlation: {spearman:.3f}   |   Naive baseline Spearman: {baseline_spearman:.3f}")
    per_season_mae = results.groupby("season").apply(
        lambda g: float((g["actual"] - g["predicted"]).abs().mean()), include_groups=False
    )
    print("Per-season MAE (stability check):")
    print(per_season_mae.to_string())
    print(f"MAE std across seasons: {per_season_mae.std():.3f}")


def main() -> None:
    weekly = _load_weekly(SEASONS)
    schedules = _load_schedules_cached()

    kicker_weeks = build_kicker_week_frame(weekly)
    real_kickers = kicker_weeks["player_id"].nunique()
    print(f"Real kicker-weeks loaded: {len(kicker_weeks)} ({real_kickers} distinct real kickers, {SEASONS[0]}-{SEASONS[-1]})")
    kicker_results = walk_forward_kicker(kicker_weeks)
    print(f"Real player-seasons with a real prior real season to predict from (coverage): {len(kicker_results)}")
    _report("KICKER direct-model research baseline (real, walk-forward, NOT promoted)", kicker_results)

    dst_weeks = build_dst_week_frame(weekly, schedules)
    real_teams = dst_weeks["team"].nunique()
    print(f"\nReal team-weeks loaded: {len(dst_weeks)} ({real_teams} distinct real teams, {SEASONS[0]}-{SEASONS[-1]})")
    dst_results = walk_forward_dst(dst_weeks)
    print(f"Real team-seasons with a real prior real season to predict from (coverage): {len(dst_results)}")
    _report("DST direct-model research baseline (real, walk-forward, NOT promoted)", dst_results)

    kicker_results.to_csv(CACHE_DIR / "KICKER_WALK_FORWARD_RESULTS.csv", index=False)
    dst_results.to_csv(CACHE_DIR / "DST_WALK_FORWARD_RESULTS.csv", index=False)


if __name__ == "__main__":
    main()
