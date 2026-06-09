from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.truth_set_v3_production_import_service import (  # noqa: E402
    DEFAULT_LOCAL_PLAYER_STATS_SOURCE,
    DEFAULT_TRUTH_SET_SOURCE,
    build_truth_set_v3_production_preview,
    write_truth_set_v3_production_outputs,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/truth_set_lab/v3/reports")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build review-only Truth Set Lab v3 native nflverse production preview."
    )
    parser.add_argument("--truth-set", type=Path, default=DEFAULT_TRUTH_SET_SOURCE)
    parser.add_argument(
        "--player-stats",
        type=Path,
        default=DEFAULT_LOCAL_PLAYER_STATS_SOURCE,
        help="Official nflverse player_stats.csv. Downloads if missing by default.",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--season",
        action="append",
        type=int,
        help="Season to include. Repeat for multiple seasons. Defaults to latest 3 available.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not download official nflverse player_stats.csv if local file is missing.",
    )
    args = parser.parse_args()

    result = build_truth_set_v3_production_preview(
        truth_set_path=args.truth_set,
        player_stats_path=args.player_stats,
        download_if_missing=not args.no_download,
        seasons=set(args.season) if args.season else None,
    )
    paths = write_truth_set_v3_production_outputs(args.output_root, result)
    print(f"status={result.summary.get('status')}")
    print(f"truth_set_players={result.summary.get('truth_set_players')}")
    print(f"matched_players={result.summary.get('matched_players')}")
    print(f"missing_players={result.summary.get('missing_players')}")
    print(f"week_rows={result.summary.get('week_rows')}")
    print(f"season_rows={result.summary.get('season_rows')}")
    print(f"requested_seasons={result.summary.get('requested_seasons')}")
    for name, path in paths.items():
        print(f"{name}={path}")
    if result.validation_errors:
        for error in result.validation_errors:
            print(f"validation_error={error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
