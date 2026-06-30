# High-Production Non-Drafted Watchlist Policy

This packet creates a review-only policy for a narrow watchlist flag:
`high_production_nondrafted_watchlist`.

## Policy

- Most `likely_udfa_needs_review` rows remain ignored or blocked.
- Only extreme approved college producers may be surfaced for human review.
- Not found in draft-pick data does not prove confirmed UDFA.
- Strong college production plus draft absence does not prove confirmed UDFA.
- `high_production_nondrafted_watchlist` is a review-only flag, not an entry-status promotion.
- No row in this packet is approved for training, model use, Gate F, Gate G, Rankings, Live Draft Room, or source truth.
- Human review is required before any future promotion or source-truth patch.

## Non-Drafted Interpretation

The phrase non-drafted here means not found in the currently approved draft-pick lookup. It does not mean confirmed UDFA, confirmed rookie free agent, clean training row, or failed-player evidence.

## Current Packet Result

Approved CFBD production/context is not safely joined to the historical likely non-drafted candidate universe in this base. The watchlist is therefore header-only with zero candidates surfaced.
