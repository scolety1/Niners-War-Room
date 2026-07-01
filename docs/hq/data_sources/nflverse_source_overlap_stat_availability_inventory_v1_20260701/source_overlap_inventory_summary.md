# NFLVerse Source Overlap and Stat Availability Inventory V1 Summary

Verdict: `YELLOW_STAT_AVAILABILITY_INVENTORY_PARTIAL_SOURCE_GAPS`

## Scope

This lane inventories NFLVerse, NFL usage, Outcome sidecar, player context, availability, rookie/pre-draft, injury, schedule, and source-governance artifacts. It does not approve model use, training use, source truth, label truth, probabilities, rankings, or app behavior.

## Counts

- Total inventory rows: `2264`
- Unique normalized fields: `1133`
- Source family coverage rows: `38`
- Fields with multi-source overlap: `263`
- Unique high-confidence factual stats: `45`
- Fields blocked by source policy or market/projection policy: `50`
- Fields blocked by licensing/vendor/private gaps: `1`
- Fields needing as-of/leakage gate: `438`
- Fields needing zero/missingness gate: `19`

## Bucket Counts By Unique Normalized Field

- `BLOCKED_AMBIGUOUS_SEMANTICS`: `1`
- `BLOCKED_LICENSED_GAP`: `1`
- `BLOCKED_LOW_COVERAGE`: `5`
- `BLOCKED_MARKET_OR_PROJECTION`: `39`
- `BLOCKED_SOURCE_POLICY`: `11`
- `DISPLAY_ONLY_CONTEXT`: `93`
- `EXPERIMENT_CANDIDATE_REQUIRES_GATE`: `210`
- `HIGH_CONFIDENCE_CONTEXT_FIELD`: `79`
- `HIGH_CONFIDENCE_FACTUAL_STAT`: `45`
- `HIGH_CONFIDENCE_IDENTITY_PLUMBING`: `55`
- `NEEDS_ASOF_OR_LEAKAGE_GATE`: `438`
- `NEEDS_IDENTITY_GATE`: `123`
- `NEEDS_ZERO_OR_MISSINGNESS_GATE`: `19`
- `NOT_AVAILABLE`: `14`

## Biggest Safe Stat Families For Later Gates

- player_stats usage/scoring components
- snap counts
- NFL usage historical panels
- draft/combine context
- schedule/team context
- identity plumbing

## Biggest Missing Or Blocked Families

- routes run / TPRR / YPRR as direct approved fields
- direct return touchdown subtype
- pre-game/as-of historical snapshots
- licensed/vendor projection/rank fields
- complete zero-row eligibility for every player-week

## Important Interpretation

Full scoring parity blockers do not block all NFLVerse usage. Scoring-reconstruction-dependent fields remain gated, while lagged usage, snap counts, draft/combine context, schedule/team context, and identity/display artifacts are classified independently for future review gates.
