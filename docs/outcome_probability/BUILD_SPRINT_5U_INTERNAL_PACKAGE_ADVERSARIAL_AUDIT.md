# Build Sprint 5U: Internal Package Adversarial Audit

Status: `INTERNAL_PACKAGE_AUDIT_PASS_WITH_FIXES`

Sprint 5U adversarially audited the Sprint 5T internal logistic package for leakage, hidden player-level outputs, app-output risk, metadata gaps, reproducibility issues, and accidental promotion paths.

This sprint did not train new calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote/release a model artifact.

## Scope

Audited:

- `src/services/nwr_outcome_internal_model_package_service.py`
- `tests/test_nwr_outcome_internal_model_package_service.py`
- Sprint 5T local package exports under:
  - `local_exports/outcome_probability/sprint_5t_internal_logistic_package/`
- App/ranking isolation paths:
  - `app/`
  - `pages/`
  - `streamlit_app.py`

## Finding Summary

| Finding | Severity | Status | Summary |
| --- | --- | --- | --- |
| `5U-001` | medium | `fixed_in_5u` | Original 5T metadata lacked explicit random seed/determinism, package timestamp, and code git hash fields. |
| `5U-002` | low | `pass` | No player identifiers or per-player probability headers in diagnostic CSV exports. |
| `5U-003` | low | `pass` | App/ranking files do not import the internal package service or 5T outputs. |
| `5U-004` | low | `pass` | Forbidden feature fragments are covered by scan and tests. |
| `5U-005` | low | `pass` | `next_year_starter` and non-same-year paths remain blocked. |

## Fixes Made

Sprint 5U fixed the reproducibility metadata gap in code and tests.

Added required metadata fields for future internal package exports:

- `random_seed`
- `package_created_at_utc`
- `code_version_git_commit`

The package uses deterministic gradient descent, so the random seed value is:

- `not_used_deterministic_gradient_descent`

The metadata validator now requires:

- `feature_schema_version`
- `feature_lineage_required=true`
- `renamed_feature_schema_required=true`
- `forbidden_feature_scan_passed=true`
- `promotion_allowed=false`
- `player_output_block=true`
- `app_output_block=true`
- `calibration_allowed=false`
- `production_artifact=false`
- `random_seed`
- `package_created_at_utc`
- `code_version_git_commit`

Added test coverage for:

- missing metadata blocking the package contract
- bad governance flags blocking the package contract
- app/ranking modules not importing the internal package service

The original Sprint 5T local export was not regenerated during this audit sprint. The code and tests now enforce the added metadata for future package exports.

## Output-Risk Audit

Result: `pass`

Checked diagnostic CSV headers for:

- `player_id`
- `player_name`
- `row_id`
- `predicted_probability`
- `player_probability`
- sortable score fields

No forbidden headers were found in Sprint 5T diagnostic exports.

Artifact scan result:

- no `*.pkl`
- no `*.pickle`
- no `*.joblib`
- no production model artifact
- no `player_level_predictions.csv`
- no `app_probability_table.csv`
- no ranking artifact

The only JSON file in the Sprint 5T local package is metadata.

## Metadata Enforcement Audit

Result: `pass_with_fix`

Existing Sprint 5T metadata already included:

- `run_id`
- `source_manifest_version`
- `feature_schema_version`
- `label_schema_version`
- `component_policy_id`
- `benchmark_policy_id`
- `training_seasons`
- `test_seasons`
- `row_family`
- `outcomes`
- `feature_list`
- output block flags
- promotion/calibration/production artifact flags

Missing from the original local export, then fixed in code/tests:

- `random_seed`
- `package_created_at_utc`
- `code_version_git_commit`

## Forbidden-Feature Adversarial Audit

Result: `pass`

Adversarial cases covered:

- old ambiguous feature names:
  - `prior_nwr_ppg`
  - `prior_nwr_finish_rank`
  - old `prior_*` production names replaced in Sprint 5R
- same-season stats
- target labels as features
- public fantasy totals
- ADP
- projections
- rankings
- market values
- trade values
- prior fantasy draft history
- legacy `private_score`
- label supplement sources as prediction features

The package scan and tests block these feature names/fragments.

## Blocked-Outcome Audit

Result: `pass`

Still blocked:

- `next_year_starter`
- multi-year outcomes
- hazard windows
- calibrated outputs
- app/player-facing outputs

The package service rejects `next_year_starter` and only allows same-year outcomes.

## App Isolation Audit

Result: `pass`

Searched app/ranking surfaces for accidental references to:

- `nwr_outcome_internal_model_package_service`
- `sprint_5t_internal_logistic_package`
- `internal_logistic_package_metadata`

No app/ranking import or consumption path was found.

## Reproducibility Audit

Result: `pass_with_fix`

Current code contract now requires:

- run id
- source manifest version
- feature schema version
- label schema version
- component policy id
- benchmark policy id
- train/test seasons
- row family
- outcome list
- feature list
- random seed/determinism marker
- package timestamp
- git commit hash when available

The package remains internal-only and aggregate-only.

## Local Outputs

Sprint 5U wrote local-only exports under:

`local_exports/outcome_probability/sprint_5u_internal_package_adversarial_audit/`

Created outputs:

- `output_risk_audit.csv`
- `metadata_enforcement_audit.csv`
- `forbidden_feature_adversarial_cases.csv`
- `blocked_outcome_audit.csv`
- `app_isolation_audit.csv`
- `reproducibility_audit.csv`
- `audit_findings.csv`
- `README_SPRINT_5U.md`

## Verdict

Verdict: `INTERNAL_PACKAGE_AUDIT_PASS_WITH_FIXES`

Internal work may continue under the Sprint 5S gate after the Sprint 5U metadata fixes. Production/app modeling remains blocked.

## Remaining Blockers Before App-Facing Calibrated Probabilities

- More seasons beyond 2023/2024.
- True calibration holdout.
- Mature next-year/multi-year labels or explicit exclusion.
- Confidence gate.
- App display gate.
- Final leakage audit.
- Model card/release policy.
- Explicit HQ approval.

## Safety Confirmation

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
