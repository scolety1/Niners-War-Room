# Sparse-History Overlay Candidate Remains Primary / Stop V1

## Verdict

`GREEN_SPARSE_HISTORY_OVERLAY_PRIMARY_STOP_PACKET_READY`

## Purpose

This closeout packet preserves the accepted Overlay Candidate Batch Rule Test V1 result and confirms that the sparse-history overlay candidate remains the primary review-only overlay candidate.

This is closeout and preservation only. It did not run new overlays, run formulas, run rule tests, stack overlays, tune thresholds, run ranking simulation, change production rankings, change app/runtime/model behavior, promote sources, push, merge, write to canonical `local_exports`, approve production/model-use, or create hidden sort/recommendation logic.

## Verified Inputs

- Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`
- Prior overlay batch commit verified: `4b5f9c68970b0487ccf147be920b1051be4455fb`
- Prior overlay-library commit verified: `d9ec52781d682b7bee116b7896fef678b9df1552`

## Final Overlay Decision

Primary overlay candidate preserved:

- `REFINE_005_A_EARLY_ROLE_015`

Status:

- `PRIMARY_REVIEW_ONLY_OVERLAY_CANDIDATE`

Accepted primary evidence:

- Net miss reduction: `16`
- Misses resolved: `25`
- New misses created: `9`
- False-negative reduction: `8`

The broader overlay batch did not improve on this candidate. No tested overlay beat `REFINE_005_A_EARLY_ROLE_015` on net miss reduction or false-negative reduction.

## Overlay Batch Outcome

The batch tested five overlay families:

- `OVERLAY_001_SPARSE_EARLY_ROLE_BREAKOUT`
- `OVERLAY_002_AVAILABILITY_REBOUND`
- `OVERLAY_003_STARTER_DEPTH_PROMOTION`
- `OVERLAY_004_SNAP_GROWTH_ROLE_PROMOTION`
- `OVERLAY_008_DRAFT_CAPITAL_WITH_ROLE`

Windows tested:

- full-history `2013-2025`
- broad-window `2014-2025`
- partial-window `2022-2025`

Primary-overlay policy:

- Discovery-priority non-stacking policy: `001 > 002 > 003 > 004 > 008`
- All eligibility was recorded.
- Only one primary overlay was applied per player-season.

Best overall batch row:

- Primary-policy application on PYF full-history
- Net miss reduction: `8`
- Misses resolved: `14`
- New misses: `6`
- False-negative reduction: `4`
- False-positive reduction: `4`
- Spearman delta: `-0.001`

Best individual overlay family:

- `OVERLAY_008_DRAFT_CAPITAL_WITH_ROLE`
- Net miss reduction: `6`
- False-negative reduction: `3`
- False-positive reduction: `3`
- Spearman delta: `0.000`

No `PROMISING_REVIEW_ONLY_OVERLAY` was found in this batch.

## Stop Decision

Active overlay experimentation should stop unless the user explicitly authorizes a new direction.

Stop rules preserved:

- Do not test more overlay families.
- Do not stack overlays.
- Do not integrate overlays into rankings.
- Do not run ranking simulation.
- Do not promote sparse-history overlay to production/model-use.

Review-only ranking simulation remains not justified.

## Gates

- Production/model-use: blocked.
- Rankings integration: blocked.
- App/runtime behavior: unchanged.
- Source promotion: blocked.
- Push/merge: not performed.

## Future Options

Future options are preserved for user review only:

1. Manual inspection of sparse-history overlay evidence.
2. Docs-only push/merge-readiness of local review packets.
3. Later review-only overlay simulation readiness gate, only after explicit user approval.
4. Non-model NWR work.
5. New data acquisition only if explicitly authorized.
