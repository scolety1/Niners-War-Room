from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.services.nflverse_refresh_health_service import (
    FULL_SAFE_REFRESH_DATASET_IDS,
)
from src.services.nflverse_refresh_health_service import (
    NFLVERSE_DATASET_SPECS as HEALTH_DATASET_SPECS,
)

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse")
USER_AGENT = "NWR-nflverse-Scheduled-Puller-V0"
DEFAULT_DATASETS = FULL_SAFE_REFRESH_DATASET_IDS
SAMPLE_PLAYERS = (
    "Drake Maye",
    "Jaylen Warren",
    "Darren Waller",
    "Brock Purdy",
    "Dak Prescott",
    "Zay Flowers",
    "Keenan Allen",
    "Chris Olave",
    "Rashee Rice",
    "Jameson Williams",
    "Brian Thomas Jr",
    "Brian Thomas",
    "Alec Pierce",
)
SAMPLE_PLAYER_ALIASES = {
    "Brian Thomas": ("Brian Thomas Jr",),
    "Brian Thomas Jr": ("Brian Thomas",),
}
PLAYER_NAME_FIELDS = {
    "player_name",
    "player_display_name",
    "display_name",
    "football_name",
    "full_name",
    "name",
    "player",
}
QUARANTINE_FIELD_PATTERNS = (
    "fantasy_points",
    "fantasy_points_ppr",
    "headshot_url",
    "_exp",
    "expected",
    "_diff",
    "epa",
    "cpoe",
    "pacr",
    "racr",
    "wopr",
    "target_share",
    "air_yard_share",
    "air_yards_share",
    "route_share",
    "snap_share",
    "share",
)
QUARANTINE_ALLOWED_EXACT_FIELDS = {
    "years_exp",
}
FORBIDDEN_USE = (
    "private_value",
    "veteran_private_values",
    "hidden_sort",
    "hidden_rank",
    "model_training",
    "final_draft_day_decision",
    "simulation",
    "recommendation",
    "production_deployment",
    "latest_candidate",
    "latest_approved",
)


class NflversePullError(RuntimeError):
    pass


class MissingNflreadpyError(NflversePullError):
    pass


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    function_names: tuple[str, ...]
    file_name: str
    required: bool = False
    loader_kwargs_variants: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class DatasetResult:
    name: str
    function_name: str
    file_name: str
    status: str
    row_count: int | None
    column_count: int | None
    byte_count: int
    sha256: str
    field_names: list[str]
    field_roles: dict[str, list[str]]
    health_summary: dict[str, str | int | None]
    quarantined_fields: list[str]
    matched_players: list[str]
    identity_matches: list[dict[str, str]]
    missing_sample_players: list[str]
    warning: str = ""
    error: str = ""


@dataclass(frozen=True)
class NflversePullResult:
    snapshot_dir: Path
    report_path: Path
    metadata_path: Path
    dataset_results: list[DatasetResult]
    warnings: list[str]


DATASET_ALIASES: dict[str, str] = {
    alias: spec.dataset_id
    for spec in HEALTH_DATASET_SPECS
    for alias in spec.runner_dataset_names
    if alias != spec.dataset_id
}

