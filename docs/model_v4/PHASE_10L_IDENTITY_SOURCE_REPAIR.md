# Phase 10L Identity And Source Repair

Generated: 2026-05-17

## Purpose

Phase 10L applies the first focused repair from the external Phase 10 data-spine
audit. The audit correctly found that duplicate-name college players could
contaminate historical rookie backtest rows. This phase tightens historical
college evidence admission before any formula work.

No active rankings, My Team, War Board, formulas, or readiness gates were
changed.

## Audit Finding Addressed

The historical rookie backtest matrix had admitted college production rows from
the same normalized name after the player's NFL draft year. Examples included
different players named Elijah Moore and Mason Taylor.

Those rows are now quarantined before matrix generation unless they satisfy both
rules:

- college evidence season is strictly before the NFL draft year
- source college/team is compatible with the drafted player's recorded college
  when the source exposes a team field

Rows failing those checks are not silently joined. They receive review warnings
such as:

- `historical_college_evidence_after_draft_year_quarantined`
- `college_team_mismatch_needs_transfer_validation_quarantined`
- `same_name_collision_possible_college_evidence_quarantined`

## Evidence Matrix Changes

Latest matrix version:

- `model_v4_phase_10l_identity_source_repair_0.1.0`

Regenerated outputs:

- `local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/prospect_current_feature_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/source_coverage_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/warning_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/evidence_matrix_summary.csv`

Current summary:

- NFL current player rows: 80
- Current prospect rows: 233
- Admitted current prospect identities: 201
- Review-only current prospect identities: 32
- Historical rookie backtest rows: 395
- Source coverage rows: 3,933
- Warning rows: 1,842
- Duplicate entity rows: 0
- Market leakage violations: 0
- Fake-zero missing violations: 0
- Ambiguous join rows: 0
- Historical post-draft college evidence violations: 0
- Status: `review_required_before_formula_design`

The status remains review-required because 32 current prospects still have
duplicate-name, position, or missing-evidence identity blockers. That is
intentional: formula work may consume only the admitted current-prospect
identity spine and must leave the review report out until those players are
resolved.

## Additional Safety Repairs

- Review-only replacement/VORP previews were moved out of
  `derived_evidence_json` and into context fields.
- Raw source table `rank` fields are stripped from factual, derived, and
  prospect-prior evidence snapshots.
- Semantic QA now counts historical college evidence with season greater than
  or equal to draft year.
- Duplicate-name regression tests now cover Elijah Moore, Mason Taylor, and
  Caleb Williams examples.
- Current prospect rows now receive admitted identity statuses only when
  name, position, draft year, and college context are source-compatible.
- Formula-facing identity outputs were added:
  - `local_exports/model_v4/evidence_matrices/latest/admitted_current_prospect_identity_spine.csv`
  - `local_exports/model_v4/evidence_matrices/latest/current_prospect_identity_review_report.csv`
- First-down and return canonicalization now write matched-only admitted views:
  - `local_exports/model_v4/first_downs/latest/admitted_rushing_first_downs.csv`
  - `local_exports/model_v4/first_downs/latest/admitted_receiving_first_downs.csv`
  - `local_exports/model_v4/returns/latest/admitted_return_scoring_evidence.csv`
- The source trust contract now includes field-level scoring/talent/role/admission
  flags for first-down and return data. Return production is direct scoring
  only, not talent or role evidence.

## Remaining Formula Blocker

Do not start full formula design yet.

The duplicate-name historical leakage is repaired, and 201 current prospect
identities now have an admitted spine. The remaining 32 current prospects should
be resolved or explicitly excluded before a rookie formula consumes the full
prospect universe.

The next focused phase should:

- resolve or quarantine the 32 current prospect identity review rows
- keep unresolved duplicate-name players review-only
- regenerate evidence matrices and rerun the pre-formula audit packet

## Validation

Focused validation:

- `pytest tests/test_model_v4_evidence_matrix_service.py tests/test_model_v4_first_down_canonicalization_service.py tests/test_model_v4_return_canonicalization_service.py tests/test_model_v4_source_trust_contract_service.py -q`
- Result: 26 passed
- `ruff check` on touched Phase 10 services/scripts/tests
- Result: passed

Generated matrix spot check:

- historical post-draft college evidence violations: 0
- Elijah Moore no longer carries 2025 Florida State evidence
- Mason Taylor no longer carries 2025 Tennessee Tech evidence
- Caleb Williams no longer carries 2025 Pittsburgh evidence
