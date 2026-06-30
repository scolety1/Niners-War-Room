from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import cached_property
from pathlib import Path
from typing import Any

from src.services.draft_day_app_v1_service import (
    build_unified_player_board,
    load_dynasty_rankings,
    load_frozen_board,
)
from src.services.nflverse_refresh_health_service import (
    AXIS_PASS,
    AXIS_REVIEW,
    BLOCKED,
    EXECUTION_SUCCEEDED,
    GREEN,
    NOT_ENOUGH_INFORMATION,
    YELLOW,
    NflverseDatasetHealth,
    build_nflverse_dataset_health,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
)

SAFE_NOW_DISPLAY_ONLY = "SAFE_NOW_DISPLAY_ONLY"
NEED_DATASET_REFRESH = "NEED_DATASET_REFRESH"
NEED_IDENTITY_REVIEW = "NEED_IDENTITY_REVIEW"
NEED_SCHEMA_REVIEW = "NEED_SCHEMA_REVIEW"
BLOCKED_SOURCE_POLICY = "BLOCKED_SOURCE_POLICY"
BLOCKED_VENDOR_OR_PRIVATE = "BLOCKED_VENDOR_OR_PRIVATE"
NOT_APPLICABLE = "NOT_APPLICABLE"
REVIEW_NEEDED = "Review needed"

DISPLAY_ONLY = "true"
DENY = "false"

PLAYER_CONTEXT_DATASETS = (
    "players",
    "rosters",
    "weekly_rosters",
    "ff_playerids",
    "injuries",
    "schedules",
    "depth_charts",
    "snap_counts",
    "player_stats_weekly",
    "player_stats_seasonal",
    "draft_picks",
    "combine",
    "contracts",
    "teams",
    "ff_rankings",
)

ARTIFACT_COLUMNS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "nwr_source_coverage",
    "nwr_rank",
    "final_board_rank",
    "nflverse_gsis_id",
    "nflverse_sleeper_id",
    "nflverse_player_name",
    "nflverse_team",
    "nflverse_position",
    "identity_join_status",
    "identity_caveat",
    "roster_birth_date_derived_age",
    "age_source",
    "roster_status",
    "weekly_roster_status",
    "injury_report_status",
    "injury_report_date_week",
    "practice_status",
    "next_game_context",
    "opponent_context",
    "bye_context",
    "depth_chart_position",
    "depth_chart_rank",
    "depth_chart_role",
    "snap_count_recency",
    "latest_snap_season",
    "latest_snap_week",
    "snap_sample_size",
    "last_active_season",
    "last_active_week",
    "draft_year",
    "draft_round",
    "draft_pick",
    "drafted_team",
    "contract_context",
    "per_field_dataset_source",
    "per_field_freshness_source_status",
    "data_coverage_status",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rank_logic_allowed",
    "hidden_sort_allowed",
    "trade_value_allowed",
    "pick_value_allowed",
    "review_required",
    "notes",
)

JOIN_HEALTH_COLUMNS = (
    "gate",
    "status",
    "source_dataset",
    "current_rankings_rows",
    "clean_join_rows",
    "no_nflverse_identity_rows",
    "ambiguous_identity_rows",
    "many_to_one_conflict_rows",
    "one_to_many_conflict_rows",
    "need_dataset_refresh_rows",
    "blocked_rows",
    "review_only_rows",
    "message",
)

SCHEMA_COLUMNS = (
    "column_name",
    "description",
    "source_dataset",
    "field_status",
    "missing_value_policy",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rank_logic_allowed",
    "hidden_sort_allowed",
    "trade_value_allowed",
    "pick_value_allowed",
)


@dataclass(frozen=True)
class NflversePlayerContextResult:
    verdict: str
    current_rankings_rows: int
    artifact_rows: tuple[dict[str, str], ...]
    join_health_rows: tuple[dict[str, str], ...]
    schema_manifest_rows: tuple[dict[str, str], ...]
    health_by_dataset: dict[str, NflverseDatasetHealth]
    rankings_source: str
    safe_refresh_attempted: bool = False
    safe_refresh_status: str = "not_run"
    output_dir: Path | None = None


def build_nflverse_player_context_display(
    *,
    shared_root: Path | None = None,
    status_root: Path | None = None,
    snapshot_dir: Path | None = None,
    schedule_snapshot_dir: Path | None = None,
    schedule_as_of: date | None = None,
    rankings_rows: Sequence[dict[str, Any]] | None = None,
    rankings_source: str = "",
    safe_refresh_attempted: bool = False,
    safe_refresh_status: str = "not_run",
) -> NflversePlayerContextResult:
    health_rows = build_nflverse_dataset_health(
        **{
            key: value
            for key, value in {
                "shared_root": shared_root,
                "status_root": status_root,
                "snapshot_dir": snapshot_dir,
            }.items()
            if value is not None
        }
    )
    health_by_dataset = {row.dataset_id: row for row in health_rows}
    schedule_rows = _load_ready_dataset_rows(health_by_dataset, "schedules")
    if schedule_snapshot_dir is not None:
        schedule_health_rows = build_nflverse_dataset_health(snapshot_dir=schedule_snapshot_dir)
        schedule_health_by_dataset = {row.dataset_id: row for row in schedule_health_rows}
        schedule_health = schedule_health_by_dataset["schedules"]
        if _dataset_ready(schedule_health):
            health_by_dataset["schedules"] = schedule_health
            schedule_rows = _load_ready_dataset_rows(schedule_health_by_dataset, "schedules")
    current_rows, resolved_rankings_source = _current_rankings_rows(
        rankings_rows=rankings_rows,
        rankings_source=rankings_source,
    )

    context = _NflverseContext(
        health_by_dataset=health_by_dataset,
        player_rows=_load_ready_dataset_rows(health_by_dataset, "players"),
        roster_rows=_load_ready_dataset_rows(health_by_dataset, "rosters"),
        weekly_roster_rows=_load_ready_dataset_rows(health_by_dataset, "weekly_rosters"),
        ff_playerid_rows=_load_ready_dataset_rows(health_by_dataset, "ff_playerids"),
        injury_rows=_load_ready_dataset_rows(health_by_dataset, "injuries"),
        schedule_rows=schedule_rows,
        depth_chart_rows=_load_ready_dataset_rows(health_by_dataset, "depth_charts"),
        snap_rows=_load_ready_dataset_rows(health_by_dataset, "snap_counts"),
        weekly_stat_rows=_load_ready_dataset_rows(health_by_dataset, "player_stats_weekly"),
        draft_pick_rows=_load_ready_dataset_rows(health_by_dataset, "draft_picks"),
        contract_rows=_load_ready_dataset_rows(health_by_dataset, "contracts"),
    )
    as_of = schedule_as_of or datetime.now(UTC).date()
    artifact_rows = tuple(_artifact_row(row, context, schedule_as_of=as_of) for row in current_rows)
    join_health_rows = tuple(_join_health_rows(artifact_rows, health_by_dataset))
    schema_rows = tuple(_schema_manifest_rows(health_by_dataset))
    verdict = _verdict(artifact_rows, join_health_rows)
    return NflversePlayerContextResult(
        verdict=verdict,
        current_rankings_rows=len(current_rows),
        artifact_rows=artifact_rows,
        join_health_rows=join_health_rows,
        schema_manifest_rows=schema_rows,
        health_by_dataset=health_by_dataset,
        rankings_source=resolved_rankings_source,
        safe_refresh_attempted=safe_refresh_attempted,
        safe_refresh_status=safe_refresh_status,
    )


