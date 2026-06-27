# NWR Player Compare + Trade Planner UX - 2026-06-27

## What Changed

This lane addresses non-draft-room issues from the original post-draft feedback:

- Player Compare now starts with a short "How to use this comparison" guide.
- Decision Summary is labeled as display-only and easier to scan.
- Dense decision rows moved behind an advanced expander.
- A plain-language comparison table now surfaces Safer profile, Upside profile, League/scoring fit, Timing/window, Main risk, and What still needs review.
- Injury / Availability Data Status now states what the app does and does not know.
- Trading Lab now includes two manual planning tabs:
  - Trade Away Pick Planner
  - Trade For Pick Planner

## Injury / Availability Policy

The Player Compare page now says clearly:

- No injury risk score is created.
- No active injury-risk adjustment is being applied on the page.
- No medical comeback projection is being made.
- Missing injury data is not treated as clean health.
- Per-game vs season totals can diverge due to missed games.
- Injury risk remains a human-review/data-gap item until an approved injury source and explicit model gate exist.

## Trading Lab Policy

The new planner tabs are manual planning scaffolds only:

- Manual planning only.
- Not a trade calculator.
- Not model input.
- Not market valuation.
- Does not write to live draft runtime state.
- Does not change pick ownership.
- Does not generate offers.
- Does not calculate the least acceptable price.

Real in-draft trade recording remains owned by the Live Draft V2 workflow and was not modified here.

## Deferred

Draft-room tabs, side panels, search, tier board placement, and in-room cheat sheet layout remain `DEFER_DRAFT_ROOM_REVIEW` because this lane was explicitly barred from draft-room files.

## Validation Intent

Focused tests cover the new Player Compare language, injury transparency, Trading Lab planner labels, manual-only guardrails, and original-doc status matrix. Route smoke should include Player Compare and Trading Lab plus render-only checks for Live Draft and Mock Draft.
