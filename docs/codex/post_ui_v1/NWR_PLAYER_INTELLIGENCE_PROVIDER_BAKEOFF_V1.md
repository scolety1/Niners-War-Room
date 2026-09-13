# NWR Live Player Intelligence Provider Bakeoff V1 (P1-5)

Worker 9, NWR Post-UI Product V1 shift, branch
`upgrade/nwr-post-ui-product-v1-20260912`. Research + shadow ingestion only.
**No purchase, API-key signup, or paid contract was made.** No recommendation
logic, scoring, roster legality, `LeagueSnapshot`/`LeagueWorkspaceContext`/
the lifecycle resolver/`DecisionResultEnvelope` was touched.
`PlayerAvailabilityStatus`'s actual authority semantics (in
`src/services/player_availability_status_service.py`) were read, never
modified.

Every number in this doc below was produced by a REAL run: real live web
searches/fetches against provider sites (2026-09-12), a real HTTP fetch of
the real, live Sleeper `players/nfl` catalog (14,651,313 bytes, 12,227
players), a real HTTP fetch of the real, live nflverse `injuries_2026.csv`
(182 real Week 1 rows), and the real shipped shadow-ingestion code in this
commit run against this worktree's real 564-player governed canonical pool
(`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv`) and the real 3-entry manual
override file (`config/nwr_verified_current_player_status_overrides_v1.json`).
No number here is estimated or carried over unverified from an old doc.

## What NWR already has (the contract being shadowed, not replaced)

`PlayerAvailabilityStatus` (`player_availability_status_service.py`) is an
honest WRAPPER around `current_player_status_overrides_service.py`'s manual,
individually-sourced, cited override file -- **not a live feed**. Its own
docstring already discloses: "there is no live/automated in-season
injury-news ingestion system anywhere in this codebase." Every `injury`-named
module elsewhere in `src/services` (`injury_availability_context_service.py`,
`rotowire_local_team_status_service.py`, etc.) reads a STATIC, historical,
offline CSV snapshot used for model-training/backtest context -- none is a
live feed either. Today (2026-09-12) there are exactly **3 real overrides on
file**: Jayden Higgins (`SEASON_OUT`, ACL), Elijah Mitchell
(`NOT_WITH_TEAM`), Kayshon Boutte (`TEAM_CORRECTION` to HOU) -- each
individually cited to real, named, dated sources by a human.

## Providers researched

### RotoWire (syndication) -- verdict: NEEDS_OWNER_CONTRACT

Real findings from `rotowire.com`, `rotowire.readme.io` (RotoWire's own data
dictionary), and OpticOdds' RotoWire distribution page
(`developer.opticodds.com/docs/rotowire-news-injury-data`, a real current
RotoWire reseller):

- **Injury coverage:** real `InjuryStatus` codes `OUT, GTD, Q, D, IR, IR-R,
  PUP, SUSP, DNP, NA, ACT` -- covers injury designation, IR/PUP, suspension
  in one field.
- **Injury detail:** body location, type, detail (strain/sprain/fracture/
  surgery/etc.), side, `ReturnDate` (frequently null -- honest, matches how
  real injury timelines actually work).
- **Practice participation:** NOT explicitly documented in the public data
  dictionary I could reach -- a real, disclosed gap in what I could verify
  (RotoWire's site claims "GTD -> OUT transitions as they happen," implying
  some practice-report tracking exists internally, but the field-level
  schema for it was not visible in public docs).
- **Timestamps:** `updatedAt`, ISO 8601. OpticOdds separately states
  "updates occurring every few minutes on game day" for injuries and
  "60-90 minutes before events" for confirmed lineups -- real, disclosed
  freshness claims from the distributor, not independently verified live
  (no key was obtained).
- **Player ID scheme:** not disclosed in any public page I could reach.
  Notably, **Sleeper's own public catalog already carries a `rotowire_id`
  field for 830/847 real fantasy-relevant rostered skill-position players
  in this worktree's live pull (98.0%)** -- if RotoWire access is ever
  purchased, that crosswalk is already sitting in a free source and would
  make identity resolution close to trivial.
