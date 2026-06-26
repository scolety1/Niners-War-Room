from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

# ruff: noqa: E501

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_ROOT = REPO_ROOT / "docs" / "hq" / "data_sources" / "nfl_usage" / "historical_panel"
SHARED_CACHE_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel")
NFLREADPY_CACHE_ROOT = SHARED_CACHE_ROOT / "nflreadpy_cache"
PANEL_ROOT = SHARED_CACHE_ROOT / "panels"

DEFAULT_SEASONS = [2022, 2023, 2024]
CORE_POSITIONS = {"QB", "RB", "WR", "TE"}
PRIMARY_DISPLAY_FIELDS = [
    "offense_snaps",
    "offense_pct",
    "targets",
    "carries",
    "receptions",
    "touches",
    "opportunities",
    "rushing_yards",
    "receiving_yards",
    "receiving_air_yards",
    "receiving_yards_after_catch",
    "rushing_first_downs",
    "receiving_first_downs",
    "red_zone_carries",
    "red_zone_targets",
    "red_zone_touches",
    "inside_10_carries",
    "inside_10_targets",
    "inside_10_touches",
    "inside_5_carries",
    "inside_5_targets",
    "inside_5_touches",
]
VALID_READINESS_STATUSES = {
    "COVERAGE_READY_FOR_FUTURE_BACKTEST",
    "YELLOW_COVERAGE_READY_WITH_CAVEATS",
    "RESEARCH_ONLY_NOT_BACKTEST_READY",
    "BLOCKED_LICENSED_DATA_GAP",
    "BLOCKED_UNSAFE",
    "BLOCKED_INSUFFICIENT_COVERAGE",
}


@dataclass(frozen=True)
class SourceSpec:
    source_family: str
    loader_name: str
    seasons: tuple[int, ...] | None
    kwargs: dict[str, Any]
    grain: str
    research_only: bool = False


@dataclass(frozen=True)
class HistoricalPanelResult:
    doc_root: Path
    shared_cache_root: Path
    files_written: tuple[Path, ...]
    source_status: dict[str, str]
    panel_status: dict[str, str]
    backtest_status: str


SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec("player_stats", "load_player_stats", tuple(DEFAULT_SEASONS), {"summary_level": "week"}, "player_week"),
    SourceSpec("snap_counts", "load_snap_counts", tuple(DEFAULT_SEASONS), {}, "player_game"),
    SourceSpec("pbp", "load_pbp", tuple(DEFAULT_SEASONS), {}, "play"),
    SourceSpec("nextgen_stats_passing", "load_nextgen_stats", tuple(DEFAULT_SEASONS), {"stat_type": "passing"}, "player_week", True),
    SourceSpec("nextgen_stats_receiving", "load_nextgen_stats", tuple(DEFAULT_SEASONS), {"stat_type": "receiving"}, "player_week", True),
    SourceSpec("nextgen_stats_rushing", "load_nextgen_stats", tuple(DEFAULT_SEASONS), {"stat_type": "rushing"}, "player_week", True),
    SourceSpec("participation", "load_participation", (2023, 2024), {}, "play", True),
    SourceSpec("ftn_charting", "load_ftn_charting", tuple(DEFAULT_SEASONS), {}, "play", True),
    SourceSpec("pfr_advstats_pass", "load_pfr_advstats", tuple(DEFAULT_SEASONS), {"stat_type": "pass", "summary_level": "week"}, "player_week", True),
    SourceSpec("pfr_advstats_rush", "load_pfr_advstats", tuple(DEFAULT_SEASONS), {"stat_type": "rush", "summary_level": "week"}, "player_week", True),
    SourceSpec("pfr_advstats_rec", "load_pfr_advstats", tuple(DEFAULT_SEASONS), {"stat_type": "rec", "summary_level": "week"}, "player_week", True),
    SourceSpec("rosters", "load_rosters", tuple(DEFAULT_SEASONS), {}, "player_week"),
    SourceSpec("players", "load_players", None, {}, "identity"),
    SourceSpec("ff_playerids", "load_ff_playerids", None, {}, "identity"),
)


def historical_panel_paths(doc_root: Path = DOC_ROOT) -> dict[str, Path]:
    return {
        "plan": doc_root / "NWR_HISTORICAL_NFL_USAGE_PANEL_V0_PLAN_20260624.md",
        "source_smoke": doc_root / "historical_source_smoke_summary_v0.csv",
        "field_coverage": doc_root / "historical_usage_field_coverage_matrix_v0.csv",
        "panel_manifest": doc_root / "historical_usage_panel_manifest_v0.csv",
        "readiness_matrix": doc_root / "historical_usage_backtest_readiness_matrix_v0.csv",
        "readiness_report": doc_root / "NWR_HISTORICAL_NFL_USAGE_PANEL_V0_BACKTEST_READINESS_20260624.md",
        "validation": doc_root / "historical_usage_validation_report_v0.csv",
        "quarantine": doc_root / "historical_usage_quarantine_report_v0.csv",
        "derived_dictionary": doc_root / "historical_usage_derived_field_dictionary_v0.csv",
        "schema_fingerprints": doc_root / "historical_usage_schema_fingerprints_v0.csv",
    }


