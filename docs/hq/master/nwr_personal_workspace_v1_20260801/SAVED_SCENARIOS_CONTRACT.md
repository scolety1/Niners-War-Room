# Saved Scenarios contract

The governed scenario types are Trading Lab, Player Compare, Draft, and Asset
Explorer. Each record preserves exact asset IDs, its source-version map, its
manual inputs/payload, title, and timestamps. A source-version mismatch is shown
as stale rather than silently recalculated. Scenario payloads reject verdict,
winner/loser, accept/reject, fair/unfair, hidden combined-score, credential, and
private-identifier fields.
