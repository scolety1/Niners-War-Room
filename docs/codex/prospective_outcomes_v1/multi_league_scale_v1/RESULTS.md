# Multi-League Scale Characterization V1 -- Real Results (Work Unit 19)

Two real, reproducible harnesses, never blended:

- **Backend** (`scripts/run_multi_league_scale_benchmark_v1.py`): real
  `DesktopBackendFacade` calls (`activate_redraft_profile` ->
  `redraft_data_health` -> `redraft_league_workspace_context`, plus
  `redraft_player_availability_status` for the status-fanout, plus
  isolated `activate_redraft_profile` for league switch), against
  isolated, LOCAL-provider profile sets of 5/10/25/50 leagues under a
  fresh temp `redraft_root` each time (real bundled projection snapshot,
  `repo_root=REPO_ROOT`, never the owner's real AppData store). Raw
  output: `backend_results.json`.
- **Frontend** (`desktop/apps/redraft/src/attention-center-scale-benchmark.test.ts`,
  a real vitest test file, 13 tests, all passing): the REAL, shipped
  `runAttentionCenterAggregation`/`searchPlayerAcrossLeagues` functions
  from `attention-center.ts`, imported directly (never reimplemented),
  run against a fake client at two settings -- 0ms delay (isolates pure
  JS orchestration overhead) and this pass's own real-measured backend
  per-call delays (a realistic end-to-end estimate). Raw output:
  `frontend_bench_results.json`.

Neither harness touches the owner's real Sleeper leagues or real AppData
profile store. Every profile is LOCAL-provider, so the Sleeper-specific
sub-fetches `fetchLeagueAttention` performs for a `sleeper` profile
(my roster/free agents/opponent rosters) are NOT exercised at scale here
-- see "Scope, disclosed" below.

## Real numbers -- backend (median / P95, 5 reps per size, 30 league-switch
## samples per size)

| Leagues | Attention Center fan-out (activate+dataHealth+workspaceContext), total | Per-league: activate | Per-league: dataHealth | Per-league: workspaceContext | Status-fanout total | League switch (isolated) |
|---:|---:|---:|---:|---:|---:|---:|
| 5  | 213.5ms / 229.8ms  | 0.78ms / 1.09ms | 27.4ms / 28.8ms | 14.2ms / 16.2ms | 3.5ms / 4.2ms   | 0.56ms / 0.58ms |
| 10 | 437.6ms / 451.2ms  | 0.78ms / 1.08ms | 27.5ms / 31.7ms | 14.2ms / 15.3ms | 7.4ms / 9.1ms   | 0.58ms / 0.66ms |
| 25 | 1076.5ms / 1082.4ms| 0.74ms / 0.94ms | 27.4ms / 29.5ms | 14.2ms / 15.2ms | 18.7ms / 19.4ms | 0.59ms / 0.67ms |
| 50 | 2150.2ms / 2161.4ms| 0.73ms / 0.92ms | 27.3ms / 29.6ms | 14.2ms / 15.0ms | 35.8ms / 37.2ms | 0.57ms / 0.65ms |

Per-league cost is flat across every tested size (~42.7ms at n=5, ~43.0ms
at n=50 -- ratio 1.007, see `linearityCheck` in the raw JSON): **linear
scaling, no superlinear behavior at any tested size.** League switch alone
(no data-health/workspace-context reads) is sub-millisecond and completely
flat with N, as expected (a single JSON read/write, independent of how
many OTHER profiles exist).

**A real methodological finding this pass caught and corrected before
trusting any number**: `tracemalloc.start()` measurably inflated every
real call's wall time by roughly 5x when first tried in the SAME pass as
timing (dataHealth 27ms -> 138ms, workspaceContext 14ms -> 71ms, confirmed
by a live side-by-side comparison). The script now runs two SEPARATE
passes per size -- one for timing (no tracemalloc), one for memory only
(fresh store, tracemalloc active, timing from that pass discarded) --
rather than reporting a tracemalloc-instrumented number as real latency.

## Real numbers -- memory (tracemalloc peak, separate pass from timing)

| Leagues | tracemalloc peak |
|---:|---:|
| 5  | 1988 KiB |
| 10 | 1999 KiB |
| 25 | 2104 KiB |
| 50 | 2126 KiB |

Peak traced-heap allocation is essentially flat (~2 MiB) across every
tested size -- no evidence of per-league memory accumulation in the
Attention Center fan-out path itself (each league's health/workspace
payload is transient within the loop, not retained).

Windows has no `resource` module (confirmed live: `ModuleNotFoundError`),
so `tracemalloc` is the only measurement used, per the directive's own
"don't over-engineer memory measurement" instruction. No `psutil` is
installed either (confirmed live) -- real process RSS was not measured;
Python-heap peak allocation was judged sufficient given the flat result.

## Real numbers -- frontend orchestration (median / P95, from
## `frontend_bench_results.json`)

| Leagues | JS overhead only (0ms backend, 41 reps) | Realistic end-to-end (real-measured delays, 9 reps) | Cross-league player search (41 reps, 200 rows/league) |
|---:|---:|---:|---:|
| 5  | 0.13ms / 0.33ms | 234.3ms / 237.3ms  | 0.003ms / 0.010ms |
| 10 | 0.13ms / 0.32ms | 471.2ms / 474.8ms  | 0.004ms / 0.011ms |
| 25 | 0.27ms / 0.39ms | 1178.3ms / 1181.7ms| 0.008ms / 0.009ms |
| 50 | 0.56ms / 0.87ms | 2364.8ms / 2369.6ms| 0.014ms / 0.015ms |

Pure JS orchestration overhead is negligible at every tested size (well
under 1ms even at 50 leagues) -- confirming the real bottleneck is
entirely the sequential backend round trips, not the TypeScript loop
itself. The "realistic end-to-end" column corroborates the backend
harness closely (2365ms vs. the backend's own 2150ms at n=50 -- both
measured completely independently, in different languages, using this
same pass's own real per-call latency numbers as the fake client's
delay). Cross-league player search is a plain in-memory substring filter
and stays sub-millisecond through 50 leagues x 200 rows/league.

## SCALE FINDING

**Acceptable at all four tested sizes (5/10/25/50 leagues).** Scaling is
linear, not superlinear, confirmed two independent ways (backend
per-league-cost ratio 1.007 across a 10x size range; frontend isolated-
overhead measurement showing negligible orchestration cost on top of the
linear backend cost). The real, architecturally-necessary hot path is the
SEQUENTIAL nature of the fan-out itself (one active-profile pointer on the
backend, documented extensively in `attention-center.ts`'s own comments as
a deliberate safety property, not an oversight) -- at 50 leagues this
costs ~2.1-2.4s median for a full Attention Center refresh, noticeable but
not the directive's own "clearly unacceptable" bar (multi-second
super-linear blowups). **No fix attempted or warranted**: parallelizing
the fan-out would mean activating more than one profile "at once" against
a backend with exactly one active-profile pointer -- the same state-leak
risk class `attention-center.ts`'s own extensive comments and regression
tests already guard against. That would be a real architecture change
(a per-profile-scoped read path, or a queueing/pooling layer), well beyond
this pass's "small, bounded, equivalence-proven fix" risk bar -- correctly
left as a real, precisely-documented open item rather than attempted here.

## Scope, disclosed

- Every bulk-generated profile this pass used is `provider="local"` (per
  the directive's own safety instruction: never touch real Sleeper
  leagues for bulk generation). `fetchLeagueAttention`'s three
  Sleeper-only sub-fetches (my roster, free agents, opponent rosters) are
  therefore NOT exercised at scale by this pass's own harness -- only
  their COST for one real league is known (see the performance
  characterization RESULTS.md's real Fantasy Gamers numbers: Home/Lineup/
  etc. surfaces that DO make these calls run into the seconds, dominated
  by real Sleeper network I/O, not by Attention-Center-specific logic).
  A future worker wanting a genuine "50 real-shaped Sleeper leagues"
  estimate could analytically combine this pass's linear per-league
  Attention-Center cost with the performance characterization's own
  per-call Sleeper-read costs, but should not fabricate 50 fake Sleeper
  league ids to do it for real.
- The "realistic" frontend delay constants are literal numbers copied from
  this pass's own real backend measurement (see the comment in the test
  file) -- there is no cross-language import path in this repo, so if a
  future re-run of the backend script produces materially different
  numbers, the frontend file's constants should be updated to match (noted
  in that file's own comment).
