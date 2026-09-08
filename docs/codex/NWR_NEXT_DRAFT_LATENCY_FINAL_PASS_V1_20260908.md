# Next-Draft Final Blocker Closure — Section 7: One More Safe Latency Pass V1

**Context:** Follow-up directive "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE", section 7. Current:
~5.8-6.95s (from the prior class-time hardening run's own real measurement).

## Real, fresh profiling run

Ran two fresh, real cProfile passes: (1) a heavy synthetic workload (200 trials, 20
candidates, 91.7s -- deliberately over-scaled to surface the hot path with maximum real
signal) and (2) a workload matched to the real, exact production `FAST` preset
(`max_rav_candidates=8, rav_trials=3` from `desktop_facade.py`'s own real `rav_preset`
constant, ~1.77s on this session's smaller synthetic fixture).

**Both real profiles show the identical hot-path signature already found and disclosed in
the prior class-time run**: `_select_asset` dominates (29.4s of its own 91.7s in the heavy
run; the same shape at the lighter scale), broken down into:

1. `_seeded_unit`'s real cryptographic hash cost (SHA256 `digest`/`openssl_sha256`/`encode`/
   `from_bytes`) -- the real, per-candidate deterministic jitter. Explicitly, deliberately
   **not touched**: changing its algorithm would alter real, shipped, reproducible
   recommendation values, which this section's own instruction ("do not restructure Monte
   Carlo or reduce simulation quality") forbids.
2. The cached `_cached_roster_candidate_allowed`/`_cached_roster_need_adjustment` wrapper
   overhead -- already memoized (prior session's own fix); the remaining cost is the real,
   unavoidable per-candidate dict lookup itself, not redundant computation.
3. `_select_asset`'s own real per-call overhead: rebuilding `roster = Counter(...)` from the
   full `state["picks"]` list, and iterating the full `pool` to build `available` -- **both
   already disclosed** in the prior session's own finding as requiring a real, riskier
   restructuring of `_advance_cpu`'s calling convention (an incrementally-maintained roster/
   pool instead of full rebuild-per-call) to fix safely.

## No new safe optimization found

Reviewed `_seeded_unit`'s own 4-line implementation directly for any loop-invariant,
equivalence-preserving micro-optimization (e.g., reusing a hasher object, avoiding redundant
string formatting) -- it is already minimal; there is no redundant work to remove without
touching the real algorithm itself. Considered whether memoizing `_seeded_unit`'s own real
output by `(seed, pick_number, player_id)` across Monte Carlo trials could help -- ruled out:
the whole point of a Monte Carlo trial is a materially different seed/outcome per trial, so
the same real key essentially never repeats across trials, making a cache pure overhead with
no real hit rate.

**No obviously loop-invariant, equivalence-testable, low-risk optimization exists beyond what
this session's own prior class-time work already applied.**

## Disposition: STOP, per the directive's own explicit instruction

"If no safe improvement exists: STOP. Record 6s-class latency as accepted next-draft
limitation." That is the real, honest conclusion here. **~5.8-6.95s (real, production-scale,
FAST-preset measurement from the prior class-time run) remains the accepted next-draft
latency** -- confirmed, not re-measured to a new number, since this pass's own synthetic
fixture is smaller than the real ~530-row admitted universe and would not produce a directly
comparable apples-to-apples figure. No code change this unit.

## Status

Section 7: **DONE.** Real, fresh profiling confirms the prior finding stands; no new safe
optimization exists; stopped per instruction.
