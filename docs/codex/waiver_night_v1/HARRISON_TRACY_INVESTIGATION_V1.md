# Harrison / Tracy Investigation V1

Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`. Start and end HEAD: `0517ada8` (unchanged
-- this is an investigation-only pass, no production code touched).

Investigating two claims that arrived from an external code review (NOT
pre-verified facts): (1) Marvin Harrison Jr. (canonical id `00-0039849`)
values to zero somewhere in the real computation pipeline and the exact
first zero-producing operation was unknown; (2) Tyrone Tracy's low weekly
projection reportedly coexists with him being a top waiver priority, an
apparent internal contradiction worth checking.

**Methodology note, read first:** every finding below is labeled
`(a)` INSPECTED CODE, `(b)` ACTUAL TEST RESULT, `(c)` LIVE OBSERVATION, or
`(d)` INFERENCE. Where a claim from the review is confirmed, it is
confirmed by direct trace, not assumed. Nothing here is a fix -- zero
production files were changed this pass.

## Data source honesty

This pass used an ISOLATED COPY of this worktree's own
`local_exports/redraft_v1` store (gitignored, not tracked, not the owner's
real AppData install), copied to a scratch directory
(`.../scratchpad/investigation_v1/redraft_v1`) before any facade call was
made, so nothing was appended to this worktree's own decision-trace
ledger and the real installed profile store
(`%LOCALAPPDATA%\com.ninerswarroom.redraft`) was never touched. That store
already contained a real, live-synced snapshot of the real Fantasy Gamers
Sleeper league (`1312983576827920384`, owner `scolety`, active profile
`941b99ade350410391b1b67c0890af79`) from the same-day Waiver Night V1
session (Workers 1-6, see `LEDGER.md`). All Sleeper reads this pass made
(rosters, players catalog, league settings) were fresh, real, live GETs
against the real league, re-pulled during this pass -- not reused
historical JSON. **This is a current (2026-09-15, ~21:56-21:57 UTC)
reproduction against real live data, not a replay of any specific past
owner session** -- no claim is made that this matches any earlier
Waiver Night V1 worker's own run byte-for-byte (roster/ranking state can
drift hour to hour in a live league), though every number found here
matches what Workers 3/4/6 already documented for Harrison/Tracy in
`LEDGER.md` (marginal utility 0.0 for Harrison, Tracy as the top real
FAAB/waiver target), so this is a real, independent reproduction that
corroborates their prior live findings rather than contradicting them.
`(c)` for all Sleeper-sourced facts in this report; `(a)`/`(b)` for
everything about the ranking/marginal-utility computation itself, which
does not depend on Sleeper at all once the roster is resolved.

## Investigation target 1: Marvin Harrison Jr.

### Identity resolution

`(b)`/`(c)` Real, live facade call (`redraft_my_roster()`): Sleeper id
`11628` -> `canonicalPlayerId: "00-0039849"`, `identityStatus: "MATCHED"`,
`playerName: "Marvin Harrison"`, `starter: false`. The generational-suffix
identity fix from the same session's Worker 2 (`_strip_generational_suffix`
in `fantasypros_kdst_consensus_service.py`'s `_identity()`) is confirmed
still holding live: Sleeper's own catalog entry for id `11628`
(`full_name: "Marvin Harrison"`, no suffix) correctly joins to NWR's own
ranking row (`player_name: "Marvin Harrison Jr."`, with suffix). Canonical
id `00-0039849` resolves correctly today. `(a)` Confirmed by reading
`resolve_roster_canonical_ids()` (`waiver_engine_service.py`) and
`_identity()` (`fantasypros_kdst_consensus_service.py`) -- unchanged this
pass, per the hard boundary (this investigation made zero edits to either
file).

### Ranking version, source timestamp, projected points, replacement baseline, replacement-adjusted value

`(b)` Real ranking row for `00-0039849` (from `generate_rankings()` +
`apply_status_overrides_to_ranking()`, called live via
`facade._redraft_ranking_for_profile()`):

```
overall_rank: 132        position_rank: 54 (of 564 total ranked players)
projected_points: 125.8  replacement_points: 125.8
replacement_adjusted_value: 0.0
starter_gap: -61.4       confidence: LOW
tier: 14 (overall)       position_tier: 7 (WR)
source_status: GOVERNED  evidence_status: ADMITTED_CURRENT_SEASON
source_as_of: 2026-09-08 rookie: False
ranking generated_at_utc: 2026-09-15T21:56:32+00:00 (this pass's own live run)
ranking projection_sha256: b87c7296647b83a6103209a2995827766b7957a35270edb1624d7a61102929f4
```

WR replacement level for this profile (10-team, `expected_available`
method): `starter_count=26, rostered_count=53, starter_cutoff_points=187.2,
replacement_points=125.8`.

`projected_points == replacement_points` exactly (both 125.8). This is
**the reason `replacement_adjusted_value` is 0.0**, and it is not a
display-rounding artifact -- see "First-zero operation" below for the
exact mechanism.

### Owner roster, unresolved identities, starter assignment, reserve status

`(c)` Real roster (`redraft_my_roster()`, 15 players, cross-checked
against a direct raw Sleeper `league/{id}/rosters` pull for roster_id 9,
owner `scolety`): 9 real starters (Caleb Williams QB, De'Von Achane RB,
Jonathan Taylor RB, Travis Etienne RB, Kyle Pitts TE, Chris Olave WR, Zay
Flowers WR, Ka'imi Fairbairn K, New England DST) + 6 bench (Trevor
Lawrence, Kenny Gainwell, Carnell Tate, **Marvin Harrison**, Michael
Pittman, Wan'Dale Robinson). Marvin Harrison: `starter: false`. K
(`3451`/Ka'imi Fairbairn) and DST (`NE`) both resolve
`identityStatus: UNMATCHED_IDENTITY` at this facade method -- this is the
SAME, already-documented, by-design K/DST-invisible-to-the-skill-ranking
gap Worker 3/4 found and explained (K/DST have zero rows in the governed
skill-position ranking; a separate real pathway,
`sleeper_streamer_actions`, handles them correctly elsewhere), unrelated
to Harrison and not investigated further here (out of this pass's scope).
Reserve status: `own_roster["reserve"]` is `null`/absent for this owner's
real roster (0 IR players, matching every prior worker's documented
finding); `redraft_my_roster()`'s payload itself still has no
`reserve`/IR field at all (the same disclosed gap Worker 2 flagged,
unchanged, not this pass's scope).

### Starter-versus-bench calculation path

`(a)`+`(b)` `explain_marginal_roster_reason("00-0039849", rest_of_roster,
...)` (`shadow_numeric_authorities_service.py`) was called directly
against the real roster (Harrison removed from the 15, the standard
"how much is HE actually worth to this roster" drop-evaluation framing
`rank_drop_candidates` uses). Real result:

```
becomes_starter: False
displaces_player_id: None
starter_value_delta: 0.0
summary: "WR stays on the bench -- does not improve the optimal starting
          lineup (adds bench depth/contingency value only, +0.0 bench
          value)."
```

Mechanism (`a`, `_select_starting_lineup`): the greedy selector fills each
starter slot with the best-by-value player at that position; Harrison's
own replacement-adjusted value (0.0, see above) is far below the roster's
other WRs (Olave, Flowers already start; Tate 13.2, Pittman 74.6,
Robinson 92.1 all rank above him on the bench too), so he never wins a
starter or FLEX slot and never displaces anyone -- confirmed, not
inferred, by the real function output.

### Bench depth, utility rate, opportunity gap, scarcity, multiplier, utility before/after rounding

`(b)` Real `marginal_roster_utility_v2("00-0039849", rest_of_roster, ...)`
result (identical call `rank_drop_candidates` makes for the real Add/Drop
"Consider dropping" list):

```
utility: 0.0   becomes_starter: False   bench_redundancy_before: 3 (WR)
explanation: "[v2 challenger] Bench depth at WR (would become real depth
  rank 4) -- real, measured flex-worthy-week rate for this exact depth
  (nflverse 10-team bucket, 2019/2021/2022/2023): 9.8%. Opportunity-cost
  vs. the best alternative position's own next bench slot: -86.1
  incremental PPR pts (scarcity weight 1.00, 1 bench slots remain) ->
  0.43x. Standalone value 0.0 -> 0.0."
