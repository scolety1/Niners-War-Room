# Rookie Pre-Draft As-Of Contract

Verdict: `YELLOW_ROOKIE_PRE_DRAFT_ASOF_CONTRACT_DEFINED_NO_BUILD`

## Scope

The future `Rookie Pre-Draft As-Of Coverage Builder V1` must isolate drafted-only review evidence and pre-draft feature timing. It must not approve Rookie Gate G, active rookie probabilities, fake T12/T24/T36 outputs, Draft Room wiring, Rankings wiring, or source-truth promotion.

## Required Outputs

- `rookie_pre_draft_asof_coverage_matrix.csv`
- `rookie_drafted_admission_manifest.csv`
- `combine_asof_coverage_report.md`
- `draft_capital_asof_report.md`
- `pre_draft_vs_post_draft_feature_report.md`
- `gate_e_f_g_non_activation_report.md`

## Required Coverage Fields

- `player_id`
- `draft_year`
- `position`
- `feature_family`
- `feature_value_present`
- `feature_source`
- `feature_as_of_timestamp`
- `pre_draft_anchor`
- `post_draft_only`
- `future_nfl_context`
- `positive_draft_picks_evidence`
- `identity_status`
- `missingness_rule`
- `as_of_safe_now`
- `replay_safe_now`
- `experiment_safe_now`
- `allowed_for_model_now`
- `allowed_for_training_now`
- `allowed_for_source_truth_now`

## Allowed Review Context

- Positive `draft_picks` evidence may support drafted-only review admission.
- Draft year, draft round, overall pick, and drafted team may be review context after admission.
- Combine data may be a candidate only with source, identity, coverage, and as-of proof.

## Blocked Context

- Missing draft capital is not confirmed UDFA.
- Fake round `8` is blocked.
- UDFA modeling remains blocked.
- CFBD model/training input remains blocked.
- Future NFL production is not a pre-draft feature.
- Roster, weekly roster, injury, practice, depth, snap, last active, player_stats, contract, schedule, and labels are not pre-draft features without a later explicit as-of gate.

## Gate Posture

- Gate E remains review/R&D only.
- Gate F remains partial display/review only where separately approved.
- Gate G remains blocked.

## Approval Boundary

The builder may produce review evidence. It may not approve experiments, model use, training use, source truth, rookie probabilities, Gate G, app wiring, Rankings behavior, hidden sort, trade value, pick value, or recommendations.
