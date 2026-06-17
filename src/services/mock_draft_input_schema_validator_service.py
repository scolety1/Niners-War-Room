from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REQUIRED_GROUPS = frozenset(
    {
        "post_drop_rosters",
        "draft_order",
        "team_managers",
        "dropped_veterans",
        "available_pool",
    }
)
OPTIONAL_GROUPS = frozenset({"market_timing", "nwr_veteran_guidance"})

SCHEMA_COLUMNS: dict[str, frozenset[str]] = {
    "post_drop_rosters": frozenset(
        {
            "team_name",
            "manager",
            "roster_slot",
            "player_name",
            "position",
            "nfl_team",
            "input_status",
        }
    ),
    "draft_order": frozenset(
        {
            "season",
            "overall_pick",
            "round",
            "round_pick",
            "pick_label",
            "current_owner",
            "original_owner",
            "manager",
            "is_niners_pick",
            "source_status",
        }
    ),
    "team_managers": frozenset({"team_name", "manager", "team_key"}),
    "dropped_veterans": frozenset({"player", "position", "source_label", "review_flags"}),
    "available_pool": frozenset(
        {"asset_id", "player", "position", "source_label", "value_status", "review_flags"}
    ),
    "market_timing": frozenset(
        {
            "asset_id",
            "player",
            "position",
            "source_name",
            "source_type",
            "source_timestamp",
            "market_adp",
            "sample_size",
            "identity_match_method",
            "review_flags",
        }
    ),
    "nwr_veteran_guidance": frozenset(
        {
            "asset_id",
            "player",
            "position",
            "source_label",
            "nwr_value_status",
            "nwr_guidance_label",
            "nwr_warning",
            "draft_action",
            "source_status",
        }
    ),
}

DISALLOWED_COLUMNS = frozenset(
    {
        "nwr_quality_score",
        "market_derived_nwr_score",
        "production_rank_override",
        "hidden_sort_key",
        "outcome_probability",
        "outcome_band",
        "streamlit_page",
        "app_route",
        "promoted_artifact",
    }
)
MARKET_BLOCKED_VALUE_COLUMNS = frozenset(
    {
        "stats_model_value",
        "model_value",
        "draft_value",
        "nwr_draft_value",
        "nwr_dynasty_score",
        "nwr_quality_score",
        "quality_score",
        "war_score",
    }
)


@dataclass(frozen=True)
class SchemaValidationRow:
    group_name: str
    status: str
    required_for_full_simulation: bool
    file_present: bool
    rows: int
    missing_columns: tuple[str, ...]
    disallowed_columns: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class SchemaValidationResult:
    review_only: bool
    phase1_can_proceed: bool
    full_simulation_blocked: bool
    rows: tuple[SchemaValidationRow, ...]
    summary: dict[str, object]


def validate_mock_draft_input_schemas(
    files_by_group: Mapping[str, str | Path | None],
) -> SchemaValidationResult:
    rows: list[SchemaValidationRow] = []
    for group_name in sorted(REQUIRED_GROUPS | OPTIONAL_GROUPS):
        path_value = files_by_group.get(group_name)
        required = group_name in REQUIRED_GROUPS
        if path_value in (None, ""):
            status = "RED" if required else "YELLOW"
            rows.append(
                SchemaValidationRow(
                    group_name=group_name,
                    status=status,
                    required_for_full_simulation=required,
                    file_present=False,
                    rows=0,
                    missing_columns=tuple(sorted(SCHEMA_COLUMNS[group_name])),
                    disallowed_columns=(),
                    message=(
                        "Missing required full-simulation input."
                        if required
                        else "Optional input missing; keep behavior fallback/review-required."
                    ),
                )
            )
            continue
        path = Path(path_value)
        if not path.exists():
            status = "RED" if required else "YELLOW"
            rows.append(
                SchemaValidationRow(
                    group_name=group_name,
                    status=status,
                    required_for_full_simulation=required,
                    file_present=False,
                    rows=0,
                    missing_columns=tuple(sorted(SCHEMA_COLUMNS[group_name])),
                    disallowed_columns=(),
                    message=f"File not found: {path}",
                )
            )
            continue
        csv_rows = _read_csv(path)
        columns = set(csv_rows[0].keys()) if csv_rows else set()
        required_columns = SCHEMA_COLUMNS[group_name]
        missing = tuple(sorted(required_columns - columns))
        disallowed = _disallowed_columns(group_name, columns)
        if disallowed:
            status = "RED"
            message = "Disallowed contamination columns found."
        elif missing:
            status = "RED" if required else "YELLOW"
            message = "Required schema columns missing."
        else:
            status = "GREEN"
            message = "Schema columns valid for review-only intake."
        rows.append(
            SchemaValidationRow(
                group_name=group_name,
                status=status,
                required_for_full_simulation=required,
                file_present=True,
                rows=len(csv_rows),
                missing_columns=missing,
                disallowed_columns=disallowed,
                message=message,
            )
        )
    full_blocked = any(
        row.status == "RED" and row.required_for_full_simulation for row in rows
    )
    summary = {
        "review_only": True,
        "phase1_can_proceed": True,
        "full_simulation_blocked": full_blocked,
        "green_rows": sum(1 for row in rows if row.status == "GREEN"),
        "yellow_rows": sum(1 for row in rows if row.status == "YELLOW"),
        "red_rows": sum(1 for row in rows if row.status == "RED"),
        "nwr_score_policy": "No numeric NWR score is invented by schema validation.",
        "market_policy": "Market timing schema is behavior-only and cannot carry NWR value fields.",
    }
    return SchemaValidationResult(
        review_only=True,
        phase1_can_proceed=True,
        full_simulation_blocked=full_blocked,
        rows=tuple(rows),
        summary=summary,
    )


def validation_rows_as_dicts(
    result: SchemaValidationResult,
) -> list[dict[str, object]]:
    return [
        {
            "group_name": row.group_name,
            "status": row.status,
            "required_for_full_simulation": row.required_for_full_simulation,
            "file_present": row.file_present,
            "rows": row.rows,
            "missing_columns": "|".join(row.missing_columns),
            "disallowed_columns": "|".join(row.disallowed_columns),
            "message": row.message,
        }
        for row in result.rows
    ]


def _disallowed_columns(group_name: str, columns: set[str]) -> tuple[str, ...]:
    blocked = set(DISALLOWED_COLUMNS) & columns
    if group_name == "market_timing":
        blocked |= set(MARKET_BLOCKED_VALUE_COLUMNS) & columns
    return tuple(sorted(blocked))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
