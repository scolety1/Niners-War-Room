from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.command_board_service import ACTIVE_STATS_FIRST_MODEL_DIR  # noqa: E402
from src.services.model_audit_packet_service import (  # noqa: E402
    DEFAULT_MODEL_AUDIT_ROOT,
    export_model_audit_packet,
)

DEFAULT_DATA_PACK = (
    REPO_ROOT
    / "local_exports"
    / "data_packs"
    / "lve_sleeper_20260505_pdf_ranks"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a repeatable review-only model audit packet."
    )
    parser.add_argument("--data-pack", type=Path, default=DEFAULT_DATA_PACK)
    parser.add_argument("--export-root", type=Path, default=DEFAULT_MODEL_AUDIT_ROOT)
    parser.add_argument("--model-source-root", type=Path, default=ACTIVE_STATS_FIRST_MODEL_DIR)
    parser.add_argument(
        "--comparison-baseline",
        type=Path,
        default=None,
        help=(
            "Optional previous audit packet folder or full_active_rankings.csv file "
            "used to export movement reason metadata."
        ),
    )
    parser.add_argument(
        "--movement-export-name",
        default="movement_vs_checkpoint.csv",
        help="Movement CSV file name when --comparison-baseline is provided.",
    )
    parser.add_argument("--packet-id", default=None)
    args = parser.parse_args()

    packet = export_model_audit_packet(
        args.data_pack,
        export_root=args.export_root,
        model_source_root=args.model_source_root,
        comparison_baseline=args.comparison_baseline,
        movement_export_name=args.movement_export_name,
        packet_id=args.packet_id,
    )
    print(f"Audit packet: {packet.export_dir}")
    print(f"Manifest: {packet.manifest_path}")
    print(f"Review only: {packet.manifest['review_only_status']}")


if __name__ == "__main__":
    main()
