from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RAW_CACHE_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache")

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"

CORE_SOURCE_REQUIRED_FIELDS: dict[str, set[str]] = {
    "snap_counts": {"season", "week", "player", "position", "team", "offense_snaps"},
    "player_stats": {"season", "week", "player_id", "position"},
    "pbp": {"season", "week", "posteam", "yardline_100"},
}

CORE_FIELD_POLICY: dict[str, dict[str, str]] = {
    "season": {"source_family": "all", "field_type": "TRUE_FACTUAL_FIELD", "grain": "player_week"},
    "week": {"source_family": "all", "field_type": "TRUE_FACTUAL_FIELD", "grain": "player_week"},
    "game_id": {"source_family": "all", "field_type": "TRUE_FACTUAL_FIELD", "grain": "player_game"},
    "player_id": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "gsis_id": {"source_family": "all", "field_type": "TRUE_FACTUAL_FIELD", "grain": "player_week"},
    "player": {
        "source_family": "snap_counts",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_game",
    },
    "player_name": {
        "source_family": "all",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "position": {
        "source_family": "all",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "team": {"source_family": "all", "field_type": "TRUE_FACTUAL_FIELD", "grain": "player_week"},
    "recent_team": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "posteam": {"source_family": "pbp", "field_type": "TRUE_FACTUAL_FIELD", "grain": "play"},
    "offense_snaps": {
        "source_family": "snap_counts",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_game",
    },
    "offense_pct": {
        "source_family": "snap_counts",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_game",
    },
    "targets": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "carries": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "receptions": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "rushing_yards": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "receiving_yards": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "receiving_air_yards": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "receiving_yards_after_catch": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "rushing_first_downs": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "receiving_first_downs": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "passing_first_downs": {
        "source_family": "player_stats",
        "field_type": "TRUE_FACTUAL_FIELD",
        "grain": "player_week",
    },
    "yardline_100": {"source_family": "pbp", "field_type": "TRUE_FACTUAL_FIELD", "grain": "play"},
}

BLOCKED_FIELD_PATTERNS = (
    "adp",
    "analyst",
    "betting",
    "dfs",
    "fantasy_points",
    "fantasy_value",
    "market",
    "projection",
    "rank",
    "salary",
    "score",
    "start_sit",
    "tier",
    "trade_value",
    "value",
)


@dataclass(frozen=True)
class NflUsageSourceLoadResult:
    source_family: str
    loader_name: str
    status: str
    rows: tuple[dict[str, Any], ...]
    field_names: tuple[str, ...]
    warnings: tuple[str, ...]
    raw_cache_root: Path = RAW_CACHE_ROOT


def nflreadpy_available() -> bool:
    return importlib.util.find_spec("nflreadpy") is not None


def dependency_status_rows() -> list[dict[str, str]]:
    return [
        {
            "package": "nflreadpy",
            "available": "yes" if nflreadpy_available() else "no",
            "dependency_policy": "defer until project-approved dependency workflow",
            "raw_cache_root": str(RAW_CACHE_ROOT),
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
    ]


def load_core_source(
    source_family: str,
    *,
    seasons: list[int] | None = None,
    loader_module: Any | None = None,
    skip_live: bool = True,
) -> NflUsageSourceLoadResult:
    if source_family not in CORE_SOURCE_REQUIRED_FIELDS:
        raise ValueError(f"unsupported source_family: {source_family}")
    if skip_live:
        return _closed_result(source_family, "DRY_RUN_BLOCKED_NO_LIVE_PULL")

    module = loader_module
    if module is None:
        if not nflreadpy_available():
            return _closed_result(source_family, "BLOCKED_NFLREADPY_NOT_INSTALLED")
        import nflreadpy as module  # type: ignore[import-not-found]

    loader_name = _loader_name(source_family)
    loader = getattr(module, loader_name, None)
    if not callable(loader):
        return _closed_result(source_family, f"BLOCKED_LOADER_MISSING:{loader_name}")

    frame = loader(seasons=seasons) if seasons else loader()
    rows = _frame_to_rows(frame)
    fields = _field_names(rows)
    blocked = blocked_fields(fields)
    if blocked:
        return NflUsageSourceLoadResult(
            source_family=source_family,
            loader_name=loader_name,
            status="QUARANTINED_BLOCKED_FIELDS",
            rows=(),
            field_names=tuple(fields),
            warnings=(f"blocked_fields={';'.join(blocked)}",),
        )
    return NflUsageSourceLoadResult(
        source_family=source_family,
        loader_name=loader_name,
        status="AVAILABLE_REVIEW_ONLY",
        rows=tuple(rows),
        field_names=tuple(fields),
        warnings=(),
    )


def build_core_field_inventory_rows(
    field_names_by_source: dict[str, list[str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_family, fields in sorted(field_names_by_source.items()):
        for field in sorted(fields):
            policy = CORE_FIELD_POLICY.get(field, {})
            status = "BLOCKED" if blocked_fields([field]) else "AVAILABLE"
            if not policy:
                status = "MISSING" if status != "BLOCKED" else status
            rows.append(
                {
                    "source_family": source_family,
                    "field_name": field,
                    "field_type": policy.get("field_type", "NOT_EVALUATED"),
                    "grain": policy.get("grain", "NOT_EVALUATED"),
                    "field_status": status,
                    "model_input_allowed": MODEL_INPUT_ALLOWED,
                    "app_wiring_allowed": APP_WIRING_ALLOWED,
                    "notes": "review-only V0 inventory",
                }
            )
    return rows


def build_core_coverage_summary_rows(
    results: list[NflUsageSourceLoadResult],
) -> list[dict[str, str]]:
    return [
        {
            "source_family": result.source_family,
            "loader_name": result.loader_name,
            "status": result.status,
            "row_count": str(len(result.rows)),
            "field_count": str(len(result.field_names)),
            "raw_cache_root": str(result.raw_cache_root),
            "raw_data_tracked": "no",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "warnings": "|".join(result.warnings),
        }
        for result in results
    ]


def build_core_validation_report_rows(
    results: list[NflUsageSourceLoadResult],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for result in results:
        missing = sorted(
            CORE_SOURCE_REQUIRED_FIELDS[result.source_family] - set(result.field_names)
        )
        status = "GREEN" if result.status == "AVAILABLE_REVIEW_ONLY" and not missing else "YELLOW"
        if "QUARANTINED" in result.status:
            status = "RED"
        rows.append(
            {
                "source_family": result.source_family,
                "validation_status": status,
                "missing_required_fields": ";".join(missing),
                "blocked_fields": ";".join(blocked_fields(result.field_names)),
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": result.status,
            }
        )
    return rows


def blocked_fields(field_names: list[str] | tuple[str, ...]) -> list[str]:
    blocked: list[str] = []
    for field in field_names:
        lower = field.lower()
        if any(pattern in lower for pattern in BLOCKED_FIELD_PATTERNS):
            blocked.append(field)
    return sorted(set(blocked))


def _closed_result(source_family: str, status: str) -> NflUsageSourceLoadResult:
    return NflUsageSourceLoadResult(
        source_family=source_family,
        loader_name=_loader_name(source_family),
        status=status,
        rows=(),
        field_names=(),
        warnings=(status,),
    )


def _loader_name(source_family: str) -> str:
    return {
        "snap_counts": "load_snap_counts",
        "player_stats": "load_player_stats",
        "pbp": "load_pbp",
    }[source_family]


def _frame_to_rows(frame: Any) -> list[dict[str, Any]]:
    if hasattr(frame, "to_dicts"):
        return [dict(row) for row in frame.to_dicts()]
    if hasattr(frame, "to_pandas"):
        return _frame_to_rows(frame.to_pandas())
    if hasattr(frame, "to_dict"):
        return [dict(row) for row in frame.to_dict(orient="records")]
    if isinstance(frame, list):
        return [dict(row) for row in frame]
    raise TypeError(f"unsupported frame type: {type(frame).__name__}")


def _field_names(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            field = str(key)
            if field not in seen:
                fields.append(field)
                seen.add(field)
    return fields
