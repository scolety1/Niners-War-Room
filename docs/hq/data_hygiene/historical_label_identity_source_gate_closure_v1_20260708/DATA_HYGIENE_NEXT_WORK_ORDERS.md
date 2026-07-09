# Data Hygiene Next Work Orders

## Recommended To Master HQ

Recommend option 2:

`Allow review-only component signal tests`

Master HQ should not approve position-scoped tournaments or full Formula Gauntlet yet.

## Work Order 1: Component Signal Test Execution Contract

Objective:

Write a narrow Master HQ contract for review-only component signal tests using the existing partial historical panel.

Required:

- Inputs limited to cleared review-only component signal families.
- PYF mandatory anchor.
- Leakage/as-of check.
- Missingness reporting.
- Sparse-history and prior-production-decline diagnostics.
- No weights, winners, production claims, or source promotion.

Safe now:

Yes, as a no-tournament contract lane. Execution still needs explicit Master HQ approval.

## Work Order 2: Exact Model v4 Historical Receipt Recovery

Objective:

Recover season-by-season exact receipts for:

- `checkpoint_review_score`
- `position_specific_review_score`
- lifecycle / age / role / confidence
- WR/QB v2 overlay chain

Safe now:

Yes, as receipt recovery only. No benchmark or Formula Gauntlet execution.

## Work Order 3: Route/YPRR/TPRR Source Admission

Objective:

Resolve whether true route denominator fields can be admitted for future WR/TE/RB tests.

Safe now:

Source-readiness only. No metric calculation as admitted input.

## Work Order 4: Sparse-History / Low-Games Policy

Objective:

Define thresholds and reporting requirements for sparse-history rows, low-games rows, prior-production decline false positives, rookie/second-year uncertainty, RB role changes, WR breakouts, and TE volatility.

Safe now:

Yes, as docs/guardrail policy.

## Work Order 5: Position-Scoped Tournament Readiness Recheck

Objective:

After source and missingness gates improve, rerun Data Hygiene closure to decide whether position-scoped review-only tournaments can be cleared.

Safe now:

No. Wait for additional source/receipt recovery.
