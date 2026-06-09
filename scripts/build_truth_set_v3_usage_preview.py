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
)
from src.services.truth_set_v3_usage_derivation_service import (  # noqa: E402
    DEFAULT_DOWNLOAD_ROOT,
    DEFAULT_REPORT_ROOT,
    build_truth_set_v3_usage_preview,
    write_truth_set_v3_usage_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build review-only Truth Set Lab v3 play-by-play usage preview."
    )
    parser.add_argument("--truth-set", type=Path, default=DEFAULT_TRUTH_SET_SOURCE)
    parser.add_argument("--player-stats", type=Path, default=DEFAULT_LOCAL_PLAYER_STATS_SOURCE)
    parser.add_argument("--download-root", type=Path, default=DEFAULT_DOWNLOAD_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument(
        "--season",
        action="append",
        type=int,
        help="Season to include. Repeat for multiple seasons. Defaults to production seasons.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not download official nflverse play-by-play files if local cache is missing.",
    )
    args = parser.parse_args()

    result = build_truth_set_v3_usage_preview(
        truth_set_path=args.truth_set,
        player_stats_path=args.player_stats,
        pbp_download_root=args.download_root,
        seasons=set(args.season) if args.season else None,
        download_if_missing=not args.no_download,
    )
    paths = write_truth_set_v3_usage_outputs(args.output_root, result)
    print(f"status={result.summary.get('status')}")
    print(f"truth_set_players={result.summary.get('truth_set_players')}")
    print(f"matched_players_with_player_ids={result.summary.get('matched_players_with_player_ids')}")
    print(f"missing_players={result.summary.get('missing_players')}")
    print(f"pbp_rows_seen={result.summary.get('pbp_rows_seen')}")
    print(f"week_rows={result.summary.get('week_rows')}")
    print(f"season_rows={result.summary.get('season_rows')}")
    print(f"requested_seasons={result.summary.get('requested_seasons')}")
    for name, path in paths.items():
        print(f"{name}={path}")
    return 0 if result.summary.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
