from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from src.services.real_draft_pool_preview_service import (  # noqa: PLC0415
        DEFAULT_DRAFT_POOL_OUTPUT_ROOT,
        build_real_draft_pool_preview,
    )
    from src.services.sleeper_import_service import DEFAULT_LEAGUE_ID  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description=(
            "Build a preview data-pack copy with real rookie/free-agent "
            "draftable pool files. Released veterans stay empty until provided."
        )
    )
    parser.add_argument(
        "--data-pack",
        type=Path,
        default=Path("local_exports/data_packs/lve_sleeper_20260505_pdf_ranks"),
    )
    parser.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_DRAFT_POOL_OUTPUT_ROOT)
    parser.add_argument("--draft-year", type=int)
    parser.add_argument("--preview-id")
    args = parser.parse_args()

    result = build_real_draft_pool_preview(
        data_pack_path=args.data_pack,
        league_id=args.league_id,
        output_root=args.output_root,
        draft_year=args.draft_year,
        preview_id=args.preview_id,
    )
    print(f"preview_id={result.preview_id}")
    print(f"status={result.status}")
    print(f"output_pack={result.output_pack_path}")
    print(f"manifest={result.manifest_path}")
    print(f"readiness={result.readiness_path}")
    print(f"rookies={result.rookie_path}")
    print(f"available_veterans={result.available_veteran_path}")
    print(f"manual={result.manual_path}")
    for step in result.steps:
        print(
            "step="
            f"{step.step},status={step.status},rows={step.rows},"
            f"output={step.output_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
