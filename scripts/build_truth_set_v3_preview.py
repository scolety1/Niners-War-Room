from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.truth_set_v3_preview_build_service import build_truth_set_v3_model_preview  # noqa: E402,I001

DEFAULT_ACTIVE_ROOT = Path("local_exports/active_veteran_model_public_sources")
DEFAULT_V3_REPORT_ROOT = Path("local_exports/truth_set_lab/v3/reports")
DEFAULT_V2_REPORT_ROOT = Path("local_exports/truth_set_lab/v2/reports")
DEFAULT_V1_SOURCE_ROOT = Path("local_exports/truth_set_lab/v1/source_clean")
DEFAULT_PREVIEW_ROOT = Path("local_exports/nflverse_model_previews")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a review-only Truth Set Lab v3 model preview.",
    )
    parser.add_argument("--preview-id", default="")
    parser.add_argument("--active-root", default=str(DEFAULT_ACTIVE_ROOT))
    parser.add_argument("--v3-report-root", default=str(DEFAULT_V3_REPORT_ROOT))
    parser.add_argument("--v2-report-root", default=str(DEFAULT_V2_REPORT_ROOT))
    parser.add_argument("--v1-source-root", default=str(DEFAULT_V1_SOURCE_ROOT))
    parser.add_argument("--preview-root", default=str(DEFAULT_PREVIEW_ROOT))
    args = parser.parse_args()

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    preview_id = args.preview_id or "truth_set_lab_v3_preview_" + computed_at.replace(
        "-",
        "",
    ).replace(":", "").replace("Z", "")

    active_root = Path(args.active_root)
    v3_root = Path(args.v3_report_root)
    v2_root = Path(args.v2_report_root)
    v1_root = Path(args.v1_source_root)
    preview_root = Path(args.preview_root)

    result = build_truth_set_v3_model_preview(
        active_output_path=active_root / "stats_first_veteran_model_preview_outputs.csv",
        active_normalized_path=active_root / "stats_first_normalized_features.csv",
        v2_output_path=_latest_v2_output(preview_root),
        production_season_path=v3_root / "truth_set_v3_production_player_season.csv",
        usage_season_path=v3_root / "truth_set_v3_usage_player_season.csv",
        snap_share_season_path=v3_root / "truth_set_v3_snap_share_player_season.csv",
        projection_recompute_path=v2_root / "projection_recompute_preview.csv",
        young_bridge_path=v2_root / "young_bridge_prior_preview.csv",
        injury_path=v1_root / "injury.csv",
        market_path=v1_root / "trade_liquidity.csv",
        route_honesty_path=v3_root / "truth_set_v3_route_data_honesty.csv",
        output_root=preview_root,
        preview_id=preview_id,
        computed_at=computed_at,
    )
    print(
        json.dumps(
            {
                "preview_id": result.preview_id,
                "preview_path": str(result.preview_path),
                "output_path": str(result.output_path),
                "summary": result.summary,
            },
            indent=2,
        )
    )


def _latest_v2_output(preview_root: Path) -> Path:
    candidates = sorted(
        preview_root.glob(
            "truth_set_lab_v2_preview_*/stats_first_veteran_model_preview_outputs.csv"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else Path("")


if __name__ == "__main__":
    main()
