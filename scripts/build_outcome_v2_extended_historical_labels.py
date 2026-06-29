"""Build extended Outcome V2 historical labels under shared data only.

This runner uses public nflreadpy player_stats data for a narrow, explicit
Outcome V2 label coverage extension. Generated CSVs are intentionally written
outside the repo and must not be committed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.outcome_v2_5y_data_coverage_service import (  # noqa: E402,I001
    build_anchor_horizon_labels,
    build_season_outcome_labels,
    write_extended_artifacts,
)


DEFAULT_OUTPUT_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
)
DEFAULT_PREVIOUS_ANCHOR_LABELS = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels"
    r"\outcome_v2_anchor_horizon_labels.csv"
)
DEFAULT_CACHE_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_source_audit\nflreadpy_cache"
)
DEFAULT_SEASONS = list(range(2012, 2025))
SCORING_MODE = "exact_verified_first_downs"
SOURCE = "nflreadpy.load_player_stats(summary_level=reg)"


def build_extended_historical_labels(
    *,
    seasons: list[int],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    cache_root: Path = DEFAULT_CACHE_ROOT,
) -> None:
    nflreadpy = _import_nflreadpy()
    _configure_nflreadpy_cache(cache_root)
    player_stats = nflreadpy.load_player_stats(seasons, summary_level="reg").to_pandas()
    _validate_source_columns(player_stats)
    season_labels = build_season_outcome_labels(
        player_stats,
        scoring_mode=SCORING_MODE,
    )
    anchor_labels = build_anchor_horizon_labels(season_labels)
    previous_anchor_labels = (
        pd.read_csv(DEFAULT_PREVIOUS_ANCHOR_LABELS)
        if DEFAULT_PREVIOUS_ANCHOR_LABELS.exists()
        else None
    )
    result = write_extended_artifacts(
        season_labels,
        anchor_labels,
        output_root,
        seasons=seasons,
        source=SOURCE,
        scoring_mode=SCORING_MODE,
        previous_anchor_labels=previous_anchor_labels,
    )
    print(f"season_label_rows={result.season_label_rows}")
    print(f"anchor_label_rows={result.anchor_label_rows}")
    print(f"complete_5y_rows={result.complete_5y_rows}")
    print(f"scoring_mode={result.scoring_mode}")
    print(f"season_labels={result.season_labels_path}")
    print(f"anchor_labels={result.anchor_labels_path}")
    print(f"manifest={result.manifest_path}")
    print(f"coverage_summary={result.coverage_summary_path}")


def _import_nflreadpy() -> object:
    try:
        import nflreadpy
    except ImportError as exc:  # pragma: no cover - exercised by runtime env
        raise RuntimeError(
            "nflreadpy is required for this narrow historical source pull. "
            "Use the existing approved shared tool environment; do not install "
            "dependencies into the repo from this script."
        ) from exc
    return nflreadpy


def _configure_nflreadpy_cache(cache_root: Path) -> None:
    from nflreadpy.config import update_config

    update_config(
        cache_mode="filesystem",
        cache_dir=cache_root,
        verbose=False,
        timeout=60,
    )


def _validate_source_columns(player_stats: pd.DataFrame) -> None:
    required = {
        "player_id",
        "player_display_name",
        "position",
        "season",
        "recent_team",
        "games",
        "passing_yards",
        "passing_tds",
        "passing_interceptions",
        "passing_first_downs",
        "rushing_yards",
        "rushing_tds",
        "rushing_first_downs",
        "receiving_yards",
        "receiving_tds",
        "receiving_first_downs",
    }
    missing = sorted(required.difference(player_stats.columns))
    if missing:
        raise RuntimeError(
            "Cannot build exact Outcome V2 labels; required factual columns "
            f"are missing: {', '.join(missing)}"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build review-only extended Outcome V2 historical labels."
    )
    parser.add_argument(
        "--seasons",
        default=",".join(str(season) for season in DEFAULT_SEASONS),
        help="Comma-separated seasons to pull from nflreadpy player_stats.",
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--cache-root", default=str(DEFAULT_CACHE_ROOT))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    seasons = [int(item.strip()) for item in args.seasons.split(",") if item.strip()]
    build_extended_historical_labels(
        seasons=seasons,
        output_root=Path(args.output_root),
        cache_root=Path(args.cache_root),
    )


if __name__ == "__main__":
    main()
