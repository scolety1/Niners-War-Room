# NWR Live Player Intelligence — Official Truth Benchmark V1

Work Unit 2, branch `upgrade/nwr-live-player-intelligence-v1-20260913`,
worktree `C:\NWR\live-player-intelligence-v1`. Built 2026-09-13/14 (UTC
`fetched_at_utc` lands 2026-09-14 early morning). Evaluated against
`LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md` (preregistered before any
source was measured) and extends Worker 1's
`CANDIDATE_SOURCE_ACQUISITION_V1.md` and `LEDGER.md`.

## THIS IS A TRUTH BENCHMARK FOR EVALUATION, NOT A PRODUCTION REDISTRIBUTION

Everything in this doc and its associated dataset
(`official_truth_benchmark_v1/nflverse_week1_2026_official_truth_benchmark.csv`)
exists so a later, separate promotion pass can measure Gate 3 (official
factual agreement) and Gate 5 (freshness) against something concrete.
**Production admission of any source is Gate 9 — a separate rights
question this doc does not resolve or imply.** Nothing here is wired into
`PlayerAvailabilityStatus`, any consumer of it, or any recommendation path.

---

## Rights path taken (per this work cycle's explicit constraint)

Worker 1 found NFL.com's live Terms and Conditions (Section 14(d))
explicitly prohibit scraping/crawling/harvesting, independent of
`robots.txt`'s technical permissiveness. Per the directive governing this
pass, the benchmark was built as follows:

1. **Primary reference: nflverse's own official injury report**
   (`github.com/nflverse/nflverse-data`, release tag `injuries`,
   `injuries_2026.csv`). Real, fresh, free, keyless fetch via the existing,
   already-admissible `scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`
   — no restrictive rights posture found (same posture this repo already
   relies on elsewhere for nflverse data). nflverse's own data is itself
   sourced from official club-reported injury designations — it is not a
   fully independent third party, but it carries no rights restriction of
   its own, unlike NFL.com direct.
2. **A SMALL, one-off, manually-issued cross-check against NFL.com** (not a
   loop, not a stored automated pipeline — a single `WebFetch` call reading
   `https://www.nfl.com/injuries/league/2026/reg1`, the same live,
   confirmed-indexed URL Worker 1 already characterized) to independently
   corroborate nflverse against the actual official page for a handful of
   specific players. Full agreement — see below.
3. **Pro-Football-Reference / Sports-Reference rights check** — see its own
   section below. Resolved: also ToS-restricted, not a lower-friction
   alternative.

### The one-off NFL.com cross-check (single fetch, 8 players, real result)

One `WebFetch` call against `https://www.nfl.com/injuries/league/2026/reg1`
(the league-wide Week 1 page — one HTTP request covering all 32 teams, not
a per-team loop), reading off 8 specific players already flagged in
nflverse's file (the highest-stakes `Out`/`Doubtful`/`Questionable` rows,
across 6 different teams):

| Player | Team | nflverse `report_status` | NFL.com page (manual read) | Agree? |
|---|---|---|---|---|
| Tua Tagovailoa | ATL | Out | Out | YES |
| Michael Penix Jr. | ATL | Out | Out | YES |
| Garrett Williams | ARI | Out | Out | YES |
| Nnamdi Madubuike | BAL | Out | Out | YES |
| Shemar Stewart | CIN | Doubtful | Doubtful | YES |
| Jalen McMillan | TB | Doubtful | Doubtful | YES |
| Kene Nwangwu | NYJ | Doubtful | Doubtful | YES |
| Za'Darius Smith | ATL | Questionable | Questionable | YES |

**8/8 exact agreement.** The NFL.com page itself carried no visible
"report generated at"/timestamp marker (confirming Worker 1's earlier
finding) — this cross-check is a designation-agreement spot-check only, not
a latency measurement.

A real, notable side-finding surfaced by this check, not an error: Tua
Tagovailoa appears under team `ATL` in BOTH nflverse's file and NWR's own
governed canonical pool
(`GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv`, `player_id 00-0036212`).
A live `WebSearch` independently confirmed this is real and correct for
the current (2026) season — Tagovailoa was released by Miami after the
2025 season and signed with, and was named Week 1 starter for, the Atlanta
Falcons. Not a data-quality bug; flagged here only because it looked like
one at first glance and is exactly the kind of claim this cross-check
exists to verify rather than assume.