def write_nflverse_player_context_display_docs(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    shared_root: Path | None = None,
    status_root: Path | None = None,
    snapshot_dir: Path | None = None,
    schedule_snapshot_dir: Path | None = None,
    schedule_as_of: date | None = None,
    rankings_rows: Sequence[dict[str, Any]] | None = None,
    rankings_source: str = "",
    safe_refresh_attempted: bool = False,
    safe_refresh_status: str = "not_run",
) -> NflversePlayerContextResult:
    result = build_nflverse_player_context_display(
        shared_root=shared_root,
        status_root=status_root,
        snapshot_dir=snapshot_dir,
        schedule_snapshot_dir=schedule_snapshot_dir,
        schedule_as_of=schedule_as_of,
        rankings_rows=rankings_rows,
        rankings_source=rankings_source,
        safe_refresh_attempted=safe_refresh_attempted,
        safe_refresh_status=safe_refresh_status,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_dir / "nflverse_player_context_display_artifact.csv",
        result.artifact_rows,
        ARTIFACT_COLUMNS,
    )
    _write_csv(
        output_dir / "nflverse_player_context_join_health.csv",
        result.join_health_rows,
        JOIN_HEALTH_COLUMNS,
    )
    _write_csv(
        output_dir / "nflverse_player_context_schema_manifest.csv",
        result.schema_manifest_rows,
        SCHEMA_COLUMNS,
    )
    (output_dir / "README.md").write_text(_readme_markdown(result), encoding="utf-8")
    (output_dir / "nflverse_player_context_source_policy.md").write_text(
        _source_policy_markdown(result), encoding="utf-8"
    )
    (output_dir / "nflverse_player_context_build_report.md").write_text(
        _build_report_markdown(result), encoding="utf-8"
    )
    (output_dir / "nflverse_player_context_guardrail_report.md").write_text(
        _guardrail_report_markdown(result), encoding="utf-8"
    )
    return NflversePlayerContextResult(
        verdict=result.verdict,
        current_rankings_rows=result.current_rankings_rows,
        artifact_rows=result.artifact_rows,
        join_health_rows=result.join_health_rows,
        schema_manifest_rows=result.schema_manifest_rows,
        health_by_dataset=result.health_by_dataset,
        rankings_source=result.rankings_source,
        safe_refresh_attempted=result.safe_refresh_attempted,
        safe_refresh_status=result.safe_refresh_status,
        output_dir=output_dir,
    )


@dataclass(frozen=True)
class _NflverseContext:
    health_by_dataset: dict[str, NflverseDatasetHealth]
    player_rows: tuple[dict[str, str], ...]
    roster_rows: tuple[dict[str, str], ...]
    weekly_roster_rows: tuple[dict[str, str], ...]
    ff_playerid_rows: tuple[dict[str, str], ...]
    injury_rows: tuple[dict[str, str], ...]
    schedule_rows: tuple[dict[str, str], ...]
    depth_chart_rows: tuple[dict[str, str], ...]
    snap_rows: tuple[dict[str, str], ...]
    weekly_stat_rows: tuple[dict[str, str], ...]
    draft_pick_rows: tuple[dict[str, str], ...]
    contract_rows: tuple[dict[str, str], ...]

    @cached_property
    def roster_index(self) -> _RosterIndex:
        return _RosterIndex.build(self.roster_rows)

    @cached_property
    def players_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.player_rows, key_columns=("gsis_id",))

    @cached_property
    def ff_playerid_index(self) -> _FfPlayerIdIndex:
        return _FfPlayerIdIndex.build(self.ff_playerid_rows)

    @cached_property
    def weekly_roster_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.weekly_roster_rows, key_columns=("gsis_id",))

    @cached_property
    def injury_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.injury_rows, key_columns=("gsis_id",))

    @cached_property
    def depth_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.depth_chart_rows, key_columns=("gsis_id",))

    @cached_property
    def draft_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.draft_pick_rows, key_columns=("gsis_id",))

    @cached_property
    def contract_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.contract_rows, key_columns=("gsis_id",))

    @cached_property
    def schedules_by_team(self) -> dict[str, tuple[dict[str, str], ...]]:
        by_team: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in self.schedule_rows:
            for column in ("home_team", "away_team"):
                team = _clean(row.get(column))
                if team:
                    by_team[team].append(row)
        return {
            team: tuple(sorted(rows, key=lambda item: _season_week_sort(item, 0)))
            for team, rows in by_team.items()
        }

    @cached_property
    def snap_by_name_team_position(self) -> dict[tuple[str, str, str], dict[str, str]]:
        return _latest_snap_rows(self.snap_rows)

    @cached_property
    def snap_sample_size_by_key(self) -> dict[tuple[str, str, str], int]:
        counts: dict[tuple[str, str, str], int] = defaultdict(int)
        for row in self.snap_rows:
            key = (
                _normalize_name(row.get("player")),
                _clean(row.get("team")),
                _clean(row.get("position")),
            )
            if key[0]:
                counts[key] += 1
        return counts

    @cached_property
    def stats_by_gsis(self) -> dict[str, dict[str, str]]:
        return _latest_by_key(self.weekly_stat_rows, key_columns=("player_id",))


@dataclass(frozen=True)
class _RosterIndex:
    latest_by_sleeper: dict[str, dict[str, str]]
    gsis_by_sleeper: dict[str, set[str]]
    latest_by_gsis: dict[str, dict[str, str]]
    latest_by_name_position: dict[tuple[str, str], dict[str, str]]
    gsis_by_name_position: dict[tuple[str, str], set[str]]

    @classmethod
    def build(cls, rows: Sequence[dict[str, str]]) -> _RosterIndex:
        latest_by_sleeper: dict[str, dict[str, str]] = {}
        gsis_by_sleeper: dict[str, set[str]] = defaultdict(set)
        latest_by_gsis: dict[str, dict[str, str]] = {}
        latest_by_name_position: dict[tuple[str, str], dict[str, str]] = {}
        gsis_by_name_position: dict[tuple[str, str], set[str]] = defaultdict(set)
        for index, row in enumerate(rows):
            sleeper = _clean(row.get("sleeper_id"))
            gsis = _clean(row.get("gsis_id"))
            name_position = (_normalize_name(row.get("full_name")), _clean(row.get("position")))
            sort_key = _season_week_sort(row, index)
            row_with_sort = dict(row)
            row_with_sort["_sort_key"] = sort_key
            if sleeper:
                if gsis:
                    gsis_by_sleeper[sleeper].add(gsis)
                existing = latest_by_sleeper.get(sleeper)
                if existing is None or sort_key > existing.get("_sort_key", ""):
                    latest_by_sleeper[sleeper] = row_with_sort
            if name_position[0]:
                if gsis:
                    gsis_by_name_position[name_position].add(gsis)
                existing = latest_by_name_position.get(name_position)
                if existing is None or sort_key > existing.get("_sort_key", ""):
                    latest_by_name_position[name_position] = row_with_sort
            if gsis:
                existing = latest_by_gsis.get(gsis)
                if existing is None or sort_key > existing.get("_sort_key", ""):
                    latest_by_gsis[gsis] = row_with_sort
        return cls(
            latest_by_sleeper=latest_by_sleeper,
            gsis_by_sleeper=dict(gsis_by_sleeper),
            latest_by_gsis=latest_by_gsis,
            latest_by_name_position=latest_by_name_position,
            gsis_by_name_position=dict(gsis_by_name_position),
        )


