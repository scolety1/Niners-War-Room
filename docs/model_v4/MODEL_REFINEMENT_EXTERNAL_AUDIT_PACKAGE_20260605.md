# Model Refinement External Audit Package v2

Date: 2026-06-05

Mode: review-only refinement prep.

This package is for an external ChatGPT Pro audit of the Niners War Room Model
v4 football-quality readiness work completed after the source-routing repair
and post-audit cleanup gates. It is an evidence package, not a formula tuning
packet.

## Audit Goal

Assess whether the model is ready for cautious human judgment and paper-tracked
decision trials, and identify blockers before any formula work. The auditor
should verify that the reports are internally coherent, source-aware,
review-only, and clear about what must be fixed or judged before tuning.

The auditor should not implement fixes, tune formulas, refresh generated
outputs, mutate app state, or turn review labels into final trade, cut, keep,
draft, buy, sell, defer, target, or start/sit recommendations.

## Current Baseline

- Repair gate and post-audit cleanup gate are complete for review-only use.
- Prior full-suite baseline from `POST_AUDIT_READINESS_HANDOFF_20260531.md`:
  `1214 passed`.
- Prior full lint baseline from the same handoff: `All checks passed!`.
- Recent refinement tasks R01-R25 were report/test focused.
- Current local bundled runtime for these refinement tasks lacked `pytest` and
  `ruff`; recent readback tests were run with direct stdlib runners plus
  `py_compile`.

## Primary Context Files

- `docs/model_v4/POST_AUDIT_READINESS_HANDOFF_20260531.md`
- `docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md`
- `docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md`
- `docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md`

## Refinement Evidence Reports

Read these in order:

1. `REFINEMENT_EVIDENCE_MAP_20260605.md`
2. `NAMED_PLAYER_AUDIT_ROSTER_20260605.md`
3. `CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md`
4. `LEGACY_VS_CURRENT_SENTINEL_EXPANSION_20260605.md`
5. `TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md`
6. `RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md`
7. `QB_1QB_DISCIPLINE_REPORT_20260605.md`
8. `TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md`
9. `VETERAN_AGE_WINDOW_AUDIT_20260605.md`
10. `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md`
11. `INJURY_STATUS_RISK_AUDIT_20260605.md`
12. `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`
13. `ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`
14. `PICK_VALUE_LADDER_AUDIT_20260605.md`
15. `PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md`
16. `EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md`
17. `DECISION_BOARD_COHERENCE_AUDIT_20260605.md`
18. `ORDERED_SANITY_FIXTURE_SPEC_20260605.md`
19. `NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md`
20. `SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md`
21. `DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md`
22. `FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md`

## UX Smoke Checklists

- `PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md`
- `DRAFT_ROOM_UX_SMOKE_CHECKLIST_20260605.md`
- `EXTERNAL_ASSET_DECISION_BOARD_UX_SMOKE_CHECKLIST_20260605.md`

## Readback Tests To Inspect

These tests are refinement readback guards, not football-formula tests:

- `tests/test_refinement_evidence_map.py`
- `tests/test_named_player_audit_roster.py`
- `tests/test_current_player_value_extraction_report.py`
- `tests/test_legacy_vs_current_sentinel_expansion.py`
- `tests/test_top_bottom_current_player_sanity_scan.py`
- `tests/test_rb_wr_cross_position_balance_report.py`
- `tests/test_qb_1qb_discipline_report.py`
- `tests/test_te_no_premium_discipline_report.py`
- `tests/test_veteran_age_window_audit.py`
- `tests/test_young_player_evidence_audit.py`
- `tests/test_injury_status_risk_audit.py`
- `tests/test_rookie_board_top_cluster_audit.py`
- `tests/test_rookie_low_evidence_watchlist_audit.py`
- `tests/test_pick_value_ladder_audit.py`
- `tests/test_pick_vs_player_neighborhood_audit.py`
- `tests/test_external_asset_reviews_sanity_audit.py`
- `tests/test_decision_board_coherence_audit.py`
- `tests/test_player_board_ux_smoke_checklist.py`
- `tests/test_draft_room_ux_smoke_checklist.py`
- `tests/test_external_asset_decision_board_ux_smoke_checklist.py`
- `tests/test_ordered_sanity_fixture_spec.py`
- `tests/test_non_formula_sanity_fixtures.py`
- `tests/test_suspicious_ranking_triage_report.py`
- `tests/test_data_source_gap_triage_report.py`
- `tests/test_formula_candidate_proposal_packet.py`
- `tests/test_model_refinement_external_audit_package.py`

