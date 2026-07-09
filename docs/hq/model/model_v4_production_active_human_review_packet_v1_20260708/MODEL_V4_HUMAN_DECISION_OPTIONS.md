# Model v4 Human Decision Options

This packet executes none of these options. It only makes the decision set explicit.

## Option 1: Keep Candidate / Review-Only

Status: safest default.

Pros:
- Preserves every existing guardrail.
- Avoids accidental production interpretation.
- Requires no app, model, ranking, or source-gate change.

Cons:
- Leaves the app-visible board in a confusing state if humans treat it as the main board.

Risk: low.

## Option 2: Approve Draft-Day Review Board Only

Status: possible human-use clarification, not production activation.

Pros:
- Recognizes that the current board is exactly reproducible.
- Allows practical review use while preserving non-production status.

Cons:
- Requires strong labeling to avoid implying proven accuracy or recommendation logic.

Risk: medium.

## Option 3: Approve App-Label Correction Packet

Status: recommended next lane.

Pros:
- Replaces ambiguous "not active rankings" language with a more precise candidate/review-only display label if humans approve.
- Can be done without changing scores, ranks, formula weights, default sort, hidden sort, recommendations, or source status.

Cons:
- Any app-visible wording change can be misread as promotion unless the wording is guarded.

Risk: low to medium.

## Option 4: Defer Production-Active Consideration Until Exact Historical Replay

Status: strongest accuracy discipline.

Pros:
- Keeps production-active approval tied to leakage-safe historical performance.
- Directly addresses the prior-year baseline warning.

Cons:
- Requires historical component receipt backfill first.

Risk: low.

## Option 5: Approve Reproducible Board Generation Policy

Status: operational hardening.

Pros:
- Prevents future loss of current-board input bundles.
- Requires future boards to ship source manifests, hashes, and receipt chains.

Cons:
- Improves reproducibility but does not prove predictive accuracy.

Risk: medium.

## Option 6: Stop And Require More Human Review

Status: conservative hold.

Pros:
- Eliminates promotion risk.
- Keeps pressure on historical replay and source-gate evidence.

Cons:
- No progress toward app-label clarity or production decision.

Risk: low.