DATASET_SPECS = {
    "player_stats_weekly": DatasetSpec(
        name="player_stats_weekly",
        function_names=("load_player_stats", "import_weekly_data"),
        file_name="player_stats_weekly.csv",
        loader_kwargs_variants=({"summary_level": "week"}, {}),
    ),
    "player_stats_seasonal": DatasetSpec(
        name="player_stats_seasonal",
        function_names=("load_player_stats", "import_seasonal_data", "load_seasonal_data"),
        file_name="player_stats_seasonal.csv",
        loader_kwargs_variants=({"summary_level": "reg"}, {}),
    ),
    "play_by_play": DatasetSpec(
        name="play_by_play",
        function_names=("load_pbp", "import_pbp_data"),
        file_name="play_by_play.csv",
    ),
    "team_stats": DatasetSpec(
        name="team_stats",
        function_names=("load_team_stats", "import_team_stats"),
        file_name="team_stats.csv",
    ),
    "schedules": DatasetSpec(
        name="schedules",
        function_names=("load_schedules", "import_schedules"),
        file_name="schedules.csv",
    ),
    "players": DatasetSpec(
        name="players",
        function_names=("load_players", "import_players"),
        file_name="players.csv",
    ),
    "rosters": DatasetSpec(
        name="rosters",
        function_names=("load_rosters", "import_rosters"),
        file_name="rosters.csv",
    ),
    "weekly_rosters": DatasetSpec(
        name="weekly_rosters",
        function_names=("load_rosters_weekly", "load_weekly_rosters", "import_weekly_rosters"),
        file_name="weekly_rosters.csv",
    ),
    "ff_playerids": DatasetSpec(
        name="ff_playerids",
        function_names=("load_ff_playerids", "import_ff_playerids"),
        file_name="ff_playerids.csv",
    ),
    "depth_charts": DatasetSpec(
        name="depth_charts",
        function_names=("load_depth_charts", "import_depth_charts"),
        file_name="depth_charts.csv",
    ),
    "injuries": DatasetSpec(
        name="injuries",
        function_names=("load_injuries", "import_injuries"),
        file_name="injuries.csv",
    ),
    "snap_counts": DatasetSpec(
        name="snap_counts",
        function_names=("load_snap_counts", "import_snap_counts"),
        file_name="snap_counts.csv",
    ),
    "participation": DatasetSpec(
        name="participation",
        function_names=("load_participation", "import_participation"),
        file_name="participation.csv",
    ),
    "ftn_charting": DatasetSpec(
        name="ftn_charting",
        function_names=("load_ftn_charting", "import_ftn_charting"),
        file_name="ftn_charting.csv",
    ),
    "pfr_advstats": DatasetSpec(
        name="pfr_advstats",
        function_names=("load_pfr_advstats", "import_pfr_advstats"),
        file_name="pfr_advstats.csv",
        loader_kwargs_variants=(
            {"stat_type": "pass"},
            {"stat_type": "rush"},
            {"stat_type": "rec"},
            {},
        ),
    ),
    "nextgen_stats": DatasetSpec(
        name="nextgen_stats",
        function_names=("load_nextgen_stats", "import_nextgen_stats"),
        file_name="nextgen_stats.csv",
        loader_kwargs_variants=(
            {"stat_type": "passing"},
            {"stat_type": "rushing"},
            {"stat_type": "receiving"},
            {},
        ),
    ),
    "draft_picks": DatasetSpec(
        name="draft_picks",
        function_names=("load_draft_picks", "import_draft_picks"),
        file_name="draft_picks.csv",
    ),
    "combine": DatasetSpec(
        name="combine",
        function_names=("load_combine", "import_combine"),
        file_name="combine.csv",
    ),
    "contracts": DatasetSpec(
        name="contracts",
        function_names=("load_contracts", "import_contracts"),
        file_name="contracts.csv",
    ),
    "trades": DatasetSpec(
        name="trades",
        function_names=("load_trades", "import_trades"),
        file_name="trades.csv",
    ),
    "teams": DatasetSpec(
        name="teams",
        function_names=("load_teams", "import_teams"),
        file_name="teams.csv",
    ),
    "officials": DatasetSpec(
        name="officials",
        function_names=("load_officials", "import_officials"),
        file_name="officials.csv",
    ),
    "espn_qbr": DatasetSpec(
        name="espn_qbr",
        function_names=("load_espn_qbr", "import_espn_qbr"),
        file_name="espn_qbr.csv",
    ),
    "ff_opportunity": DatasetSpec(
        name="ff_opportunity",
        function_names=(
            "load_ff_opportunity",
            "load_opportunity",
            "import_opportunity",
            "import_player_stats",
        ),
        file_name="ff_opportunity.csv",
        loader_kwargs_variants=(
            {"stat_type": "weekly"},
            {"stat_type": "pbp_pass"},
            {"stat_type": "pbp_rush"},
            {},
        ),
    ),
}


