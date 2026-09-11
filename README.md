# Niners War Room

> **LEGACY NOTICE (2026-09-10):** This document describes the original
> Streamlit/CSV-pack V1 dynasty prototype. The live product today is a
> React/Tauri desktop app with a real, live-Sleeper-integrated in-season
> Redraft workspace (`desktop/apps/redraft`) that this document does not
> mention at all. Kept unedited below as the accurate historical record
> for that original product line, which still exists in this repo. The
> current, accurate architecture for the whole product (including the
> live desktop app) is `PRODUCT_ARCHITECTURE.md`.

Niners War Room is a private, local-first dynasty decision-support application. V1
uses admitted repository fixtures and optional repository-local data only. It does
not require provider credentials, private league data, `LocalData`, or a live API to
start.

## Runtime and installation

Python 3.12 or newer is required. A conventional environment can be prepared with:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . pytest ruff
```

The repository verification scripts use `uv` in offline, no-project mode so their
dependency resolution is isolated from a developer virtual environment.

## Hermetic bootstrap and verification

Create the deterministic public test pack:

```powershell
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\bootstrap-hermetic-test-pack.ps1 -RepoRoot $PWD -OutputRoot .\local_exports\hermetic_test_pack_v1 -Clean
```

Run the canonical V1 gate:

```powershell
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\verify-repository.ps1 -Tier Hermetic -RepoRoot $PWD
```

`Hermetic` must exit `0`. It runs the bootstrap controls, focused security controls,
the Hermetic Python collection with skips/xfails/xpasses prohibited, and the owned
Ruff check.

`LocalData` is a separate, non-waivable gate:

```powershell
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\verify-repository.ps1 -Tier LocalData -RepoRoot $PWD
```

When the private local test pack is unavailable, the required result is
`BLOCKED_MISSING_LOCAL_TEST_PACK` with exit code `4`. That result is neither a pass
nor a skipped Hermetic test, and the pack must not be copied into or committed to
the repository.

## Start the application

```powershell
streamlit run app/main.py
```

The app can also be launched with the same isolated runtime used by verification:

```powershell
uv run --offline --no-project --with nflreadpy --with numpy --with pandas --with pydantic --with streamlit streamlit run app/main.py
```

Open the local URL printed by Streamlit. Starting or opening a page does not refresh
a provider, mutate a refresh receipt, or write source data. Refresh Data is an
explicit user-controlled workflow; Settings / Data Health is read-only inspection.

## V1 workflows

The primary V1 navigation includes Draft Cockpit, Mock Draft, Dynasty Rankings,
Player Compare, Trading Lab, Draft Analyzer, Development Lab, Roster Weakness
Tracker, planning/deadline surfaces, Future Tools, Refresh Data, evidence review,
and Settings / Data Health.

- Rankings and Player Compare expose governed scores, warnings, trust, freshness,
  and unavailable states. Optional full rankings data must be repository-local;
  missing optional data is shown truthfully.
- Trading Lab is manual trade entry and display only. It does not persist saved
  scenarios or composite asset IDs and does not issue a hidden recommendation.
- Live Draft and Mock Draft use local state and existing admitted data. Mock-draft
  files, when explicitly saved, are local artifacts; they do not mutate source data.
- Refresh Data runs only after an explicit action. Data Health distinguishes latest
  attempt, latest success, retained data, stale data, and last-known-good state.
- Roster Weakness Tracker is manual/display-only. Automated roster hydration is not
  part of V1 and no name-only identity fallback is permitted.
- Review and future-tool surfaces remain review-only, gated, unavailable, or parked
  when their evidence or authority is incomplete.

## Security and trust posture

Runtime inputs are local and admitted; no scraping or page-open provider calls are
part of V1. Stable admitted identity is required where identity affects decisions.
Name-only joins, inferred opaque IDs, hidden source promotion, hidden ranking or
recommendation changes, and unsafe CSV formula output are prohibited. Refresh
receipts reject secrets, provider payloads, paths, duplicates, oversized content,
and invalid schema before durable mutation.

Repository automation remains disabled. Its release disposition is
`READY_FOR_HUMAN_REENABLE_REVIEW`; a human must separately review and enable it.
Automatic commit, push, and force-push behavior are not part of V1.

## Known V1 limitations

- Automated roster hydration is parked pending stable admitted identity.
- Trading Lab saved scenarios are parked pending stable asset IDs.
- Exact rookie-evidence hydration is paused pending authority and identity.
- Route-based advanced metrics remain gated where provider rights are absent.
- Formula challengers and future 2026 outcome tuning are post-V1 research.
- The private `LocalData` pack may be unavailable; the separate gate then exits `4`.
- Plugin-backed recommendations are not admitted V1 behavior.
- Cloud and cross-device durability are not supported.
- Automatic commit and push remain disabled pending human re-enable review.

The governed list and re-entry conditions are in the V1 release-readiness packet
under `docs/hq/master/nwr_v1_release_readiness_scope_freeze_final_acceptance_v1_20260718/`.

## Rollback

V1 release-candidate work is delivered as one local commit on its release branch.
Rollback means returning to the recorded canonical HQ commit or creating a new
revert commit after human adoption; do not force-push or delete private local data.
The release packet records the exact HQ, candidate commit, protected-path proof,
and clean-checkout recovery steps.
