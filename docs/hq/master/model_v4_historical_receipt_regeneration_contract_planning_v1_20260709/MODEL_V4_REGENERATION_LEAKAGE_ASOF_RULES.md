# Model v4 Regeneration Leakage and As-Of Rules

## Universal Rule

Every regenerated row must be reconstructable from information available at or before the decision date for that player-season. If a source field is current-only, future-known, post-outcome, or not reproducible historically, it must be excluded or marked blocked.

## Allowed Timing

- Prior-season or earlier facts.
- Pre-target-season roster-independent historical facts.
- Source coverage and missingness states that can be proven as-of.
- Outcome labels only as labels or validation targets, never as input receipts.

## Blocked Timing

- Current 2026 board values as historical inputs.
- Future-season fantasy finishes as inputs.
- Post-outcome role knowledge.
- Current ADP, current depth charts, current injuries, current roster state, or current rankings.
- Any field whose timestamp cannot be separated from the target outcome.

## Family-Specific Rules

### Confidence Cap Receipts

Confidence can describe source coverage, missingness, known component availability, and warning states. It cannot encode later accuracy, future performance, or production approval.

### Role Archetype Receipts

Role labels must be generated from lagged usage/production context only. A later breakout or role collapse cannot be used to label a prior decision-date role.

### Red-Zone Exact Receipts

Red-zone values may be regenerated only from source-traced red-zone historical inputs. They cannot be inferred from fantasy points, touchdowns, final ranks, or future outcomes.

## Required Checks

- Input source timestamp or season provenance.
- No target-season outcome fields in input receipt generation.
- No current-board-only field mapped into historical rows except as schema reference.
- Leakage flag per row.
- Lane-level leakage summary.
