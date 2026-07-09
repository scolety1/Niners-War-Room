# Fallback Provider Outreach Templates V1

Status: no outreach sent by this lane.

## Fallback Providers

- PFF
- SIS
- Sportradar
- commercial FTN
- FantasyPoints Data
- Establish The Run
- Rotoviz
- SportsDataIO
- official NFL Next Gen Stats access

These are contractable/proprietary leads only. Do not use, scrape, or copy their data unless a future contract/source-admission lane approves a safe path.

## Commercial Route Feed Inquiry Template

Subject: NFL routes-run data feed licensing inquiry

Hello [provider contact],

I am working on an internal historical fantasy football research project for Niners War Room and would like to ask whether [provider] offers a licensed NFL route denominator feed.

Minimum need:

- actual player-level `routes_run`
- WR/TE/RB pass-catcher coverage
- season grain at minimum
- week/game grain preferred
- stable player identity field
- player name
- team
- season
- position
- provider/feed name
- source update timestamp
- field dictionary
- historical coverage range
- update cadence
- missingness documentation
- reproducible export/API/static file delivery
- clear storage, display, model-use, and redistribution terms

Preferred fields:

- week/game IDs
- GSIS/ESPN/provider IDs
- targets
- receiving yards
- targets per route run
- yards per route run
- missingness/eligibility flags
- checksums or row hashes

Could you share whether such a feed is available for licensing and what terms apply for internal research and derived metrics such as yards per route run and targets per route run?

We are not asking for sample player data in this email. We are first determining whether a permission-safe feed exists that can be reviewed through our source-admission process.

Thank you,

[NWR contact]

## Official NFL / NGS Access Variant

Subject: NFL route denominator / route recognition data access inquiry

Hello [NFL/NGS contact],

I am working on an internal historical fantasy football research project for Niners War Room and would like to ask whether official NFL Next Gen Stats route denominator or route recognition data can be licensed or otherwise accessed for internal research.

The minimum need is actual player-level `routes_run` for WR, TE, and RB pass catchers, preferably at game or week grain. We are not asking for sample player data in this email; we are first trying to determine whether an official, permission-safe access path exists.

Thank you,

[NWR contact]

## Follow-Up Questions For Fallback Providers

Ask every fallback provider:

1. Does the feed include actual `routes_run`?
2. Are WR, TE, and RB included?
3. What seasons are covered?
4. What row grains are available?
5. What stable player IDs are included?
6. Are GSIS, ESPN, or official crosswalk fields available?
7. What export/API/static delivery options exist?
8. What internal storage and derived-metric rights are allowed?
9. What raw or derived redistribution restrictions apply?
10. Are checksums, schema versions, and provenance metadata available?
