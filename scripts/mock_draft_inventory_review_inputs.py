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

APPROVED_SCAN_DIRS = (
    Path("local_exports/mock_draft/review_inputs"),
    Path("local_exports/mock_draft/combined_simulator_state_20260616"),
    Path("local_exports/mock_draft/mock_draft_run_20260616"),
    Path("local_exports/mock_draft/draft_room_kit_20260616"),
    Path("local_exports/mock_draft/full_pool_visibility_overlay_20260616"),
    Path("local_exports/mock_draft/scenario_variants_20260617"),
    Path("local_exports/mock_draft/scenario_comparison_20260617"),
    Path("local_exports/mock_draft/manual_review_packet_20260617"),
)
DEFAULT_INVENTORY_OUTPUT = Path(
    "local_exports/mock_draft/input_inventory_20260617/mock_draft_input_inventory_manifest.json"
)
REQUIRED_FUTURE_INPUT_MARKERS = {
    "post_drop_rosters": "post_drop_roster_rows.csv",
    "post_drop_draft_order": "post_drop_draft_order_rows.csv",
    "team_managers": "team_manager_rows.csv",
}


@dataclass(frozen=True)
class ReviewInputInventory:
    review_only: bool
    scanned_directories: tuple[str, ...]
    file_rows: tuple[dict[str, object], ...]
    missing_required_inputs: tuple[str, ...]
    manifest: dict[str, object]
    artifact_path: Path


def build_review_input_inventory(
    *,
    repo_root: str | Path = REPO_ROOT,
    output_path: str | Path = DEFAULT_INVENTORY_OUTPUT,
    approved_dirs: Sequence[str | Path] = APPROVED_SCAN_DIRS,
) -> ReviewInputInventory:
    root = Path(repo_root).resolve()
    output = Path(output_path)
    file_rows: list[dict[str, object]] = []
    scanned: list[str] = []
    for relative_dir in approved_dirs:
        directory = _resolve_inside(root, relative_dir)
        scanned.append(str(Path(relative_dir)))
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            file_rows.append(_file_inventory_row(root=root, path=path))
    missing_required = _missing_required_inputs(file_rows)
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "scanned_directories": scanned,
        "file_count": len(file_rows),
        "readable_csv_count": sum(1 for row in file_rows if row.get("row_count") != ""),
        "missing_required_inputs": list(missing_required),
        "full_simulation_blocked": bool(missing_required),
        "simulation_run": False,
        "real_market_data_imported": False,
        "nwr_score_policy": "No NWR score is invented by inventory.",
        "market_policy": "Inventory does not use ADP/market as NWR value.",
        "promotion_status": "local_inventory_only_not_app_wired_not_promoted",
        "files": file_rows,
    }
    return ReviewInputInventory(
        review_only=True,
        scanned_directories=tuple(scanned),
        file_rows=tuple(file_rows),
        missing_required_inputs=missing_required,
        manifest=manifest,
        artifact_path=output,
    )


def write_review_input_inventory(
    inventory: ReviewInputInventory,
    *,
    repo_root: str | Path = REPO_ROOT,
) -> ReviewInputInventory:
    root = Path(repo_root).resolve()
    output = _resolve_inside(root, inventory.artifact_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory.manifest, indent=2, sort_keys=True), encoding="utf-8")
    return ReviewInputInventory(
        review_only=inventory.review_only,
        scanned_directories=inventory.scanned_directories,
        file_rows=inventory.file_rows,
        missing_required_inputs=inventory.missing_required_inputs,
        manifest={**inventory.manifest, "artifact_path": str(inventory.artifact_path)},
        artifact_path=inventory.artifact_path,
    )


def build_and_write_review_input_inventory(
    *,
    repo_root: str | Path = REPO_ROOT,
    output_path: str | Path = DEFAULT_INVENTORY_OUTPUT,
) -> ReviewInputInventory:
    return write_review_input_inventory(
        build_review_input_inventory(repo_root=repo_root, output_path=output_path),
        repo_root=repo_root,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory local mock draft review inputs.")
    parser.add_argument("--output-path", default=str(DEFAULT_INVENTORY_OUTPUT))
    args = parser.parse_args(argv)
    inventory = build_and_write_review_input_inventory(output_path=args.output_path)
    print(json.dumps(inventory.manifest, indent=2, sort_keys=True))
    return 0


def _resolve_inside(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    resolved = candidate if candidate.is_absolute() else root / candidate
    resolved = resolved.resolve()
    if not str(resolved).startswith(str(root)):
        raise ValueError(f"Path escapes mock-draft worktree: {path}")
    return resolved


def _file_inventory_row(*, root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(root)
    row_count: int | str = ""
    columns = ""
    if path.suffix.lower() == ".csv":
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))
            row_count = len(rows)
            columns = "|".join(rows[0].keys()) if rows else ""
        except UnicodeDecodeError:
            row_count = ""
            columns = ""
    return {
        "path": str(relative),
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "row_count": row_count,
        "columns": columns,
    }


def _missing_required_inputs(file_rows: Sequence[dict[str, object]]) -> tuple[str, ...]:
    paths = {str(row["path"]).replace("\\", "/") for row in file_rows}
    missing = []
    for group, marker in REQUIRED_FUTURE_INPUT_MARKERS.items():
        if not any(path.endswith(marker) for path in paths):
            missing.append(group)
    return tuple(missing)


if __name__ == "__main__":
    raise SystemExit(main())
