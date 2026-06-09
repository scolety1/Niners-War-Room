# Model v4 Formula Lane Architecture

Created: 2026-05-16

This document defines the Model v4 scoring lanes before any player formulas are
implemented. It is an architecture contract, not a formula implementation. It
does not change player values, active rankings, app readiness gates, or legacy
model outputs.

Authoritative context:

- `docs/model_v4/PHASE_1_CHECKPOINT.md`
- `docs/model_v4/PHASE_2_CHECKPOINT.md`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.md`
- `docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv`
- `docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`

## Global Separation Rules

These rules apply to every lane:

1. League rank cannot affect Dynasty Asset Value.
2. Market cannot affect private football value.
3. Required top-five release logic is roster-rule context only.
4. Draftable-player logic stays separate from rostered-player value.
5. Route participation, routes run, TPRR, and YPRR remain unavailable until a
   legal structured source is approved.
6. Snap share can be a proxy role input, but it cannot masquerade as route
   participation.
7. Missing or neutral defaults must be visible in receipts and source coverage.
8. No lane can unlock decision-ready status until the formal gates pass.

## Lane Summary

| Lane | Question Answered | Primary Output |
| --- | --- | --- |
| Dynasty Asset Value | How valuable is this player as a dynasty football asset? | `dynasty_asset_value` |
| Roster Decision Value | What should the Niners do with this rostered player? | `roster_decision_value` |
| Required Top-Five Release Pain | Which locked top-five release is least painful? | `release_pain` |
| Trade / Market Context | Where does model value disagree with market/liquidity? | `model_vs_market_context` |
| Draft Value | Who is the best available draftable player? | `draft_value` |
| Confidence | How strongly should any score be trusted? | `confidence_label` |

## Lane: Dynasty Asset Value

### Purpose

Measure the player's private football value for this 10-team, 1QB, no-PPR,
no-TE-premium dynasty league. This is the core football-value lane and must be
independent from roster rules, trade liquidity, and draft-room availability.

### Allowed Inputs

- imported nflverse production
- rushing and receiving first downs
- targets and carries
- derived target share and carry share
- derived red-zone and goal-line usage with confidence penalty
- snap share as proxy role evidence with confidence penalty
- recomputed raw-stat projections with explicit projection status
- age/bio and position-specific dropoff context
- identity confidence
- young-player draft capital and prospect context when lifecycle-eligible

### Forbidden Inputs

- league rank
- Roster's League-Rank Top Five status
- trade market or liquidity
- model-vs-market edge
- roster spot pressure
- draftable-player availability
- manual agent player-stat tables
- restricted route data
- unavailable route participation, routes run, TPRR, or YPRR
- supplied non-LVE fantasy projection point totals

### Output Fields

- `dynasty_asset_value`
- `dynasty_asset_rank`
- `position_asset_rank`
- `asset_lifecycle`
- `component_scores`
- `confidence_label`
- `warning_summary`

### Receipt Requirements

Receipts must show production, first-down scoring fit, usage/opportunity,
snap/proxy role, projection, age/dropoff, young-player prior when applicable,
confidence, and unavailable sections. Market context and league-rank rule
context may appear beside the score, but never as private-value contributions.

### Sanity Fixtures That Apply

- `rb_elite_order_001`
- `rb_bijan_rb1_002`
- `rb_gibbs_near_bijan_003`
- `rb_achane_core_004`
- `wr_elite_tier_001`
- `wr_jsn_top_tier_002`
- `wr_jsn_vs_tee_003`
- `young_btj_luther_001`
- `young_kaleb_veterans_003`
- `age_wr_vs_rb_001`
- `qb_1qb_suppression_001`
- `te_no_premium_001`

## Lane: Roster Decision Value

### Purpose

Translate Dynasty Asset Value into Niners pre-declaration roster context. This
lane can help compare holds, shop candidates, roster-risk players, and forced
release pressure, but it cannot pretend a review-only model is decision-ready.

### Allowed Inputs

- Dynasty Asset Value
- confidence label and source warnings
- Niners roster membership
- Niners roster size and keeper limit
- official roster rank context
- Roster's League-Rank Top Five status as rule context
- current roster construction and positional depth
- trade/market context as a separate shop-context signal only

### Forbidden Inputs

- league rank as player quality
- market as private football value
- non-top-five players as Required Top-Five Release Slot candidates
- draftable-player availability
- legacy labels as trusted decisions while v4 is review-only

### Output Fields

- `roster_decision_value`
- `roster_decision_section`
- `roster_action_review_label`
- `keep_priority`
- `cut_risk`
- `shop_context`
- `confidence_label`
- `warning_summary`

### Receipt Requirements

Receipts must show Dynasty Asset Value drivers first, then roster-rule context,
confidence, market context if relevant, and the exact reason a label is
review-only. Top-five rule language must be separate from model recommendation.

### Sanity Fixtures That Apply

- `rb_achane_core_004`
- `young_luther_chase_brown_002`
- `young_kaleb_veterans_003`
- `age_veteran_receipts_002`
- `league_rank_context_001`
- `forced_release_pool_001`
- `source_gap_control_001`

## Lane: Required Top-Five Release Pain

### Purpose

Evaluate the required release from the locked Niners Roster's League-Rank Top
Five. This lane answers only: if the league rule forces one top-five release,
which top-five player is the least painful release?

### Allowed Inputs

- locked Niners Roster's League-Rank Top Five candidate pool
- Dynasty Asset Value
- Roster Decision Value
- confidence label and source warnings
- lifecycle and age/dropoff context
- positional replacement context
- roster construction context

### Forbidden Inputs

- players outside the locked top-five candidate pool as primary candidates
- league rank as player quality
- market as private football value
- easy non-top-five cuts as the required release answer
- draftable-player availability

### Output Fields

- `top_five_rule_status`
- `required_release_candidate_pool`
- `release_pain`
- `release_pain_rank`
- `default_release_review_candidate`
- `release_pain_explanation`
- `confidence_label`

### Receipt Requirements

Receipts must show the top-five candidate pool, league-rank rule context,
Dynasty Asset Value, Roster Decision Value, release-pain calculation inputs,
confidence, and why non-top-five drops are secondary context only.

### Sanity Fixtures That Apply

- `league_rank_context_001`
- `forced_release_pool_001`
- `rb_achane_core_004`
- `young_luther_chase_brown_002`

## Lane: Trade / Market Context

### Purpose

Find possible trade edges by comparing private football value with external
trade market/liquidity context. This lane is for opportunity discovery, not for
changing private football value.

### Allowed Inputs

- Dynasty Asset Value
- market source and market date
- market/liquidity value
- model-vs-market gap
- roster pressure context
- confidence label and source warnings
- source freshness and missing-market status

### Forbidden Inputs

- market as Dynasty Asset Value contribution
- missing or neutral market values as real edge
- league rank as player quality
- acceptance likelihood without a sourced or explicitly modeled basis
- private value changes from market changes

### Output Fields

- `trade_market_value`
- `market_source_status`
- `model_vs_market_context`
- `market_edge_review_label`
- `liquidity_warning`
- `trade_context_confidence`

### Receipt Requirements

Receipts must show private value and market context as separate sections. Missing
market values must display as missing and cannot create fake edge.

### Sanity Fixtures That Apply

- `market_isolation_001`
- `market_missing_edge_002`
- `source_gap_control_001`

## Lane: Draft Value

### Purpose

Rank only actual draftable players for the offline mixed rookie/veteran draft.
This lane is separate from rostered-player value and cannot include protected
roster players unless a manual draftable override exists.

### Allowed Inputs

- Dynasty Asset Value for available veterans
- rookie/prospect model inputs for incoming rookies
- young-player prior for eligible young players
- draftable-pool source status
- why-available field
- projection and confidence context
- market context only as separate trade/draft context

### Forbidden Inputs

- protected roster players unless manually added as review-needed draftable
- official roster rank as player quality
- league-rank top-five rule mechanics
- market as private football value
- unavailable route metrics
- fixture/demo draft pools as normal data

### Output Fields

- `draft_value`
- `draft_rank`
- `asset_type`
- `asset_lifecycle`
- `why_available`
- `availability_status`
- `draft_confidence_label`
- `draft_warning_summary`

### Receipt Requirements

Receipts must show why the player is available, lifecycle, model value drivers,
rookie/prospect inputs where applicable, confidence, and unavailable data
sections. Draft board receipts must clearly say when released veterans are not
loaded yet.

### Sanity Fixtures That Apply

- `rb_jeanty_young_prior_006`
- `incoming_rookie_lane_001`
- `young_lifecycle_004`
- `source_gap_control_001`

## Lane: Confidence

### Purpose

Control how strongly the app may describe any lane output. Confidence is not a
player-value booster. It is a trust label and warning system.

### Allowed Inputs

- identity confidence
- source coverage
- stale or missing production indicators
- projection source status
- route/participation availability
- injury/context source quality
- market source status
- young-prior source status
- fixture review status
- receipt completeness

### Forbidden Inputs

- confidence as a direct private-value bonus
- unsourced healthy injury rows as confidence boosts
- local baseline projection as independent forecast evidence
- missing market as trade edge
- hidden neutral defaults

### Output Fields

- `confidence_score`
- `confidence_label`
- `confidence_tier`
- `confidence_penalty_reasons`
- `blocking_source_gaps`
- `review_warning_summary`

### Receipt Requirements

Receipts must explain why confidence is strong, usable, review, weak, or blocked.
They must show accepted gaps and retained penalties rather than pretending the
data exists.

### Sanity Fixtures That Apply

- `source_gap_control_001`
- `route_unavailable_001`
- every fixture with high review severity

## Phase 3A Exit Criteria

Phase 3A is complete when:

- all six lanes have purpose, allowed inputs, forbidden inputs, output fields,
  receipt requirements, and applicable fixtures
- lane separation tests pass
- no formulas are implemented
- no active rankings are changed
- no readiness gates are unlocked
