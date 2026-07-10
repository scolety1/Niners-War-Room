# Team Offensive Environment Team-Change Caveats

The sidecar joins player-season rows to the player's prior-season team environment only. It does not know or project the player's future/target-season team. This is intentionally conservative and leakage-safe, but it can understate or misstate context for free-agent moves, trades, depth-chart changes, coaching changes, or quarterback changes between feature season N and target season N+1.

No target-season team context, current team context, or 2026 team context was used as a historical feature.
