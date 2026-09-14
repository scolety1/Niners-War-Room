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

## OPEN ISSUES FOR WORKER 2 (official-NFL-truth-benchmark worker)

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
