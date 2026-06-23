"""Refresh DynastyProcess market baseline with stale-cache protection."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import csv
import sys
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_dynastyprocess_market_baseline_v1 import DEFAULT_OUTPUT_DIR, write_outputs
from src.connectors.dynastyprocess_connector import (
    DEFAULT_CACHE_ROOT,
    DEFAULT_FILE_NAMES,
    DynastyProcessConnector,
    DynastyProcessFetchError,
    DynastyProcessSchemaError,
    evaluate_freshness,
    latest_cached_snapshot,
)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--snapshot-label", default=None)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    connector = DynastyProcessConnector(cache_root=args.cache_root)
    fetch_failed = False
    previous_snapshot = None

    try:
        snapshot = connector.fetch_snapshot(
            file_names=DEFAULT_FILE_NAMES,
            snapshot_label=args.snapshot_label,
        )
        previous_snapshot = latest_cached_snapshot(
            args.cache_root,
            exclude_snapshot_dir=snapshot.snapshot_dir,
        )
    except (DynastyProcessFetchError, DynastyProcessSchemaError) as exc:
        fetch_failed = True
        snapshot = latest_cached_snapshot(args.cache_root)
        if snapshot is None:
            freshness = evaluate_freshness(
                None,
                fetch_failed=True,
                derived_artifact_path=args.output_dir,
            )
            args.output_dir.mkdir(parents=True, exist_ok=True)
            with (args.output_dir / "dp_freshness_report.csv").open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=list(asdict(freshness)))
                writer.writeheader()
                writer.writerow(asdict(freshness))
            print(f"RED_NO_VALID_CACHE: {exc}")
            return 2
        print(f"YELLOW_FETCH_FAILED_USING_LAST_CACHE: {exc}")

    freshness = evaluate_freshness(
        snapshot,
        previous_snapshot=previous_snapshot,
        fetch_failed=fetch_failed,
        derived_artifact_path=args.output_dir,
    )
    paths = write_outputs(
        snapshot_dir=Path(snapshot.snapshot_dir),
        output_dir=args.output_dir,
        freshness=freshness,
    )
    print(f"DynastyProcess raw cache: {snapshot.snapshot_dir}")
    print(f"freshness_status: {freshness.freshness_status}")
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
