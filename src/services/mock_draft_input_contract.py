from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

READINESS_GREEN = "GREEN"
READINESS_YELLOW = "YELLOW"
READINESS_RED = "RED"

FROZEN_ROOKIE_INPUT_PATH = Path(
    "local_exports/rookie_framework/final_post_fill_runway_20260616/"
    "rookie_2026_mock_draft_input_20260616.csv"
)

NWR_PRIVATE_VALUE_COLUMNS = frozenset(
    {
        "nwr_private_value",
        "nwr_quality_score",
        "nwr_value",
        "private_value",
        "private_score",
        "war_score",
    }
)
MARKET_CONTEXT_COLUMNS = frozenset(
    {
        "adp",
        "market_adp",
        "market_adp_pick",
        "market_rank",
        "market_value",
        "opponent_likelihood_score",
        "opponent_likelihood_signal",
        "availability_curve",
        "pick_timing_score",
    }
)
GLOBAL_BLOCKED_COLUMNS = frozenset(
    {
        "hidden_sort_key",
        "production_rank",
        "production_rank_override",
        "outcome_probability",
        "outcome_band",
        "probability_band",
        "app_route",
        "streamlit_page",
        "promoted_artifact",
    }
)


@dataclass(frozen=True)
class InputSchema:
    key: str
    label: str
    required_columns: frozenset[str]
    required_for_simulation: bool = True
    real_missing_status: str = READINESS_YELLOW
    fixture_missing_status: str = READINESS_RED


@dataclass(frozen=True)
class InputContractRow:
    key: str
    label: str
    readiness: str
    path: str
    present: bool
    row_count: int
    required_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    blocked_columns: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class InputContractReport:
    review_only: bool
    no_simulations_run: bool
    market_policy: str
    rows: tuple[InputContractRow, ...]
    readiness: str


INPUT_SCHEMAS: dict[str, InputSchema] = {
    "frozen_rookie_input": InputSchema(
        key="frozen_rookie_input",
        label="Frozen rookie input",
        required_columns=frozenset(
            {
                "asset_id",
                "player",
                "position",
                "asset_type",
                "nwr_private_value",
                "source_status",
            }
        ),
    ),
    "veteran_pool": InputSchema(
        key="veteran_pool",
        label="Dropped or available veteran pool",
        required_columns=frozenset(
            {
                "asset_id",
                "player",
                "position",
                "nfl_team",
                "availability_source",
                "review_status",
            }
        ),
    ),
    "pick_order": InputSchema(
        key="pick_order",
        label="Final pick order",
        required_columns=frozenset(
            {
                "overall_pick",
                "round",
                "round_pick",
                "pick_label",
                "current_owner",
                "original_owner",
            }
        ),
    ),
    "my_picks": InputSchema(
        key="my_picks",
        label="NWR/my pick numbers",
        required_columns=frozenset({"overall_pick", "pick_label", "owner", "is_nwr_pick"}),
    ),
    "rosters": InputSchema(
        key="rosters",
        label="Current rosters and keepers",
        required_columns=frozenset(
            {"team_id", "team_name", "player", "position", "keeper_status"}
        ),
    ),
    "team_needs": InputSchema(
        key="team_needs",
        label="Team needs and opponent tendencies",
        required_columns=frozenset(
            {"team_id", "team_name", "position", "need_weight", "tendency_note"}
        ),
    ),
    "nwr_private_values": InputSchema(
        key="nwr_private_values",
        label="NWR private value source",
        required_columns=frozenset(
            {
                "asset_id",
                "player",
                "position",
                "nwr_private_value",
                "value_source",
                "separation_note",
            }
        ),
    ),
    "market_context": InputSchema(
        key="market_context",
        label="ADP/market opponent behavior source",
        required_columns=frozenset(
            {
                "asset_id",
                "player",
                "position",
                "market_adp_pick",
                "market_source",
                "opponent_likelihood_signal",
                "allowed_use",
                "separation_note",
            }
        ),
    ),
}


def default_real_input_paths() -> dict[str, Path | None]:
    return {
        "frozen_rookie_input": FROZEN_ROOKIE_INPUT_PATH,
        "veteran_pool": None,
        "pick_order": None,
        "my_picks": None,
        "rosters": None,
        "team_needs": None,
        "nwr_private_values": None,
        "market_context": None,
    }


def fixture_input_paths(root: str | Path) -> dict[str, Path]:
    root_path = Path(root)
    return {
        "frozen_rookie_input": root_path / "rookie_input_fixture.csv",
        "veteran_pool": root_path / "veteran_pool_fixture.csv",
        "pick_order": root_path / "pick_order_fixture.csv",
        "my_picks": root_path / "my_picks_fixture.csv",
        "rosters": root_path / "rosters_fixture.csv",
        "team_needs": root_path / "team_needs_fixture.csv",
        "nwr_private_values": root_path / "nwr_private_values_fixture.csv",
        "market_context": root_path / "market_context_fixture.csv",
    }


