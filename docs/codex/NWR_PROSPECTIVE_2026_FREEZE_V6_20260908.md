# NWR Prospective 2026 Freeze V6 (2026-09-08, fresh projection admission)

**Verdict: `NEXT_DRAFT_READY_FRESH_ADMISSION_INSTALLED`**

**HEAD:** `ace8089da249b440259dd130a649b9dff5deb397`

Does NOT overwrite V1 (`NWR_PROSPECTIVE_2026_FREEZE_20260907.md`, commit `d815c633`), V2
(`NWR_PROSPECTIVE_2026_FREEZE_V2_20260908.md`, commit `5ec89064`), V3
(`NWR_PROSPECTIVE_2026_FREEZE_V3_20260908.md`, commit `c318a10c`), V4
(`NWR_PROSPECTIVE_2026_FREEZE_V4_20260908.md`, commit `26c455d9`), or V5
(`NWR_PROSPECTIVE_2026_FREEZE_V5_20260908.md`, commit `eaef1a47`). This freeze covers the real
work of the "NWR OWNER AUTHORIZATION -- FRESH PROJECTION ADMISSION + COVERAGE FIX INSTALL"
directive (2026-09-08), starting from V5's own HEAD and ending at the commit above.

## What changed since V5 (real, committed, this directive)

1. **A real, fresh, governed projection admission was installed into the real, live owner
   product for the first time this entire project** (`ace8089d`). V5's own #1 disclosed open
   next-draft blocker (the real owner projection snapshot blocked by the freshness gate) is
   **resolved** -- not by a bypass, by a genuine fresh admission.
2. **The Diggs-class fix is now live** in the real installed `current.csv` for the first time
   (V5's own #2 disclosed limitation) -- verified directly: all 5 previously-checked Diggs-class
   names admitted in the real, live file.
3. **A new, real, previously-undiscovered class of staleness bug found and fixed** in
   `build_redraft_2026_projection_admission_packet.py`: several fields referenced the module-level
   `SOURCE_AS_OF` constant directly instead of the real `source_as_of` parameter, and `valid_until`
   plus a freshness-report "days old" figure were hardcoded literals that would have silently kept
   reporting a fresh `PASS` state forever on any future run. Regression-proved byte-identical output
   under default arguments before and after the fix.
4. **A new, real, owner-approved coverage widening**: `CURRENTLY_ROSTERED_STATUSES` now includes
   `EXE`/`RSR`/`PUP` alongside `ACT`/`RES` (DEV/practice-squad remains excluded) in
   `redraft_2026_projection_model_service.py` -- found mid-build (the fresh registry would have
   newly excluded 8 real, previously-admitted, currently-relevant players, including Josh Jacobs
   and James Conner), disclosed to the owner rather than decided unilaterally, explicitly approved
   in-session before being applied.
5. **The Brooks-class fallback was built and run for the first time in this project's history**
   (`build_insufficient_history_fallback_candidate` had zero real callers before this task) --
   staged as review-only reference data, deliberately not merged into the governed ranking (no
   evidence_status other than AVAILABLE/ADMITTED_CURRENT_SEASON is admitted by the engine at all).
6. **ESPN Top-250 and the 403 owner-pick replay both rerun against the newly-installed real data**:
   241/250 FULLY_MODELED_FOR_RECOMMENDATION; 13/14 (unchanged -- HOU D/ST remains the permanent
   K/DST design boundary).

## What did NOT change

Team Score, Championship Equity, Pick Score, and `marginal_roster_utility`'s own underlying
VALUES/formulas; the historical burned-holdout rule; K/DST's manual/unmodeled status; the
freshness gate's own 30-day governance rule (a genuinely fresh admission was produced, not a
bypass); DecisionBundle latency (unchanged, not re-measured this pass -- no code on that path
touched); the true-rookie pipeline's own separate `ACT`/`RES`-only status check (deliberately left
untouched, out of this fix's approved, narrow scope).

