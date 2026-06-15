from __future__ import annotations

import unittest
from dataclasses import fields
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.nwr_outcome_phase8_status_contract_service import (
    APPROVED_PHASE8_OUTCOME_STATUSES,
    ELIGIBLE_PHASE8_OUTCOME_HEADS,
    PHASE8_OUTCOME_STATUS_COPY,
    build_phase8_outcome_status,
    phase8_outcome_head_policy_rows,
    phase8_outcome_status_contract_rows,
)


class Phase8OutcomeStatusContractTests(unittest.TestCase):
    def test_phase8_status_vocabulary_is_exact(self) -> None:
        self.assertEqual(
            APPROVED_PHASE8_OUTCOME_STATUSES,
            (
                "internal_review_passed",
                "under_review",
                "unavailable",
            ),
        )
        self.assertEqual(set(PHASE8_OUTCOME_STATUS_COPY), set(APPROVED_PHASE8_OUTCOME_STATUSES))
        self.assertEqual(
            set(PHASE8_OUTCOME_STATUS_COPY.values()),
            {
                "Outcome model: internal review passed",
                "Outcome model: under review",
                "Outcome model: unavailable",
            },
        )

    def test_phase8_eligible_heads_are_exact(self) -> None:
        self.assertEqual(
            ELIGIBLE_PHASE8_OUTCOME_HEADS,
            (
                "qb_t12",
                "rb_t12",
                "wr_t12",
                "wr_t24",
                "wr_t36",
                "te_t12",
            ),
        )

    def test_phase8_status_builds_text_only_for_eligible_heads(self) -> None:
        for head in ELIGIBLE_PHASE8_OUTCOME_HEADS:
            display = build_phase8_outcome_status(
                head=head,
                status_key="internal_review_passed",
            )

            self.assertEqual(display.head, head)
            self.assertEqual(display.status_key, "internal_review_passed")
            self.assertEqual(display.display_copy, "Outcome model: internal review passed")
            self.assertEqual(display.display_scope, "non_numeric_status_only")
            self.assertIs(display.display_only, True)
            self.assertIs(display.released, False)

    def test_phase8_unknown_status_falls_back_or_raises(self) -> None:
        display = build_phase8_outcome_status(head="qb_t12", status_key="mystery")

        self.assertEqual(display.status_key, "unavailable")
        self.assertEqual(display.display_copy, "Outcome model: unavailable")

        with self.assertRaisesRegex(ValueError, "Unsupported Phase 8 Outcome status"):
            build_phase8_outcome_status(head="qb_t12", status_key="mystery", strict=True)

    def test_phase8_excluded_heads_fall_back_or_raise(self) -> None:
        for head in ("qb_t18", "rb_t36", "wr_t6", "te_t3", "unknown_head"):
            display = build_phase8_outcome_status(
                head=head,
                status_key="internal_review_passed",
            )

            self.assertEqual(display.status_key, "unavailable")
            self.assertEqual(display.display_copy, "Outcome model: unavailable")

        with self.assertRaisesRegex(ValueError, "Unsupported Phase 8 Outcome head"):
            build_phase8_outcome_status(
                head="rb_t48",
                status_key="under_review",
                strict=True,
            )

    def test_phase8_contract_rows_are_non_numeric_status_only(self) -> None:
        rows = phase8_outcome_status_contract_rows()

        self.assertEqual({row["status_key"] for row in rows}, set(APPROVED_PHASE8_OUTCOME_STATUSES))
        self.assertTrue(all(row["display_scope"] == "non_numeric_status_only" for row in rows))
        for row in rows:
            combined = " ".join(row.values()).lower()
            self.assertNotIn("%", combined)
            self.assertNotIn(" high", combined)
            self.assertNotIn(" medium", combined)
            self.assertNotIn(" low", combined)
            self.assertNotIn("green", combined)
            self.assertNotIn("yellow", combined)
            self.assertNotIn("red", combined)

    def test_phase8_head_policy_blocks_excluded_heads(self) -> None:
        rows = phase8_outcome_head_policy_rows()
        policy_by_head = {row["head"]: row["policy"] for row in rows}

        for head in ELIGIBLE_PHASE8_OUTCOME_HEADS:
            self.assertEqual(policy_by_head[head], "eligible")
        for head in ("qb_t18", "rb_t36", "wr_t48", "te_t6"):
            self.assertEqual(policy_by_head[head], "unavailable")

    def test_phase8_contract_exposes_no_ordering_or_numeric_fields(self) -> None:
        display = build_phase8_outcome_status(head="wr_t24", status_key="under_review")
        field_names = {field.name for field in fields(display)}

        forbidden_fragments = (
            "prob",
            "pct",
            "band",
            "odds",
            "score",
            "rank",
            "sort",
            "hidden",
        )
        self.assertFalse(
            any(
                fragment in field_name
                for field_name in field_names
                for fragment in forbidden_fragments
            )
        )

    def test_phase8_contract_service_does_not_read_forbidden_sources(self) -> None:
        service = ROOT / "src/services/nwr_outcome_phase8_status_contract_service.py"
        text = service.read_text(encoding="utf-8")

        for forbidden in (
            "local_exports",
            "read_csv",
            "glob(",
            "model_artifact",
            "current_player",
            "open(",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
