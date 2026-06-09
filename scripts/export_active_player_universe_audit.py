from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.active_player_universe_audit_service import (  # noqa: E402
    build_active_player_universe_audit,
    write_active_player_universe_audit,
)
from src.services.player_feature_receipts_service import (  # noqa: E402
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
)

DEFAULT_DATA_PACK = PROJECT_ROOT / "local_exports" / "data_packs" / "lve_sleeper_20260505_pdf_ranks"
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "local_exports" / "model_audits"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Project Gold active player universe audit.",
    )
    parser.add_argument("--data-pack", default=str(DEFAULT_DATA_PACK))
    parser.add_argument("--source-root", default=str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR))
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--audit-id", default="")
    args = parser.parse_args()

    audit_id = args.audit_id or f"active_player_universe_{datetime.now(UTC):%Y%m%d_%H%M%S}"
    export_dir = Path(args.export_root) / audit_id
    report = build_active_player_universe_audit(
        args.data_pack,
        source_root=args.source_root,
    )
    paths = write_active_player_universe_audit(export_dir, report)
    manifest = {
        "audit_id": audit_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "active_data_pack": str(Path(args.data_pack)),
        "source_root": str(Path(args.source_root)),
        "review_only_status": True,
        "files": {key: str(path) for key, path in paths.items()},
        "row_counts": {
            "active_player_universe": len(report.rows),
            "active_player_universe_blockers": len(report.blocker_rows),
            "draftable_pool_universe": len(report.draft_pool_rows),
        },
        "blocker_count": len(report.blocker_rows),
        "summary": list(report.summary_rows),
        "draft_pool_summary": list(report.draft_pool_summary_rows),
    }
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