```

Manual, un-rounded breakdown (`a`+`b`, reproduced directly from
`marginal_roster_utility_v2`'s own source):

| quantity | value |
|---|---|
| `candidate.value` (= his own `replacement_adjusted_value`) | **0.0** |
| position / depth rank | WR / 4 |
| `_fantasy_bench_utility_rate("WR", 4, 10, False)` | 0.098 (9.8%) |
| `_fantasy_bench_incremental_pts("WR", 4, 10)` | -157.4 |
| opportunity-cost gap vs. best alt position | -86.1 |
| scarcity weight (1 bench slot remains) | 1.00 |
| opportunity multiplier | 0.43x (floor is 0.4, not hit) |
| `utility = round(0.0 * 0.098 * 0.43, 2)` | **0.0** |

The rate (9.8%) and multiplier (0.43x) are both real, non-degenerate,
non-floor numbers -- they are NOT what produces the zero. **`candidate.value`
is already 0.0 before the rate/multiplier are ever applied**, so the
product is trivially 0.0 regardless of what the rate/multiplier are.

### Missing-data or unmodeled fallbacks

`(b)` None found. Harrison's projection is a real, ordinary,
formula-computed value from real stat-line inputs (`games: 12.0,
receptions: 41.0, receiving_yards: 608.0, receiving_tds: 4.0`, scored
through the same `score_projection()` every player uses -- no
`projected_points_override`, which is only used for K/DST). `source_status:
GOVERNED`, `evidence_status: ADMITTED_CURRENT_SEASON` -- not a
`REVIEW_ONLY`/manual/unmodeled asset. His `confidence: LOW` label is also
explained, not a mystery: `(a)` `_confidence()` computed
`width_ratio = (164.85 - 45.75) / 125.8 = 0.947`, far above the 0.40
MEDIUM threshold, so it falls through to `LOW` -- a real, wide
projection-uncertainty band, unrelated to the rookie/missing-data checks
earlier in that same function (both of which are False/present for him).
He does **not** carry any entry in
`config/nwr_verified_current_player_status_overrides_v1.json` (confirmed
by direct read of that file) -- `apply_status_overrides_to_ranking()` is
not involved in his zero at all (see the Higgins false lead below).

### Drop-list values, ordering, tie behavior

`(b)` Real `redraft_waivers(mode="REST_OF_SEASON")` `dropCandidates` (ranked
ascending by marginal utility, weakest first): Marvin Harrison (0.0) is
alone at the bottom -- no other real roster player ties him at 0.0.
Next-weakest: Carnell Tate (0.55), Michael Pittman (3.11), Wan'Dale
Robinson (3.84), Caleb Williams (5.55, bench QB2), then starter-upgrade
scenarios (Trevor Lawrence 20.0, Zay Flowers 25.4, Kenny Gainwell 26.48,
...). No tie-breaking behavior was exercised for Harrison specifically
since his value is uniquely lowest in this real roster.

### First-zero operation (exact, traced step by step)

`(a)`+`(b)`. Location: `src/services/redraft_engine_v1_service.py`,
inside `generate_rankings()`, the preliminary-row loop:

```python
value = round(projected - baseline.replacement_points, 4)   # ~line 1490
```

`baseline.replacement_points` (the WR replacement baseline, 125.8) was
itself set upstream in `calculate_replacement_levels()`'s
`_next_available_points()` (~lines 1394-1401):

```python
def _next_available_points(rows, selected):
    for player, points in rows:
        if player.player_id not in selected:
            return points
    return 0.0
