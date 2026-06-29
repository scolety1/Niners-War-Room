# Gate D Feature Policy Inventory - 2026-06-30

## Base

- Actual base HEAD: `f0832ecd49d0190609310bc961979a26d2374be0`
- Branch: `work/rookie-gate-d-feature-policy-v1-20260630`
- Lane: rookie outcome feature policy only

## Prior Gates

- Gate A: `GREEN_REVIEW_ONLY_IDENTITY_APPROVAL`
- Gate B: `PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT`
- Gate C: `PARTIAL_HISTORICAL_ROOKIE_LABELS`

## Available Inputs

- Draft capital and draft context: review-only historical drafted-player bridge.
- Draft year / rookie class year: available for 1,025 drafted QB/RB/WR/TE bridge rows.
- Position: available for 1,025 bridge rows.
- Drafted team / NFL landing spot: available as review-only context in the bridge.
- College/team context: available from nflverse draft-picks bridge as review-only context.
- Historical rookie labels: 919 review-only label rows under `C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1\`.
- Outcome scoring: `exact_verified_first_downs`; approximation rows: 0.

## Partial / Missing Inputs

- CFBD production context is still review-only and not model/training/source truth.
- Age at draft is not in the current approved bridge artifact.
- Size / height / weight exists only in review queues or needs approved source linkage.
- Recruiting context is not available in an approved tracked source.
- Final-year/career college production exists only as review-only CFBD context.
- Market share / dominator, transfer timeline, early declare, combine/pro day are not approved.
- UDFA/free-agent rookie-entry bridge is still missing.

## Policy Need

Gate E may only run as review-only model R&D if it uses non-leaky, source-gated features and keeps all model/training flags closed. Historical labels may be targets for review analysis, never input features.
