# Manual Plugin Operating Guide

## Common operating rules

Consultation must be manually requested, read-only, purpose-limited, and clearly labeled as non-authoritative. Do not persist substantial provider output, copy provider explanations, expose private league data, or let a result influence production calculations or ordering. Applicable provider terms and privacy duties continue to control.

## Flaim permitted manual uses

- Explicit league settings.
- Explicit lineup-slot counts.
- Roster membership snapshots.
- Provider-ID-based ownership review.
- Tentative matchup context.
- Individual player identity lookup.

Every use must retain the relevant fidelity, freshness, completeness, and verification caveats. When a source-as-of field is unavailable, say that currentness is not established.

## Flaim prohibited authoritative uses

Do not treat Flaim as authoritative for standings rank, season phase, playoff status, the complete free-agent pool, add/drop direction, exact trade sides, transaction-window completeness, current freshness without a source-as-of field, or production source truth.

Specific rules:

- A roster snapshot is a point observation, not guaranteed current truth.
- Ownership can support identifier-based review but was not verified against same-time native truth.
- Matchup context is tentative where phase and playoff semantics are incomplete.
- Free-agent results cannot be treated as exhaustive or directly actionable.
- Standings, normalized add/drop direction, and reconstructed trade sides must not be relied on.

## FantasyBot permitted manual uses

- Generic external opinion.
- Hypothesis generation.
- General statistical context.
- A clearly labeled approximate second opinion.

Every FantasyBot use must state: `Exact NWR scoring and league context are not supported.`

## FantasyBot prohibited uses

Do not use FantasyBot as NWR dynasty value, a trade winner, a player rank, a production recommendation, a numerical formula input, a hidden confidence signal, a sorting signal, roster-specific truth, exact NWR-scoring analysis, a persistent disagreement panel, or a source-admitted datum.

Do not translate season or PPR production totals into a comparable dynasty trade-value scale. Immediate exact repeatability does not establish day-to-day, week-to-week, or provider-version stability.

## Recording a consultation

If a human records a decision influenced by manual consultation, record only a brief paraphrase of the human takeaway and the applicable caveat. Do not retain private identifiers, full output, provider prose, or reversible league mappings. The NWR base result must remain independently reproducible without the consultation.