@dataclass(frozen=True)
class _FfPlayerIdIndex:
    latest_by_sleeper: dict[str, dict[str, str]]
    gsis_by_sleeper: dict[str, set[str]]

    @classmethod
    def build(cls, rows: Sequence[dict[str, str]]) -> _FfPlayerIdIndex:
        latest_by_sleeper: dict[str, dict[str, str]] = {}
        gsis_by_sleeper: dict[str, set[str]] = defaultdict(set)
        for index, row in enumerate(rows):
            sleeper = _clean(row.get("sleeper_id"))
            gsis = _clean(row.get("gsis_id"))
            if not sleeper:
                continue
            if gsis:
                gsis_by_sleeper[sleeper].add(gsis)
            sort_key = _season_week_sort(row, index)
            row_with_sort = dict(row)
            row_with_sort["_sort_key"] = sort_key
            existing = latest_by_sleeper.get(sleeper)
            if existing is None or sort_key > existing.get("_sort_key", ""):
                latest_by_sleeper[sleeper] = row_with_sort
        return cls(
            latest_by_sleeper=latest_by_sleeper,
            gsis_by_sleeper=dict(gsis_by_sleeper),
        )


def _artifact_row(
    row: dict[str, Any],
    context: _NflverseContext,
    *,
    schedule_as_of: date,
) -> dict[str, str]:
    nwr_player_id = _clean(row.get("player_id"))
    nwr_player_name = _clean(row.get("player_name") or row.get("player"))
    nwr_position = _clean(row.get("position"))
    nwr_team = _clean(row.get("nfl_team") or row.get("team"))
    identity = _resolve_identity(row, context)
    roster = identity.get("roster_row", {})
    player = identity.get("player_row", {})
    ff_playerid = identity.get("ff_playerid_row", {})
    gsis = (
        _clean(roster.get("gsis_id") or player.get("gsis_id") or ff_playerid.get("gsis_id"))
        if identity["status"] == SAFE_NOW_DISPLAY_ONLY
        else ""
    )
    weekly_roster = context.weekly_roster_by_gsis.get(gsis, {}) if gsis else {}
    snap_row, snap_count = _snap_context(row, roster, context) if gsis else ({}, 0)
    stat_row = context.stats_by_gsis.get(gsis, {}) if gsis else {}
    injury_row = context.injury_by_gsis.get(gsis, {}) if gsis else {}
    depth_row = context.depth_by_gsis.get(gsis, {}) if gsis else {}
    draft_row = context.draft_by_gsis.get(gsis, {}) if gsis else {}
    contract_row = context.contract_by_gsis.get(gsis, {}) if gsis else {}
    schedule = (
        _schedule_context(
            _clean(roster.get("team") or player.get("latest_team") or nwr_team),
            context,
            schedule_as_of,
        )
        if identity["status"] == SAFE_NOW_DISPLAY_ONLY
        else _empty_schedule_context()
    )

    age, age_source = _age_from_birth_date(
        roster.get("birth_date") or player.get("birth_date") or ff_playerid.get("birthdate"),
        (
            "rosters.birth_date"
            if roster.get("birth_date")
            else "players.birth_date"
            if player.get("birth_date")
            else "ff_playerids.birthdate"
            if ff_playerid.get("birthdate")
            else NOT_ENOUGH_INFORMATION
        ),
    )

    last_active_season = _clean(stat_row.get("season")) or _clean(snap_row.get("season"))
    last_active_week = _clean(stat_row.get("week")) or _clean(snap_row.get("week"))
    if not last_active_season:
        last_active_season = NOT_ENOUGH_INFORMATION
    if not last_active_week:
        last_active_week = NOT_ENOUGH_INFORMATION

    review_required = "true" if identity["status"] != SAFE_NOW_DISPLAY_ONLY else "false"
    data_coverage = _data_coverage_status(context.health_by_dataset)
    notes = _notes_for_row(
        identity,
        context.health_by_dataset,
        injury_row=injury_row,
        depth_row=depth_row,
        draft_row=draft_row,
        snap_row=snap_row,
    )
    return _ordered(
        {
            "nwr_player_id": nwr_player_id or NOT_ENOUGH_INFORMATION,
            "nwr_player_name": nwr_player_name or NOT_ENOUGH_INFORMATION,
            "nwr_position": nwr_position or NOT_ENOUGH_INFORMATION,
            "nwr_team": nwr_team or NOT_ENOUGH_INFORMATION,
            "nwr_source_coverage": _clean(row.get("source_coverage")) or NOT_ENOUGH_INFORMATION,
            "nwr_rank": _clean(row.get("nwr_rank")) or NOT_ENOUGH_INFORMATION,
            "final_board_rank": _clean(row.get("final_board_rank")) or NOT_ENOUGH_INFORMATION,
            "nflverse_gsis_id": gsis or NOT_ENOUGH_INFORMATION,
            "nflverse_sleeper_id": (
                _clean(roster.get("sleeper_id") or ff_playerid.get("sleeper_id"))
                or NOT_ENOUGH_INFORMATION
            ),
            "nflverse_player_name": (
                _clean(
                    roster.get("full_name")
                    or player.get("display_name")
                    or ff_playerid.get("name")
                )
                or NOT_ENOUGH_INFORMATION
            ),
            "nflverse_team": (
                _clean(roster.get("team") or player.get("latest_team") or ff_playerid.get("team"))
                or NOT_ENOUGH_INFORMATION
            ),
            "nflverse_position": (
                _clean(
                    roster.get("position")
                    or player.get("position")
                    or ff_playerid.get("position")
                )
                or NOT_ENOUGH_INFORMATION
            ),
            "identity_join_status": identity["status"],
            "identity_caveat": identity["caveat"],
            "roster_birth_date_derived_age": age,
            "age_source": age_source,
            "roster_status": _clean(roster.get("status") or player.get("status"))
            or NOT_ENOUGH_INFORMATION,
            "weekly_roster_status": _clean(weekly_roster.get("status")) or NOT_ENOUGH_INFORMATION,
            "injury_report_status": _field_value(
                context.health_by_dataset["injuries"], injury_row.get("report_status")
            ),
            "injury_report_date_week": _injury_date_week(
                context.health_by_dataset["injuries"], injury_row
            ),
            "practice_status": _field_value(
                context.health_by_dataset["injuries"], injury_row.get("practice_status")
            ),
            "next_game_context": _field_value(
                context.health_by_dataset["schedules"], schedule["next_game_context"]
            ),
            "opponent_context": _field_value(
                context.health_by_dataset["schedules"], schedule["opponent_context"]
            ),
            "bye_context": _field_value(
                context.health_by_dataset["schedules"], schedule["bye_context"]
            ),
            "depth_chart_position": _field_value(
                context.health_by_dataset["depth_charts"],
                depth_row.get("depth_position") or depth_row.get("position"),
            ),
            "depth_chart_rank": _field_value(
                context.health_by_dataset["depth_charts"], depth_row.get("pos_rank")
            ),
            "depth_chart_role": _depth_chart_role(
                context.health_by_dataset["depth_charts"], depth_row
            ),
            "snap_count_recency": _snap_recency(snap_row),
            "latest_snap_season": _clean(snap_row.get("season")) or NOT_ENOUGH_INFORMATION,
            "latest_snap_week": _clean(snap_row.get("week")) or NOT_ENOUGH_INFORMATION,
            "snap_sample_size": str(snap_count) if snap_count else NOT_ENOUGH_INFORMATION,
            "last_active_season": last_active_season,
            "last_active_week": last_active_week,
            "draft_year": _field_value(
                context.health_by_dataset["draft_picks"], draft_row.get("season")
            ),
            "draft_round": _field_value(
                context.health_by_dataset["draft_picks"], draft_row.get("round")
            ),
            "draft_pick": _field_value(
                context.health_by_dataset["draft_picks"], draft_row.get("pick")
            ),
            "drafted_team": _field_value(
                context.health_by_dataset["draft_picks"], draft_row.get("team")
            ),
            "contract_context": _contract_context(
                context.health_by_dataset["contracts"], contract_row
            ),
            "per_field_dataset_source": (
                "identity=rosters; weekly_status=weekly_rosters; "
                "injury=injuries; schedule=schedules; depth=depth_charts; "
                "snap=snap_counts; last_active=player_stats_weekly; "
                "draft=draft_picks; contract=contracts"
            ),
            "per_field_freshness_source_status": _freshness_summary(context.health_by_dataset),
            "data_coverage_status": data_coverage,
            "display_only": DISPLAY_ONLY,
            "model_use_allowed": DENY,
            "training_allowed": DENY,
            "source_truth_allowed": DENY,
            "rank_logic_allowed": DENY,
            "hidden_sort_allowed": DENY,
            "trade_value_allowed": DENY,
            "pick_value_allowed": DENY,
            "review_required": review_required,
            "notes": notes,
        },
        ARTIFACT_COLUMNS,
    )


