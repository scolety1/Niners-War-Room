from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.nfl_usage_historical_panel_service import (
    DEFAULT_SEASONS,
    DOC_ROOT,
    SHARED_CACHE_ROOT,
    build_historical_usage_panel,
    historical_panel_paths,
    validate_csv_flags,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build review-only historical NFL usage panel summaries."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write sanitized docs and shared-cache panels.",
    )
    parser.add_argument("--seasons", nargs="+", type=int, default=DEFAULT_SEASONS)
    parser.add_argument("--doc-root", type=Path, default=DOC_ROOT)
    parser.add_argument("--shared-cache-root", type=Path, default=SHARED_CACHE_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = build_historical_usage_panel(
        doc_root=args.doc_root,
        shared_cache_root=args.shared_cache_root,
        seasons=args.seasons,
        write=args.run,
    )
    if args.run:
        validate_csv_flags(list(historical_panel_paths(args.doc_root).values()))
    print(f"doc_root={result.doc_root}")
    print(f"shared_cache_root={result.shared_cache_root}")
    print(f"backtest_status={result.backtest_status}")
    print(f"files_written={len(result.files_written)}")
    for source, status in sorted(result.source_status.items()):
        print(f"source_status={source}:{status}")
    for panel, status in sorted(result.panel_status.items()):
        print(f"panel_status={panel}:{status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