- **Redistribution/UI rights, historical access, rate limits, SLA:** NOT
  disclosed anywhere self-serve. **RotoWire has no self-serve API signup or
  published pricing.** OpticOdds' own docs say it plainly: "Your OpticOdds
  API Key will not work with RotoWire. Please contact your OpticOdds sales
  representative if you're interested in adding RotoWire data to your
  package." RotoWire's own syndication rate card
  (`rotowire.com/ratecard/syndicatedcontent.htm`, redirects to
  `rotosportsinc.com/syndication.html`) is a sales-contact page, not a
  self-serve price list.
- **Cost:** unknown/undisclosed. Requires a sales conversation with RotoWire
  or a reseller (OpticOdds, SportsStack) to get a real quote.

**Verdict: NEEDS_OWNER_CONTRACT.** Best-in-class field coverage on paper
(the only researched provider whose public docs show a single field
covering OUT/GTD/Q/D/IR/PUP/SUSP together), but there is no legitimate way
to integrate this without the owner personally initiating a sales
conversation and agreeing to a real contract/price. Not attempted.

### SportsDataIO -- verdict: NEEDS_OWNER_CONTRACT (self-serve tier exists but is rate/latency-limited and still a paid signup)

Real findings from `sportsdata.io/developers`, `discoverylab.sportsdata.io`,
and third-party pricing aggregators (Vendr, APIs.io) since SportsDataIO's
own pricing page is client-rendered and did not return literal dollar
figures to a page fetch:

- **Coverage claimed:** live injuries, lineups, depth charts, player news,
  projections, standings -- broad, matches this repo's own prior
  `PROJECT_GOLD_PAID_DATA_VALUE_ASSESSMENT.md` finding (SportsDataIO scored
  15/15 on injury quality in that May 2026 review).
- **Access tiers, real (2026):**
  - **Free trial** -- "no credit card required," time-limited, for testing
    endpoints only.
  - **DiscoveryLab (self-serve, "personal-use APIs")** -- real third-party
    pricing sources (Vendr, APIs.io) report **$99-149/month**, with **daily
    call caps and next-day-delayed data** (i.e. NOT real-time/current --
    a real, material limitation for a game-day inactive-list use case).
    SportsDataIO's own DiscoveryLab NFL page states "Get Last Season for
    FREE" -- confirms the genuinely-free tier is HISTORICAL-ONLY, not
    current-season.
  - **Enterprise/commercial** -- real-time data + SLA, requires a sales
    conversation, no public price.
- **Player ID scheme:** SportsDataIO's own `PlayerID`, with documented
  crosswalk fields to other providers per their workflow guide (not
  independently verified against NWR's `gsis_id` in this pass -- flagged
  as "to verify" in the existing May 2026 doc too).
- **Redistribution/desktop-caching rights, SLA:** governed by the
  commercial/Enterprise agreement only; the $99-149/mo self-serve tier is
  explicitly "personal projects and hobby apps," which is a real, relevant
  fit for NWR's actual use case (a personal desktop app), but still a real
  recurring cost requiring a real signup and payment method.
- **Historical access:** yes, real and disclosed (their own selling point).

**Verdict: NEEDS_OWNER_CONTRACT.** A self-serve paid tier exists and would
likely be the cheapest path to a broad, official-feeling API if the owner
wants one -- but it is still $99-149/month of real recurring cost with a
real signup, and the self-serve tier's own real limitation (next-day-delayed
data) makes it weaker than advertised for exactly the "live game-day
inactive" use case this bakeoff cares about. Not signed up for.

### Sportradar -- verdict: NEEDS_OWNER_CONTRACT (enterprise-only, no public pricing found)

Real findings from `developer.sportradar.com` and
`marketplace.sportradar.com`:

