from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.player_feature_receipts_service import (  # noqa: E402
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
)
from src.services.route_participation_gap_gate_service import (  # noqa: E402
    build_route_participation_gap_gate_report,
    write_route_participation_gap_gate_report,
)

DEFAULT_OUTPUT_ROOT = REPO_ROOT / "local_exports" / "model_audits"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export route/participation gap gate reports."
    )
    parser.add_argument("--model-dir", default=str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR))
    parser.add_argument("--output-id", default="")
    args = parser.parse_args()

    report = build_route_participation_gap_gate_report(args.model_dir)
    output_id = args.output_id or f"route_participation_gap_gate_{_timestamp()}"
    output_dir = DEFAULT_OUTPUT_ROOT / output_id
    paths = write_route_participation_gap_gate_report(output_dir, report)
    manifest = {
        "audit_id": output_id,
        "created_at": _now_utc(),
        "model_dir": str(Path(args.model_dir)),
        "review_status": "review",
        "ranking_status": "review_only",
        "player_rows": len(report.rows),
        "area_rows": len(report.area_rows),
        "summary_rows": len(report.summary_rows),
        "issues": list(report.issues),
        "files": {name: str(path) for name, path in paths.items()},
    }
    manifest_path = output_dir / "route_participation_gap_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"audit_id={output_id}")
    print("status=review")
    print("ranking_status=review_only")
    print(f"output_dir={output_dir}")
    print(f"player_rows={len(report.rows)}")
    print(f"area_rows={len(report.area_rows)}")
    print(f"summary_rows={len(report.summary_rows)}")
    print(f"manifest={manifest_path}")
    if report.issues:
        print("issues=" + "; ".join(report.issues))
        return 1
    return 0


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
