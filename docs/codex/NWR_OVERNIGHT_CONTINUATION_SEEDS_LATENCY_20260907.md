# Continuation-seeds latency check (NWR Overnight repair pass, 2026-09-07)

Real timing against the practice profile (`nwr_gui_test_root`,
`4b4a990faf124ce7a5d612537ba5943b`, pick 23, FAST preset), measured directly
via `DesktopBackendFacade.redraft_decision_bundle` -- not estimated.

## Before this pass (continuation_seeds=1, the unchanged prior default)

| call | latency |
|---|---|
| cold | 4.214s |
| warm | 2.250s |
| warm | 2.239s |

## After wiring continuation_seeds=3 for FAST (this pass)

Candidate count also grew from 8 to 12 in this same measurement window (the
K/DST shortlist-injection fix landed earlier in this pass and was already
live) -- both changes are reflected together below, which is the real
number the owner's draft clock actually experiences.

| call | latency |
|---|---|
| cold | 8.407s |
| warm | 6.535s |
| warm | 6.581s |

## Verdict

~6.5s warm, well inside the documented 60-second draft-clock budget (see
`DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md` for the original FAST-preset
budget rationale). STANDARD/DEEP were not independently re-measured this
pass (they see fewer live Suggestions refreshes in practice); DEEP's
`continuation_seeds=5` is a proportionally bounded extension of the same
FAST multiplier, not independently latency-verified here -- disclosed, not
assumed safe.
