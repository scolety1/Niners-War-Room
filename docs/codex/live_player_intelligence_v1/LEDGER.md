# NWR Live Player Intelligence V1 — Ledger

Branch `upgrade/nwr-live-player-intelligence-v1-20260913`, worktree
`C:\NWR\live-player-intelligence-v1`. Start HEAD `4d46f107`. Not merged,
not pushed, not deployed.

## Worker 1 (this pass) — Baseline + preregistration + candidate source acquisition

**Commits:**
1. `29fca2d8` — `docs: preregister live player intelligence admission
   contract (WU0)` — the 10 admission gates, written BEFORE any source
   was measured. `docs/codex/live_player_intelligence_v1/
   LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md`.
2. (this commit) — `docs: characterize live player intelligence candidate
   sources (WU1)` — `docs/codex/live_player_intelligence_v1/
   CANDIDATE_SOURCE_ACQUISITION_V1.md` + this ledger.

**Baseline verified before any measurement:** branch/HEAD/clean worktree
confirmed; 41/41 pre-existing tests pass across
`test_live_player_intelligence_shadow_v1_service.py`,
`test_player_availability_status_service.py`,
`test_player_availability_status_consumer_consistency.py`,
`test_current_player_status_overrides_service.py`. No production file
touched.

**Sources characterized (real fetches, 2026-09-13):**
- (A) Sleeper `players/nfl` catalog — RE-VERIFIED. 18.1% actionable-
  signal canonical-pool coverage (up from 12.4% two days prior — real,
  observed week-progression churn). Rights unchanged (free,
  non-commercial-use-only, re-check before any commercial distribution).
- (B) nflverse official weekly injury report — RE-VERIFIED. 9.2%
  canonical-pool coverage (unchanged). **New finding: the file revises
  in place** — the same nominal Week 1 file changed its own
  `report_status` distribution (Out 27→31, blank 123→121) between the
  prior pass's pull and this one, detectable only by diffing successive
  pulls (no version column exists).