### Pro-Football-Reference / Sports-Reference rights — RESOLVED (also restricted)

Worker 1's `data_use.html` fetch returned HTTP 403 and was left
unverified. This pass tried a different approach per the directive
(search first, then a direct fetch of a different static page on the same
domain) rather than re-hitting the same blocked path:

- A `WebSearch` (not subject to the site's own bot-blocking) surfaced and
  quoted the site's own real, indexed terms language: *"Without express
  written permission, you may not use any automated means to access or use
  the Site, including scripts, bots, scrapers, data miners, or similar
  software..."* and *"You should not create websites or tools based on
  data you scrape from Sports Reference or any of their sites... without
  their permission."*
- A direct `WebFetch` retry against `https://www.sports-reference.com/data_use.html`
  AND a second, different page on the same domain
  (`https://www.sports-reference.com/termsofuse.html`) both returned real
  HTTP 403 to this pass's fetch tool as well — independently confirming
  Worker 1's finding, not a fluke of one path.

**Conclusion: Pro-Football-Reference / Sports-Reference is NOT a
lower-friction alternative to NFL.com.** It carries the same kind of
explicit anti-scraping restriction. This closes Worker 1's open item —
nflverse (no restrictive terms found) plus a small, disclosed, manual
NFL.com spot-check remains the correct approach, not a bigger PFR-based
pull.

---

## Benchmark coverage

- **Source file**: `injuries_2026.csv`, real fresh pull this pass
  (`fetched_at_utc` `2026-09-14T03:03:53Z`), 182 rows.
- **Season/week**: 2026, Week 1 (REG) — the only week that exists yet this
  season; nflverse has not published a Week 2 file at the time of this
  pass.
- **Teams**: all 32 NFL teams represented (verified: `distinctTeams: 32`
  in `official_truth_benchmark_v1/manifest.json`).
- **Rows**: 182 total. `reportStatusCategory`: OUT 31, QUESTIONABLE 24,
  DOUBTFUL 6, CLEARED_OR_NOT_LISTED 121 (players who appear on the report
  for practice-participation reasons but carry no game-status designation
  — an honest, disclosed real shape of the file, not a gap). `practice
  StatusCategory`: FULL 96, LIMITED 50, DNP 36.
- **Normalized fields** (see `nflverse_week1_2026_official_truth_benchmark.csv`,
  182 rows, committed): `playerId` (gsis_id, canonical scheme),
  `playerName`, `position`, `team`, `season`, `week`, `reportStatusRaw` +
  `reportStatusCategory` (normalized OUT/DOUBTFUL/QUESTIONABLE/
  CLEARED_OR_NOT_LISTED), `practiceStatusRaw` + `practiceStatusCategory`
  (normalized FULL/LIMITED/DNP/NONE_RECORDED), the four raw injury-location
  text fields, `source`/`sourceUrl`/`fetchedAtUtc`/`sourceAsOf`
  (provenance, matching Gate 1's shape), and `matchedCanonicalPlayerId` +
  `identityMatchMethod` (this row's own identity-mapping result — see
  `IDENTITY_MAPPING_V1.md` for the full classification; joined here via
  the exact same resolver, not a second join).

### Real, disclosed limitation: no Wednesday/Thursday/Friday per-day rows

The directive asked this pass to "aim for Wednesday/Thursday/Friday
practice-report-shaped data." The real, inspected file structure does
**not** support that: `injuries_2026.csv` carries exactly ONE row per
player per week — a single `practice_status` value, not three separate
per-day columns or three separate per-day rows. Worker 1 already found (and
this pass independently re-confirmed by re-pulling, see below) that the
file **revises itself in place** across the week rather than appending a
new dated row each day. There is no `date`/`day_of_week` column in the
file at all.

Given that real structural constraint, this benchmark represents the file
**at the granularity nflverse actually publishes it** — a single
end-of-week state per player — and treats successive pulls (diffed) as the
only available proxy for "which day's state is this." This pass performed
exactly that: it preserved Worker 1's original 2026-09-13 pull
(`local_exports/.../nflverse_injuries/wu1_snapshot_20260913/`, gitignored
raw copy) and re-fetched fresh (~11 minutes later,
`fetched_at_utc` `02:52:46Z` → `03:03:53Z`). Result: **0 rows changed**
between the two pulls (`official_truth_benchmark_v1/manifest.json`,
`revisionEvidence.rowsChangedBetweenPulls: 0`) — real, first-hand evidence
that, as of this pass, the file had already reached its Friday-final state
for Week 1 (consistent with `operations.nfl.com`'s documented "final
designation due no later than 4:00 PM" policy Worker 1 already found, and
consistent with Week 1 games already underway). This is real evidence of
freshness/stability at THIS point in the week, not proof the file never
revises — Worker 1's own two-day-apart diff already proved it does revise
earlier in a week (Out 27→31 between 2026-09-11 and 2026-09-13).

**Net effect on Gate 5 measurability**: this benchmark can support a
before/after revision comparison (as demonstrated) but cannot, on its own,
pin an exact "official publication timestamp" for a Wed/Thu/Fri practice
report, because the file itself carries no such timestamp — only a
season/week label (`sourceAsOf`). A future pass wanting Gate 5's precise
2-hour ordinary-context P95 would need either (a) a source with an actual
per-update timestamp, or (b) NWR's own repeated-pull cadence (fetch every
N hours, log each pull's own `fetched_at_utc`, and treat "value changed
since last poll" as the closest obtainable proxy for "official update
happened sometime in this poll window") — not implemented this pass,
flagged for the next worker.

---

## Benchmark independence caveat (honest disclosure)

**This benchmark is NOT fully independent of nflverse.** 182 of 182
primary benchmark rows come from nflverse's own file. The only genuinely
independent corroboration is the 8-player NFL.com manual spot-check above
(8/8 agreement) — a real, first-hand, non-automated cross-check, but a
small sample, not a second full dataset. This matches exactly what the
directive anticipated and explicitly permitted ("If this still feels
rights-ambiguous, skip it and rely on nflverse alone, clearly disclosing
that the benchmark is therefore not fully independent of nflverse") and
what Worker 1's own research concluded (nflverse's injuries file is itself
very likely republishing the same official club-reporting process NFL.com
displays, just without NFL.com's restrictive ToS attached) — this pass's
8/8 agreement result is consistent with, though does not by itself prove,
that conclusion.

**What this means for Gate 3 (official factual agreement)**: Gate 3 asks
for ≥99% exact agreement "against official NFL reports on the held-out
test sample built by the official-NFL-truth-benchmark work." Because this
benchmark IS substantially nflverse itself, measuring a candidate source
(e.g. Sleeper) against THIS benchmark measures agreement with nflverse, not
with a fully independent official record. The 8/8 NFL.com spot-check is
real, positive evidence that nflverse tracks the actual official
designations closely for the sampled players, which is the best evidence
available under the rights constraint — but a future worker should not
describe a future Gate-3 pass run against this benchmark as measuring
"independent official truth" without repeating this caveat.

---

## Gate mapping (directional only — this pass does not itself decide a gate PASS/FAIL)

- **Gate 1 (Provenance)**: every benchmark row carries `source`,
  `sourceUrl`, `fetchedAtUtc`, and `sourceAsOf` (a week-granularity
  proxy for source timestamp, explicitly labeled as such rather than
  substituted with `fetchedAtUtc`) — satisfies the per-field shape Gate 1
  requires, at the granularity this source actually offers.
- **Gate 3 (Official factual agreement)**: not computed as a percentage by
  this pass (that is explicitly the next work unit's job per the
  admission contract's own scope note) — but the raw material now exists,
  plus the 8/8 NFL.com spot-check as directional supporting evidence.
- **Gate 5 (Freshness)**: not precisely measurable from this file alone
  (see the Wed/Thu/Fri limitation above) — the 0-rows-changed /
  27→31-rows-changed two data points are the only real freshness evidence
  available from this source shape.
- **Gates 2, 4, 6-10**: out of scope for this doc — see
  `IDENTITY_MAPPING_V1.md` for Gate 2, and `LEDGER.md` for what remains
  open for later work units.
