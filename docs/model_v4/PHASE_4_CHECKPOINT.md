# Model v4 Phase 4 Checkpoint

Created: 2026-05-16

Phase 4 made the review-only Model v4 preview inspectable inside the app. It
did not promote Model v4 into War Board, My Team, Rankings, Draft Board, League
Targets, or any readiness gate.

## Current Preview State

The active Model v4 preview is loaded from
`local_exports/model_v4/review_only_latest`.

Current preview summary:

- review status: review_only
- formula version: model_v4_review_only_0.1.0
- preview engine: model_v4_preview_engine_review_only_0.1.0
- computed at: 2026-05-16T02:40:51Z
- truth-set players: 80
- preview output rows: 80
- component rows: 640
- receipt rows: 640
- source coverage rows: 640
- warning rows: 839
- active rankings overwritten: false
- app promotion: false
- decision-ready unlocked: false
- draft-ready unlocked: false
- final-money-ready unlocked: false

## Phase 4 Work Completed

### Model Lab v4 Integration

Model Lab now exposes Model v4 as a dedicated review-only workbench. The app
shows preview status, formula version, row counts, guard rows, and a clear
warning that active decision pages are unchanged.

The integration keeps these outputs isolated:

- active War Board: unchanged
- active My Team: unchanged
- active Rankings: unchanged
- active Draft Board: unchanged
- active League Targets: unchanged
- readiness gates: unchanged

### Preview Rankings Workbench

The Model v4 Preview Rankings tab shows review-only ranks from the v4 preview
output. It includes:

- overall preview rank
- position preview rank
- player
- position
- NFL team
- lifecycle
- Dynasty Asset Value
- confidence label
- review warnings
- unavailable sections

The table is filterable by position, lifecycle, confidence label, warning text,
and player search. The label remains:

`Review-only v4 preview. Not active rankings.`

### Receipt Drilldown

The receipt drilldown makes selected-player Model v4 scoring inspectable. It
groups receipts by:

- production
- first-down scoring fit
- usage/opportunity
- snap/proxy role
- projection
- age/dropoff
- young-player prior
- confidence

Each receipt row shows normalized score, weight, contribution, source status,
raw fields, warning, unavailable reason, and reconciliation to the preview
component contribution. Raw JSON stays behind Advanced.

### WR Evidence Audit

`PHASE_4_WR_EVIDENCE_AUDIT.md` and
`PHASE_4_WR_EVIDENCE_AUDIT.csv` investigated the main Phase 3 review finding:
whether some elite WR values were low due to data gaps or a formula issue.

Summary:

- requested WRs: 9
- matched WRs: 9
- route data unavailable rows: 9
- first-down projection gap rows: 9
- usage normalization review rows: 8
- production normalization review rows: 5
- young bridge review rows: 4
- true formula imbalance review rows: 0
- score changes applied: false
- active rankings promoted: false

Interpretation:

- true route metrics remain unavailable from safe free/public sources
- first-down projections remain missing
- several WR rows deserve production or usage normalization review
- no fixture-backed formula imbalance was proven in this pass
- no formula weights were changed

### Source Gap Display

The Model v4 Source Coverage tab now classifies evidence gaps into user-facing
categories:

- Critical Missing Evidence
- Proxy-Only Evidence
- Projection Gap
- First-Down Projection Gap
- Route Data Unavailable
- Not Applicable
- Covered Evidence

Counts are shown by category, component, and position. Importantly,
young-player prior being not applicable for established veterans is now
displayed as `Not Applicable`, not as a data failure.

### Sanity And Named Audit UI

Model Lab now has review-focused audit sections for:

- Sanity Fixture Dry Run
- Named Player Review

Each section shows:

- ready count
- review count
- blocked count
- decision-ready unlocked: false

Review findings are sorted first and show:

- expected behavior
- actual behavior
- classification
- likely cause
- next action
- receipt drilldown hint

These findings are audit signals only. They do not auto-change formulas and do
not unlock readiness.

### External Audit Packet

A Model v4 Phase 4 external audit packet is not present yet in the current
workspace. Earlier external-audit packets exist for Truth Set Lab / Project
Gold work, but no dedicated Model v4 Phase 4 packet was found.

This checkpoint should therefore be treated as the handoff before creating a
Model v4 external audit packet, not as proof that external review has already
been completed.

## Safety Confirmation

- active rankings unchanged: confirmed by preview summary
- My Team unchanged: confirmed by review-only app integration policy
- War Board unchanged: confirmed by review-only app integration policy
- app promotion: false
- decision-ready unlocked: false
- draft-ready unlocked: false
- final-money-ready unlocked: false
- v4 remains review-only: yes

## Remaining Issues Before Promotion

The following should be resolved or explicitly accepted before Model v4 can be
promoted into normal roster-decision pages:

- WR production and usage normalization review remains open
- route participation / routes / TPRR / YPRR remain unavailable from safe free
  public data
- snap share is still only a role proxy, not route evidence
- first-down projections are missing
- incoming and year-one players still have unavoidable NFL evidence gaps
- external Model v4 audit packet has not been created or reviewed

## Next-Step Decision

### App promotion planning?

Not yet. Model v4 should not replace My Team or War Board until the remaining
review findings are externally audited or patched.

### Formula patch pass?

Not as the immediate next step. Phase 4D found no true formula imbalance rows.
If formula work happens next, it should be limited to documented normalization
or fixture-backed issues, not rank-shaping.

### Source/data patch pass?

Useful, but only for specific open findings:

- WR production normalization review
- WR derived usage normalization review
- first-down projection strategy
- route-data unavailable policy

### External audit first?

Yes. The best next step is to create a dedicated Model v4 external audit packet
from the Phase 4 artifacts and send it through the neutral external/pro audit
process before app promotion or formula tuning.

Recommended next phase:

`Model v4 / Phase 4G: External Audit Packet`

The packet should include:

- this checkpoint
- Phase 3 checkpoint
- Phase 4 WR evidence audit
- Model v4 preview outputs
- component rows
- receipt rows
- source coverage rows
- warning rows
- sanity fixture dry-run rows
- named-player review rows
- current formula config
- feature/source contract
- receipt requirement contract
- a neutral auditor prompt

## Test And Static Check Status

This checkpoint should be followed by:

- full test suite
- full static check

Expected safety condition remains:

- tests pass
- static check passes
- no readiness gates unlock
- no active rankings are overwritten
