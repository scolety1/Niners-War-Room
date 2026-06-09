from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.truth_set_v3_production_import_service import (  # noqa: E402
    DEFAULT_TRUTH_SET_SOURCE,
)
from src.services.truth_set_v3_snap_share_import_service import (  # noqa: E402
    DEFAULT_DOWNLOAD_ROOT,
    DEFAULT_IDENTITY_MAP_SOURCE,
    DEFAULT_PRODUCTION_WEEK_SOURCE,
    build_truth_set_v3_snap_share_preview,
    write_truth_set_v3_snap_outputs,
)
from src.services.truth_set_v3_usage_derivation_service import (  # noqa: E402
    DEFAULT_REPORT_ROOT,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build review-only Truth Set Lab v3 snap-share preview."
    )
    parser.add_argument("--truth-set", type=Path, default=DEFAULT_TRUTH_SET_SOURCE)
    parser.add_argument("--production-week", type=Path, default=DEFAULT_PRODUCTION_WEEK_SOURCE)
    parser.add_argument("--download-root", type=Path, default=DEFAULT_DOWNLOAD_ROOT)
    parser.add_argument("--identity-map", type=Path, default=DEFAULT_IDENTITY_MAP_SOURCE)
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
        help="Do not download official nflverse snap counts if local cache is missing.",
    )
    parser.add_argument(
        "--no-identity-map",
        action="store_true",
        help="Skip PFR-to-GSIS/Sleeper enrichment and emit identity warnings.",
    )
    args = parser.parse_args()

    result = build_truth_set_v3_snap_share_preview(
        truth_set_path=args.truth_set,
        production_week_path=args.production_week,
        snap_download_root=args.download_root,
        identity_map_path=None if args.no_identity_map else args.identity_map,
        seasons=set(args.season) if args.season else None,
        download_if_missing=not args.no_download,
    )
    paths = write_truth_set_v3_snap_outputs(args.output_root, result)
    print(f"status={result.summary.get('status')}")
    print(f"truth_set_players={result.summary.get('truth_set_players')}")
    print(f"matched_players_with_player_ids={result.summary.get('matched_players_with_player_ids')}")
    print(f"missing_players={result.summary.get('missing_players')}")
    print(f"snap_rows_seen={result.summary.get('snap_rows_seen')}")
    print(f"week_rows={result.summary.get('week_rows')}")
    print(f"season_rows={result.summary.get('season_rows')}")
    print(f"identity_warning_rows={result.summary.get('identity_warning_rows')}")
    print(f"requested_seasons={result.summary.get('requested_seasons')}")
    for name, path in paths.items():
        print(f"{name}={path}")
    return 0 if result.summary.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
