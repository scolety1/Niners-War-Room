# Model v4 Spec

Model v4 is a clean scoring and decision lane for the Niners War Room. It exists
because legacy model scores repeatedly produced implausible roster advice, and
patching that layer no longer deserves trust.

## Phase 0 Status

Phase 0 freezes legacy readiness and defines the v4 contract. It does not rebuild
formulas yet.

During the v4 rebuild freeze:

- legacy/current rankings may remain visible for inspection
- all legacy/current rankings are review-only
- no page may display decision-ready, roster-ready, draft-ready, or final-money
  ready from legacy logic
- old action labels are not trusted until v4 thresholds are defined

## Authoritative Inputs

1. Official league files and rules.
2. Sleeper roster, player, and pick IDs.
3. nflverse structured data.
4. Licensed structured/API data if the user approves it.
5. Agent research only as review evidence, never direct scoring.

## Scoring Profile

The v4 scoring profile is `lve_2026_rules_lock`.

| Component | Value |
| --- | ---: |
| Passing yards | 0.033333 per yard |
| Passing TD | 3 |
| Interception | -1 |
| Rushing yards | 0.1 per yard |
| Rushing TD | 4 |
| Receiving yards | 0.1 per yard |
| Receiving TD | 4 |
| Reception | 0 |
| Rushing/receiving first down | 0.4 |
| Fumble lost | -1 |

Kickers are excluded from player value and only used for roster mechanics if
needed.

## Output Lanes

### Dynasty Asset Value

Pure player value for this league format. It cannot include:

- league-rank top-five mechanics
- roster over-limit mechanics
- trade-market value
- manual overrides
- hidden defaults as evidence

### Roster Decision Value

My Team decision layer built from Dynasty Asset Value plus Niners roster context.
It must answer:

- safest 23 keepers
- required top-five release decision
- aggressive-smart shop/trade list
- review rows where data/confidence is not enough

### Required Top-Five Release Analysis

Operates only on the `Roster's League-Rank Top Five`.

Non-top-five drops are secondary context only. They cannot determine the required
top-five release candidate.

### Trade Context

Market/liquidity and model-vs-market opportunity. Trade context must not change
Dynasty Asset Value.

The desired posture is aggressive but smart: identify exploitable market
imbalance while avoiding forced certainty where the edge is not real.

### Draft Value

Available-player-only value for the mixed rookie/veteran draft. This lane cannot
include protected roster players by default.

Draft readiness stays blocked until official released veterans and the full
draftable pool are available.

### Confidence

Confidence controls language strength. Weak data produces review language, not
quietly buried player values.

## Sanity Beliefs

The first sanity-belief source is:

- `docs/model_v4/FOOTBALL_SANITY_BELIEFS.md`

Those beliefs are review-only guardrails. The model may disagree, but it must
show receipts and source evidence for why.

## Formula Work Preconditions

Do not rebuild formulas until these exist:

1. v4 feature/source contract
2. truth set player list
3. sanity fixtures generated from the football beliefs
4. receipt schema for v4 output lanes
5. scoring constants tested against the rules lock
6. legacy readiness freeze tests passing

The Phase 1A feature/source contract is:

- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.csv`

## Phase 0 Exit Criteria

- Rules lock exists.
- V4 roadmap exists.
- V4 spec exists.
- Football sanity beliefs exist.
- Legacy readiness is frozen.
- LVE scoring constants match the PDF lock.
- Static check passes.
