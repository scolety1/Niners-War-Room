# Validation results

- Starting HQ/tree: PASS.
- Prior logo lane review: PASS.
- Route inventory: 60 of 60 live.
- Visible viewport checks: 76 of 76 no Page Not Found, exception, or overflow.
- Repaired root: PASS at four viewports; one H1 and six primary links.
- Candidate rankings: PASS, 240 rows at desktop and 320px.
- Ordered top five: PASS through exact loader.
- Focused root/navigation tests: 24 passed.
- Hermetic: PASS, 13 bootstrap, 20 controls, 2,736 Python, exit 0.
- LocalData: BLOCKED_MISSING_LOCAL_TEST_PACK, exit 4.
- Python compilation: PASS.
- PowerShell parse: 25 files, zero errors.
- Changed-file Ruff: PASS.
- No-new-Ruff: PASS, 4,443 baseline and candidate with identical rules.
- Security regressions: PASS; no new scan.
- Data Health, CSV safety, trust, UI, routes, rankings, compare, trading, draft,
  launcher, ownership, and persistence: PASS in Hermetic.
- Protected/frozen and security automation: no change.
- Five primary CSV hashes: exact at every checkpoint.
- Persistent product data: unchanged at 14 files / 542,801 bytes / aggregate
  SHA-256 626ff6f6e78c71e8a74e9ee159f23d92a7a117de8f739a3a256fe9bbe843135f.
- Recovery quarantine: unchanged at 7 files / 172,878 bytes / aggregate
  SHA-256 ded770c1b4ad76ec6ee263d3ec976d6cb69102536a6fa76cd79ded1d9fe1f5a9.
- Backups: five of five valid; Data Health recovery: one of one valid.
- Port 8520: free after final Stop.
- Git diff checks: PASS.
- Push: NOT PERFORMED.
