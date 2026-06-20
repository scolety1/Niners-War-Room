# NWR NFL Stats Source V0 Decision

Date: 2026-06-20

Owner: Master/Main HQ

## Executive Decision

NWR Stats Source V0 will use `nflverse` / `nflreadr` / `nflreadpy` as the primary free historical/player stats source candidate.

SportsDataIO Discovery Lab may be evaluated as an optional backup and cross-check source only if its free tier, API key requirements, license terms, fields, caching rights, and player identity mapping are safe for local NWR use.

Do not blend or average stats sources automatically. If nflverse and SportsDataIO disagree, NWR should create a YELLOW audit report and require Tim/Master/QA review before any downstream use changes.

This decision does not implement pullers, create scheduled tasks, create Lane Exchange packages, update `latest_candidate`, update `latest_approved`, approve private value use, approve model training, approve final draft-day use, deploy, push, or run simulations.

## Research Basis

This decision uses the external research summary Tim provided:

1. Primary: `nflverse` / `nflreadr` / `nflreadpy`
2. Backup/cross-check: SportsDataIO Discovery Lab, if free/license/key constraints work
3. Avoid scraping and unofficial unstable endpoints for V0

A separate full external research report file was not found in the local Master/shared-data workspace during this pass. Local NWR docs corroborate the direction: prior NWR source audits already treated nflverse as the factual historical stats route and the local RotoWire spike found RotoWire oriented toward projections, injuries, and news rather than proven historical stats.

## Source Roles

| Source | V0 Role | Decision |
| --- | --- | --- |
| `nflverse` / `nflreadr` / `nflreadpy` | Primary historical/player stats source | GREEN to spike first, local-only |
| SportsDataIO Discovery Lab | Optional backup/cross-check | YELLOW until key, license, free-tier limits, fields, and identity mapping are verified |
| Sleeper | League truth: rosters, users, draft order, picks, trades, transactions | GREEN for league state, not historical stats truth |
| RotoWire | Optional paid display context: injuries, news, projections | YELLOW/HOLD; not V0 historical stats truth |
| CollegeFootballData | College/rookie yearly refresh candidate | YELLOW for rookie/college only; not NFL veteran stats truth |

## Sources Not Recommended For V0

Do not use these as V0 source-of-truth inputs:

- random scraping
- unofficial unstable endpoints
- unverified GitHub clients as the actual source of truth
- ESPN/Yahoo/FantasyPros integrations before Sleeper, nflverse, and CFBD are stable
- any source that cannot be licensed, cached, mapped to player identity, and audited safely
- any source that mixes factual stats with ADP, market ranks, projections, public rankings, editorial tiers, trade values, or hidden scores

## Why Each Adjacent Source Is Limited

Sleeper remains league truth because it is best suited for league settings, rosters, users/team mappings, draft order, traded picks, transactions, ownership evidence, and live league-state checks. It is not the historical NFL production source.

RotoWire remains optional display-only projection/news/injury context because the local vendor spike found no API key, unverified NFL entitlement, unverified response fields, and an installed client surface focused on daily/weekly projections, injuries, and news/injuries. It is not accepted as V0 historical stats truth.

CollegeFootballData remains rookie/college-only because it supports college player/team/game data and rookie/offseason refreshes. It must preserve Rookie HQ board/formula/order guardrails and must not be used as NFL veteran historical stats truth.

## Local-Only Raw Snapshot Paths

