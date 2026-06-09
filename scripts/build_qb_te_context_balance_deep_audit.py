from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.qb_te_context_balance_deep_audit_service import (  # noqa: E402
    build_context_balance_deep_audit,
    write_context_balance_deep_audit,
)


def main() -> int:
    result = build_context_balance_deep_audit()
    paths = write_context_balance_deep_audit(result=result)
    print(f"deep_audit_report: {paths.deep_audit_report}")
    print(f"production_patch_proposal: {paths.production_patch_proposal}")
    print(f"active_hash_before: {result.active_hash_before}")
    print(f"active_hash_after: {result.active_hash_after}")
    print(f"active_output_changed: {result.active_output_changed}")
    print(f"verdict: {result.summary['verdict']}")
    print(f"top25_position_counts: {result.summary['top25_position_counts']}")
    print(f"my_team_max_abs_rank_delta: {result.summary['my_team_max_abs_rank_delta']}")
    print(f"sentinels_safe: {result.summary['sentinels_safe']}")
    print(f"contamination_safe: {result.summary['contamination_safe']}")
    print(f"decision_board_blocked: {result.summary['decision_board_blocked']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
