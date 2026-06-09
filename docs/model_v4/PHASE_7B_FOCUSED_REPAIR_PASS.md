# Phase 7B Focused External Audit Repair Pass

Created: 2026-05-16

This pass patched only issues confirmed by the Phase 7 external audit triage.
All outputs remain review-only. Active War Board, My Team, draft, and final
decision surfaces were not promoted or unlocked.

## Repairs Applied

| Issue | Classification | Repair |
| --- | --- | --- |
| Incoming rookies with no evidence showed strong confidence | confirmed bug | Component-level missing-evidence warnings now feed confidence, and incoming rookies missing production, first-down, usage, snap, projection, age, and young-prior evidence are capped at weak confidence. |
| Incoming-rookie prior policy was ambiguous | confirmed policy gap | Incoming rookies use only sourced prospect/rookie prior evidence. If that evidence is missing, they remain weak/review until rookie-board data exists. |
| 1QB QB suppression still let QBs behave too much like superflex assets | confirmed formula issue | QB `position_scarcity_suppression` is now a small exception score, and the QB weight mix makes the 1QB replacement/suppression lane the largest QB lane. |
| QB fixture coverage was too light | confirmed fixture gap | Added elite-QB-vs-core-RB/WR and Lamar roster-sensitivity sanity fixtures. |

## Current Review-Only Results

| Check | Result |
| --- | --- |
| Incoming rookie confidence | All incoming rookies with no evidence are weak, not strong. |
| QB sanity fixtures | 31 of 31 sanity fixtures ready. |
| Named player review | 19 of 19 players matched. Three review rows remain: Luther Burden, Kaleb Johnson, Keenan Allen. |
| Movement audit | 68 meaningful movement rows, 10 large movement rows, 0 unexpected movement rows. |
| Active rankings promoted | false |
| Decision-ready unlocked | false |

## Key Artifacts

- Preview outputs: `local_exports/model_v4/review_only_latest/v4_preview_outputs.csv`
- Receipt rows: `local_exports/model_v4/review_only_latest/v4_receipt_rows.csv`
- Sanity fixtures: `docs/model_v4/PHASE_7B_SANITY_FIXTURE_RESULTS.md`
- Named player review: `docs/model_v4/PHASE_7B_NAMED_PLAYER_REVIEW.md`
- Movement audit: `docs/model_v4/PHASE_7B_MOVEMENT_AUDIT.md`

## Important Guardrails

- Market value remains excluded from Dynasty Asset Value.
- League rank remains rule context only.
- Route metrics remain unavailable unless a licensed structured source exists.
- Incoming rookies without sourced rookie-board data remain weak/review.
- V4 remains review-only until a separate promotion decision.
