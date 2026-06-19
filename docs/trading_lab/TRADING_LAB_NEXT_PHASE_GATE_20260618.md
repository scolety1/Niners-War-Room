# Trading Lab Next Phase Gate - 2026-06-18

This gate defines options only. It does not approve work.

## A. Human UI Review And Copy Polish

- Would do: run desktop review, refine copy, tune layout.
- Required approvals: user approval of review findings.
- Allowed paths: `docs/trading_lab/`, `src/trading_lab/`, `tests/test_trading_lab_*.py`, `app/pages/11_trade_lab.py`.
- Blocked paths: data, exports, generated artifacts, other lanes.
- Tests required: focused UI label/copy tests and Ruff.

## B. Real NWR Value Integration Proposal

- Would do: propose read-only adapter wiring for NWR private value.
- Required approvals: explicit source, fields, paths, validation, rollback.
- Allowed paths: proposal docs first; source only after approval.
- Blocked paths: direct cross-lane edits, generated outputs.
- Tests required: contract, provenance, missing-data, no-contamination tests.

## C. Public Fantasy Market Source Discovery

- Would do: research possible display-only market sources.
- Required approvals: source approval, attribution, access terms.
- Allowed paths: docs first.
- Blocked paths: scraping/API/data ingestion without explicit approval.
- Tests required: source policy and no-secret checks if code is later approved.

## D. Opponent Roster Context Manual-Entry MVP

- Would do: add manual in-memory opponent context inputs.
- Required approvals: UI behavior and no-persistence rules.
- Allowed paths: Trade Lab source/tests/page.
- Blocked paths: private league scraping, file writes, generated outputs.
- Tests required: no-persistence, missing-data, UI smoke tests.

## E. Saved Review Queue Design

- Would do: design persistence, storage, and export rules before implementation.
- Required approvals: storage path, file format, generated-output policy.
- Allowed paths: docs first.
- Blocked paths: writing files before approval.
- Tests required: persistence boundary and generated-artifact exclusion tests.

## F. Freeze And Handoff To Master

- Would do: final report and handoff only.
- Required approvals: Master handoff prompt.
- Allowed paths: docs only unless instructed.
- Blocked paths: code changes, deploy, generated outputs.
- Tests required: final validation and clean status.
