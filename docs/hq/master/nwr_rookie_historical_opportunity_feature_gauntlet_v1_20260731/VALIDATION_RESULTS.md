# Validation Results

- Source/schema and immutable receipt checks: PASS
- Exact identity contract: PASS; feature-panel exact-ID rate `1.0`
- Temporal leakage and chronological folds: PASS
- Outcome scoring/replacement/maturity checks: PASS
- Feature definitions, semantic labels, and missingness: PASS
- Same-row comparisons: PASS
- Metrics/promotion gates: PASS
- Mutation sensitivity: 20/20 detected
- Python compilation / changed-file Ruff / Git whitespace: validation command required
- Existing security regression controls: included only through repository Hermetic gate; no new security scan
- Canonical Hermetic before: `FAIL: bootstrap 13/13; security 20/20; pytest 2950 passed, 3 failed, 15 errors; EXIT 1`
- Candidate Hermetic after: `FAIL: bootstrap 13/13; security 20/20; pytest 2965 passed, 3 failed, 15 errors; EXIT 1; exact baseline signature`
- LocalData: `BLOCKED_MISSING_LOCAL_TEST_PACK; EXIT 4`
- Data Health: passive reads only
- Provider calls: `NONE`
- New skip/xfail/xpass: `NONE`
- Model V4 / 2026 board / Finished V1 / Outcome V3 / Trading Lab / active pack change: `NONE`
