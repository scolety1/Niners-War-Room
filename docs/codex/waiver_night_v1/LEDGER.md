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

## OPEN ISSUES FOR THE NEXT WORKER (Work Unit 2: current Sleeper roster
## sync verification)

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
5. **Work Unit 2 itself** (current Sleeper roster sync verification, the
   next assignment per this cycle's own naming) was not started this
   pass -- Work Unit 1 (this alias fix) was this pass's sole scope, per
   its own directive.