- (C) nflverse depth charts — **NEW, first characterized this pass**.
  Real ESPN-sourced schema (`dt, team, player_name, espn_id, gsis_id,
  pos_grp, pos_name, pos_rank`), materially different from the published
  data dictionary (real schema-drift finding, same pattern as the prior
  pass's injuries `date_modified` finding). 88.5% canonical-pool coverage
  via direct `gsis_id` match — the broadest of all sources examined.
  Real per-snapshot `dt` timestamps, near-daily cadence, 177 snapshots
  from 2026-03-22 to 2026-09-13 in one 49MB file. No injury field —
  role/starter-rank signal only, complementary to (A)/(B), not
  redundant.
- (D) NFL.com / official league-published injury reports — characterized
  as the Work Unit 2 benchmark candidate, NOT built. **Real, material
  rights finding: NFL.com's own live Terms and Conditions explicitly
  prohibit automated scraping/crawling/harvesting** (Section 14(d),
  quoted verbatim in the doc), independent of `robots.txt`'s technical
  permissiveness and independent of personal/non-commercial intent. A
  recurring automated production ingestion pipeline against NFL.com
  directly would knowingly violate its ToS. Official reporting cadence
  (Wed/Thu/Fri practice reports, final designation due 4PM) is real and
  publicly documented via `operations.nfl.com`, useful context for
  Work Unit 2 regardless of the ToS finding.

**Raw artifacts** (gitignored, not committed):
`local_exports/live_player_intelligence_shadow_v1/{nflverse_injuries,
nflverse_depth_charts,sleeper_players}/latest/`.

**No production file was modified.** `git diff --stat` against Start HEAD
shows only the two new docs (contract + acquisition doc) and this ledger.

## Worker 2 — Official truth benchmark + canonical identity mapping

**Commits:** (see `git log`) — docs + one new pure service module + one new
test file + two standalone research/build scripts + committed benchmark/
identity-mapping data artifacts. No existing file modified (`git diff
--stat` against Start HEAD `61623f11` shows only new files).

**A. Official truth benchmark** — `OFFICIAL_TRUTH_BENCHMARK_V1.md` +
`official_truth_benchmark_v1/nflverse_week1_2026_official_truth_benchmark.csv`
(182 rows, all 32 teams, 2026 Week 1 — the only week published so far).
Built from nflverse's official injury report (real fresh pull) per the
rights constraint, joined to the canonical pool via the SAME identity
resolver used everywhere else. Independently corroborated with ONE
manual, one-off `WebFetch` against `nfl.com/injuries/league/2026/reg1`
covering 8 specific players across 6 teams: **8/8 exact agreement**.
Resolved Worker 1's open PFR question: Pro-Football-Reference/
Sports-Reference is ALSO ToS-restricted (real quoted anti-scraping
language found via `WebSearch`, plus two independent HTTP 403s on direct
fetch) — not a lower-friction alternative, closing that open item.
**Explicitly disclosed limitation**: nflverse's file has no Wed/Thu/Fri
per-day rows (one row per player per week, revised in place) — this
pass re-pulled ~11 minutes after Worker 1's own pull and found 0 rows
changed, real evidence the file had already reached its Friday-final
state, but this means Gate 5's precise P95 latency still cannot be
computed from this file alone. **Independence caveat honestly
disclosed**: the benchmark is substantially nflverse itself; the 8-player
NFL.com check is real corroboration, not a second full independent
dataset.

**B. Canonical identity mapping** — `IDENTITY_MAPPING_V1.md` +
`src/services/live_player_intelligence_identity_mapping_v1_service.py`
(new pure module, reuses `_identity`, does NOT invent a second matcher) +
`tests/test_live_player_intelligence_identity_mapping_v1_service.py` (16
tests, all passing). Maps ALL rows of all three sources (not just the
"actionable status" subset), classifying each into matched-uniquely /
unmatched / ambiguous / team-mismatch / name-mismatch(diagnostic) /
provider-ID-mismatch(diagnostic), with zero ambiguous rows found across
all three sources and 15 real Sleeper team-mismatch rows quarantined (14
of which are the already-known `LAR`/`LA` team-code-alias convention
noise this codebase already handles elsewhere — reporting-only label, does
not un-quarantine them; 1 genuine, Xavier Gipson PHI-vs-NYG). Exact
counts and full quarantine lists are in `IDENTITY_MAPPING_V1.md` and
`identity_mapping_v1/*_quarantined.csv` / `summary.json` (all committed).
Full per-row detail for every row (large — 12k+ for Sleeper) was written
to gitignored `local_exports/.../identity_mapping_v1/` instead of
committed — regenerable via `scripts/build_live_player_intelligence_identity_mapping_v1.py`.

**Real, reproducible run commands** (both standalone, network-free, read
already-fetched local files):
- `python scripts/build_live_player_intelligence_official_truth_benchmark_v1.py`
- `python scripts/build_live_player_intelligence_identity_mapping_v1.py`

**Hard boundary respected**: nothing under `marginal_roster_utility_v2`,
draft recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/lifecycle-resolver/`DecisionResultEnvelope`/
`PlayerAvailabilityStatus` was touched. `player_availability_status_service.py`
tests still pass unmodified (51/51 across the shadow/availability/override
test files, plus the 16 new identity-mapping tests, plus
`waiver_engine_service`/`fantasypros_kdst_consensus_service` tests — 79
total, all green).

## Worker 3 — Normalized factual status schema (Work Unit 4) + source quality evaluation (Work Unit 5)

**Commits:** (see `git log`) — schema extension + gate-computation service
+ two new test files + one new standalone script + new committed docs/
data artifact. No existing production file's BEHAVIOR changed (`git diff
--stat` against Start HEAD `81b3d36f` shows only additive changes to
`player_availability_status_service.py` — 86 insertions, 0 deletions —
plus new files).

**A. Work Unit 4 — schema extension.** Extended the EXISTING
`PlayerAvailabilityStatus` dataclass (`player_availability_status_service.py`)
in place — did NOT fork a parallel schema. Nine new fields, all
defaulting to `None` (Gate 1's "unknown stays unknown"): `game_status`
(the game-day inactive determination, kept separate from
`injury_designation`'s weekly designation per Gate 5's two distinct
freshness bars), `on_injured_reserve`/`on_pup`/`on_nfi` (broken out from
the existing, unchanged, still-populated-the-same-way `ir_pup_nfi`
free-text field), `active_inactive`, `depth_chart_position`/
`depth_chart_context`, `fetched_at`, `freshness_seconds` (via a new pure
`compute_freshness_seconds` helper). Confirmed explicitly OUT of scope
(no fields added for): news prose, analyst commentary, projected return
date, role speculation. Today's only real source (the manual-override
wrapper) leaves every new field `None` — proven by a real test
(`test_real_manual_override_wrapper_leaves_all_new_fields_none`) — so
CURRENT production behavior is unchanged, only extended. 14 tests in
`tests/test_player_availability_status_service.py` (6 original + 8 new),
all passing.

**B. Work Unit 5 — real gate computation.** New pure module
`src/services/live_player_intelligence_source_quality_v1_service.py`
(coverage/agreement/freshness computation, no I/O) + standalone script
`scripts/build_live_player_intelligence_source_quality_v1.py` (reads
already-fetched local files, reuses the EXISTING
`build_sleeper_shadow_records`/`match_shadow_records_to_canonical`/
`load_canonical_pool`/`classify_rows` production-adjacent functions — no
second identity matcher) + 24 tests on known constructed examples
(`tests/test_live_player_intelligence_source_quality_v1_service.py`).
Real results (full detail + real per-player disagreement table in
`SOURCE_QUALITY_EVALUATION_V1.md`, machine-readable in
`source_quality_evaluation_v1/summary.json`, both committed):

- **Gate 4 (coverage)**: population = 52 real official-report
  fantasy-relevant players resolvable to NWR's canonical pool (Jonathon
  Brooks, the 53rd in-scope-position row, is real but outside NWR's
  governed pool entirely — a different, already-documented exclusion —
  reported separately, not folded into the population). **Sleeper
  covers only 17/52 (32.69%) — FAILS the ≥95% gate badly** (35/52, 67.3%,
  have no Sleeper signal at all this week). nflverse depth charts
  (role/context only, not an injury field) covers 52/52 (100%) of the
  same population — real, strong, but a different concept.
- **Gate 3 (agreement)**: nflverse-injuries-vs-itself is explicitly
  disclosed as circular (100% by construction, not real evidence) — the
  admission contract's own scope note anticipated this; a genuinely
  independent Gate 3 measurement for nflverse still does not exist this
  cycle (best available real evidence remains Worker 2's 8/8 NFL.com
  spot-check). **The real, meaningful computation — Sleeper
  `injury_status` vs. the benchmark, 14 comparable pairs — found 28.57%
  exact agreement (FAILS the ≥99% gate badly) AND one real zero-tolerance
  hard contradiction** (Zay Flowers, BAL: benchmark says
  `CLEARED_OR_NOT_LISTED`/healthy, Sleeper's own `injury_status="Out"`
  with a `news_updated` only ~52 minutes old — not a stale-data artifact).
  Real, disclosed pattern (not explained, not claimed as causal): every
  Sleeper disagreement was the same-or-more-severe than the benchmark,
  never the reverse.
- **Gate 5 (freshness)**: nflverse injuries — **not computable this
  session**, honestly reported as such. This pass added a THIRD real poll
  (beyond Worker 1's and Worker 2's) — zero changes across all three,
  ~27 minutes total — real stability evidence but zero observed update
  events means no latency can be timed; Worker 1's own 2-day-apart diff
  proves the file does revise earlier in a week but is too coarse for a
  P95. Sleeper — a real per-player `news_updated` epoch-ms field exists
  (P50 ~14.2 days, P95 ~398 days over 722 flagged players) but this pass
  found real evidence it is CONTAMINATED (only 12.7% of values are
  <24h old; a real 15.1% tail is 180+ days old, with multi-year-old
  values directly observed) — proving it is a whole-record "last touched
  for any reason" field, not specifically bumped on `injury_status`
  changes. **No P95 is claimed for Sleeper either** — the honest finding
  is the bucketed age distribution itself (mixed: real evidence some
  updates ARE near-real-time, real evidence the field overall cannot be
  trusted as a freshness clock).
- **Preliminary source×field verdicts** (full table in the doc): nflverse
  injuries `injury_designation`/`practice_state` → SHADOW (Gate 3/5 not
  yet independently measurable, not a failure); Sleeper
  `injury_designation` → **REJECT** (fails Gate 3 AND Gate 4 with real
  current-week evidence, including the zero-contradiction floor); Sleeper
  `ir_pup_nfi`-class fields → SHADOW (too little evidence, n=3, directionally
  clean); Sleeper `current_team`/`active_inactive` → NOT EVALUATED (no
  benchmark exists for these concepts); nflverse depth charts
  `depth_chart_position`/`depth_chart_context` → SHADOW (Gate 3 N/A,
  strong Gate 4 coverage, Gate 5 not re-measured this pass). No
  `RIGHTS_BLOCKED` verdict applies to anything evaluated here.

**Hard boundary respected**: nothing under `marginal_roster_utility_v2`,
draft recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/lifecycle-resolver/`DecisionResultEnvelope`, or
`PlayerAvailabilityStatus`'s CURRENT production behavior was touched —
only additive schema fields (all default `None`, all left `None` by
today's only real source) and new, unwired evaluation code/docs.
73 tests green across
`test_player_availability_status_service.py`/
`test_player_availability_status_consumer_consistency.py`/
`test_live_player_intelligence_shadow_v1_service.py`/
`test_live_player_intelligence_identity_mapping_v1_service.py`/
`test_live_player_intelligence_source_quality_v1_service.py`.

**Real, reproducible run command** (reads only already-fetched local
files, no network I/O of its own):
`python scripts/build_live_player_intelligence_source_quality_v1.py`

## Worker 4 — Additional evidence + source composition/precedence (Work Unit 6) + shadow-mode consumer testing (Work Unit 7) + production admission decision (Work Unit 8) — CYCLE CLOSING

**Commits:** (see `git log`) — one addendum to an existing doc (additive
section only, nothing above it edited), new composition/precedence service
+ its test file, two new standalone evidence-gathering scripts + their
committed JSON outputs, the real admission-decision doc, and this closing
ledger update. No existing PRODUCTION file (`desktop_facade.py`,
`player_availability_status_service.py`, or any recommendation/scoring
module) was touched — `git diff --stat` against Start HEAD `8a09b031`
shows only new files plus the one additive doc section.

**A. Additional evidence gathering (step 1 of Work Unit 6).** Real,
reproducible via
`python scripts/build_live_player_intelligence_worker4_additional_evidence_v1.py`
(committed output: `worker4_additional_evidence_v1/summary.json`; full
detail folded into `SOURCE_QUALITY_EVALUATION_V1.md`'s new addendum
section, nothing above it edited):
  - **nflverse Gate 5**: a real, single, lightweight GET against GitHub's
    Releases API read the `injuries_2026.csv` asset's own `updated_at`
    (`2026-09-13T12:41:50Z`) — a real, independent, per-FILE freshness
    proxy distinct from in-row data (which the file has none of). Extended
    the confirmed-stable observation window from Worker 3's ~27 minutes to
    **~14.95 hours**. Still not P95-computable (every poll this cycle,
    across all workers, occurred AFTER that timestamp — zero update EVENTS
    captured in any window yet) but is a real, stronger stability claim
    plus a new, cheap, reusable freshness-detection mechanism for a future
    multi-week cycle.
  - **Sleeper `current_team` vs. the same 182-row benchmark** (a gap
    Worker 3 explicitly flagged NOT YET EVALUATED): broader identity
    coverage of the 52-player population is real and strong (47/52,
    90.38%, via Sleeper's FULL catalog, not just the injury-flagged
    subset). The non-circular team-agreement sample (`MATCHED_GSIS_DIRECT`
    only, n=9) is 88.89% raw / **100% alias-adjusted** (the one raw
    disagreement is the already-known LAR/LA code-convention pair, not a
    genuine conflict). Real, honestly small (n=9) — not claimed as a
    passed gate, but the most directionally positive finding of the whole
    cycle.

**B. Work Unit 6 — real composition/precedence engine.** New pure module
`src/services/live_player_intelligence_composition_v1_service.py` (no I/O,
not imported by `desktop_facade.py`/`player_availability_status_service.py`/
any recommendation module — architecture guard test confirms this) +
`tests/test_live_player_intelligence_composition_v1_service.py` (19 tests,
all passing). Implements real precedence (manual verified override >
reserved-but-currently-EMPTY admitted-automated tier > supplementary
SHADOW-source tier > unknown) with a real freshness-monotonicity guarantee
(an out-of-order-arriving OLDER same-tier observation is rejected, proven
by a real test) and structural, defense-in-depth exclusion of Sleeper's
REJECTED `injury_designation` field (two independent enforcement points,
both tested). Covers every directive-named scenario: newer-after-older,
manual-then-automated (override wins), automated-then-manual (override
still wins), conflicting same-tier sources (resolved by freshness, or by a
documented per-field preferred-source order when neither side has a usable
timestamp), an unknown field staying unknown (never a guessed "healthy"),
and a released/team-change state. Still entirely SHADOW infrastructure —
never wired into any consumer or recommendation path this pass.

**C. Work Unit 7 — real shadow-mode consumer plumbing test.** New
standalone script
`scripts/build_live_player_intelligence_worker4_shadow_consumer_test_v1.py`
(real network I/O against Sleeper's public, read-only API; NOT exercised
by pytest, same convention as every other network-fetching script in this
family). Used the REAL, read-only Fantasy Gamers Sleeper league (id
`1312983576827920384`, username `scolety`), imported via the SAME
already-existing, already-proven `import_sleeper_redraft_profile` path
other tests in this repo already use, into an ISOLATED throwaway
`redraft_root` (never the owner's real production AppData store). Real
results (committed: `shadow_consumer_test_v1/summary.json`):
  - **Zero side effects, proven, not asserted**: every one of 11 real
    consumer-surface reads (Bootstrap/Home, `PlayerAvailabilityStatus`
    authority used by Lineup/Waivers/Trades/Player-Drawer, Weekly Home
    Actions, Weekly Lineup, My Roster, Free Agents, Opponent Rosters,
    Waivers/Improve-Team, Trade Finder, League Workspace Context, Data
    Health) was captured BEFORE and AFTER building the real shadow
    composition, hashed, and diffed. Raw hashes differ on 6/11 surfaces --
    investigated for real and found to be PRE-EXISTING, ALREADY-PRESENT
    volatility unrelated to this pass's work entirely (`generatedAtUtc`/
    `lastUpdate`/`lastGeneratedTimestamp` wall-clock stamps advancing
    between two real calls, `servedFromCache` flipping true once a real
    cache warms -- confirmed by calling the SAME facade methods twice in
    isolation with zero shadow-composition code involved at all). With
    those three documented volatile keys stripped, **all 11 surfaces are
    byte-identical before and after** -- the real, honest zero-side-effect
    proof.
  - **Real identity plumbing works**: of 565 distinct real player ids
    surfaced across those 11 real reads for this real, live league,
    **507 (89.73%) resolve into a real composed shadow status** built
    entirely outside the facade. A real 3-way comparison (current
    production status / composed shadow status / official benchmark
    truth) was recorded for the 53 real overlapping players -- disclosed,
    not acted on.
  - **Sleeper writes: 0**, verified by code inspection (`SleeperHttpClient`
    in `sleeper_import_service.py` defines only `get_json`/`urlopen` GET;
    no POST/PUT/DELETE exists anywhere in that client or in
    `sleeper_redraft_owner_service.py`).

**D. Work Unit 8 — the real production admission decision.**
`PRODUCTION_ADMISSION_DECISION_V1.md` (full detail there). Headline: **no
source/field pair evaluated this cycle clears the full admission bar for
recommendation-affecting integration.** Sleeper `injury_designation` stays
REJECTED (`NO_SOURCE_PASSED`). Sleeper `ir_pup_nfi`-class/`current_team`/
`active_inactive` stay `NO_SOURCE_PASSED` (insufficient evidence, not
failure -- `current_team`'s n=9 is the strongest small-sample finding of
the cycle but still too small to round up). nflverse
`injury_designation`/`practice_state`/depth-chart role fields are real,
clean on Gates 1/2/9, but do not clear Gates 3/5 -- ruled
`FREE_SOURCE_CONTEXT_ONLY` (a future, SEPARATE pass could wire them as
disclosed, non-recommendation-affecting display context; this pass does
NOT perform that wiring). The game-day inactive determination
(`game_status`) gets its own decisive call -- `PAID_SOURCE_REQUIRED_FOR_
GAME_DAY` -- because neither free source has ANY mechanism capable of
proving a 10-minute freshness bar even in principle (nflverse: no per-row
timestamp at all; Sleeper: proven-contaminated timestamp), a real,
structural disqualification distinct from the ordinary 2-hour use case's
"simply not measured yet" status.

**Work Unit 9 (hard game-day availability integration affecting
recommendations): NOT ATTEMPTED.** Per the directive's own instruction --
no field clears Gates 3 AND 5 together with real, independent,
threshold-level evidence this cycle.

**Tests**: 19 new composition tests + the 108 already-passing
live-player-intelligence/player-availability/override tests (127 total,
all green). `test_desktop_application_api.py`: 46 passed / 4 failed --
confirmed via `git stash -u` that the SAME 4 tests fail at Start HEAD
`8a09b031` with ZERO of this pass's files present (pure pre-existing
failures, unrelated to this cycle). Frontend `vitest run` could not be
attempted this pass -- `desktop/node_modules` was never installed in this
worktree (a pre-existing environment condition; this pass made zero
frontend changes, so nothing of this pass's own could have regressed
there).

**Hard boundary respected**: nothing under `marginal_roster_utility_v2`,
draft recommendation logic, scoring, roster legality, `LeagueSnapshot`/
`LeagueWorkspaceContext`/lifecycle-resolver/`DecisionResultEnvelope`, or
any live recommendation's actual output was touched this pass.

---

## Worker 5 (separate pass, same worktree) -- Prospective Outcome V1: outcome-evaluation schema + ingestion mechanism

**This is a SEPARATE body of work from the Live Player Intelligence V1
cycle above** (that cycle closed at Worker 4, is DONE, and was not
reopened). Full detail lives in its own doc directory, not folded into this
one:
`docs/codex/prospective_outcome_v1/PROSPECTIVE_OUTCOME_V1.md`.

One-paragraph summary: `in_season_decision_trace_service.py`'s
`record_outcome` append-path existed but had no real ingestion mechanism
deciding what to put in it. This pass built (1) eight genuinely distinct
decision-type-specific outcome schemas (`prospective_outcome_schema_v1_
service.py` -- START_SIT/WAIVER/ADD_DROP/FAAB/TRADE/TRADE_FINDER/STREAMER/
DRAFT, deliberately not one generic score), (2) a pure ingestion mechanism
over real, already-fetched Sleeper data (`prospective_outcome_ingestion_v1_
service.py`), and (3) a small, additive, backward-compatible `detail`
parameter on `record_outcome` itself. Real Week 1 2026 Sleeper data for the
real Fantasy Gamers league was used for a real, committed fixture-based
test AND a real live end-to-end demo script (isolated throwaway root, zero
Sleeper writes) proving the whole pipeline plus the append-only guarantee
against real data. No facade/UI wiring was added this pass (explicitly left
to the next worker, alongside History UI V2 and boundary property tests --
see the doc's own "Open issues" section for the full list). Hard boundary
respected: nothing under `marginal_roster_utility_v2`, draft recommendation
logic, scoring, roster legality, `LeagueSnapshot`/`LeagueWorkspaceContext`/
lifecycle-resolver/`DecisionResultEnvelope`/`PlayerAvailabilityStatus`
semantics, or this cycle's admission/composition code was touched.

---

## CYCLE CLOSING SUMMARY (Workers 1-4, whole Live Player Intelligence V1 cycle)

Four real, current-season candidate signals were characterized end-to-end
against a preregistered, evidence-based admission contract: Sleeper's
public players catalog, nflverse's official weekly injury report, nflverse
depth charts, and (as a benchmark-only source, not itself an admission
candidate) a real 182-row Week-1 2026 official-truth benchmark built from
nflverse's own file and independently corroborated against 8 real,
manually-checked NFL.com rows. One real, hard rejection was found and
honestly enforced (Sleeper `injury_designation`, with a real, current,
zero-tolerance-floor-violating hard contradiction -- Zay Flowers, BAL).
Two real, clean, narrow, identity-resolved sources (nflverse's injury
report and depth charts) were found safe for disclosed context display but
NOT for anything recommendation-affecting, because this cycle's own
preregistered Gate 3 (independent agreement) and Gate 5 (freshness) could
not be honestly cleared for either -- not because either source failed
them, but because a genuinely independent, non-circular benchmark and a
real multi-week polling cadence do not yet exist. A real, working,
fully-tested source-composition/precedence engine was built and shadow-
tested end-to-end against a real, live, read-only league with zero side
effects and zero Sleeper writes -- proving the PLUMBING for a future
promotion is real, separate from the admission-worthiness question. The
honest final conclusion is that this cycle correctly did NOT promote
anything into recommendation-affecting production status, and documents
exactly what additional real evidence (mostly: more time, more weeks, a
larger sample, or a real paid-vendor evaluation for the game-day case)
would be needed before a future cycle could responsibly do so.

## OPEN ISSUES FOR FUTURE CYCLES (Work Units 12+, per the outer directive)

1. **nflverse Gate 3**: still no genuinely independent, non-circular
   official benchmark exists (NFL.com/PFR both ToS-blocked for automated
   use). Either build one through a different, real, rights-clean channel,
   or get an explicit owner-level risk-acceptance decision to treat the
   existing 8/8 NFL.com manual spot-check as the practical evidence
   ceiling -- that is a different KIND of decision (owner risk acceptance)
   than anything this cycle's workers were authorized to make themselves.
2. **nflverse Gate 5**: needs a real multi-week polling cadence (this
   whole cycle only ever had Week 1 to observe) to catch a real update
   event and compute an honest P95. The GitHub release-asset `updated_at`
   metadata check this pass added is a cheap, reusable mechanism for that
   -- poll it, don't re-download the full CSV every time.
3. **Sleeper `current_team`/`ir_pup_nfi`-class fields**: real, clean,
   small samples (n=9, n=3) -- simply need more real overlap cases (more
   weeks, or a dedicated roster-ground-truth source) to reach a confident
   verdict either way. This looks like the fastest realistic path to an
   actual `FREE_SOURCE_ADMITTED`/`FIELD_SPECIFIC_FREE_SOURCE_ADMITTED`
   verdict of anything evaluated this cycle.
4. **`game_status`/game-day inactive determination**: a real paid-vendor
   evaluation (RotoWire/SportsDataIO/Sportradar, per Worker 1's historical
   bakeoff) against this contract's actual 10-minute Gate 5 bar has never
   been performed. Needed before `PAID_SOURCE_REQUIRED_FOR_GAME_DAY` can
   become an actual admission rather than a documented blocker.
5. **Sleeper `active_inactive`**: needs its own dedicated ground-truth
   source; the injury-report benchmark has no comparable concept at all.
6. **The 15 quarantined Sleeper team-mismatch rows** (Worker 2, 14
   known-alias/1 genuine Xavier Gipson) and the Sleeper
   `depth_chart_position`/`depth_chart_order` vs. nflverse `pos_rank`
   cross-check (Worker 1) remain unresolved, carried forward again.
7. **If a future worker DOES wire nflverse `injury_designation`/
   `practice_state`/depth-chart fields as `FREE_SOURCE_CONTEXT_ONLY`
   display** (this cycle explicitly did not): it must never feed any
   ranking/score/eligibility calculation (Gate 10), must visibly disclose
   its own unverified-for-recommendation status, and must show
   `fetchedAt` alongside the value. See
   `PRODUCTION_ADMISSION_DECISION_V1.md`'s "What `FREE_SOURCE_CONTEXT_ONLY`
   means here" section for the exact conditions.
8. **Work Unit 9 (hard availability integration)** should not be attempted
   until at least one of items 1-4 above produces a real, independent,
   threshold-clearing result for BOTH Gate 3 and Gate 5 on the SAME field.

---

## OPEN ISSUES FOR WORKER 4 (Work Unit 6-7: source composition/precedence + shadow-mode consumer testing) — HISTORICAL, ADDRESSED ABOVE

1. **Sleeper's `injury_designation` field has a preliminary REJECT
   verdict** (Gate 3 and Gate 4 both fail badly, with a real hard
   contradiction) — a future composition/precedence design (Work Unit 6)
   should NOT treat Sleeper as a viable primary or even corroborating
   injury-designation source without new evidence; it may still be
   viable for OTHER fields (`ir_pup_nfi`-class, `current_team`) that
   weren't rejected here, but those also were not affirmatively measured
   — treat as genuinely unknown, not pre-cleared.
2. **nflverse injuries' Gate 3/5 still lack an independent, non-circular
   measurement.** A real fix requires either (a) a genuinely independent
   second official source (blocked by Worker 1/2's NFL.com/PFR rights
   findings for automated use), or (b) accepting the 8/8 NFL.com manual
   spot-check as the practical ceiling of available evidence and making
   an explicit, disclosed risk call about that at promotion time — not
   this pass's decision to make.
3. **Gate 5 for nflverse injuries needs either a multi-week polling
   cadence** (this cycle only has Week 1 to observe — a real update event
   has never actually been captured mid-transition) **or a different
   source with a real per-update timestamp.** Worth revisiting once Week
   2's file exists.
4. **Sleeper `current_team`/`active_inactive`/roster-status fields were
   not evaluated against any benchmark this pass** — the injury-report
   benchmark has no comparable ground truth for these concepts; a future
   worker wanting to evaluate them needs a different real ground-truth
   source (e.g. a manually-verified roster snapshot) before any
   admission claim.
5. **The `on_injured_reserve`/`on_pup`/`on_nfi` split fields (Work Unit
   4's schema) are defined and tested for structure/defaults only** —
   no automated source has been wired to populate them yet (that is a
   promotion-time decision, deliberately not made this pass).
6. All of Worker 1/2's still-open items not superseded above remain open
   (see the historical section below): items 4/5/6 in the original
   "OPEN ISSUES FOR WORKER 3/4-5" list (now folded into this section) —
   specifically, the 15 quarantined Sleeper team-mismatch rows are still
   unresolved, Sleeper `depth_chart_position`/`depth_chart_order` vs.
   nflverse depth-chart `pos_rank` still uncross-checked, and depth
   charts' historical range beyond 2026-03-22 still unconfirmed.
7. Gates 6 (precedence), 7 (cross-league correctness), 8 (performance),
   and 10 (recommendation regression) remain promotion-time gates, not
   evaluable from benchmark/gate-computation work alone — Work Unit
   6-7's job.

## OPEN ISSUES FOR WORKER 3/4-5 (normalized factual status schema + source quality evaluation against gates 3/4/5) — HISTORICAL, ADDRESSED ABOVE

1. **Gate 3's ≥99% exact-agreement figure still not computed as a
   percentage.** The benchmark and the 8-player spot-check now exist; a
   real agreement-rate computation (Sleeper vs. benchmark, depth-chart
   role signal has no injury field to compare) is still open.
2. **Gate 5's precise P95 latency is still not computable** from
   nflverse's injuries file alone (no per-update timestamp in the file,
   only season/week). Consider a repeated-poll-and-diff approach (log
   each pull's own `fetched_at_utc`, treat "changed since last poll" as
   the closest obtainable freshness proxy) if a real P95 number is needed
   before a wider polling window naturally accumulates.
3. **Gate 4's ≥95% coverage-of-official-report-population** is now
   directly computable from `official_truth_benchmark_v1`'s 182 rows (the
   real official-report population for Week 1) cross-referenced against
   Sleeper's/depth-charts' own coverage — not yet computed by this pass,
   flagged for the next worker.
4. **The 15 quarantined Sleeper team-mismatch rows** (14 known-alias, 1
   genuine — Xavier Gipson) were not resolved one way or the other, only
   quarantined and listed. A future pass could decide whether the
   already-existing app-wide `LAR`/`LA`/`JAC`/`JAX` alias convention
   should also apply inside `_identity` itself (a real, separate design
   decision, deliberately NOT made unilaterally by this pass since the
   directive said reuse `_identity`, don't modify it).
5. Sleeper's `depth_chart_position`/`depth_chart_order` vs. nflverse
   depth-chart `pos_rank` (Worker 1's open item #3) still not
   cross-checked.
6. nflverse depth charts' historical range beyond 2026-03-22 (Worker 1's
   open item #4) still not confirmed.
7. Gates 6 (precedence), 7 (cross-league correctness), 8 (performance),
   and 10 (recommendation regression) remain promotion-time gates, not
   evaluable from benchmark/identity work alone.

## OPEN ISSUES FOR WORKER 2 (official-NFL-truth-benchmark worker) — HISTORICAL, ADDRESSED ABOVE

This section is Worker 1's original handoff, kept verbatim for the audit
trail. Item 1 (rights path) and item 4/3-PFR (Pro-Football-Reference
verification) are now RESOLVED by Worker 2 above. Item 2 (Gate 3/5
figures) is PARTIALLY addressed (benchmark + spot-check now exist; the
percentage itself is still open, see "OPEN ISSUES FOR WORKER 3/4-5" above).
Items 3/5 (Sleeper depth-chart-order cross-check) and 4/6 (depth-chart
historical range) remain open, carried forward above.

1. **Rights path decision needed before building the benchmark**:
   NFL.com direct scraping is ToS-prohibited for a recurring/automated
   pipeline (see Gate 9 and the (D) section above). Decide between (a) a
   bounded, human-reviewed, one-time-per-sample-window manual cross-check
   (lower risk, more labor, does not itself become a stored automated
   scrape), (b) verifying Pro-Football-Reference's actual data-use terms
   (returned HTTP 403 to this pass's fetch tool, genuinely unverified —
   check this first, it's the clearest untried lead), or (c) escalating
   to the owner for an explicit risk-accepted decision or a real paid
   vendor from the prior bakeoff (RotoWire/SportsDataIO/Sportradar) that
   has already solved licensing.
2. **Gate 3's ≥99% exact-agreement figure and Gate 5's precise P95
   freshness figures** cannot be computed until an actual official-truth
   benchmark sample exists — this pass only characterized the raw
   material, it did not build the benchmark or run any agreement/latency
   measurement against it.
3. **Sleeper's `depth_chart_position`/`depth_chart_order` vs. the new
   nflverse depth-chart `pos_rank`** were not cross-checked against each
   other this pass (time-boxed) — worth reconciling if a future
   promotion pass wants to use either as a starter/role signal.
4. **nflverse depth charts' historical range beyond 2026-03-22** was not
   confirmed (111 total GitHub release assets exist per the releases
   page but were not individually enumerated this pass).
5. Official NFL.com practice/designation publication timestamps (needed
   to measure Gate 5's ordinary-context 2-hour bar precisely) were not
   found on the live injuries page itself — the page shows no visible
   "report generated at" marker; Worker 2 will need another way to pin
   down exact official-publication timestamps (e.g. via the operations
   policy's fixed weekly schedule as an expected-time proxy, or a
   licensed vendor's own timestamp field once/if one is engaged).
6. Gates 6 (precedence), 7 (cross-league correctness), 8 (performance),
   and 10 (recommendation regression) are all promotion-time gates, not
   evaluable from source characterization alone — they will need a
   later, separate promotion-design work unit once Gates 1-5/9 are
   actually cleared for specific fields.
