# Mock Draft HQ Lane Charter

## Scope

This charter approves opening a separate Mock Draft HQ/lane for drop-day draft
prep. It is Master/Main HQ governance only. It does not reopen Rookie HQ, modify
Rookie artifacts, run simulations, create app/production rankings, create
probabilities or bands, create hidden sort keys, create promoted artifacts, or
touch app/source/Outcome/Deployment files.

## Lane Separation

Mock Draft HQ is separate from Rookie HQ.

Rookie HQ remains paused/frozen at the recorded final handoff state. Mock Draft
HQ may consume the approved Rookie mock draft input as a read-only manual-use
input, but it must not change Rookie formulas, Rookie board order, Rookie
exports, Rookie warnings, or Rookie framework files.

## Approved Rookie Input

Mock Draft HQ may use this file:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv
```

Use classification:

- manual-use rookie input only
- not production rankings
- not app rankings
- not a new Rookie model
- not a hidden sort key source
- not a source of probabilities or bands unless separately approved later

## Core Guardrails

- Rookie outputs are not production/app rankings.
- Mock Draft must not modify Rookie repo files or Rookie artifacts.
- Mock Draft must not alter Outcome model behavior or app output.
- Mock Draft must not create app-readable probabilities, bands, rankings, hidden
  sort keys, or promoted artifacts unless separately approved.
- ADP/market context may be used only for draft-behavior, opponent-likelihood,
  and availability modeling. It must remain separate from NWR private
  quality/value.
- NWR value and ADP/market behavior must remain separate columns, separate
  features, and separate explanations.

## Mock Draft Modeling Scope

Mock Draft should model draft behavior using:

- rookies
- dropped veterans
- all team rosters
- pick order
- team needs
- ADP/market behavior
- NWR value

This is draft-prep/human-review work, not production ranking work.

## League Settings

- 10 teams
- Dynasty/keeper hybrid
- 1QB
- Non-PPR
- first-down scoring: 0.4 rush/rec first down
- pass yards: 1 per 30
- pass TD: 3
- INT: -1
- rush/rec yards: 1 per 10
- rush/rec TD: 4
- return yards: 1 per 30
- return TD: 4
- 2-point conversions: 2
- fumble lost: -1
- kickers not important

## Mock Draft HQ Opening Gate

GREEN if:

- a separate lane can be opened
- only manual/local inputs are used
- Rookie HQ remains frozen
- no production/app/Outcome contamination is required
- no app-readable probabilities, bands, hidden sort keys, or promoted artifacts
  are created

YELLOW if:

- required draft inputs are missing
- source files need confirmation
- data contracts need clarification before simulations

RED if:

- production/app ranking work is required
- Rookie HQ must be reopened without explicit HQ approval
- Outcome model/app output would be touched
- probabilities, bands, hidden sort keys, or promoted artifacts would be created
- `data/`, `local_exports/`, or `.venv/` would need to be committed

## Charter Verdict

Verdict: `GREEN_TO_OPEN_SEPARATE_MOCK_DRAFT_HQ_LANE`

Reason: the lane can start as isolated, docs/intake/design-first work using
manual/local inputs only. Simulation and implementation should wait until Mock
Draft HQ confirms required inputs and source boundaries.
