from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.free_data_import_coverage_service import (  # noqa: E402
    build_free_data_import_coverage_matrix,
    write_free_data_import_coverage_matrix,
)

DEFAULT_RAW_ROOT = PROJECT_ROOT / "templates" / "real_data_inputs" / "nflverse_stats_upgrade"
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "local_exports" / "model_audits"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Project Gold free/public data import coverage matrix.",
    )
    parser.add_argument("--raw-import-root", default=str(DEFAULT_RAW_ROOT))
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--audit-id", default="")
    args = parser.parse_args()

    audit_id = args.audit_id or f"free_data_import_coverage_{datetime.now(UTC):%Y%m%d_%H%M%S}"
    export_dir = Path(args.export_root) / audit_id
    report = build_free_data_import_coverage_matrix(args.raw_import_root)
    paths = write_free_data_import_coverage_matrix(export_dir, report)
    manifest = {
        "audit_id": audit_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "raw_import_root": report.raw_import_root,
        "raw_import_status": report.raw_import_status,
        "review_only_status": True,
        "files": {key: str(path) for key, path in paths.items()},
        "row_counts": {
            "coverage_matrix": len(report.coverage_rows),
            "field_matrix": len(report.field_rows),
            "adapter_matrix": len(report.adapter_rows),
            "summary": len(report.summary_rows),
        },
        "issues": list(report.issues),
        "summary": list(report.summary_rows),
    }
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
