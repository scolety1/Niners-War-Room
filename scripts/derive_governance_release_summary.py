"""Deterministically derive a release-safe governance admission summary from
a canonical NWR_DATA_GOVERNANCE.json receipt.

Usage:
    python scripts/derive_governance_release_summary.py \
        docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/NWR_DATA_GOVERNANCE.json \
        docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json

This script is the same mechanism used to produce the committed
NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json files and to prove, in
tests/test_governance_release_summary_service.py, that the committed summary
has zero drift from its canonical receipt: re-running this script against
the canonical receipt must reproduce the committed summary file exactly.

Never mutates the canonical receipt. Reads it, writes only the summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.governance_release_summary_service import (  # noqa: E402
    derive_release_admission_summary,
    summary_json_bytes,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical_receipt", type=Path)
    parser.add_argument("release_summary_out", type=Path)
    args = parser.parse_args()

    receipt_bytes = args.canonical_receipt.read_bytes()
    receipt = json.loads(receipt_bytes.decode("utf-8-sig"))
    summary = derive_release_admission_summary(receipt, receipt_bytes)
    args.release_summary_out.write_bytes(summary_json_bytes(summary))
    print(f"Wrote {args.release_summary_out} (derived from {args.canonical_receipt})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
