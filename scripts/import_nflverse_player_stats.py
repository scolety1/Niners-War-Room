from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.services.nflverse_player_stats_import_service import (
        OFFICIAL_PLAYER_STATS_URL,
        download_official_player_stats_csv,
        transform_official_player_stats_csv,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Transform official nflverse player_stats.csv into the local "
            "nflverse_player_stats_weekly.csv contract."
        )
    )
    parser.add_argument("--input", type=Path, help="Local official player_stats.csv path.")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output nflverse_player_stats_weekly.csv path.",
    )
    parser.add_argument(
        "--season",
        type=int,
        action="append",
        help="Season to include. Repeat for multiple seasons. Defaults to all seasons.",
    )
    parser.add_argument(
        "--season-type",
        default="REG",
        help="Season type filter. Defaults to REG. Use empty string to include all.",
    )
    parser.add_argument(
        "--download-to",
        type=Path,
        help="Optional path to download official player_stats.csv before transforming.",
    )
    args = parser.parse_args()

    input_path = args.input
    if args.download_to:
        download_result = download_official_player_stats_csv(args.download_to)
        print(f"Downloaded {OFFICIAL_PLAYER_STATS_URL} -> {download_result.output_path}")
        input_path = args.download_to

    if input_path is None:
        parser.error("Provide --input or --download-to.")

    season_type = args.season_type or None
    result = transform_official_player_stats_csv(
        input_path,
        args.output,
        seasons=set(args.season) if args.season else None,
        season_type=season_type,
    )
    print(
        "Transformed "
        f"{result.rows_transformed}/{result.rows_seen} rows "
        f"({result.rows_skipped} skipped) -> {result.output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
