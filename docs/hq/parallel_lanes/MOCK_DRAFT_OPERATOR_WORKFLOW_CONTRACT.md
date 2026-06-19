# Mock Draft Operator Workflow Contract

## Purpose

This contract defines the fixture-only Mock Draft operator workflow. It gives Niners
War Room a safe way to practice the draft-day actions before real draft inputs are
present, validated, and approved.

The workflow is review-only and practice-only. It must not run a real draft
simulation, load real candidate/archive inputs as live draft inputs, or produce
production rankings, probabilities, bands, hidden sort keys, app wiring, exports,
or promoted artifacts.

## Non-Goals

- No real draft simulation.
- No production app or Streamlit UI wiring.
- No automated opponent draft algorithm.
- No real input manifest creation.
- No copied or committed real player data.
- No ADP/market data as NWR private value.

## Core Operator Actions

The fixture-only workflow may support these manual actions:

- Load a fake fixture practice state.
- Show current status and current pick.
- List available fixture assets.
- Mark a fixture asset drafted.
- Undo the last pick.
- Show draft history.
- Show upcoming NWR/my picks.
- Validate state after mutations.
- Render a concise operator status report.
- Serialize or deserialize fixture state for explicit local-only recovery tests.

Every state mutation must validate the draft state. Duplicate drafted assets,
duplicate filled picks, drafted/available overlap, stale current pick values, and
market/private value contamination must fail before the state is treated as valid.

## Fixture Data Rules

Fixture practice data must be tiny, deterministic, and obviously fake. Player names
should use labels such as `Fixture Rookie A` and `Fixture Veteran B`.

Fixture private-value fields may exist only as fake display data for tests and
practice. Fixture market fields may exist only as opponent-behavior context. Market
fields must not be copied into private value rows, and private score fields must not
be copied into market rows.

## Future Real-Draft Gate

Future real-draft mode remains blocked until all of these are true:

- The local real input manifest validates GREEN.
- Frozen rookie input, veteran pool, pick order, my picks, rosters/keepers, team
  needs, NWR private values, and market context are owner-approved.
- ADP/market context is confirmed as opponent behavior, availability, and likely
  pick timing only.
- Real data remains local-only and is not committed.
- The operator receives explicit approval to move beyond fixture practice.

Until then, real draft-use readiness is YELLOW/HOLD.

## Persistence And Recovery

The default operator workflow writes no files. Any future persisted state must be
explicitly requested and confined to a local-only path such as
`local_exports/mock_draft/` or a temporary directory during tests. No default state
file may be created by running the practice command.

## Readiness Rules

- GREEN: fixture-only operator actions work, validate after mutation, and write no
  files by default.
- YELLOW: real inputs or manifest are missing or not owner-approved.
- RED: real data is copied or committed, a real simulation path is introduced, ADP
  becomes NWR private value, or cross-lane/production files are touched.

No real simulations are run by this workflow.