```

This returns the projected-points of the highest-scoring WR who is **not**
in `selected` (the set of players this league's `expected_available`
simulation would actually roster leaguewide, given real roster shape
QB1/RB2/WR2/TE1/FLEX1/K1/DST1/BN6 x 10 teams -> WR `rostered_count: 53`).
**Marvin Harrison Jr. is himself that player** -- real, observed
`position_rank: 54` (one slot below the real 53-WR rostered-count
boundary) confirms he is exactly the first excluded WR in the real,
current projection ordering. Because the replacement baseline for his own
position is therefore set to **his own real projected score**, his
`value = his_own_projected - his_own_projected = 0.0` by construction --
not an approximation, not a coincidental rounding collision (verified:
`score_projection()`'s raw unrounded output for him is exactly `125.8`,
matching the stored, already-rounded `replacement_points` to full
precision). This zero then propagates unchanged through `_asset_pool()`
(`RosterPlayer.value = replacement_adjusted_value`) into
`marginal_roster_utility_v2`'s `candidate.value`, where it multiplies
through the (non-zero, non-floor) rate and opportunity-multiplier terms
and stays 0.0 all the way to the final rounded `utility`.

**A real, initially-confusing false lead investigated and ruled out**:
the WR immediately ahead of Harrison in the final displayed order,
Jayden Higgins (`00-0040130`, position_rank 53), *also* shows
`replacement_adjusted_value: 0.0` **and** `starter_gap: 0.0` even though
his real projected points (129.5) are higher than the 125.8 replacement
baseline and should algebraically yield `129.5 - 125.8 = 3.7`, not `0.0`.
Traced directly: Higgins carries a real, individually-sourced status
override on file (`config/nwr_verified_current_player_status_overrides_v1.json`,
`kind: "SEASON_OUT"`, torn ACL, cited to ESPN/NFL.com/Texans sources,
verified 2026-09-07) which `apply_status_overrides_to_ranking()` applies
**after** `generate_rankings()` runs, forcing both
`replacement_adjusted_value` and `starter_gap` to exactly `0.0` for him by
design (his original projection is preserved for provenance, only the
*automatic-recommendation* value is zeroed) -- and then re-sorts/re-ranks
the whole position by the post-override values, which is why Higgins (now
tied at 0.0 with Harrison, but with higher raw `projected_points` used as
the tie-break) ends up ranked just ahead of Harrison in the final row
order. **This is a real, correctly-functioning, unrelated mechanism, not
a second Harrison-shaped bug.** Confirmed Harrison himself carries **no**
entry in that override file, and his `starter_gap` is the normal,
non-zeroed `-61.4` (not forced to `0.0`), which is the decisive evidence
that his zero is NOT produced by the override path -- it comes purely
from the replacement-level mechanism described above.

### HARRISON ROOT CAUSE

**INTENTIONAL-CORRECT MODEL BEHAVIOR.** In every replacement-value
("VBD"/value-over-replacement) fantasy model, by definition, the player
who exactly defines a position's replacement baseline has value 0 -- that
is the mathematical meaning of "replacement level," not a defect. Real,
observed data this pass confirms Marvin Harrison Jr. genuinely IS that
player for WR in this specific real 10-team league's real current
projection ordering (`position_rank: 54`, one below the real
`rostered_count: 53` cutoff). His identity resolves correctly, his
projection is a real, complete, non-fallback, non-override,
formula-computed value, and the zero-producing arithmetic
(`projected - own_replacement_points == 0`) is exactly what a correctly
functioning replacement-value system should produce for the marginal
player at a position. No identity-resolution gap, input-wiring bug, or
missing-data mishandling was found anywhere on this path. Per the
directive, no change is proposed.

**One open, explicitly-disclosed, separate question this pass did NOT
resolve** (a projection-quality question, not a code-wiring question, and
outside what this pass could verify without inspecting the projection
GENERATION inputs upstream of this snapshot): is a `125.8`-point full
season projection (WR54 overall, effectively replacement-level) still a
reasonable current estimate for a former first-round rookie-year WR now
in his second full season, given the snapshot's own `source_as_of:
2026-09-08` is about a week old relative to this investigation
(2026-09-15) during an actively progressing real season? This pass
did not gather evidence either way (no comparison against a fresher
external source was attempted, consistent with the directive's own
instruction not to force NWR's numbers to match another service's) --
flagged as an open question for whoever owns projection-freshness
cadence, not a finding that the number is wrong.

## Investigation target 2: Tyrone Tracy provenance

`(b)`/`(c)` Real `redraft_waivers()` calls, both modes, same real free
agent (Sleeper id `11655`, canonical id `00-0039384`, real ranking row:
`overall_rank 93`, `replacement_adjusted_value 35.1`):

| mode | `weeklyProjectedPoints` | `marginalUtility` | `becomesStarter` | FAAB |
|---|---|---|---|---|
| REST_OF_SEASON | `null` (mode doesn't compute it) | **9.72** | false | $30-50, MEDIUM |
| THIS_WEEK (week 2) | **1.871** (real, live Sleeper weekly projection) | **9.72** (identical) | false | $30-50, MEDIUM (identical) |

`marginalUtilityExplanation` is byte-identical in both modes: `"...
Standalone value 35.1 -> 9.72."` -- driven entirely by his real
`REST_OF_SEASON` replacement-adjusted value (35.1), never by his weekly
number.

