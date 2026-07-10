# Formula Data Remaining Upgrade Action Plans

## red_zone_exact_receipts

- Current status: `NEEDS_SOURCE_GATE_REVIEW`
- Next action: Model v4 Red Zone Exact Receipt Regeneration Pilot V1 with a mandatory source/as-of gate and stop condition before any values are generated if unsafe.
- Why it matters: Could add high-value TD/opportunity context if source-traced and decision-date safe.
- Evidence: 234 candidate artifacts; candidate_source_needs_gate=116|partial_or_contextual=118
- Caveat: Candidate red-zone sidecar/schema artifacts exist, but source/as-of semantics are not proven enough for value regeneration.

## shadow_model_v2_metrics

- Current status: `MISSING_SOURCE`
- Next action: Shadow Metrics Scope Removal / Recovery Decision later; not worth prioritizing now.
- Why it matters: May support historical shadow-sidecar audit, but current exact board rebuild proved it is not required for current-board hash reproduction.
- Evidence: 80 candidate artifacts; context_only=80
- Caveat: Exact sidecar remains absent and is not needed for the review-only mart.

## historical_checkpoint_review_score

- Current status: `MISSING_RECEIPT`
- Next action: Historical Checkpoint Receipt Recovery Plan.
- Why it matters: Needed for exact Model v4 replay and historical score-chain audit.
- Evidence: 123 candidate artifacts; context_or_manifest_only=87|current_or_partial_equivalent=36
- Caveat: Current-board equivalents exist, but exact season-by-season receipts remain absent.

## historical_position_specific_review_score

- Current status: `MISSING_RECEIPT`
- Next action: Historical Checkpoint Receipt Recovery Plan.
- Why it matters: Needed for exact Model v4 position-layer replay and score decomposition.
- Evidence: 141 candidate artifacts; context_or_manifest_only=104|current_or_partial_equivalent=37
- Caveat: Partial equivalents exist, but exact season-by-season position receipts remain absent.

## age_lifecycle_sidecars

- Current status: `READY_TO_FREEZE`
- Next action: Age Lifecycle Sidecar Freeze / Validation V1.
- Why it matters: Likely useful for dynasty decay, sparse-history interpretation, and lifecycle guardrails.
- Evidence: 509 candidate artifacts; context_only=395|freeze_or_review_candidate=114
- Caveat: Age/lifecycle artifacts are freeze/review candidates and likely easier to validate than red-zone source semantics.

## point_in_time_injury_availability_gates

- Current status: `LEAKAGE_UNSAFE`
- Next action: Point-in-Time Injury Availability Gate Review V1.
- Why it matters: Could explain misses and low-games context, but high leakage risk without point-in-time evidence.
- Evidence: 80 candidate artifacts; source_gate_candidate=80
- Caveat: Availability/injury artifacts require historical as-of controls before formula testing.

## point_in_time_market_adp_gates

- Current status: `LEAKAGE_UNSAFE`
- Next action: Point-in-Time Market Gate Review V1.
- Why it matters: Market/ADP can be strong context, but requires historical point-in-time source control.
- Evidence: 80 candidate artifacts; source_gate_candidate=80
- Caveat: Market/ADP artifacts require point-in-time as-of gates and source review.
