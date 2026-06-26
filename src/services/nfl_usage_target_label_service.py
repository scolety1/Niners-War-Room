# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"
DOC_ROOT = Path("docs/hq/data_sources/nfl_usage/target_backtest")
SHARED_CACHE_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest")
TARGET_PANEL_PATH = SHARED_CACHE_ROOT / "nfl_usage_target_labels_v0.csv"
DEFAULT_TARGET_SEASONS = [2023, 2024]
SUPPORTED_POSITIONS = ["QB", "RB", "WR", "TE"]

SCORING_FORMULA = {
    "passing_yards": "passing_yards / 30",
    "passing_tds": "passing_tds * 3",
    "passing_interceptions": "passing_interceptions * -1",
    "rushing_yards": "rushing_yards / 10",
    "rushing_tds": "rushing_tds * 4",
    "receiving_yards": "receiving_yards / 10",
    "receiving_tds": "receiving_tds * 4",
    "rushing_receiving_first_downs": "(rushing_first_downs + receiving_first_downs) * 0.4",
    "return_yards": "(punt_return_yards + kickoff_return_yards) / 30",
    "return_tds": "special_teams_tds * 4",
    "two_point_conversions": "(passing_2pt_conversions + rushing_2pt_conversions + receiving_2pt_conversions) * 2",
    "fumbles_lost": "(sack_fumbles_lost + rushing_fumbles_lost + receiving_fumbles_lost) * -1",
}

TARGET_LABELS = [
    "next_season_nwr_points",
    "next_season_nwr_points_per_game",
    "next_season_games",
    "next_season_position_rank",
    "next_season_top_qb12",
    "next_season_top_rb12",
    "next_season_top_rb24",
    "next_season_top_wr12",
    "next_season_top_wr24",
    "next_season_top_wr36",
    "next_season_top_te12",
    "next_season_starter_level_by_position",
    "next_season_flex_relevant_rb_wr_te",
]


@dataclass(frozen=True)
class TargetBuildResult:
    run_id: str
    run_timestamp: str
    target_panel_path: Path
    target_rows: int
    target_seasons: list[int]
    docs_written: list[Path]
    status: str


def run_id(timestamp: str | None = None) -> str:
    stamp = timestamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(stamp.encode("utf-8")).hexdigest()[:10]
    return f"nfl_usage_target_backtest_v0_{stamp}_{digest}"


def configure_nflreadpy_cache(nflreadpy_module: Any) -> None:
    SHARED_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    config = getattr(nflreadpy_module, "config", None)
    update_config = getattr(config, "update_config", None)
    if update_config is not None:
        update_config(cache_mode="filesystem", cache_dir=SHARED_CACHE_ROOT / "nflreadpy_cache")


def load_player_stats_from_nflreadpy(seasons: list[int]) -> pd.DataFrame:
    import nflreadpy as nfl  # type: ignore[import-not-found]

    configure_nflreadpy_cache(nfl)
    frame = nfl.load_player_stats(seasons, summary_level="reg")
    if hasattr(frame, "to_pandas"):
        frame = frame.to_pandas()
    return pd.DataFrame(frame)


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def derive_nwr_points(player_stats: pd.DataFrame) -> pd.Series:
    points = (
        _num(player_stats, "passing_yards") / 30.0
        + _num(player_stats, "passing_tds") * 3.0
        - _num(player_stats, "passing_interceptions")
        + _num(player_stats, "rushing_yards") / 10.0
        + _num(player_stats, "rushing_tds") * 4.0
        + _num(player_stats, "receiving_yards") / 10.0
        + _num(player_stats, "receiving_tds") * 4.0
        + (_num(player_stats, "rushing_first_downs") + _num(player_stats, "receiving_first_downs")) * 0.4
        + (_num(player_stats, "punt_return_yards") + _num(player_stats, "kickoff_return_yards")) / 30.0
        + _num(player_stats, "special_teams_tds") * 4.0
        + (
            _num(player_stats, "passing_2pt_conversions")
            + _num(player_stats, "rushing_2pt_conversions")
            + _num(player_stats, "receiving_2pt_conversions")
        )
        * 2.0
        - (
            _num(player_stats, "sack_fumbles_lost")
            + _num(player_stats, "rushing_fumbles_lost")
            + _num(player_stats, "receiving_fumbles_lost")
        )
    )
    return points.round(4)


