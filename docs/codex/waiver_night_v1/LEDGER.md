# NWR Waiver Night V1 -- Ledger

Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`. Not merged, not pushed, not deployed.

## Worker 1 (this pass) -- Work Unit 1: FantasyPros JAC / Sleeper JAX
## team-code alias fix

Start HEAD `2612369a` (the prior cycle's real DST identity-matching fix,
which left the JAC/JAX gap explicitly documented as a separate,
out-of-scope issue -- see that commit message and
`docs/codex/prospective_outcomes_v1/DST_IDENTITY_MATCHING_FIX_PROPOSAL_V1.md`).

### What was found

Real, live-confirmed root cause: FantasyPros' K/DST consensus API reports
Jacksonville's team code as `"JAC"`; Sleeper's real `players/nfl` catalog
and every real roster entry report it as `"JAX"`. The shared identity
boundary both sides feed through, `_identity()` in
`src/services/fantasypros_kdst_consensus_service.py`, normalized team
codes with plain `str(team or "").upper().strip()` -- no alias table --
so a real Jacksonville row from either provider never matched the other.

No existing SHARED normalizer was found (searched near
`fantasypros_kdst_consensus_service.py`, `_identity()`, and any
`team_alias`/`normalize_team`-shaped name). A local, duplicated
`TEAM_ALIASES` dict pattern (JAC->JAX, plus several others) already
exists independently in at least 4 other already-tested modules in this
codebase (`model_v4_fantasypros_identity_mapping_service.py`,
`outcome_v2_identity_bridge_service.py`,
`model_v4_stats_first_expected_value_service.py`,
`truth_set_v3_snap_share_import_service.py`, and a differently-shaped one
in `rotowire_local_team_status_service.py`) -- none of them are imported
by `fantasypros_kdst_consensus_service.py`, and none are structured as a
reusable shared utility. This confirms JAC->JAX (and the other aliases
below) as real, established facts in this codebase, not a guess -- but
also confirms no single shared boundary existed yet.

### What was built

**New**: `src/services/team_code_alias_service.py` -- one small, pure
module: `TEAM_CODE_ALIASES` (dict) + `normalize_team_code(value)`
(uppercase, strip, alias-lookup, pass-through-if-unknown). Canonical form
is Sleeper's/modern nflverse's own codes.

**Modified**: `src/services/fantasypros_kdst_consensus_service.py` --
`_identity()`'s `normalized_team = str(team or "").upper().strip()`
became `normalized_team = normalize_team_code(team)`. This is the ONLY
production code change. `_identity()` is the single shared boundary every
Sleeper-vs-FantasyPros identity comparison in this file already goes
through (`sleeper_streamer_actions`, `sleeper_free_agent_pool`), so the
fix applies symmetrically without touching any call site.

**Did NOT** refactor the other 4-5 files' own local `TEAM_ALIASES`/
`_team_key` copies to import the new shared module -- that is real,
available follow-up cleanup (duplication reduction), but touching 4+
already-tested, unrelated pipelines (`model_v4`, `truth_set_v3`,
`outcome_v2`) was judged out of scope for a same-night, narrowly-scoped
identity fix. Flagged as an open issue below, not silently dropped.

### Real live verification (2026-09-15, read-only)

- FantasyPros K/DST consensus API (`NWR_FANTASYPROS_API_KEY` already
  configured in this environment), queried live for DST and K, weeks
  0-5, season 2026: **every real Jacksonville row returned `"JAC"`,
  never `"JAX"`**, across every query. FantasyPros' own consensus
  endpoint only ever returns its own top-10-ranked rows per
  position/week query -- confirmed structurally, not assumed -- so no
  single query ever returns all 32 teams; the union across weeks 1-5 and
  both positions surfaced only 14 distinct team codes total.
- Sleeper `players/nfl` catalog, fetched live: exactly 32 real `DEF`
  (DST) entries, one per franchise, team codes = the full modern set
  (`JAX`, `LAR`, `LV`, `LAC`, `WAS`, etc. -- never `JAC`/`STL`/`SD`/
  `OAK`/`WSH`/`ARZ`).
- Real Fantasy Gamers league (`1312983576827920384`, owner user id
  `1000507609050337280`, resolved live from username `scolety`): real
  rosters fetched, combined with the real live FantasyPros week-1 DST
  consensus (10 rows) and the real live Sleeper `players/nfl` catalog,
  run through the FIXED `sleeper_streamer_actions`. Result: **10/10 of
  the real, provider-supplied DST rows now resolve correctly** (9
  `ROSTERED_ELSEWHERE`, 1 genuinely-unrostered `ADD` for Detroit) --
  Jacksonville (`ecr=1`) now correctly resolves `ROSTERED_ELSEWHERE`
  instead of the pre-fix `AVAILABLE`. This matches the prior session's
  "8 of 10" pre-fix baseline exactly (1 genuine unrostered team + 1 JAC
  failure = 8 correctly resolved pre-fix; only the DET slot was ever
  meant to show `AVAILABLE`).
- Same real-data method repeated for K (real FantasyPros K consensus,
  same real league rosters): Cam Little (Jacksonville's real K) now also
  correctly resolves `ROSTERED_ELSEWHERE` instead of falling through as
  `AVAILABLE` -- a real, previously-undocumented second instance of the
  same JAC/JAX bug (K entries always carry `full_name`, so the K path
  was never broken by the *name*-matching gap the prior session fixed,
  but it WAS silently broken by this same team-code gap, since
  `_identity()`'s 3-part key requires team to match too).
- **Zero writes verified three ways**: (1) structural -- only GET
  requests were issued anywhere in this pass's own verification code and
  in the touched production file; grepped the touched files for
  `POST`/`PUT`/`PATCH`/`DELETE` method strings, zero matches; (2) grep of
  the actual diff for any Sleeper write-shaped call, zero matches; (3)
  before/after byte-diff of `GET league/{id}/rosters` around both the DST
  and the K real-data runs -- byte-identical both times (`6394` bytes,
  unchanged).

### Data-availability limit on "32/32"

FantasyPros' real K/DST consensus endpoint structurally caps at its own
top-10-ranked rows per query -- it is not possible to observe all 32 real
teams from a single real FantasyPros query, regardless of this fix. This
pass's real, honest claim is: **10/10 of the real rows FantasyPros
actually returned now resolve correctly** (up from 8/10 pre-fix), not a
literal "32/32" -- the other 22 real teams were never present in any
queried FantasyPros response this pass, live or historically (a provider
data-availability fact, not a remaining bug in the fix).

### The other aliases included, and why

`LA`->`LAR`, `STL`->`LAR`, `SD`->`LAC`, `OAK`->`LV`, `WSH`->`WAS`,
`ARZ`->`ARI` were added to `TEAM_CODE_ALIASES` alongside `JAC`->`JAX`.
These were **not** re-observed live against this specific FantasyPros
K/DST consensus endpoint this pass (it never returned a row for a team
needing one of them, in any week/position queried) -- they are carried
over from the 4 independent, already-tested FantasyPros-facing modules
listed above, which each independently arrived at the same aliases
against FantasyPros' other real feeds. This is real, established
in-codebase evidence, not an invented guess, and each one is a real
alias between a canonical-Sleeper-style code and a legacy/alternate code
that has genuinely applied to a currently-supported provider (FantasyPros)
at some point (LA relocations, Oakland->Las Vegas, Washington's name
change) -- no alias was added for a provider or franchise this codebase
does not actually touch.

### Tests

- `tests/test_fantasypros_kdst_consensus_service.py`: existing DST test
  fixture corrected to use the REAL FantasyPros code (`"JAC"`, was
  incorrectly `"JAX"` in the prior session's own test, which meant it
  never actually exercised the alias gap); 6 new tests added (identity
  boundary resolves JAC against JAX, ordinary codes unaffected,
  `normalize_team_code` covers every documented alias and passes unknown
  codes through, the alias table never maps a code to itself, K
  regression at the alias-table level).
- **New** `tests/test_team_code_alias_service.py`: 5 tests, dedicated
  coverage of the new shared module itself.
- `python -m pytest tests/test_fantasypros_kdst_consensus_service.py
  tests/test_team_code_alias_service.py -q`: **23 passed**.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability or
  fantasypros_kdst or team_code_alias"`): **509 passed, 0 failed**.
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** --
  the SAME 4 pre-existing failures the prior cycle's ledger documents at
  this exact worktree (`test_dynasty_facade_composes_real_governed_
  workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
  trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
  contract`, `test_facade_has_no_streamlit_or_app_component_dependency`).
  Re-confirmed live after this pass's changes, unrelated to this fix.
- `git diff` grepped for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): **zero matches**.

### Backend/model files changed this pass

- **New**: `src/services/team_code_alias_service.py`,
  `tests/test_team_code_alias_service.py`.
- **Modified**: `src/services/fantasypros_kdst_consensus_service.py`
  (2-line change: one new import, `_identity()`'s team normalization now
  calls `normalize_team_code`), `tests/test_fantasypros_kdst_consensus_service.py`
  (1 existing fixture corrected + 6 new tests).
- This ledger (new file/directory).
- Nothing in `desktop_facade.py`, `desktop_api/`, or any consumer/UI
  layer touched.

## OPEN ISSUES FROM WORKER 1 (Work Unit 1), CARRIED FORWARD

