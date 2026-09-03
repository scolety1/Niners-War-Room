# Champion/Challenger scaffolding (section 28)

Code: `src/services/champion_challenger_registry_service.py`. Tests:
`tests/test_champion_challenger_registry_service.py`, 9/9 passing.

## What this is

A registry for tracking SHADOW/RESEARCH challengers against their
production champions, with an explicit, auditable promotion decision —
**no automatic promotion**, per this section's own instruction.

Storage mirrors `nwr_pure_experiment_service.py`'s established pattern
(write-once JSON + append-only JSON Lines), under
`<redraft_root>/champion_challenger_registry/<challenger_id>/`:
- `registration.json` — written once per `challenger_id`. Requires a
  real `hypothesis` (the specific weakness targeted, not a vague "improve
  accuracy" claim) and a non-empty `evaluation_summary` (real evidence —
  a challenger is registered with a backtest result, not a bare claim).
  Refuses a duplicate `challenger_id`: a new hypothesis or module version
  needs a new id, so history is never silently rewritten.
- `decisions.jsonl` — append-only. `record_promotion_decision()` is the
  **only** function that can change a challenger's status, and it always
  requires: a prior registration to exist, a non-empty human-authored
  `reason`, and a `decided_by` that is a real identity/role (rejects
  `"system"`/`"auto"`/`"automatic"` outright). There is no scheduler, no
  threshold-based auto-promotion anywhere in this module or the repo
  (verified via grep for calls to `record_promotion_decision`), and no
  default value that resolves to `PROMOTED`.

`current_status()` reads `UNREGISTERED` / `REGISTERED` / the most recent
decision (`PROMOTED` / `REJECTED` / `RETIRED`) — a later decision always
wins, so a challenger can move `PROMOTED -> RETIRED` later, but only ever
via another explicit call in that same challenger's own history.

## What promotion means, and does not mean

Recording a `PROMOTED` decision here **only records the decision**. It
does not wire the challenger into `desktop_facade.py`, production
ranking, or any owner-facing surface — actually swapping a champion for
a challenger remains a separate, explicit code change, reviewed on its
own merits, exactly like every other production change this session has
made. The registry's job is to make that decision auditable and
reversible (a `RETIRED` decision after the fact), not to perform it.

## First real registrant

`rookie-market-blend-v1` (`src/services/rookie_market_blend_challenger_service.py`,
see `docs/codex/ROOKIE_MARKET_BLEND_CHALLENGER_20260903.md`) is the
reference challenger this scaffolding was built to track. It is **not
registered in any persistent store this pass** — the registry root lives
under the owner's local redraft data directory (runtime state, not
repo-tracked, same as `nwr_pure_experiments/`), and this session does not
fabricate an owner's promotion/rejection decision on their behalf. The
test suite exercises the full real lifecycle (register → reject → a
distinct v2 registered and promoted independently, v1's own history
untouched) using `rookie-market-blend-v1`'s actual real backtest numbers
as the `evaluation_summary`, so the registry is proven against real
evidence, not a synthetic placeholder — but no live promotion decision
for it exists anywhere yet. That is the owner's call to make.
