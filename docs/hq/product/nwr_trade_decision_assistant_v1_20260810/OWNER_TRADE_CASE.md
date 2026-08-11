# Owner Trade Case

## Exact trade

Owner gives Luther Burden, Chris Bell, and 2027 1st. Owner receives George Kittle,
Chuba Hubbard, Brock Purdy, and 2028 2nd.

## Decision

- Recommendation: `COUNTER`
- Preferred side: Your current side
- Confidence: `MEDIUM`
- Biggest uncertainty: Chris Bell is not on the Finished V1 production scale.

Strongest reasons: Luther is the strongest production-ranked asset; the owner gives the
stronger pick class; Kittle and Hubbard have active age-window cautions; Purdy has limited
scarcity in 1QB; the incoming side supplies more established depth but more lifecycle risk.

## Roster-aware negotiation

- Classification: `PARTIAL_ROSTER_STATE`
- Source: active pack, snapshot `2026-pre-draft`, league `1344772855908290560`
- Owner: Niners, team 7, 24 players, 5 governed 2026 picks
- Kittle/Hubbard: The Mighty Canucks, team 3
- Purdy: WhoDat?, team 6
- Chris Bell: no roster row
- 2027/2028 picks: no ownership rows; admitted table contains only 2026
- Result: `BLOCKED_COUNTEROFFERS_NO_ROSTER_OWNERSHIP`

No specific Counter 1/2/3 is emitted because doing so would violate the additive hard rule.
The counter capability remains available for trades that resolve to one exact opponent.

## Missing capability

- Live roster sync exists: NO for this product runtime.
- Historical/local roster ingestion exists: YES.
- New manual ownership layer required: NO; the existing governed layer is reconnectable.
- Targeted data requirement: admit a current player plus 2027/2028 pick ownership snapshot.

## Market negotiation context

Stale as of 2026-07-17. Covered owner-give total: 4,443 (Luther only). Covered owner-receive
total: 3,495 (Kittle 916, Hubbard 538, Purdy 2,041). Covered delta: -948. Chris Bell and both
picks are excluded. These are partial external negotiation totals, not NWR package value.