1. **Duplicate local `TEAM_ALIASES`/`_team_key` copies were not
   consolidated onto the new shared module.** At least 5 other files
   (`model_v4_fantasypros_identity_mapping_service.py`,
   `outcome_v2_identity_bridge_service.py`,
   `model_v4_stats_first_expected_value_service.py`,
   `truth_set_v3_snap_share_import_service.py`,
   `rotowire_local_team_status_service.py`) carry their own local alias
   dict, all overlapping but not byte-identical (some include `ARZ`,
   some don't; `rotowire`'s is a completely different shape -- full team
   names/nicknames, not provider codes). A future pass explicitly scoped
   to dedup could migrate these onto `team_code_alias_service.py`, but
   each one touches a different already-tested pipeline (model_v4,
   truth_set_v3, outcome_v2, rotowire) -- real, separate blast-radius
   review needed per file, not a single mechanical find/replace.
2. **The `TEAM_CODE_ALIASES` table's non-JAC entries are not reconfirmed
   live against the FantasyPros K/DST consensus endpoint specifically**
   (see "Data-availability limit" above) -- only corroborated from other
   already-tested modules' own historical verification. Worth a live
   recheck if/when FantasyPros' K/DST feed ever surfaces a Rams-era `LA`,
   `OAK`, or `WSH` row directly (it hasn't, across 5 real weeks x 2
   positions checked this pass).
3. **32/32 DST identity is not literally achievable from a single
   FantasyPros K/DST consensus query** -- that endpoint structurally
   returns only its own top-10-ranked rows per query. A real "all 32"
   check would need to union many real weeks' worth of real queries (as
   this pass did for a 14-team union across weeks 1-5) and would still
   depend on which teams FantasyPros chooses to rank each week, not on
   anything this fix controls.
4. **K identity was also silently affected by this same gap** (see "Real
   live verification" above, the Cam Little finding) -- this was not
   previously documented anywhere in this codebase's ledgers as a
   distinct K-side bug (only the DST full_name gap was documented). Now
   fixed by the same one-line change, verified live, but worth noting
   explicitly since no prior worker's finding named it.

## Worker 2 (this pass) -- Work Unit 2: current Sleeper roster sync
## verification, Work Unit 3: real free-agent pool verification

Start HEAD `63a81142` (Worker 1's JAC/JAX + K fix, above). Real, live,
read-only verification against the real Fantasy Gamers Sleeper league
(`1312983576827920384`, owner `scolety`, real user id
`1000507609050337280`, roster_id `9`), 2026-09-15, in-season week 2
(NFL `state/nfl`: `week=2`, games not yet started -- all `0.0` points,
a genuinely current, not-stale fact).

### Work Unit 2 result: PASS, with one real bug found + fixed

Verification method: instantiated the real `DesktopBackendFacade`
against this worktree's real, already-active `local_exports/redraft_v1`
profile (`941b99ade350410391b1b67c0890af79`, "Fantasy Gamers", already
the active profile -- no state was created or changed), called
`redraft_my_roster()`, and independently pulled the raw Sleeper
`league/{id}/rosters` + `state/nfl` + `league/{id}` + `league/{id}/users`
directly via `SleeperHttpClient` (GET-only), then diffed.

- **Owner roster (scolety, roster_id 9): exact match.** 15 players, 9
  starters, 6 bench, 0 reserve/IR (this owner has none on IR right now --
  see IR/reserve note below). Raw Sleeper player-id set == facade
  `redraft_my_roster()` player-id set (`raw_ids == facade_ids`: `True`,
  15/15, zero missing/extra either direction). Starter-id set also exact
  match (`raw_starter_set == facade_starter_set`: `True`).
- **League-wide roster table (raw, all 10 teams, for the record):**

  | roster_id | owner | players | starters | reserve | FAAB used |
  |---|---|---|---|---|---|
  | 1 | QuippyR | 16 | 9 | 1 | 0 |
  | 2 | JalenTheAsian | 16 | 9 | 1 | 0 |
  | 3 | SadiesLadies | 15 | 9 | 0 | 0 |
  | 4 | logans21 | 15 | 9 | 0 | 0 |
  | 5 | kdizzy7 | 15 | 9 | 0 | 0 |
  | 6 | Ootley | 15 | 9 | 0 | 0 |
  | 7 | LiLDcK | 16 | 9 | 1 | 0 |
  | 8 | JohnnyDisB | 14 | 9 | 0 | 0 |
  | 9 | **scolety (owner)** | 15 | 9 | 0 | 0 |
  | 10 | josh702 | 15 | 9 | 0 | 0 |

  League settings (raw): `waiver_type=1` (FAAB), `waiver_budget=100`,
  `reserve_slots=2`, `taxi_slots=0`, `total_rosters=10`,
  `roster_positions=[QB,RB,RB,WR,WR,TE,FLEX,K,DEF,BN,BN,BN,BN,BN,BN]`.
  Owner's remaining FAAB (raw `waiver_budget` minus this roster's
  `settings.waiver_budget_used`): **100/100** (nothing spent yet, real
  and current for week 2 preseason-of-the-week state). Sync timestamp:
  **2026-09-15, live pull this pass** (not a cached/stale read).

- **Real bug found and fixed:** `redraft_my_roster()` marked
  Marvin Harrison Jr. (the owner's own real rostered WR, Sleeper id
  `11628`) as `identityStatus: UNMATCHED_IDENTITY` even though he IS in
  NWR's own ranking data. Root cause: Sleeper's real `players/nfl`
  catalog drops generational suffixes (`full_name` = "Marvin Harrison",
  no "Jr.") while NWR's own ranking/consensus rows keep them ("Marvin
  Harrison Jr."). `_identity()` -- the SAME shared boundary Worker 1 just
  fixed for JAC/JAX -- alnum-normalizes the full string with no suffix
  handling, so "marvinharrisonjr" never equalled "marvinharrison". Live
  scan of all 564 rows in this profile's real ranking output found
  **26/26 real, currently-rostered-or-draftable players carrying a
  suffix (Jr./Sr./II/III/IV) failed this exact match before the fix**
  (Kenneth Walker III, Deebo Samuel Sr., Brian Thomas Jr., Michael Penix
  Jr., etc. -- full list in the diff/verification transcript). Confirmed
  zero name collisions introduced by stripping the suffix across all 564
  real ranking rows (no two different real players in this profile's
  ranking collapse to the same stripped name+position+team key).
  **Fixed** in `src/services/fantasypros_kdst_consensus_service.py`:
  `_identity()` now strips a trailing, whitespace-separated generational
  suffix token (`Jr`/`Sr`/`II`/`III`/`IV`/`V`, optional trailing period,
  case-insensitive) before alnum-normalizing the name. Guarded so it only
  strips a genuine trailing token (e.g. "Steve Smith" / "Marcus Levi" are
  unaffected -- confirmed via a dedicated over-stripping regression test).
  Re-verified live after the fix: Marvin Harrison now resolves
  `identityStatus: MATCHED` in the owner's real roster, with roster
  player-id/starter-id exact-match unaffected (still `True`/`True`).
- **Honest gap, not fixed (documented for the next worker, not silently
  dropped):** `redraft_my_roster()` has no `reserve`/IR field at all --
  every roster row is only ever `starter: true/false`, so a player on IR
  would render identically to an ordinary bench player, losing real
  information. This owner's own roster has 0 players on IR right now (3
  of the 9 opponent rosters DO have exactly 1 each, raw-confirmed above),
  so this pass could not reproduce a live *mismatch* against the owner's
  own data -- it is a real, disclosed completeness gap, not a proven
  wrong-data bug, and was deliberately NOT built out this pass (new UI
  surface / new facade field is feature work, not a same-night
  verify-and-fix scope). Flagged below for the next worker.
- Also directly verified (read-only, via `redraft_league_workspace_context()`,
  NOT modified -- this method is inside the hard-boundary-protected
  `LeagueWorkspaceContext` composition): `currentWeek` resolves live and
  correctly to **2** (matches raw `state/nfl`), `syncStatus: LIVE`, no
  `issues`. `matchupContext` came back `null` even though the real raw
  `league/{id}/matchups/2` endpoint DOES return real data (10 rows, all
  `0.0` points since week 2 hasn't kicked off). This was NOT
  investigated further or touched (hard boundary explicitly forbids
  `LeagueWorkspaceContext` semantics) -- flagged as an open question for
  whichever worker owns that surface, not assumed to be a bug.

### Work Unit 3 result: PASS

Verified `sleeper_free_agent_pool` (unchanged mechanism/name, still the
canonical one -- confirmed no newer successor exists) is genuinely
derived as (live Sleeper `players/nfl` catalog) MINUS (every currently
rostered player across all 10 real rosters), not a static file:

- Raw Sleeper player catalog: **12,227** real entries. Raw rostered-
  everywhere count (union across all 10 real rosters): **152**. Facade
  `redraft_free_agents()` free-agent count: **718** (position-filtered to
  `SLEEPER_FANTASY_POSITIONS`, inactive-excluded -- not `12227 - 152`,
  by design, confirmed correct via source read).
- **Zero overlap**, computed directly: intersection of the facade's
  free-agent Sleeper-id set with the raw all-rosters-rostered-id set is
  the empty set (`0` matches).
- **Real spot checks, both directions, across QB/RB/WR/TE/K/DEF:**
  - 8 of the owner's own real rostered players (Caleb Williams QB,
    Marvin Harrison WR, Carnell Tate WR, Ka'imi Fairbairn K, Jonathan
    Taylor RB, Michael Pittman WR, Trevor Lawrence QB, Travis Etienne
    RB): **none** appear in the free-agent list (all `False`, correct).
  - 8 real opponent-rostered players sampled across 4 different opposing
    rosters (Spencer Shrader K, Quinshon Judkins RB, Sam LaPorta TE,
    Chris Boswell K, Brian Thomas WR, Ladd McConkey WR, MarShawn Lloyd
    RB, Bucky Irving RB): **none** appear in the free-agent list (all
    `False`, correct).
  - 6 genuinely unrostered real, active, currently-on-an-NFL-team
    players, one per fantasy position (Salvon Ahmed RB/CHI, Jerry Jeudy
    WR/CLE, Behren Morton QB/NE, Oronde Gadsden TE/LAC, Ryan Fitzgerald
    K/CAR, Indianapolis DEF): **all 6** correctly appear as free agents
    (`True`).
  - (First attempt at the "genuinely unrostered" spot check picked
    inactive/no-current-team retired players by mistake -- those
    correctly do NOT show as free agents either, since
    `sleeper_free_agent_pool` requires a non-empty `team`; re-ran with
    `active is True and team` players and got clean `True`s above. Not a
    bug -- retired/teamless players are not real fantasy free agents.)