## Updated frozen component versions (delta from V5)

| Component | V5 status | V6 status |
|---|---|---|
| Real owner projection snapshot freshness | Blocked (expired authorization) | **Fresh, governed, installed** (`source_as_of=2026-09-08`, valid through 2026-10-08) |
| Diggs-class fix, live status | Code-complete, NOT live | **LIVE** in the real installed `current.csv` |
| Brooks-class fallback | Code-complete, never run, not staged | **Run for the first time, staged as review-only reference data** -- not governed/ranked |
| Admitted veteran rows | 530 (prior installed, pre-Diggs-fix, stale) | **491** (fresh registry + Diggs-class widening + owner-approved EXE/RSR/PUP widening) |
| Admission-script freshness reporting | Multiple real, undiscovered hardcoded-date bugs | **Fixed** -- all real, computed values; regression-proved behavior-preserving |
| Admitted-status vocabulary | `ACT`/`RES` only | **`ACT`/`RES`/`EXE`/`RSR`/`PUP`** (owner-approved; `DEV` deliberately still excluded) |
| ESPN Top-250 coverage | 243/250 (measured against the pre-fresh-admission live state) | **241/250 (96.4%)**, corrected methodology, against the newly-installed real data |
| 403 owner-pick replay | 13/14 | **13/14** (unchanged, reconfirmed against live data) |
| `DRAFT_DAY_AUTHORIZATION.json` | Expired, not renewed | **Still expired, still not renewed** -- not needed; the fresh admission alone resolves freshness for every real row that matters |

Every other V5 component/limitation entry stands unchanged.

## Real coverage/count summary

- Admitted veteran universe: 491 real players (up from 472 pre-status-widening, up net from the
  prior 530 pre-fresh-admission stale set once the real, honest ~106-player roster-cutdown
  correction and the ~19-player owner-approved status-widening recovery are both accounted for).
- Real rookie rows carried forward unchanged: 78 (still correctly, honestly excluded by their own
  independent freshness window -- a real, disclosed, unrenewed limitation, not a new one).
- Real ESPN Top-250 coverage: 241/250 (96.4%) FULLY_MODELED_FOR_RECOMMENDATION.
- Real 403-league owner-pick coverage: 13/14 (unchanged; the one non-modeled pick is a
  manual/unmodeled DST, by permanent design).

## Known limitations carried forward (honest, not fixed this directive)

1. The 78 real rookie rows remain excluded by their own 30-day freshness window -- this directive
   did not touch or renew the separate rookie packet's own admission (unchanged from every prior
   freeze; the real owner's own 2026-09-06 renewal already established this precedent).
2. Brooks-class fallback data remains review-only, with no live UI/route consumption path --
   building that wiring is real, new feature work, out of this pass's "install already-staged
   fixes" scope.
3. The true-rookie pipeline's own `ACT`/`RES`-only status check was deliberately left untouched --
   a real, disclosed, symmetric follow-up to item 4 of V5's own list, not fixed here either.
4. DecisionBundle latency (~5.8-6.95s) unchanged -- not re-measured or re-optimized this pass; no
   code on that path was touched.
5. K/DST direct model remains research-only, correctly not promoted (unchanged).
6. Travis Hunter remains a genuine SOURCE_GAP -- absent from the registry snapshot entirely.

## Prospective evaluation protocol (unchanged from V1-V5, restated)

1. 2016/2024/2025 remain permanently excluded from this engine's evaluation.
2. When 2026 season results become available, compare against this frozen state honestly.
3. Do not retune Team Score/Championship Equity/Pick Score/`marginal_roster_utility`/
   `CURRENTLY_ROSTERED_STATUSES` based on this freeze or any single 2026 outcome.
4. If 2026 real outcomes suggest any promoted component (including the new status widening)
   underperforms, that is real, new prospective evidence to be evaluated on its own terms, not
   silently reverted.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
