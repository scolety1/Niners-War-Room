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

## OPEN ISSUES FOR WORKER 3/4-5 (normalized factual status schema + source quality evaluation against gates 3/4/5)

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
