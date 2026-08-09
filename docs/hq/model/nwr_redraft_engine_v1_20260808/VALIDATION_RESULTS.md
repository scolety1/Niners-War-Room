# Validation Results

- Focused redraft, page, and navigation suite: **37 passed**.
- Expanded impacted Redraft/Draft Cockpit/Player Compare/navigation suite: **65 passed**.
- Full repository suite: **3,204 passed, 71 skipped, 312 failed** in 514.85 seconds.
- That broad run predates the final governance-receipt hardening and is retained as context only;
  it is explicitly marked `source_match=false` and does not pass a promotion gate.
- The broad failures are dominated by clean-worktree omissions under ignored `local_exports`,
  historical tests that intentionally reject any dirty `app/` path, and pre-existing page-harness
  assumptions. They are not claimed as passes and prevent a full green-regression assertion.
- Ruff on changed Python files: **passed**.
- Source-fingerprint-matched responsive browser receipt: **27/27 passed after warm-up** with one
  Streamlit first-request route fallback recorded, one semantic h1 per warmed route, no root
  overflow, and no traceback.
- Player Compare's live selector could not be exercised in the clean worktree because its Finished
  V1 local player source is absent; source/static tests cover the selector and fail-closed branch.

Focused coverage includes all supported scoring components, K/DST override gating, explicit
current-evidence admission, stale/review-only/depth rejection, SHA-manifest tamper rejection,
profile CRUD/isolation, dynamic replacement, settings sensitivity, exact-ID comparison, Data
Health, and no page-open mutation.

Promotion remains blocked by G1 current-season source authority regardless of passing focused
software tests.
