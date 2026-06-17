from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from src.services.mock_draft_input_schema_validator_service import SCHEMA_COLUMNS

STAGING_ROOT = Path("local_exports/mock_draft/user_supplied_inputs_20260617")

FILENAME_TO_SCHEMA = {
    "post_drop_rosters.csv": "post_drop_rosters",
    "post_drop_draft_order.csv": "draft_order",
    "team_managers.csv": "team_managers",
    "dropped_veterans.csv": "dropped_veterans",
    "behavior_only_adp_market.csv": "market_timing",
    "nwr_veteran_value_guidance.csv": "nwr_veteran_guidance",
}
REQUIRED_FILENAMES = frozenset(
    {"post_drop_rosters.csv", "post_drop_draft_order.csv", "team_managers.csv"}
)
OPTIONAL_FILENAMES = frozenset(FILENAME_TO_SCHEMA) - REQUIRED_FILENAMES


@dataclass(frozen=True)
class StagingFileCheck:
    file_name: str
    schema_group: str
    required_for_full_simulation: bool
    status: str
    file_present: bool
    row_count: int
    missing_columns: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class StagingValidationResult:
    review_only: bool
    staging_root: Path
    full_simulation_ready: bool
    checks: tuple[StagingFileCheck, ...]
    summary: dict[str, object]


def validate_filled_input_staging(
    *,
    staging_root: str | Path = STAGING_ROOT,
    files_by_name: Mapping[str, str | Path] | None = None,
) -> StagingValidationResult:
    root = Path(staging_root)
    checks: list[StagingFileCheck] = []
    for file_name, schema_group in FILENAME_TO_SCHEMA.items():
        required = file_name in REQUIRED_FILENAMES
        path = (
            Path(files_by_name[file_name])
            if files_by_name and file_name in files_by_name
            else root / file_name
        )
        if not path.exists():
            checks.append(
                StagingFileCheck(
                    file_name=file_name,
                    schema_group=schema_group,
                    required_for_full_simulation=required,
                    status="YELLOW",
                    file_present=False,
                    row_count=0,
                    missing_columns=tuple(sorted(SCHEMA_COLUMNS[schema_group])),
                    message=(
                        "Missing required staged input; full simulation remains blocked."
                        if required
                        else "Optional staged input missing; review fallback remains allowed."
                    ),
                )
            )
            continue
        rows = _read_csv(path)
        columns = set(rows[0]) if rows else set()
        missing = tuple(sorted(SCHEMA_COLUMNS[schema_group] - columns))
        checks.append(
            StagingFileCheck(
                file_name=file_name,
                schema_group=schema_group,
                required_for_full_simulation=required,
                status="RED" if missing else "GREEN",
                file_present=True,
                row_count=len(rows),
                missing_columns=missing,
                message=(
                    "Missing required columns."
                    if missing
                    else "Staged input header is valid."
                ),
            )
        )
    full_ready = all(
        check.status == "GREEN"
        for check in checks
        if check.required_for_full_simulation
    )
    return StagingValidationResult(
        review_only=True,
        staging_root=root,
        full_simulation_ready=full_ready,
        checks=tuple(checks),
        summary={
            "review_only": True,
            "staging_root": str(root),
            "required_files": sorted(REQUIRED_FILENAMES),
            "optional_files": sorted(OPTIONAL_FILENAMES),
            "full_simulation_ready": full_ready,
            "green": sum(1 for check in checks if check.status == "GREEN"),
            "yellow": sum(1 for check in checks if check.status == "YELLOW"),
            "red": sum(1 for check in checks if check.status == "RED"),
            "market_policy": "ADP/market files are behavior-only and not NWR value.",
            "nwr_score_policy": "No numeric NWR score is invented by staging checks.",
        },
    )


def staging_checks_as_dicts(result: StagingValidationResult) -> list[dict[str, object]]:
    return [
        {
            "file_name": check.file_name,
            "schema_group": check.schema_group,
            "required_for_full_simulation": check.required_for_full_simulation,
            "status": check.status,
            "file_present": check.file_present,
            "row_count": check.row_count,
            "missing_columns": "|".join(check.missing_columns),
            "message": check.message,
        }
        for check in result.checks
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
