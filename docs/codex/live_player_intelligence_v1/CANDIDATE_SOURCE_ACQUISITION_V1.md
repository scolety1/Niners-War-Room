# NWR Live Player Intelligence — Candidate Source Acquisition V1

Work Unit 1, branch `upgrade/nwr-live-player-intelligence-v1-20260913`,
worktree `C:\NWR\live-player-intelligence-v1`. Research + read-only source
characterization only — no promotion, no production wiring, no purchase,
no signup. Evaluated against the gates preregistered in
`LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md` (committed before this
doc's measurement began). Real fetches performed 2026-09-13 (UTC
timestamps land 2026-09-14 early morning per `fetched_at_utc`). Raw
artifacts are stored at
`local_exports/live_player_intelligence_shadow_v1/{nflverse_injuries,
nflverse_depth_charts,sleeper_players}/latest/` (gitignored, outside
production code) — see the Raw Artifacts section at the end.

This doc extends, and does not duplicate, the prior session's
`docs/codex/post_ui_v1/NWR_PLAYER_INTELLIGENCE_PROVIDER_BAKEOFF_V1.md`
(2026-09-12), which already researched RotoWire/SportsDataIO/Sportradar/
FantasyData/FantasyPros/ESPN-unofficial and admitted nflverse-injuries +
Sleeper as shadow-only. Those provider verdicts are not re-litigated here
except where this pass's fresh (2026-09-13) pull changed a number enough
to matter. New this pass: (C) nflverse depth charts, and (D) official
NFL.com / league-published injury report characterization for the
Work Unit 2 benchmark worker.

---

## (A) Sleeper `players/nfl` catalog — RE-VERIFIED, current state

Same endpoint, same schema as the prior bakeoff. Real fresh pull this
pass (2026-09-13, `fetched_at_utc` 2026-09-14T02:52:46Z): 12,227 players,
14,656,478 bytes.

- **Field coverage:** `status` (roster-level: Active/Inactive/Injured
  Reserve/Physically Unable to Perform/Practice Squad/Non Football
  Injury/null), `injury_status` (Questionable/IR/Out/NA/PUP/Sus/COV/DNR),
  `depth_chart_position`/`depth_chart_order`, `team`, crosswalk ids
  (`gsis_id`, `espn_id`, `rotowire_id`, `sportradar_id`, etc.),
  `news_updated` (epoch-ms). `practice_participation` remains real but
  essentially unpopulated: **1 non-null value out of 12,227** in this
  pass's own fresh pull (unchanged from the prior pass's finding) — still
  not usable as a practice-participation source.
- **Retrieval timestamp granularity:** whole-catalog snapshot; this
  pass's own `fetched_at_utc` is second-precision. No per-record
  retrieval timestamp — only `news_updated` is per-player.
- **Source timestamp granularity:** `news_updated` epoch-ms, but only
  populated for players with recent news; most rows carry no source
  timestamp at all (an honest per-field gap, matching Gate 1's per-field
  scoping).
- **Identity scheme:** own `player_id`; direct `gsis_id` field present on
  3,893/12,227 catalog rows (up from a much smaller subset the prior pass
  reported for the *matched* subset specifically — direct comparison
  requires the same canonical-pool lens, see coverage below).