def build_historical_usage_panel(
    *,
    nflreadpy_module: Any | None = None,
    frames: dict[str, pd.DataFrame] | None = None,
    doc_root: Path = DOC_ROOT,
    shared_cache_root: Path = SHARED_CACHE_ROOT,
    seasons: list[int] | None = None,
    write: bool = False,
) -> HistoricalPanelResult:
    selected_seasons = seasons or list(DEFAULT_SEASONS)
    source_frames, smoke_rows = _load_or_use_frames(
        nflreadpy_module=nflreadpy_module,
        frames=frames,
        seasons=selected_seasons,
        shared_cache_root=shared_cache_root,
    )
    panel_root = shared_cache_root / "panels"
    panels = build_panels(source_frames)
    panel_rows = panel_manifest_rows(panels, panel_root)
    coverage_rows = field_coverage_rows(panels, selected_seasons)
    readiness_rows = backtest_readiness_rows(coverage_rows)
    validation_rows = validation_report_rows(source_frames, panels, coverage_rows)
    quarantine_rows = quarantine_report_rows(smoke_rows, coverage_rows, readiness_rows)
    schema_rows = schema_fingerprint_rows(source_frames)

    paths = historical_panel_paths(doc_root)
    files_written: list[Path] = []
    if write:
        doc_root.mkdir(parents=True, exist_ok=True)
        panel_root.mkdir(parents=True, exist_ok=True)
        for panel_name, panel in panels.items():
            path = panel_root / f"{panel_name}.csv"
            panel.to_csv(path, index=False, encoding="utf-8")
        _write_text(paths["plan"], plan_markdown(selected_seasons, shared_cache_root))
        _write_csv(paths["source_smoke"], SOURCE_SMOKE_HEADER, smoke_rows)
        _write_csv(paths["field_coverage"], FIELD_COVERAGE_HEADER, coverage_rows)
        _write_csv(paths["panel_manifest"], PANEL_MANIFEST_HEADER, panel_rows)
        _write_csv(paths["readiness_matrix"], READINESS_HEADER, readiness_rows)
        _write_text(paths["readiness_report"], readiness_markdown(readiness_rows, panel_rows))
        _write_csv(paths["validation"], VALIDATION_HEADER, validation_rows)
        _write_csv(paths["quarantine"], QUARANTINE_HEADER, quarantine_rows)
        _write_csv(paths["derived_dictionary"], DERIVED_DICTIONARY_HEADER, derived_dictionary_rows())
        _write_csv(paths["schema_fingerprints"], SCHEMA_FINGERPRINT_HEADER, schema_rows)
        files_written = list(paths.values())

    return HistoricalPanelResult(
        doc_root=doc_root,
        shared_cache_root=shared_cache_root,
        files_written=tuple(files_written),
        source_status={row["source_family"]: row["status"] for row in smoke_rows},
        panel_status={row["panel_name"]: "GREEN" if int(row["row_count"]) > 0 else "YELLOW" for row in panel_rows},
        backtest_status=_overall_backtest_status(readiness_rows),
    )


SOURCE_SMOKE_HEADER = [
    "source_family",
    "loader_name",
    "seasons_attempted",
    "seasons_succeeded",
    "seasons_failed",
    "row_count_summary",
    "column_count",
    "raw_cache_path",
    "raw_committed",
    "status",
    "notes",
]
FIELD_COVERAGE_HEADER = [
    "field_name",
    "source_family",
    "field_type",
    "data_grain",
    "seasons_available",
    "player_rows_available",
    "player_id_coverage_pct",
    "position_coverage",
    "missingness_pct",
    "coverage_status",
    "display_only_candidate",
    "model_candidate_status",
    "caveats",
]
PANEL_MANIFEST_HEADER = [
    "panel_name",
    "grain",
    "source_families",
    "seasons",
    "local_or_shared_path",
    "committed_to_git",
    "row_count",
    "field_count",
    "raw_payload_included",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]
READINESS_HEADER = [
    "field_name",
    "source_family",
    "coverage_status",
    "seasons_available",
    "positions_supported",
    "missingness_risk",
    "leakage_risk",
    "target_join_readiness",
    "recommended_backtest_status",
    "blocker",
    "notes",
]
VALIDATION_HEADER = [
    "check_name",
    "subject",
    "status",
    "row_count",
    "field_count",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]
QUARANTINE_HEADER = [
    "subject",
    "quarantine_status",
    "reason",
    "model_input_allowed",
    "app_wiring_allowed",
    "notes",
]
DERIVED_DICTIONARY_HEADER = [
    "field_name",
    "field_type",
    "derivation_formula",
    "grain",
    "model_input_allowed",
    "app_wiring_allowed",
    "caveats",
]
SCHEMA_FINGERPRINT_HEADER = [
    "source_family",
    "row_count",
    "field_count",
    "schema_fingerprint",
    "model_input_allowed",
    "app_wiring_allowed",
]


def configure_nflreadpy_cache(nflreadpy_module: Any, cache_root: Path = NFLREADPY_CACHE_ROOT) -> None:
    try:
        from nflreadpy.config import update_config

        cache_root.mkdir(parents=True, exist_ok=True)
        update_config(cache_mode="filesystem", cache_dir=cache_root, verbose=False, timeout=60)
    except Exception:
        # The lane can still run from supplied frames or memory cache; reports show cache path.
        return