def _resolve_identity(row: dict[str, Any], context: _NflverseContext) -> dict[str, Any]:
    roster_index = context.roster_index
    ff_index = context.ff_playerid_index
    sleeper_id = _clean(row.get("player_id"))
    if sleeper_id:
        gsis_matches = roster_index.gsis_by_sleeper.get(sleeper_id, set())
        roster_row = roster_index.latest_by_sleeper.get(sleeper_id)
        if len(gsis_matches) == 1 and roster_row:
            gsis = next(iter(gsis_matches))
            return {
                "status": SAFE_NOW_DISPLAY_ONLY,
                "caveat": "exact_nwr_player_id_to_rosters_sleeper_id",
                "roster_row": roster_row,
                "player_row": context.players_by_gsis.get(gsis, {}),
                "ff_playerid_row": ff_index.latest_by_sleeper.get(sleeper_id, {}),
            }
        if len(gsis_matches) > 1:
            return {
                "status": NEED_IDENTITY_REVIEW,
                "caveat": "one_nwr_player_id_maps_to_multiple_gsis_ids",
                "roster_row": {},
                "player_row": {},
                "ff_playerid_row": {},
            }
        ff_gsis_matches = ff_index.gsis_by_sleeper.get(sleeper_id, set())
        ff_playerid_row = ff_index.latest_by_sleeper.get(sleeper_id)
        if len(ff_gsis_matches) == 1 and ff_playerid_row:
            gsis = next(iter(ff_gsis_matches))
            return {
                "status": SAFE_NOW_DISPLAY_ONLY,
                "caveat": "exact_nwr_player_id_to_ff_playerids_sleeper_id",
                "roster_row": context.roster_index.latest_by_gsis.get(gsis, {}),
                "player_row": context.players_by_gsis.get(gsis, {}),
                "ff_playerid_row": ff_playerid_row,
            }
        if len(ff_gsis_matches) > 1:
            return {
                "status": NEED_IDENTITY_REVIEW,
                "caveat": "one_nwr_player_id_maps_to_multiple_ff_playerids_gsis_ids",
                "roster_row": {},
                "player_row": {},
                "ff_playerid_row": {},
            }
    key = (
        _normalize_name(row.get("player_name") or row.get("player")),
        _clean(row.get("position")),
    )
    name_matches = roster_index.gsis_by_name_position.get(key, set())
    if len(name_matches) == 1:
        return {
            "status": NEED_IDENTITY_REVIEW,
            "caveat": "name_position_match_available_but_not_approved_identity",
            "roster_row": {},
            "player_row": {},
            "ff_playerid_row": {},
        }
    if len(name_matches) > 1:
        return {
            "status": NEED_IDENTITY_REVIEW,
            "caveat": "name_position_match_ambiguous_multiple_gsis_ids",
            "roster_row": {},
            "player_row": {},
            "ff_playerid_row": {},
        }
    return {
        "status": NEED_IDENTITY_REVIEW,
        "caveat": "no_safe_nflverse_identity_match",
        "roster_row": {},
        "player_row": {},
        "ff_playerid_row": {},
    }


def _snap_context(
    row: dict[str, Any],
    roster: dict[str, str],
    context: _NflverseContext,
) -> tuple[dict[str, str], int]:
    if not _dataset_ready(context.health_by_dataset["snap_counts"]):
        return {}, 0
    key = (
        _normalize_name(roster.get("full_name") or row.get("player_name")),
        _clean(roster.get("team") or row.get("nfl_team")),
        _clean(roster.get("position") or row.get("position")),
    )
    snap = context.snap_by_name_team_position.get(key, {})
    count = context.snap_sample_size_by_key.get(key, 0)
    if snap:
        return snap, count
    loose_matches = [
        (candidate_key, candidate_row)
        for candidate_key, candidate_row in context.snap_by_name_team_position.items()
        if candidate_key[0] == key[0] and candidate_key[1] == key[1]
    ]
    if len(loose_matches) == 1:
        loose_key, loose_row = loose_matches[0]
        return loose_row, context.snap_sample_size_by_key.get(loose_key, 0)
    return {}, 0


