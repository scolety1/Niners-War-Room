from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.qb_te_upper_band_guard_v2_patch_audit_service import (  # noqa: E402
    build_upper_band_guard_v2_patch_audit,
    write_upper_band_guard_v2_patch_audit,
)


def main() -> None:
    result = build_upper_band_guard_v2_patch_audit()
    paths = write_upper_band_guard_v2_patch_audit(result)
    print("wrote", paths.movement_audit_csv)
    print("wrote", paths.audit_report)
    print("wrote", paths.handoff)
    print("verdict", result.summary["verdict"])
    print("failed_acceptance_criteria", result.summary["failed_acceptance_criteria"])


if __name__ == "__main__":
    main()
