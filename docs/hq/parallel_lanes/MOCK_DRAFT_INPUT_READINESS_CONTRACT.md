# Mock Draft Input Readiness Contract

## Purpose

Mock Draft runs remain blocked until required local inputs are present and
reviewed. Missing inputs are YELLOW readiness gaps, not a reason to fabricate
data or import live sources.

## Required Inputs

1. Frozen rookie input path:
   `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`
2. Dropped, released, or otherwise available veteran pool.
3. Final pick order.
4. NWR/my pick numbers.
5. Current rosters and keeper state.
6. Team needs and opponent tendencies.
7. NWR private value source.
8. ADP/market source for opponent behavior only.
9. Manual review rules.
10. Stop conditions for any missing or stale input.

## Source Separation

ADP and market context may support opponent behavior, availability, and likely
pick timing only. They must never become NWR private value, NWR quality score,
production ranking, sorting key, probability, or band input.

## Stop Conditions

Do not run a mock draft when:

- the frozen rookie input path is missing;
- the available veteran pool is missing or not reviewed;
- pick order or my-pick ownership is missing;
- roster/keeper state is missing or stale;
- team needs and opponent tendency notes are missing;
- NWR private value source is not identified;
- ADP/market source lacks a separation note;
- manual review rules are missing;
- any required input would need to be invented, live-imported, or promoted.

## Allowed Readiness Checks

Readiness checks may confirm whether expected paths exist and may inspect CSV
headers with Python stdlib `csv`. They must not write outputs, create generated
artifacts, modify `local_exports/`, import live ADP, or run simulations.

## Current Runway Status

GREEN:

- Draft-state invariant smoke validation is available.
- Fixture-only schema templates are available under
  `tests/fixtures/mock_draft_inputs/`.
- Fixture contract validation can run without real inputs.

YELLOW:

- Real frozen rookie input is missing locally until the local-only path exists.
- Veteran pool, final pick order, rosters/keepers, team needs, NWR private
  value source, and market behavior context are not configured yet.

No mock draft simulation may run until real inputs are present, reviewed, and
validated. Normal locked pytest/Ruff remain preferred; the approved ephemeral
`uv run --with pytest --with ruff` path was used for the prior runway because
the locked environment does not currently include pytest/Ruff.

The input contract runway also used the approved ephemeral pytest/Ruff path;
`uv.lock` remained clean. Locked validation should still be preferred if the
locked environment later restores test and lint executables.

## Diagnostics Runway Status

GREEN:

- Human-readable readiness rendering is available.
- Schema diagnostics and safe header alias contracts are available.
- Fixture and adversarial contract tests cover missing columns, contaminated
  market/private schemas, duplicate identities, and no-simulation guardrails.

YELLOW:

- Real draft inputs remain missing or unconfigured.
- Real input validation remains read-only until the user provides local paths.
