# Personal Board contract

Personal Board stores user-controlled tier, ordinal, watchlist, target, avoid,
sleeper, sell-high, buy-low, tags, notes, conviction, team-window label, and
future extension fields against an exact governed asset ID and source type.
Supported assets are 240 Finished V1 current players, 73 scored Review-Only
rookies, seven visible blocked rookies, and 50 frozen draft-context picks.

Personal fields are always labeled as user-authored. They never overwrite,
reorder, or masquerade as source ranks, scores, evidence, confidence, or
authority. Unknown IDs and source-type mismatches fail closed. Saves, imports,
archives, and deletes are explicit; page loads are read-only.