def _join_health_rows(
    artifact_rows: tuple[dict[str, str], ...],
    health_by_dataset: dict[str, NflverseDatasetHealth],
) -> Iterable[dict[str, str]]:
    total = len(artifact_rows)
    clean = sum(1 for row in artifact_rows if row["identity_join_status"] == SAFE_NOW_DISPLAY_ONLY)
    review = sum(1 for row in artifact_rows if row["identity_join_status"] == NEED_IDENTITY_REVIEW)
    no_identity = sum(
        1
        for row in artifact_rows
        if row["identity_caveat"] == "no_safe_nflverse_identity_match"
    )
    ambiguous = sum(
        1
        for row in artifact_rows
        if row["identity_caveat"]
        in {
            "one_nwr_player_id_maps_to_multiple_gsis_ids",
            "one_nwr_player_id_maps_to_multiple_ff_playerids_gsis_ids",
            "name_position_match_ambiguous_multiple_gsis_ids",
        }
    )
    one_to_many = sum(
        1
        for row in artifact_rows
        if row["identity_caveat"]
        in {
            "one_nwr_player_id_maps_to_multiple_gsis_ids",
            "one_nwr_player_id_maps_to_multiple_ff_playerids_gsis_ids",
        }
    )
    many_to_one = _many_to_one_conflicts(artifact_rows)
    yield _join_row(
        "current_rankings_identity_gate",
        SAFE_NOW_DISPLAY_ONLY if review == 0 and many_to_one == 0 else NEED_IDENTITY_REVIEW,
        "rosters",
        total,
        clean,
        no_identity,
        ambiguous,
        many_to_one,
        one_to_many,
        0 if _dataset_ready(health_by_dataset["rosters"]) else total,
        0,
        review,
        "Current Rankings rows join only through exact NWR player_id to rosters.sleeper_id.",
    )
    for dataset_id, gate in (
        ("players", "players_identity_file_gate"),
        ("ff_playerids", "ff_playerids_crosswalk_gate"),
        ("weekly_rosters", "weekly_roster_status_gate"),
        ("injuries", "injury_context_gate"),
        ("schedules", "next_game_bye_gate"),
        ("depth_charts", "depth_chart_context_gate"),
        ("snap_counts", "snap_count_context_gate"),
        ("player_stats_weekly", "last_active_week_gate"),
        ("player_stats_seasonal", "seasonal_stats_presence_gate"),
        ("draft_picks", "draft_capital_context_gate"),
        ("combine", "combine_context_gate"),
        ("contracts", "contract_context_gate"),
        ("teams", "teams_metadata_gate"),
        ("ff_rankings", "ff_rankings_source_policy_gate"),
    ):
        health = health_by_dataset[dataset_id]
        status = _field_status_for_dataset(health)
        field_columns = _artifact_columns_for_dataset(dataset_id)
        field_matches = _field_match_count(artifact_rows, field_columns)
        field_needs_refresh = _field_value_count(
            artifact_rows,
            field_columns,
            NEED_DATASET_REFRESH,
        )
        yield _join_row(
            gate,
            status,
            dataset_id,
            total,
            field_matches if field_columns else (total if status == SAFE_NOW_DISPLAY_ONLY else 0),
            0,
            0,
            0,
            0,
            field_needs_refresh
            if field_columns
            else (total if status in {NEED_DATASET_REFRESH, NEED_SCHEMA_REVIEW} else 0),
            total if status in {BLOCKED_SOURCE_POLICY, BLOCKED_VENDOR_OR_PRIVATE} else 0,
            total if health.source_policy_status in {"review_only", "transparency_only"} else 0,
            _dataset_message(health),
        )


def _schema_manifest_rows(
    health_by_dataset: dict[str, NflverseDatasetHealth],
) -> Iterable[dict[str, str]]:
    source_map = {
        "nwr_player_id": "current_rankings",
        "nwr_player_name": "current_rankings",
        "nwr_position": "current_rankings",
        "nwr_team": "current_rankings",
        "nwr_source_coverage": "current_rankings",
        "nwr_rank": "current_rankings",
        "final_board_rank": "current_rankings",
        "nflverse_gsis_id": "rosters",
        "nflverse_sleeper_id": "rosters",
        "nflverse_player_name": "rosters",
        "nflverse_team": "rosters",
        "nflverse_position": "rosters",
        "identity_join_status": "rosters",
        "identity_caveat": "rosters",
        "roster_birth_date_derived_age": "rosters",
        "age_source": "rosters",
        "roster_status": "rosters",
        "weekly_roster_status": "weekly_rosters",
        "injury_report_status": "injuries",
        "injury_report_date_week": "injuries",
        "practice_status": "injuries",
        "next_game_context": "schedules",
        "opponent_context": "schedules",
        "bye_context": "schedules",
        "depth_chart_position": "depth_charts",
        "depth_chart_rank": "depth_charts",
        "depth_chart_role": "depth_charts",
        "snap_count_recency": "snap_counts",
        "latest_snap_season": "snap_counts",
        "latest_snap_week": "snap_counts",
        "snap_sample_size": "snap_counts",
        "last_active_season": "player_stats_weekly",
        "last_active_week": "player_stats_weekly",
        "draft_year": "draft_picks",
        "draft_round": "draft_picks",
        "draft_pick": "draft_picks",
        "drafted_team": "draft_picks",
        "contract_context": "contracts",
    }
    guardrail_columns = {
        "per_field_dataset_source",
        "per_field_freshness_source_status",
        "data_coverage_status",
        "display_only",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "rank_logic_allowed",
        "hidden_sort_allowed",
        "trade_value_allowed",
        "pick_value_allowed",
        "review_required",
        "notes",
    }
    for column in ARTIFACT_COLUMNS:
        dataset_id = source_map.get(column, "guardrail_static")
        if column in guardrail_columns or dataset_id == "current_rankings":
            status = SAFE_NOW_DISPLAY_ONLY
        else:
            status = _field_status_for_dataset(health_by_dataset[dataset_id])
        yield _ordered(
            {
                "column_name": column,
                "description": column.replace("_", " "),
                "source_dataset": dataset_id,
                "field_status": status,
                "missing_value_policy": (
                    "Missing data remains Not enough information. Ambiguous identity "
                    "is Review needed. Missing draft is not UDFA."
                ),
                "display_only": DISPLAY_ONLY,
                "model_use_allowed": DENY,
                "training_allowed": DENY,
                "source_truth_allowed": DENY,
                "rank_logic_allowed": DENY,
                "hidden_sort_allowed": DENY,
                "trade_value_allowed": DENY,
                "pick_value_allowed": DENY,
            },
            SCHEMA_COLUMNS,
        )


def _artifact_columns_for_dataset(dataset_id: str) -> tuple[str, ...]:
    return {
        "weekly_rosters": ("weekly_roster_status",),
        "injuries": ("injury_report_status", "injury_report_date_week", "practice_status"),
        "schedules": ("next_game_context", "opponent_context", "bye_context"),
        "depth_charts": ("depth_chart_position", "depth_chart_rank", "depth_chart_role"),
        "snap_counts": ("snap_count_recency", "latest_snap_season", "latest_snap_week"),
        "player_stats_weekly": ("last_active_season", "last_active_week"),
        "draft_picks": ("draft_year", "draft_round", "draft_pick", "drafted_team"),
        "contracts": ("contract_context",),
    }.get(dataset_id, ())


def _field_match_count(
    rows: tuple[dict[str, str], ...],
    columns: tuple[str, ...],
) -> int:
    if not columns:
        return 0
    return sum(
        1
        for row in rows
        if any(row[column] not in _missing_or_gate_tokens() for column in columns)
    )


def _field_value_count(
    rows: tuple[dict[str, str], ...],
    columns: tuple[str, ...],
    value: str,
) -> int:
    if not columns:
        return 0
    return sum(1 for row in rows if any(row[column] == value for column in columns))


def _missing_or_gate_tokens() -> set[str]:
    return {
        "",
        NOT_ENOUGH_INFORMATION,
        NEED_DATASET_REFRESH,
        NEED_IDENTITY_REVIEW,
        NEED_SCHEMA_REVIEW,
        BLOCKED_SOURCE_POLICY,
        BLOCKED_VENDOR_OR_PRIVATE,
        NOT_APPLICABLE,
        REVIEW_NEEDED,
    }


