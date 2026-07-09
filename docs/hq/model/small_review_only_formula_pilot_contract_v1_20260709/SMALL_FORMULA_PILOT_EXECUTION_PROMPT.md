# Future Execution Prompt: Small Review-Only Formula Pilot V1

Use the following prompt only after Master HQ explicitly approves execution.

```text
NWR MASTER CODEX REQUEST - Small Review-Only Formula Pilot V1

Master HQ accepts:

GREEN_SMALL_FORMULA_PILOT_CONTRACT_READY

Contract artifact:
docs/hq/model/small_review_only_formula_pilot_contract_v1_20260709/

Goal:
Run the first small review-only formula pilot using only the candidate definitions, input use gates, metrics, advancement rules, and stop conditions in the contract.

This is not Formula Gauntlet.
This is not a 100-candidate tournament.
This is not tuning.
This is not champion refinement.
This is not rankings integration.
This is not production/model-use.

Do not:
- run Formula Gauntlet tournaments
- run 100 candidates
- tune or optimize weights
- select production winners
- promote sources
- change rankings
- change app/runtime/model behavior
- claim production accuracy
- write into canonical local_exports
- push or merge

Canonical remote HQ:
origin/work/hq-parallel-control

Before starting:
1. git fetch origin
2. verify the current remote HEAD expected by Master HQ
3. if remote moved, inspect the range and stop if dangerous paths changed

Required prior artifacts:
1. docs/hq/model/small_review_only_formula_pilot_contract_v1_20260709/
2. docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/
3. docs/hq/master/age_lifecycle_master_review_v1_20260709/
4. docs/hq/master/model_v4_role_archetype_master_review_v1_20260709/
5. docs/hq/model/model_v4_confidence_cap_component_signal_test_v1_20260709/

Required tasks:
1. Reproduce the review-only Formula Data Mart.
2. Reproduce the PYF baseline.
3. Execute only the allowed candidates in SMALL_FORMULA_PILOT_ALLOWED_CANDIDATES.csv.
4. Use only allowed inputs from SMALL_FORMULA_PILOT_INPUT_USE_GATE.md.
5. Produce all metrics required by SMALL_FORMULA_PILOT_METRICS_CONTRACT.csv.
6. Apply advancement rules from SMALL_FORMULA_PILOT_ADVANCEMENT_RULES.md.
7. Stop on any stop condition in SMALL_FORMULA_PILOT_STOP_CONDITIONS.md.
8. Preserve all current gates.

Required outputs:
- pilot report
- candidate metrics scorecard
- PYF comparison
- sparse-history / low-games harm review
- prior-decline review
- age/lifecycle slice review
- role-archetype slice review
- coverage/missingness
- source/use-gate and leakage/as-of validation
- blockers/caveats

Final answer must state:
- verdict
- rows tested
- candidates tested
- whether any candidate is promising review-only
- PYF comparison result
- sparse-history and low-games harm
- whether Formula Gauntlet remains blocked
- whether production/model-use remains blocked
- whether rankings integration remains blocked
- local commit hash if committed
```
