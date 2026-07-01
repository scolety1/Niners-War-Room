# Guardrail Report

Verdict: `GREEN_GUARDRAILS_PASSED_FOR_GENERATED_ARTIFACTS`

- Candidate-only output: confirmed.
- Production approval: false for all candidates.
- Production formula changes: none.
- App/model/rank/source-truth/runtime changes: none by this generator.
- Rankings, hidden sort, recommendations: none.
- Market/vendor/rank/projection fields as source truth: absent.
- Routes/TPRR/YPRR/route proxies: absent.
- Ambiguous `rz_att`: absent.
- Current-only roster/status/injury/depth/schedule context as historical feature data: absent.
- Missing values forced to zero by this generator: no.
- Candidate count: 12 of max 40.

## Validation Evidence

- Focused artifact/source tests: `9 passed`.
- Focused outcome/scoring tests: `44 passed`.
- `git diff --check`: passed.
- `git diff --cached --check`: passed after staging.
- Protected path scan: no matches.
- Forbidden raw/shared/cache/local/secrets path scan: no matches.
- Secret content scan: no matches.
- Approval invariant scan: no matches.
- CSV schema/readability validation: passed.
- Core usage/red-zone parquet sample validation: passed.
