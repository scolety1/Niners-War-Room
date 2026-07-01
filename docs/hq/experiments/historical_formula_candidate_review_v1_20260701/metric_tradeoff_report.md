# Metric Tradeoff Report

The candidate's main positive tradeoff is lower MAE with stable aggregate rank/order.

Known tradeoffs:

- Some Top-N buckets move slightly, including WR/RB bucket-level precision changes.
- Validation Spearman is slightly lower than baseline, while holdout Spearman is slightly higher.
- Aggregate startable precision is flat on holdout.

This supports human review, not production promotion.
