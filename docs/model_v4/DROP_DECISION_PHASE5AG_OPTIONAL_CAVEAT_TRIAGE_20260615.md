# Drop Decision Phase 5AG Optional Caveat Triage

Date: 2026-06-15
Lane: `work/drop-decision-day-review`
Baseline: `6b8c04f96ba7af8ad3e5eb1e62895aa13f4ba2d3` / `Fix branch diff whitespace hygiene`

## Classification

Overall: GREEN

Phase 5A remains GREEN as human-review context. Phase 5B remains CLOSED / NOT OPENED.

This triage resolved the two optional adjacent caveats from Phase 5AF without changing production model, service, or app logic. The changes are limited to stale optional audit test contracts, a docs-only audit note, and regenerated ignored local-only review fixtures.

## Caveat A: Decision Board Coherence Warning Count

Initial finding: `tests/test_decision_board_coherence_audit.py` passed 4 tests and failed 1 test because it asserted an exact `june15_decision_board_warnings.csv` row count of 54. Current local Decision Board artifacts contain 105 review rows, 105 receipts, 315 component rows, and 51 warning rows.

Classification: stale exact-count test expectation.

Action: replaced the brittle exact warning total with invariant checks:

- warning rows must exist
- warning rows cannot exceed board rows
- warning severity must remain `review`
- expected review-only warning codes must be present

Final result: `tests/test_decision_board_coherence_audit.py` passes.

## Caveat B: Rookie Pick Decision Lab Fixture

Initial finding: `tests/test_non_formula_sanity_fixtures.py` failed because `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv` was missing.

Classification: optional adjacent local fixture absent, repairable from admitted local-only review inputs.

Action:

- regenerated `startup_slot_simulator/latest` local review artifacts with `scripts/build_model_v4_startup_slot_simulator.py`
- regenerated `rookie_pick_decision_lab/latest` local review artifacts with `scripts/build_model_v4_rookie_pick_decision_lab.py`
- restored generated tracked docs drift from those scripts
- updated the stale optional sanity assertion for the `2026 5.04` manual-only row to assert the current neutral label `manual_decision_required` plus the manual-only `pick_tier`, `confidence_status`, and no-exact-equivalence guardrail

Final result: `tests/test_non_formula_sanity_fixtures.py`, `tests/test_model_v4_rookie_pick_decision_lab_service.py`, and `tests/test_model_v4_startup_slot_simulator_service.py` pass.

## Safe-Use Notes

The regenerated local fixtures are ignored local review artifacts only. They are not committed and must not be treated as final pick, trade, cut/keep, roster, ranking, probability, band, or recommendation outputs.

The fixture tests preserve review-only guardrails:

- `review_only_rookie_pick_decision_lab_not_final_selection`
- `do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation`
- internal model neighbor context is not one-for-one trade-market equivalence
- manual-only missing-baseline picks require human review

## Guardrail Confirmation

This triage did not push, deploy, merge, stage or commit `data/` or `local_exports/`, create final/implied recommendations, sort or rank drop candidates, change rankings/sorting, create probabilities, create outcome bands, create app-readable recommendation outputs, promote artifacts, modify rookie framework files, use external/ranking/projection sources, or open Phase 5B.
