# NWR Prospective 2026 Freeze V5 (2026-09-08, next-draft final blocker closure)

**Verdict: `NEXT_DRAFT_READY_WITH_DISCLOSED_STALE_PROJECTION_BLOCKER`**

**HEAD:** `eaef1a47c40d9e4e77b871f9052ad7350c92e0dd`

Does NOT overwrite V1 (`NWR_PROSPECTIVE_2026_FREEZE_20260907.md`, commit `d815c633`), V2
(`NWR_PROSPECTIVE_2026_FREEZE_V2_20260908.md`, commit `5ec89064`), V3
(`NWR_PROSPECTIVE_2026_FREEZE_V3_20260908.md`, commit `c318a10c`), or V4
(`NWR_PROSPECTIVE_2026_FREEZE_V4_20260908.md`, commit `26c455d9`). This freeze covers the real
work of the "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE" directive (2026-09-08, sections 1-10),
starting from V4's own HEAD and ending at the commit above -- the deliberate, single deferral
recorded in this same directive's own Section 3 (see
`docs/codex/NWR_NEXT_DRAFT_FREEZE_RECONCILIATION_V1_20260908.md`).

## What changed since V4 (real, committed, this directive)

1. **Projection freshness/bootstrap diagnostic fixed** (`80a28ffc`): the row-level 30-day
   freshness gate itself is real, correctly-designed governance -- not a bug. Fixed the
   diagnostic quality: a new `_draft_day_authorization_status()` plus an upgraded top-level
   error message make the real blocking cause and the real required owner action (a fresh
   admission, or an owner-issued draft-day authorization bound to the exact snapshot hash)
   explicit end-to-end, instead of the prior generic "no rankable player rows" message. 7 new
   tests. Governance semantics unchanged.
2. **`marginalRosterUtility` wired into the Player Drawer** (`e2041107`): the real, walk-
   forward-promoted PRIMARY ordering signal had zero frontend consumer anywhere (verified by
   source grep) despite being computed on every real DecisionBundle candidate -- now rendered
   with the backend's own real label/explanation.
3. **Freeze V4/HEAD reconciled** (`606b71ef`): proved by exact commit diff that V4 remained
   accurate through its own 2 trailing docs-only commits, then went stale exactly at this
   directive's own sections 1-2 (`80a28ffc`, `e2041107`) -- V5 (this document) is that
   deliberately deferred cut.
4. **Real ESPN Top-250 audit corrected and rerun** (`23bf24ff`): using the owner's own real
   ESPN ADP snapshot's full 294-row `match_report` (not the 276-row pre-matched `entries`
   subset, which had silently excluded 18 real ADP-importer-rejected players). Result:
   **243/250 (97.2%) FULLY_MODELED_FOR_RECOMMENDATION** (up from a 235/250 pre-directive
   baseline), every remaining gap individually named (6 VISIBLE_REVIEW_ONLY, 1 genuine
   SOURCE_GAP -- Travis Hunter).
5. **403 14th-pick gap explained** (`f23364eb`): the real 14th pick is HOU D/ST -- a
   permanent, project-wide, already-established design boundary (K/DST never NWR-scored), not
   a fixable gap. 13/14 stands as the real, legitimate ceiling; not force-fitted to 14/14.
6. **Brooks/Diggs live-status verification -- the directive's single most important finding**
   (`f237077a`): traced precisely that the real Diggs-class/Brooks-class fixes have never
   reached the real, live, currently-installed product (the desktop app reads a pre-built,
   governance-approved CSV at runtime; it never computes a projection universe live). Verified
   directly against the real owner `current.csv` (608 rows, hash
   `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25`): zero of the 5 real
   Diggs-class names present. Built and staged (NOT installed -- real owner governance
   approval is required and not self-issuable) a real, fresh candidate artifact proving the
   fix is deployable.
