# Sandbox Experiment Design Contract

Verdict: `YELLOW_SANDBOX_EXPERIMENT_DESIGN_CONTRACT_DEFINED_NO_RUN`

## Scope

The future `Sandbox Experiment Design V1` lane may draft a proposed sandbox experiment only after upstream substrate artifacts exist and pass a later HQ gate. It may not execute the experiment.

## Required Preconditions

- point-in-time snapshot manifest exists;
- prediction anchor contract exists;
- leakage diagnostics pass for the requested feature family;
- missingness and censoring policy exists;
- identity-safe join manifest exists;
- player_stats sidecar exists if labels or sidecar parity are in scope;
- label parity validation exists if sidecar comparison is in scope;
- rookie pre-draft as-of coverage exists if rookie features are in scope;
- blocked-source scan passes;
- non-activation report passes;
- later HQ gate explicitly allows design review.

## Required Design Fields

- `hypothesis`
- `population`
- `prediction_anchor`
- `eligible_feature_families`
- `excluded_feature_families`
- `feature_as_of_rule`
- `label_interaction_rule`
- `missingness_rule`
- `censoring_rule`
- `leakage_tests`
- `identity_exclusion_rule`
- `holdout_design`
- `negative_controls`
- `success_metrics`
- `failure_metrics`
- `production_activation_status`
- `execution_status`
- `approval_boundary`

## Mandatory Values

- `production_activation_status=NOT_APPROVED`
- `execution_status=NOT_RUN`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `app_wiring_allowed=false`
- `probability_creation_allowed=false`
- `gate_g_allowed=false`

## Exclusions

The design may not include:

- app behavior changes;
- runtime JSON changes;
- source-truth promotion;
- Rankings behavior;
- hidden sort;
- tiers;
- recommendations;
- trade value;
- pick value;
- active Outcome V2 probabilities;
- active rookie probabilities;
- Rookie Gate G approval;
- UDFA modeling;
- CFBD model/training input;
- `ff_rankings`.

## Approval Boundary

An experiment design packet is not an experiment approval. A separate later HQ gate is required before any sandbox or shadow experiment may run.
