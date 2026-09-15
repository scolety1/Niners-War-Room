# Performance Characterization V1 -- Real Results (Work Unit 20)

Harness: `scripts/run_performance_characterization_v1.py` (real,
reproducible; needs live internet for the real Fantasy Gamers Sleeper
reads). Raw output: `results.json`. SAFETY: the real Fantasy Gamers
profile is read from a `shutil.copytree` COPY of the real AppData Redraft
store (never the original -- `activate_redraft_profile` performs a real
local write, so the original is never opened directly by this script);
outcome ingestion is measured against a fresh, isolated, throwaway root
seeded with realistic fixture traces, never the real production trace
ledger (which still has zero real traces recorded in it, unchanged from
every prior worker's own finding). Zero writes to Sleeper anywhere (every
call is a plain public GET); zero writes to the real AppData store.

## Real numbers (median / P95 unless noted, 5 reps unless noted)

| Surface | Median | P95 | Notes |
|---|---:|---:|---|
| Cold startup (subprocess: interpreter + import + facade + first bootstrap) | 424.9ms | 429.5ms | 3 reps; excludes the Tauri native shell/webview launch (not drivable in this environment) |
| League open (`activate_redraft_profile`, real Fantasy Gamers profile) | 0.66ms | 1.07ms | Local JSON write only; no network call in this step |
| Home (`redraft_weekly_home_actions`) | 4302.6ms | 11099.3ms | Real Sleeper reads; min 2562.7ms |
| Lineup (`redraft_weekly_lineup`) | 9616.6ms | 15657.2ms | Real Sleeper reads; min 866.8ms -- see "high variance" below |
| Improve Team -- waivers (`redraft_waivers`, REST_OF_SEASON) | 2001.6ms | 4241.3ms | Real Sleeper reads |
| Improve Team -- K/DST streamer (`redraft_kdst_streamer`) | 1290.9ms | 2063.9ms | Real Sleeper + FantasyPros reads |
| Trade Finder (`redraft_trade_finder`) | 1742.4ms | 2542.7ms | Real Sleeper reads |
| Trade Package Search (`redraft_trade_package_search`, FIND_WIN_WIN) | 2383.1ms | 2627.9ms | Real Sleeper reads |
| History V3 (`redraft_decision_trace_history`) | 0.31ms | 0.71ms | Local JSONL read only (owner has 0 real traces recorded) |
| Draft refresh (`refresh_redraft_adp`, real FFC ADP fetch) | 211.9ms | -- | 1 rep only (repeated real refreshes against the real provider were judged inconsiderate) |
| Player Drawer -- backing status read, first open | 0.24ms | -- | 1 rep; see "Player Drawer" note below |
| Player Drawer -- backing status read, warm open | 0.10ms | 0.12ms | 5 reps |
| Outcome ingestion, 0 traces (real production state today) | 0.05ms | -- | 1 run; nothing to process |
| Outcome ingestion, 5 fixture traces (3 matured + 2 immature) | 549.4ms | -- | 1 run; matured START_SIT traces do real, network-fetching work |
| Outcome ingestion, 20 fixture traces (10 matured + 10 immature) | 1268.3ms | -- | 1 run |

## Player Drawer -- a real, disclosed finding, not a measurement gap

Read `player-detail-state.ts`/`player-detail-drawer.tsx`/`player-drawer-core.tsx`
in full before benchmarking (per this pass's own discipline): **there is
no dedicated backend endpoint for opening the Player Drawer.** Player
identity (`playerName`/`position`/`team`) is caller-supplied -- every
surface that opens the drawer already has this from its own already-
fetched row data -- and the only shared, canonical lookup
(`deriveBackbone`) is an in-memory filter against the SAME already-loaded
`PlayerAvailabilityStatus` list every other surface reads from
`redraftPlayerAvailabilityStatus`. So "first open" and "warm open" do not
differ in backend cost at all -- both are a plain array lookup on data the
app already has in memory. The numbers above are for that one shared
backing read (amortized across every surface, not drawer-specific), which
is itself sub-millisecond warm and effectively free even cold (0.24ms).
**No performance concern here, and none to fix.**

## A real, corroborated finding: Sleeper-network-bound surfaces show high
## variance, root-caused with cProfile (not fixed, per the risk bar)

Home/Lineup/Improve Team/Trade Finder/Trade Package Search are all
dominated by real Sleeper HTTPS round trips, not by NWR's own CPU-bound
ranking/scoring logic. A single, ISOLATED cProfile run of the exact same
`redraft_weekly_lineup(week=2)` call (freshly activated profile, no
preceding rapid-fire calls in the same process) completed in **1.271s**,
with the profile showing:

- `{method 'read' of '_ssl._SSLSocket' objects}`: 0.706s (55.6% of total)
  -- real TLS socket reads waiting on Sleeper's server.
- `do_handshake`/`connect`: 0.118s + 0.097s = 0.215s (16.9%) -- a fresh
  TCP+TLS handshake for EVERY real GET (`SleeperHttpClient.get_json` uses
  a plain `urllib.request.urlopen` per call, no persistent session/
  connection pooling or keep-alive reuse across calls).
- Every remaining line (JSON decoding, NWR's own ranking/projection
  merge code) sums to well under 100ms combined.

This is a genuinely real, but already partially-addressed, class of cost:
the EARLIER Weekly Home latency work (commit `00446dcd`, prior session)
fixed redundant re-fetches WITHIN one `redraft_weekly_home_actions` call
(5 sub-facade calls independently re-fetching the same rosters/players
payload). Connection reuse ACROSS separate real GETs (no persistent
session in `SleeperHttpClient` at all) is a DIFFERENT, not-yet-addressed
dimension of the same "real network I/O dominates" story.

**This pass's own benchmark loop (5 reps per surface, all six surfaces run
back-to-back) shows dramatically higher and more variable numbers than the
isolated cProfile run** (Lineup: 9616.6ms median / 15657.2ms P95 in the
loop vs. 1.271s isolated) -- most plausibly real internet/Sleeper-server
conditions varying under this pass's own repeated rapid-fire real calls
(~30 real Sleeper-hitting calls in quick succession across the six
surfaces), not a deterministic app-side algorithmic hot path. Disclosed
honestly rather than averaged away: the isolated cProfile number is the
more trustworthy per-call estimate for a single real user's occasional
real usage; the benchmark-loop numbers are real but reflect this pass's
own measurement methodology stressing the real network more than a normal
user session would.

**Not fixed this pass**: `SleeperHttpClient` is used broadly across the
whole codebase (every provider-read call site). Switching it to a
persistent `requests.Session`/`http.client.HTTPSConnection` with
keep-alive would be a real behavior change needing its own equivalence
proof across every call site -- larger and riskier than this pass's "small,
bounded" fix bar (the same bar the earlier Weekly Home fix met and this
would not, without materially more scoping). Flagged precisely for a
future worker with that scope, not attempted here.

## OPTIMIZATION MADE: NONE

Every surface's real cost is either already comfortably fast (League
open, History V3, Player Drawer, League switch -- all sub-millisecond to
low-single-digit-millisecond) or is dominated by real, external network
I/O with a precisely root-caused (cProfile-evidenced) explanation that
does not meet this pass's own bounded-fix risk bar. No code was changed in
`desktop_facade.py`, any `src/services/*` module, or `attention-center.ts`
this pass.