- **Unmatched-identity players are never silently dropped**: confirmed
  by code read -- `sleeper_free_agent_pool` always emits a row for every
  active, position-eligible, teamed catalog entry regardless of whether
  a ranking match was found; unmatched rows get
  `rankingAuthority: "UNRANKED"` / `playerId: ""` rather than being
  omitted. The suffix fix above (Work Unit 2's bug) directly improves
  this: fewer real players now incorrectly show `UNRANKED` when they
  actually have a real NWR ranking.

### Tests (this pass)

- New tests added to `tests/test_fantasypros_kdst_consensus_service.py`:
  `test_identity_boundary_strips_generational_suffix_sleeper_drops`,
  `test_identity_boundary_suffix_stripping_only_matches_a_trailing_token`,
  `test_sleeper_free_agent_pool_matches_ranking_despite_missing_sleeper_suffix`.
- `python -m pytest tests/test_fantasypros_kdst_consensus_service.py
  tests/test_team_code_alias_service.py -q`: **26 passed**.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability or
  fantasypros_kdst or team_code_alias or waiver_engine or sleeper"`):
  **611 passed, 0 failed**.
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** --
  the SAME 4 pre-existing failures this worktree's documented baseline
  expects (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_facade_has_no_streamlit_or_app_component_dependency`).
  Re-confirmed unaffected by this pass's change.
- `git diff` grepped for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): **zero matches**.

### Zero Sleeper writes, verified 3 ways

1. Structural: grepped the one touched production file for
   `POST`/`PUT`/`PATCH`/`DELETE` -- zero matches (it has no HTTP methods
   at all; identity normalization is pure string logic).
2. `SleeperHttpClient` (the only Sleeper client used, both by this
   verification script and by every facade method exercised) exposes
   only `get_json` -- structurally incapable of writing.
3. Before/after byte-diff of `GET league/{id}/rosters`, taken
   immediately before and after this pass's entire live verification
   run (both facade calls and raw pulls): **byte-identical**, SHA-256
   `cd1b3932...` both times, `7145` bytes unchanged.

### Backend/model files changed this pass

- **Modified**: `src/services/fantasypros_kdst_consensus_service.py`
  (added `_strip_generational_suffix()` + one call site inside
  `_identity()`'s name normalization -- same shared boundary Worker 1's
  JAC/JAX fix touched, no other production code changed).
- **Modified**: `tests/test_fantasypros_kdst_consensus_service.py` (3 new
  tests, described above).
- This ledger.
- Nothing in `desktop_facade.py`, `desktop_api/`, `waiver_engine_service.py`,
  or any consumer/UI layer touched -- `resolve_roster_canonical_ids` and
  `sleeper_free_agent_pool` both import `_identity` from the one file
  that changed, so the fix applies symmetrically to both roster-sync and
  free-agent-pool identity matching without touching either call site.

## Worker 3 (this pass) -- Work Unit 4: waiver ranking, Work Unit 5:
## Add/Drop, Work Unit 6: FAAB live

Start HEAD `18f66c73` (Worker 2's suffix-stripping + free-agent-pool
verification, above). Real, live, read-only verification against the real
Fantasy Gamers Sleeper league (`1312983576827920384`, owner `scolety`,
2026-09-15, in-season week 2, `waiver_type=1`/FAAB confirmed live), using
the EXISTING `waiver_engine_service.py` unchanged -- not rebuilt.

### Work Unit 4 result: PASS

Instantiated the real `DesktopBackendFacade` against this worktree's real
active profile and called `redraft_waivers()` live in both modes:

- **THIS_WEEK (week=2): real weekly projection genuinely available.**
  `weeklyProviderHealth`: `status: OK`, `freshness: LIVE`,
  `totalRows: 9420`, `nonzeroProjectionRows: 901`, live-fetched this pass
  (not cached/stale). 25 real add candidates returned, e.g. Tyrone Tracy
  (RB NYG, wk_proj 1.9 -- note: THIS_WEEK's own weekly number can be low
  for a player whose ROS value is driven by a role change; the mode
  correctly reports it rather than hiding it), Juwan Johnson/Hunter
  Henry/Dalton Schultz (real streaming TEs), Jared Goff (real streaming
  QB). Every field the directive asked for is present per candidate:
  `playerName`/`position`/`team`/`weeklyProjectedPoints`/
  `rosReplacementValue`/`rosOverallRank`/`marginalUtility`/
  `becomesStarter`/`identityStatus`("status")/`marginalUtilityExplanation`
  ("reason")/`playerAvailabilityStatus`("availability", correctly `null`
  for every real candidate spot-checked -- an absent entry in the
  canonical `PlayerAvailabilityStatus` map means "no known status issue",
  never a fabricated "OK", by that service's own documented contract; not
  a bug).
- **REST_OF_SEASON: PASS.** Same 25 real candidates, ranked identically by
  real marginal utility (THIS_WEEK only re-breaks ties with live weekly
  points, confirmed structurally in `rank_waiver_candidates`' `sort_key`).
- **Real sanity spot-check:** top drop candidate (weakest real bench
  piece) was the owner's own Marvin Harrison (`marginalUtility: 0.0`) --
  plausible for a real rookie WR in a limited early-season role behind
  this roster's other real starters. Top real adds (Tracy, streaming
  TEs/QB) are genuine, currently-relevant real 2026 waiver-wire names, not
  synthetic ones -- passes the "do the top candidates make sense given
  the real roster gaps" sanity bar.
- **K/DST are never evaluated by this waiver-ranking path at all, by
  design, not a bug this pass introduced.** The owner's own real K
  (Ka'imi Fairbairn, Sleeper id `3451`) and DST (`NE`) both show up in
  `unmatchedRosterSleeperPlayerIds` every real run -- traced to the fact
  that K/DST have zero rows in the main governed NWR ranking by design
  (see the `practical_mode` comment elsewhere in this file), so
  `resolve_roster_canonical_ids`' identity join can never match them, and
  the same is true for every K/DST free agent (never a real add
  candidate, never a real drop candidate via this path). This is the
  real, concrete evidence for Work Unit 7 below, not a guess.

### Work Unit 5 result: PASS, with one real bug found + fixed

**Real, reproducible bug found:** Worker 2's flagged gap (`redraft_my_
roster()` has no reserve/IR field) also affected `redraft_waivers`'
Add/Drop pairing specifically. Raw-confirmed live: a real Sleeper roster's
`players` list INCLUDES any IR/reserve-slotted player (the `reserve` list
is a labeled subset of `players`, never a separate pool) -- so
`rank_drop_candidates` ranked an IR player as an ordinary drop candidate,
using the same `marginal_roster_utility_v2` call as any other bench piece.
Since an IR-stashed player often has a genuinely low live marginal
utility, he could become the single weakest drop and get surfaced as the
Add/Drop pairing's recommended drop -- a real wrong recommendation
(dropping a reserve-slot player doesn't free the bench-slot type an
ordinary Add/Drop implies, and this app has no signal to reason about
IR-specific mechanics). This owner's own roster has 0 IR players right
now, so it could not be reproduced against live owner data -- per the
directive, a test fixture was constructed instead:
roster = [bench-1: Christian McCaffrey, ir-1: Bijan Robinson (`reserve`)],
free agent = Tyreek Hill. **Reproduced on the pre-fix code** (`git stash`
+ rerun): Bijan Robinson (marginal utility 238.8, real ranking-driven,
genuinely lower than McCaffrey's 275.1 in this fixture) was recommended as
the drop. **Fixed** in `desktop_facade.py`'s `redraft_waivers`: reads the
real raw `own_roster["reserve"]` list directly (independent of the
`redraft_my_roster()` gap), resolves it to canonical ids, and filters any
reserve-slotted player OUT of the returned/paired drop-candidate list --
the FULL roster (reserve included) is still passed into
`rank_drop_candidates` so every OTHER bench player's own marginal-utility
computation still reflects the real, actual roster composition; only the
reserve player himself is excluded from being offered as a drop. Re-ran
the same fixture post-fix: McCaffrey (the real ordinary bench player) is
now correctly recommended instead. `waiver_engine_service.py` itself is
UNCHANGED -- the fix is entirely at the facade call site.

**Roster legality after a hypothetical move (structural verification,
not a new legality engine call):** every Add/Drop pairing is a strict
1-for-1 swap (one free agent in, one already-rostered non-reserve player
out), so total roster size and slot count are unchanged by construction;
combined with the reserve-exclusion fix above, the drop side can now only
ever be an ordinary starter/bench player, never a roster slot with
different legality semantics. Position-cap-aware legality itself lives
inside the closed, hard-boundary-protected `marginal_roster_utility_v2` --
not re-verified or touched here.

**Never recommends dropping a player not on the owner's real roster:**
structurally guaranteed -- `drop_candidates` is built exclusively from
`resolved.canonical_player_ids`, itself derived only from
`own_roster.get("players")` (the real, live-fetched Sleeper roster), never
from any other source.

Directive's optional "2-3 drop alternatives where close" was NOT built --
`pair_add_drop` only ever pairs the single weakest real drop candidate
(`drop_candidates[0]`) with every add, a pre-existing, disclosed
simplification (see that function's own docstring). The directive said
"if the service already supports this" -- it doesn't; treated as
out-of-scope new feature work for a same-night pass, not a bug.

### Work Unit 6 result: PASS, with one real bug found + fixed

**Real, previously-undocumented gap found:** grepped the entire codebase
(backend AND frontend) for `waiver_budget`/`waiver_type` -- ZERO hits
anywhere except this ledger. `suggest_faab_bids` itself
(`waiver_engine_service.py`) was always genuinely contextual (real
percentile-of-pool math, never a static table) -- confirmed unchanged --
but nothing ever fed it real Sleeper budget data. The facade method's
`remaining_budget_dollars`/`total_budget_dollars` are caller-supplied
parameters, and the ONLY real caller
(`desktop/apps/redraft/src/improve-team.tsx`) seeded them from hardcoded
`useState(100)` defaults with a manual-edit form -- only coincidentally
correct for this real league today (week 2, $0 spent). It would silently
go stale the first week the owner actually won a bid, and, worse, a
genuinely non-FAAB (Sleeper rolling waiver-priority) league would still
show a fabricated dollar bid range, since nothing ever checked
`waiver_type`.

**Fixed:** `redraft_waivers` now also reads the real, live
`league/{id}` settings (one more read-only GET, through the same cached
`_sleeper_get_json` wrapper rosters/players already use) plus the
already-fetched `own_roster["settings"]`, and returns a new, additive
`faabContext` field: `isFaabLeague` (real `waiver_type == 1`),
`totalBudgetDollars`/`remainingBudgetDollars` (both `null` when not FAAB
-- never fabricated), `waiverPosition` (real `roster.settings.
waiver_position`, useful for a non-FAAB league too), `source:
"SLEEPER_LIVE"`. `suggest_faab_bids` itself is completely unchanged.
Frontend (`improve-team.tsx`): seeds `remainingBudget`/`totalBudget` from
this real data the first time it loads for a profile (still editable
afterward, for scenario planning -- never fights a manual edit), and the
FAAB tab now checks `faabContext.isFaabLeague === false` to replace the
dollar-bid UI entirely with the real waiver-priority position instead
(never shows a fake bid for a confirmed non-FAAB league). Added
`WaiverFaabContext` to `contracts/src/index.ts`. `npm run typecheck` and
`npx vitest run` (423 tests) both clean after the frontend change.

**Real live verification (this owner's real league):** `faabContext`:
`{"isFaabLeague": true, "totalBudgetDollars": 100,
"remainingBudgetDollars": 100, "waiverPosition": 10, "source":
"SLEEPER_LIVE"}` -- exactly matches Worker 2's independent raw pull
(`waiver_budget=100`, `waiver_budget_used=0`) and the raw
`roster.settings.waiver_position=10`. Top real FAAB suggestion: Tyrone
Tracy, bid $30-50, urgency `MEDIUM` (bench-depth reasoning; correctly not
`HIGH` since `becomesStarter` is `false` for this roster right now).
**Urgency enum verified live as the real HIGH/MEDIUM/LOW contract
values** (`FAAB_URGENCY_TIER`'s existing 3-tier mapping, unchanged --
confirmed by direct read of the live JSON response, not just the
pre-existing regression test).

**No real non-FAAB Sleeper league exists in this environment to verify
the suppression path against live data** -- the only other real profile
is `provider="local"` (not Sleeper). Verified instead with a constructed
fixture (`tests/test_redraft_waivers_faab_context_fix.py`,
`waiver_type=0`): `isFaabLeague: false`,
`totalBudgetDollars`/`remainingBudgetDollars` both `null`,
`waiverPosition` still real/populated. Flagged for a future worker to
re-confirm against a real non-FAAB league if/when one becomes available.

### Tests (this pass)

- **New**: `tests/test_redraft_waivers_ir_reserve_drop_exclusion_fix.py`
  (3 tests -- the real IR-drop bug reproduction + fix verification +
  no-reserve equivalence guard).
- **New**: `tests/test_redraft_waivers_faab_context_fix.py` (3 tests --
  real FAAB league, real non-FAAB league, league-settings-read-failure
  degrades honestly rather than crashing).
- Updated 2 existing test fixtures
  (`tests/test_redraft_waivers_unmatched_identity_rationale_fix.py`,
  `tests/test_weekly_home_sleeper_fetch_caching.py`) to model the new
  real `league/{id}` GET call this pass adds -- both were strict
  path-allowlist fixtures that would otherwise raise on an unmodeled real
  call; `test_weekly_home_sleeper_fetch_caching.py`'s own dedup-caching
  assertions continued passing unmodified (the new call uses the same
  cached `_sleeper_get_json` wrapper, so it dedupes the same way rosters/
  players already do).
- `python -m pytest tests/test_redraft_waivers_ir_reserve_drop_exclusion_fix.py
  tests/test_redraft_waivers_faab_context_fix.py
  tests/test_redraft_waivers_unmatched_identity_rationale_fix.py
  tests/test_waiver_engine_service.py -q`: **23 passed**.
- Targeted regression slice (`pytest -k "decision_trace or
  prospective_outcome or live_player_intelligence or
  boundary_property_reliability or composition or player_availability or
  fantasypros_kdst or team_code_alias or waiver_engine or sleeper or
  redraft_waivers or faab or weekly_home or desktop_facade_architecture"`):
  **629 passed, 0 failed** (up from Worker 2's 611 baseline for a smaller
  slice, +18 net new/broadened tests this pass added or now includes).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures this worktree's documented baseline
  expects, re-confirmed unaffected.
- Frontend: `npm run typecheck` (tsc -b, both apps) clean; `npx vitest run`
  (desktop workspace): **423 passed** (0 failed).
- `git diff -U0` grepped (added/removed lines only, not context) for every
  hard-boundary term (`marginal_roster_utility_v2`, `LeagueSnapshot`,
  `LeagueWorkspaceContext`, `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`): **zero matches**.

### Zero Sleeper writes, verified 3 ways

1. Structural: `SleeperHttpClient` exposes only `get_json` (`dir()`
   confirmed live) -- structurally incapable of writing. Grepped
   `desktop_facade.py` for `POST`/`PUT`/`PATCH`/`DELETE`: zero matches.
2. `git diff` of every touched file grepped for any Sleeper write-shaped
   call: zero matches.
3. Before/after byte-diff of `GET league/{id}/rosters`, taken immediately
   before and after this pass's ENTIRE live verification run (both real
   facade calls and raw pulls, including the new `league/{id}` settings
   read): **byte-identical**, SHA-256 `cd1b3932...` both times, `7145`
   bytes unchanged -- the exact same hash Worker 2's own before/after
   check recorded, i.e. genuinely nothing changed league-wide across two
   full workers' worth of live verification today.

### Backend/model files changed this pass

- **Modified**: `src/application/desktop_facade.py` -- `redraft_waivers`
  only: (a) reads real `own_roster["reserve"]`, filters reserve-slotted
  canonical ids out of the returned/paired drop-candidate list (Work Unit
  5 fix); (b) reads real `league/{id}` settings + the owner's own
  `roster["settings"]`, adds the new `faabContext` response field (Work
  Unit 6 fix). No other facade method touched.
- **Modified**: `desktop/packages/contracts/src/index.ts` -- added
  `WaiverFaabContext` interface + `faabContext` field on `WaiversResult`
  (additive only).
- **Modified**: `desktop/apps/redraft/src/improve-team.tsx` -- seeds real
  FAAB budget state from `faabContext` once per profile; `FaabTab` shows
  real waiver-priority position instead of a dollar bid range when
  `faabContext.isFaabLeague === false`.
- **Modified** (test-fixture-only, not production behavior):
  `tests/test_redraft_waivers_unmatched_identity_rationale_fix.py`,
  `tests/test_weekly_home_sleeper_fetch_caching.py`.
- **New**: `tests/test_redraft_waivers_ir_reserve_drop_exclusion_fix.py`,
  `tests/test_redraft_waivers_faab_context_fix.py`.
- This ledger.
- `waiver_engine_service.py` itself: **UNCHANGED** -- both fixes are
  entirely at the `desktop_facade.py` call site, per the directive's "use
  the existing waiver engine, do not rebuild it."
- `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/
  frontend_bench_results.json` was regenerated as a side effect of running
  `npx vitest run` (a perf-benchmark artifact, timing noise only) --
  reverted with `git checkout --` before committing, not part of this
  pass's real changes.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 7-8: K/DST waiver
## completeness, Improve Team UI live data)

1. **K/DST are structurally invisible to `redraft_waivers` end-to-end.**
   Real, concrete live evidence this pass: the owner's own real K (Ka'imi
   Fairbairn, Sleeper id `3451`) and DST (`NE`) both always show up in
   `unmatchedRosterSleeperPlayerIds`, never as a drop candidate; the same
   identity-join gap means no K/DST free agent can ever become a real add
   candidate either. Root cause: K/DST simply have zero rows in the main
   governed NWR ranking `resolve_roster_canonical_ids` joins against
   (`practical_mode`'s own comment elsewhere in this codebase confirms
   this is by design, not an oversight). This app already HAS a separate,
   real, live K/DST pathway (`sleeper_streamer_actions`, the FantasyPros
   ECR-based streamer service Worker 1 fixed for JAC/JAX) -- Work Unit 7 is
   almost certainly about deciding whether/how to fold that separate
   pathway's real signal into (or alongside) the main Waivers/Add-Drop
   surface so K/DST aren't a silent blind spot there, NOT about building a
   new K/DST ranking signal from scratch.