def _current_rankings_rows(
    *,
    rankings_rows: Sequence[dict[str, Any]] | None,
    rankings_source: str,
) -> tuple[tuple[dict[str, Any], ...], str]:
    if rankings_rows is not None:
        return tuple(dict(row) for row in rankings_rows), rankings_source or "test_rankings_rows"
    frozen = load_frozen_board()
    dynasty = load_dynasty_rankings()
    unified = build_unified_player_board(dynasty.frame, frozen.frame)
    if unified.empty:
        return (), "current_unified_rankings_unavailable"
    return tuple(unified.fillna("").to_dict("records")), (
        f"current_unified_rankings; dynasty={dynasty.source_label}; "
        f"frozen={frozen.source_label}"
    )


def _load_ready_dataset_rows(
    health_by_dataset: dict[str, NflverseDatasetHealth], dataset_id: str
) -> tuple[dict[str, str], ...]:
    health = health_by_dataset[dataset_id]
    if not _dataset_ready(health) or not health.data_path:
        return ()
    path = Path(health.data_path)
    if not path.exists() or path.is_dir():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def _dataset_ready(health: NflverseDatasetHealth) -> bool:
    return (
        health.execution_status == EXECUTION_SUCCEEDED
        and health.schema_status == AXIS_PASS
        and health.coverage_status in {AXIS_PASS, AXIS_REVIEW}
        and health.row_count_status in {AXIS_PASS, AXIS_REVIEW}
        and health.missingness_status in {AXIS_PASS, AXIS_REVIEW}
        and health.status in {GREEN, YELLOW}
        and health.source_policy_status != "blocked_policy"
    )


def _field_status_for_dataset(health: NflverseDatasetHealth) -> str:
    if health.dataset_id == "ff_rankings":
        return BLOCKED_VENDOR_OR_PRIVATE
    if health.status == BLOCKED or health.source_policy_status == "blocked_policy":
        return BLOCKED_SOURCE_POLICY
    if health.schema_status not in {AXIS_PASS, AXIS_REVIEW, "not_applicable"}:
        return (
            NEED_SCHEMA_REVIEW
            if health.execution_status == EXECUTION_SUCCEEDED
            else NEED_DATASET_REFRESH
        )
    return SAFE_NOW_DISPLAY_ONLY if _dataset_ready(health) else NEED_DATASET_REFRESH


def _field_gate(health: NflverseDatasetHealth) -> str:
    status = _field_status_for_dataset(health)
    if status == SAFE_NOW_DISPLAY_ONLY:
        return NOT_ENOUGH_INFORMATION
    return status


def _verdict(
    artifact_rows: tuple[dict[str, str], ...],
    join_health_rows: tuple[dict[str, str], ...],
) -> str:
    if not artifact_rows:
        return "YELLOW_BLOCKED_NEEDS_DATASET_REFRESH"
    identity_gate = next(
        row for row in join_health_rows if row["gate"] == "current_rankings_identity_gate"
    )
    if identity_gate["clean_join_rows"] == "0":
        return "YELLOW_BLOCKED_NEEDS_IDENTITY_REVIEW"
    if any(row["status"] == NEED_SCHEMA_REVIEW for row in join_health_rows):
        return "YELLOW_BLOCKED_NEEDS_SCHEMA_REVIEW"
    identity_review_rows = sum(
        int(identity_gate[column])
        for column in (
            "no_nflverse_identity_rows",
            "ambiguous_identity_rows",
            "many_to_one_conflict_rows",
            "one_to_many_conflict_rows",
        )
    )
    if any(
        row["status"] in {NEED_DATASET_REFRESH, BLOCKED_VENDOR_OR_PRIVATE}
        for row in join_health_rows
    ):
        return "YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT"
    if identity_review_rows > 0:
        return "YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT"
    return "GREEN_PLAYER_CONTEXT_DISPLAY_ARTIFACT_BUILT"


def _latest_by_key(
    rows: Sequence[dict[str, str]],
    *,
    key_columns: tuple[str, ...],
) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for index, row in enumerate(rows):
        key = "|".join(_clean(row.get(column)) for column in key_columns)
        if not key.strip("|"):
            continue
        sort_key = _season_week_sort(row, index)
        row_with_sort = dict(row)
        row_with_sort["_sort_key"] = sort_key
        existing = output.get(key)
        if existing is None or sort_key > existing.get("_sort_key", ""):
            output[key] = row_with_sort
    return output


