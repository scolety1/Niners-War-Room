# Human Review Summary - Current Rookie UDFA Unknown Packet V1

This packet exists because Gate G is blocked by non-drafted/unknown rookie rows.
A UDFA status here means review-only undrafted/free-agent context. It is not
source truth, model input, training truth, or a rookie probability.

Absence from the completed nflverse 2025/2026 draft-pick set is useful evidence.
It is strongest when paired with an approved review-only identity and an existing
NWR/Sleeper team or FA context. Absence by itself is not enough for thin rows.

Decision meanings:
- `CONFIRM_UDFA_REVIEW_ONLY`: safe recommendation for review-only approval if the user accepts it later.
- `KEEP_LIKELY_UDFA_REVIEW`: likely undrafted, but evidence is not strong enough.
- `REJECT_WRONG_UNIVERSE`: wrong player/year/name collision.
- `KEEP_UNKNOWN`: too little evidence; keep `Not enough information`.
- `NEEDS_MORE_INFO`: a specific missing source is required.

Counts by recommended decision:
- CONFIRM_UDFA_REVIEW_ONLY: 28
- KEEP_UNKNOWN: 10

Rows likely safe to confirm review-only: 28.
Rows that should remain unknown: 10.
Wrong-universe/name-collision rows remain blocked from the prior lane: 2.

If accepted later, these recommendations can unlock status-only UDFA display
context for the recommended rows. They do not unlock model use, training use,
Rankings wiring, hidden sorting, or rookie outcome probabilities.
