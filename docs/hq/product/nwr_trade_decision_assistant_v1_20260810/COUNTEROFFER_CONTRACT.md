# Counteroffer Contract

The base decision engine emits no generic counters. The roster-aware adapter may show 2–4
specific structures only after:

- the owner team is exact;
- all outgoing assets are owner-owned;
- every incoming/candidate asset is owned by one resolved opponent;
- pick ownership is exact;
- identities are unique and sides do not overlap.

When resolved, the adapter searches the full opponent roster, maps NWR/market rank bands,
examines team fit, explores both keep-premium and trade-premium structures, checks every
candidate again for constructibility, and provides “why this helps me,” “why they might
consider,” opportunity, and risk text.

When any ownership condition fails, the only result is
`BLOCKED_COUNTEROFFERS_NO_ROSTER_OWNERSHIP`. No target-profile or generic counter fallback is
rendered.

