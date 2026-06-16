# Build Sprint 5AB: Expanded Package Adversarial Audit

## Scope

Sprint 5AB adversarially audits the expanded internal validation and calibration-readiness work for leakage, output risk, app/ranking isolation risk, metadata gaps, and governance gaps.

This sprint did not train new models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote/release model artifacts.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5ab_expanded_package_adversarial_audit/`

Created files:

- `expanded_output_risk_audit.csv`
- `expanded_forbidden_feature_audit.csv`
- `expanded_app_isolation_audit.csv`
- `expanded_metadata_audit.csv`
- `expanded_governance_audit.csv`
- `expanded_audit_findings.csv`
- `README_SPRINT_5AB.md`

## Audit Findings

No blocker was found.

Findings:

- Expanded validation outputs are aggregate-only.
- Forbidden feature scan has 0 blockers.
- No active app/ranking references to expanded internal validation outputs were found.
- Metadata contract is complete.
- Governance flags remain restrictive.
- Production/app modeling remains blocked.

## Output-Risk Audit

Output-risk audit passed.

Verified absent from expanded internal validation outputs:

- `player_id`
- `player_name`
- row ID
- per-player probability
- sortable score
- app probability column
- app-compatible probability table
- production model artifact
- ranking/sort output

The metadata file contains run and governance metadata only. It does not contain player-level predictions or app-readable probability outputs.

## Forbidden-Feature Audit

Forbidden-feature audit passed with 0 blockers.

The 5Z feature scan covered all 17 package features, including encoded position features. No blocked fragments were detected.

Still blocked:

- ADP/rankings/projections.
- Public fantasy totals as labels.
- Market/trade values.
- Prior fantasy draft history.
- Legacy `private_score`.
- RotoWire projections/rankings/outlooks/values.
- Same-season final stats as features.
- Target labels as features.
- Label supplement sources as prediction features.
- Old ambiguous feature names.

## App Isolation

Active app/ranking isolation scan passed.

No active app or ranking service/script references were found for:

- Sprint 5Z outputs.
- Sprint 5AA outputs.
- Expanded internal validation outputs.
- Expanded calibration gate outputs.
- Internal logistic package outputs.

An unrelated, pre-existing untracked `outcome_column_package_service.py` scaffold contains probability-package terms. It was not touched, staged, or used by this sprint and is not an active app/ranking integration from the expanded internal package.

## Metadata And Governance

Metadata audit passed.

Required fields present:

- `run_id`
- feature and label schema versions
- benchmark and component policy IDs
- source manifest version
- train/validation/test seasons
- row family
- outcomes
- feature list
- random seed
- package timestamp
- code version/git commit

Required governance flags:

- `renamed_feature_schema_required=true`
- `feature_lineage_required=true`
- `forbidden_feature_scan_passed=true`
- `player_output_block=true`
- `app_output_block=true`
- `promotion_allowed=false`
- `calibration_allowed=false`
- `production_artifact=false`

## Fixes Made

No code fixes were required.

The local 5Z forbidden-feature scan export was tightened before this audit so it matches the full encoded package feature list, including `position_QB`, `position_RB`, `position_TE`, and `position_WR`. This was a local audit-output correction only, not an app/model behavior change.

## Verdict

`EXPANDED_PACKAGE_AUDIT_PASS`

The expanded internal validation/calibration-readiness package is safe to hand off as internal-only. Production/app modeling remains blocked.

## Confirmed Non-Actions

- No app percentage values created.
- No calibrated probabilities created.
- No public/player-facing probabilities created.
- No rankings created.
- No push or deploy occurred.
- No active app/ranking logic modified.
- No promoted or released model artifact.
