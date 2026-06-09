from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transform official nflverse snap_counts_{season}.csv into the "
            "Niners War Room local raw snap-count template."
        )
    )
    parser.add_argument("--input", help="Downloaded nflverse snap counts CSV.")
    parser.add_argument(
        "--download-to",
        help="Optional path for downloading the official nflverse season CSV first.",
    )
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument(
        "--season-type",
        default="REG",
        help="Filter source rows by game_type. Use empty string to disable.",
    )
    parser.add_argument(
        "--identity-map",
        help=(
            "Optional nflverse_identity_map.csv. Without it, GSIS/Sleeper IDs "
            "remain blank because snap counts expose PFR IDs."
        ),
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from src.services.nflverse_player_stats_import_service import (  # noqa: PLC0415
        download_official_snap_counts_csv,
        transform_official_snap_counts_csv,
    )

    args = _parse_args()
    input_path = args.input
    if args.download_to:
        download_report = download_official_snap_counts_csv(
            args.download_to,
            season=args.season,
        )
        print(f"download_status={download_report.status}")
        print(f"download_path={download_report.output_path}")
        input_path = args.download_to
    if not input_path:
        raise SystemExit("Provide --input or --download-to.")

    report = transform_official_snap_counts_csv(
        input_path,
        args.output,
        seasons={args.season},
        season_type=args.season_type or None,
        identity_map_path=args.identity_map,
    )
    print(f"status={report.status}")
    print(f"rows_seen={report.rows_seen}")
    print(f"rows_transformed={report.rows_transformed}")
    print(f"rows_skipped={report.rows_skipped}")
    print(f"output_path={report.output_path}")
    for warning in report.warnings:
        print(f"warning={warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
