# Validation results

Canonicalization readiness:
`YELLOW_NWR_ACCURACY_AUDIT_PUSHED_WITH_EXACT_REPLAY_BLOCKERS`.

- Controlling HQ/tree: exact.
- Original commit identities and parentage: exact.
- Rejected commit excluded from ancestry: pass.
- Original blocker reproduction before hardening: 8/8 survived.
- Original blocker closure after hardening: 8/8 detected.
- Expanded mutation sensitivity: 33/33 detected.
- Exact replay focused suite: 32 passed.
- Full Hermetic suite: 2,798 passed; exit 0.
- LocalData: `BLOCKED_MISSING_LOCAL_TEST_PACK`; native exit 4.
- Security regression automation: 20/20 pass; no scan run.
- Data Health passive-read regressions: pass.
- Same-checkout regeneration: 28/28 identical.
- Two independent clean checkouts: 28/28 identical.
- Input-order and environment isolation: 28/28 identical.
- Committed-packet reproduction: 28/28 identical.
- Mutable Git-state isolation: 28/28 identical.
- Metric reproduction and challenger disposition: exact.
- Candidate 1: blocked; Candidate 3: not created.
- Final disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.
- Python compilation and changed-file Ruff: pass.
- No-new-Ruff differential: pass at 4,443/4,443.
- New skip/xfail/xpass: zero.
- Git whitespace checks: pass.
- Current board: exact 240 rows and governed SHA-256.
- Frozen comparator: exact 924 rows and governed SHA-256.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.
- Five primary opaque hashes: exact.
- Persistent/recovery Digest V1: exact.
- Backups/recovery validation: 5/5 and 1/1 valid.
- Protected production path changes: zero.

Exact replay remains blocked at 0/5,518 complete rows; therefore the final
adoption is yellow even though assertion and reproducibility gates are green.
