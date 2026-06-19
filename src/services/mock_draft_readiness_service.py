from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.mock_draft_input_contract import (
    READINESS_GREEN,
    READINESS_RED,
    READINESS_YELLOW,
    default_real_input_paths,
    fixture_input_paths,
    validate_input_contract,
)
from src.services.mock_draft_input_manifest import validate_input_manifest
from src.services.mock_draft_market_separation_contract import validate_market_separation


@dataclass(frozen=True)
class ReadinessReport:
    readiness: str
    real_input_readiness: str
    fixture_readiness: str
    manifest_readiness: str
    market_separation_readiness: str
    missing_real_inputs: tuple[str, ...]
    schema_violations: tuple[str, ...]
    no_simulations_run: bool = True
    no_files_written: bool = True


def build_mock_draft_readiness_report(
    *,
    repo_root: str | Path = ".",
    fixture_root: str | Path = "tests/fixtures/mock_draft_inputs",
    manifest_path: str | Path = "local_exports/mock_draft/manual_input_manifest.local.json",
) -> ReadinessReport:
    root = Path(repo_root)
    real_report = validate_input_contract(
        default_real_input_paths(),
        mode="real",
        repo_root=root,
    )
    fixture_report = validate_input_contract(
        fixture_input_paths(fixture_root),
        mode="fixture",
        repo_root=root,
    )
    manifest_report = validate_input_manifest(manifest_path, repo_root=root)
    market_report = validate_market_separation(
        _read_csv(root / Path(fixture_root) / "market_context_fixture.csv"),
        _read_csv(root / Path(fixture_root) / "nwr_private_values_fixture.csv"),
    )
    missing_real = tuple(row.label for row in real_report.rows if not row.present)
    violations = tuple(
        f"{row.label}: {' | '.join(row.errors)}"
        for row in fixture_report.rows
        if row.errors
    )
    readiness = _aggregate(
        (
            real_report.readiness,
            fixture_report.readiness,
            market_report.readiness,
        )
    )
    return ReadinessReport(
        readiness=readiness,
        real_input_readiness=real_report.readiness,
        fixture_readiness=fixture_report.readiness,
        manifest_readiness=manifest_report.readiness,
        market_separation_readiness=market_report.readiness,
        missing_real_inputs=missing_real,
        schema_violations=violations,
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _aggregate(colors: tuple[str, ...]) -> str:
    if READINESS_RED in colors:
        return READINESS_RED
    if READINESS_YELLOW in colors:
        return READINESS_YELLOW
    return READINESS_GREEN
