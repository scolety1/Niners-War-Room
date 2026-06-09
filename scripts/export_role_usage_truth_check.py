from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.role_usage_truth_check_service import (  # noqa: E402
    build_role_usage_truth_check_report,
    write_role_usage_truth_check_report,
)

DEFAULT_PREVIEW_ID = "sprint2_phase7_stats_first_20260514"
DEFAULT_MODEL_PREVIEW_ROOT = REPO_ROOT / "local_exports" / "nflverse_model_previews"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "local_exports" / "model_audits"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a role/usage truth audit from a stats-first preview."
    )
    parser.add_argument("--preview-id", default=DEFAULT_PREVIEW_ID)
    parser.add_argument("--model-preview-root", default=str(DEFAULT_MODEL_PREVIEW_ROOT))
    parser.add_argument("--output-id", default="")
    args = parser.parse_args()

    preview_dir = Path(args.model_preview_root) / args.preview_id
    receipt_path = preview_dir / "lve_normalized_feature_receipts.csv"
    contribution_path = preview_dir / "stats_first_feature_contributions.csv"
    if not receipt_path.exists() or not contribution_path.exists():
        print(f"Missing preview artifacts under {preview_dir}")
        return 1

    report = build_role_usage_truth_check_report(receipt_path, contribution_path)
    output_id = args.output_id or f"role_usage_truth_{_timestamp()}"
    output_dir = DEFAULT_OUTPUT_ROOT / output_id
    paths = write_role_usage_truth_check_report(output_dir, report)
    manifest = {
        "audit_id": output_id,
        "created_at": _now_utc(),
        "preview_id": args.preview_id,
        "preview_dir": str(preview_dir),
        "review_status": "review",
        "ranking_status": "review_only",
        "audit_rows": len(report.audit_rows),
        "summary_rows": len(report.summary_rows),
        "gap_report_rows": len(report.gap_report_rows),
        "files": {name: str(path) for name, path in paths.items()},
    }
    manifest_path = output_dir / "role_usage_truth_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"audit_id={output_id}")
    print("status=review")
    print("ranking_status=review_only")
    print(f"output_dir={output_dir}")
    print(f"audit_rows={len(report.audit_rows)}")
    print(f"summary_rows={len(report.summary_rows)}")
    print(f"gap_report_rows={len(report.gap_report_rows)}")
    print(f"manifest={manifest_path}")
    return 0


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
