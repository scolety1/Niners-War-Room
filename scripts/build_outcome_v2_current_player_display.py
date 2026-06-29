from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.outcome_v2_current_player_display_service import (
    CURRENT_BOARD_PATH,
    DISPLAY_ARTIFACT_PATH,
    IDENTITY_BRIDGE_PATH,
    MODEL_BUCKET_RATES_PATH,
    SEASON_STATS_POINTER_PATH,
    VALIDATION_RESULTS_PATH,
    write_current_player_display_artifact,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build compact display-only Outcome V2 current-player artifact.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write the compact display artifact.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DISPLAY_ARTIFACT_PATH,
        help="Destination CSV path for the compact display artifact.",
    )
    parser.add_argument(
        "--current-board-path",
        type=Path,
        default=CURRENT_BOARD_PATH,
        help="Current board CSV path.",
    )
    parser.add_argument(
        "--season-stats-pointer-path",
        type=Path,
        default=SEASON_STATS_POINTER_PATH,
        help="latest_candidate pointer for approved partial 2025 season stats.",
    )
    parser.add_argument(
        "--identity-bridge-path",
        type=Path,
        default=IDENTITY_BRIDGE_PATH,
        help="Outcome V2 current-board-to-GSIS identity bridge CSV.",
    )
    parser.add_argument(
        "--validation-results-path",
        type=Path,
        default=VALIDATION_RESULTS_PATH,
        help="Outcome V2 extended validation results CSV.",
    )
    parser.add_argument(
        "--model-bucket-rates-path",
        type=Path,
        default=MODEL_BUCKET_RATES_PATH,
        help="Outcome V2 validated model bucket rates CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to build the compact display-only artifact")
        print(f"default_output_path={args.output_path}")
        return 0

    result = write_current_player_display_artifact(
        output_path=args.output_path,
        current_board_path=args.current_board_path,
        season_stats_pointer_path=args.season_stats_pointer_path,
        identity_bridge_path=args.identity_bridge_path,
        validation_results_path=args.validation_results_path,
        model_bucket_rates_path=args.model_bucket_rates_path,
    )
    print(f"artifact_path={result.artifact_path}")
    print(f"row_count={result.row_count}")
    print(f"eligible_probability_rows={result.eligible_probability_rows}")
    print(f"not_enough_information_rows={result.not_enough_information_rows}")
    print(f"rookie_out_of_scope_rows={result.rookie_out_of_scope_rows}")
    print(f"missing_feature_rows={result.missing_feature_rows}")
    print(f"unsupported_position_rows={result.unsupported_position_rows}")
    print(f"included_field_count={len(result.included_fields)}")
    print(f"blocked_fields={'|'.join(result.blocked_fields)}")
    print(f"sha256={result.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
