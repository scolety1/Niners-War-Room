# Score Breakdown Feasibility

Date: 2026-06-30

Status: DEFER

Future candidate status: MODEL_FEATURE_CANDIDATE

## Summary

The current approved Dynasty Rankings source exposes `NWR Dynasty Score` and score/source metadata, but it does not expose approved component-level score rows, weights, weighted contribution amounts, or percent contribution fields. The app therefore adds only a safe placeholder `NWR Score Audit` preset and does not calculate or display invented score breakdown math.

## Approved Fields Available

- `nwr_rank`
- `nwr_dynasty_score`
- `score_status`
- `trust_status`
- `source_path`
- `source_column`
- `upstream_source_path`
- `upstream_source_column`
- `model_version`
- `lineage_class`
- `score_type`
- `score_as_of_date`
- `confidence_cap`
- `confidence_status`
- `allowed_use`
- `blocked_use`
- `candidate_evidence_fields_used`

## Missing For A Real Score Breakdown

- Approved score component names.
- Approved component weights.
- Approved raw component scores.
- Approved weighted contribution values.
- Approved percent contribution values.
- Approved per-player component receipt rows tied to the current active rankings output.

## Guardrails

- No model training, tuning, feature creation, or rank mutation was added.
- No Market/DynastyProcess, Outcome V2, injury context, CFBD, NFL usage, vendor, Gmail, or proxy evidence was used to explain or calculate score contribution.
- Missing score component data must display as unavailable or Not enough information, never zero.
- The placeholder preset is display/UX only and does not promote any review-only, display-only, or blocked source to model input.

## Verdict

`NWR Score Audit` is not ready as `SAFE_DISPLAY_CONTEXT` because the approved component/weight/contribution artifact does not exist. The appropriate next lane is a model-output receipt feasibility lane that can propose a governed component receipt artifact as a `MODEL_FEATURE_CANDIDATE` without changing rankings.
