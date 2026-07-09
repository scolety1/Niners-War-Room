# Fallback Provider Send Template V1

Status: not sent by this lane.

## Fallback Provider Classification

Fallback providers are proprietary/contractable leads only:

- PFF
- SIS
- Sportradar
- commercial FTN
- FantasyPoints Data
- Establish The Run
- Rotoviz
- SportsDataIO
- official NFL Next Gen Stats access

Do not use, scrape, copy, or infer permission from these providers. Any usable path requires a contract/permission response and a separate source-admission lane.

## Send-Ready Template

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

## Send Gate

Before sending, complete `provider_send_authorization_checklist_v1.md`. Classify any favorable fallback response as `CONTRACT_ONLY_PROPRIETARY` unless public/permission-safe use is explicitly documented.
