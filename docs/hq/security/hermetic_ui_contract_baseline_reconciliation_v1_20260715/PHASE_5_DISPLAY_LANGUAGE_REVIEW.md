# Phase-5 Display-Language Review

## Meaning of Phase 5

“Phase 5” in the failing test file refers to **Model v4.5 Phase 5: Clean Naming And Warning Cleanup**, not the current roadmap phase, Draft-Day V1, or a security phase. Its original authority is `docs/model_v4/MODEL_V4_5_PHASE_5_CLEAN_NAMING_WARNING_CLEANUP.md`.

The phase introduced human-readable display mappings and warning groups while preserving raw field names/codes in drilldowns and exports. The wording was user-facing at the time; the tests themselves are static source-text checks.

## Current ownership

- `app/pages/08_june15_review.py` remains the legacy Decision Board and still owns the governed `Warning Groups` / `Warning Details` presentation and raw `warning_flags` disclosure.
- `app/pages/06_draft_board.py` is registered as **Legacy Draft Prep** and now presents scouting-pool/legal-pool state, not the former Phase-5 multi-tab review layout.
- `app/pages/20_final_board_v1.py` is the current `/rankings` implementation and owns current ranking presets, filters, score context, and the Decision Trust Strip.

## Failure decisions

1. `test_phase5_default_tables_use_warning_groups_and_preserve_raw_drilldowns`: stale expectation. The repair keeps exact governed wording where it still communicates the legacy Decision Board states and keeps raw-code assertions. It does not require a later Draft Prep surface to recreate the superseded table layout.
2. `test_phase5_filter_controls_use_clean_language`: stale expectation. The repair checks the accepted current Dynasty Rankings filter vocabulary (`Dynasty Review`, `Market Context`, `Data Review`, `Advanced filters`, `Review needed`) and continues rejecting deprecated internal labels.
3. `test_main_score_tables_expose_score_disclosure_fields`: stale expectation. The repair checks the current raw score metadata plus the canonical six Decision Trust Strip labels rather than obsolete mappings inside a compatibility wrapper.

## Exact-string policy

Exact strings remain justified for governed state distinctions, canonical control labels, and shared trust-field labels. The repair does not replace state-specific language with generic text. It removes only assertions whose owning surface was superseded by later accepted product/navigation contracts.

Classification confidence: `HIGH`. Unresolved ambiguity: none.
