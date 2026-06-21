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

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse")
USER_AGENT = "NWR-nflverse-Scheduled-Puller-V0"
DEFAULT_DATASETS = (
    "weekly_stats",
    "season_stats",
    "rosters",
    "weekly_rosters",
    "snap_counts",
    "participation",
    "opportunity",
)
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
    loader_kwargs: dict[str, Any] | None = None


@dataclass(frozen=True)
class DatasetResult:
    name: str
    function_name: str
    file_name: str
    status: str
    row_count: int
    column_count: int
    byte_count: int
    sha256: str
    field_names: list[str]
    field_roles: dict[str, list[str]]
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


DATASET_SPECS = {
    "weekly_stats": DatasetSpec(
        name="weekly_stats",
        function_names=("import_weekly_data", "load_player_stats"),
        file_name="weekly_stats.csv",
    ),
    "season_stats": DatasetSpec(
        name="season_stats",
        function_names=("import_seasonal_data", "load_player_stats", "load_seasonal_data"),
        file_name="season_stats.csv",
        loader_kwargs={"summary_level": "reg"},
    ),
    "rosters": DatasetSpec(
        name="rosters",
        function_names=("import_rosters", "load_rosters"),
        file_name="rosters.csv",
    ),
    "weekly_rosters": DatasetSpec(
        name="weekly_rosters",
        function_names=("import_weekly_rosters", "load_rosters_weekly", "load_weekly_rosters"),
        file_name="weekly_rosters.csv",
    ),
    "snap_counts": DatasetSpec(
        name="snap_counts",
        function_names=("import_snap_counts", "load_snap_counts"),
        file_name="snap_counts.csv",
    ),
    "participation": DatasetSpec(
        name="participation",
        function_names=("import_participation", "load_participation"),
        file_name="participation.csv",
    ),
    "opportunity": DatasetSpec(
        name="opportunity",
        function_names=(
            "import_player_stats",
            "load_ff_opportunity",
            "load_opportunity",
            "import_opportunity",
        ),
        file_name="opportunity.csv",
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
        choices=tuple(DATASET_SPECS),
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
        )

    output_path = snapshot_dir / spec.file_name
    try:
        frame = _call_loader(loader, seasons, spec.loader_kwargs or {})
        rows, fields = _frame_to_rows(frame)
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
            quarantined_fields=quarantined,
            matched_players=matched,
            identity_matches=identity_matches,
            missing_sample_players=missing,
            warning=_dataset_warning(spec.name, quarantined),
        )
    except Exception as exc:
        output_path.write_text("", encoding="utf-8")
        return DatasetResult(
            name=spec.name,
            function_name=function_name,
            file_name=spec.file_name,
            status="error" if spec.required else "warning",
            row_count=0,
            column_count=0,
            byte_count=0,
            sha256=_sha256(b""),
            field_names=[],
            field_roles={},
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
    attempts = (
        lambda: loader(seasons, **kwargs),
        lambda: loader(seasons),
        lambda: loader(seasons=seasons, **kwargs),
        lambda: loader(seasons=seasons),
        lambda: loader(years=seasons, **kwargs),
        lambda: loader(years=seasons),
    )
    last_error: TypeError | None = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


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


def _skipped_dataset_result(spec: DatasetSpec, reason: str) -> DatasetResult:
    return DatasetResult(
        name=spec.name,
        function_name="",
        file_name=spec.file_name,
        status="skipped",
        row_count=0,
        column_count=0,
        byte_count=0,
        sha256=_sha256(b""),
        field_names=[],
        field_roles={},
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
                "function_name": result.function_name,
                "file_name": result.file_name,
                "status": result.status,
                "row_count": result.row_count,
                "column_count": result.column_count,
                "byte_count": result.byte_count,
                "sha256": result.sha256,
                "field_names": result.field_names,
                "field_name_summary": result.field_names[:60],
                "field_roles": result.field_roles,
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


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _norm(value: Any) -> str:
    return "".join(char for char in str(value).lower() if char.isalnum())


if __name__ == "__main__":
    raise SystemExit(main())
