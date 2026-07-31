# Golden Lane Autopilot Policy

## Authority and mode

The canonical Golden Lane operates in `BOUNDED_CONTINUOUS_AUTOPILOT` mode. A
successful phase may dispatch the next canonical work order without an owner
handoff. This changes dispatch only; it does not weaken or combine phase gates.

Each major phase retains a fresh implementation worktree, a fresh independent
review/adoption worktree, deterministic evidence, focused commits, at most one
bounded correction cycle, a normal non-force canonical push, and stable-checkout
synchronization only after adoption. The operational checkout is never updated.

## Automatic-advance gate

Advance is permitted only when every item below is true:

1. The phase has an authorized Green verdict or an explicitly accepted truthful null result.
2. Independent review passes and no correction remains.
3. The canonical push succeeds normally and remote reads back at 0 ahead / 0 behind.
4. Stable is synchronized and clean.
5. Status, phase matrix, manifest, and phase packet validate deterministically.
6. `owner_decisions_required` is `0`.
7. The next prompt hash and phase identity match `GOLDEN_LANE_AUTOPILOT_STATE.json`.
8. The next phase is allowlisted and no active hard-stop row exists.
9. No concurrent lane owns overlapping paths.
10. Protected, opaque, persistent, recovery, user, scheduler, and production state are unchanged.
11. No provider, credential, payment, license-acceptance, or external-permission action is required.

Open fail-closed source controls do not count as owner decisions required to
advance while their sources remain ineligible and unused. They remain recorded
in `EXTERNAL_BLOCKERS_AND_OWNER_DECISIONS.csv` and
`open_fail_closed_controls` until resolved. If a phase needs one of those
sources, the relevant control becomes a blocking owner decision and autopilot
stops.

## Automatic-execution allowlist

- Phase 1B: exact authoritative restoration, receipt correction, or documented
  quarantine of a non-production baseline exception only.
- Phase 2: outcome, replacement, eligibility, target, chronological-fold, and
  baseline persistence contracts.
- Phase 3: already admitted/open data, bounded preregistered feature families,
  research-only tests, and truthful null results.
- Phase 4: null-result research closure or decision recording that does not
  adopt a replacement formula.
- Phase 7: contracted product completion using admitted authorities with no
  pending formula authority, opaque recommendation, migration, or destructive
  state change.
- Phase 8: release acceptance after every applicable earlier phase is passed,
  closed, or not required.

Phases 5 and 6 are not automatically executable. Phase 4 stops if a passing
feature requires a production/model authority choice.

## Hard-stop behavior

Any active condition in `GOLDEN_LANE_HARD_STOP_REGISTRY.csv` stops dispatch.
Completed earlier phases remain canonical. The controller records exactly one
owner decision, updates status and state, and replaces the resume prompt with a
concise decision packet. It must not create speculative alternatives.

