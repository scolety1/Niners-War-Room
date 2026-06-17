from __future__ import annotations

# ruff: noqa: E402
import argparse
import csv
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.mock_draft_filled_input_staging_service import (
    REQUIRED_FILENAMES,
    STAGING_ROOT,
    validate_filled_input_staging,
)
from src.services.mock_draft_pick_order_validator_service import validate_pick_order
from src.services.mock_draft_roster_coverage_validator_service import (
    validate_roster_coverage,
)

DEFAULT_PREFLIGHT_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/preflight_input_gates_20260617"
)
GATE_ROWS_FILE = "mock_draft_preflight_input_gate_rows.csv"
MANIFEST_FILE = "mock_draft_preflight_input_gate_manifest.json"
GATE_ROW_COLUMNS = (
    "gate_name",
    "status",
    "required_for_full_simulation",
    "review_flag",
    "message",
)


@dataclass(frozen=True)
class PreflightInputGateResult:
    review_only: bool
    staging_root: Path
    output_root: Path
    full_simulation_ready: bool
    blocking_reasons: tuple[str, ...]
    gate_rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def build_preflight_input_gates(
    *,
    staging_root: str | Path = STAGING_ROOT,
    output_root: str | Path = DEFAULT_PREFLIGHT_OUTPUT_ROOT,
) -> PreflightInputGateResult:
    staging = Path(staging_root)
    output = Path(output_root)
    gate_rows: list[dict[str, object]] = []
    blockers: list[str] = []

    staging_result = validate_filled_input_staging(staging_root=staging)
    for check in staging_result.checks:
        review_flag = (
            "required_input_missing_or_invalid"
            if check.required_for_full_simulation and check.status != "GREEN"
            else "optional_input_missing_or_review_required"
            if check.status != "GREEN"
            else ""
        )
        gate_rows.append(
            {
                "gate_name": f"staging:{check.file_name}",
                "status": check.status,
                "required_for_full_simulation": check.required_for_full_simulation,
                "review_flag": review_flag,
                "message": check.message,
            }
        )
        if check.file_name in REQUIRED_FILENAMES and check.status != "GREEN":
            blockers.append(f"{check.file_name}:{check.status}")

    roster_path = staging / "post_drop_rosters.csv"
    team_managers_path = staging / "team_managers.csv"
    if roster_path.exists():
        roster_result = validate_roster_coverage(
            roster_path,
            team_managers_path=team_managers_path if team_managers_path.exists() else None,
        )
        for issue in roster_result.issues:
            gate_rows.append(
                {
                    "gate_name": f"roster_coverage:{issue.issue_type}",
                    "status": issue.status,
                    "required_for_full_simulation": True,
                    "review_flag": issue.review_flag,
                    "message": issue.message,
                }
            )
        if not roster_result.full_simulation_ready:
            blockers.append("post_drop_roster_coverage:not_green")

    draft_order_path = staging / "post_drop_draft_order.csv"
    if draft_order_path.exists():
        pick_order_result = validate_pick_order(draft_order_path)
        for issue in pick_order_result.issues:
            gate_rows.append(
                {
                    "gate_name": f"pick_order:{issue.issue_type}",
                    "status": issue.status,
                    "required_for_full_simulation": True,
                    "review_flag": issue.review_flag,
                    "message": issue.message,
                }
            )
        if not pick_order_result.full_simulation_ready:
            blockers.append("post_drop_draft_order:not_green")

    full_ready = not blockers
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "staging_root": str(staging),
        "output_root": str(output),
        "required_files": sorted(REQUIRED_FILENAMES),
        "gate_rows": len(gate_rows),
        "green_gate_rows": sum(1 for row in gate_rows if row["status"] == "GREEN"),
        "yellow_gate_rows": sum(1 for row in gate_rows if row["status"] == "YELLOW"),
        "red_gate_rows": sum(1 for row in gate_rows if row["status"] == "RED"),
        "blocking_reasons": blockers,
        "full_simulation_ready": full_ready,
        "simulation_run": False,
        "real_market_data_imported": False,
        "market_policy": "ADP/market remains behavior-only and cannot become NWR value.",
        "nwr_score_policy": "No numeric NWR score is invented by preflight gates.",
        "promotion_status": "local_preflight_only_not_app_wired_not_promoted",
    }
    return PreflightInputGateResult(
        review_only=True,
        staging_root=staging,
        output_root=output,
        full_simulation_ready=full_ready,
        blocking_reasons=tuple(blockers),
        gate_rows=tuple(gate_rows),
        manifest=manifest,
        artifact_paths={
            "gate_rows": output / GATE_ROWS_FILE,
            "manifest": output / MANIFEST_FILE,
        },
    )


def write_preflight_input_gate_artifacts(
    result: PreflightInputGateResult,
) -> PreflightInputGateResult:
    result.output_root.mkdir(parents=True, exist_ok=True)
    gate_rows_path = result.artifact_paths["gate_rows"]
    manifest_path = result.artifact_paths["manifest"]
    _write_csv(gate_rows_path, GATE_ROW_COLUMNS, result.gate_rows)
    manifest = {
        **result.manifest,
        "artifact_paths": {
            "gate_rows": str(gate_rows_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return PreflightInputGateResult(
        review_only=result.review_only,
        staging_root=result.staging_root,
        output_root=result.output_root,
        full_simulation_ready=result.full_simulation_ready,
        blocking_reasons=result.blocking_reasons,
        gate_rows=result.gate_rows,
        manifest=manifest,
        artifact_paths=result.artifact_paths,
    )


def build_and_write_preflight_input_gates(
    *,
    staging_root: str | Path = STAGING_ROOT,
    output_root: str | Path = DEFAULT_PREFLIGHT_OUTPUT_ROOT,
) -> PreflightInputGateResult:
    return write_preflight_input_gate_artifacts(
        build_preflight_input_gates(staging_root=staging_root, output_root=output_root)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run review-only mock draft preflight input gates."
    )
    parser.add_argument("--staging-root", default=str(STAGING_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_PREFLIGHT_OUTPUT_ROOT))
    args = parser.parse_args(argv)
    result = build_and_write_preflight_input_gates(
        staging_root=args.staging_root,
        output_root=args.output_root,
    )
    print(json.dumps(result.manifest, indent=2, sort_keys=True))
    return 0


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: Sequence[dict[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
