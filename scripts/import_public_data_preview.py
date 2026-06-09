from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.services.public_data_preview_import_service import (  # noqa: PLC0415
        DEFAULT_PREVIEW_OUTPUT_ROOT,
        run_public_data_preview_import,
    )
    from src.services.sleeper_import_service import DEFAULT_LEAGUE_ID  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description=(
            "Download public nflverse/Sleeper/DynastyProcess data into an "
            "isolated preview folder. This never promotes model outputs."
        )
    )
    parser.add_argument(
        "--data-pack",
        type=Path,
        default=Path("local_exports/data_packs/lve_sleeper_20260505_pdf_ranks"),
        help="Current data pack used to identify rostered players for identity review.",
    )
    parser.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_PREVIEW_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--season",
        type=int,
        action="append",
        help="Season to import. Repeat for multiple seasons. Defaults to 2023-2025.",
    )
    parser.add_argument("--preview-id", help="Optional deterministic preview folder name.")
    args = parser.parse_args()

    seasons = tuple(args.season) if args.season else (2023, 2024, 2025)
    result = run_public_data_preview_import(
        data_pack_path=args.data_pack,
        league_id=args.league_id,
        output_root=args.output_root,
        seasons=seasons,
        preview_id=args.preview_id,
    )
    print(f"preview_id={result.preview_id}")
    print(f"status={result.status}")
    print(f"output_dir={result.output_dir}")
    print(f"raw_dir={result.raw_dir}")
    print(f"manifest={result.manifest_path}")
    print(f"coverage={result.coverage_path}")
    print(f"identity_map={result.identity_map_path}")
    print(f"critical_gaps={result.critical_gap_path}")
    for step in result.steps:
        print(
            "step="
            f"{step.step},status={step.status},rows={step.rows},"
            f"output={step.output_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
