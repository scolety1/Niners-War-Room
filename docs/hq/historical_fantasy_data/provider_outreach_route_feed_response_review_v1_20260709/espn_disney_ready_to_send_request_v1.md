# ESPN / Disney Ready-To-Send Request V1

Status: not sent by this lane.

Subject: ESPN Receiver Scores route denominator data licensing inquiry

Hello [ESPN/Disney contact],

I am working on an internal historical fantasy football research project for Niners War Room and would like to ask whether ESPN/Disney can license or otherwise permit use of Receiver Scores route denominator data.

We are specifically looking for actual player-level routes run for WR, TE, and RB pass catchers. Season-level data is the minimum need; week or game grain would be preferred.

Minimum required fields:

- `routes_run`, `rtm_routes`, or equivalent route denominator field
- stable player ID
- player name
- team
- season
- position
- provider/feed name
- source update timestamp

Preferred fields:

- week/game IDs
- GSIS ID
- ESPN player ID
- provider player ID
- targets or `rtm_targets`
- receiving yards
- targets per route run
- yards per route run
- eligibility/missingness flags
- checksums or row hashes

Could you confirm whether ESPN/Disney offers a supported export, API, or licensed feed for Receiver Scores or receiver tracking metrics? We are especially interested in permissible use of route denominator data and documentation around row grain, eligibility thresholds, and player identity fields.

We would also appreciate documentation for:

- historical coverage range
- WR/TE/RB position coverage
- season/week/game row grain
- field dictionary for `rtm_routes` and related fields
- eligibility threshold policy
- update cadence
- storage, display, model-use, and redistribution terms
- checksum/provenance support

We are not asking for sample player data in this email. We are first trying to determine whether there is a permission-safe, reproducible route denominator feed that could be reviewed through a future source-admission process.

Thank you,

[NWR contact]

## Intake Notes

If ESPN/Disney replies, record the response in `provider_response_intake_template_v1.md` before any data is accepted or reviewed. Do not use public client objects as admitted feeds without a separate source-admission lane.
