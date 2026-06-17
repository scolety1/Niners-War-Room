# Mock Draft HQ Kickoff Handoff And Review Hold

## Scope

This is the final Master/Main HQ kickoff handoff for a future separate Mock
Draft HQ/lane. It is docs/governance only. Do not run Mock Draft implementation
from Master HQ.

This document does not reopen Rookie HQ, modify Rookie artifacts, run
simulations, create app/production rankings, create probabilities or bands,
create hidden sort keys, create promoted artifacts, or touch
app/source/Outcome/Deployment files.

## Mock Draft HQ Purpose

Mock Draft HQ should prepare a review-only mock draft simulator for drop-day
draft prep.

The lane should model likely draft behavior using:

- rookies
- dropped veterans
- all team rosters
- pick order
- team needs
- ADP/market behavior
- NWR value

The goal is human review context, not production/app rankings.

## Repo / Lane Status

- Master HQ approved a separate Mock Draft HQ/lane.
- Rookie HQ remains paused/frozen.
- Mock Draft HQ must remain separate from Rookie HQ.
- Mock Draft HQ must not modify Rookie repo files or Rookie artifacts.
- Mock Draft HQ should begin with Phase 1 intake/design unless all required
  inputs are confirmed locally.

## Final Rookie Input Path

Use this Rookie input as manual-use rookie input only:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv
```

This file is:

- manual-use rookie input only
- not production rankings
- not app rankings
- not a new Rookie model
- not a hidden sort key source
- not a source of probabilities or bands unless separately approved later

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

## Required Inputs

Confirmed from Master HQ:

- Rookie input path is approved for manual-use intake.
- Rookie HQ is paused/frozen.
- League settings are recorded.
- Mock Draft HQ is approved as a separate lane.

Known but must be validated:

- dropped player context from prior HQ notes
- current roster/free agent source packet
- any parsed roster/free-agent exports

Missing or needing confirmation before simulation:

- full dropped veteran pool
- all current team rosters
- complete draft pick order
- current free agent / available pool
- team needs / roster construction needs
- selected ADP/market behavior source and as-of date
- approved NWR value source for veterans
- approved use of rookie NWR value fields from the manual-use rookie input

## Guardrails

- Do not reopen Rookie HQ.
- Do not modify Rookie artifacts.
- Do not touch app/source files.
- Do not touch Outcome model behavior or app output.
- Do not create production/app rankings.
- Do not create probabilities, bands, or exact percentage app outputs.
- Do not create hidden sort keys.
- Do not create promoted artifacts.
- Do not commit `data/`, `local_exports/`, or `.venv/`.
- Do not invent missing rosters, picks, dropped players, available players, team
  needs, or source data.
- Keep ADP/market behavior separate from NWR private quality/value.

## Pasteable Prompt For Future Mock Draft HQ

```text
You are Mock Draft HQ for Niners War Room.

Mission:
Build a separate review-only mock draft lane for drop-day draft prep. Start with
Phase 1 intake/design only unless all required inputs are confirmed locally.

Use this Rookie input as read-only manual-use input:
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv

Treat that file as:
- manual-use rookie input only
- not production rankings
- not app rankings
- not a new Rookie model
- not a hidden sort key source
- not a source of probabilities/bands unless separately approved later

Rookie HQ is paused/frozen. Do not reopen Rookie HQ or modify Rookie repo files
or Rookie artifacts.

Mock Draft scope:
- rookies
- dropped veterans
- all team rosters
- pick order
- team needs
- ADP/market behavior
- NWR value

League settings:
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

Hard boundaries:
- do not modify Rookie artifacts
- do not touch app/source files
- do not touch Outcome behavior
- do not create production/app rankings
- do not create probabilities, bands, hidden sort keys, or promoted artifacts
- do not commit data/, local_exports/, or .venv/
- keep ADP/market behavior separate from NWR private quality/value
- do not run simulations until rosters, pick order, dropped veteran pool,
  available pool, ADP/market source, and NWR value source are confirmed

First task:
Inventory local inputs, confirm source paths and schemas, identify missing
inputs, and propose the first safe Phase 1 implementation plan.
```

## Opening Recommendation

Recommendation: `GREEN_TO_OPEN_SEPARATE_MOCK_DRAFT_HQ_CHAT_LANE`

Reason:

- Rookie HQ freeze is recorded.
- Mock Draft HQ lane is chartered separately.
- Required inputs and blockers are inventoried.
- Execution guardrails are documented.
- The first Mock Draft HQ task can be intake/design only.

Simulation remains blocked until required inputs are confirmed in the separate
Mock Draft HQ lane.

## Review Hold

Do not run Mock Draft implementation from Master HQ.

Master HQ should remain in monitor/control mode and use this handoff to open or
coordinate the separate Mock Draft HQ lane.
