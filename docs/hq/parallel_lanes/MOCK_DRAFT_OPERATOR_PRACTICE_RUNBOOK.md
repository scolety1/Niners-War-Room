# Mock Draft Operator Practice Runbook

## Scope

This runbook covers fixture-only operator practice. It is not real draft use and it
does not run a real draft simulation.

## Commands

Run from `C:\NWR\Niners-War-Room-mock-draft`:

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
$env:PYTHONDONTWRITEBYTECODE="1"

& $uv run --locked python -B scripts/mock_draft_operator_practice.py demo
& $uv run --locked python -B scripts/mock_draft_operator_practice.py status
& $uv run --locked python -B scripts/mock_draft_operator_practice.py available
& $uv run --locked python -B scripts/mock_draft_operator_practice.py draft --asset-id fixture:rookie_a
& $uv run --locked python -B scripts/mock_draft_operator_practice.py undo
& $uv run --locked python -B scripts/mock_draft_operator_practice.py history
& $uv run --locked python -B scripts/mock_draft_operator_practice.py upcoming
& $uv run --locked python -B scripts/mock_draft_operator_practice.py validate
```

## Expected Behavior

- `demo` shows status, lists fake available assets, manually drafts one fake asset,
  shows history, undoes the pick, and validates the state.
- `status` shows current pick, next NWR pick, drafted count, and available count.
- `available` lists fixture assets in deterministic display order.
- `draft` marks one fixture asset drafted and advances current pick.
- `undo` restores the last drafted fixture asset.
- `history` shows fixture picks already made.
- `upcoming` shows upcoming NWR/my picks.
- `validate` checks state invariants and market/private separation.

All commands print fixture-only and no-real-simulation language.

## What Is GREEN

- Fixture-only practice session creation.
- Current pick display.
- Available fixture asset display.
- Manual mark drafted.
- Undo last pick.
- Draft history.
- Upcoming NWR pick display.
- State validation after mutations.
- Explicit temp-file persistence tests.

## What Remains YELLOW

- Real input manifest is missing or unapproved.
- Frozen rookie input, veteran pool, pick order, my picks, rosters/keepers, team
  needs, private value source, and market context remain incomplete for real use.
- Real draft-use workflow remains HOLD until those inputs validate GREEN.

## Persistence And Recovery

The practice script writes no file by default. A state path may be used only when
explicitly provided and validated as local-only or temporary. During real draft-day
work, persisted state design must be re-approved before use with real inputs.

## Operator Checklist For Later Live Mode

- Validate the real manifest first.
- Confirm no real files are staged or committed.
- Confirm ADP/market is opponent behavior only.
- Confirm NWR private value source is separate.
- Run readiness checks and state smoke.
- Do not run any simulation until Mock Draft HQ explicitly approves the live mode.
