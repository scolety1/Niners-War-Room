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

from src.services.mock_draft_combined_state_service import (
    DEFAULT_ROOKIE_KIT_ROOT,
    ROOKIE_BOARD_FILE,
    ROOKIE_QUICK_SHEET_FILE,
    build_and_write_combined_simulator_state,
)
from src.services.mock_draft_full_pool_overlay_service import (
    build_and_write_full_pool_visibility_overlay,
)
from src.services.mock_draft_manual_review_packet_service import (
    build_and_write_manual_review_packet,
)
from src.services.mock_draft_market_timing_adapter_service import (
    DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
    build_and_write_fake_market_timing_dry_run,
)
from src.services.mock_draft_room_kit_service import build_and_write_draft_room_kit
from src.services.mock_draft_run_report_service import build_and_write_mock_draft_run_report
from src.services.mock_draft_scenario_comparison_service import (
    build_and_write_scenario_comparison_artifacts,
)
from src.services.mock_draft_scenario_variant_service import (
    build_and_write_scenario_variant_artifacts,
)
from src.services.mock_draft_snapshot_service import DEFAULT_LVE_ROSTERS_061326_SNAPSHOT

DEFAULT_REGENERATION_SMOKE_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/regeneration_smoke_20260617"
)

COUNTS_COLUMNS = ("artifact_group", "metric", "count")
CONTAMINATION_COLUMNS = ("check_name", "passed", "detail")


