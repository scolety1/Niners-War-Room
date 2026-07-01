# Parallel Builder Lane Plan

Verdict: `YELLOW_PARALLEL_BUILDER_LANES_DEFINED_NO_BUILD`

This plan defines future builder lanes only. It does not run those lanes and does not create any substrate artifact.

## Lane 1: Point-in-Time Snapshot Manifest Builder V1

Owning lane: `Data Hygiene`

Purpose: build tracked point-in-time and as-of feasibility manifests for NFLVerse-derived feature families.

Required future outputs:

- `point_in_time_snapshot_manifest.csv`
- `prediction_anchor_contract.md`
- `feature_replay_window_matrix.csv`
- `identity_safe_join_manifest.csv`
- `non_activation_guardrail_report.md`

Minimum requirements:

- define prediction anchors before row construction;
- record source snapshot id, source extraction timestamp, and feature as-of timestamp;
- preserve season/week/game anchors separately;
- exclude unresolved identity rows;
- keep missing values as `Not enough information`;
- report leakage status by feature family;
- keep `safe_for_replay_now=false` and `safe_for_experiment_now=false` unless a later HQ gate explicitly changes them.

No replay, experiment, model, training, or source-truth approval is granted by this lane.

## Lane 2: NFLVerse Player Stats Sidecar Builder V1

Owning lane: `Outcome Lane`

Purpose: build row-level review-only NFLVerse `player_stats` sidecar rows where tracked safe data and source manifests support it.

Required future outputs:

- `player_stats_sidecar_rows.csv`
- `player_stats_sidecar_schema_manifest.md`
- `player_stats_sidecar_coverage_report.md`
- `identity_overlap_report.md`
- `non_label_truth_report.md`

Minimum requirements:

- build rows at player-season-week-stat grain;
- attach source snapshot and extraction timestamp;
- keep missing player_stats rows as `Not enough information`, not zero;
- treat existing labels as evaluation targets only;
- report row counts by season and position;
- exclude unresolved identity rows;
- preserve censoring states for incomplete horizons.

This lane does not promote NFLVerse `player_stats` to label truth, model input, training truth, or source truth.

## Lane 3: Label Parity Validator V1

Owning lane: `Outcome Lane or Policy Lane`

Purpose: compare the review-only player_stats sidecar to existing labels after the sidecar exists.

Required future outputs:

- `label_parity_validation_report.md`
- `label_parity_validation_matrix.csv`
- `label_parity_mismatch_taxonomy.md`
- `censoring_parity_report.md`
- `no_label_truth_promotion_report.md`

Minimum requirements:

- compute matched players and unmatched label/sidecar rows;
- report identity match rate;
- report scoring parity and first-down scoring status where relevant;
- report censoring parity;
- classify mismatch categories;
- define acceptance thresholds for later HQ review;
- keep labels out of model input features.

This lane does not promote labels, change probabilities, or approve model/training/source-truth use.

## Lane 4: Rookie Pre-Draft As-Of Coverage Builder V1

Owning lane: `Rookie Outcome Lane`

Purpose: build drafted-only pre-draft feature coverage and as-of audit evidence.

Required future outputs:

- `rookie_pre_draft_asof_coverage_matrix.csv`
- `rookie_drafted_admission_manifest.csv`
- `combine_asof_coverage_report.md`
- `draft_capital_asof_report.md`
- `gate_e_f_g_non_activation_report.md`

Minimum requirements:

- use positive `draft_picks` evidence for drafted-only review admission only;
- separate pre-draft, post-draft-only, and future-NFL-production fields;
- keep missing draft capital from becoming confirmed UDFA;
- keep future roster, injury, depth, snaps, player_stats, contract, and schedule fields out of pre-draft features unless a future as-of gate explicitly approves;
- preserve Gate E as review/R&D only;
- preserve Gate F as partial display/review only where separately approved;
- preserve Gate G as blocked.

This lane does not approve rookie probabilities, fake T12/T24/T36 outputs, Gate G, or app wiring.

## Lane 5: Sandbox Experiment Design V1

Owning lane: `Policy/HQ`

Purpose: design a future sandbox experiment only after the builder outputs exist and pass a later HQ gate.

Required future outputs:

- `sandbox_experiment_design_spec.md`
- `eligible_feature_family_review_matrix.csv`
- `excluded_feature_family_report.md`
- `experiment_non_activation_guardrail_report.md`
- `hq_gate_request.md`

Minimum requirements:

- consume only built and validated substrate artifacts;
- define hypotheses, anchors, holdouts, leakage tests, missingness tests, and label interaction tests;
- keep execution status as `NOT_RUN`;
- keep experiment approval false until a later HQ gate;
- keep production model use, training, source truth, app wiring, probabilities, and Gate G blocked.

This lane may design a future request. It may not execute an experiment.

## Sequencing

1. Build point-in-time manifest evidence first.
2. Build row-level player_stats sidecar only with tracked safe data and source manifests.
3. Run label parity only after sidecar rows exist.
4. Build rookie pre-draft as-of coverage separately from current NFL production context.
5. Draft sandbox experiment design only after upstream outputs exist and pass HQ review.