- **Rights:** RE-CONFIRMED unchanged — Sleeper's own docs
  (https://docs.sleeper.com/) state the API is "free to use for
  non-commercial purposes... For commercial use of the Sleeper API,
  please reach out to us directly to discuss licensing." NWR remains a
  personal, non-distributed desktop app today; this stands but must be
  re-checked before any commercial distribution. `players/nfl`
  specifically is "intended only to be used once per day at most... save
  this information on your own servers" — this pass's fetch used the
  existing `scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`,
  which enforces that 24h floor for real.
- **Historical access:** none — current snapshot only (unchanged finding).
- **Freshness:** `news_updated` genuinely current where populated;
  whole-catalog cadence is bounded by NWR's own 24h re-fetch floor, not
  by how often Sleeper itself updates upstream (unverified independently
  of NWR's own cache policy).
- **Missingness:** `practice_participation` effectively 100% missing;
  `gsis_id` populated for 3,893/12,227 whole-catalog rows.
- **Revision behavior:** not directly observable in a single pull; the
  field-level distribution shift versus the prior pass (below) is
  consistent with Sleeper updating designations as the week progresses,
  not with the file silently correcting past errors.

**Coverage against the real 564-player Freeze V7 canonical pool** (this
pass's own run of the existing `build_coverage_report`):
distinct canonical players matched with an actionable status signal:
**102/564 = 18.09%** (up from the prior pass's 12.4%, expected — this
pull is closer to Week 1 kickoff, so more players carry a real flagged
status). Match-method breakdown: `GSIS_DIRECT` 18, `NAME_POSITION_TEAM`
84, `UNMATCHED_NO_TEAM` 3,728 (mostly retired/practice-squad/irrelevant
catalog noise, not real misses), `UNMATCHED` 405.

**Real field-value delta versus the prior (2026-09-12) pull**, itself
useful revision/freshness evidence: `status=Inactive` 3,581→3,582,
`injury_status=Out` 52→191 (real, large increase — expected as teams
finalize Week 1 designations), `injury_status=Doubtful` 5→0 (real
churn — Doubtful designations resolved to Out/Questionable/cleared as
the week advanced), `injury_status=Questionable` 284→291. This is real,
directly-observed evidence that the catalog reflects genuine in-week
status movement, not a static snapshot re-served.

---

## (B) nflverse official weekly injury report — RE-VERIFIED, current state

Same source as the prior bakeoff
(`github.com/nflverse/nflverse-data/releases/download/injuries/
injuries_2026.csv`). Real fresh pull this pass: 182 rows, 20,631 bytes,
`gsis_id` populated 182/182 (unchanged: 100%).

- **Field coverage:** unchanged — `report_status` (Out/Questionable/
  Doubtful/blank), `practice_status` (Full/Limited/DNP), plus
  `report_primary_injury`/`report_secondary_injury`/
  `practice_primary_injury`/`practice_secondary_injury`, `team`,
  `position`, `full_name`.
- **Real revision-behavior finding (new this pass):** the SAME nominal
  file (`injuries_2026.csv`, still 182 rows, still exactly Week 1) now
  reports a materially different `report_status` distribution than the
  prior pass's pull two days earlier: Out 27→31, Questionable 26→24,
  Doubtful 6→6 (unchanged), blank 123→121. This is real, concrete,
  first-hand evidence that this file **does revise itself in place**
  after initial publication (teams update designations Wed→Thu→Fri, and
  the published file tracks the latest state rather than freezing at
  first publication) — directly relevant to Gate 5 (freshness) and the
  "revision behavior" characterization the directive asked for. There is
  no version/changelog column in the file itself; a revision is only
  detectable by diffing successive pulls, exactly as this pass just did.
- **Coverage of the real 564-player canonical pool** (re-run this pass):
  unchanged, **52/564 = 9.22%** distinct canonical players matched, all
  52 via `GSIS_DIRECT`, and all 52 carry a populated `practice_status`
  (100% when present, matching the prior finding).
- **Identity scheme:** `gsis_id`, identical to NWR's own canonical id —
  direct match, no fuzzy join.
- **Historical access:** unchanged — real, free, back to 2009.
- **Rights:** unchanged — no restrictive license/ToS found for
  nflverse-data releases; same posture this repo already relies on
  elsewhere.
- **Missingness:** by design, only lists players who are actually on that
  week's report (52/564 this week) — not a broad-coverage source, a
  narrow high-confidence one.
- **Freshness:** file already carries real Week 1 rows; the in-place
  revision found above shows real sub-week update cadence, but there is
  no intra-week timestamp column to measure exact latency against
  official publication — Gate 5's precise P95 cannot be computed from
  this file alone (a real, disclosed limitation; the Work Unit 2 official
  benchmark will need its own publication timestamps to measure this).

---

## (C) nflverse depth charts — NEW, characterized for the first time this pass

`github.com/nflverse/nflverse-data`, release tag `depth_charts`
(`nflreadr::load_depth_charts()` upstream, but this repo fetches the raw
CSV release asset directly, matching the injuries-fetch convention).
**Real, disclosed schema-drift finding**: the published data dictionary
(`nflreadr.nflverse.com/reference/load_depth_charts.html`) describes an
older, Sportradar-shaped schema (`season, week, game_type, depth_team,
formation, elias_id, depth_position, ...`, seasonal cadence back to
2001). The REAL, currently-live file at the direct download URL
(`.../releases/download/depth_charts/depth_charts_2026.csv`, real fetch
this pass, 49,097,593 bytes) has a **different, ESPN-sourced schema**:
`dt, team, player_name, espn_id, gsis_id, pos_grp_id, pos_grp, pos_id,
pos_name, pos_abb, pos_slot, pos_rank` — no `season`/`week`/`formation`/
`depth_position` columns at all in the real file. This mirrors the same
kind of documentation-vs-reality drift the prior bakeoff already found in
the injuries file's `date_modified` column — a real, repeat pattern
worth flagging generally about nflverse's public docs lagging the actual
release assets, not a defect in this pass's method.

**Real, live-verified findings (this pass's own fetch/inspection):**
- **`dt` is a real, per-snapshot ISO-8601 UTC datetime** (e.g.
  `2026-09-13T12:42:08Z`), NOT a season/week label. 177 distinct `dt`
  snapshots span 2026-03-22 through 2026-09-13 in this one file — a
  genuinely near-daily cadence (the last 10 distinct `dt` values are 10
  consecutive calendar days, one snapshot per day), confirming this is a
  real rolling-snapshot feed, not a seasonal dump. This is real
  timestamp granularity meaningfully finer than the injuries file's
  season/week-only `source_as_of`.
- **Coverage is broad, not narrow**: the latest single-day snapshot
  (`dt=2026-09-13T12:42:08Z`) has 2,222 rows across all 32 teams (~69
  rows/team — full-depth-chart, not just starters). `gsis_id` populated
  2,217/2,222 (99.8%) in that snapshot; `espn_id` populated 2,222/2,222
  (100%).
- **Coverage of the real 564-player canonical pool** (this pass's own
  computation, direct `gsis_id` set-membership against the latest
  snapshot): **499/564 = 88.5%** — by far the broadest of the three
  nflverse-family sources examined, because a depth chart lists every
  rostered player at every position group, not only injured/flagged ones.
- **Fields present:** team, position-group role (`pos_grp`, e.g. "3WR
  1TE", "Base 3-4 D", "Special Teams"), specific role name (`pos_name`,
  e.g. "Wide Receiver", "Left Tackle", "Quarterback"), and **ordinal
  depth rank** (`pos_rank`: 1=starter/first-string, 2=backup, etc. —
  875 rows at rank 1, 700 at rank 2, tapering to 2 at rank 9 in the
  latest snapshot). This is a genuine starter/role signal NWR does not
  currently have from any other admitted source — neither the injury
  report nor Sleeper's `depth_chart_order` field (which this pass did
  not independently cross-check against this file in the time available
  — flagged as an open item below) carries an explicit starter-rank like
  this.
- **No explicit injury/availability field** — this source characterizes
  ROLE/depth, not health status. It is a different kind of signal than
  (A) and (B), not a competing coverage number for the same field.
- **Player/team identity scheme:** `gsis_id` (same scheme as NWR's
  canonical id — direct match) plus `espn_id`; no fuzzy name matching
  needed given the high direct-id population rate.
- **Historical access:** real — this single release-asset file already
  spans back to 2026-03-22 (pre-season) in this one pull; the release's
  111 total assets (per the GitHub releases page, not individually
  enumerated this pass) suggest per-season files exist further back,
  consistent with nflverse's general historical-archival posture, but
  this pass did not fetch a prior-season file to confirm — flagged as an
  open item below.
- **Rights:** same nflverse-data family, same posture already
  established and relied on elsewhere in this repo — no restrictive
  license or ToS found. Not separately re-verified this pass beyond
  confirming the fetch succeeded with no auth/key required (same GitHub
  release-asset mechanism as the injuries file).
- **SLA:** none — same real, disclosed risk as every other nflverse
  source (volunteer open-source project, no uptime/support guarantee).
- **Missingness:** 5/2,222 rows (0.2%) in the latest snapshot lack a
  `gsis_id`.
- **Revision behavior:** each `dt` is its own immutable daily snapshot
  appended to the same file (177 snapshots present) rather than a single
  row being edited in place — a materially different revision model than
  the injuries file's in-place update found in (B) above. A future
  consumer wanting "yesterday's depth chart" vs. "today's" can do so by
  filtering on `dt` directly from this one file, without needing
  separate historical fetches.
- **A file this large (49MB) as a single CSV** is a real practical
  consideration for a future production fetch script: filtering to only
  the latest `dt` (or the last N days) before writing/parsing would be
  the sane approach rather than loading the whole 516,349-row history
  every time — noted for whoever eventually builds a real fetch
  path, not implemented here (this pass's fetch was a one-time
  characterization pull, written to the gitignored research location
  exactly like the other two sources).

---

## (D) Official NFL / league-published injury reports — characterized as the Work Unit 2 benchmark candidate (NOT built this pass)

Real, current (2026-09-13) research against `nfl.com` directly (the
directive's named example), not a re-litigation of the paid syndication
vendors already researched in the prior bakeoff (RotoWire/SportsDataIO/
Sportradar all ultimately resell/aggregate official injury-report data
under a paid contract).

- **What exists, confirmed live:** `https://www.nfl.com/injuries/`
  (current-week landing page) and season/week-addressable URLs
  (`https://www.nfl.com/injuries/league/2026/reg1`, confirmed live and
  indexed for the real 2026 Week 1). Also real, current NFL.com news
  articles summarizing weekly injury/inactive reports in prose form
  (e.g. "NFL Week 1 injury report: Player statuses for all 16 games").
- **Field coverage on the actual page** (real fetch + structural read
  this pass): organized by game/matchup, each player row shows name,
  position, injury body part, practice status (Full/Limited/Did Not
  Participate — same three-state vocabulary as nflverse's `practice_
  status`), and game-status designation (Out/Questionable/Doubtful/blank
  for full clearance) — i.e., the same conceptual fields nflverse's
  injuries file already carries, which makes sense: nflverse's own file
  is itself sourced from this same official reporting process. The page
  reads as static server-rendered HTML with no obvious JS-only data
  gating, and **no visible "report generated at" timestamp** on the page
  itself — a real, disclosed gap for anyone trying to measure Gate 5's
  precise publication-to-availability latency from the page alone.
- **Official reporting cadence (from `operations.nfl.com`'s own,
  publicly posted injury-report policy):** clubs must report player
  injury status on a fixed weekly schedule (Wednesday/Thursday/Friday
  practice reports during the regular season), with a **final game
  status designation due no later than 4:00 PM** on the last reporting
  day before the game, and specific-enough injury-location language
  (e.g. "knee," not "leg") is mandated by policy. This is a real,
  official, publicly documented cadence useful for the Work Unit 2
  benchmark worker to know the EXPECTED publication schedule against
  which to measure any candidate source's freshness.
- **`robots.txt` (real, fetched this pass):** does not explicitly
  disallow `/injuries` or `/news` paths — technically crawlable by the
  letter of `robots.txt` alone.
- **RIGHTS — the real, material finding for Work Unit 2, quoted
  verbatim from NFL.com's own live Terms and Conditions
  (`https://www.nfl.com/legal/subscriptions_terms`, fetched this pass):**
  - Section 1(d): "The Products and any content accessed through the
    Products are for your personal, non-commercial use only and may not
    be shared with anyone outside of your household."
  - Section 14(d): "You agree that you will not attempt to, or assist
    any third party in attempting to, bypass any robot exclusion
    headers or other measures we take to restrict access to the
    Products..., or use any software, technology, or device to send
    content or messages, **scrape, spider or crawl** the Products..., or
    **harvest or manipulate data** on or from the Products..."
  - A related public-search finding (not independently re-verified by
    directly quoting the exact clause text a second time, flagged as
    such): systematic retrieval of data to build a compiled
    collection/database is separately prohibited without NFL.com's
    express prior written consent.
  - **Net rights finding: NFL.com's own ToS explicitly and unambiguously
    prohibits automated scraping/crawling/harvesting, REGARDLESS of
    `robots.txt`'s technical permissiveness and regardless of personal/
    non-commercial intent.** This is a hard Gate 9 blocker for treating
    NFL.com itself as an automated-fetch production source — the ToS
    conflict is with the ACT of automated scraping, not with the
    commercial/non-commercial status of the user. A one-time,
    small-sample, human-reviewed research pull (of the kind this pass
    performed via `WebFetch` to characterize the page, not to build a
    stored dataset) sits in a materially different, much lower-risk
    posture than a recurring automated production ingestion pipeline
    would — but building the latter against NFL.com directly would
    knowingly violate the site's own stated terms and should not be
    done without the owner explicitly accepting that risk or securing
    real written permission.
- **A real, disclosed adjacent finding, not deep-dived (time-boxed,
  flagged for the next worker rather than fully chased):** searching for
  a lower-friction "official-adjacent" mirror turned up
  Sports-Reference/Pro-Football-Reference's own data-use terms page
  (`sports-reference.com/data_use.html`), but that URL returned an HTTP
  403 to this pass's fetch tool and was not independently verified — its
  actual terms are unknown to this pass, not assumed favorable or
  unfavorable. This is the single clearest lead for the Work Unit 2
  worker to check first if NFL.com's ToS makes it the wrong integration
  target: Pro-Football-Reference is a well-known third-party mirror of
  official NFL data (not itself "official," but potentially a friendlier
  terms posture) and was not eliminated by this pass, only left
  unverified.
- **Conclusion for Work Unit 2:** NFL.com is real, live, structurally
  fetchable, and its field vocabulary already matches what nflverse's
  injuries file (already admitted, already free, already ToS-clean)
  exposes — meaning nflverse is very likely ALREADY effectively
  republishing this same official process, just without NFL.com's
  restrictive ToS attached. The most defensible path for building an
  independent Gate-3 benchmark is almost certainly NOT a recurring
  automated NFL.com scrape (ToS-prohibited), but either (a) a bounded,
  human-reviewed, one-time-per-sample-window manual cross-check against
  the live NFL.com page (analogous to how this pass itself read the
  page, not a stored automated pipeline), or (b) locating a source with
  cleaner redistribution terms that still traces back to the same
  official reporting process (Pro-Football-Reference unverified per
  above, or a paid vendor from the prior bakeoff that has already done
  the licensing work). This is a decision for Work Unit 2 to make
  explicitly, not implied or pre-decided by this pass.

---

## Cross-source observations

- **Complementary, not redundant coverage**: nflverse injuries (9.2% of
  canonical pool, narrow/high-confidence, injury-specific), Sleeper
  (18.1% actionable-signal coverage, broader roster-status/IR/PUP/
  Suspended net), nflverse depth charts (88.5% of canonical pool, broad
  role/starter-rank coverage but no injury field at all). None of the
  three alone would satisfy Gate 4's 95% coverage-of-official-report
  target on its own for injury-specific fields; depth charts materially
  help overall PLAYER coverage (role/team/starter-status) but do not
  substitute for an injury signal.
- **Both in-place-revision (nflverse injuries) and append-only-snapshot
  (nflverse depth charts) revision models exist within the same
  nflverse-data GitHub org** — a future production fetch script cannot
  assume one revision model applies to every nflverse file; each file
  needs its own diffing/versioning strategy if NWR ever wants to detect
  a correction after the fact (Gate-adjacent design note, not itself a
  gate).
- **None of the three admitted/characterized free sources (A/B/C)
  requires a key or contract** — consistent with the prior bakeoff's
  finding that no paid provider researched (RotoWire/SportsDataIO/
  Sportradar/FantasyData/FantasyPros) has a genuinely free, current-
  season, self-serve tier suitable for this use case.

---

## Raw artifacts location

`local_exports/live_player_intelligence_shadow_v1/` (repo-root-relative,
gitignored via the existing repo-wide `local_exports/` rule — confirmed
via `.gitignore`, not committed):
- `nflverse_injuries/latest/injuries_2026.csv` (20,631 bytes, 182 rows,
  fetched 2026-09-13) + `manifest_2026.json`
- `nflverse_depth_charts/latest/depth_charts_2026.csv` (49,097,593 bytes,
  516,349 rows spanning 177 daily snapshots, fetched 2026-09-13) +
  `manifest_2026.json`
- `sleeper_players/latest/sleeper_players_snapshot.json` (14,656,478
  bytes, 12,227 players, fetched 2026-09-13) + `fetch_log.json`

All three were fetched using the existing
`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py` (nflverse
injuries + Sleeper, unchanged from the prior pass) plus a small ad-hoc,
non-committed research script for the new depth-charts pull (same
User-Agent/no-auth/read-only pattern as the existing script; not added
to the repo as a permanent script this pass — if a future pass wants a
depth-charts fetch made permanent, it should be added to the existing
`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py` rather
than a new standalone file, to keep one fetch entrypoint). No file in
`src/` or `scripts/` was modified or added by this pass beyond what
already existed at Start HEAD.

## Open items for the next worker (explicit, see also LEDGER.md)

1. Sleeper's own `depth_chart_position`/`depth_chart_order` fields were
   NOT cross-checked against the new nflverse depth-chart `pos_rank`
   finding in this pass (time-boxed) — worth reconciling before any
   future promotion design assumes they agree.
2. nflverse depth charts' historical range beyond this pull's own
   2026-03-22 start was not confirmed (111 total GitHub release assets
   were seen but not individually enumerated).
3. Pro-Football-Reference's data-use terms returned HTTP 403 to this
   pass's fetch tool and remain unverified — the clearest lead for a
   lower-friction Gate-3-benchmark-adjacent source if NFL.com direct
   scraping is ruled out.
4. Gate 3's ≥99% exact-agreement figure and Gate 5's precise P95
   freshness figures cannot be computed until Work Unit 2 actually
   builds the official-NFL-truth benchmark this pass only characterized
   the raw material for.
