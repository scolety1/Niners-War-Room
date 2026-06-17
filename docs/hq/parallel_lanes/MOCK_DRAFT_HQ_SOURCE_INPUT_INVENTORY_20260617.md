# Mock Draft HQ Source Input Inventory

## Scope

This is a Master/Main HQ docs-only inventory for a future Mock Draft HQ/lane. It
does not reopen Rookie HQ, modify Rookie artifacts, run simulations, create
app/production rankings, create probabilities or bands, create hidden sort keys,
create promoted artifacts, or touch app/source/Outcome/Deployment files.

## Rookie Input

Approved Rookie input:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv
```

Input status:

- Rookie input readiness: GREEN
- Manual draft trust: YELLOW

Manual draft trust is YELLOW because some display-only fields still have
`needs_data`.

Use classification:

- manual-use rookie input only
- not production rankings
- not app rankings
- not a new Rookie model
- not a hidden sort key source
- not a source of probabilities or bands unless separately approved later

## Required Additional Mock Draft Inputs

Mock Draft HQ needs the following inputs before simulation:

1. Dropped veteran pool.
2. All current team rosters.
3. Draft pick order.
4. Team needs / roster construction needs.
5. League scoring/settings.
6. ADP/market behavior source.
7. NWR value board/source for veterans and rookies, if approved.

## Known From HQ Context

Known:

- Rookie input path is approved for manual-use Mock Draft intake.
- Rookie HQ is paused/frozen.
- League settings are recorded in the M1 charter.
- Mock Draft should use rookies plus dropped veterans.
- ADP/market may be used only for draft behavior, opponent likelihood, and
  availability modeling.
- ADP/market must not be blended into NWR private quality/value.
- Rookie artifacts are manual-use inputs only, not production/app rankings.

Known dropped players from prior HQ context:

- Dak Prescott
- Brock Purdy
- Brock Purdy
- Brian Thomas
- Alec Pierce
- Zay Flowers
- Jameson Williams
- Rashee Rice
- Chris Olave
- Drake Maye

This list should be validated by Mock Draft HQ against the current roster/free
agent source packet before simulation.

## Missing Or Needing Confirmation

Needs confirmation before simulation:

- full dropped veteran pool
- all current rosters
- complete draft pick order
- current free agent pool
- exact team needs / roster construction needs
- selected ADP/market behavior source and as-of date
- approved NWR value source for veterans
- approved use of rookie NWR value fields from the manual-use rookie input
- source paths for any current roster/free-agent PDF or parsed exports

## Simulation Blockers

Stop a Mock Draft simulation if any of these are missing or unclear:

- draft pick order
- all current team rosters
- dropped veteran pool
- available/free agent pool
- league settings
- input-source approval for ADP/market behavior
- separation between ADP/market behavior and NWR private value
- confirmation that outputs are human-review only

Do not invent missing rosters, picks, dropped veterans, or team needs.

## Data Boundaries

- Rookie input is manual-use only.
- ADP/market is behavior/context only unless separately approved.
- No production/app ranking effects.
- No app-readable probability or band outputs.
- No hidden sort keys.
- No promoted artifacts.
- No Rookie repo or artifact modification.
- No app/source/Outcome/Deployment file modification.
- No `data/`, `local_exports/`, or `.venv/` commits.

## Recommended First Mock Draft HQ Task

Recommended first task: Phase 1 intake/design only.

Mock Draft HQ should first confirm source paths, schemas, and missing inputs.
Simulation should wait until all required inputs are present and the
ADP/market-vs-NWR-value separation contract is explicit.

## Inventory Verdict

Verdict: `GREEN_FOR_PHASE_1_INTAKE_DESIGN`

Reason: Mock Draft HQ can safely start with input inventory and data-contract
design. Full simulation remains blocked until required current rosters, dropped
veterans, pick order, available pool, and behavior/value source approvals are
confirmed.
