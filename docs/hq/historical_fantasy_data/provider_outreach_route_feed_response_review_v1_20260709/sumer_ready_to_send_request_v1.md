# SumerSports Ready-To-Send Request V1

Status: not sent by this lane.

Subject: NFL routes-run data licensing/export inquiry

Hello [SumerSports contact],

I am working on an internal historical fantasy football research project for Niners War Room and would like to ask whether SumerSports can license or otherwise permit use of an NFL route denominator feed.

We are specifically looking for actual player-level routes run for WR, TE, and RB pass catchers. Season-level data is the minimum need; week or game grain would be preferred.

Minimum required fields:

- `routes_run` or `receivingPassRoutesRun`
- stable player ID
- player name
- team
- season
- position
- provider/feed name
- source update timestamp

Preferred fields:

- week/game IDs
- provider player ID and any GSIS/ESPN crosswalk fields
- targets
- receiving yards
- targets per route run
- yards per route run
- missingness/eligibility flags
- checksums or row hashes

Could you confirm whether SumerSports offers a supported export, API, or licensed data product for this? We are also trying to understand whether RB route denominator fields are supported for export, and whether a `sumerPlayerId` crosswalk is available.

We would also appreciate documentation for:

- historical coverage range
- WR/TE/RB position coverage
- season/week/game row grain
- field dictionary for route fields
- update cadence
- null/zero/missingness policy
- storage, display, model-use, and redistribution terms
- checksum/provenance support

We are not asking for sample player data in this email. We are first trying to determine whether there is a permission-safe, reproducible route denominator feed that could be reviewed through a future source-admission process.

Thank you,

[NWR contact]

## Intake Notes

If Sumer replies, record the response in `provider_response_intake_template_v1.md` before any data is accepted or reviewed. Do not ask for raw route rows until source-admission ownership approves a safe intake path.
