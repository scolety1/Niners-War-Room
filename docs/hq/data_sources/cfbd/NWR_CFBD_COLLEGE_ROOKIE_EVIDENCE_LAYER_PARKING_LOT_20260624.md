# CFBD College/Rookie Evidence Layer Parking Lot

CFBD belongs in a separate College/Rookie Evidence Layer.

It may help with rookie/prospect production, usage, recruiting, transfer, team context, and advanced college metrics.

Likely future college/rookie signals include:
- college production
- player usage
- recruiting profile
- transfer portal context
- team/conference context
- PPA and advanced college metrics
- draft/NFL transition evidence

It should not feed rankings, model, or app pages until its own contract, field inventory, validation/quarantine, and promotion gate exist.

It should later join the Unified Universe Review as review-only, not source truth.

Do not mix CFBD into NFL Usage Evidence Layer V0. NFL Usage Evidence Layer V0 is pro/NFL usage after players enter the league.

The separate CFBD setup lane currently has a real-pull blocker documented in `docs/hq/parallel_lanes/NWR_CFBD_FULL_SETUP_AND_REAL_PULL_COMPLETION_20260624.md`: direct CFBD auth returned `401 Unauthorized`, so broad pulls should wait for a valid API token. That blocker does not affect NFL Usage Evidence Layer V0.

Future CFBD work requires its own source contract, field inventory, validation/quarantine harness, review artifacts, and promotion/backtest gate before any display/model/rank use.
