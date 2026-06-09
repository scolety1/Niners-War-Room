# Phase 6 Promotion Decision

Status: review-only.

Decision: Model v4 should move to app promotion planning after the Phase 6 external audit is reviewed. It should not be promoted into active War Board, My Team, Rankings, Draft Board, League Targets, or Trade Lab surfaces yet.

This is not a formula-failure decision. The internal Phase 6 evidence is strong enough to stop doing blind formula repair. The remaining blockers are promotion, confidence, external-audit, and app-integration blockers.

## Evidence Reviewed

- `docs/model_v4/PHASE_6_MOVEMENT_AUDIT.md`
- `docs/model_v4/PHASE_6_SANITY_FIXTURE_RESULTS.md`
- `docs/model_v4/PHASE_6_NAMED_PLAYER_REVIEW.md`
- `docs/model_v4/PHASE_6_REMAINING_BLOCKERS.md`
- `local_exports/model_v4/review_only_latest/v4_preview_outputs.csv`
- `local_exports/model_v4/review_only_latest/v4_source_coverage_rows.csv`
- `local_exports/model_v4/review_only_latest/v4_receipt_rows.csv`
- `local_exports/model_v4/review_only_latest/v4_warning_rows.csv`
- Current roster-decision readiness gate for `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

No post-Phase-6 external audit result was available locally at the time of this decision. The Phase 6 packet is available at:

`local_exports/model_v4/audit_packets/model_v4_phase6_formula_patch_external_audit_20260516T054432Z.zip`

## Phase 6 Internal Audit Summary

| Check | Result | Promotion Meaning |
| --- | --- | --- |
| Movement audit | 80 rows, 63 meaningful movement rows, 6 large movement rows, 0 unexpected movement rows | Formula patch movement is explainable by receipts. |
| Sanity fixtures | 29 ready, 0 review, 0 blocked | No sanity fixture currently blocks formula confidence. |
| Named player review | 19 of 19 requested players matched | Named audit is complete. |
| Named inspection findings | 5 ready, 1 review | The only review finding is weak-evidence young-player bridge rows. |
| Source coverage rows | 660 rows: 518 covered, 92 missing, 50 not applicable | Missing evidence is visible, not hidden. |
| Receipt rows | 660 rows | Preview values are receipt-backed. |
| Warning rows | 1491 rows, all review severity | Warnings are visible and not treated as blockers by themselves. |
| Confidence labels | 5 strong, 31 usable, 33 review, 11 weak | Confidence is not pretending every player is equally trustworthy. |

## Live Gate Recheck

The current app gate still evaluates the legacy active data pack, not a promoted v4 app surface.

Roster-decision gate result:

- Badge: `Roster Decisions Review Only`
- Ready: false
- Blocked: 0
- Review: 2
- Ready rows: 8

Review rows:

| Gate | Status | Why It Matters | Next Action |
| --- | --- | --- | --- |
| Model v4 rebuild freeze | review | Legacy roster action buckets may be inspected, but cannot be trusted as final decisions while v4 is being rebuilt. | Finish v4 promotion planning, roster thresholds, receipts, and app wiring. |
| Active roster model output quality reviewed | review | The legacy selected-roster rows still require model/source review, so old Core/Bubble/Shop labels must not be treated as action calls. | Replace or quarantine legacy action labels when v4 is promoted. |

Pre-decision checklist result:

- Roster Decisions Ready: `Roster Decisions Review Only`
- Draft Ready: `Draft Pool Needs Data`
- Final Money Decisions Ready: `Needs Data`

The checklist rows are otherwise ready under the current legacy gate, but that does not prove v4 can power the app because v4 has not been promoted into active decision surfaces.

## Remaining Issue Classification

| Issue | Classification | Roster-Decision Impact | Draft/Final Impact | Decision |
| --- | --- | --- | --- | --- |
| Post-Phase-6 external audit not reviewed | confidence blocker | Blocks promotion into trusted roster decisions. | Blocks final trust. | Run and triage the Phase 6 external audit before promotion. |
| v4 preview not wired into active app decision surfaces | UI blocker / integration blocker | Blocks using v4 inside My Team and War Board. | Blocks all app-level promotion. | Move to app promotion planning, not more formula tuning. |
| Model v4 rebuild freeze is active | UI blocker / process blocker | Keeps roster labels review-only. | Keeps all readiness labels locked. | Keep active until v4 app adapter and gate pass. |
| Legacy Core/Bubble/Shop labels still exist in old surfaces | UI blocker | Could mislead roster decisions if read as v4 output. | Not relevant to draft until promoted. | Quarantine or replace during v4 promotion. |
| Young-player bridge weak-evidence rows | confidence blocker / accepted limitation | Affects young players with little or no NFL production, first-down, usage, or snap evidence. | Affects rookies and young draft targets too. | Keep visible warnings; do not boost draft capital blindly. |
| Route metrics unavailable from safe free/public structured sources | source gap accepted limitation | Lowers confidence for WR/TE role precision. | Also affects draft targets. | Keep unavailable; do not use restricted route data as real evidence. |
| Snap share is proxy-only | source gap accepted limitation | Useful role signal but not route participation. | Same limitation for draft. | Keep labeled as proxy-only. |
| Projection first downs estimated from history | confidence blocker / accepted limitation | Projection component is useful but not direct first-down evidence. | Draft and final decisions need the same warning. | Keep estimated labels and confidence penalty. |
| Injury context weak unless sourced | source gap accepted limitation | Should not boost confidence. | Same limitation for draft/final. | Keep context-only unless sourced. |
| Official released veterans and final draft pool incomplete | data blocker | Does not block pre-declaration roster review. | Blocks Draft Ready and Final Money Decisions. | Keep draft/final blocked. |

## Formula Decision

No new formula blocker was found in Phase 6D.

Reasons:

- Phase 6 movement has zero unexpected rows.
- All 29 sanity fixtures are ready.
- Named player review found no RB/WR, QB, TE, aging-veteran, market-isolation, or league-rank formula blocker.
- The only named-player inspection review is weak-evidence young-player bridge behavior, which is a confidence/source limitation, not proof that draft capital or young-player formulas should be tuned.

Therefore the next step should not be another broad formula patch pass.

## Promotion Decision

Model v4 should remain review-only today.

Recommended next state:

- Move to app promotion planning after external audit triage.
- Do not mark Roster Decisions Ready yet.
- Do not mark Draft Ready.
- Do not mark Final Money Decisions Ready.

The clean path is:

1. Review the Phase 6 external audit packet.
2. Triage any findings into bug, data gap, formula concern, UI blocker, or accepted limitation.
3. If no external-audit formula/data blockers remain, build a v4 app adapter.
4. Wire v4 into My Team and War Board in a clearly labeled v4 preview mode.
5. Replace legacy action labels with v4 roster-decision language and receipts.
6. Add a v4-specific roster decision gate that checks all Niners roster players have v4 values, receipts, confidence labels, source warnings, and top-five release context.
7. If that v4 roster gate passes, mark only `Roster Decisions Ready`.
8. Keep Draft Ready and Final Money Decisions blocked until official released veterans, draft-pool, and final gates pass.

## Next Patch List

| Priority | Patch | Why |
| --- | --- | --- |
| 1 | Phase 6 external audit triage | Independent audit is the last confidence check before promotion planning. |
| 2 | v4 app promotion plan | The formula preview is not useful to the user until it powers inspectable app surfaces. |
| 3 | v4 My Team preview adapter | Roster decisions are the immediate deadline use case. |
| 4 | v4 roster-decision labels and thresholds | Legacy Core/Bubble/Shop language caused confusion and should not survive promotion unchanged. |
| 5 | v4 receipt-first My Team UI | Every roster decision must show value drivers, source warnings, confidence, and top-five rule context. |
| 6 | v4 roster readiness gate | Only mark roster ready after the promoted v4 surface passes its own gate. |
| 7 | Draft-pool/released-veteran gate later | Draft readiness is separate from pre-declaration roster readiness. |

## Final Call

Proceed to external-audit triage and app promotion planning. Do not do another formula patch pass unless the external audit or v4 app adapter reveals a receipt-backed formula bug.

Roster decisions are not officially ready in the app yet because v4 is still review-only and not promoted into active decision surfaces.
