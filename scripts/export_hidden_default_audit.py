from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.hidden_default_audit_service import (  # noqa: E402
    build_hidden_default_audit,
    write_hidden_default_audit_csv,
)
from src.services.player_feature_receipts_service import (  # noqa: E402
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
)

DEFAULT_DATA_PACK = PROJECT_ROOT / "local_exports" / "data_packs" / "lve_sleeper_20260505_pdf_ranks"
DEFAULT_EXPORT_ROOT = PROJECT_ROOT / "local_exports" / "model_audits"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Project Gold hidden-default audit rows.",
    )
    parser.add_argument("--data-pack", default=str(DEFAULT_DATA_PACK))
    parser.add_argument("--model-source-root", default=str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR))
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--audit-id", default="")
    args = parser.parse_args()

    audit_id = args.audit_id or f"hidden_default_audit_{datetime.now(UTC):%Y%m%d_%H%M%S}"
    export_dir = Path(args.export_root) / audit_id
    export_dir.mkdir(parents=True, exist_ok=False)

    report = build_hidden_default_audit(
        args.data_pack,
        veteran_model_dir=args.model_source_root,
    )
    audit_path = export_dir / "default_value_audit.csv"
    summary_path = export_dir / "default_value_audit_summary.csv"
    write_hidden_default_audit_csv(audit_path, list(report.rows))
    _write_summary_csv(summary_path, list(report.summary_rows))

    manifest = {
        "audit_id": audit_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "active_data_pack": str(Path(args.data_pack)),
        "active_model_source_root": str(Path(args.model_source_root)),
        "review_only_status": True,
        "default_values_scanned": [50, 75, 76, 78],
        "audit_file": str(audit_path),
        "summary_file": str(summary_path),
        "row_count": len(report.rows),
        "unsafe_hidden_evidence_rows": len(report.unsafe_rows),
        "summary": list(report.summary_rows),
    }
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


def _write_summary_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["default_bucket", "row_count"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "default_bucket": row.get("default_bucket", ""),
                    "row_count": row.get("row_count", ""),
                }
            )


if __name__ == "__main__":
    main()