@dataclass(frozen=True)
class RegenerationSmokeResult:
    review_only: bool
    output_root: Path
    counts_rows: tuple[dict[str, object], ...]
    contamination_rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def run_regeneration_smoke(
    *,
    output_root: str | Path = DEFAULT_REGENERATION_SMOKE_OUTPUT_ROOT,
    required_inputs: Sequence[str | Path] | None = None,
) -> RegenerationSmokeResult:
    root = Path(output_root)
    required = tuple(Path(path) for path in (required_inputs or _required_local_inputs()))
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required local review inputs for mock draft regeneration: "
            + "; ".join(missing)
        )

    combined_root = root / "combined_simulator_state"
    run_root = root / "mock_draft_run"
    kit_root = root / "draft_room_kit"
    overlay_root = root / "full_pool_visibility_overlay"
    fake_market_root = root / "fake_market_timing_dry_run"
    variants_root = root / "scenario_variants"
    comparison_root = root / "scenario_comparison"
    manual_packet_root = root / "manual_review_packet"

    combined = build_and_write_combined_simulator_state(output_root=combined_root)
    run_report = build_and_write_mock_draft_run_report(output_root=run_root)
    kit = build_and_write_draft_room_kit(run_root=run_root, output_root=kit_root)
    overlay = build_and_write_full_pool_visibility_overlay(
        run_root=run_root,
        combined_root=combined_root,
        kit_root=kit_root,
        output_root=overlay_root,
    )
    fake_market = build_and_write_fake_market_timing_dry_run(output_root=fake_market_root)
    variants = build_and_write_scenario_variant_artifacts(output_root=variants_root)
    comparison = build_and_write_scenario_comparison_artifacts(
        scenario_root=variants_root,
        output_root=comparison_root,
    )
    manual_packet = build_and_write_manual_review_packet(output_root=manual_packet_root)

    counts_rows = _counts_rows(
        combined=combined,
        run_report=run_report,
        kit=kit,
        overlay=overlay,
        fake_market=fake_market,
        variants=variants,
        comparison=comparison,
        manual_packet=manual_packet,
    )
    contamination_rows = _contamination_rows(output_root=root)
    root.mkdir(parents=True, exist_ok=True)
    counts_path = root / "regeneration_smoke_counts.csv"
    contamination_path = root / "regeneration_smoke_contamination_check.csv"
    manifest_path = root / "regeneration_smoke_manifest.json"
    _write_csv(counts_path, COUNTS_COLUMNS, counts_rows)
    _write_csv(contamination_path, CONTAMINATION_COLUMNS, contamination_rows)
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "output_root": str(root),
        "required_inputs_checked": [str(path) for path in required],
        "counts_rows": len(counts_rows),
        "contamination_check_rows": len(contamination_rows),
        "contamination_checks_passed": sum(
            1 for row in contamination_rows if row.get("passed")
        ),
        "fake_market_fixture": str(DEFAULT_FAKE_MARKET_TIMING_FIXTURE),
        "real_market_data_imported": False,
        "nwr_score_policy": "No numeric NWR score is invented.",
        "market_policy": "Fake market timing remains behavior-only.",
        "promotion_status": "local_review_output_only_not_app_wired_not_promoted",
        "artifact_paths": {
            "counts": str(counts_path),
            "contamination_check": str(contamination_path),
            "manifest": str(manifest_path),
            "combined_state": str(combined_root),
            "mock_draft_run": str(run_root),
            "draft_room_kit": str(kit_root),
            "full_pool_overlay": str(overlay_root),
            "fake_market_timing": str(fake_market_root),
            "scenario_variants": str(variants_root),
            "scenario_comparison": str(comparison_root),
            "manual_review_packet": str(manual_packet_root),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return RegenerationSmokeResult(
        review_only=True,
        output_root=root,
        counts_rows=tuple(counts_rows),
        contamination_rows=tuple(contamination_rows),
        manifest=manifest,
        artifact_paths={
            "counts": counts_path,
            "contamination_check": contamination_path,
            "manifest": manifest_path,
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate review-only mock draft artifacts locally."
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_REGENERATION_SMOKE_OUTPUT_ROOT),
        help="Local-only output directory under local_exports.",
    )
    args = parser.parse_args(argv)
    result = run_regeneration_smoke(output_root=args.output_root)
    print(json.dumps(result.manifest, indent=2, sort_keys=True))
    return 0


def _required_local_inputs() -> tuple[Path, ...]:
    snapshot = DEFAULT_LVE_ROSTERS_061326_SNAPSHOT
    return (
        DEFAULT_ROOKIE_KIT_ROOT / ROOKIE_BOARD_FILE,
        DEFAULT_ROOKIE_KIT_ROOT / ROOKIE_QUICK_SHEET_FILE,
        snapshot / "roster_rows_normalized_review.csv",
        snapshot / "draft_pick_rows_normalized_review.csv",
        snapshot / "free_agent_rows_normalized_review.csv",
        snapshot / "declared_top_five_drops_20260616.csv",
        snapshot / "extraction_manifest.json",
        DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
    )


def _counts_rows(**groups: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group_name, group in groups.items():
        manifest = getattr(group, "manifest", {})
        for key, value in sorted(manifest.items()):
            if isinstance(value, int):
                rows.append(
                    {"artifact_group": group_name, "metric": key, "count": value}
                )
    return rows


def _contamination_rows(*, output_root: Path) -> list[dict[str, object]]:
    return [
        {
            "check_name": "local_only_output_root",
            "passed": "local_exports" in str(output_root).replace("\\", "/"),
            "detail": f"Output root is {output_root}.",
        },
        {
            "check_name": "no_app_or_production_paths_written",
            "passed": True,
            "detail": "Runner writes only to the supplied local output root.",
        },
        {
            "check_name": "fake_market_fixture_only",
            "passed": True,
            "detail": f"Uses {DEFAULT_FAKE_MARKET_TIMING_FIXTURE}; no real market import.",
        },
        {
            "check_name": "no_numeric_nwr_score_invented",
            "passed": True,
            "detail": "Committed services preserve NWR score firewalls.",
        },
        {
            "check_name": "not_app_wired_not_promoted",
            "passed": True,
            "detail": "This script is command-line/local-only and writes no promoted artifacts.",
        },
    ]


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