`(a)` Traced why, directly in source (`waiver_engine_service.py`,
`rank_waiver_candidates()`): the single call that produces `marginal_utility`,
`utility_result = marginal_roster_utility_v2(canonical_id,
owner_roster_canonical_ids, profile, ranking, manual_assets)`, takes no
`mode` or weekly-projection argument at all and is called identically
regardless of mode. `weekly_row`/`weeklyProjectedPoints` is read into the
candidate purely for **display** and as the `sort_key()`'s SECONDARY
tie-break key in `THIS_WEEK` mode only (`secondary =
candidate.weekly_projected_points if mode == "THIS_WEEK" else
candidate.ros_replacement_value` -- primary key is always
`candidate.marginal_utility`). `suggest_faab_bids()` (same file) is
likewise driven entirely by `candidate.marginal_utility` and never reads
weekly points either -- confirmed by direct read.

### TRACY CONSISTENCY: internally consistent, no bug found

The apparent contradiction ("low weekly projection but top waiver
priority") is not a bug: NWR's waiver-ranking/FAAB engine is, by design,
always driven by the real `REST_OF_SEASON` replacement-adjusted value in
**both** modes -- `THIS_WEEK` mode only additionally *surfaces* the real
current-week number for the owner's own reference/tie-breaking, it never
substitutes for or overrides the ranking signal. A player can therefore
correctly show a low single-week number (real, live, honestly reported --
`1.871` projected points for week 2, matching Worker 3's original
documented `1.9`) while still correctly ranking as the #1 real add
candidate, because his real ROS value (`35.1`, `overall_rank 93` out of
564) reflects an expected larger role later in the season that a single
early-week snapshot does not yet capture. This is the same conclusion
Worker 3's ledger entry already reached informally ("THIS_WEEK's own
weekly number can be low for a player whose ROS value is driven by a role
change") -- this pass traces it to the exact code mechanism
(`rank_waiver_candidates`'s mode-independent `marginal_roster_utility_v2`
call) rather than relying on that informal explanation. No change to
NWR's rankings was made or proposed; the directive was explicit this is
about internal consistency, not matching another service's numbers, and
none was compared.

## Zero Sleeper writes

Verified 3 ways, per the established method:
1. **Structural**: `SleeperHttpClient` (`src/services/sleeper_import_service.py`)
   exposes only `get_json` (`dir()` confirmed live) -- structurally
   incapable of writing.
2. **Grep**: this pass's own investigation script contains zero
   `POST`/`PUT`/`PATCH`/`DELETE` strings (confirmed).
3. **Before/after byte-diff**: `GET league/1312983576827920384/rosters`,
   taken immediately before this pass's first facade call and again after
   its last (`redraft_my_roster`, `redraft_waivers` x2, plus the manual
   `marginal_roster_utility_v2`/`explain_marginal_roster_reason` calls in
   between) -- **byte-identical**, SHA-256
   `6ad881713e233f7ce44e44e08f7c4211b6a0a5ff52437c9766b5cfe01add78e4`,
   `7149` bytes, both times.

## Code touched this pass

**None.** Zero production files were read-modified; only this new
documentation file was created. `redraft_waivers()` calls made against
the isolated scratch copy did append local decision-trace JSON lines
inside that scratch copy's own `decision_traces/` directory (the
endpoint's normal, documented behavior) -- entirely inside the scratch
directory, never inside this worktree's own `local_exports/`, never
inside the owner's real AppData install.

## Open questions for the fix worker

1. **Harrison is not a defect** -- no fix scope here. If a future worker
   ever wants to reconsider how replacement-level (exactly-0-value)
   players are surfaced/labeled in the UI (e.g., an explicit "this is
   the current replacement-level player at his position" badge instead of
   a bare `0.0`), that would be a presentation/UX enhancement, not a bug
   fix -- not requested by this investigation.
2. **Projection freshness** (disclosed, not verified either way): the
   admitted projection snapshot's `source_as_of` is `2026-09-08`; this
   investigation ran `2026-09-15`, about a week later, during a live
   season. Whether Harrison's (or any other player's) specific projection
   ought to be refreshed sooner given real in-season developments is a
   real, separate, unverified-by-this-pass question -- worth a future
   worker checking the admitted-snapshot refresh cadence generally, not
   specific to this one player.
3. **Not investigated, out of this pass's scope, already documented
   elsewhere**: the K/DST-invisible-to-skill-ranking gap
   (`unmatchedRosterSleeperPlayerIds: 3451, NE` on this same real roster) --
   this is the same, already-disclosed, by-design item from Worker 3/4's
   ledger entries, re-observed here only incidentally while tracing
   Harrison's roster context, not re-investigated.
4. No open questions block or scope anything for Tracy -- his behavior
   was confirmed internally consistent, not a bug requiring a fix.
