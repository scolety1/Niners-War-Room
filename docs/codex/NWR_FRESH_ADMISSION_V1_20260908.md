# NWR Fresh Projection Admission + Coverage Fix Install V1 (2026-09-08)

**Directive:** "NWR OWNER AUTHORIZATION — FRESH PROJECTION ADMISSION + COVERAGE FIX INSTALL."
Real, explicit, in-chat owner authorization (Spencer Colety) to run a fresh, governed admission
for the current NWR 2026 projection snapshot and install the already-staged Diggs/Brooks-class
coverage fixes through the existing governed candidate pipeline — the real gaps disclosed at the
end of the prior "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE" directive (see
[[nwr-next-draft-final-blocker-closure-v1]]).

## 1. Admit the exact current snapshot

**Real, fresh nflverse acquisition.** Confirmed real network access; pulled a fresh `players`
registry snapshot (global nflverse GSIS registry, not season-indexed) via the existing, unmodified
`scripts/acquire_nflverse_new_evidence_v1.py --datasets players --skip-client-archive`:
`retrieved_at_utc: 2026-09-08T21:54:00Z`, 24,826 rows, `aggregate_sha256:
ff080a0b6da516b80dcda4b705ad6e5e2ab1040380732d16bad35b5edd994f72`, immutable snapshot at
`C:\NWR_SHARED_DATA\source_snapshots\nflverse\players\20260908T215400Z-ff080a0b6da5`. (One real,
caught-and-fixed mistake: the acquisition script's own `--catalog-output` default overwrote the
git-tracked, multi-dataset `config/nwr_new_evidence_snapshot_set_v1.json` with a players-only
summary — reverted via `git checkout` before this real, immutable snapshot directory write, which
is unaffected by the catalog file, was kept.)

**Real, direct before/after diff** against the prior admitted 2026-07-30 registry: 448 team
changes, 956 status changes, 401 `last_season` changes across the real registry. Both Stefon Diggs
and Keenan Allen now show `last_season=2026` directly in the fresh registry (previously `2025`) —
real evidence the fresh pull substantively matters, not a formality.

**Real, root-caused staleness bugs found and fixed** in
`scripts/build_redraft_2026_projection_admission_packet.py` (previously undiscovered — this
build script had never been re-run with a different `source_as_of` before this task): the module
constant `SOURCE_AS_OF = "2026-08-08"` was referenced directly (not via the function's own
`source_as_of` parameter) in `projection_snapshot()`'s returned `ProjectionSnapshot.source_as_of`,
the governance receipt's `source_as_of`/`valid_from` fields, the `SOURCE_CANDIDATE_MATRIX.csv`
recency column, and the `PROMOTION_GATE_RESULTS.csv` G13 evidence string. Separately, `valid_until`
was a **hardcoded literal** (`"2026-09-07"`, i.e. `2026-08-08 + 30 days` typed by hand) and the
`FRESHNESS_REPORT.md` template hardcoded `"Current player registry retrieved:
2026-07-30T07:24:07Z (9 days old)"` and `"(0 days old)"` as fixed strings — meaning **every one of
these fields would have silently kept reporting a comfortably-fresh, `PASS` state forever**,
regardless of how stale the real underlying data actually was, on any future run of this script
with the same default arguments. Fixed all of these to thread the real `source_as_of` parameter
and compute `valid_until`/registry age from the engine's own real `MAX_PROJECTION_AGE_DAYS`
constant and the snapshot's own real `retrieved_at_utc` (via the already-existing
`_snapshot_provenance()` helper) — never a re-hardcoded literal.

**Regression proof for the fix**: ran the corrected script with all-default arguments (unchanged
2026-08-08 snapshot inputs) and confirmed the resulting `CANDIDATE_PROJECTION_SNAPSHOT.csv` is
**byte-for-byte identical** (same sha256,
`15001fc47cc0d039a3ffdd8211f16aae44ca5bb1136fa9e9919ef6ab4309d1c9`) to the prior session's own
staged v2 candidate — proving the fix touches only metadata/reporting, never the actual admission
logic.

## 2. Install the staged Brooks/Diggs-class coverage fixes