def _latest_snap_rows(rows: Sequence[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    output: dict[tuple[str, str, str], dict[str, str]] = {}
    for index, row in enumerate(rows):
        key = (
            _normalize_name(row.get("player")),
            _clean(row.get("team")),
            _clean(row.get("position")),
        )
        if not key[0]:
            continue
        sort_key = _season_week_sort(row, index)
        row_with_sort = dict(row)
        row_with_sort["_sort_key"] = sort_key
        existing = output.get(key)
        if existing is None or sort_key > existing.get("_sort_key", ""):
            output[key] = row_with_sort
    return output


def _age_from_birth_date(value: Any, source: str) -> tuple[str, str]:
    birth_date = _clean(value)
    if not birth_date:
        return NOT_ENOUGH_INFORMATION, NOT_ENOUGH_INFORMATION
    try:
        born = date.fromisoformat(birth_date[:10])
    except ValueError:
        return REVIEW_NEEDED, source
    today = datetime.now(UTC).date()
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    if years < 15 or years > 70:
        return REVIEW_NEEDED, source
    return str(years), source


def _field_value(health: NflverseDatasetHealth, value: Any) -> str:
    status = _field_status_for_dataset(health)
    if status != SAFE_NOW_DISPLAY_ONLY:
        return status
    return _clean(value) or NOT_ENOUGH_INFORMATION


def _injury_date_week(health: NflverseDatasetHealth, row: dict[str, str]) -> str:
    status = _field_status_for_dataset(health)
    if status != SAFE_NOW_DISPLAY_ONLY:
        return status
    if not row:
        return NOT_ENOUGH_INFORMATION
    parts = [
        f"season={_clean(row.get('season'))}",
        f"week={_clean(row.get('week'))}",
    ]
    modified = _clean(row.get("date_modified"))
    if modified:
        parts.append(f"modified={modified}")
    return "; ".join(parts)


def _depth_chart_role(health: NflverseDatasetHealth, row: dict[str, str]) -> str:
    status = _field_status_for_dataset(health)
    if status != SAFE_NOW_DISPLAY_ONLY:
        return status
    if not row:
        return NOT_ENOUGH_INFORMATION
    parts = []
    for label, column in (
        ("formation", "formation"),
        ("depth_team", "depth_team"),
        ("pos_group", "pos_grp"),
    ):
        value = _clean(row.get(column))
        if value:
            parts.append(f"{label}={value}")
    return "; ".join(parts) if parts else NOT_ENOUGH_INFORMATION


def _contract_context(health: NflverseDatasetHealth, row: dict[str, str]) -> str:
    status = _field_status_for_dataset(health)
    if status != SAFE_NOW_DISPLAY_ONLY:
        return status
    if not row:
        return NOT_ENOUGH_INFORMATION
    parts = []
    for label, column in (
        ("active", "is_active"),
        ("team", "team"),
        ("year_signed", "year_signed"),
        ("years", "years"),
    ):
        value = _clean(row.get(column))
        if value:
            parts.append(f"{label}={value}")
    return "; ".join(parts) if parts else NOT_ENOUGH_INFORMATION


def _schedule_context(team: str, context: _NflverseContext, as_of: date) -> dict[str, str]:
    if not _dataset_ready(context.health_by_dataset["schedules"]):
        return _empty_schedule_context()
    schedule_team = _schedule_team(team)
    team_rows = context.schedules_by_team.get(schedule_team, ())
    dated_rows = sorted(
        (row for row in team_rows if _date_from_row(row) is not None),
        key=lambda row: _date_from_row(row) or date.max,
    )
    future_rows = [row for row in dated_rows if (_date_from_row(row) or date.min) >= as_of]
    if not future_rows:
        return _empty_schedule_context()
    next_game = future_rows[0]
    next_date = _clean(next_game.get("gameday"))
    opponent = _next_opponent(schedule_team, next_game)
    home_away = _home_away(schedule_team, next_game)
    return {
        "next_game_context": (
            f"season={_clean(next_game.get('season'))}; "
            f"week={_clean(next_game.get('week'))}; "
            f"date={next_date}; "
            f"game_id={_clean(next_game.get('game_id'))}"
        ),
        "opponent_context": (
            f"opponent={opponent}; home_away={home_away}"
            if opponent != NOT_ENOUGH_INFORMATION
            else NOT_ENOUGH_INFORMATION
        ),
        "bye_context": _bye_context(schedule_team, team_rows, next_game),
    }


def _empty_schedule_context() -> dict[str, str]:
    return {
        "next_game_context": NOT_ENOUGH_INFORMATION,
        "opponent_context": NOT_ENOUGH_INFORMATION,
        "bye_context": NOT_ENOUGH_INFORMATION,
    }


def _schedule_team(team: str) -> str:
    return {"LAR": "LA", "JAC": "JAX"}.get(_clean(team), _clean(team))


def _next_opponent(team: str, row: dict[str, str]) -> str:
    home = _clean(row.get("home_team"))
    away = _clean(row.get("away_team"))
    if team == home:
        return away or NOT_ENOUGH_INFORMATION
    if team == away:
        return home or NOT_ENOUGH_INFORMATION
    return NOT_ENOUGH_INFORMATION


def _home_away(team: str, row: dict[str, str]) -> str:
    if team == _clean(row.get("home_team")):
        return "home"
    if team == _clean(row.get("away_team")):
        return "away"
    return NOT_ENOUGH_INFORMATION


def _bye_context(
    team: str,
    rows: Sequence[dict[str, str]],
    next_game: dict[str, str],
) -> str:
    season = _clean(next_game.get("season"))
    played_weeks = {
        week
        for row in rows
        if _clean(row.get("season")) == season and _clean(row.get("game_type")) == "REG"
        for week in [_as_int(row.get("week"))]
        if week is not None
    }
    missing_weeks = sorted(set(range(1, 19)) - played_weeks)
    if len(missing_weeks) == 1:
        return f"week={missing_weeks[0]}"
    return NOT_ENOUGH_INFORMATION


def _date_from_row(row: dict[str, str]) -> date | None:
    text = _clean(row.get("gameday"))
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _snap_recency(row: dict[str, str]) -> str:
    if not row:
        return NOT_ENOUGH_INFORMATION
    return f"season={_clean(row.get('season'))}; week={_clean(row.get('week'))}"


def _data_coverage_status(health_by_dataset: dict[str, NflverseDatasetHealth]) -> str:
    ready = [
        dataset_id
        for dataset_id in PLAYER_CONTEXT_DATASETS
        if dataset_id != "ff_rankings" and _dataset_ready(health_by_dataset[dataset_id])
    ]
    blocked_count = sum(
        1
        for dataset_id in PLAYER_CONTEXT_DATASETS
        if _field_status_for_dataset(health_by_dataset[dataset_id])
        in {BLOCKED_SOURCE_POLICY, BLOCKED_VENDOR_OR_PRIVATE}
    )
    needs = [
        dataset_id
        for dataset_id in PLAYER_CONTEXT_DATASETS
        if _field_status_for_dataset(health_by_dataset[dataset_id])
        in {NEED_DATASET_REFRESH, NEED_SCHEMA_REVIEW}
    ]
    return (
        f"ready={';'.join(ready) or NOT_ENOUGH_INFORMATION}; "
        f"needs_refresh={';'.join(needs) or NOT_APPLICABLE}; "
        f"blocked_dataset_count={blocked_count or 0}"
    )


def _freshness_summary(health_by_dataset: dict[str, NflverseDatasetHealth]) -> str:
    parts = []
    for dataset_id in PLAYER_CONTEXT_DATASETS:
        if dataset_id == "ff_rankings":
            continue
        health = health_by_dataset[dataset_id]
        parts.append(
            f"{dataset_id}:{health.status}/{health.freshness_status}/{health.source_policy_status}"
        )
    return "; ".join(parts)


def _notes_for_row(
    identity: dict[str, Any],
    health_by_dataset: dict[str, NflverseDatasetHealth],
    *,
    injury_row: dict[str, str],
    depth_row: dict[str, str],
    draft_row: dict[str, str],
    snap_row: dict[str, str],
) -> str:
    notes = [
        "display-only; no model/rank/source-truth/hidden-sort/trade/pick use",
        str(identity["caveat"]),
    ]
    if not _dataset_ready(health_by_dataset["injuries"]) or not injury_row:
        notes.append("injury_missing_nei")
    if not _dataset_ready(health_by_dataset["depth_charts"]) or not depth_row:
        notes.append("depth_chart_missing_nei")
    if not _dataset_ready(health_by_dataset["snap_counts"]) or not snap_row:
        notes.append("snap_missing_nei")
    if not _dataset_ready(health_by_dataset["draft_picks"]) or not draft_row:
        notes.append("draft_capital_missing_nei")
    return " | ".join(notes)


def _many_to_one_conflicts(rows: tuple[dict[str, str], ...]) -> int:
    by_gsis: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        gsis = row["nflverse_gsis_id"]
        player_id = row["nwr_player_id"]
        if gsis not in {"", NOT_ENOUGH_INFORMATION} and player_id:
            by_gsis[gsis].add(player_id)
    conflicted = {gsis for gsis, ids in by_gsis.items() if len(ids) > 1}
    return sum(1 for row in rows if row["nflverse_gsis_id"] in conflicted)


def _join_row(
    gate: str,
    status: str,
    source_dataset: str,
    total: int,
    clean: int,
    no_identity: int,
    ambiguous: int,
    many_to_one: int,
    one_to_many: int,
    needs_refresh: int,
    blocked: int,
    review_only: int,
    message: str,
) -> dict[str, str]:
    return _ordered(
        {
            "gate": gate,
            "status": status,
            "source_dataset": source_dataset,
            "current_rankings_rows": str(total),
            "clean_join_rows": str(clean),
            "no_nflverse_identity_rows": str(no_identity),
            "ambiguous_identity_rows": str(ambiguous),
            "many_to_one_conflict_rows": str(many_to_one),
            "one_to_many_conflict_rows": str(one_to_many),
            "need_dataset_refresh_rows": str(needs_refresh),
            "blocked_rows": str(blocked),
            "review_only_rows": str(review_only),
            "message": message,
        },
        JOIN_HEALTH_COLUMNS,
    )


def _dataset_message(health: NflverseDatasetHealth) -> str:
    return (
        f"{health.dataset_id}: status={health.status}; execution={health.execution_status}; "
        f"schema={health.schema_status}; coverage={health.coverage_status}; "
        f"rows={health.row_count}; policy={health.source_policy_status}."
    )


def _readme_markdown(result: NflversePlayerContextResult) -> str:
    return "\n".join(
        [
            "# NFLVerse Player Context Display Artifact",
            "",
            f"Verdict: `{result.verdict}`",
            f"Current Rankings rows evaluated: `{result.current_rankings_rows}`",
            "",
            "This directory contains compact, derived, review/display-only player context "
            "from the approved local nflverse refresh-health contract. It is not raw cache.",
            "",
            "## Artifact Grain",
            "",
            "- Primary app artifact: one row per current NWR Rankings/unified-board player.",
            "- Join-health support: one row per gate/dataset, used to explain coverage and "
            "deferred fields.",
            "- No broad observed-nflverse-player artifact is approved in this lane.",
            "",
            "## App-Lane Consumption Contract",
            "",
            "App lanes may read `nflverse_player_context_display_artifact.csv` and "
            "`nflverse_player_context_join_health.csv` as display context only. They must "
            "not read raw `C:\\NWR_SHARED_DATA` nflverse files directly.",
            "",
            "- Join on `nwr_player_id` only.",
            "- Required row filter for player-level use: "
            "`identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.",
            "- Confirm the relevant field has `field_status=SAFE_NOW_DISPLAY_ONLY` in "
            "`nflverse_player_context_schema_manifest.csv` before showing it.",
            "- Treat `Not enough information`, `NEED_DATASET_REFRESH`, "
            "`NEED_IDENTITY_REVIEW`, `NEED_SCHEMA_REVIEW`, `BLOCKED_SOURCE_POLICY`, and "
            "`BLOCKED_VENDOR_OR_PRIVATE` as unavailable display values.",
            "- Every row remains `display_only=true` with model/training/source-truth/rank/"
            "hidden-sort/trade/pick flags set to `false`.",
            "",
            "## Safe Display Fields Now",
            "",
            "- Identity/profile: `nflverse_gsis_id`, `nflverse_sleeper_id`, "
            "`nflverse_player_name`, `nflverse_team`, `nflverse_position` after the "
            "required identity filter.",
            "- Roster/age: `roster_birth_date_derived_age`, `age_source`, "
            "`roster_status`, `weekly_roster_status`.",
            "- Review/status context: `injury_report_status`, `injury_report_date_week`, "
            "`practice_status`, `depth_chart_position`, `depth_chart_rank`, "
            "`depth_chart_role`, `snap_count_recency`, `latest_snap_season`, "
            "`latest_snap_week`, `snap_sample_size`, `last_active_season`, "
            "`last_active_week`, `draft_year`, `draft_round`, `draft_pick`, "
            "`drafted_team`, non-financial `contract_context`, `next_game_context`, "
            "`opponent_context`, and `bye_context`, only when values are present and "
            "not gate tokens.",
            "",
            "## Deferred Or Blocked",
            "",
            "- `ff_rankings` is blocked and unused.",
            "- Schedule fields are display-only and require current/future approved "
            "schedules. If a row still says `Not enough information`, app lanes must "
            "not infer an opponent, bye, or clean schedule state.",
            "- Rows with `identity_join_status=NEED_IDENTITY_REVIEW` need separate identity "
            "review before any player-level app display.",
        ]
    )


def _source_policy_markdown(result: NflversePlayerContextResult) -> str:
    return "\n".join(
        [
            "# NFLVerse Player Context Source Policy",
            "",
            f"Verdict: `{result.verdict}`",
            "",
            "- `display_only=true` for every row.",
            "- `model_use_allowed=false`, `training_allowed=false`, "
            "`source_truth_allowed=false`, `rank_logic_allowed=false`, "
            "`hidden_sort_allowed=false`, `trade_value_allowed=false`, and "
            "`pick_value_allowed=false`.",
            "- Missing data remains `Not enough information` or `NEED_DATASET_REFRESH`.",
            "- Missing injury is not healthy.",
            "- Missing depth chart data is not no-role.",
            "- Missing snap data is not zero snaps.",
            "- Missing draft capital is not confirmed UDFA.",
            "- Ambiguous identity and fallback name matches remain `Review needed`.",
            "- `ff_rankings` remains blocked and is not used.",
            "- Contract context is non-financial display metadata only; it excludes dollar "
            "values, guarantees, APY, cap values, and valuation signals.",
            "- Schedule context is only populated when a current/future game context is "
            "approved. The current artifact leaves it unavailable rather than inferring a "
            "bye or next opponent from stale/historical schedules.",
        ]
    )


def _build_report_markdown(result: NflversePlayerContextResult) -> str:
    lines = [
        "# NFLVerse Player Context Build Report",
        "",
        f"Verdict: `{result.verdict}`",
        f"Current Rankings source: `{result.rankings_source}`",
        f"Current Rankings rows: `{result.current_rankings_rows}`",
        f"Artifact rows: `{len(result.artifact_rows)}`",
        f"Safe refresh attempted: `{str(result.safe_refresh_attempted).lower()}`",
        f"Safe refresh status: `{result.safe_refresh_status}`",
        "",
        "## Dataset Inspection",
        "",
        "| dataset | status | rows | coverage | freshness | policy | usability | local path |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for dataset_id in PLAYER_CONTEXT_DATASETS:
        health = result.health_by_dataset[dataset_id]
        lines.append(
            "| "
            + " | ".join(
                [
                    dataset_id,
                    health.status,
                    health.row_count,
                    health.season_coverage,
                    health.freshness_status,
                    health.source_policy_status,
                    _field_status_for_dataset(health),
                    health.data_path or NOT_ENOUGH_INFORMATION,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _guardrail_report_markdown(result: NflversePlayerContextResult) -> str:
    flag_fields = (
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "rank_logic_allowed",
        "hidden_sort_allowed",
        "trade_value_allowed",
        "pick_value_allowed",
    )
    flags_ok = all(
        row["display_only"] == DISPLAY_ONLY and all(row[field] == DENY for field in flag_fields)
        for row in result.artifact_rows
    )
    ff_rankings_blocked = result.health_by_dataset["ff_rankings"].status == BLOCKED
    return "\n".join(
        [
            "# NFLVerse Player Context Guardrail Report",
            "",
            f"Guardrail flags valid: `{str(flags_ok).lower()}`",
            f"`ff_rankings` blocked and unused: `{str(ff_rankings_blocked).lower()}`",
            "",
            "No app behavior, Rankings behavior, Player Compare behavior, Trading Lab behavior, "
            "model logic, rank logic, source truth, hidden sort, trade value, pick value, "
            "`latest_candidate`, or `latest_approved` is changed by this lane.",
            "",
            "The service may read approved local NFLVerse cache only while building tracked "
            "derived docs artifacts. App pages must consume the tracked CSVs or a repo-backed "
            "service layer, not raw shared-cache files.",
        ]
    )


def _write_csv(path: Path, rows: Iterable[dict[str, str]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _season_week_sort(row: dict[str, Any], index: int) -> str:
    season = _as_int(row.get("season")) or -1
    week = _as_int(row.get("week")) or -1
    return f"{season:04d}:{week:03d}:{index:08d}"


def _ordered(row: dict[str, Any], columns: tuple[str, ...]) -> dict[str, str]:
    return {column: str(row.get(column, "")) for column in columns}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_name(value: Any) -> str:
    return "".join(character.lower() for character in _clean(value) if character.isalnum())


def _as_int(value: Any) -> int | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None