- **Coverage:** a real, documented `NFL Weekly Injuries` endpoint
  ("a list of injured players for each team for a given week, including
  practice status"), part of the NFL v7 API.
- **Access model:** "a RESTful B2B API," JSON or XML, API-key auth
  established per account -- **no self-serve signup or public price list
  found anywhere** (the marketplace listing page is client-rendered and
  returned no content to a direct fetch; every third-party summary
  describes it as enterprise/quote-only).
- **Player ID scheme, historical access, rate limits, SLA, redistribution
  rights:** none of these are publicly disclosed -- everything is gated
  behind a sales conversation.

**Verdict: NEEDS_OWNER_CONTRACT.** The least self-serve of the three named
providers; there is nothing to research further without the owner
personally engaging Sportradar's sales team.

### Other providers already flagged in this repo's own prior research (not re-litigated in depth here)

`docs/codex/PROJECT_GOLD_PAID_DATA_VALUE_ASSESSMENT.md` (last reviewed
2026-05-14, a different focus -- route/usage/projection data, not
injury/availability specifically) already scored **FantasyData** (78,
budget-friendly API/CSV, injury quality 8/10) and **FantasyPros**
(55, projection/news context, injury quality 3/10 -- explicitly "not a
core model" source) against the same general provider landscape. Both
remain **NEEDS_OWNER_CONTRACT** for the same reason as the three above: no
verified, current, self-serve free tier suitable for a live availability
feed. Not re-verified line-by-line in this pass (out of this pass's time
budget) -- flagged as a real gap if a future pass wants fresh 2026 pricing
for these two specifically.

**ESPN's unofficial/undocumented API** (a real, widely-used community-
reverse-engineered endpoint set, e.g. `site.api.espn.com/apis/site/v2/...`)
was found in search results and is known to carry injury/news data, but was
**not deep-dived** in this pass: it has no published terms of service, no
stated rate limits, no redistribution rights, and is not disclosed by ESPN
as a public product -- it could change or disappear without notice.
**Verdict: REFERENCE_ONLY at most, not researched further, not admitted.**
A future pass could dig deeper if the two admitted sources below prove
insufficient, but building on an undocumented API with zero stated terms is
a real reliability/legal risk this pass declines to take on without the
owner's explicit sign-off.

## Real, additional free/legitimate sources found (beyond the three named providers) -- ADMIT

The directive's own instruction ("and any other credible lower-cost/free
provider you discover") turned up two genuinely free, keyless, already-in-use-
elsewhere-in-this-exact-repo sources that, together, cover a meaningful slice
of the requested field list with **zero cost and zero contract**:

### nflverse official weekly injury report -- verdict: ADMIT (shadow-only)

`github.com/nflverse/nflverse-data`, release tag `injuries`,
`injuries_<season>.csv` (also available via the R package `nflreadr::
load_injuries()`; this repo is Python-only, so the raw CSV release asset is
fetched directly). This is the SAME nflverse family this repo already
treats as an admissible free source everywhere else (play-by-play, rosters,
snap counts, etc.).

**Real, live-verified findings (fetched 2026-09-12, real Week 1 2026 file,
182 rows):**
- Columns present in the real file: `season, season_type, game_type, team,
  week, gsis_id, position, full_name, first_name, last_name,
  report_primary_injury, report_status, practice_primary_injury,
  practice_secondary_injury, practice_status`. (The published data
  dictionary at `nflreadr.nflverse.com/articles/dictionary_injuries.html`
  also lists a `date_modified` column -- **that column is NOT present in
  this real, live-fetched CSV** -- a real, disclosed schema-drift finding
  between the documentation and the actual current file, not a defect in
  this pass's code.)
- **`gsis_id` is populated on every real row (182/182)** and is the EXACT
  SAME id scheme NWR's own canonical `player_id` uses -- direct
  set-membership matching, no fuzzy join needed, for any player who
  appears on the report.
- **Real official designations found:** `report_status` -- Out (27),
  Questionable (26), Doubtful (6), blank/no designation (123).
- **Real official practice participation found:** `practice_status` --
  Full Participation in Practice (97), Limited Participation in Practice
  (50), Did Not Participate In Practice (35). **This is real, current,
  populated data** -- a genuine practice-report signal, which is exactly
  the field NWR's own manual-override authority does not track at all.
- **Coverage of NWR's real 564-player canonical pool (Week 1 2026, run
  through this pass's actual shipped code):** 52/564 = **9.2%** distinct
  canonical players matched. This is EXPECTED to be small, not a weakness:
  the injury report only ever lists players who are actually on that
  week's report -- most of a 564-player pool is healthy in any given week.
  Of the 52 matched, **100% carry a real, populated `practice_status`**
  (52/52) -- when this source has a player at all, its practice-
  participation signal is real and complete, not sparse.
- **Update cadence:** the file already contains real Week 1 2026 rows
  ahead of the season's first games (fetched 2026-09-12) -- confirms this
  is genuinely updated in-season on a rolling basis, not a season-end-only
  historical dump.
- **Historical access:** real and free back to 2009 per the package
  documentation.
- **Terms/redistribution/desktop-caching rights:** no restrictive license
  or ToS found for nflverse-data releases (the same public-domain-style
  posture this repo already relies on for every other nflverse dataset it
  uses); no rate limit documented for GitHub release asset downloads.
- **SLA:** none -- a volunteer open-source project, not a commercial
  product. Real, disclosed risk: no uptime/accuracy guarantee, no support
  contract, could change format or disappear (mitigated in practice by
  this being the same infrastructure this repo already depends on
  elsewhere for training data).

### Sleeper public `players/nfl` catalog -- verdict: ADMIT (shadow-only, with a real commercial-use caveat)

`api.sleeper.app/v1/players/nfl` -- the SAME free, keyless endpoint this
exact repo already calls elsewhere (`scripts/backfill_active_pack_public_
veteran_model.py`, `scripts/build_model_v4_sleeper_age_supplement.py`) and
the same provider NWR already uses live for real Sleeper-linked leagues via
`SleeperHttpClient` (read-only, GET-only, structurally cannot write).

**Real, live-verified findings (fetched 2026-09-12, real catalog, 12,227
total players, 14,651,313 bytes -- larger than the ~5MB the docs describe,
a real, disclosed size-growth finding):**
- Real fields present on every player object: `player_id, first_name,
  last_name, full_name, position, fantasy_positions, team, team_abbr,
  team_changed_at, number, status, injury_status, injury_start_date,
  injury_body_part, injury_notes, practice_participation,
  practice_description, depth_chart_position, depth_chart_order, age,
  years_exp, college, birth_date/city/state/country, news_updated`, plus
  crosswalk id fields: `gsis_id, espn_id, yahoo_id, rotowire_id,
  rotoworld_id, sportradar_id, fantasy_data_id, oddsjam_id, opta_id,
  stats_id, pandascore_id, kalshi_id, swish_id`.
- **Real `status` distribution (whole catalog):** Active (8,369), Inactive
  (3,581), Injured Reserve (227), Physically Unable to Perform (3),
  Practice Squad (1), Non Football Injury (1), null (45) -- covers roster-
  level IR/PUP/NFI/Inactive states, though PUP/NFI counts are tiny (real,
  likely under-populated for those specific tags rather than truly rare).
- **Real `injury_status` distribution:** Questionable (284), IR (194), NA
  (96), Out (52), PUP (38), **Sus (12)** -- suspension IS covered, Doubtful
  (5), COV (2), DNR (2).
- **`practice_participation` is REAL but essentially unpopulated:**
  **1 non-null value out of 12,227 real players.** The field exists in the
  schema and is documented, but empirically carries almost no signal --
  this pass does NOT treat it as a practice-participation source for that
  reason (nflverse fills this gap instead, see above).
- **Player ID mapping feasibility (real, computed with this pass's actual
  matcher against the real 564-player canonical pool, regardless of
  health status):** direct `gsis_id` match for 93/564 canonical players;
  name+position+team fallback (the SAME `_identity` normalizer
  `waiver_engine_service.resolve_roster_canonical_ids` already uses)
  brings the total to **481/564 = 85.3%** identity-matchable. `rotowire_id`
  is populated for 830/847 (98.0%) of real fantasy-relevant rostered
  skill-position players in the live catalog, and `sportradar_id` for
  832/847 (98.2%) -- meaningful future crosswalk value if either paid
  provider is ever purchased.
- **Actionable-signal coverage (real, computed via this pass's shipped
  `build_coverage_report`, i.e. only players carrying a non-default
  status/injury signal):** 70/564 = **12.4%** of the canonical pool has a
  real, currently-flagged Sleeper status today (2026-09-12, pre-Week-1).
- **Freshness:** `news_updated` is a real epoch-millisecond timestamp;
  spot-checked values resolve to 2026-09 dates -- genuinely current, not
  stale.
- **Rate limits/caching (real, quoted from `docs.sleeper.com`):** "stay
  under 1000 API calls per minute" generally; the `players/nfl` endpoint
  specifically is "intended only to be used once per day at most... save
  this information on your own servers." This pass's fetch script
  (`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`) enforces
  that 24h floor for real (verified live: a second real fetch attempt
  immediately after the first was correctly SKIPPED with the real elapsed-
  time message printed).
- **Commercial-use terms (real, quoted):** "The Sleeper API is a read-only
  HTTP API that is free to use for non-commercial purposes... For
  commercial use of the Sleeper API, please reach out to us directly to
  discuss licensing." **Real, disclosed caveat:** NWR is currently a
  personal desktop app, not sold/distributed commercially, so this
  admission stands today -- but this assumption should be explicitly
  re-checked with Sleeper if NWR is ever distributed or monetized. Not a
  reason to reject the source today; a reason to flag it honestly.
- **Historical access:** none disclosed -- this is a current-snapshot
  catalog, not a historical archive (nflverse fills that gap).
- **SLA:** none -- same real, disclosed risk as nflverse (free community
  API, no support contract, no uptime guarantee).

## Real comparison against NWR's existing 3 manual overrides

Run for real via `build_manual_override_comparison_report` against the real
fetched Sleeper snapshot and real nflverse Week 1 file:

| Real override on file | Kind | nflverse Week 1 finding | Sleeper finding |
|---|---|---|---|
| Jayden Higgins | `SEASON_OUT` (ACL) | No entry (expected -- he's already on IR, off the active-roster weekly report) | **Matches exactly**: `status=Inactive`, `injury_status=IR`, `injury_body_part=Knee - ACL`, team `HOU` -- independently confirms NWR's own manually-verified override |
| Elijah Mitchell | `NOT_WITH_TEAM` | No entry | Real catalog entry exists (`team=None`, `injury_status=Questionable`) but is honestly reported as `UNMATCHED_NO_TEAM` by this pass's shipped matcher -- **the matcher correctly refuses to guess an identity for a team-less player** rather than silently assuming a match. Illustrates in a completely real, concrete case exactly why manual verification must stay authoritative: even when a real signal exists, automated identity resolution can legitimately fail to attach it. |
| Kayshon Boutte | `TEAM_CORRECTION` -> HOU | No entry | Real catalog entry shows `team=HOU`, `status=Active`, no injury flag -- **agrees with the corrected team**, but produces no shadow record at all in the actionable-signal report (he's healthy, so `build_sleeper_shadow_records` correctly excludes him -- team corrections are outside this pass's injury/availability-signal scope, not a source failure) |

Net finding, stated honestly: in the one case with an active injury signal
(Higgins), the free Sleeper shadow source independently corroborates NWR's
already-verified manual override in every field it carries. In the other
two (non-injury) cases, the automated sources either can't attach an
identity (Mitchell, no team) or have nothing to say (Boutte, healthy) --
demonstrating real value in the injury case and real, honest limits
elsewhere, not overclaimed in either direction.

## Admission matrix

| Provider | Injury designation | Practice participation | IR/PUP/NFI | Suspension | Game-day inactive/active | Depth-chart movement | Player news | Timestamp granularity | Corrections/versioning | Player ID scheme | Historical access | Rate limits | Desktop-caching rights | UI-redistribution rights | Cost (real, 2026) | SLA | **Verdict** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RotoWire (syndication) | Yes (OUT/GTD/Q/D/IR/PUP/SUSP in one field) | Not confirmed in public docs | Yes (in same field) | Yes (SUSP) | Not confirmed | Yes (claimed) | Yes, rich (fantasy+betting context) | ISO 8601 `updatedAt` | Not disclosed | Not disclosed (but Sleeper carries a free `rotowire_id` crosswalk for 98% of real rostered skill players) | Not disclosed | Not disclosed | Not disclosed | Not disclosed | **Undisclosed -- sales-only** | Not disclosed | **NEEDS_OWNER_CONTRACT** |
| SportsDataIO | Yes | Yes (claimed, tier-dependent) | Yes (claimed) | Yes (claimed) | Yes (claimed) | Yes (claimed) | Yes | Not verified without a key | Not verified | Own `PlayerID`, crosswalk claimed, not verified against `gsis_id` | Yes, real | Real self-serve tier has daily caps | Personal-use tier terms allow hobby/personal apps | Not verified | **$99-149/mo self-serve (real, third-party-confirmed) but next-day-delayed; Enterprise real-time is quote-only** | None on self-serve; real SLA only on Enterprise | **NEEDS_OWNER_CONTRACT** |
| Sportradar | Yes (real, documented `NFL Weekly Injuries` endpoint) | Yes (claimed, "including practice status") | Not itemized separately | Not confirmed | Not confirmed | Not confirmed | Not confirmed | Not disclosed | Not disclosed | Not disclosed | Not disclosed | Not disclosed | Not disclosed | Not disclosed | **Undisclosed -- enterprise B2B, quote-only** | Not disclosed | **NEEDS_OWNER_CONTRACT** |
| FantasyData (prior repo research, not re-verified this pass) | Yes | Partial | Partial | Not confirmed | Not confirmed | Yes | Partial | Not verified | Not verified | Own ID, crosswalk claimed | Yes, claimed | Not verified | Not verified | Not verified | Budget API tier (not re-priced this pass) | Not verified | **NEEDS_OWNER_CONTRACT** |
| FantasyPros (prior repo research) | Partial (news/status context only) | No | No | No | No | No | Yes | Not verified | Not verified | Own ID | Not confirmed | Not verified | Not verified | Not verified | Not re-priced this pass | Not verified | **NEEDS_OWNER_CONTRACT** (and explicitly not a core fit even if free, per prior research) |
| ESPN unofficial API | Yes (community-reported) | Not researched | Not researched | Not researched | Yes (community-reported) | Not researched | Yes (community-reported) | Not researched | Not researched | ESPN internal id | Not researched | Undocumented, real risk | None stated | None stated | Free, no key (undocumented) | None -- no ToS found at all | **REFERENCE_ONLY**, not deep-dived, not admitted |
| **nflverse official injury report** | **Yes, real, verified** (`report_status`: Out/Doubtful/Questionable) | **Yes, real, verified, fully populated when present** (Full/Limited/DNP) | No (injury-report file only; roster-transaction IR/PUP is not this file's scope) | No | No (this file is the practice/game-status report, not the inactive list) | No | No | Season/week only in this file (no intra-week timestamp column found, despite the published dictionary describing one) | Not verified (no visible version history on the CSV asset itself) | **`gsis_id` -- IDENTICAL to NWR's own canonical id, direct match** | **Yes, real, free, back to 2009** | None documented | Yes -- static file, cache freely | Yes -- same posture as every other nflverse dataset this repo uses | **$0, verified free** | None (volunteer open-source project) | **ADMIT (shadow-only)** |
| **Sleeper public players/nfl catalog** | **Yes, real, verified** (`injury_status`) | Field exists but **empirically ~0% populated (1/12,227)** -- not usable | **Yes, real, verified** (`status`: IR/PUP/NFI/Inactive) | **Yes, real, verified** (`injury_status=Sus`, 12 real cases) | Partial (`status=Inactive` is the closest real signal; not a dedicated per-game active/inactive list) | **Yes, real, verified** (`depth_chart_position`/`order`) | Partial (`injury_notes`, short) | Real epoch-ms `news_updated` | Not disclosed (snapshot-only, no version history) | Own `player_id`; **real `gsis_id` field present for 93/564 canonical players directly, 481/564 (85.3%) identity-matchable overall via this pass's reused name/position/team matcher**; also carries `rotowire_id`/`sportradar_id`/`espn_id`/`yahoo_id` crosswalks | No (current snapshot only) | **Real, quoted: ~1000 calls/min general; `players/nfl` "once per day at most," enforced live by this pass's fetch script** | Yes -- explicitly told to cache locally | **Free for non-commercial use only** (real, quoted) -- flag for re-check if NWR is ever distributed/sold | **$0 for non-commercial use, verified free** | None (best-effort community API) | **ADMIT (shadow-only)** |

## Shadow ingestion built (reference-only, inert)

**Files:**
- `src/services/live_player_intelligence_shadow_v1_service.py` (new) --
  pure, network-free mapping/matching/report functions:
  `build_nflverse_injury_shadow_records`, `build_sleeper_shadow_records`,
  `match_shadow_records_to_canonical` (reuses the SAME `_identity`
  normalizer `fantasypros_kdst_consensus_service.py`/
  `waiver_engine_service.resolve_roster_canonical_ids` already use -- no
  new identity heuristic invented), `build_coverage_report`,
  `build_manual_override_comparison_report`, `precedence_design`.
- `scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py` (new) --
  the ONLY part of this pass that performs real network I/O. Fetches the
  real nflverse `injuries_<season>.csv` (no rate limit) and the real
  Sleeper `players/nfl` catalog (enforces the real 24h re-fetch floor,
  verified live: a second immediate real run was correctly SKIPPED).
  Writes RAW snapshots to `local_exports/live_player_intelligence_shadow_v1/
  {nflverse_injuries,sleeper_players}/latest/` -- a new, clearly-separate,
  **gitignored** location (`local_exports/` is repo-wide gitignored;
  confirmed via `.gitignore`), nowhere near
  `config/nwr_verified_current_player_status_overrides_v1.json`.
- `tests/test_live_player_intelligence_shadow_v1_service.py` (new, 11
  tests, all passing) -- mapping fidelity for both real source shapes,
  identity-matching (GSIS-direct, name/position/team fallback, honest
  `UNMATCHED_NO_TEAM` for team-less players), coverage/comparison report
  construction, the precedence-design contract, AND two hard-boundary
  proofs:
  1. `test_shadow_module_is_imported_by_no_production_consumer` -- a real,
     source-level static proof (reads the actual file text of
     `desktop_facade.py`, `server.py`, `player_availability_status_
     service.py`, `current_player_status_overrides_service.py`,
     `redraft_engine_v1_service.py`, `shadow_numeric_authorities_
     service.py`) that none of them import this module.
  2. `test_creating_a_shadow_snapshot_file_does_not_change_the_real_
     player_availability_status_authority_output` -- calls the REAL
     `load_player_availability_statuses`/`player_availability_authority_
     health` functions before AND after writing a real shadow snapshot
     probe file to the new `local_exports/` location, and asserts
     byte-identical (`==`) output both times.

**No production file was modified.** `git diff --stat` against this
worktree's start HEAD shows only the two new `src`/`scripts` files, the new
test file, this doc, and the ledger update.

**Real run against real data (reproducible via `scripts/fetch_live_player_
intelligence_shadow_snapshot_v1.py --source both --season 2026`, then the
service functions above against the real Freeze V7 seed and real override
file):** all numbers quoted throughout this doc's "Real, live-verified
findings" sections and the admission matrix's nflverse/Sleeper rows came
from exactly this real run, not a fixture.

## Precedence design (PROPOSAL ONLY -- not implemented, not wired anywhere)

Also returned as structured data by `precedence_design()` for a future
promotion pass to implement against directly, so nothing needs to be
re-derived from prose:

1. **`MANUAL_VERIFIED_OVERRIDE`** (`current_player_status_overrides_
   service.py`) -- always wins, unconditionally, on every field it sets.
   A verified manual override must be able to surgically supersede bad or
   stale automated data -- non-negotiable per existing project discipline,
   never weakened by a shadow source's presence, freshness, or
   agreement/disagreement with it.
2. **`AUTOMATED_SHADOW_SOURCE`** -- only applies to a player with NO
   manual override on that field. Between the two admitted automated
   sources, when both report on the SAME field for the SAME player and
   disagree: **nflverse's official `report_status`/`practice_status` wins
   for injury designation and practice participation** (it is the actual
   official NFL injury report, not a community-maintained mirror);
   **Sleeper wins for team/roster-status fields** (IR/PUP/Suspended/
   Inactive, current team, depth-chart order) that nflverse's weekly
   injury file does not carry at all. Never auto-applied to any ranking/
   recommendation path until a future, separate, deliberate promotion
   decision is made and implemented.
3. **`NO_SIGNAL`** (default) -- no override and no shadow signal: treated
   as full, healthy value, exactly as today.

**Promotion is a future, separate, deliberate decision** -- not automatic,
not implied by this module's existence, and not performed by this pass.

## Vendor/contact/action list for the owner (paid providers)

| Provider | Action needed | Why |
|---|---|---|
| RotoWire | Contact RotoWire's syndication/partnership team directly (`rotowire.com/partner/`) or a reseller (OpticOdds, SportsStack) for a real quote | No self-serve signup or public pricing exists at all |
| SportsDataIO | Sign up for the real self-serve DiscoveryLab personal-use tier (~$99-149/mo per third-party pricing trackers) if next-day-delayed data is acceptable; otherwise contact SportsDataIO sales for real-time Enterprise pricing | Self-serve tier is real and cheap but data-delayed; real-time requires a contract |
| Sportradar | Contact Sportradar sales via `developer.sportradar.com` or `marketplace.sportradar.com` | Fully enterprise/quote-gated, no self-serve tier found at all |
| FantasyData | Re-verify current 2026 pricing directly (not re-priced this pass) then contact sales if the tier fits | Prior repo research (May 2026) flagged it as the budget API fallback but did not confirm current price |
| FantasyPros | Only worth revisiting for projection/news context, not core availability data, per this repo's own prior research | Weakest injury-quality score (3/10) of the paid providers reviewed |

None of the above require any action from this pass -- they are handed to
the owner as real, disclosed options, not integrated, not paid for, and no
API key was requested or created anywhere in this pass.

## Real environment note

No `.env` file exists in this worktree; `.env.example` already has empty
placeholders for `SPORTSDATAIO_API_KEY`/`ROTOWIRE_EXPORT_ROOT` from an
earlier pass's scaffolding -- confirmed both are genuinely empty, no real
key is configured or was added by this pass.

## Sources

- [Sleeper API docs](https://docs.sleeper.com/)
- [RotoWire data dictionary](https://rotowire.readme.io/docs/data-dictionary)
- [RotoWire syndication/partner page](https://www.rotowire.com/partner/)
- [RotoWire via OpticOdds](https://developer.opticodds.com/docs/rotowire-news-injury-data)
- [SportsDataIO developers](https://sportsdata.io/developers)
- [SportsDataIO Discovery Lab](https://discoverylab.sportsdata.io/)
- [SportsDataIO Discovery Lab NFL personal-use page](https://discoverylab.sportsdata.io/personal-use-apis/nfl)
- [SportsDataIO pricing (third-party, Vendr)](https://www.vendr.com/marketplace/sportsdataio)
- [Sportradar NFL Weekly Injuries reference](https://developer.sportradar.com/football/reference/nfl-weekly-injuries)
- [Sportradar NFL API marketplace listing](https://marketplace.sportradar.com/products/64d179bb0a92ec119620d9d5)
- [nflreadr `load_injuries` reference](https://nflreadr.nflverse.com/reference/load_injuries.html)
- [nflreadr injuries data dictionary](https://nflreadr.nflverse.com/articles/dictionary_injuries.html)
- [nflverse-data injuries release](https://github.com/nflverse/nflverse-data/releases/tag/injuries)
- [Prior repo research: Project Gold Paid Data Value Assessment](../PROJECT_GOLD_PAID_DATA_VALUE_ASSESSMENT.md)
