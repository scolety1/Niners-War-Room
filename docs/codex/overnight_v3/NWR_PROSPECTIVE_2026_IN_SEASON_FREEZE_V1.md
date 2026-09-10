# NWR Prospective 2026 In-Season Freeze V1

Cut because real, tested new in-season capability shipped this pass -- not a routine
end-of-session freeze. Does NOT overwrite the existing draft-engine freeze (V7); that
freeze covers draft-day only and is untouched by this document.

**HEAD at freeze time**: `20b72cb8898754300218aa641d3b4c0fbab17dad` (branch
`overnight/nwr-full-advance-v3-20260909`, worktree `C:\NWR\overnight-full-advance-v3`).

## What changed this pass, and why it was possible

Three prior overnight passes on this branch (Part 2, Part 3, the retry-queue report)
each independently reached a BLOCKED verdict on weekly per-player fantasy projections
after checking the FFA archive (real, season-level only) and `nflreadpy` (real, but
schedules/stats, not forward point forecasts). This pass ran the two live-platform
checks the governing directive named as genuinely unaudited (ESPN's public
`kona_player_info` endpoint, Sleeper's undocumented `projections/nfl/...` endpoint) and
found a real, live, per-player, per-week source: Sleeper's projections endpoint. That
finding unblocked Start/Sit, and downstream, Waivers' THIS_WEEK mode and the Weekly Home
actions section.

## Weekly source

- **Source**: `SLEEPER_WEEKLY_PROJECTIONS_V1` -- Sleeper's undocumented, unauthenticated
  `GET /v1/projections/nfl/{season_type}/{season}/{week}`, fetched live on every call
  through the existing `SleeperHttpClient` (no local cache, no staleness risk by
  construction -- a fetch failure raises rather than reusing a prior week).
- **Coverage this pass's verification**: 9,420 total player entries in the raw payload
  for 2026 Week 1, 863 with a nonzero `pts_ppr`; identity cross-checked against the real
  `players/nfl` catalog for several real names (Jalen Hurts, Christian McCaffrey, Puka
  Nacua, Brandon Aubrey).
- **Adapter**: `src/services/weekly_projection_service.py`. Skill positions (QB/RB/WR/TE)
  scored via NWR's OWN existing `score_projection()` (`redraft_engine_v1_service.py`)
  from mapped raw stat categories -- real league-scoring-specific points. K/DST preserve
  Sleeper's own `pts_ppr`, labeled `SLEEPER_PROVIDER_SCORING`, never a fabricated NWR
  K/DST formula.
- **Freshness**: no cache -- every call is a live fetch; `source_status`/`source_as_of`
  are returned on every response.
- **Known real limits, disclosed, not fixed this pass**: undocumented by Sleeper (could
  change/break without notice); non-commercial-use posture per Sleeper's own docs
  (matches this app's existing Sleeper usage, not a new exposure); no per-player
  variance/uncertainty figure (CLOSE CALL labeling in Start/Sit uses a disclosed
  heuristic band, not a statistically derived one); no 2-point-conversion or weekly
  scoring-bonus fields mapped.

## Engine/component versions cut into this freeze

| Component | Version tag | File |
|---|---|---|
| Weekly projections | `SLEEPER_WEEKLY_PROJECTIONS_V1` | `src/services/weekly_projection_service.py` |
| Start/Sit lineup optimizer | `weekly_lineup_optimizer_service-v1` | `src/services/weekly_lineup_optimizer_service.py` |
| Waivers / Add-Drop / FAAB | `waiver_engine_service-v1` | `src/services/waiver_engine_service.py` |
| Redraft Trade Analysis | `redraft_trade_analysis_service-v1` | `src/services/redraft_trade_analysis_service.py` |
| Trade Finder | (same evaluator, no independent version) | `src/services/trade_finder_service.py` |
| In-season decision trace | schema v1 (append-only jsonl) | `src/services/in_season_decision_trace_service.py` |
| Weekly Home NWR Actions | composition of the above, no independent model | `desktop_facade.redraft_weekly_home_actions` |
| ROS ranking / scoring | unchanged, existing governed ranking | `redraft_engine_v1_service.py` (untouched) |
| `marginal_roster_utility_v2` | CLOSED, unchanged, called read-only | `shadow_numeric_authorities_service.py` (untouched) |

## Data versions

- Weekly projections: `SLEEPER_WEEKLY_PROJECTIONS_V1` (live, no snapshot).
- ROS ranking: whatever governed 2026 projection snapshot the active profile's store
  has installed (unchanged by this pass -- this worktree's own default store still has
  none installed, same disclosed gap as every prior pass).
- Status overrides: `config/nwr_verified_current_player_status_overrides_v1.json`
  (unchanged, ONE shared layer, reused not duplicated).
- Free agent / opponent roster reads: live Sleeper `players/nfl` + `league/.../rosters`
  (unchanged existing capability, reused).

## New HTTP surface (backend wired, no new frontend UI this pass -- disclosed, not
## claimed)

- `POST /api/v1/redraft/weekly-projections`
- `POST /api/v1/redraft/weekly-lineup`
- `POST /api/v1/redraft/waivers`
- `POST /api/v1/redraft/trade-analysis`
- `GET  /api/v1/redraft/trade-finder`
- `POST /api/v1/redraft/weekly-home-actions`

All live-verified end-to-end against a real running backend this pass (real auth, real
routing, real honest error responses when no Sleeper context exists -- see the
integrated-acceptance section of the final handoff report for the exact verified
requests/responses). No frontend UI panel was built for any of these yet; this matches
the branch's own established "engine wired, no visible UI toggle yet" precedent (the
Team Score V2/Equity V2 challenger layer).

## Known blockers, unchanged or newly disclosed

- No governed 2026 projection snapshot is installed in this worktree's default store
  (unchanged, requires owner-issued approval receipt this session cannot self-issue) --
  ROS-dependent paths (REST_OF_SEASON waivers, Trade Analysis/Finder, Weekly Home
  Actions' WAIVER/TRADE sections) require it to do anything beyond return an honest
  `RANKINGS_UNAVAILABLE` error.
- Compare mode extension (THIS_WEEK/REST_OF_SEASON/ROSTER_FIT/TRADE) NOT built this
  pass -- all four modes' backend data now exists and is reachable (weekly projections,
  existing ROS ranking, marginal utility via the waiver engine, trade analysis), but the
  frontend UI work to add mode selection to the existing Compare component was not
  attempted. Real, scoped next increment.
- Trade Finder searches only the weakest `candidates_per_side` (default 8) roster
  pieces per side and only 1-for-1 packages -- a disclosed simplification, not a full
  combinatorial/multi-player search.
- No acceptance-probability/"likely to accept" figure exists anywhere in FAAB or Trade
  Finder -- deliberately not estimated (no real signal in this app supports one).

## Test evidence at freeze time

- New/touched backend unit tests: 63 new tests across 6 new service files, all passing.
- Full targeted regression (new services + desktop application API + adjacent existing
  services): **235 passed, 5 pre-existing failed (exact documented baseline,
  unrelated), 1 skipped**.
- Frontend: `vitest run` 16/16 files, 154/154 tests pass (unchanged, zero frontend files
  touched this pass); `tsc -b` clean.
- Live backend boot + all 6 new endpoints exercised against a real running server:
  correct routing, correct auth, correct honest error responses (see final handoff
  report).

## Explicitly NOT overwritten

- `NWR_NEXT_DRAFT_READINESS_FREEZE_V7` (draft-engine freeze) -- untouched.
- `marginal_roster_utility_v2` promotion / MODEL STATUS CLOSED -- untouched, called
  read-only throughout this pass's new code.
- Team Score V2 / Equity V2 / Raw Action Value / Pick Score / Decision Confidence --
  untouched.