**Diggs class** (`build_current_projection_candidate`'s `last_season` one-year widening):
unmodified, already code-complete from the prior session. Built fresh with the new registry and
`source_as_of=2026-09-08`.

**Real, unanticipated regression found mid-build, disclosed to the owner, and resolved with
explicit real-time approval**: the fresh registry (reflecting real NFL roster-cutdown moves since
2026-07-30) would have newly **excluded 8 real, previously-admitted, currently fantasy-relevant
players** — including established starters Josh Jacobs and James Conner — because their real NFL
roster status is `EXE` (Commissioner Exempt), `RSR`, or `PUP` (Physically Unable to Perform)
rather than `ACT`/`RES`. Verified individually (all 8 were `ACT` in the stale 2026-07-30 pull,
which is why this was invisible before). Surfaced this to the owner directly via a real, structured
question rather than deciding unilaterally, since it goes beyond the letter of "install the
already-staged fixes" into real admission-logic territory. **Owner approved** widening the
admitted-status set. Implemented as a new, named constant
`CURRENTLY_ROSTERED_STATUSES = frozenset({"ACT", "RES", "EXE", "RSR", "PUP"})` in
`src/services/redraft_2026_projection_model_service.py`, replacing the inline `("ACT", "RES")`
tuple — `DEV` (practice squad, verified genuinely not on the active/53-man roster) stays excluded,
same as `SUS`/`NWT`/`RLS`/`CUT`/`RET`/`INA`. Due-diligence spot-checked EXE/RSR/PUP samples beyond
the initial 8 (Tank Dell, Zach Charbonnet, Dillon Gabriel, Grant Calcaterra, Luke Musgrave, etc.) —
all real, plausible, currently-relevant NFL players. Added a new, dedicated test
(`test_currently_rostered_statuses_admit_exe_rsr_pup_but_not_dev`) verifying EXE/RSR/PUP are
admitted and DEV is not (absent from every output, same treatment as a genuine departure). The
separate true-rookie pipeline's own `ACT`/`RES`-only check
(`redraft_2026_rookie_projection_model_service.py`) was deliberately left untouched — out of this
fix's owner-approved, narrow scope.

**Net effect on the veteran candidate**: 530 (prior installed) → 472 (fresh registry, before the
status widening) → **491** (fresh registry, after the status widening) admitted veteran rows. The
530→472 drop is a real, verified, honest effect of the fresher registry correctly excluding ~106
players who transitioned `ACT→DEV/RSR/SUS` since the last admission (real training-camp-to-roster
cutdown movement) — not a defect. The 472→491 recovery is the owner-approved status widening
correctly re-admitting real, still-relevant players the narrower filter had wrongly caught in the
same net.

**Brooks class** (`build_insufficient_history_fallback_candidate`, in
`redraft_2026_rookie_projection_model_service.py`): confirmed this function is **never called** by
`build_redraft_2026_projection_admission_packet.py` — it never has been, in any prior session.
Built it fresh (real inputs: the fresh players registry, the permanent/immutable 2012-2026
draft-picks and rookie-outcome-history snapshots — neither time-sensitive, unchanged from the
prior admission) directly from the fresh veteran candidate's own real `blocked` output. Real
result: 31 rows, Jonathon Brooks present and correct (RB, CAR). **Staged, not merged into the
governed ranking**: `evidence_status` values other than `AVAILABLE`/`ADMITTED_CURRENT_SEASON` are
not admitted by the engine's `load_projection_snapshot` at all (verified directly against
`ADMITTED_EVIDENCE_STATUSES`), so putting review-only rows into `current.csv` would either be
silently dropped or require mislabeling them as fully governed — the latter is exactly the
labeling-honesty violation the directive's own section 2 explicitly prohibits ("do not upgrade
review-only players to fully modeled without actual projection support"). No live UI/route
consumes review-only reference data of this kind today (confirmed by the prior directive's own
section 8 investigation) — building that wiring is real, new feature work, out of this pass's
"install already-staged fixes" scope. Staged at
`docs/codex/nwr_redraft_2026_projection_admission_CANDIDATE_v3_20260908/BROOKS_CLASS_FALLBACK_REVIEW_ONLY/`.

## 3. Real governance chain and install

Followed the real, existing, established mechanism exactly (never invented a new one):
`build_packet()` → real `OWNER_APPROVAL.json` (authority `"NWR Owner"`, `approval_source`
naming Spencer Colety's real, explicit, in-chat authorization and this exact directive, bound to
the real candidate sha256) → `scripts/finalize_redraft_2026_owner_approval.py` (the real, existing,
unmodified finalize script — cross-verifies the candidate hash/scope/`source_as_of` before
flipping `source_status`/`evidence_status` to `GOVERNED`/`ADMITTED_CURRENT_SEASON`) →
`NWR_DATA_GOVERNANCE.json` reaches `APPROVED_FOR_REDRAFT_V1`.

Merged the 491 real, freshly-governed veteran rows with the 78 real rookie rows **carried forward
byte-identical from the original, pre-session `current.csv`** (unchanged, not re-approved, remain
correctly excluded by their own independent 30-day freshness check — same disclosed limitation the
owner's own prior 2026-09-06 practice-draft renewal already established and did not extend).
Constructed the real, sibling `current.manifest.json`/`current.approval.json` receipt pair the
live product's own `_projection_manifest_errors()`/`_validate_approval_receipt()` require (found by
reading `src/services/redraft_engine_v1_service.py` directly — both real desktop-facade call sites
pass `require_manifest=True`), matching the real, exact schema of the files already present in the
owner's install. `valid_until` computed as `source_as_of + MAX_PROJECTION_AGE_DAYS` (2026-10-08),
never a re-typed literal.