2. **No real non-FAAB Sleeper league exists in this environment.** This
   pass's `faabContext.isFaabLeague === false` path is verified only via a
   constructed test fixture (`waiver_type=0`), not live. Re-confirm
   against a real non-FAAB league if/when one becomes available to this
   owner.
3. **`pair_add_drop`'s "2-3 close drop alternatives" was not built** --
   the directive itself hedged this as optional ("if the service already
   supports this"); it doesn't. Real, scoped follow-up if ever prioritized
   (would touch `waiver_engine_service.py`, not just the facade call
   site).
4. **`matchupContext` came back `null`** from
   `redraft_league_workspace_context()` (Worker 2's finding, still open,
   still not investigated -- hard-boundary-protected surface). Carried
   forward again since Work Unit 8 (Improve Team UI live data) may depend
   on it.
5. Items 1-4 carried over from Worker 1, and Worker 1's disclosed
   FantasyPros top-10-per-query cap / duplicate `TEAM_ALIASES` files --
   still open, unrelated to Work Units 4-6, no change this pass.

## Worker 4 (this pass) -- Work Unit 7: K/DST waiver completeness,
## Work Unit 8: Improve Team UI live data

Start HEAD `e1a1bb0a` (Worker 3's IR-drop exclusion + real FAAB context,
above). Real, live, read-only verification against the real Fantasy
Gamers Sleeper league (`1312983576827920384`, owner `scolety`, 2026-09-15,
in-season week 2).

### Work Unit 7 result: PASS -- the existing Streamers tab already wires
### the real K/DST streamer pathway correctly; one real display bug found
### + fixed (cosmetic, not scoring)

Confirmed FIRST via a direct, isolated `DesktopBackendFacade.
redraft_kdst_streamer(week=2)` call (before touching the UI at all) that
Worker 3's suspicion was correct: the separate, real
`sleeper_streamer_actions` pathway (`fantasypros_kdst_consensus_service.py`,
already fixed for JAC/JAX and generational suffixes by Workers 1-2) already
resolves the owner's own real K and DST correctly --
`Ka'imi Fairbairn (HOU, K) -> rosterStatus YOUR_STARTER, recommendation
START` and `New England Patriots (NE, DST) -> rosterStatus YOUR_STARTER,
recommendation START` -- with zero backend changes needed. The Streamers
tab (`ImproveTeamPage` -> `StreamersTab`, `improve-team.tsx`) already reads
this exact endpoint via `client.kdstStreamer(week)` and already renders a
full FantasyPros-ECR-vs-Sleeper-availability table plus a DecisionExplain
card per position -- this surface was NOT rewired this pass, only verified
and then cosmetically fixed (below).

**A rostered K/DST can never appear as an ADD candidate -- structurally
guaranteed, re-confirmed by direct code read of `streamer_actions()`
(`fantasypros_kdst_consensus_service.py`): the `ADD`/`ALTERNATIVE`
recommendation branch is only ever reached when `rosterStatus ==
"AVAILABLE"`; every rostered player falls into `YOUR_STARTER`/`YOUR_ROSTER`
/`ROSTERED` first.** Live-verified directly in the rendered Chrome table,
not just read in source (see Work Unit 8 below for the exact rows).

**Real display bug found + fixed:** `rosterStatus`/`recommendation` are
raw backend enum values with underscores (`"YOUR_STARTER"`,
`"ROSTERED_ELSEWHERE"`), and were rendered completely unhumanized in two
places: the STREAMERS table's "Sleeper status"/"Action" columns
(`buildStreamerColumns` in `improve-team.tsx`, no `render` on the status
column, `StatusBadge`'s `label` passed the raw enum straight through) and
the DecisionExplain card's "this week" line
(`explainStreamerPlay`'s `thisWeekImpact` in `improve-team-explain.ts`).
Every OTHER enum-shaped value already surfaced in this same file IS
humanized (`result.writeBehavior.replaceAll("_", " ")`, a few lines above
the bug) -- this was a real, live-reproduced inconsistency, not a guess:
before the fix, the real Chrome session showed `"YOUR_STARTER · Week 1"`
and `"ROSTERED_ELSEWHERE"` verbatim with underscores. **Fixed**,
presentation-only, in both files (`.replaceAll("_", " ")` on
`rosterStatus`/`recommendation` immediately before display; the
underlying enum values themselves, the backend response, and
`sleeper_streamer_actions`' own scoring/classification logic are
completely unchanged). Re-verified live after a real `npm run build` +
hard reload: the same real rows now render `"YOUR STARTER"`,
`"ROSTERED ELSEWHERE"`, `"AVAILABLE"`, `"ADD"`, `"ALTERNATIVE"`, `"START"`
with spaces.

**Real live label verification, both positions, both against week 1 and
week 2 (FantasyPros' top-10-per-query cap means the owner's real DST,
New England, is only inside the returned set for some weeks -- confirmed
by direct comparison, not treated as a bug; see Worker 1's own disclosed
"Data-availability limit" note above)**:
- Week 1 K table (10 rows): Ka'imi Fairbairn (HOU) row 4 -> `YOUR STARTER`
  / `START`. Every other rostered K (Brandon Aubrey, Cameron Dicker, Cam
  Little, Jason Myers, Jake Bates, Chris Boswell) -> `ROSTERED` /
  `ROSTERED ELSEWHERE`. Every unrostered K (Evan McPherson, Tyler Loop,
  Chase McLaughlin) -> `AVAILABLE` / `ADD` (top pick only) or
  `ALTERNATIVE`.
- Week 1 DST table (10 rows): New England not present in FantasyPros'
  real top-10 for week 1 (a real provider fact, not a bug); every other
  row resolves the same `ROSTERED`/`AVAILABLE` pattern correctly
  (Jacksonville -> `ROSTERED ELSEWHERE`, matching Worker 1's own JAC/JAX
  fix holding live; Detroit -> `AVAILABLE`/`ADD`).
- Week 2 K table: Ka'imi Fairbairn (HOU) -> `YOUR STARTER` / `START`
  again, real live re-confirmation.
- Week 2 DST table: **New England Patriots (NE) row 9 -> `YOUR STARTER` /
  `START`** -- the exact real ownership label the directive asked to
  verify, confirmed live in the rendered UI (not just the facade call).
  Jacksonville, LAC, PIT, LAR, PHI, SEA, DEN, HOU, BAL all correctly
  `ROSTERED` / `ROSTERED ELSEWHERE`; Tampa Bay `AVAILABLE`/`ADD`; Green
  Bay `AVAILABLE`/`ALTERNATIVE`.

### Work Unit 8 result: PASS, all 5 tabs confirmed real/populated, zero
### console errors

Launched a real production `vite build` + the real Python desktop API
backend via `desktop/scripts/nwr_release_gate_smoke.ps1 -KeepRunning
-SleeperLeagueId 1312983576827920384 -SleeperUsername scolety` (backend
port 18742, vite preview port 1422) -- the same real bridge-smoke harness
Worker 8 of the prior `prospective_outcomes_v1` cycle used. The script's
own real, read-only Sleeper before/after byte-diff (league/rosters/users)
came back **IDENTICAL** -- 0 writes confirmed independently by the
script itself, not merely trusted. Opened the real app in a real Chrome
tab (`claude-in-chrome`, `http://127.0.0.1:1422/#/league/
941b99ade350410391b1b67c0890af79/improve`, the real active Fantasy Gamers
profile) and exercised all 5 Improve Team tabs:

- **TARGETS**: PASS. `25 TARGETS` badge; real top target `ADD Tyrone
  Tracy / DROP Marvin Harrison`, `$30-50 MEDIUM urgency`, replacement
  value +35.1 / marginal utility +9.7 -- exact match to Worker 3's own
  documented real finding.
- **ADD/DROP**: PASS, all 3 views. "Available to add" (25 shown, Tyrone
  Tracy top). "Consider dropping" (13 shown, weakest first -- Marvin
  Harrison 0.0 marginal utility is the real weakest, matching Worker 3;
  zero IR/reserve players shown, consistent with the owner's real 0-IR
  roster and Worker 3's exclusion fix still holding structurally). "Add/
  Drop pairings" (10 shown, every pairing drops Marvin Harrison --
  correct, single-weakest-drop-candidate design, unchanged this pass).
  `Unresolved roster Sleeper IDs: 3451, NE` still correctly shown at the
  bottom -- this is the SAME real, disclosed gap Worker 3 documented
  (K/DST invisible to `redraft_waivers` specifically, by design), now
  cross-verified as expected/non-regressed since Work Unit 7 confirmed
  the Streamers tab is the correct real channel for K/DST.
- **FAAB**: PASS. Remaining Budget `$100` of `$100` total, 14 weeks
  remaining, explicit "SEEDED FROM YOUR REAL LIVE SLEEPER BUDGET" caption
  -- confirms Worker 3's fix is live, not a coincidental hardcoded
  default. Top real bid: Tyrone Tracy, `$30-50 MEDIUM urgency`.
- **STREAMERS**: PASS -- see Work Unit 7 above for the exact real K/DST
  ownership labels, both weeks.
- **ALL FREE AGENTS**: PASS. `718 unrostered players` -- exact match to
  Worker 2's own documented real count. Real spot-checks: Marvin Harrison,
  Ka'imi Fairbairn, and New England's DST slot are correctly ABSENT (all
  rostered); genuinely unrostered real players (Jared Goff, Keenan Allen,
  every D/ST except the 10 actually rostered, etc.) all correctly present
  and `AVAILABLE`.
- **Player Drawer**: PASS. Clicked "View" on Jared Goff (a real free
  agent) from the ALL FREE AGENTS table -- drawer opened with the correct
  player (`Jared Goff / QB · DET`), `OPENED FROM IMPROVE TEAM` tag,
  honest `NO STATUS ISSUE` state.
- **Console errors**: `read_console_messages` (pattern `.`, no filter)
  returned **zero messages of any kind** (not just zero errors) across
  the entire session -- every tab visit, both Streamers refreshes (weeks
  1 and 2), the Add/Drop view-toggle clicks, and the drawer open/close.
- **Network**: `read_network_requests` confirmed every call this pass's
  own UI interactions made was to the local NWR backend
  (`127.0.0.1:18742/api/v1/redraft/...`) -- never directly to Sleeper or
  FantasyPros from the browser (those calls happen server-side, already
  covered by the release-gate script's own before/after Sleeper diff).

Backend + vite preview processes this pass started were both killed at
the end (`taskkill`); `local_exports/release_gate/<timestamp>/` (git-
ignored) and a throwaway local `python -m http.server` used only to route
around a same-origin restriction while iframing for wide-viewport
rendering were not part of any commit.

### Tests (this pass)

- **Modified**: `desktop/apps/redraft/src/improve-team-explain.test.ts`
  -- 2 new tests (`humanizes the raw backend rosterStatus enum in
  thisWeekImpact`, `humanizes ROSTERED_ELSEWHERE the same way`), covering
  the one real bug fixed this pass.
- `npx vitest run apps/redraft/src/improve-team-explain.test.ts
  apps/redraft/src/home-action-explain.test.ts
  apps/redraft/src/attention-center.test.ts`: **48 passed**.
- Full monorepo `npx vitest run` (from `desktop/`): **425 passed** (up
  from Worker 3's 423 baseline by exactly the 2 new tests this pass
  added; 0 failed).
- `npm run typecheck` (`tsc -b`, both apps): clean, 0 errors, both before
  and after the fix.
- No Python/backend files touched this pass -- Work Unit 7 needed no
  backend fix (the existing pathway already worked correctly), so no
  Python test suite re-run was needed beyond the read-only facade call
  used to FIRST verify the pathway (no state written, no fixture/test
  file touched).
- `git diff -U0` (added/removed lines only) grepped for every hard-
  boundary term (`marginal_roster_utility_v2`, `LeagueSnapshot`,
  `LeagueWorkspaceContext`, `lifecycle_resolver`, `DecisionResultEnvelope`,
  `PlayerAvailabilityStatus`, and also `sleeper_streamer_actions`/
  `streamer_actions` to confirm the streamer's own scoring function was
  never edited): zero matches on the hard-boundary list; the streamer
  function names appear only in this ledger's prose, not in any diff
  hunk.

### Zero Sleeper writes, verified 3 ways

1. The release-gate script's own real, independent before/after byte-
   diff of `league/{id}/rosters` + `users` (fetched directly from
   `api.sleeper.app`, not through the app) came back **IDENTICAL**.
2. Structural: no Python file was touched this pass at all (0 backend
   diff), so the already-established GET-only `SleeperHttpClient`
   contract (verified by Workers 1-3) is trivially unchanged.
3. `read_network_requests` in the real Chrome session showed every
   request this pass's own UI interactions triggered went to the local
   NWR backend only, never directly to Sleeper/FantasyPros from the
   browser.

### Backend/model files changed this pass

**None.** Work Unit 7 required zero backend changes -- the real K/DST
streamer pathway (`sleeper_streamer_actions`,
`fantasypros_kdst_consensus_service.py`; `redraft_kdst_streamer`,
`desktop_facade.py`) was already correct and already wired into the
Streamers tab before this pass began; this pass only verified it live and
fixed a presentation-only display bug in the frontend.

- **Modified**: `desktop/apps/redraft/src/improve-team.tsx` (added a
  `humanizeStreamerEnum` helper + `render` on the STREAMERS table's
  "Sleeper status"/"Action" columns), `desktop/apps/redraft/src/
  improve-team-explain.ts` (`thisWeekImpact` now humanizes `rosterStatus`
  the same way), `desktop/apps/redraft/src/improve-team-explain.test.ts`
  (2 new tests).
- Nothing in `src/services/`, `src/application/desktop_facade.py`,
  `src/desktop_api/`, or any other backend/model file touched.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 9-11: FAAB transaction
## context, non-Sleeper leagues, decision trace)

1. **`unmatchedSleeperPlayerIds` (the K/DST streamer's OWN unmatched-id
   diagnostic field, returned by `redraft_kdst_streamer` but never
   rendered anywhere in the frontend) is internally cross-contaminated
   between K and DST.** Found this pass while investigating the streamer
   pathway, NOT fixed (not user-visible, and fixing it would mean editing
   `sleeper_streamer_actions` itself -- the hard boundary explicitly says
   verify/wire the streamer, don't touch its scoring/matching logic).
   Root cause: `sleeper_streamer_actions`'s internal loop filters roster
   players by `position in SUPPORTED_POSITIONS` (`{K, DST}`, both
   positions, always) rather than by the position of the specific
   consensus rows passed in for that call -- so when called for DST rows,
   every rostered K in the league also gets scanned, inevitably fails to
   match any DST provider id, and gets added to that call's `unmatched`
   set (and vice versa for the K call). Confirmed live: calling
   `redraft_kdst_streamer(week=2)` returned Ka'imi Fairbairn's own Sleeper
   id (`3451`, a K) inside the **DST** position's `unmatchedSleeperPlayerIds`
   list, not the K list. This does NOT affect the real rosterStatus/
   recommendation values shown to the owner (verified live, Work Unit 7
   above) -- it only pollutes an internal diagnostic list nothing reads.
   A future worker explicitly scoped to that file could narrow the filter
   to the row's own target position per call; flagged, not touched.
2. **No real non-FAAB Sleeper league still exists in this environment.**
   Worker 3's `faabContext.isFaabLeague === false` path remains verified
   only via a constructed test fixture, not live. Still open.
3. **`pair_add_drop`'s "2-3 close drop alternatives" still not built.**
   Unchanged from Worker 3's note -- optional, would touch
   `waiver_engine_service.py`.
4. **`matchupContext` still returns `null`** from
   `redraft_league_workspace_context()`. Not investigated this pass
   either (hard-boundary-protected surface); did NOT block Work Unit 8 --
   Weekly Home was not part of this pass's tab checklist, and nothing in
   the 5 Improve Team tabs depends on `matchupContext`.
5. Items 1-5 from Worker 3's own carried-forward list (Worker 1's
   FantasyPros top-10-per-query cap, duplicate `TEAM_ALIASES` files, the
   pre-existing `test_desktop_application_api.py` 4-failure baseline)
   remain open and unrelated to Work Units 7-8, no change this pass.

## Worker 5 (this pass) -- Work Unit 10: non-Sleeper leagues, Work Unit 11:
## waiver decision trace

Start HEAD `ad8c8872` (Worker 4's K/DST streamer humanization fix, above).

### Work Unit 10 result: PASS, with two real honesty bugs found + fixed

**Real profile inventory.** The worktree's own `local_exports/redraft_v1`
(2 profiles: real Fantasy Gamers Sleeper test data + one throwaway
"Isolation Check Local" fixture) is NOT the owner's real profile store --
per repo memory, that lives at
`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\profiles`. Read
that real store directly (6 profile files):

| profile_id | league name | provider | team_count | draft picks | draft updated_at_utc | classification |
|---|---|---|---|---|---|---|
| `4c5f0476...` | Fantasy Gamers | sleeper | 10 | 150/150 (complete) | 2026-09-09 | **LIVE_SYNC_SUPPORTED** -- real, working live read (Workers 1-4 exhaustively verified this exact mechanism this session) |
| `fb1c4940...` | 2026 KHA High Stakes League | espn | 16 | 157/240 (real real-world draft, complete per memory) | 2026-09-03 | **STALE/NEEDS_OWNER_UPDATE** |
| `4b4a9902...` | 403 N 18th and friends | espn | 8 | 118/118 (complete) | 2026-09-08 | **STALE/NEEDS_OWNER_UPDATE** |
| `eafa580e...` | Tester | espn | 10 | 135 | 2026-09-09 | dev/QA artifact, not a real owner league (name says so) -- flagged below, NOT fixed (out of scope: this is currently the ACTIVE profile, which is odd but a product/data decision, not a bug this pass introduces or should silently "fix" by switching it) |
| `f92cff21...` | 2026 KHA High Stakes League – TEST | espn | 16 | 9 | 2026-09-06 | dev/QA artifact (name says so) |
| `16d2e550...` | 2026 KHA High Stakes League – PRACTICE 20260905 | local | 16 | 6 | 2026-09-06 | dev/QA artifact (name says so) |

Real owner leagues: **3** (Fantasy Gamers/Sleeper, KHA/ESPN, 403 N
18th/ESPN). The other 3 are dev/QA leftovers (`Tester`/`TEST`/`PRACTICE`
naming makes this unambiguous, not a guess) -- not touched, not deleted
(deletion wasn't asked for and risks destroying real test fixtures another
session may still want).

**ESPN live-integration check (real, not assumed):** grepped the entire
backend for `SWID`/`espn_s2`/`fantasy.espn.com`/any ESPN HTTP client class
-- zero real integration exists anywhere (only a manual-setup checklist
doc and unrelated `nflverse`/data-health references that happen to contain
the substring "espn"). Confirmed no hack/scrape/stub exists and none was
added. `_active_sleeper_context()` (`desktop_facade.py`) already
structurally refuses ESPN/local profiles for every in-season surface
(`redraft_my_roster`, `redraft_waivers`, Trade Analysis/Finder, weekly
lineup, etc.) with `SLEEPER_REDRAFT_PROFILE_REQUIRED` (409) -- this is
correct, honest, pre-existing behavior, unchanged.

**Real bug 1 (fixed):** `league.tsx`'s `LeagueSyncTab` (League workspace ->
Sync tab) told the owner, for any Local/ESPN profile: *"scoring and roster
changes are made manually in Settings."* This is false. Settings
(`ProfileEditor`/`editableProfile` in `profile.tsx`, confirmed by direct
read) only edits league name, roster SLOT COUNTS (qb/rb/wr/te/flex/k/dst/
benchSize -- structural limits), scoring rules, and draft rules -- there is
no field anywhere in this app for which SPECIFIC PLAYERS are on a Local/
ESPN roster. Once a draft is complete, the pick-correction UI (the only
mechanism that ever writes to a draft board's roster) is structurally
disabled (`canRecordPick` requires `!board.complete` in LIVE_READ_ONLY mode
or `ownerTurn` in MOCK mode, both false post-draft -- confirmed by direct
code read, `draft-room-v2.tsx`). **There is no live sync, CSV import, or
manual editor anywhere in this codebase that can record a post-draft
add/drop/trade for a Local/ESPN league.** The message pointed the owner at
a nonexistent capability. **Fixed**, presentation-only, in
`desktop/apps/redraft/src/league.tsx`: the EmptyState now states plainly
that NWR does not track transactions for these providers and that Settings
only changes scoring/roster structure, not team composition.

**Real bug 2 (fixed):** the same panel's "Last synced" row showed
`context.syncAsOf` unconditionally, labeled "Last synced" for every
provider. `syncAsOf` is `LeagueWorkspaceContext`'s `sync_as_of`, which
`redraft_league_workspace_context()` sets to `selected.updated_at_utc` --
the PROFILE record's own last-modified timestamp (this is unchanged,
hard-boundary-protected `LeagueWorkspaceContext` backend logic; NOT touched
this pass). For a Sleeper profile that field really is refreshed on every
resync, so "Last synced" is honest. For a Local/ESPN profile it is only
ever "the last time ANY part of the profile record changed" (e.g. a
scoring edit, a rename, an unrelated K/DST-reuse fix from a prior session)
-- reproducibly demonstrated live from the real store above: 403 N 18th's
profile `updated_at_utc` is `2026-09-09T00:48:33Z`, a full day AFTER its
draft board's real last pick (`2026-09-08T02:50:29Z`), because of an
unrelated later Settings-adjacent fix, not because any roster data changed.
Labeling that "Last synced" would tell the owner their roster reflects
09-09 state when the real roster data (draft results) is frozen as of
09-08 and has had zero owner-visible refresh mechanism since. **Fixed**,
presentation-only: relabeled to "Profile record last changed" for
non-Sleeper profiles (keeps "Last synced" only for Sleeper, where it's
true), and added a new, honestly-labeled "Roster last known from" row for
non-Sleeper profiles using the DRAFT BOARD's own real `updatedAtUtc`
(`data.draftBoard.updatedAtUtc`, already loaded as part of
`RedraftBootstrap` for every provider, an existing field this pass did not
add -- `redraft_draft_room_v1_service.py`'s `build_draft_room_payload` was
not touched) -- the one real, accurate "as of" timestamp this app actually
has for a frozen non-Sleeper roster.

**Also fixed, same root cause, different surface:** `in-season.tsx`'s
`MyRosterContent` (My Roster page/tab) already correctly blocked non-
Sleeper profiles ("ESPN and local profiles have no live roster source" --
true, left as-is), but gave the owner no path forward. Added the same real
`data.draftBoard.updatedAtUtc` timestamp to that message plus a link to
Draft Room (`/draft-room-v2`, where the real, frozen `myRoster` from the
draft board IS actually viewable) -- the simplest already-existing real
path to "the last roster NWR actually knows about," since no refresh path
exists.

Neither fix touches `LeagueWorkspaceContext`'s backend semantics, the
draft-room service's scoring/matching logic, or any hard-boundary item --
both are presentation-only, using fields the backend already returns.

### Work Unit 11 result: PASS, with two real trace-completeness bugs found
### + fixed, dedup re-verified live and holding

Read `in_season_decision_trace_service.py` in full (NOT modified --
confirmed by `git diff`, zero lines changed in that file). Checked the
directive's exact required-field list against the real WAIVER/FAAB trace
calls in `desktop_facade.py`'s `redraft_waivers` (the method Workers 3-4
both touched this session):

- league/week/roster-snapshot/free-agent-snapshot/trace-ID: already
  correctly captured (`league_id`, `week`, `resolved.canonical_player_ids`,
  `[candidate.sleeper_player_id for candidate in add_candidates]`, real
  `trace_id` returned by `_record_decision_trace_safe`).
- **Real bug found (fixed): `recommendation` never included the DROP.**
  Only `topAdd`/`topAddCanonicalId` were ever recorded on the WAIVER
  trace, even though `pair_add_drop` (unchanged) already computes the
  paired drop candidate a few lines above the trace call -- a real WAIVER
  recommendation is "add X, drop Y," and the ledger only ever recorded
  half of it. **Fixed**: added `dropPlayerName`/`dropCanonicalPlayerId`
  to the WAIVER trace's `recommendation` (`None` when no drop candidate
  exists, e.g. an empty roster -- never fabricated). This also closes a
  latent dedup-accuracy gap: two genuinely different recommendations
  (same top add, different drop, e.g. the bench changed) would previously
  fingerprint identically and incorrectly dedup; now they correctly
  differ.
- **Real bug found (fixed): `data_versions` never carried a "weekly-
  projection version" or "ROS version."** Both WAIVER and FAAB always
  passed `data_versions={"mode": mode}` only -- contrast with the
  already-existing START_SIT trace a few hundred lines above, which
  already includes `weekly_projection_source`. **Fixed**: both traces now
  add `rosProjectionSha256` (`ranking.projection_sha256`, already computed
  in scope -- the same real ranking-provenance field other call sites in
  this file, e.g. the Monte Carlo draft-room calls, already treat as the
  authoritative ranking-version signal), and, for THIS_WEEK mode only,
  `weeklyProjectionSource`/`weeklyProjectionRetrievedAt` from the
  already-computed `weekly_provider_health` dict. Both additions are
  purely additive to `data_versions`, which `_content_fingerprint`
  (unchanged) never hashes -- confirmed by direct code read that this
  cannot affect dedup behavior, only trace completeness.
- **Real gap found (fixed): the FAAB trace never recorded `alternatives`**
  (the call site never passed the parameter, defaulting to empty) despite
  `faab_by_id` already having every other real add candidate's bid range
  available. **Fixed**: FAAB trace now includes up to 4 real bid-range
  alternatives (`playerName`/`bidLowDollars`/`bidHighDollars` for
  `add_candidates[1:5]`).
- **FAAB range**: already correctly captured on the FAAB trace itself
  (`bidLowDollars`/`bidHighDollars`/`urgency`) -- unchanged, confirmed
  correct.

**Dedup re-verified live, specifically for the newly-fixed waiver/FAAB
paths, per the directive's explicit ask.** Real, live test against the
real Fantasy Gamers Sleeper league (`1312983576827920384`, via this
worktree's own already-active real profile
`941b99ade350410391b1b67c0890af79` in `local_exports/redraft_v1`,
2026-09-15, in-season week 2):
- Called `redraft_waivers(mode="REST_OF_SEASON")` **3x in immediate
  succession**: all 3 calls returned the SAME `traceId`
  (`31789fc1-219a-...`); the ledger gained exactly **1** new WAIVER line
  and **1** new FAAB line for that scope, not 3.
- Called `redraft_waivers(mode="THIS_WEEK", week=2)` **2x in immediate
  succession**: both calls returned the SAME `traceId`
  (`133ea933-74d4-...`); the ledger gained exactly 1 new WAIVER line and 1
  new FAAB line for THAT scope (week=2 is a legitimately distinct scope
  from `week=None`/REST_OF_SEASON, per `record_decision_trace`'s own
  documented `== week` scoping -- both are real, intentionally separate
  events, not duplicates of each other).
- Net: 40 total ledger lines before this run's real live calls -> 40 + 4
  (2 REST_OF_SEASON + 2 THIS_WEEK, one WAIVER + one FAAB each) = correct,
  observed exactly.
- Inspected the 4 real new lines directly: the WAIVER lines now show
  `"dropPlayerName": "Marvin Harrison"` (the owner's real weakest bench
  piece, matching every prior worker's own documented finding) alongside
  the real top add (Tyrone Tracy); `data_versions` on the REST_OF_SEASON
  lines correctly has NO `weeklyProjectionSource` key (mode-gated, as
  designed), while the THIS_WEEK lines correctly DO
  (`"weeklyProjectionSource": "SLEEPER"`,
  `"weeklyProjectionRetrievedAt": "2026-09-15T19:39:05..."`); both
  WAIVER and FAAB lines share the identical real
  `rosProjectionSha256`; the FAAB line's `alternatives` now has 4 real
  entries (Juwan Johnson/Hunter Henry/Woody Marks/Dalton Schultz, each
  with a real bid range).
- **Zero Sleeper writes, verified the established way**: before/after
  byte-diff (SHA-256) of `GET league/{id}/rosters`, taken immediately
  before the first call and immediately after the last call of this
  entire live test (7 facade calls total: 3 REST_OF_SEASON + 2 THIS_WEEK +
  the 2 real weekly-projection fetches those trigger) --
  **byte-identical**, `cd1b3932...` both times, matching the exact hash
  every prior worker in this session has independently recorded for this
  same real league today.

### Tests (this pass)

- **New**: `tests/test_redraft_waivers_decision_trace_completeness_fix.py`
  (4 tests -- WAIVER trace now records the paired drop; WAIVER and FAAB
  traces now carry the real, matching `rosProjectionSha256`; FAAB trace
  now records real bid-range alternatives; the dedup window still holds
  for both WAIVER and FAAB after these changes, via 3 rapid identical
  calls producing exactly 1 line per tool).
- `python -m pytest tests/test_redraft_waivers_decision_trace_completeness_fix.py -q`:
  **4 passed**.
- Targeted regression slice (same `-k` filter Workers 2-4 used): **633
  passed, 0 failed** (up from Worker 4's 629 baseline by exactly the 4 new
  tests).
- `tests/test_desktop_application_api.py`: **46 passed / 4 failed** -- the
  SAME 4 pre-existing failures this worktree's documented baseline
  expects, re-confirmed unaffected.
- Frontend: `npm run typecheck` (tsc -b, both apps) clean, 0 errors.
  `npx vitest run` (desktop workspace): **425 passed** (0 failed, exact
  match to Worker 4's baseline -- these were presentation-only text/prop
  changes to two already-tested components, no new frontend test needed
  beyond confirming zero regressions).
- `git diff -U0` grepped for every hard-boundary term
  (`marginal_roster_utility_v2`, `LeagueSnapshot`, `LeagueWorkspaceContext`,
  `lifecycle_resolver`, `DecisionResultEnvelope`, `PlayerAvailabilityStatus`):
  the only match is this pass's own code COMMENT in `league.tsx` explaining
  that `LeagueWorkspaceContext`'s semantics were deliberately NOT touched
  -- zero matches in any actual code change. `git diff` on
  `src/services/in_season_decision_trace_service.py` itself: **empty**
  (the dedup mechanism's own logic was not touched, per the hard
  boundary -- only verified, as directed).
- A benchmark artifact (`docs/codex/prospective_outcomes_v1/
  multi_league_scale_v1/frontend_bench_results.json`) was regenerated as a
  side effect of `npx vitest run` (timing noise only, same as Worker 3's
  note) -- reverted with `git checkout --` before committing.

### Zero Sleeper writes, verified 3 ways (whole pass)

1. The live decision-trace test's own before/after byte-diff of
   `GET league/{id}/rosters` (SHA-256) came back **identical**.
2. Structural: `desktop_facade.py`'s only change this pass is inside the
   ALREADY-READ-ONLY `redraft_waivers` method (adds fields to values
   already computed from GET-only reads; adds no new Sleeper call of any
   kind). Grepped the diff for `POST`/`PUT`/`PATCH`/`DELETE`: zero matches.
3. `SleeperHttpClient` (the only Sleeper client used) still exposes only
   `get_json` -- structurally incapable of writing; unchanged this pass.

### Work Unit 9 (FAAB transaction context): SKIPPED FOR TIME, honestly

Work Units 10-11 (both higher priority per the directive, and both turned
up real, concrete, fixable bugs worth the time) consumed this pass's
available budget. Work Unit 9 was explicitly scoped by the directive as
"optional, only if time remains" and "a nice-to-have... skip cleanly." No
code was written for it, no partial/half-verified implementation was left
behind. Real Sleeper `league/{id}/transactions/{round}` data for the
Fantasy Gamers league was not investigated this pass; genuinely open for a
future worker (not carried forward as a "bug," since nothing was broken --
it simply was not attempted).

### Backend/model files changed this pass

- **Modified**: `src/application/desktop_facade.py` -- `redraft_waivers`
  only: WAIVER trace's `recommendation` gains
  `dropPlayerName`/`dropCanonicalPlayerId`; both WAIVER and FAAB traces'
  `data_versions` gain `rosProjectionSha256` (+ `weeklyProjectionSource`/
  `weeklyProjectionRetrievedAt` for THIS_WEEK mode only); FAAB trace call
  gains a real `alternatives` list. No other facade method touched. No
  change to `_record_decision_trace_safe`'s own signature/behavior, no
  change to `record_decision_trace`/`_content_fingerprint`/the dedup
  mechanism itself (`in_season_decision_trace_service.py` has zero diff).
- **Modified** (frontend, presentation-only): `desktop/apps/redraft/src/
  league.tsx` (Sync tab: honest per-provider "last changed" label + new
  "Roster last known from" row + corrected EmptyState copy for Local/ESPN
  profiles), `desktop/apps/redraft/src/in-season.tsx` (`MyRosterContent`'s
  non-Sleeper EmptyState now shows the real draft-board timestamp + a
  Draft Room link).
- **New**: `tests/test_redraft_waivers_decision_trace_completeness_fix.py`.
- This ledger.
- `waiver_engine_service.py`, `redraft_draft_room_v1_service.py`,
  `in_season_decision_trace_service.py`: **UNCHANGED**.

## OPEN ISSUES FOR THE NEXT WORKER (Work Units 12-15: real waiver dogfood,
## performance, full test suite, final push)

1. **`Tester` (`eafa580e...`) is currently the ACTIVE profile** in the
   real owner install, not one of the 3 real owner leagues. Not changed
   this pass (a profile-selection/product decision, not a bug this pass
   should silently "fix" by switching it out from under the owner) --
   flagged so the next worker doesn't mistake it for a real league if
   dogfooding against "whatever's currently active."
2. **KHA (`fb1c4940...`) and 403 N 18th (`4b4a9902...`) rosters are
   real, stale, and currently have no path back to current** -- this
   pass made the UI honest about that fact (Work Unit 10) but did not
   (and structurally could not, without a real ESPN API credential/auth
   flow the owner would need to supply, which this pass was explicitly
   told never to fake/hack) build a refresh mechanism. If the owner wants
   these leagues usable for waivers again, that is real, separately-scoped
   future work (either a real ESPN OAuth/cookie-based integration, or a
   manual CSV/roster-paste importer built from scratch -- neither exists
   today).
3. **Work Unit 9 (FAAB transaction context) not attempted** -- see above,
   skipped cleanly for time, not carried forward as a defect.
4. Items 1-5 from Worker 4's own carried-forward list (the K/DST streamer
   diagnostic cross-contamination, no real non-FAAB Sleeper league to test
   against live, `pair_add_drop`'s alternatives not built, `matchupContext`
   still `null`, Worker 1's FantasyPros top-10 cap / duplicate
   `TEAM_ALIASES` files / the pre-existing `test_desktop_application_api.py`
   4-failure baseline) remain open, unrelated to Work Units 10-11, no
   change this pass.
