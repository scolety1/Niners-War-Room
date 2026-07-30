# Validation results

| validation | command | expected | observed | status | notes |
| --- | --- | --- | --- | --- | --- |
| builder internal invariants | python scripts/build_nwr_dual_lens_rc1_v1_20260729.py | exit 0 | exit 0 | PASS | Fixed source hashes, identities, temporal predicates, output schema. |
| external regression and independent review | pending | required mission matrix | pending | PENDING | Final validation evidence not supplied to builder. |

Required interpretation:

- Hermetic must exit 0.
- LocalData must return `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit 4.
- No provider is called and no new security scan is run.
- No new skip/xfail/xpass is allowed.
- The scheduled task must remain disabled.
- Production integration is absent, so dual-lens viewport controls are
  correctly `NOT_APPLICABLE_PRODUCTION_UI_NOT_INTEGRATED`, not falsely passed.