def derive_target_labels(player_stats: pd.DataFrame, run_id_value: str | None = None) -> pd.DataFrame:
    frame = player_stats.copy()
    if "player_display_name" not in frame.columns:
        frame["player_display_name"] = frame.get("player_name", "")
    frame["position"] = frame.get("position", "").astype(str).str.upper()
    frame = frame[frame["position"].isin(SUPPORTED_POSITIONS)].copy()
    frame["nwr_points"] = derive_nwr_points(frame)
    frame["games"] = _num(frame, "games")
    frame["nwr_points_per_game"] = (frame["nwr_points"] / frame["games"].where(frame["games"] > 0)).fillna(0.0).round(4)
    frame["position_rank"] = frame.groupby(["season", "position"])["nwr_points"].rank(method="min", ascending=False).astype(int)
    frame["starter_level_by_position"] = frame.apply(_starter_label, axis=1)
    frame["flex_relevant_rb_wr_te"] = frame.apply(_flex_relevant, axis=1)

    out = pd.DataFrame(
        {
            "run_id": run_id_value or run_id(),
            "target_season": frame["season"].astype(int),
            "player_id": frame["player_id"].astype(str),
            "player_name": frame["player_display_name"].astype(str),
            "position": frame["position"].astype(str),
            "recent_team": frame.get("recent_team", "").astype(str),
            "next_season_nwr_points": frame["nwr_points"],
            "next_season_nwr_points_per_game": frame["nwr_points_per_game"],
            "next_season_games": frame["games"].astype(int),
            "next_season_position_rank": frame["position_rank"].astype(int),
            "next_season_top_qb12": ((frame["position"] == "QB") & (frame["position_rank"] <= 12)).astype(int),
            "next_season_top_rb12": ((frame["position"] == "RB") & (frame["position_rank"] <= 12)).astype(int),
            "next_season_top_rb24": ((frame["position"] == "RB") & (frame["position_rank"] <= 24)).astype(int),
            "next_season_top_wr12": ((frame["position"] == "WR") & (frame["position_rank"] <= 12)).astype(int),
            "next_season_top_wr24": ((frame["position"] == "WR") & (frame["position_rank"] <= 24)).astype(int),
            "next_season_top_wr36": ((frame["position"] == "WR") & (frame["position_rank"] <= 36)).astype(int),
            "next_season_top_te12": ((frame["position"] == "TE") & (frame["position_rank"] <= 12)).astype(int),
            "next_season_starter_level_by_position": frame["starter_level_by_position"],
            "next_season_flex_relevant_rb_wr_te": frame["flex_relevant_rb_wr_te"].astype(int),
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
    )
    return out.sort_values(["target_season", "position", "next_season_position_rank", "player_name"]).reset_index(drop=True)


def _starter_label(row: pd.Series) -> str:
    pos = str(row.get("position", "")).upper()
    rank = int(row.get("position_rank", 9999))
    if pos == "QB":
        return "QB1" if rank <= 12 else "DEPTH"
    if pos == "RB":
        if rank <= 12:
            return "RB1"
        return "RB2" if rank <= 24 else "DEPTH"
    if pos == "WR":
        if rank <= 12:
            return "WR1"
        if rank <= 24:
            return "WR2"
        return "WR3" if rank <= 36 else "DEPTH"
    if pos == "TE":
        return "TE1" if rank <= 12 else "DEPTH"
    return "DEPTH"


def _flex_relevant(row: pd.Series) -> bool:
    pos = str(row.get("position", "")).upper()
    rank = int(row.get("position_rank", 9999))
    return (pos == "RB" and rank <= 36) or (pos == "WR" and rank <= 48) or (pos == "TE" and rank <= 18)


def target_source_audit_rows(run_id_value: str) -> list[dict[str, Any]]:
    allowed = "actual historical NFL player stats from nflverse/nflreadpy/player_stats"
    blocked_sources = [
        ("ADP", "BLOCKED_MARKET_OR_DRAFT_COST"),
        ("market rank", "BLOCKED_MARKET_VALUE"),
        ("DynastyProcess rank/value", "BLOCKED_VENDOR_MARKET_VALUE"),
        ("projections", "BLOCKED_PROJECTION_NOT_ACTUAL_OUTCOME"),
        ("fantasy analyst ranks", "BLOCKED_ANALYST_RANK"),
        ("current rankings", "BLOCKED_CURRENT_RANK"),
        ("candidate rankings", "BLOCKED_CANDIDATE_RANK"),
        ("manually adjusted ranks", "BLOCKED_MANUAL_RANK"),
        ("RotoWire", "BLOCKED_VENDOR_SCRAPE"),
        ("CFBD", "BLOCKED_COLLEGE_LANE"),
        ("proxy drop rows as hard labels", "BLOCKED_PROXY_LABEL"),
        ("unsupported Outcome gaps as negative labels", "BLOCKED_FAKE_NEGATIVE"),
    ]
    rows = [
        {
            "run_id": run_id_value,
            "source_family": "nflreadpy/player_stats",
            "source_name": allowed,
            "approval_status": "APPROVED_FACTUAL_TARGET_SOURCE",
            "allowed_as_target": "yes",
            "blocked_reason": "",
            "leakage_risk": "LOW_IF_FEATURE_SEASON_N_TARGET_SEASON_N_PLUS_1",
            "notes": "Used only for actual next-season scoring/finish labels; no projections, ranks, market, or CFBD.",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
    ]
    for source, reason in blocked_sources:
        rows.append(
            {
                "run_id": run_id_value,
                "source_family": source,
                "source_name": source,
                "approval_status": "BLOCKED",
                "allowed_as_target": "no",
                "blocked_reason": reason,
                "leakage_risk": "NOT_ALLOWED",
                "notes": "Explicitly excluded from NFL usage target/backtest lane.",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
            }
        )
    return rows


def target_manifest_rows(labels: pd.DataFrame, run_id_value: str, panel_path: Path) -> list[dict[str, Any]]:
    seasons = ";".join(str(s) for s in sorted(labels["target_season"].unique()))
    source_fields = ";".join(SCORING_FORMULA)
    rows: list[dict[str, Any]] = []
    for label in TARGET_LABELS:
        if label in {
            "next_season_nwr_points",
            "next_season_nwr_points_per_game",
            "next_season_games",
            "next_season_position_rank",
        }:
            label_type = "continuous_or_ordinal"
        else:
            label_type = "binary_or_bucket"
        rows.append(
            {
                "run_id": run_id_value,
                "label_name": label,
                "label_type": label_type,
                "target_grain": "player_season",
                "source_family": "nflreadpy/player_stats",
                "source_fields": source_fields,
                "derivation_formula": _label_formula(label),
                "seasons_available": seasons,
                "row_count": int(labels[label].notna().sum()) if label in labels.columns else 0,
                "position_scope": _position_scope(label),
                "target_status": "APPROVED_REVIEW_ONLY_TARGET_LABEL",
                "leakage_policy": "feature season N joins only to target season N+1",
                "shared_cache_path": str(panel_path),
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "Factual historical target label; not active model input.",
            }
        )
    return rows


def _label_formula(label: str) -> str:
    if label == "next_season_nwr_points":
        return "sum documented NWR/LVE non-PPR scoring components from factual player_stats target season"
    if label == "next_season_nwr_points_per_game":
        return "next_season_nwr_points / games, zero when games is zero"
    if label == "next_season_games":
        return "games from target-season factual player_stats"
    if label == "next_season_position_rank":
        return "rank next_season_nwr_points descending within target season and position"
    if label == "next_season_starter_level_by_position":
        return "QB top12, RB top12/top24, WR top12/top24/top36, TE top12 buckets"
    if label == "next_season_flex_relevant_rb_wr_te":
        return "RB top36 or WR top48 or TE top18; QB excluded from flex"
    return f"{label.replace('next_season_top_', '').upper()} positional rank threshold from factual scoring"


def _position_scope(label: str) -> str:
    if "_qb" in label:
        return "QB"
    if "_rb" in label:
        return "RB"
    if "_wr" in label:
        return "WR"
    if "_te" in label:
        return "TE"
    if "flex" in label:
        return "RB;WR;TE"
    return "QB;RB;WR;TE"


def coverage_summary_rows(labels: pd.DataFrame, run_id_value: str, panel_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for season, season_frame in labels.groupby("target_season"):
        for label in TARGET_LABELS:
            rows.append(
                {
                    "run_id": run_id_value,
                    "label_name": label,
                    "target_season": int(season),
                    "row_count": int(len(season_frame)),
                    "player_count": int(season_frame["player_id"].nunique()),
                    "qb_count": int((season_frame["position"] == "QB").sum()),
                    "rb_count": int((season_frame["position"] == "RB").sum()),
                    "wr_count": int((season_frame["position"] == "WR").sum()),
                    "te_count": int((season_frame["position"] == "TE").sum()),
                    "missingness_pct": round(float(season_frame[label].isna().mean() * 100.0), 4),
                    "coverage_status": "GREEN_TARGET_LABEL_COVERAGE",
                    "shared_cache_path": str(panel_path),
                    "model_input_allowed": MODEL_INPUT_ALLOWED,
                    "app_wiring_allowed": APP_WIRING_ALLOWED,
                    "notes": "Review-only target coverage from factual NFL player_stats.",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_plan_doc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# NWR NFL Usage Target Label + Backtest V0 Plan",
                "",
                "Purpose: create review-only factual next-season target labels and leakage-safe diagnostics for NFL usage fields.",
                "",
                "Approved target source: factual historical NFL player statistics from nflverse/nflreadpy `player_stats` only.",
                "",
                "Blocked target sources: ADP, market rank, DynastyProcess rank/value, projections, fantasy analyst ranks, current/candidate/manual rankings, RotoWire, CFBD, proxy drop rows, and unsupported Outcome gaps.",
                "",
                "League scoring policy: 1QB, non-PPR; pass yards 1/30, pass TD 3, interception -1, rush/rec yards 1/10, rush/rec TD 4, rush/rec first down 0.4, return yards 1/30, return TD 4 via special teams TD where available, two-point conversion 2, fumble lost -1. K is excluded from usage backtest labels.",
                "",
                "Target label definitions: next-season NWR points, points per game, games, positional rank, QB/RB/WR/TE top-threshold labels, starter-level buckets, and RB/WR/TE flex relevance.",
                "",
                "Feature/target split: feature season N may join only to target season N+1. No target-season usage feature is allowed.",
                "",
                "Leakage policy: no market/projection/rank fields, no current rankings, no target-season feature windows, no CFBD, and no vendor scrape inputs.",
                "",
                "Minimum coverage: at least one complete feature season joined to the next factual target season for diagnostics; more seasons are required before model-candidate promotion.",
                "",
                "Position-specific targets: QB top12, RB top12/top24, WR top12/top24/top36, TE top12, RB/WR/TE flex relevance.",
                "",
                "Missing-data policy: missing factual scoring components are treated as zero only when the source omits that stat field; missing player rows are not fabricated.",
                "",
                "No-CFBD boundary: this lane does not read, write, or depend on CFBD files or college/rookie evidence.",
                "",
                "No-market/no-projection/no-rank target boundary: target truth is actual factual NFL production only.",
                "",
                "No-model/no-app boundary: all outputs remain `model_input_allowed=no` and `app_wiring_allowed=no`; no app page or model integration is performed.",
                "",
                "Parallel-lane safety policy: changes are boxed to `docs/hq/data_sources/nfl_usage/target_backtest/`, the two NFL usage target/backtest services, scripts, and focused tests.",
                "",
                "Stop conditions: dirty branch, CFBD changes, dependency changes, app/navigation changes, source-truth/rank/model changes, insufficient factual labels, raw payload staged, or leakage violation.",
                "",
                "Validation checklist: pytest, Ruff, compile, CSV load validation, diff check, raw/shared tracked scan, CFBD/dependency/app/model/rank/source-truth scans, frozen board row count, pinned hash.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_target_label_artifacts(
    *,
    seasons: list[int] | None = None,
    doc_root: Path = DOC_ROOT,
    target_panel_path: Path = TARGET_PANEL_PATH,
    player_stats: pd.DataFrame | None = None,
) -> TargetBuildResult:
    target_seasons = seasons or DEFAULT_TARGET_SEASONS
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id_value = run_id(timestamp)
    stats = player_stats if player_stats is not None else load_player_stats_from_nflreadpy(target_seasons)
    labels = derive_target_labels(stats, run_id_value)
    target_panel_path.parent.mkdir(parents=True, exist_ok=True)
    labels.to_csv(target_panel_path, index=False)

    docs = [
        doc_root / "NWR_NFL_USAGE_TARGET_LABEL_BACKTEST_V0_PLAN_20260624.md",
        doc_root / "nfl_usage_target_source_audit_v0.csv",
        doc_root / "nfl_usage_target_label_manifest_v0.csv",
        doc_root / "nfl_usage_target_label_coverage_summary_v0.csv",
    ]
    write_plan_doc(docs[0])
    write_csv(docs[1], target_source_audit_rows(run_id_value))
    write_csv(docs[2], target_manifest_rows(labels, run_id_value, target_panel_path))
    write_csv(docs[3], coverage_summary_rows(labels, run_id_value, target_panel_path))
    return TargetBuildResult(
        run_id=run_id_value,
        run_timestamp=timestamp,
        target_panel_path=target_panel_path,
        target_rows=len(labels),
        target_seasons=target_seasons,
        docs_written=docs,
        status="GREEN_TARGET_LABELS_CREATED",
    )


def validate_review_only_flags(paths: list[Path]) -> None:
    for path in paths:
        frame = pd.read_csv(path, keep_default_na=False)
        for column in ("model_input_allowed", "app_wiring_allowed"):
            if column in frame.columns and not frame[column].astype(str).str.lower().eq("no").all():
                raise ValueError(f"{path} has non-no {column}")
