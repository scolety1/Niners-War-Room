# Historical Backtest Frame

The frozen 5,518-row Formula Data Mart uses completed feature season N facts to predict target
season N+1. Current/future role, injury, market, and target fields are excluded from the feature
side. Seasons are evaluated independently; no random split or current 2026 board is used.

The mart contains the frozen NWR non-PPR/first-down target, so it supports the representative
10-team 1QB architecture test. It does not contain target-season granular stat components needed
to truthfully recompute PPR or Superflex target labels. Those profiles receive deterministic
sensitivity tests, not fabricated historical outcomes.
