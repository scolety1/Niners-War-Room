# Mock Draft Operator Practice Run Report

## Scope

Run date: 2026-06-19
Lane: Mock Draft HQ
Branch: `work/mock-draft-simulator`
Starting HEAD: `b360dbf`

This was a fixture-only operator practice drill. No real rookie, veteran, pick
order, roster, NWR private value, ADP, market, archive, candidate, or manifest
inputs were used. No real draft simulation ran.

## Commands Run

Baseline:

```powershell
git fetch origin
git branch --show-current
git rev-parse --short HEAD
git log --oneline -5
git status --short
git status --short -- uv.lock
git diff --check
```

Basic operator commands:

```powershell
scripts/mock_draft_operator_practice.py status
scripts/mock_draft_operator_practice.py available
scripts/mock_draft_operator_practice.py upcoming
scripts/mock_draft_operator_practice.py history
scripts/mock_draft_operator_practice.py validate
```

Practice flows:

```powershell
scripts/mock_draft_operator_practice.py demo
scripts/mock_draft_operator_practice.py draft --asset-id fixture:rookie_a
scripts/mock_draft_operator_practice.py history
scripts/mock_draft_operator_practice.py undo
```

Temp persistence drill:

```powershell
scripts/mock_draft_operator_practice.py status --state-path <temp-state>
scripts/mock_draft_operator_practice.py available --state-path <temp-state>
scripts/mock_draft_operator_practice.py draft --asset-id fixture:rookie_a --state-path <temp-state>
scripts/mock_draft_operator_practice.py history --state-path <temp-state>
scripts/mock_draft_operator_practice.py undo --state-path <temp-state>
scripts/mock_draft_operator_practice.py validate --state-path <temp-state>
```

Mistake-handling drill:

```powershell
scripts/mock_draft_operator_practice.py draft --asset-id fixture:rookie_a --state-path <temp-state>
scripts/mock_draft_operator_practice.py draft --asset-id fixture:rookie_a --state-path <temp-state>
scripts/mock_draft_operator_practice.py draft --asset-id fixture:not_real --state-path <temp-state>
scripts/mock_draft_operator_practice.py validate --state-path <temp-state>
scripts/mock_draft_operator_practice.py undo --state-path <temp-state>
scripts/mock_draft_operator_practice.py undo --state-path <temp-state>
scripts/mock_draft_operator_practice.py validate --state-path <temp-state>
```

Validation:

```powershell
git diff --check
pytest tests/test_mock_draft_operator_session.py tests/test_mock_draft_operator_practice_script.py
ruff check src/services/mock_draft_operator_session.py scripts/mock_draft_operator_practice.py tests/test_mock_draft_operator_session.py tests/test_mock_draft_operator_practice_script.py
scripts/mock_draft_state_smoke.py
scripts/mock_draft_operator_practice.py demo
scripts/mock_draft_operator_practice.py validate
```

## What Worked

- `status` clearly showed fixture-only mode, no real inputs, no real simulation,
  current pick `1.01`, next NWR pick `1.02`, drafted count, and available count.
- `available` showed three fake fixture assets in simple deterministic order.
- `upcoming` clearly marked the next NWR pick.
- `history` clearly reported `History: none` on a fresh fixture session.
- `validate` reported `Operator session validation: GREEN`.
- `demo` showed status, available assets, one manual fake draft, history, undo,
  and clean validation.
- Explicit temp `--state-path` persistence preserved draft history across
  commands and was removable after the drill.
- Duplicate and invalid asset attempts exited nonzero and did not corrupt state.
- Duplicate and invalid asset attempts now print clean operator-facing errors
  instead of Python tracebacks.
- Empty-history undo now reports `No drafted pick to undo.`
- CLI help now states that separate commands start fresh unless `--state-path`
  is supplied.
- Validation after failed actions remained GREEN.

## What Was Confusing

- State does not persist across separate commands by default. This is safe, but
  a live operator could expect `draft` followed by `history` to remember the
  previous command without `--state-path`.
- Live-style practice requires an explicit temp or local-only `--state-path`.

## State Persistence

Default commands do not persist state. This is a safe default and prevents
accidental files, but it is a YELLOW usability issue for repeated manual drills.

Explicit temp persistence worked:

- temp state was created only when `--state-path` was supplied
- history persisted after a fake draft
- undo restored the original state
- temp state was removed after the drill

Practice persistence verdict: GREEN with explicit temp path, YELLOW by default
for operator ergonomics.

## Undo And Correction Safety

Undo safely restored availability, current pick, and history after a persisted
fixture pick. Undo on empty history did not corrupt state and now reports that no
drafted pick was available to undo.

## Operator Signals

- Current pick is obvious in `status`.
- Available list is usable for fixture practice.
- Upcoming NWR/my picks are obvious.
- History is useful once a temp state path is used.
- Error safety is good; duplicate and invalid asset attempts are clean nonzero
  operator errors.

## Readiness Verdict

Fixture-only operator practice: YELLOW/GREEN

- GREEN for safe fixture-only command execution, no real data, no real
  simulation, deterministic fake assets, validation, explicit temp persistence,
  and state recovery.
- YELLOW for live-operator ergonomics because default commands do not persist
  across invocations without an explicit `--state-path`.

Real draft use remains YELLOW/HOLD until real inputs are supplied, validated
GREEN, owner-approved, and explicitly cleared for live operator use.

## Required Improvements Before Live Draft Use

1. Decide whether live mode should require an explicit local state path.
2. Add a clearer persisted-session workflow for draft-day use.
3. Validate real inputs and manifest read-only before any live mode.
4. Keep ADP/market as opponent behavior, availability, and pick timing only.

## Safety Statements

No real data was used, copied, or committed.

No real draft simulation ran.

ADP/market separation remains preserved.