## Known Sentinel Checks

The auditor should explicitly verify:

- Keenan Allen legacy active-pack `82.4` is comparison-only and cannot become
  the primary Player Board Model Value.
- Darius Slayton legacy active-pack `78.88` is comparison-only and cannot become
  the primary Player Board Model Value.
- Blank current-player primary rows remain fail-closed/manual-only:
  Jeremiyah Love, Carnell Tate, Jordyn Tyson, Fernando Mendoza, Kenyon Sadiq.
- `2026 5.04` remains manual-only with no exact baseline or invented
  equivalence.
- Market, ADP, rankings, projections, consensus, startup, and trade-calculator
  context remain display-only or excluded from private value.

## Main Review Areas

| Area | Evidence Files | What To Judge |
|---|---|---|
| Source readiness | `DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md`, `CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md` | Are source gaps and identity/team warnings separated from formula candidates? |
| Suspicious rankings | `SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md`, `TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md` | Are suspicious rows bucketed without becoming final recommendations? |
| QB/TE format context | `QB_1QB_DISCIPLINE_REPORT_20260605.md`, `TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md` | Are 1QB and no-premium TE assumptions visible and review-only? |
| RB/WR balance | `RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md`, `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md` | Are cross-position concerns framed as review prompts, not formula changes? |
| Veterans/status | `VETERAN_AGE_WINDOW_AUDIT_20260605.md`, `INJURY_STATUS_RISK_AUDIT_20260605.md` | Are age, identity, team, and source warnings visible before judgment? |
| Rookies/picks | `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`, `ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`, `PICK_VALUE_LADDER_AUDIT_20260605.md`, `PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md` | Are rookie and pick rows blocked from final draft/trade actions? |
| External/Decision Board | `EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md`, `DECISION_BOARD_COHERENCE_AUDIT_20260605.md` | Are external assets and aggregate rows review-only with source receipts? |
| Formula candidates | `FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md` | Are candidates proposal-only with no implementation? |

## Candidate Formula Areas For Audit Only

Do not tune these during the audit. Verify whether the evidence packet frames
them well enough for future human-approved experiments:

- FC01: No-premium TE ceiling clarity.
- FC02: 1QB spread and cap clarity.
- FC03: RB/WR cross-position balance.
- FC04: Veteran age/status confidence shape.
- FC05: Young-player evidence sensitivity.
- FC06: Rookie source-limited prior handling.
- FC07: Pick-neighborhood explanation and comparison shape.

## Suggested Focused Checks

If the external environment has `pytest` and `ruff`, run:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_non_formula_sanity_fixtures.py tests\test_suspicious_ranking_triage_report.py tests\test_data_source_gap_triage_report.py tests\test_formula_candidate_proposal_packet.py tests\test_model_refinement_external_audit_package.py -q
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m ruff check tests\test_non_formula_sanity_fixtures.py tests\test_suspicious_ranking_triage_report.py tests\test_data_source_gap_triage_report.py tests\test_formula_candidate_proposal_packet.py tests\test_model_refinement_external_audit_package.py
```

If those tools are unavailable, inspect the tests directly as readback
assertions and report the tooling gap.

## Requested External Verdict

Return exactly one top-level verdict:

- `refinement_packet_ready_for_human_review_only`
- `needs_repair_before_human_review`
- `needs_source_cleanup_before_formula_tuning`
- `formula_tuning_not_ready`

Also include:

- Blockers.
- High-priority issues.
- Medium/low issues.
- Missing evidence or unclear assumptions.
- Whether the packet keeps formula candidates proposal-only.
- Whether any report accidentally becomes a recommendation surface.
- Exact file/test references for every finding.

## Residual Risks

- This packet does not prove football accuracy.
- This packet does not authorize money decisions.
- This packet does not refresh generated model outputs.
- This packet does not import new player/team/injury/projection/market data.
- This packet does not tune formulas.
- Human judgment is still required before any real roster, draft, trade, or
  keeper decision.
