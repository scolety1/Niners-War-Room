# Model v4 Phase 8 Checkpoint

Created: 2026-05-17

Phase 8 makes Model v4 visible in the app as a shadow/review-only model. It
does not promote Model v4 into the active War Board, My Team, Rankings, Draft
Board, League Targets, Trade Lab, or any readiness gate.

## Current V4 Preview State

Source: `local_exports/model_v4/review_only_latest/v4_preview_summary.json`

| Field | Value |
| --- | --- |
| Review status | `review_only` |
| Formula version | `model_v4_review_only_0.2.1` |
| Preview engine | `model_v4_preview_engine_review_only_0.1.0` |
| Computed at | `2026-05-17T01:15:12Z` |
| Preview rows | 80 |
| Component rows | 660 |
| Receipt rows | 660 |
| Source coverage rows | 660 |
| Warning rows | 2123 |
| Active rankings overwritten | false |
| App promotion | false |
| Decision ready unlocked | false |
| Draft ready unlocked | false |
| Final money ready unlocked | false |

## Shadow Surfaces Added

| Surface | Status | What it allows |
| --- | --- | --- |
| Model Lab V4 overview | visible | Inspect preview status, formula version, row counts, guard rows, preview rankings, component receipts, source coverage, warnings, sanity fixtures, and named-player review. |
| V4 Shadow War Board | visible | Inspect V4 overall/position ranks, Dynasty Asset Value, confidence labels, warnings, unavailable sections, and filters without changing active War Board rows. |
| V4 Shadow My Team | visible | Join Niners roster/rank context to V4 preview values while keeping rule context separate from football value. |
| V4 Receipts Drilldown | visible | Inspect selected-player V4 receipt groups, raw fields, normalized scores, weights, contributions, source status, warnings, and unavailable reasons. |
| Old vs V4 Comparison | visible | Compare active ranks/values/confidence/warnings against V4 shadow ranks/values/confidence/warnings and flag large unexplained movement. |
| Promotion Blockers | visible | Show what still prevents V4 from becoming the live model, grouped by blocker class. |

## Browser Smoke

Browser smoke was run against the local Streamlit app on `localhost:8501`.

| Surface | Result |
| --- | --- |
| Model Lab V4 overview | Passed after opening the `Model v4 Preview` tab. No traceback. |
| V4 Shadow War Board | Passed. Review-only shadow banner visible. No traceback. |
| V4 Shadow My Team | Passed. Review-only shadow banner visible. No traceback. |
| V4 Receipts Drilldown | Passed. Receipt drilldown section visible with selected-player prompt. No traceback. |
| Old vs V4 Comparison | Passed. Section and review-only banner visible. No traceback. |
| Promotion Blockers | Passed. Blocker panel and review-only banner visible. No traceback. |
| Active Rankings | Passed smoke check; page remains review-only and did not switch to V4. No traceback. |

## Guardrail Confirmation

| Guardrail | Status | Evidence |
| --- | --- | --- |
| Active War Board unchanged | confirmed | V4 appears only in `V4 Shadow War Board`; active War Board still loads active data-pack rows. |
| Active My Team unchanged | confirmed | V4 appears only in `V4 Shadow My Team`; active My Team is not replaced. |
| Active Rankings unchanged | confirmed | Rankings page remains active/review-only and does not read V4 as live rankings. |
| No readiness gates unlocked | confirmed | Preview summary has `decision_ready_unlocked=false`, `draft_ready_unlocked=false`, and `final_money_ready_unlocked=false`. |
| V4 remains review-only | confirmed | Preview summary is `review_only`; every Phase 8 surface uses review-only language. |

## Current Promotion Blockers

| Group | Count | Blocks app promotion | Blocks final decision-ready | Notes |
| --- | ---: | ---: | ---: | --- |
| Data blocker | 1 | 1 | 1 | Caleb Williams is missing from current V4 QB-control preview. |
| Formula blocker | 0 | 0 | 0 | No current formula blocker is shown after Phase 7 repairs. |
| Confidence blocker | 1 | 1 | 1 | Source-limited incoming/young players remain review/blocked. |
| Source limitation | 1 | 0 | 1 | Route metrics are unavailable from safe free/public structured sources. |
| UI blocker | 2 | 2 | 2 | Shadow app review is not accepted yet; roster-decision gate is not unlocked. |
| Accepted limitation | 1 | 0 | 0 | Estimated first-down projections remain clearly labeled and visible. |

Specific blocker rows currently shown:

- Caleb Williams missing from current V4 QB-control preview.
- Source-limited incoming/young players.
- Unavailable route metrics.
- Shadow app review not accepted yet.
- No roster-decision gate unlock yet.
- Estimated first-down projections.

## What Can Be Reviewed Now

You can now review V4 without trusting it as live output:

- Which players V4 values highest and lowest.
- Which V4 rows have weak, review, or blocked confidence.
- Why a selected V4 row is ranked where it is.
- Which sections are missing, proxy-only, estimated, or unavailable.
- How V4 differs from the current active model.
- Which blockers must be cleared or explicitly accepted before promotion.

## What Cannot Be Trusted Yet

V4 still cannot be used as the live roster-decision model because:

- Caleb Williams is missing from QB-control preview coverage.
- Young/incoming players still have source-limited confidence.
- Route metrics remain unavailable and must not be faked.
- Shadow app review has not been accepted by the user.
- The roster-decision gate has not been run/unlocked on a promoted V4 model.

## Phase 9 Recommendation

Next step: user review and targeted repair triage, not a broad formula rebuild.

Recommended Phase 9 shape:

1. User reviews V4 Shadow War Board, Shadow My Team, receipt drilldowns, Old vs V4, and Promotion Blockers.
2. Capture suspicious rankings or confusing receipts from that review.
3. Patch only confirmed data, identity, receipt, blocker-classification, or UI issues.
4. Add Caleb Williams or document why he is not required for app promotion.
5. Re-run the shadow smoke and promotion blocker panel.
6. Only then decide whether to run another external audit or move to a controlled roster-decision promotion gate.

Do not promote V4 into active My Team or War Board until Phase 9 review is
accepted and the formal roster-decision gate passes.

## Verification

- Focused Phase 8 service/UI tests passed.
- Full test suite passed: 847 tests.
- Static check passed: `ruff check .`.