Planned local-only roots, outside all Git repos:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\
C:\NWR_SHARED_DATA\scheduled_ingest\sportsdataio\
C:\NWR_SHARED_DATA\scheduled_ingest\stats_compare\
C:\NWR_SHARED_DATA\scheduled_ingest\reports\stats_source_v0\
```

These paths are not created by this document. They should be created only by a later approved local-only implementation prompt.

## Candidate Lane Exchange Package Names

These package names are reserved for future implementation. Do not create them yet.

```text
stats_context/player_weekly_stats_display_context
stats_context/player_season_stats_display_context
stats_context/player_usage_context
stats_context/player_stats_crosscheck_report
```

Initial package use must be display/stat context only. Any private value, model training, hidden ranking, or final draft-day use requires a later approved source policy.

## Source Priority And Disagreement Policy

Source priority:

1. `nflverse` is the primary V0 factual stats source candidate.
2. SportsDataIO may cross-check missing, changed, or disagreeing stats.
3. SportsDataIO cannot override nflverse automatically.
4. Disagreements create YELLOW audit reports.
5. Tim/Master/QA review decides whether a source correction, identity repair, or source-specific caveat is needed.

No automated blend, average, majority vote, or fallback substitution is approved.

## Proof-Of-Concept Plan

The first proof-of-concept must be local-only.

Allowed:

- Use `nflverse` / `nflreadr` / `nflreadpy` or official nflverse release assets.
- Write local-only scratch reports under `C:\NWR_SHARED_DATA\scheduled_ingest\reports\stats_source_v0\`.
- Capture source version, endpoint or release path, retrieval timestamp, field names, row counts, ID mapping fields, and small redacted samples.
- Compare identity mapping against Sleeper identity where locally available.
- Report whether weekly stats, season stats, usage fields, player IDs, team, position, season, and week fields exist.

Blocked:

- No repo data commits.
- No raw stats data committed.
- No Lane Exchange publishing.
- No `latest_candidate` or `latest_approved` updates.
- No API keys in Git.
- No `.env` in any Git repo.
- No simulations.
- No deploy.

Test player set should include at least:

- Drake Maye
- Jaylen Warren
- Darren Waller
- Brock Purdy
- Dak Prescott
- Zay Flowers
- Keenan Allen
- Chris Olave
- Rashee Rice
- Jameson Williams
- Brian Thomas
- Alec Pierce

The spike should also allow additional identity-control players if needed, but must not expand into broad raw-data publication without approval.

## SportsDataIO Discovery Lab

SportsDataIO may be tested only after Tim provides or confirms:

- API key availability
- free-tier or paid license terms
- allowed local caching rights
- allowed local analytical use
- rate limits
- player identity fields
- NFL stat endpoint coverage

SportsDataIO output should be stored only in local-only raw snapshots and small reports until a later approval. It may produce a cross-check report, but not a private value package or automatic replacement for nflverse.

## Security And Key Rules

- nflverse should not require a paid API key for the primary proof-of-concept route.
- SportsDataIO may require a key; any key must remain outside Git.
- Preferred secret locations are local environment variables, Windows Credential Manager, or `C:\NWR_SHARED_DATA\secrets\`.
- Do not create `.env` inside any NWR Git repo.
- Do not print full keys in logs.
- Do not commit full raw vendor responses.
- Do not commit licensed data unless the license explicitly allows it and Master approves the exact artifact.
- Reports should use redacted config summaries only.

## Schedule Recommendation

After implementation approval:

| Source | Schedule | Status |
| --- | --- | --- |
| nflverse | Every 2-3 days if useful during active analysis, or weekly if mostly historical | Candidate after POC |
| SportsDataIO | Cross-check only after key/license verification | HOLD |

Scheduled jobs may write raw snapshots, status reports, and validated `latest_candidate` packages only after a separate implementation approval.

`latest_approved` remains Tim/Master/QA-gated. `pinned_live_snapshot` requires separate final live-test or draft-day approval.

## Blocked Uses

Stats Source V0 is blocked from:

- private value
- hidden sorting
- hidden ranking
- ADP or market blending
- final draft-day decisions
- simulations or recommendations
- model training
- probabilities, bands, promoted artifacts, or production app display changes

Any upgrade from display/stat context into model features, private value, or final decision support requires a separate source policy and audit gate.

## Recommended Next Implementation Prompt

```text
You are Master/Main HQ for Niners War Room.

Run a local-only nflverse proof-of-concept spike for NFL Stats Source V0.

Use only C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\ and C:\NWR_SHARED_DATA\scheduled_ingest\reports\stats_source_v0\ for local outputs.
Do not modify any NWR repo except for an optional Master report doc if explicitly useful.
Do not create Lane Exchange packages.
Do not update latest_candidate or latest_approved.
Do not commit raw stats data.
Do not create .env files or secrets in any Git repo.
Do not run simulations or deploy.

Check whether nflreadpy, nflreadr, or official nflverse release assets can provide weekly player stats, season player stats, usage/snap/participation context, stable player IDs, team, position, season, and week fields.
Test a small player sample including Drake Maye, Jaylen Warren, Darren Waller, Brock Purdy, Dak Prescott, Zay Flowers, Keenan Allen, Chris Olave, Rashee Rice, Jameson Williams, Brian Thomas, and Alec Pierce.
Compare identity mapping to Sleeper where available.
Capture only row counts, field names, ID mapping results, source paths, hashes, and small redacted samples.
Return GREEN/YELLOW/RED and recommend whether to build scheduled nflverse raw snapshot puller next.
```

SportsDataIO proof-of-concept should wait until Tim confirms a safe key/license/free-tier path.

## Master Verdict

GREEN for Stats Source V0 decision planning.

YELLOW for implementation because no local proof-of-concept has run, SportsDataIO key/license status is unknown, and no source is approved for private value, model training, or final draft-day decisions.
