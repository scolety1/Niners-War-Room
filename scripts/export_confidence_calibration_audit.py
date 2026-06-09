from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.command_board_service import ACTIVE_STATS_FIRST_MODEL_DIR  # noqa: E402
from src.services.confidence_calibration_audit_service import (  # noqa: E402
    build_confidence_calibration_audit,
)

DEFAULT_DATA_PACK = (
    REPO_ROOT
    / "local_exports"
    / "data_packs"
    / "lve_sleeper_20260505_pdf_ranks"
)
DEFAULT_EXPORT_ROOT = REPO_ROOT / "local_exports" / "model_audits"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export confidence calibration audit rows for Project Gold Phase 23."
    )
    parser.add_argument("--data-pack", type=Path, default=DEFAULT_DATA_PACK)
    parser.add_argument("--model-source-root", type=Path, default=ACTIVE_STATS_FIRST_MODEL_DIR)
    parser.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    parser.add_argument("--audit-id", default=None)
    args = parser.parse_args()

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    audit_id = args.audit_id or "confidence_calibration_" + computed_at.replace(
        "-",
        "",
    ).replace(":", "").replace("Z", "")
    export_dir = args.export_root / audit_id
    export_dir.mkdir(parents=True, exist_ok=True)

    report = build_confidence_calibration_audit(
        args.data_pack,
        veteran_model_dir=args.model_source_root,
    )
    rows_path = export_dir / "confidence_calibration_audit_rows.csv"
    summary_path = export_dir / "confidence_calibration_summary.csv"
    explanations_path = export_dir / "confidence_calibration_explanations.csv"
    manifest_path = export_dir / "manifest.json"
    _write_csv(rows_path, report.rows)
    _write_csv(summary_path, report.summary_rows)
    _write_csv(explanations_path, report.explanation_rows)
    manifest = {
        "audit_id": audit_id,
        "computed_at": computed_at,
        "data_pack": str(args.data_pack),
        "model_source_root": report.source_root,
        "review_only": True,
        "files": {
            "audit_rows": str(rows_path),
            "summary": str(summary_path),
            "explanations": str(explanations_path),
        },
        "row_counts": {
            "audit_rows": len(report.rows),
            "summary": len(report.summary_rows),
            "explanations": len(report.explanation_rows),
        },
        "issues": report.issues,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Confidence calibration audit: {export_dir}")
    print(f"Rows: {len(report.rows)}")
    print(f"Mismatches: {sum(1 for row in report.rows if row['mismatch_flag'])}")
    print(f"Manifest: {manifest_path}")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