def validate_input_contract(
    paths_by_key: Mapping[str, str | Path | None],
    *,
    mode: str,
    repo_root: str | Path = ".",
) -> InputContractReport:
    root = Path(repo_root)
    rows = tuple(
        _validate_one_schema(
            schema=schema,
            path_value=paths_by_key.get(schema.key),
            mode=mode,
            repo_root=root,
        )
        for schema in INPUT_SCHEMAS.values()
    )
    return InputContractReport(
        review_only=True,
        no_simulations_run=True,
        market_policy=(
            "ADP/market context is opponent behavior, availability, and pick timing "
            "only; it is never NWR private value."
        ),
        rows=rows,
        readiness=_overall_readiness(rows),
    )


def report_rows_as_dicts(report: InputContractReport) -> list[dict[str, object]]:
    return [
        {
            "key": row.key,
            "label": row.label,
            "readiness": row.readiness,
            "path": row.path,
            "present": row.present,
            "row_count": row.row_count,
            "missing_columns": "|".join(row.missing_columns),
            "blocked_columns": "|".join(row.blocked_columns),
            "warnings": "|".join(row.warnings),
            "errors": "|".join(row.errors),
        }
        for row in report.rows
    ]


def _validate_one_schema(
    *,
    schema: InputSchema,
    path_value: str | Path | None,
    mode: str,
    repo_root: Path,
) -> InputContractRow:
    missing_status = (
        schema.fixture_missing_status if mode == "fixture" else schema.real_missing_status
    )
    if path_value in (None, ""):
        return _missing_row(schema, missing_status, "Path is not configured.")

    path = Path(path_value)
    display_path = str(path)
    full_path = path if path.is_absolute() else repo_root / path
    if not full_path.exists():
        return _missing_row(schema, missing_status, f"File not found: {display_path}")

    try:
        headers, row_count = _csv_headers_and_count(full_path)
    except OSError as exc:
        return InputContractRow(
            key=schema.key,
            label=schema.label,
            readiness=READINESS_RED,
            path=display_path,
            present=True,
            row_count=0,
            required_columns=tuple(sorted(schema.required_columns)),
            missing_columns=(),
            blocked_columns=(),
            warnings=(),
            errors=(f"Could not read CSV: {exc}",),
        )

    missing_columns = tuple(sorted(schema.required_columns - headers))
    blocked_columns = _blocked_columns_for_schema(schema.key, headers)
    errors: list[str] = []
    warnings: list[str] = []
    if missing_columns:
        errors.append("Required columns are missing.")
    if blocked_columns:
        errors.append("Blocked columns violate source separation.")
    if row_count == 0:
        warnings.append("CSV contains headers but no data rows.")

    return InputContractRow(
        key=schema.key,
        label=schema.label,
        readiness=READINESS_RED if errors else READINESS_GREEN,
        path=display_path,
        present=True,
        row_count=row_count,
        required_columns=tuple(sorted(schema.required_columns)),
        missing_columns=missing_columns,
        blocked_columns=blocked_columns,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _missing_row(
    schema: InputSchema,
    readiness: str,
    message: str,
) -> InputContractRow:
    warnings = (message,) if readiness == READINESS_YELLOW else ()
    errors = (message,) if readiness == READINESS_RED else ()
    return InputContractRow(
        key=schema.key,
        label=schema.label,
        readiness=readiness,
        path="",
        present=False,
        row_count=0,
        required_columns=tuple(sorted(schema.required_columns)),
        missing_columns=tuple(sorted(schema.required_columns)),
        blocked_columns=(),
        warnings=warnings,
        errors=errors,
    )


def _csv_headers_and_count(path: Path) -> tuple[frozenset[str], int]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = frozenset(reader.fieldnames or ())
        row_count = sum(1 for _ in reader)
    return headers, row_count


def _blocked_columns_for_schema(schema_key: str, headers: frozenset[str]) -> tuple[str, ...]:
    blocked = set(headers & GLOBAL_BLOCKED_COLUMNS)
    if schema_key == "market_context":
        blocked.update(headers & NWR_PRIVATE_VALUE_COLUMNS)
    if schema_key == "nwr_private_values":
        blocked.update(headers & MARKET_CONTEXT_COLUMNS)
    return tuple(sorted(blocked))


def _overall_readiness(rows: Sequence[InputContractRow]) -> str:
    if any(row.readiness == READINESS_RED for row in rows):
        return READINESS_RED
    if any(row.readiness == READINESS_YELLOW for row in rows):
        return READINESS_YELLOW
    return READINESS_GREEN
