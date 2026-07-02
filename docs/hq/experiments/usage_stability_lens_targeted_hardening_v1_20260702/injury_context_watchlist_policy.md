# Injury Context Watchlist Policy

Decision: preserve injury/context caution as review classification only.

No current injury field was used as a formula feature in this lane. Injury context may be discussed as human-review context where Tim has explicitly identified it, but it is not promoted to source truth and is not wired into ranking behavior.

## Policy

- Do not automatically correct a low candidate output when recent factual data may be missing, limited, or difficult to interpret.
- Do not treat market disagreement as proof of formula failure.
- Do not use current-only injury/status/depth/schedule context as historical formula features.
- Do not create player-name formula exceptions.
- Keep injury/timeline cases as review-only watchlist classifications unless a future gate approves a safe source and explicit use.

## Applied Case

Malik Nabers remains `INJURY_TIMELINE_DISCOUNT_WATCHLIST`, not an automatic dynasty-stability miss.
