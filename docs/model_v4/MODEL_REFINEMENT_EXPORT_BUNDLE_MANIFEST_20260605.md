# Model Refinement Export Bundle Manifest

Date: 2026-06-05

Mode: review-only refinement prep.

Bundle path:

- `docs/model_v4/MODEL_REFINEMENT_EXPORT_BUNDLE_20260605.zip`

Purpose: package the Model v4 refinement reports, audit prompt, user worksheet,
queue, readiness rerun, and morning handoff for external audit and human review.
This bundle is not a formula tuning packet, not a generated model output refresh, and not a recommendation artifact.

## Included Core Context

- `docs/model_v4/POST_AUDIT_READINESS_HANDOFF_20260531.md`
- `docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md`
- `docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md`
- `docs/model_v4/TOMORROW_MORNING_HANDOFF_20260605.md`
- `docs/model_v4/FINAL_OVERNIGHT_READINESS_RERUN_20260605.md`

## Included Audit Package

- `docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md`
- `docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md`
- `docs/model_v4/FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md`
- `docs/model_v4/DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md`
- `docs/model_v4/SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md`

## Included Human Review Worksheet

- `docs/model_v4/USER_JUDGMENT_WORKSHEET_20260605.md`
- `docs/model_v4/USER_JUDGMENT_WORKSHEET_20260605.csv`

## Included Refinement Reports

- `docs/model_v4/REFINEMENT_EVIDENCE_MAP_20260605.md`
- `docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md`
- `docs/model_v4/CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md`
- `docs/model_v4/LEGACY_VS_CURRENT_SENTINEL_EXPANSION_20260605.md`
- `docs/model_v4/TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md`
- `docs/model_v4/RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md`
- `docs/model_v4/QB_1QB_DISCIPLINE_REPORT_20260605.md`
- `docs/model_v4/TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md`
- `docs/model_v4/VETERAN_AGE_WINDOW_AUDIT_20260605.md`
- `docs/model_v4/YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md`
- `docs/model_v4/INJURY_STATUS_RISK_AUDIT_20260605.md`
- `docs/model_v4/ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`
- `docs/model_v4/ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`
- `docs/model_v4/PICK_VALUE_LADDER_AUDIT_20260605.md`
- `docs/model_v4/PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md`
- `docs/model_v4/EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md`
- `docs/model_v4/DECISION_BOARD_COHERENCE_AUDIT_20260605.md`
- `docs/model_v4/ORDERED_SANITY_FIXTURE_SPEC_20260605.md`
- `docs/model_v4/NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md`

## Included UX Smoke Checklists

- `docs/model_v4/PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md`
- `docs/model_v4/DRAFT_ROOM_UX_SMOKE_CHECKLIST_20260605.md`
- `docs/model_v4/EXTERNAL_ASSET_DECISION_BOARD_UX_SMOKE_CHECKLIST_20260605.md`

## Included Readback Tests

- `tests/test_non_formula_sanity_fixtures.py`
- `tests/test_suspicious_ranking_triage_report.py`
- `tests/test_data_source_gap_triage_report.py`
- `tests/test_formula_candidate_proposal_packet.py`
- `tests/test_model_refinement_external_audit_package.py`
- `tests/test_user_judgment_worksheet.py`
- `tests/test_final_overnight_readiness_rerun.py`
- `tests/test_tomorrow_morning_handoff.py`
- `tests/test_model_refinement_export_bundle.py`

## Excluded

- Source code implementation files.
- Active data packs.
- Generated model output CSVs outside the human worksheet.
- Git staging or commits.
- Any formula tuning or experiment output.

## Guardrails

- Do not tune formulas from this bundle.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated model outputs, or user-entered draft
  state.
- Do not turn review labels into final recommendations.
