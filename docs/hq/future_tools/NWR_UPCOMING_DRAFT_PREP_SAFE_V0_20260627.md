# NWR Upcoming Draft Prep Safe V0 - 2026-06-27

## Verdict

GREEN feature lane candidate: Upcoming Draft Prep was added as a Safe V0 Development Lab page for manual planning only. It does not create rookie rankings, class-strength grades, recommendations, model outputs, pick values, or trade values.

## Page Purpose

`/upcoming-draft-prep` gives the user one place to manually prepare for the next draft before opening Live Draft or Mock Drafts. It is a checklist and notes workspace, not a decision engine.

## Sections Added

1. Draft Setup Checklist
2. Roster Needs Snapshot
3. Pick Inventory / Asset Prep
4. Rookie / Prospect Watchlist Placeholder
5. Mock Draft Scenario Prep
6. Questions to Answer Before Draft
7. Data Readiness Checklist

## Data Used

- User-entered manual notes.
- Existing Live Draft runtime trade event log for future pick context, read-only and manual/local only.
- Existing Development Lab / Future Tools status matrix for nav and control-board status.

## Data Explicitly Not Used

- CFBD as model input.
- NFL usage as model input.
- DynastyProcess, ADP, or market data as hidden logic.
- Vendor/Gmail automation.
- Rookie projections, class-strength grades, or prospect model outputs.
- Any source-truth artifact.

## Guardrails

- No Frozen Final Draft Board V1 mutation.
- No `final_board_rank`, Dynasty Rank, tier, pinned snapshot, `latest_candidate`, or `latest_approved` mutation.
- No production model/rank logic changes.
- No source-truth/model-input gates opened.
- No decision-page wiring.
- No hosted deployment.
- No pick valuation or trade valuation.

## Compatibility

`/draft-prep` is registered as a compatibility page that points to `/upcoming-draft-prep`, Live Draft, Mock Drafts, and Dynasty Rankings. The existing `/draft-room` legacy route remains unchanged.

## Limitations

- Manual inputs are not saved after reload unless exported.
- Future pick context from runtime state is not official source truth.
- Rookie/prospect watchlist rows are manual placeholders only.
- Data readiness checklist is not a refresh button or data promotion mechanism.

## Future Upgrade Ideas

- Add optional untracked local persistence if explicitly approved.
- Add a human-review import workflow for notes.
- Add source-status summaries from Settings/Data Health after a separate review-only integration gate.
