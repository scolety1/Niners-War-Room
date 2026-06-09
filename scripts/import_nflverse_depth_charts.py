from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transform official nflverse depth_charts_{season}.csv into the "
            "Niners War Room local raw depth-chart template."
        )
    )
    parser.add_argument("--input", help="Downloaded nflverse depth charts CSV.")
    parser.add_argument(
        "--download-to",
        help="Optional path for downloading the official nflverse season CSV first.",
    )
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument(
        "--default-week",
        type=int,
        default=0,
        help=(
            "Week to use when the official depth-chart row has only a date. "
            "Use 0 for preseason/as-of context."
        ),
    )
    parser.add_argument(
        "--identity-map",
        help="Optional nflverse_identity_map.csv for Sleeper ID enrichment.",
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from src.services.nflverse_player_stats_import_service import (  # noqa: PLC0415
        download_official_depth_chart_csv,
        transform_official_depth_chart_csv,
    )

    args = _parse_args()
    input_path = args.input
    if args.download_to:
        download_report = download_official_depth_chart_csv(
            args.download_to,
            season=args.season,
        )
        print(f"download_status={download_report.status}")
        print(f"download_path={download_report.output_path}")
        input_path = args.download_to
    if not input_path:
        raise SystemExit("Provide --input or --download-to.")

    report = transform_official_depth_chart_csv(
        input_path,
        args.output,
        season=args.season,
        default_week=args.default_week,
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
