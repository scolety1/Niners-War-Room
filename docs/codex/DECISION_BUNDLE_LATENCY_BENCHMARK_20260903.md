# DecisionBundle real latency benchmark (Owner Test Candidate V1, section 11)

Real measurements from `scripts/run_decision_bundle_latency_benchmark_v1.py`
(median of 3 runs, 240-player synthetic fixture matching this session's
established shadow-authorities benchmark shape, 12-team league, ~10
Suggestions candidates):

| Preset | trials | seasons | candidates | comparable_leagues p50 | decision_bundle p50 | total p50 | worst |
|---|---|---|---|---|---|---|---|
| FAST | 2 | 20 | 8 | 0.125s | 0.662s | **0.787s** | 0.790s |
| STANDARD | 20 | 100 | 10 | 1.268s | 2.546s | **3.814s** | 3.834s |
| DEEP | 50 | 200 | 12 | 3.126s | 6.463s | **9.592s** | 9.601s |

`comparable_leagues` (the Monte Carlo reference population) is cached in
the real facade per `(profile_id, universe_hash, market_hash, trials,
seed)` — the numbers above are the first, uncached call; every
subsequent DecisionBundle call for the same profile/universe/market
during a draft pays only the `decision_bundle` cost (FAST: ~0.66s).

## What this means for the default

**FAST is the default** (`redraft_decision_bundle(profile_id, speed="FAST")`,
also the parameter default) — the only preset that comfortably clears the
directive's `<2 seconds` target with real margin, on both cold and warm
calls, against an owner's 60-second pick clock. STANDARD and DEEP are
available (`speed="STANDARD"`/`"DEEP"`) for a non-time-pressured
inspection (e.g. Compare, Score Details) but are not selected
automatically during live play.

## What is not yet measured

IPC/HTTP round-trip and frontend render time (the directive's other two
latency components) — not measured this wave, since the live HTTP route
and frontend wiring were built after this benchmark; the backend
computation time above is the dominant, now-real cost. A follow-up
measurement once the full request/response/render path is live would
complete the p50/p95/worst picture end-to-end.
