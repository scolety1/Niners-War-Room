from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import fields
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.nwr_outcome_phase8_status_contract_service import (  # noqa: E402
    APPROVED_PHASE8_OUTCOME_STATUSES,
    ELIGIBLE_PHASE8_OUTCOME_HEADS,
    build_phase8_outcome_status,
    phase8_outcome_status_contract_rows,
)


class Phase9OutcomeStatusReleaseGateTests(unittest.TestCase):
    def test_release_gate_status_vocabulary_remains_exact(self) -> None:
        self.assertEqual(
            APPROVED_PHASE8_OUTCOME_STATUSES,
            ("internal_review_passed", "under_review", "unavailable"),
        )

    def test_release_gate_eligible_heads_remain_exact(self) -> None:
        self.assertEqual(
            ELIGIBLE_PHASE8_OUTCOME_HEADS,
            ("qb_t12", "rb_t12", "wr_t12", "wr_t24", "wr_t36", "te_t12"),
        )

    def test_public_contract_has_no_numeric_or_sort_fields(self) -> None:
        display = build_phase8_outcome_status(head="te_t12", status_key="under_review")
        forbidden = ("prob", "pct", "percent", "band", "odds", "score", "rank", "sort", "hidden")

        for field in fields(display):
            self.assertFalse(
                any(fragment in field.name for fragment in forbidden),
                field.name,
            )

    def test_contract_rows_are_text_only_and_non_numeric(self) -> None:
        for row in phase8_outcome_status_contract_rows():
            combined = " ".join(row.values()).lower()
            self.assertIn("non_numeric_status_only", combined)
            for forbidden in ("%", "probability", "band", "odds", "score", "rank", "sort"):
                self.assertNotIn(forbidden, combined)

    def test_excluded_heads_fail_closed(self) -> None:
        for head in ("qb_t18", "rb_t48", "wr_t6", "te_t3", "unknown"):
            display = build_phase8_outcome_status(
                head=head,
                status_key="internal_review_passed",
            )
            self.assertEqual(display.status_key, "unavailable")

    def test_service_source_has_no_forbidden_reads_or_artifact_paths(self) -> None:
        service = ROOT / "src/services/nwr_outcome_phase8_status_contract_service.py"
        text = service.read_text(encoding="utf-8").lower()
        for forbidden in (
            "local_exports",
            "read_csv",
            "glob(",
            "current_player",
            "model_artifact",
            "promoted",
            "outcome_probability",
            "outcome_band",
            "outcome_sort",
            "hidden_outcome",
        ):
            self.assertNotIn(forbidden, text)

    def test_phase9_static_release_gate_returns_green(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "scripts/outcome_probability/audit_phase9_outcome_status_release_gate_v1.py"),
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        self.assertIn("VERDICT=GREEN", result.stdout)
        self.assertIn("app_readable_outputs_created=false", result.stdout)
        self.assertIn("current_player_inference_created=false", result.stdout)


if __name__ == "__main__":
    unittest.main()
