# Validation Results

- Canonical HQ/tree preflight: pass.
- Current board and frozen comparator hashes: pass.
- HQ2 Git commit/tree/blob/SHA-256/size/schema/identity checks: pass.
- HQ2 independent semantic regeneration: 4,764 panel rows and 4 scorecard rows; pass.
- Deterministic ZIP inventory: 1,061 files / 40 unique hashes / 40 opened.
- Exactness lattice: 5,518 rows; zero unsupported exact admissions.
- Required exact-claim mutations: 14/14 detected.
- New focused suite: 21/21 passed.
- Canonical exact-replay focused suite: 32/32 passed.
- Metric reproduction: exact for the canonical proxy panel and HQ2 scorecard.
- Hermetic bootstrap controls: 13/13 passed.
- Existing security automation: 20/20 passed, including all five closed findings.
- Hermetic Python: 2,819 passed; no skip/xfail/xpass; exit 0.
- LocalData: `BLOCKED_MISSING_LOCAL_TEST_PACK`; native exit 4.
- Data Health passive-read slice: 59/59 passed.
- Changed-file Ruff: pass with zero findings.
- No-new-Ruff differential: 4,443 baseline / 4,443 current; changed files zero.
- Python compilation: pass.
- PowerShell parse: not applicable; no PowerShell file changed.
- `git diff --check`: pass.
- `git diff --cached --check`: pass.
- Board: 240 rows / governed SHA-256; pass.
- Frozen comparator: 924 rows / governed SHA-256; pass.
- Five opaque primary hashes: pass by hash-only verification.
- Persistent state: 14 files / 542,801 bytes / governed Digest V1; pass.
- Recovery state: 7 files / 172,878 bytes / governed Digest V1; pass.
- Retained backups/recovery snapshot: 5/5 and 1/1; pass.
- Protected/frozen changed paths: zero.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.

- `changed_score` — DETECTED: score mismatch
- `changed_rank` — DETECTED: rank mismatch
- `changed_player_id` — DETECTED: player ID authority mismatch
- `removed_as_of_date` — DETECTED: source as-of date is required
- `changed_model_identifier` — DETECTED: model identifier mismatch
- `missing_code_commit` — DETECTED: code commit missing or invalid
- `future_input` — DETECTED: future input detected
- `current_only_adp` — DETECTED: current-only ADP or market input prohibited
- `name_based_join` — DETECTED: name-based or non-authoritative join prohibited
- `incomplete_checkpoint_chain` — DETECTED: incomplete checkpoint chain
- `mutable_claimed_immutable` — DETECTED: mutable file cannot be claimed immutable
- `approximate_relabel` — DETECTED: approximate or review evidence cannot be relabeled exact
- `nondeterministic_order` — DETECTED: nondeterministic input ordering
- `silently_dropped_prediction` — DETECTED: silently dropped prediction

No result was inferred from an expected exit code. No security scan or LocalData
inspection was performed.
