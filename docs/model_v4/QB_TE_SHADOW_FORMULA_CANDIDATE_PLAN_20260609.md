# QB/TE Shadow Formula Candidate Plan - 2026-06-09

This is proposal-only. It does not tune production formulas and does not choose a final winner.

## Private Baseline Distribution Inputs
- QB median baseline score: 15.1316
- TE median baseline score: 14.3814
- RB/WR 90th percentile baseline score: 50.9317
- RB/WR 85th percentile baseline score: 44.9537

## Variants
- `qb_1qb_spread_compression_v1`: compresses QB scores toward the private QB median to test 1QB spread discipline without using public ranks.
- `te_no_premium_ceiling_v1`: applies a no-premium TE ceiling shaped by the private RB/WR score distribution, then compresses TE spread toward the TE median.
- `qb_te_context_balance_v1`: combines QB spread compression with a stricter TE no-premium ceiling to test cross-position interpretability.

## Broad Behavior Goals
- In 1QB, QB scores should be less likely to dominate top overall dynasty tiers unless strongly supported by private evidence.
- Elite QBs should not collapse below depth rows without explainable private evidence.
- In no-TE-premium, elite TE exceptions should be possible but should not automatically outrank elite RB/WR assets.
- RB/WR scores should not be changed by these QB/TE candidates; rank movement is collateral only.

## Blocked Inputs
Market rank, league rank, ADP, startup, public ranks, projections, consensus, trade calculators, RotoWire rankings/projections, and legacy active-pack scores are not candidate inputs.