def run_nflverse_pull(
    *,
    seasons: list[int],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    dataset_names: list[str] | None = None,
    snapshot_label: str | None = None,
    skip_live: bool = False,
    loader_module: Any | None = None,
    sample_players: tuple[str, ...] = SAMPLE_PLAYERS,
) -> NflversePullResult:
    if not seasons:
        raise NflversePullError("at least one season is required")

    names = dataset_names or list(DEFAULT_DATASETS)
    specs = [_dataset_spec(name) for name in names]
    nflreadpy = loader_module
    warnings: list[str] = []
    if skip_live:
        warnings.append("live nflreadpy loading skipped by --skip-live")
    else:
        nflreadpy = nflreadpy or _import_nflreadpy()

    snapshot = snapshot_label or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    snapshot_dir = output_root / snapshot
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    results: list[DatasetResult] = []
    if skip_live:
        for spec in specs:
            results.append(_skipped_dataset_result(spec, "skip_live requested"))
    else:
        assert nflreadpy is not None
        for spec in specs:
            results.append(
                _load_dataset(
                    nflreadpy=nflreadpy,
                    spec=spec,
                    seasons=seasons,
                    snapshot_dir=snapshot_dir,
                    sample_players=sample_players,
                )
            )

    metadata_path = snapshot_dir / "snapshot_metadata.json"
    report_path = snapshot_dir / "nflverse_pull_report.md"
    metadata = _metadata_payload(
        seasons=seasons,
        snapshot_label=snapshot,
        dataset_results=results,
        warnings=warnings,
        nflreadpy_module=nflreadpy,
        skip_live=skip_live,
    )
    metadata_path.write_bytes(_json_bytes(metadata))
    report_path.write_text(_markdown_report(metadata, results), encoding="utf-8")
    return NflversePullResult(
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        metadata_path=metadata_path,
        dataset_results=results,
        warnings=warnings,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a local-only raw nflverse/nflreadpy stats snapshot and redacted "
            "report. Does not create Lane Exchange packages or approvals."
        )
    )
    parser.add_argument("--seasons", nargs="+", type=int, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--snapshot-label", default=None)
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=tuple(sorted(set(DATASET_SPECS) | set(DATASET_ALIASES))),
        default=list(DEFAULT_DATASETS),
    )
    parser.add_argument(
        "--skip-live",
        action="store_true",
        help="Create metadata/report scaffolding without importing nflreadpy datasets.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_nflverse_pull(
            seasons=args.seasons,
            output_root=args.output_root,
            dataset_names=args.datasets,
            snapshot_label=args.snapshot_label,
            skip_live=args.skip_live,
        )
    except Exception as exc:
        print(f"nflverse scheduled pull failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"snapshot_dir={result.snapshot_dir}")
    print(f"report_path={result.report_path}")
    for dataset in result.dataset_results:
        print(
            f"{dataset.name}: {dataset.status} rows={dataset.row_count} "
            f"cols={dataset.column_count} sha256={dataset.sha256}"
        )
    return 0


def _import_nflreadpy() -> Any:
    try:
        return importlib.import_module("nflreadpy")
    except ModuleNotFoundError as exc:
        raise MissingNflreadpyError(
            "nflreadpy is not installed in this Python environment. "
            "Install it only in an approved local-only scratch/runtime, never into "
            "an NWR repo, then rerun this puller with that interpreter."
        ) from exc


def _dataset_spec(name: str) -> DatasetSpec:
    name = DATASET_ALIASES.get(name, name)
    try:
        return DATASET_SPECS[name]
    except KeyError as exc:
        raise NflversePullError(f"unsupported dataset: {name}") from exc


def _load_dataset(
    *,
    nflreadpy: Any,
    spec: DatasetSpec,
    seasons: list[int],
    snapshot_dir: Path,
    sample_players: tuple[str, ...],
) -> DatasetResult:
    function_name, loader = _find_loader(nflreadpy, spec)
    if loader is None:
        return _skipped_dataset_result(
            spec,
            f"no supported nflreadpy function found: {', '.join(spec.function_names)}",
            status="missing_loader",
        )

    output_path = snapshot_dir / spec.file_name
    try:
        rows: list[dict[str, Any]] = []
        fields: list[str] = []
        last_type_error: TypeError | None = None
        for kwargs in spec.loader_kwargs_variants or ({},):
            try:
                frame = _call_loader(loader, seasons, kwargs)
            except TypeError as exc:
                if len(spec.loader_kwargs_variants) > 1:
                    last_type_error = exc
                    continue
                raise
            variant_rows, variant_fields = _frame_to_rows(frame)
            if kwargs and len(spec.loader_kwargs_variants) > 1:
                variant_rows = [_with_loader_variant(row, kwargs) for row in variant_rows]
                variant_fields = _field_names(variant_rows, (*variant_fields, *kwargs))
            rows.extend(variant_rows)
            fields = _field_names(rows, (*fields, *variant_fields))
        if not fields and last_type_error is not None:
            raise last_type_error
        body = _csv_bytes(rows, fields)
        output_path.write_bytes(body)
        field_roles = _field_roles(fields)
        quarantined = _quarantined_fields(fields)
        identity_matches, missing = _identity_matches(rows, fields, sample_players)
        matched = [match["query"] for match in identity_matches]
        return DatasetResult(
            name=spec.name,
            function_name=function_name,
            file_name=spec.file_name,
            status="ok",
            row_count=len(rows),
            column_count=len(fields),
            byte_count=len(body),
            sha256=_sha256(body),
            field_names=fields,
            field_roles=field_roles,
            health_summary=_dataset_health_summary(rows, fields),
            quarantined_fields=quarantined,
            matched_players=matched,
            identity_matches=identity_matches,
            missing_sample_players=missing,
            warning=_dataset_warning(spec.name, quarantined),
        )
    except Exception as exc:
        return DatasetResult(
            name=spec.name,
            function_name=function_name,
            file_name=spec.file_name,
            status="failed",
            row_count=None,
            column_count=None,
            byte_count=0,
            sha256=_sha256(b""),
            field_names=[],
            field_roles={},
            health_summary={
                "season_coverage": None,
                "key_column_coverage": None,
                "duplicate_key_count": None,
            },
            quarantined_fields=[],
            matched_players=[],
            identity_matches=[],
            missing_sample_players=list(sample_players),
            error=f"{type(exc).__name__}: {exc}",
        )


def _find_loader(nflreadpy: Any, spec: DatasetSpec) -> tuple[str, Any | None]:
    for function_name in spec.function_names:
        loader = getattr(nflreadpy, function_name, None)
        if callable(loader):
            return function_name, loader
    return "", None


def _call_loader(loader: Any, seasons: list[int], kwargs: dict[str, Any]) -> Any:
    attempts = [
        lambda: loader(seasons, **kwargs),
        lambda: loader(seasons=seasons, **kwargs),
        lambda: loader(years=seasons, **kwargs),
        lambda: loader(**kwargs),
    ]
    if not kwargs:
        attempts.extend(
            [
                lambda: loader(seasons),
                lambda: loader(seasons=seasons),
                lambda: loader(years=seasons),
                lambda: loader(),
            ]
        )
    last_error: TypeError | None = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def _with_loader_variant(row: dict[str, Any], kwargs: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for key, value in kwargs.items():
        output.setdefault(key, value)
    return output


def _frame_to_rows(frame: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if hasattr(frame, "to_dicts"):
        rows = [dict(row) for row in frame.to_dicts()]
        return rows, _field_names(rows, getattr(frame, "columns", None))
    if hasattr(frame, "to_pandas"):
        return _frame_to_rows(frame.to_pandas())
    if hasattr(frame, "to_dict"):
        try:
            raw_records = frame.to_dict(orient="records")
        except TypeError:
            raw_records = frame.to_dict("records")
        rows = [dict(row) for row in raw_records]
        return rows, _field_names(rows, getattr(frame, "columns", None))
    if isinstance(frame, list):
        rows = [dict(row) for row in frame if isinstance(row, dict)]
        return rows, _field_names(rows, None)
    raise NflversePullError(f"unsupported nflreadpy frame type: {type(frame).__name__}")


def _field_names(rows: list[dict[str, Any]], columns: Any | None) -> list[str]:
    if columns is not None:
        return [str(column) for column in columns]
    names: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            name = str(key)
            if name not in seen:
                names.append(name)
                seen.add(name)
    return names


def _dataset_health_summary(
    rows: list[dict[str, Any]],
    fields: list[str],
) -> dict[str, str | int | None]:
    season_field = _first_field(fields, ("season", "draft_year", "year"))
    week_field = _first_field(fields, ("week",))
    player_field = _first_field(
        fields,
        (
            "player_id",
            "gsis_id",
            "player_name",
            "player_display_name",
            "full_name",
            "player",
            "name",
        ),
    )
    seasons = {str(row.get(season_field)) for row in rows if season_field and row.get(season_field)}
    weeks = {str(row.get(week_field)) for row in rows if week_field and row.get(week_field)}
    key_fields = [field for field in (season_field, week_field, player_field) if field]
    seen: set[tuple[str, ...]] = set()
    duplicate_count = 0
    if key_fields:
        for row in rows:
            key = tuple(str(row.get(field) or "") for field in key_fields)
            if not any(key):
                continue
            if key in seen:
                duplicate_count += 1
            seen.add(key)
    missing_key_columns = [
        label
        for label, field in (
            ("season", season_field),
            ("week", week_field),
            ("player", player_field),
        )
        if not field
    ]
    season_coverage = _range_text(seasons) if seasons else "Not enough information"
    if weeks:
        season_coverage = f"seasons={season_coverage}; weeks={len(weeks)}"
    else:
        season_coverage = f"seasons={season_coverage}"
    return {
        "season_coverage": season_coverage,
        "key_column_coverage": (
            f"present={3 - len(missing_key_columns)}/3; "
            f"missing={'; '.join(missing_key_columns) or 'none'}"
        ),
        "duplicate_key_count": duplicate_count,
    }


def _first_field(fields: list[str], candidates: tuple[str, ...]) -> str:
    by_lower = {field.lower(): field for field in fields}
    for candidate in candidates:
        match = by_lower.get(candidate.lower())
        if match:
            return match
    return ""


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    if not fields:
        fields = ["empty"]
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _cell(value) for key, value in row.items()})
    return buffer.getvalue().encode("utf-8")


def _cell(value: Any) -> Any:
    if isinstance(value, (list, dict, tuple, set)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return value


def _quarantined_fields(fields: list[str]) -> list[str]:
    quarantined: list[str] = []
    for field in fields:
        lower = field.lower()
        if lower in QUARANTINE_ALLOWED_EXACT_FIELDS:
            continue
        if any(pattern in lower for pattern in QUARANTINE_FIELD_PATTERNS):
            quarantined.append(field)
    return sorted(set(quarantined))


def _field_roles(fields: list[str]) -> dict[str, list[str]]:
    roles = {
        "player_id": [],
        "player_name": [],
        "team": [],
        "season": [],
        "week": [],
        "position": [],
    }
    for field in fields:
        lower = field.lower()
        if lower in PLAYER_NAME_FIELDS:
            roles["player_name"].append(field)
        if lower in {
            "player_id",
            "gsis_id",
            "sleeper_id",
            "pfr_player_id",
            "pfr_id",
            "espn_id",
            "sportraradar_id",
            "sportradar_id",
            "yahoo_id",
            "rotowire_id",
            "fantasy_data_id",
        } or ("player" in lower and lower.endswith("_id")):
            roles["player_id"].append(field)
        if lower in {"team", "recent_team", "opponent", "opponent_team", "club_code"}:
            roles["team"].append(field)
        if lower in {"season", "season_type", "game_type"}:
            roles["season"].append(field)
        if lower in {"week", "game_week"}:
            roles["week"].append(field)
        if lower in {"position", "position_group", "ngs_position", "depth_chart_position"}:
            roles["position"].append(field)
    return {role: columns for role, columns in roles.items() if columns}


def _identity_matches(
    rows: list[dict[str, Any]], fields: list[str], sample_players: tuple[str, ...]
) -> tuple[list[dict[str, str]], list[str]]:
    name_fields = [
        field
        for field in fields
        if field.lower() in PLAYER_NAME_FIELDS
    ]
    if not name_fields:
        return [], list(sample_players)

    available: dict[str, dict[str, str]] = {}
    for row in rows:
        for field in name_fields:
            if row.get(field):
                source_name = str(row[field])
                available.setdefault(
                    _norm(source_name),
                    {"matched_name": source_name, "field": field},
                )

    matches: list[dict[str, str]] = []
    missing: list[str] = []
    for query in sample_players:
        candidates = (query, *SAMPLE_PLAYER_ALIASES.get(query, ()))
        match = _match_identity_candidate(query, candidates, available)
        if match:
            matches.append(match)
        else:
            missing.append(query)
    return matches, missing


def _match_identity_candidate(
    query: str, candidates: tuple[str, ...], available: dict[str, dict[str, str]]
) -> dict[str, str] | None:
    for candidate in candidates:
        source = available.get(_norm(candidate))
        if source:
            return {
                "query": query,
                "matched_name": source["matched_name"],
                "match_type": "exact" if _norm(candidate) == _norm(query) else "alias",
                "matched_on": candidate,
                "source_field": source["field"],
            }
    return None


def _dataset_warning(name: str, quarantined_fields: list[str]) -> str:
    if not quarantined_fields:
        return ""
    return (
        f"YELLOW: {name} contains fields quarantined from private value/hidden sorting "
        f"until later source policy approval: {', '.join(quarantined_fields[:20])}"
    )


def _skipped_dataset_result(
    spec: DatasetSpec,
    reason: str,
    *,
    status: str = "skipped",
) -> DatasetResult:
    return DatasetResult(
        name=spec.name,
        function_name="",
        file_name=spec.file_name,
        status=status,
        row_count=None,
        column_count=None,
        byte_count=0,
        sha256=_sha256(b""),
        field_names=[],
        field_roles={},
        health_summary={
            "season_coverage": None,
            "key_column_coverage": None,
            "duplicate_key_count": None,
        },
        quarantined_fields=[],
        matched_players=[],
        identity_matches=[],
        missing_sample_players=list(SAMPLE_PLAYERS),
        warning=f"YELLOW: {reason}",
    )


def _metadata_payload(
    *,
    seasons: list[int],
    snapshot_label: str,
    dataset_results: list[DatasetResult],
    warnings: list[str],
    nflreadpy_module: Any | None,
    skip_live: bool,
) -> dict[str, Any]:
    return {
        "source": "nflverse/nflreadpy local raw snapshot",
        "puller": "nflverse_scheduled_pull_v0",
        "created_at": datetime.now(UTC).isoformat(),
        "snapshot_label": snapshot_label,
        "package_tool": "nflreadpy",
        "package_version": _package_version(nflreadpy_module),
        "user_agent": USER_AGENT,
        "seasons": seasons,
        "skip_live": skip_live,
        "approval_status": "raw_snapshot_only_not_approved",
        "creates_lane_exchange_packages": False,
        "updates_latest_candidate": False,
        "updates_latest_approved": False,
        "allowed_use": [
            "local_raw_snapshot",
            "display_stat_context_source_audit",
            "future_candidate_normalizer_input_after_review",
        ],
        "forbidden_use": list(FORBIDDEN_USE),
        "field_policy": {
            "stats_are_display_context_only": True,
            "quarantined_fields_not_deleted_from_raw_snapshot": True,
            "no_private_value": True,
            "no_hidden_rank_sort": True,
            "no_model_training": True,
        },
        "warnings": warnings,
        "datasets": [
            {
                "name": result.name,
                "dataset_id": result.name,
                "function_name": result.function_name,
                "file_name": result.file_name,
                "status": result.status,
                "row_count": result.row_count,
                "column_count": result.column_count,
                "byte_count": result.byte_count,
                "sha256": result.sha256,
                "schema_fingerprint": _schema_fingerprint(result.field_names),
                "field_names": result.field_names,
                "field_name_summary": result.field_names[:60],
                "field_roles": result.field_roles,
                "health_summary": result.health_summary,
                "quarantined_fields": result.quarantined_fields,
                "matched_sample_players": result.matched_players,
                "identity_matches": result.identity_matches,
                "missing_sample_players": result.missing_sample_players,
                "warning": result.warning,
                "error": result.error,
            }
            for result in dataset_results
        ],
    }


def _markdown_report(metadata: dict[str, Any], results: list[DatasetResult]) -> str:
    lines = [
        "# nflverse Scheduled Pull V0 Raw Snapshot Report",
        "",
        "## Scope",
        "",
        "Local-only raw nflverse/nflreadpy stats snapshot. Stats are display/stat "
        "context only. This report does not approve private value, hidden ranking, "
        "hidden sorting, model training, Lane Exchange publishing, simulations, "
        "recommendations, deployment, or final draft-day use.",
        "",
        "## Snapshot",
        "",
        f"- Created at: `{metadata['created_at']}`",
        f"- Seasons: `{', '.join(str(season) for season in metadata['seasons'])}`",
        f"- Package/tool: `{metadata['package_tool']}`",
        f"- Package version: `{metadata['package_version']}`",
        f"- Snapshot label: `{metadata['snapshot_label']}`",
        f"- Skip live: `{metadata['skip_live']}`",
        "",
        "## Dataset Status",
        "",
        "| Dataset | Status | Rows | Columns | SHA256 | Quarantined fields | "
        "Matched sample players |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            f"| `{result.name}` | `{result.status}` | {result.row_count} | "
            f"{result.column_count} | `{result.sha256}` | "
            f"{len(result.quarantined_fields)} | {len(result.matched_players)} |"
        )
    lines.extend(["", "## Quarantined Field Warnings", ""])
    quarantine_warnings = [
        result.warning
        for result in results
        if result.quarantined_fields and result.warning
    ]
    if quarantine_warnings:
        lines.extend(f"- {warning}" for warning in quarantine_warnings)
    else:
        lines.append("- none")
    lines.extend(["", "## Identity Match Summary", ""])
    for result in results:
        if result.status != "ok":
            continue
        lines.append(
            f"- `{result.name}`: matched {len(result.matched_players)} of "
            f"{len(SAMPLE_PLAYERS)} sample players."
        )
        for match in result.identity_matches:
            if match["match_type"] == "alias":
                lines.append(
                    f"  - `{match['query']}` matched source `{match['matched_name']}` "
                    f"via alias `{match['matched_on']}` in `{match['source_field']}`."
                )
        if result.missing_sample_players:
            lines.append(
                f"  Missing: {', '.join(result.missing_sample_players)}"
            )
    lines.extend(["", "## Dataset Field Summaries", ""])
    for result in results:
        if result.status != "ok":
            warning = result.warning or result.error or "not loaded"
            lines.append(f"- `{result.name}`: `{result.status}` - {warning}")
            continue
        preview = ", ".join(result.field_names[:40])
        lines.append(f"- `{result.name}` ({result.column_count} fields): {preview}")
        if result.field_roles:
            role_summary = "; ".join(
                f"{role}: {', '.join(columns)}"
                for role, columns in result.field_roles.items()
            )
            lines.append(f"  Likely roles: {role_summary}")
    lines.extend(["", "## Guardrails", ""])
    lines.extend(f"- {item}" for item in _guardrail_lines())
    return "\n".join(lines) + "\n"


def _guardrail_lines() -> list[str]:
    return [
        "Raw stats outputs stay local-only outside Git.",
        "No Lane Exchange packages were created.",
        "`latest_candidate` was not updated.",
        "`latest_approved` was not updated.",
        "Stats are not private value.",
        "Stats are not veteran_private_values.",
        "No hidden ranking, hidden sorting, model training, simulation, recommendation, "
        "or deployment path is approved.",
    ]


def _package_version(module: Any | None) -> str:
    if module is None:
        return "not_loaded"
    return str(getattr(module, "__version__", "unknown"))


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _schema_fingerprint(fields: list[str]) -> str:
    if not fields:
        return ""
    body = "\n".join(f"{index}:{field}" for index, field in enumerate(fields)).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _norm(value: Any) -> str:
    return "".join(char for char in str(value).lower() if char.isalnum())


def _range_text(values: set[str]) -> str:
    numeric: list[int] = []
    for value in values:
        try:
            numeric.append(int(value))
        except (TypeError, ValueError):
            return "; ".join(sorted(values))
    numeric = sorted(numeric)
    return f"{numeric[0]}-{numeric[-1]}" if len(numeric) > 1 else str(numeric[0])


if __name__ == "__main__":
    raise SystemExit(main())
