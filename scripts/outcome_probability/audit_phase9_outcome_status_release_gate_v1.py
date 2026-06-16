from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.services.nwr_outcome_phase8_status_contract_service import (  # noqa: E402
    APPROVED_PHASE8_OUTCOME_STATUSES,
    ELIGIBLE_PHASE8_OUTCOME_HEADS,
    build_phase8_outcome_status,
)


APPROVED_STATUSES = (
    "internal_review_passed",
    "under_review",
    "unavailable",
)

ELIGIBLE_HEADS = (
    "qb_t12",
    "rb_t12",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
)

FORBIDDEN_FIELD_FRAGMENTS = (
    "prob",
    "pct",
    "percent",
    "band",
    "odds",
    "score",
    "rank",
    "sort",
    "hidden",
)

FORBIDDEN_SOURCE_FRAGMENTS = (
    "local_exports",
    "read_csv",
    "glob(",
    "model_artifact",
    "current_player",
    "outcome_probability",
    "outcome_band",
    "outcome_rank",
    "outcome_sort",
    "hidden_outcome",
    "promoted",
)


def main() -> int:
    issues: list[str] = []

    if APPROVED_PHASE8_OUTCOME_STATUSES != APPROVED_STATUSES:
        issues.append("RED approved status vocabulary changed")
    if ELIGIBLE_PHASE8_OUTCOME_HEADS != ELIGIBLE_HEADS:
        issues.append("RED eligible head list changed")

    display = build_phase8_outcome_status(head="qb_t12", status_key="internal_review_passed")
    field_names = {field.name for field in fields(display)}
    for field_name in sorted(field_names):
        for fragment in FORBIDDEN_FIELD_FRAGMENTS:
            if fragment in field_name:
                issues.append(f"RED forbidden public field fragment {fragment!r} in {field_name!r}")

    service_path = REPO_ROOT / "src/services/nwr_outcome_phase8_status_contract_service.py"
    service_text = service_path.read_text(encoding="utf-8").lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in service_text:
            issues.append(f"RED forbidden source fragment {fragment!r}")

    unavailable = build_phase8_outcome_status(head="rb_t48", status_key="internal_review_passed")
    if unavailable.status_key != "unavailable":
        issues.append("RED excluded head did not fail closed to unavailable")

    if issues:
        for issue in issues:
            print(issue)
        print("VERDICT=RED")
        return 1

    print("VERDICT=GREEN")
    print("status_contract=non_numeric_only")
    print(f"approved_statuses={','.join(APPROVED_STATUSES)}")
    print(f"eligible_heads={','.join(ELIGIBLE_HEADS)}")
    print("app_readable_outputs_created=false")
    print("current_player_inference_created=false")
    print("numeric_outputs_created=false")
    print("rank_sort_hidden_keys_created=false")
    print("promoted_artifacts_created=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
