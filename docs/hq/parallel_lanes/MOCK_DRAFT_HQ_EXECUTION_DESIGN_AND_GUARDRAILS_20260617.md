# Mock Draft HQ Execution Design And Guardrails

## Scope

This is a Master/Main HQ docs-only execution design for a future Mock Draft
HQ/lane. It does not reopen Rookie HQ, modify Rookie artifacts, run simulations,
create app/production rankings, create probabilities or bands, create hidden
sort keys, create promoted artifacts, or touch app/source/Outcome/Deployment
files.

## Purpose

Mock Draft HQ should simulate post-drop-day fantasy draft behavior for human
drop-day draft prep.

The simulator should help answer:

- which players may be available at each pick
- how opponent needs and market behavior may shape picks
- where NWR value differs from likely room behavior
- which draft scenarios deserve manual review

It is not production ranking work.

## Scope Of Future Mock Draft Work

Future Mock Draft scope may include:

- rookies
- dropped veterans
- all team rosters
- pick order
- team needs
- ADP/market behavior
- NWR value

ADP/market behavior and NWR private quality/value must remain separate.

## Phase Structure

### Phase 1: Intake / Design

Confirm source paths, schemas, league settings, required inputs, and output
contracts. Do not simulate until required inputs are confirmed.

### Phase 2: Source Validation

Validate:

- rookie manual-use input
- dropped veteran pool
- all team rosters
- pick order
- free agent / available pool
- ADP/market behavior source
- NWR value source, if approved

Stop if any required input is missing or ambiguous.

### Phase 3: Draft Behavior Assumptions

Define human-review assumptions for:

- team needs
- roster construction
- positional scarcity
- market/ADP-driven opponent likelihood
- availability ranges
- NWR value comparison

Keep assumptions visible and editable. Do not bury them in hidden sort keys.

### Phase 4: Simulation Harness

Only after source validation, build a review-only harness that can produce draft
scenarios. The harness must not write production/app rankings or app-readable
probability/band outputs unless separately approved.

### Phase 5: Human Review Packets

Produce human-facing review packets such as:

- draft scenario tables
- pick-by-pick notes
- player availability simulations
- team need notes
- value-vs-room behavior explanations

### Phase 6: Optional Iterative Scenario Runs

Run iterative scenarios only after HQ confirms Phase 1 through Phase 5 outputs
are safe and useful. Scenario runs remain local/manual review work.

## Explicitly Blocked

The following remain blocked:

- Rookie HQ reopening
- Rookie artifact modification
- app/production rankings
- Outcome model changes
- probabilities
- coarse bands
- exact percentage app outputs
- hidden sort keys
- promoted artifacts
- app/source file changes
- Deployment V2 file changes
- `data/`, `local_exports/`, or `.venv/` commits

## Missing Input Handling

Stop and report if any of these are missing:

- pick order
- all team rosters
- dropped veteran pool
- available/free agent pool
- league settings
- selected ADP/market behavior source
- approved NWR value source, if needed

Do not invent missing rosters, picks, dropped veterans, available players, team
needs, or source data.

## Allowed Human-Facing Outputs

Allowed, if generated in the future Mock Draft lane after source validation:

- draft scenario tables
- team need notes
- player availability simulations
- manual review packets
- source coverage notes
- visible assumptions and caveats

These must remain human-review outputs.

## Forbidden Outputs

Forbidden unless separately approved later:

- app-readable production rankings
- hidden sort keys
- production probability columns
- coarse probability bands
- exact percentage outputs
- promoted artifacts
- changed app rankings/sorting
- Rookie model outputs
- Outcome model outputs

## Recommended First Mock Draft Lane Stance

Recommended first stance:

```text
Phase 1 intake/design only
```

Reason: the Rookie manual-use input is ready, but full simulation still depends
on confirming current rosters, dropped veterans, pick order, available pool, and
source boundaries.

## Design Verdict

Verdict: `GREEN_FOR_MOCK_DRAFT_PHASE_1_DESIGN`

Reason: Mock Draft HQ can safely start as a separate intake/design lane. It
should not run simulations until all required inputs are confirmed and all
output boundaries are explicit.
