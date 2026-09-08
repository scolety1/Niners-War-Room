# Next-Draft Final Blocker Closure — Section 1: Projection Freshness/Bootstrap V1

**Context:** Follow-up directive "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE", section 1.

## Real root cause, traced precisely

`load_projection_snapshot` (`redraft_engine_v1_service.py`) enforces a real, working-as-
designed row-level freshness gate: `_source_as_of_reason` rejects any row whose
`source_as_of` is more than `MAX_PROJECTION_AGE_DAYS = 30` days before the real current date.
A real, existing bypass mechanism (`_load_draft_day_authorization` /
`DRAFT_DAY_AUTHORIZATION.json`) lets an owner explicitly, per-artifact-hash, per-player-id,
time-boxed authorize continuing on disclosed-stale rows.

**This is not a bug in the gate or the bypass mechanism.** Both are real, correctly designed,
already well-documented (their own docstrings state the safety conditions precisely). The
real problem is diagnostic quality: when every row fails this one real check, the top-level
message was the generic "Projection snapshot has no rankable player rows." -- true, but gives
no hint of the real cause or the real fix.

**Urgent, real, live finding**: this is not merely a test-fixture artifact. Read-only-traced
directly against the **real owner AppData install**
(`...\com.ninerswarroom.redraft\state\redraft\projections\2026\current.csv`, never written
to): **all 608 real rows are currently blocked** -- both the veteran component
(`source_as_of=2026-08-08`) and the rookie component (`source_as_of=2026-07-30`) are past the
30-day window as of the real current date (verified: `datetime.now(UTC)` =
2026-09-08T20:27:48Z). The one real `DRAFT_DAY_AUTHORIZATION.json` present
(`OWNER_DRAFT_DAY_APPROVAL_2026_403N18TH`) was real, valid, owner-authorized, and correctly
scoped to the 2026-09-07 403 N 18th draft -- it self-expired at `2026-09-08T10:00:00Z`, exactly
as its own design intends ("Self-expires automatically after tonight's draft window; does not
persist beyond it"). **The owner's real, live install is currently unable to generate any
real ranking for any league**, until either a fresh governed projection admission (a new
`source_as_of`) or a new, real, owner-issued draft-day authorization is in place.

## Real, minimal, honest fix (diagnostic only -- no governance change)

Added `_draft_day_authorization_status()` (`redraft_engine_v1_service.py`) -- inspects the
same real authorization file `_load_draft_day_authorization` already reads, returning one of:
no file present / unreadable / malformed / unrecognized label / hash-mismatched (bound to a
different artifact) / expired (with the real timestamp) / active-but-not-covering. This
function **never changes which rows are admitted** -- it is read-only diagnostic text.

`load_projection_snapshot`'s `not players and not errors` branch now checks whether **every**
blocked row shares the exact same real freshness reason; if so, the top-level error becomes:

> "All N projection rows are blocked because source_as_of exceeds the 30-day freshness window,
> and \<real authorization status\>. A new governed admission with a current source_as_of, or
> an owner-issued draft-day authorization bound to this exact snapshot hash, is required
> before ranking can proceed."

Verified traced live against the real owner data (isolated read-only copy, `redraft_bootstrap()`):
this exact message now reaches the real, owner-facing `status.summary`/`status.errors` fields.
The partial-admission case (some rows covered by a real authorization, others not -- the
owner's own real veteran/rookie split) is unaffected: the generic message still applies there,
since not every row shares the one reason, and real per-row admission is unchanged and
verified correct.

## Real, honest answer to "VALID BUT STALE vs. hard block"

No softer path exists in real policy today beyond the existing, real, explicit, per-artifact,
per-player, time-boxed `DRAFT_DAY_AUTHORIZATION` bypass -- there is no general "valid but
stale, silently disclosed" ranking mode to preserve. Per the directive's own instruction ("if
policy genuinely requires blocking: make the exact missing authorization/action explicit"):
implemented that branch. No dates were changed, no authorization was extended, no freshness
check was loosened or disabled anywhere.

## Tests

`tests/test_projection_freshness_diagnostic_v1_20260908.py` -- 7 new tests, all built with
dynamically-computed dates (never a hardcoded calendar date, avoiding the exact "environmental
source_as_of date-cliff" this session found rotting several pre-existing, unrelated fixtures
in `test_redraft_engine_v1_service.py`): fresh data root/no authorization; existing data root/
expired authorization; hash-mismatched authorization; valid active authorization (real bypass
still works); veteran-component-authorized/rookie-component-still-blocked (the owner's own
real scope pattern); fresh rows never blocked; two unrelated data roots (leagues) do not leak
an authorization across each other. All pass.

Full regression: `test_projection_freshness_diagnostic_v1_20260908.py` (7/7),
`test_decision_bundle_service.py` + `test_shadow_numeric_authorities_service.py` (all pass,
77 total). Pre-existing failures in `test_redraft_engine_v1_service.py` (hardcoded-date
fixtures, same root cause, not this session's origin) and
`test_validate_admitted_redraft_2026_combined.py` remain exactly as they were --
message text changed (now more informative), real pass/fail outcome unchanged. Both real
boards re-verified byte-identical. The real owner AppData `current.csv` and
`DRAFT_DAY_AUTHORIZATION.json` files were read (copied to an isolated tmp dir for the
facade-level trace) but never written to -- verified via a final sha256 check matching the
receipt's own bound hash exactly.

## Real, disclosed action item (cannot be self-issued)

The owner's real install needs one of the following, real owner action, before their next
real draft: (1) a fresh governed projection admission with a current `source_as_of` (the
normal, non-emergency path), or (2) a new, real, owner-authorized `DRAFT_DAY_AUTHORIZATION.json`
scoped to the next real draft, following the exact same real pattern as the expired one. This
session cannot self-issue either -- both are real governance-approval actions requiring the
owner's own authorization, per this project's own established discipline.

## Status

Section 1: **DONE.** Real root cause traced end-to-end; real, honest, actionable diagnostic
implemented and tested; no governance semantics changed; the real, live owner-facing blocker
is now precisely explained rather than vaguely reported.
