# Route Feed Provider Email Templates V1

## Template 1: SumerSports Route Feed Permission Request

Subject: NFL routes-run data licensing/export inquiry

Hello [SumerSports contact],

I am working on an internal historical fantasy football research project and would like to ask whether SumerSports can license or otherwise permit use of an NFL route denominator feed.

We are specifically looking for actual player-level routes run for WR, TE, and RB pass catchers. Season-level data is the minimum need; week or game grain would be preferred.

The fields we would like to discuss include:

- player ID and player name
- team, season, position
- week/game fields if available
- routes run
- targets per route run if available
- yards per route run if available
- field dictionary
- historical coverage range
- update cadence
- missingness/eligibility documentation
- export/API/static delivery options
- permitted storage and derived-metric use

Could you confirm whether SumerSports offers a supported export, API, or licensed data product for this? We are also trying to understand whether RB route denominator fields are supported for export, and whether a Sumer player ID crosswalk is available.

We are not asking for sample player data in this email. We are first trying to determine whether there is a permission-safe, reproducible route denominator feed that could be reviewed for future source admission.

Thank you,
[NWR contact]

## Template 2: ESPN / Disney Receiver Tracking Metrics Request

Subject: ESPN Receiver Scores route denominator data licensing inquiry

Hello [ESPN/Disney contact],

I am working on an internal historical fantasy football research project and would like to ask whether ESPN/Disney can license or otherwise permit use of Receiver Scores route denominator data.

We are specifically looking for actual player-level routes run for WR, TE, and RB pass catchers. Season-level data is the minimum need; week or game grain would be preferred.

The fields we would like to discuss include:

- GSIS ID
- ESPN player ID
- player name
- team, season, position
- week/game fields if available
- routes run or `rtm_routes`
- targets or `rtm_targets`
- receiving yards if included
- row-grain documentation
- eligibility threshold documentation
- historical coverage range
- update cadence
- export/API/static delivery options
- permitted storage and derived-metric use

Could you confirm whether ESPN/Disney offers a supported export, API, or licensed feed for Receiver Scores or receiver tracking metrics? We are especially interested in the permissible route denominator field and any documentation around row grain, eligibility thresholds, and player identity fields.

We are not asking for sample player data in this email. We are first trying to determine whether there is a permission-safe, reproducible route denominator feed that could be reviewed for future source admission.

Thank you,
[NWR contact]

## Template 3: Fallback Commercial Provider Route Data Inquiry

Subject: NFL routes-run data feed licensing inquiry

Hello [provider contact],

I am working on an internal historical fantasy football research project and would like to ask whether [provider] offers a licensed NFL route denominator feed.

Minimum need:

- actual player-level routes run
- WR/TE/RB pass-catcher coverage
- season grain at minimum
- week/game grain preferred
- stable player identity fields
- team, season, position
- field dictionary
- historical coverage range
- update cadence
- missingness documentation
- reproducible export/API/static file delivery
- clear storage, display, model-use, and redistribution terms

Could you share whether such a feed is available for licensing and what terms apply for internal research and derived metrics such as yards per route run and targets per route run?

We are not asking for sample player data in this email. We are first determining whether a permission-safe feed exists that can be reviewed through our source-admission process.

Thank you,
[NWR contact]

## Follow-Up Checklist For Any Provider Reply

Ask for:

- license/terms document
- field dictionary
- schema sample without real player rows if possible
- coverage table
- identity key documentation
- row-grain documentation
- missingness/eligibility notes
- export/API documentation
- checksum/provenance support
- storage/redistribution restrictions
