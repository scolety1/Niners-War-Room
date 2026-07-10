# Overlay Batch Primary Priority Policy

For V1, all overlay eligibility is recorded, but only one primary overlay is applied per player-season. This follows the discovery packet priority order:

1. `OVERLAY_001_SPARSE_EARLY_ROLE_BREAKOUT`
2. `OVERLAY_002_AVAILABILITY_REBOUND`
3. `OVERLAY_003_STARTER_DEPTH_PROMOTION`
4. `OVERLAY_004_SNAP_GROWTH_ROLE_PROMOTION`
5. `OVERLAY_008_DRAFT_CAPITAL_WITH_ROLE`

The user prompt suggested moving availability rebound after starter/depth and snap-growth. This lane uses the discovery packet order because the accepted discovery priority ranked availability rebound second by evidence strength, signal availability, and expected near-term value.

No silent stacking is allowed. Secondary eligibility is recorded in `OVERLAY_BATCH_ELIGIBILITY_LEDGER.csv` but does not alter the score.