def build_panels(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    player_stats = _core_player_stats(frames.get("player_stats", pd.DataFrame()))
    snaps = _snap_features(frames.get("snap_counts", pd.DataFrame()))
    week_core = _merge_snap_features(player_stats, snaps)
    redzone = _redzone_weekly_features(frames.get("pbp", pd.DataFrame()))
    season_core = _season_core_features(week_core)
    season_redzone = _season_redzone_features(redzone)
    rolling = _rolling_features(week_core)
    return {
        "player_week_core_usage_panel": _flag_panel(week_core),
        "player_season_core_usage_panel": _flag_panel(season_core),
        "player_week_redzone_usage_panel": _flag_panel(redzone),
        "player_season_redzone_usage_panel": _flag_panel(season_redzone),
        "player_season_usage_rolling_features_panel": _flag_panel(rolling),
    }


def panel_manifest_rows(panels: dict[str, pd.DataFrame], panel_root: Path = PANEL_ROOT) -> list[dict[str, str]]:
    grains = {
        "player_week_core_usage_panel": "player_week",
        "player_season_core_usage_panel": "player_season",
        "player_week_redzone_usage_panel": "player_week",
        "player_season_redzone_usage_panel": "player_season",
        "player_season_usage_rolling_features_panel": "player_season_rolling",
    }
    families = {
        "player_week_core_usage_panel": "player_stats;snap_counts",
        "player_season_core_usage_panel": "player_stats;snap_counts",
        "player_week_redzone_usage_panel": "pbp",
        "player_season_redzone_usage_panel": "pbp",
        "player_season_usage_rolling_features_panel": "player_stats;snap_counts",
    }
    rows = []
    for name, frame in panels.items():
        rows.append(
            {
                "panel_name": name,
                "grain": grains[name],
                "source_families": families[name],
                "seasons": _season_list(frame),
                "local_or_shared_path": str(panel_root / f"{name}.csv"),
                "committed_to_git": "no",
                "row_count": str(len(frame)),
                "field_count": str(len(frame.columns)),
                "raw_payload_included": "no",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "normalized review-only panel under ignored shared cache",
            }
        )
    return rows


def field_coverage_rows(
    panels: dict[str, pd.DataFrame],
    seasons_attempted: list[int],
) -> list[dict[str, str]]:
    rows = []
    core_week = panels.get("player_week_core_usage_panel", pd.DataFrame())
    redzone_week = panels.get("player_week_redzone_usage_panel", pd.DataFrame())
    field_source = {
        "offense_snaps": ("snap_counts", core_week),
        "offense_pct": ("snap_counts", core_week),
        "targets": ("player_stats", core_week),
        "carries": ("player_stats", core_week),
        "receptions": ("player_stats", core_week),
        "touches": ("derived_usage", core_week),
        "opportunities": ("derived_usage", core_week),
        "rushing_yards": ("player_stats", core_week),
        "receiving_yards": ("player_stats", core_week),
        "receiving_air_yards": ("player_stats", core_week),
        "receiving_yards_after_catch": ("player_stats", core_week),
        "rushing_first_downs": ("player_stats", core_week),
        "receiving_first_downs": ("player_stats", core_week),
        "red_zone_carries": ("pbp", redzone_week),
        "red_zone_targets": ("pbp", redzone_week),
        "red_zone_touches": ("pbp", redzone_week),
        "inside_10_carries": ("pbp", redzone_week),
        "inside_10_targets": ("pbp", redzone_week),
        "inside_10_touches": ("pbp", redzone_week),
        "inside_5_carries": ("pbp", redzone_week),
        "inside_5_targets": ("pbp", redzone_week),
        "inside_5_touches": ("pbp", redzone_week),
    }
    for field, (source_family, frame) in field_source.items():
        rows.append(_field_coverage_row(field, source_family, frame, seasons_attempted))
    rows.extend(
        [
            _research_field_row("ngs_efficiency_fields", "nextgen_stats", "RESEARCH_ONLY"),
            _research_field_row("participation_personnel_formation_context", "participation", "RESEARCH_ONLY"),
            _research_field_row("route_participation_proxy", "participation", "RESEARCH_ONLY"),
            _research_field_row("tprr_like_proxy", "derived_proxy", "RESEARCH_ONLY"),
            _research_field_row("yprr_like_proxy", "derived_proxy", "RESEARCH_ONLY"),
            _research_field_row("ftn_pfr_advanced_fields", "ftn_pfr", "RESEARCH_ONLY"),
            _research_field_row("true_routes_run", "licensed_gap", "BLOCKED_LICENSED_DATA_GAP"),
            _research_field_row("true_tprr", "licensed_gap", "BLOCKED_LICENSED_DATA_GAP"),
            _research_field_row("true_yprr", "licensed_gap", "BLOCKED_LICENSED_DATA_GAP"),
        ]
    )
    return rows


def backtest_readiness_rows(coverage_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in coverage_rows:
        coverage_status = row["coverage_status"]
        missingness = float(row["missingness_pct"] or 100)
        id_coverage = float(row["player_id_coverage_pct"] or 0)
        if coverage_status.startswith("GREEN") and id_coverage >= 95:
            readiness = "COVERAGE_READY_FOR_FUTURE_BACKTEST"
            blocker = "target manifest and separate backtest runner still required"
            join = "yes"
        elif coverage_status.startswith("YELLOW") and id_coverage >= 80:
            readiness = "YELLOW_COVERAGE_READY_WITH_CAVEATS"
            blocker = "coverage caveats require review before predictive run"
            join = "partial"
        elif coverage_status == "RESEARCH_ONLY":
            readiness = "RESEARCH_ONLY_NOT_BACKTEST_READY"
            blocker = "research-only field semantics or proxy risk"
            join = "no"
        elif coverage_status == "BLOCKED_INSUFFICIENT_COVERAGE":
            readiness = "BLOCKED_INSUFFICIENT_COVERAGE"
            blocker = "insufficient historical coverage"
            join = "no"
        elif coverage_status.startswith("BLOCKED"):
            readiness = coverage_status
            blocker = "licensed-data gap or unsafe field"
            join = "no"
        else:
            readiness = "BLOCKED_INSUFFICIENT_COVERAGE"
            blocker = "insufficient historical coverage"
            join = "no"
        rows.append(
            {
                "field_name": row["field_name"],
                "source_family": row["source_family"],
                "coverage_status": coverage_status,
                "seasons_available": row["seasons_available"],
                "positions_supported": row["position_coverage"],
                "missingness_risk": _risk_from_missingness(missingness),
                "leakage_risk": "low" if row["source_family"] in {"player_stats", "snap_counts", "pbp", "derived_usage"} else "medium",
                "target_join_readiness": join,
                "recommended_backtest_status": readiness,
                "blocker": blocker,
                "notes": "model_input_allowed=no; app_wiring_allowed=no",
            }
        )
    return rows


def validation_report_rows(
    source_frames: dict[str, pd.DataFrame],
    panels: dict[str, pd.DataFrame],
    coverage_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for source, frame in source_frames.items():
        rows.append(
            {
                "check_name": "schema_fingerprint",
                "subject": source,
                "status": "GREEN" if not frame.empty else "YELLOW",
                "row_count": str(len(frame)),
                "field_count": str(len(frame.columns)),
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": _schema_hash(frame),
            }
        )
    for panel_name, panel in panels.items():
        dupes = _duplicate_count(panel)
        rows.append(
            {
                "check_name": "panel_row_duplicate_sanity",
                "subject": panel_name,
                "status": "GREEN" if dupes == 0 and len(panel) > 0 else "YELLOW",
                "row_count": str(len(panel)),
                "field_count": str(len(panel.columns)),
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": f"duplicate_rows={dupes}",
            }
        )
    ready = sum(
        1
        for row in coverage_rows
        if row["coverage_status"].startswith("GREEN")
        or row["coverage_status"].startswith("YELLOW")
    )
    rows.append(
        {
            "check_name": "field_coverage",
            "subject": "primary_usage_fields",
            "status": "GREEN" if ready >= 13 else "YELLOW",
            "row_count": str(len(coverage_rows)),
            "field_count": str(len(FIELD_COVERAGE_HEADER)),
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": f"covered_or_caveated_fields={ready}",
        }
    )
    return rows


def quarantine_report_rows(
    smoke_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    readiness_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for row in smoke_rows:
        if row["status"] != "GREEN":
            rows.append(
                _quarantine(
                    row["source_family"],
                    "QUARANTINED_OR_SKIPPED",
                    row["notes"],
                )
            )
    for row in coverage_rows:
        if row["coverage_status"] in {"RESEARCH_ONLY", "BLOCKED_LICENSED_DATA_GAP", "BLOCKED_UNSAFE"}:
            rows.append(_quarantine(row["field_name"], row["coverage_status"], row["caveats"]))
    for row in readiness_rows:
        if row["recommended_backtest_status"] == "BLOCKED_INSUFFICIENT_COVERAGE":
            rows.append(_quarantine(row["field_name"], "BACKTEST_BLOCKED", row["blocker"]))
    if not rows:
        rows.append(_quarantine("historical_usage_panel_v0", "NONE", "no quarantines"))
    return rows


def derived_dictionary_rows() -> list[dict[str, str]]:
    formulas = {
        "touches": "carries + receptions",
        "opportunities": "carries + targets",
        "red_zone_carries": "count of rushing attempts with yardline_100 <= 20",
        "red_zone_targets": "count of targeted pass attempts with yardline_100 <= 20",
        "red_zone_touches": "red_zone_carries + completed red_zone_targets",
        "inside_10_carries": "count of rushing attempts with yardline_100 <= 10",
        "inside_10_targets": "count of targeted pass attempts with yardline_100 <= 10",
        "inside_10_touches": "inside_10_carries + completed inside_10_targets",
        "inside_5_carries": "count of rushing attempts with yardline_100 <= 5",
        "inside_5_targets": "count of targeted pass attempts with yardline_100 <= 5",
        "inside_5_touches": "inside_5_carries + completed inside_5_targets",
        "first_downs_per_touch": "(rushing_first_downs + receiving_first_downs) / touches",
        "rolling_3_game_opportunities": "player-week opportunities rolling mean over prior/current 3 games by player-season",
        "rolling_5_game_opportunities": "player-week opportunities rolling mean over prior/current 5 games by player-season",
        "rolling_8_game_opportunities": "player-week opportunities rolling mean over prior/current 8 games by player-season",
    }
    return [
        {
            "field_name": field,
            "field_type": "TRUE_DERIVED_FACT" if "rolling" not in field and field != "first_downs_per_touch" else "DERIVED_CONTEXT",
            "derivation_formula": formula,
            "grain": "player_week/player_season_rolling",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "caveats": "review-only; no model or app decision wiring",
        }
        for field, formula in formulas.items()
    ]


def schema_fingerprint_rows(source_frames: dict[str, pd.DataFrame]) -> list[dict[str, str]]:
    return [
        {
            "source_family": source,
            "row_count": str(len(frame)),
            "field_count": str(len(frame.columns)),
            "schema_fingerprint": _schema_hash(frame),
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
        for source, frame in sorted(source_frames.items())
    ]


def plan_markdown(seasons: list[int], shared_cache_root: Path) -> str:
    season_text = ", ".join(str(season) for season in seasons)
    return f"""# Historical NFL Usage Panel V0 Plan

## Purpose

Build a review-only historical NFL usage panel to evaluate the coverage blocker from the NFL Usage Promotion Gate V0: `BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE`.

## Source Families

Primary source families are `player_stats`, `snap_counts`, `pbp`, `nextgen_stats`, `participation`, `ftn_charting`, `pfr_advstats`, `rosters`, `players`, and `ff_playerids`.

## Seasons Attempted By Source Family

Core player-week panels attempt `{season_text}` for player stats, snap counts, and play-by-play. Participation is attempted for 2023-2024 because public participation coverage starts later in this project contract. Identity sources without seasons are loaded as all-ID tables.

## Raw-Cache Policy

Raw/download cache material must stay under `{shared_cache_root}` or its `nflreadpy_cache` child. Raw payloads are not committed.

## Normalized-Output Policy

Normalized player-week/player-season panels are written only to ignored shared cache under `{shared_cache_root}\\panels`. Git receives only manifests, coverage summaries, schema fingerprints, validation reports, quarantine reports, and readiness docs.

## Feature Grain

- `player_week`
- `player_season`
- `player_season_rolling`

## Field Coverage Requirements

Fields need multi-season availability, stable player identity, position coverage across QB/RB/WR/TE where relevant, low missingness, and explicit caveats before future backtesting.

## Join Keys

Preferred join key is `player_id`/GSIS for player_stats and PBP. Snap counts use PFR/player-name context and are joined by normalized player name, position, team, season, and week, with caveats.

## Player ID Policy

Do not fabricate IDs. Player-week panels preserve source IDs and mark identity caveats. Rows without stable player IDs may be display coverage context but are weaker for target joins.

## Missing-Data Policy

Missing means unknown or not covered, not zero value. Derived zeroes are used only where a source row exists and an event count is absent after a left join.

## No-CFBD Boundary

CFBD, college, and rookie/prospect evidence are out of scope.

## No-Model / No-App Boundary

Every artifact keeps `model_input_allowed=no` and `app_wiring_allowed=no`. No decision page consumes usage fields.

## Stop Conditions

Fail closed if source pulls are too large/slow, schemas drift, player IDs are insufficient for target joins, raw data would be tracked, or model/app/rank/source-truth files would change.

## Validation Checklist

- Source smoke summary.
- Schema fingerprints.
- Field coverage matrix.
- Panel manifests.
- Backtest readiness matrix.
- Validation and quarantine reports.
- CSV load validation.
- No raw/shared/local/runtime files tracked.
- No CFBD changes.
- Frozen board and pinned hash unchanged.
"""


def readiness_markdown(readiness_rows: list[dict[str, str]], panel_rows: list[dict[str, str]]) -> str:
    ready = [
        row["field_name"]
        for row in readiness_rows
        if row["recommended_backtest_status"] == "COVERAGE_READY_FOR_FUTURE_BACKTEST"
    ]
    caveat = [
        row["field_name"]
        for row in readiness_rows
        if row["recommended_backtest_status"] == "YELLOW_COVERAGE_READY_WITH_CAVEATS"
    ]
    research = [
        row["field_name"]
        for row in readiness_rows
        if row["recommended_backtest_status"] == "RESEARCH_ONLY_NOT_BACKTEST_READY"
    ]
    gaps = [
        row["field_name"]
        for row in readiness_rows
        if row["recommended_backtest_status"] == "BLOCKED_LICENSED_DATA_GAP"
    ]
    panels = [f"{row['panel_name']} ({row['row_count']} rows)" for row in panel_rows]
    return f"""# Historical NFL Usage Panel V0 Backtest Readiness

## Is Predictive Backtest Still Blocked?

Yes, but the blocker has narrowed. Historical coverage artifacts and local/shared-cache panels now exist for core usage fields, but predictive backtesting should remain blocked until a separate backtest lane connects these panels to approved target labels, validates leakage windows end to end, and runs ablations.

## Exact Remaining Blockers

- Target labels remain conditionally approved from prior local Backtest V0 work and need a committed target manifest for this usage-panel lane.
- Snap share fields have identity/join caveats because snap counts use PFR/player-name context rather than direct GSIS IDs.
- Red-zone and inside-10/inside-5 fields are coverage-ready with small-sample caveats.
- Research-only and licensed-gap fields remain out of predictive scope.

## Fields With Enough Historical Coverage

{_bullet_list(ready)}

## Fields With Coverage Caveats

{_bullet_list(caveat)}

## Fields Remaining Display-Only Only

All coverage-ready fields remain display/review-only until a future promotion/backtest lane approves more. No model input is enabled here.

## Fields Remaining Research-Only

{_bullet_list(research)}

## Licensed-Data Gaps

{_bullet_list(gaps)}

## Target Labels Still Needed

Use only approved future outcome labels such as `next_nwr_points`, `next_nwr_ppg`, and position finish flags from a committed target manifest. Do not use ADP, market, DynastyProcess, ranks, projections, or vendor values.

## Generated Local Panels

{_bullet_list(panels)}

## Safest Next Step

Run a separate historical usage backtest lane that reads the shared-cache panels, joins approved target labels by player/season, validates season-N to season-N+1 leakage rules, and reports field-family ablations without enabling model input.
"""


def _load_or_use_frames(
    *,
    nflreadpy_module: Any | None,
    frames: dict[str, pd.DataFrame] | None,
    seasons: list[int],
    shared_cache_root: Path,
) -> tuple[dict[str, pd.DataFrame], list[dict[str, str]]]:
    if frames is not None:
        loaded = {name: _to_pandas(frame) for name, frame in frames.items()}
        smoke = [
            _smoke_row(
                source_family=name,
                loader_name="supplied_frame",
                seasons_attempted=seasons,
                seasons_succeeded=seasons,
                seasons_failed=[],
                frame=frame,
                raw_cache_path=shared_cache_root / "supplied_frames",
                status="GREEN" if not frame.empty else "YELLOW_EMPTY",
                notes="test/supplied frame; no live pull",
            )
            for name, frame in loaded.items()
        ]
        return loaded, smoke

    if nflreadpy_module is None:
        import nflreadpy as nflreadpy_module  # type: ignore[import-not-found]

    configure_nflreadpy_cache(nflreadpy_module, shared_cache_root / "nflreadpy_cache")
    loaded: dict[str, pd.DataFrame] = {}
    smoke_rows: list[dict[str, str]] = []
    for spec in SOURCE_SPECS:
        attempted = list(spec.seasons) if spec.seasons else []
        try:
            loader = getattr(nflreadpy_module, spec.loader_name)
            if spec.seasons:
                narrowed = [season for season in seasons if season in spec.seasons]
                frame = _to_pandas(loader(narrowed, **spec.kwargs))
                succeeded = sorted(int(season) for season in frame.get("season", pd.Series(dtype=int)).dropna().unique()) if "season" in frame else narrowed
            else:
                frame = _to_pandas(loader(**spec.kwargs))
                succeeded = []
            status = "GREEN" if len(frame) > 0 else "YELLOW_EMPTY"
            notes = "review-only historical smoke"
        except Exception as exc:
            frame = pd.DataFrame()
            succeeded = []
            status = "YELLOW_BLOCKED"
            notes = f"{type(exc).__name__}: {exc}"
        loaded[spec.source_family] = frame
        failed = sorted(set(attempted) - set(succeeded))
        smoke_rows.append(
            _smoke_row(
                source_family=spec.source_family,
                loader_name=spec.loader_name,
                seasons_attempted=attempted,
                seasons_succeeded=succeeded,
                seasons_failed=failed,
                frame=frame,
                raw_cache_path=shared_cache_root / "nflreadpy_cache",
                status=status,
                notes=notes,
            )
        )
    return loaded, smoke_rows


def _core_player_stats(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty_core_week()
    data = frame.copy()
    data["position"] = data.get("position", "").astype(str)
    data = data[data["position"].isin(CORE_POSITIONS)].copy()
    output = pd.DataFrame()
    output["season"] = _num(data, "season").astype(int)
    output["week"] = _num(data, "week").astype(int)
    output["player_id"] = data.get("player_id", "").astype(str)
    output["player_name"] = data.get("player_display_name", data.get("player_name", "")).astype(str)
    output["position"] = data.get("position", "").astype(str)
    output["team"] = data.get("recent_team", data.get("team", "")).astype(str)
    for field in [
        "targets",
        "carries",
        "receptions",
        "rushing_yards",
        "receiving_yards",
        "receiving_air_yards",
        "receiving_yards_after_catch",
        "rushing_first_downs",
        "receiving_first_downs",
    ]:
        output[field] = _num(data, field)
    output["touches"] = output["carries"] + output["receptions"]
    output["opportunities"] = output["carries"] + output["targets"]
    output["join_name"] = output["player_name"].map(_norm_name)
    return output


def _snap_features(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["season", "week", "join_name", "position", "team", "offense_snaps", "offense_pct"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    data = frame.copy()
    data["position"] = data.get("position", "").astype(str)
    data = data[data["position"].isin(CORE_POSITIONS)].copy()
    output = pd.DataFrame()
    output["season"] = _num(data, "season").astype(int)
    output["week"] = _num(data, "week").astype(int)
    output["join_name"] = data.get("player", "").astype(str).map(_norm_name)
    output["position"] = data.get("position", "").astype(str)
    output["team"] = data.get("team", "").astype(str)
    output["offense_snaps"] = _num(data, "offense_snaps")
    output["offense_pct"] = _num(data, "offense_pct")
    return output.groupby(["season", "week", "join_name", "position", "team"], as_index=False).agg(
        offense_snaps=("offense_snaps", "sum"),
        offense_pct=("offense_pct", "mean"),
    )


def _merge_snap_features(player_stats: pd.DataFrame, snaps: pd.DataFrame) -> pd.DataFrame:
    if player_stats.empty:
        return _empty_core_week()
    if snaps.empty:
        player_stats["offense_snaps"] = pd.NA
        player_stats["offense_pct"] = pd.NA
        return player_stats.drop(columns=["join_name"], errors="ignore")
    merged = player_stats.merge(
        snaps,
        on=["season", "week", "join_name", "position", "team"],
        how="left",
        suffixes=("", "_snap"),
    )
    return merged.drop(columns=["join_name"], errors="ignore")


def _redzone_weekly_features(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "season",
        "week",
        "player_id",
        "player_name",
        "team",
        "red_zone_carries",
        "red_zone_targets",
        "red_zone_touches",
        "inside_10_carries",
        "inside_10_targets",
        "inside_10_touches",
        "inside_5_carries",
        "inside_5_targets",
        "inside_5_touches",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, Any]] = []
    data = frame.copy()
    yardline = _num(data, "yardline_100")
    season = _num(data, "season").astype(int)
    week = _num(data, "week").astype(int)
    is_rush = _bool_series(data, "rush_attempt")
    is_pass = _bool_series(data, "pass_attempt") | _bool_series(data, "qb_dropback")
    complete = _bool_series(data, "complete_pass")
    for threshold, prefix in ((20, "red_zone"), (10, "inside_10"), (5, "inside_5")):
        in_zone = yardline <= threshold
        rush_rows = data[in_zone & is_rush].copy()
        if not rush_rows.empty:
            tmp = pd.DataFrame(
                {
                    "season": season.loc[rush_rows.index],
                    "week": week.loc[rush_rows.index],
                    "player_id": rush_rows.get("rusher_player_id", "").astype(str),
                    "player_name": rush_rows.get("rusher_player_name", "").astype(str),
                    "team": rush_rows.get("posteam", "").astype(str),
                    f"{prefix}_carries": 1,
                    f"{prefix}_targets": 0,
                    f"{prefix}_receptions": 0,
                }
            )
            rows.extend(tmp.to_dict(orient="records"))
        pass_rows = data[in_zone & is_pass & data.get("receiver_player_id", pd.Series("", index=data.index)).notna()].copy()
        if not pass_rows.empty:
            tmp = pd.DataFrame(
                {
                    "season": season.loc[pass_rows.index],
                    "week": week.loc[pass_rows.index],
                    "player_id": pass_rows.get("receiver_player_id", "").astype(str),
                    "player_name": pass_rows.get("receiver_player_name", "").astype(str),
                    "team": pass_rows.get("posteam", "").astype(str),
                    f"{prefix}_carries": 0,
                    f"{prefix}_targets": 1,
                    f"{prefix}_receptions": complete.loc[pass_rows.index].astype(int),
                }
            )
            rows.extend(tmp.to_dict(orient="records"))
    if not rows:
        return pd.DataFrame(columns=columns)
    output = pd.DataFrame(rows).fillna(0)
    for field in [
        "red_zone_carries",
        "red_zone_targets",
        "red_zone_receptions",
        "inside_10_carries",
        "inside_10_targets",
        "inside_10_receptions",
        "inside_5_carries",
        "inside_5_targets",
        "inside_5_receptions",
    ]:
        if field not in output:
            output[field] = 0
    grouped = output.groupby(["season", "week", "player_id", "player_name", "team"], as_index=False).sum(numeric_only=True)
    grouped["red_zone_touches"] = grouped["red_zone_carries"] + grouped["red_zone_receptions"]
    grouped["inside_10_touches"] = grouped["inside_10_carries"] + grouped["inside_10_receptions"]
    grouped["inside_5_touches"] = grouped["inside_5_carries"] + grouped["inside_5_receptions"]
    return grouped[columns]


def _season_core_features(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    group_keys = ["season", "player_id", "player_name", "position", "team"]
    sum_fields = [
        "targets",
        "carries",
        "receptions",
        "rushing_yards",
        "receiving_yards",
        "receiving_air_yards",
        "receiving_yards_after_catch",
        "rushing_first_downs",
        "receiving_first_downs",
        "touches",
        "opportunities",
        "offense_snaps",
    ]
    agg = {field: (field, "sum") for field in sum_fields if field in frame}
    output = frame.groupby(group_keys, as_index=False).agg(**agg)
    output["games_with_usage_row"] = frame.groupby(group_keys)["week"].nunique().to_numpy()
    if "offense_pct" in frame:
        pct = frame.groupby(group_keys, as_index=False).agg(offense_pct=("offense_pct", "mean"))
        output = output.merge(pct, on=group_keys, how="left")
    return output


def _season_redzone_features(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    group_keys = ["season", "player_id", "player_name", "team"]
    fields = [field for field in frame.columns if field.endswith(("carries", "targets", "touches"))]
    return frame.groupby(group_keys, as_index=False).agg(**{field: (field, "sum") for field in fields})


def _rolling_features(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    data = frame.sort_values(["player_id", "season", "week"]).copy()
    for source_field in ["targets", "carries", "opportunities", "touches", "offense_pct"]:
        if source_field not in data:
            continue
        for window in (3, 5, 8):
            data[f"rolling_{window}_game_{source_field}"] = (
                data.groupby(["player_id", "season"])[source_field]
                .rolling(window, min_periods=1)
                .mean()
                .reset_index(level=[0, 1], drop=True)
            )
    keep = [
        "season",
        "week",
        "player_id",
        "player_name",
        "position",
        "team",
        *[column for column in data.columns if column.startswith("rolling_")],
    ]
    return data[keep]


def _flag_panel(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    if "model_input_allowed" not in output:
        output["model_input_allowed"] = MODEL_INPUT_ALLOWED
    if "app_wiring_allowed" not in output:
        output["app_wiring_allowed"] = APP_WIRING_ALLOWED
    return output


def _field_coverage_row(
    field: str,
    source_family: str,
    frame: pd.DataFrame,
    seasons_attempted: list[int],
) -> dict[str, str]:
    if frame.empty or field not in frame:
        return {
            "field_name": field,
            "source_family": source_family,
            "field_type": _field_type(field),
            "data_grain": "player_week",
            "seasons_available": "",
            "player_rows_available": "0",
            "player_id_coverage_pct": "0.00",
            "position_coverage": "",
            "missingness_pct": "100.00",
            "coverage_status": "BLOCKED_INSUFFICIENT_COVERAGE",
            "display_only_candidate": "yes",
            "model_candidate_status": "no",
            "caveats": "field absent from generated historical panel",
        }
    non_null = frame[field].notna()
    seasons = sorted(str(int(season)) for season in frame.loc[non_null, "season"].dropna().unique())
    id_coverage = _pct(frame.loc[non_null, "player_id"].astype(str).str.len().gt(0).sum(), int(non_null.sum()))
    missingness = _pct((~non_null).sum(), len(frame))
    positions = (
        ";".join(sorted(frame.loc[non_null, "position"].dropna().astype(str).unique()))
        if "position" in frame
        else "not_position_scoped"
    )
    status = "GREEN_MULTI_SEASON_COVERAGE"
    caveats = "review-only; model_input_allowed=no; app_wiring_allowed=no"
    if len(seasons) < min(3, len(seasons_attempted)) or float(missingness) > 15:
        status = "YELLOW_PARTIAL_COVERAGE"
    if field in {"offense_snaps", "offense_pct"}:
        status = "YELLOW_COVERAGE_ID_JOIN_CAVEAT"
        caveats = "snap counts joined by normalized name/team/position/week; verify identity before predictive use"
    if field.startswith(("inside_10", "inside_5", "red_zone")):
        caveats = "small-sample event counts; use coverage/readiness only before ablation"
    return {
        "field_name": field,
        "source_family": source_family,
        "field_type": _field_type(field),
        "data_grain": "player_week",
        "seasons_available": ";".join(seasons),
        "player_rows_available": str(int(non_null.sum())),
        "player_id_coverage_pct": f"{id_coverage:.2f}",
        "position_coverage": positions,
        "missingness_pct": f"{missingness:.2f}",
        "coverage_status": status,
        "display_only_candidate": "yes",
        "model_candidate_status": "no",
        "caveats": caveats,
    }


def _research_field_row(field_name: str, source_family: str, status: str) -> dict[str, str]:
    return {
        "field_name": field_name,
        "source_family": source_family,
        "field_type": "LICENSED_DATA_GAP" if status.startswith("BLOCKED") else "RESEARCH_ONLY",
        "data_grain": "source_defined",
        "seasons_available": "",
        "player_rows_available": "0",
        "player_id_coverage_pct": "0.00",
        "position_coverage": "",
        "missingness_pct": "100.00",
        "coverage_status": status,
        "display_only_candidate": "no",
        "model_candidate_status": "no",
        "caveats": "not part of safe historical model candidate panel",
    }


def _smoke_row(
    *,
    source_family: str,
    loader_name: str,
    seasons_attempted: list[int],
    seasons_succeeded: list[int],
    seasons_failed: list[int],
    frame: pd.DataFrame,
    raw_cache_path: Path,
    status: str,
    notes: str,
) -> dict[str, str]:
    return {
        "source_family": source_family,
        "loader_name": loader_name,
        "seasons_attempted": ";".join(str(season) for season in seasons_attempted) or "all_ids",
        "seasons_succeeded": ";".join(str(season) for season in seasons_succeeded) or ("all_ids" if seasons_attempted == [] and len(frame) else ""),
        "seasons_failed": ";".join(str(season) for season in seasons_failed),
        "row_count_summary": str(len(frame)),
        "column_count": str(len(frame.columns)),
        "raw_cache_path": str(raw_cache_path),
        "raw_committed": "no",
        "status": status,
        "notes": notes,
    }


def _quarantine(subject: str, status: str, reason: str) -> dict[str, str]:
    return {
        "subject": subject,
        "quarantine_status": status,
        "reason": reason,
        "model_input_allowed": MODEL_INPUT_ALLOWED,
        "app_wiring_allowed": APP_WIRING_ALLOWED,
        "notes": "fail closed; review-only",
    }


def _empty_core_week() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "season",
            "week",
            "player_id",
            "player_name",
            "position",
            "team",
            *PRIMARY_DISPLAY_FIELDS,
        ]
    )


def _to_pandas(frame: Any) -> pd.DataFrame:
    if isinstance(frame, pd.DataFrame):
        return frame.copy()
    if hasattr(frame, "to_pandas"):
        return frame.to_pandas()
    if hasattr(frame, "to_dicts"):
        return pd.DataFrame(frame.to_dicts())
    if isinstance(frame, list):
        return pd.DataFrame(frame)
    return pd.DataFrame(frame)


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def _bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(False, index=frame.index)
    values = frame[column]
    if values.dtype == bool:
        return values.fillna(False)
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().any():
        return numeric.fillna(0).gt(0)
    return values.astype(str).str.lower().isin({"1", "1.0", "true", "yes"})


def _norm_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _field_type(field: str) -> str:
    if field in {"touches", "opportunities"} or field.startswith(("red_zone", "inside_10", "inside_5")):
        return "TRUE_DERIVED_FACT"
    return "TRUE_FACTUAL_FIELD"


def _season_list(frame: pd.DataFrame) -> str:
    if frame.empty or "season" not in frame:
        return ""
    return ";".join(str(int(season)) for season in sorted(frame["season"].dropna().unique()))


def _pct(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return float(numerator) / float(denominator) * 100.0


def _risk_from_missingness(missingness: float) -> str:
    if missingness <= 5:
        return "low"
    if missingness <= 25:
        return "medium"
    return "high"


def _duplicate_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    keys = [key for key in ["season", "week", "player_id", "team"] if key in frame]
    if not keys:
        return int(frame.duplicated().sum())
    return int(frame.duplicated(keys).sum())


def _schema_hash(frame: pd.DataFrame) -> str:
    fields = [f"{column}:{dtype}" for column, dtype in zip(frame.columns, frame.dtypes, strict=False)]
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()


def _overall_backtest_status(readiness_rows: list[dict[str, str]]) -> str:
    ready_count = sum(
        row["recommended_backtest_status"] == "COVERAGE_READY_FOR_FUTURE_BACKTEST"
        for row in readiness_rows
    )
    caveat_count = sum(
        row["recommended_backtest_status"] == "YELLOW_COVERAGE_READY_WITH_CAVEATS"
        for row in readiness_rows
    )
    if ready_count >= 10:
        return "YELLOW_COVERAGE_READY_TARGET_MANIFEST_REQUIRED"
    if ready_count + caveat_count >= 10:
        return "YELLOW_PARTIAL_COVERAGE_READY"
    return "BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE"


def validate_csv_flags(paths: list[Path]) -> None:
    for path in paths:
        if path.suffix.lower() != ".csv" or not path.exists():
            continue
        frame = pd.read_csv(path, keep_default_na=False)
        for column in ("model_input_allowed", "app_wiring_allowed"):
            if column in frame and not frame[column].astype(str).str.lower().eq("no").all():
                raise ValueError(f"{path} has non-no {column}")
        if path.name == "historical_usage_derived_field_dictionary_v0.csv":
            if "derivation_formula" not in frame or frame["derivation_formula"].astype(str).str.len().eq(0).any():
                raise ValueError(f"{path} has unlabeled derived formulas")


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _bullet_list(values: list[str]) -> str:
    if not values:
        return "- None."
    return "\n".join(f"- `{value}`" for value in values)
