# Pre-Draft vs Post-Draft Feature Policy

Pre-draft factual candidates, such as combine or prospect-age context, still require a source, as-of, historical replay, missingness, and feature approval gate before experimentation.

Post-draft/current NFLVerse fields are display/review context only. This includes rosters, weekly rosters, snap counts, player_stats, depth charts, injuries, schedule context, contracts, last-active fields, and current player-context identity fields.

Post-draft fields cannot be used as pre-draft Rookie Outcome features unless a future replay proves they existed at the prediction anchor and passes leakage review. Future NFL production, games, starts, awards, career length, player_stats, snaps, injury reports, roster state, and depth chart role cannot be used as input features for drafted-only rookie prediction in this lane.

Missing values remain `Not enough information`; they are never zero, false, clean, healthy, no-role, low-risk, confirmed UDFA, or negative outcomes.