7. **One more safe latency pass -- no new optimization, stopped per instruction** (`5933810a`):
   two fresh real cProfile passes confirm the identical hot-path signature already found and
   disclosed (`_seeded_unit`'s real cryptographic jitter cost, deliberately untouched). ~5.8-
   6.95s remains the accepted next-draft latency.
8. **UDK rollback + status/risk intake wired end-to-end** (`8937d4f9`): closed a real, 3-layer
   gap (HTTP route -> client method -> UI) for the real "roll back one UDK position" facade
   method and the real status/risk read+write contracts, closing V4's own disclosed "backend-
   ready but not frontend-built" limitation for these two. The Ballers PDF import UI remains
   explicitly, honestly deferred (no live file-dialog precedent exists anywhere in this
   product -- documented, not force-built).
9. **Next-draft full mock battery** (`eaef1a47`): 6/6 real complete mock drafts (8/10x2/12/16-
   team 1QB + 12-team Superflex) legally complete, K/DST timing correctly scaling with round
   count -- independently reconfirms V4's own multi-league battery a second time. Additionally
   closed that prior battery's own disclosed gap: real DecisionBundle latency, DQ coverage, and
   tie-frequency sampling now measured (see the full report for the exact, traced findings).

## What did NOT change

Team Score, Championship Equity, and Pick Score's own underlying VALUES/formulas;
`marginal_roster_utility`'s own promoted formula; the historical burned-holdout rule
(2016/2024/2025 remain permanently excluded); K/DST's manual/unmodeled status; the pair-turn
planner's informational-only status; `action` labeling; the freshness gate's own 30-day
governance rule (diagnostic quality changed, not the rule).

## Updated frozen component versions (delta from V4)

| Component | V4 status | V5 status |
|---|---|---|
| Projection freshness blocker | Found (Sections 7/18), not fixed | **Diagnostic fixed** -- real cause + real required action now explicit end-to-end; gate itself correctly unchanged |
| `marginalRosterUtility` frontend | Computed backend-only, zero UI consumer | **Rendered** in the Player Drawer |
| Freeze artifact currency | V4 accurate at its own HEAD | **V5 cut** at this directive's true final HEAD |
| ESPN Top-250 coverage | Not measured with the corrected methodology | **243/250 (97.2%)**, every gap individually named |
| 403 14th pick | Unexplained (13/14) | **Explained**: HOU D/ST, permanent design boundary, 13/14 stands |
| Diggs/Brooks fix live status | Assumed live (code-level proof conflated with product-level) | **Corrected**: code-complete, NOT live in the real installed product; deployable candidate staged, not installed |
| DecisionBundle latency | ~5.8-6.95s | **Unchanged** -- reconfirmed via a second real profiling pass; no further safe optimization exists |
| UDK rollback UI | No route/UI | **Live**: full HTTP route -> client -> UI |
| Status/risk intake UI | Facade-reachable, no route/UI | **Live** (read + write) in the Player Drawer |
| Ballers PDF import UI | Facade-reachable, no route/UI | **Still not built** -- explicitly documented, no live file-dialog precedent exists in this product |
| Multi-league battery | 6/6 legal, latency/DQ/ties not measured | **6/6 legal reconfirmed**; latency/DQ/tie-frequency now measured and explained |

Every other V4 component/limitation entry stands unchanged.

## Real coverage/count summary

- Admitted universe: 973 real players (unchanged this directive -- no model research reopened,
  per the directive's own explicit prohibition).
- Real ESPN Top-250 coverage: 243/250 (97.2%) FULLY_MODELED_FOR_RECOMMENDATION.
- Real 403-league owner-pick coverage: 13/14 (the one non-modeled pick is a manual/unmodeled
  DST, by permanent design).
- DecisionBundle latency: ~5.8-6.95s (unchanged; confirmed no further safe optimization
  exists).
- Next-draft mock battery: 6/6 real complete, legal mock drafts across the directive's named
  formats/slots/seeds.

## Known limitations carried forward (honest, not fixed this directive)

1. **The real owner projection snapshot (`current.csv`, 608 rows) is currently blocked by the
   real 30-day freshness governance gate** -- correctly, by design. A fresh admission with a
   current `source_as_of`, or an owner-issued draft-day authorization bound to the exact
   snapshot hash, is required before the next real draft. **This is the one real, disclosed,
   pre-existing next-draft blocker this directive could not and should not self-resolve** (see
   OPEN NEXT-DRAFT BLOCKERS in the closing report).
2. The real, fixed Diggs-class/Brooks-class code has not yet been installed into the live
   product -- a real, staged, deployable candidate artifact exists
   (`docs/codex/nwr_redraft_2026_projection_admission_CANDIDATE_v2_20260908/`) but requires the
   same real owner governance approval as item 1, and still carries the same stale
   `source_as_of` (does not by itself resolve item 1).
3. DecisionBundle latency still above the `<5s` target from V3/V4 -- reconfirmed, no further
   safe optimization found; accepted as the next-draft limitation.
4. The Ballers PDF import UI remains backend-ready only (no HTTP route, no UI) -- documented
   manual workaround: the existing, working CSV lane, or direct facade invocation.
5. K/DST direct model remains research-only, correctly not promoted (unchanged from V4).
6. The insufficient-history fallback (Brooks-class) is correctly not promoted as a calibrated
   point estimate (unchanged from V4).
7. Travis Hunter is a genuine SOURCE_GAP -- absent from the registry snapshot entirely, not a
   fixable identity/matching issue.

## Prospective evaluation protocol (unchanged from V1-V4, restated)

1. 2016/2024/2025 remain permanently excluded from this engine's evaluation.
2. When 2026 season results become available, compare against this frozen state honestly.
3. Do not retune Team Score/Championship Equity/Pick Score/`marginal_roster_utility`'s own
   values based on this freeze or any single 2026 outcome.
4. If 2026 real outcomes suggest any promoted component underperforms, that is real, new
   prospective evidence to be evaluated on its own terms, not silently reverted.
5. Resolving limitation 1 (freshness) requires the real owner's own action, not another
   autonomous session -- see the closing report's OPEN NEXT-DRAFT BLOCKERS.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