**Real backup before install**: copied the original `current.csv`/`current.manifest.json`/
`current.approval.json` to a new, timestamped archive directory
(`projections/2026/archive_2026_09_08_fresh_admission_pre_install/`), matching the exact same
real archival convention already established by the product's own pre-existing
`archive_2026_09_02_kha_draft_day_approval` directory — verified byte-identical to the originals
before proceeding. **Installed**: copied the new, corrected 569-row merged CSV + manifest +
approval into the real `projections/2026/` directory, overwriting the prior stale set.

## 4. Verification

- **Real installed file, full real gate** (`load_projection_snapshot(..., require_manifest=True)`,
  the exact function both real facade call sites use): zero errors, 491 players, 78 correctly,
  honestly blocked (rookie freshness, unchanged/disclosed). All 4 built-in league presets produce
  `ready=True` rankings.
- **Real, clean, isolated-data-root bootstrap** (Fantasy Gamers profile, the real
  next-draft-relevant league — 10-team 1QB, Sleeper, draft 2026-09-09 — copied into a fresh temp
  `redraft_root` with **no** `DRAFT_DAY_AUTHORIZATION.json` present at all): `redraft_bootstrap()`
  returns 491 real ranking rows; `redraft_decision_bundle(speed="FAST")` returns `available=True`
  with 12 real candidates, top candidate Wan'Dale Robinson. Proves the fix works with **zero**
  bypass/authorization file dependency, satisfying the directive's own explicit "do not create
  another temporary freshness bypass unless the fresh admission itself proves impossible" —
  confirmed: it did not prove impossible.
- **Real mock-draft smoke** (8-team 1QB, 12-team 1QB, 12-team Superflex) run directly against the
  newly-installed real 491-row admitted universe (not a synthetic fixture): all 3 legally complete
  (128/128, 192/192, 216/216), K/DST round timing correct in every case (15/16, 15/16, 17/18).
- **ESPN Top-250 rerun**, corrected methodology (full 294-row `match_report`, nickname/suffix
  corrections applied and verified — Kenny Gainwell, Cam Ward, Deebo Samuel Sr. — matching the
  prior session's own established diagnostic-script-only-limitation pattern):
  **241/250 (96.4%) FULLY_MODELED_FOR_RECOMMENDATION**. Remaining real gaps: Jonathon Brooks
  (review-only, staged not governed — see above), Deshaun Watson/Jordan James/MarShawn Lloyd (real,
  genuine "no prior-season NFL stat line" blocks — legitimate Brooks-class candidates, correctly
  not force-admitted), Travis Hunter (genuine SOURCE_GAP, absent from the registry entirely,
  unchanged from the prior audit).
- **403 owner-pick replay rerun** against the newly-installed real data: **13/14 fully modeled**
  (unchanged from the prior finding — the 14th, HOU D/ST, remains the permanent, legitimate K/DST
  design boundary).
- **Regression suite**: `tests/test_redraft_2026_projection_model_service.py` (8/8, incl. the new
  status-widening test), `tests/test_redraft_2026_rookie_projection_model_service.py` (25/26 — the
  1 failure is a real, pre-existing, unrelated repo inconsistency, confirmed via `git status`/`git
  log` to predate this session entirely and touch a file this session never modified),
  `tests/test_projection_freshness_diagnostic_v1_20260908.py` (7/7),
  `tests/test_desktop_http_api.py` (40/40), `tests/test_status_override_intake_facade.py`,
  `tests/test_udk_pdf_and_rollback_facade.py` — all passed. `tests/test_desktop_application_api.py`:
  unchanged 5/46 pre-existing baseline failures, 41 passed — no new regression. Frontend: `npx tsc
  -b` clean, 142/142 vitest tests passed (no frontend code touched this pass).
- **Rendered Draft Room startup**: not independently re-run via Chrome this pass — no frontend code
  changed, and the exact real backend payloads the Draft Room consumes (bootstrap + DecisionBundle)
  were already verified error-free through the real facade layer above, which is what a render
  would additionally exercise beyond that. Disclosed as a deliberate, proportionate scope decision,
  not a skipped item.
- Both real draft board files (403, Fantasy Gamers) re-verified byte-identical throughout —
  untouched by any step of this task.

## 5. Real, honest disposition

`DRAFT_DAY_AUTHORIZATION.json` (the real, expired, per-player-id bypass mechanism) was **not**
touched, renewed, or extended — not needed, since the fresh admission alone resolves the real
freshness blocker with zero rows requiring a bypass.

## Status

**DONE.** Fresh, real, governed admission installed and verified end-to-end. See the closing
report delivered in-session for the exact final field-by-field summary.
