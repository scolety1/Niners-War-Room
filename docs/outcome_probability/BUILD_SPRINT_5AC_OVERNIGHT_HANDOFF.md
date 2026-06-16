# Build Sprint 5AC: Overnight Outcome Probability Handoff

## Verdict

`OVERNIGHT_HANDOFF_READY`

No blocker, safety risk, app-output risk, leakage risk, or unsafe test failure stopped the run.

## Starting Checkpoint

Sprint 5X was already complete and committed before this overnight continuation.

Starting checkpoint:

- Sprint 5X verdict: `EXPANDED_HISTORICAL_ROWS_READY`
- Commit: `bfafb26 Rebuild NWR historical outcome rows for 2020 to 2022`
- Expanded trainable universe: 2,118 rows across 2020-2024
- 2020-2022 legality checks: passed
- Feature missingness: 0
- Leakage issues: 0
- Duplicate row IDs: 0

Sprint 5X was not rerun.

## Sprints Completed In This Run

| Sprint | Verdict | Commit |
| --- | --- | --- |
| 5Y Expanded Calibration Readiness | `READY_FOR_5Z_EXPANDED_INTERNAL_VALIDATION` | `74624f5 Reassess NWR calibration readiness on expanded history` |
| 5Z Expanded Internal Validation Package | `EXPANDED_INTERNAL_VALIDATION_PASS_WITH_WARNINGS` | `418fb73 Run expanded NWR internal validation package` |
| 5AA Calibration Feasibility Gate | `CALIBRATION_FEASIBILITY_READY_FOR_INTERNAL_ONLY_AUDIT` | `d15aed7 Gate NWR internal calibration feasibility` |
| 5AB Expanded Package Adversarial Audit | `EXPANDED_PACKAGE_AUDIT_PASS` | `3449f16 Audit expanded NWR internal model package` |

This handoff is Sprint 5AC.

## Files Committed During This Run

- `docs/outcome_probability/BUILD_SPRINT_5Y_EXPANDED_CALIBRATION_READINESS.md`
- `docs/outcome_probability/BUILD_SPRINT_5Z_EXPANDED_INTERNAL_VALIDATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5AA_CALIBRATION_FEASIBILITY_GATE.md`
- `docs/outcome_probability/BUILD_SPRINT_5AB_EXPANDED_PACKAGE_ADVERSARIAL_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5AC_OVERNIGHT_HANDOFF.md`

## Local-Only Exports Created

Local exports were created but not committed:

- `local_exports/outcome_probability/sprint_5y_expanded_calibration_readiness/`
- `local_exports/outcome_probability/sprint_5z_expanded_internal_validation_package/`
- `local_exports/outcome_probability/sprint_5aa_calibration_feasibility_gate/`
- `local_exports/outcome_probability/sprint_5ab_expanded_package_adversarial_audit/`

## Checks Run

Repeated sprint checks used the bundled Python runtime because the shell `python` alias points to the Microsoft Store stub.

Checks run during the overnight continuation:

- `pytest tests/test_nwr_outcome_internal_model_package_service.py tests/test_nwr_outcome_feature_snapshot_service.py tests/test_nwr_outcome_base_rate_service.py tests/test_nwr_outcome_source_manifest_service.py tests/test_nwr_outcome_historical_row_factory.py tests/test_nwr_outcome_training_row_service.py tests/test_nwr_outcome_scoring_service.py tests/test_outcome_probability_build_packet.py -q`
  - Result: 87 passed
- `py_compile src/services/nwr_outcome_internal_model_package_service.py tests/test_nwr_outcome_internal_model_package_service.py`
  - Result: passed during Sprint 5Z
- `ruff check src/services/nwr_outcome_internal_model_package_service.py tests/test_nwr_outcome_internal_model_package_service.py`
  - Result: passed during Sprint 5Z
- `git diff --check`
  - Result: passed, with unrelated pre-existing line-ending warnings on outcome-column files
- `git status --short`
  - Reviewed before/after each sprint
- `git diff --stat`
  - Reviewed before commits

## Current Approved Internal Assets

- Expanded 2020-2024 `all_player_pre_week1` historical universe.
- 2,118 trainable rows.
- Renamed Sprint 5R feature schema.
- Feature lineage metadata.
- Source manifest policy for completed prior-season `player_stats.csv` facts.
- Supplemented internal v0 benchmark policy.
- Internal-only validation split:
  - Train: 2020-2022
  - Validation: 2023
  - Test: 2024
- Same-year outcomes only.

## Current Internal-Only Capabilities

Allowed internally:

- Aggregate outcome support diagnostics.
- Aggregate validation/test diagnostics.
- Internal-only regularized logistic mechanics.
- Future internal-only calibration audit for simple Platt or outcome-level mechanics, if the Sprint 5AA gate contract is followed.
- Aggregate bins and coefficient/feature sanity.

Still not allowed:

- Player-facing probabilities.
- App percentage values.
- App-readable probability tables.
- Rankings or rank sorting from outcome output.
- Decision automation.
- Model promotion or release.
- Production deployment.

## Stoplight

| Area | Status | Notes |
| --- | --- | --- |
| Historical rows | Green internal | Expanded 2020-2024 universe is ready for internal validation. |
| Feature schema | Green internal | Renamed Sprint 5R schema and lineage audit passed. |
| Internal logistic mechanics | Green with warnings | Aggregate-only validation package passed with warnings. |
| Calibration | Yellow internal-only | Future internal-only audit may start; production/app calibration remains blocked. |
| App display | Red blocked | No app percentages or player-facing probabilities allowed. |
| Rankings/decision automation | Red blocked | No ranking/sorting/automation from model outputs allowed. |
| Production release | Red blocked | Requires final leakage audit, release policy, display/confidence gates, HQ approval. |

## Exact Blockers Before App-Facing Probabilities

- Final leakage audit.
- Calibration validation and stability evidence.
- Confidence gate.
- App display gate.
- Release/model-card policy.
- Explicit HQ approval.
- Clear policy for `next_year_starter`, which remains partially observed/censored.
- Continued app/ranking isolation.

## What Codex Did Not Do

- Did not rerun Sprint 5X.
- Did not push.
- Did not deploy.
- Did not modify active app/ranking logic.
- Did not create app percentage values.
- Did not create public/player-facing probabilities.
- Did not create rankings.
- Did not create decision automation.
- Did not create app-readable probability tables.
- Did not promote or release any model artifact.
- Did not commit local exports.
- Did not stage unrelated dirty/untracked files.

## Must Not Be Done Next Without HQ Approval

- Wire internal outputs into app columns or player cards.
- Display percentages to users.
- Sort/rank players by internal outcome mechanics.
- Promote a model artifact.
- Treat internal calibration audit output as production probability.
- Use ADP, public rankings, projections, market/trade values, prior fantasy draft history, RotoWire projections/rankings/outlooks/values, legacy `private_score`, same-season final stats, or label supplement sources as prediction features.

## Recommended Next Step

Run a tightly scoped Sprint 5AD internal-only calibration audit, if HQ wants it, using the Sprint 5AA gate contract:

- Same-year outcomes only.
- Aggregate-only outputs only.
- No app/player-facing outputs.
- No production artifact.
- Stop on leakage, schema, metadata, or output-block failure.

Production/app modeling remains blocked.
