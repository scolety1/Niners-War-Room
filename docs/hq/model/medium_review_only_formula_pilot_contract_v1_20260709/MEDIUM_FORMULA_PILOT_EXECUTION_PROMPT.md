# Future Execution Prompt: Medium Review-Only Formula Pilot V1

Use the following prompt only after Master HQ explicitly approves execution.

```text
NWR MASTER CODEX REQUEST - Medium Review-Only Formula Pilot V1

Master HQ accepts:

GREEN_MEDIUM_FORMULA_PILOT_CONTRACT_READY

Contract artifact:
docs/hq/model/medium_review_only_formula_pilot_contract_v1_20260709/

Goal:
Run the Medium Review-Only Formula Pilot using exactly the fixed candidates, metrics, input use gates, advancement rules, and stop conditions in the contract.

This is not Formula Gauntlet.
This is not a 100-candidate run.
This is not champion refinement.
This is not dynamic tuning.
This is not production/model-use.
This is not rankings integration.

Do not:
- run more than the contract candidates
- add candidates after seeing results
- optimize weights dynamically
- train ML models
- select winners or champions
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
1. docs/hq/model/medium_review_only_formula_pilot_contract_v1_20260709/
2. docs/hq/model/small_review_only_formula_pilot_v1_20260709/
3. docs/hq/model/small_review_only_formula_pilot_contract_v1_20260709/
4. docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/
5. docs/hq/master/age_lifecycle_master_review_v1_20260709/
6. docs/hq/master/model_v4_role_archetype_master_review_v1_20260709/

Required tasks:
1. Rebuild or assemble the review-only Formula Data Mart.
2. Reproduce PYF baseline metrics.
3. Execute exactly the candidates in MEDIUM_FORMULA_PILOT_ALLOWED_CANDIDATES.csv.
4. Use only inputs allowed by MEDIUM_FORMULA_PILOT_INPUT_USE_GATE.md.
5. Produce all metrics in MEDIUM_FORMULA_PILOT_METRICS_CONTRACT.csv.
6. Apply advancement rules and stop conditions exactly.
7. Preserve all current gates.

Required outputs:
- medium pilot report
- candidate metrics scorecard
- PYF comparison
- position results
- season stability and leave-one-season-out directional checks if feasible
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
- best review-only candidate
- PYF comparison result
- sparse-history / low-games harm
- season stability
- whether Formula Gauntlet remains blocked
- whether production/model-use remains blocked
- whether rankings integration remains blocked
- local commit hash if committed
```
