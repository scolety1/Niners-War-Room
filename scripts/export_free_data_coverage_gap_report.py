from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.command_board_service import ACTIVE_STATS_FIRST_MODEL_DIR  # noqa: E402
from src.services.free_data_coverage_gap_report_service import (  # noqa: E402
    build_free_data_coverage_gap_report,
    write_free_data_coverage_gap_report,
)

DEFAULT_DATA_PACK = PROJECT_ROOT / "local_exports" / "data_packs" / "lve_sleeper_20260505_pdf_ranks"
DEFAULT_RAW_ROOT = PROJECT_ROOT / "templates" / "real_data_inputs" / "nflverse_stats_upgrade"
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "local_exports" / "model_audits"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Project Gold free/public data source gap report.",
    )
    parser.add_argument("--data-pack", default=str(DEFAULT_DATA_PACK))
    parser.add_argument("--model-source-root", default=str(ACTIVE_STATS_FIRST_MODEL_DIR))
    parser.add_argument("--raw-import-root", default=str(DEFAULT_RAW_ROOT))
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--audit-id", default="")
    args = parser.parse_args()

    audit_id = args.audit_id or f"free_data_gap_report_{datetime.now(UTC):%Y%m%d_%H%M%S}"
    export_dir = Path(args.export_root) / audit_id
    report = build_free_data_coverage_gap_report(
        args.data_pack,
        veteran_model_dir=args.model_source_root,
        raw_import_root=args.raw_import_root,
    )
    paths = write_free_data_coverage_gap_report(export_dir, report)
    manifest = {
        "audit_id": audit_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "active_data_pack": str(Path(args.data_pack)),
        "active_model_source_root": str(Path(args.model_source_root)),
        "raw_import_root": str(Path(args.raw_import_root)),
        "review_only_status": report.review_only_status,
        "files": {key: str(path) for key, path in paths.items()},
        "row_counts": {
            "category_report": len(report.category_rows),
            "missing_critical_fields": len(report.missing_critical_field_rows),
            "unavailable_free_sources": len(report.unavailable_free_source_rows),
            "recommendations": len(report.recommendation_rows),
            "source_coverage_summary": len(report.source_coverage_summary_rows),
            "free_data_summary": len(report.free_data_summary_rows),
        },
        "blocking_critical_fields": sum(
            1 for row in report.missing_critical_field_rows if row["blocks_decision_ready"]
        ),
        "issues": list(report.issues),
        "recommendations": list(report.recommendation_rows),
    }
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
