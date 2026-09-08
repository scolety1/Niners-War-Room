# NWR Next-Draft Final Blocker Closure — Running Ledger

**Started:** 2026-09-08, HEAD `d00f51dd` (end of the prior "class-time autonomous hardening"
run, all 20 sections of that directive complete). This is a distinct, follow-up directive:
close remaining next-draft readiness gaps only. Do NOT retune marginal_roster_utility, reopen
age/rookie studies, rebuild K/DST models, change Pick Score formulas, redo FFA research, or
redesign the Draft Room. No push/merge/deploy.

## Section 1 — Projection snapshot freshness/bootstrap bug (DONE)

Full evidence: `docs/codex/NWR_NEXT_DRAFT_FRESHNESS_BLOCKER_V1_20260908.md`. Real root cause:
the row-level freshness gate (30-day window) is real, correctly-designed governance, not a
bug -- the real owner's live install has organically aged past it (verified directly,
read-only: all 608 real rows blocked; the one real draft-day authorization self-expired at
2026-09-08T10:00:00Z, exactly as designed). Fixed the diagnostic (not the gate): a new
`_draft_day_authorization_status()` plus an upgraded top-level error message make the real
cause and real required action explicit, traced end-to-end through to the real
`redraft_bootstrap()` owner-facing status. 7 new tests (dynamically-dated, all directive-named
scenarios). No governance semantics changed. Real owner data read-only (isolated copy for the
facade trace); verified untouched via final hash check.

## Section 2 — Full owner runtime acceptance after freshness fix (DONE)

Full evidence: `docs/codex/NWR_NEXT_DRAFT_OWNER_RUNTIME_ACCEPTANCE_V1_20260908.md`. Real,
isolated Chrome walkthrough (test-only fixture, dynamically-dated, never real owner data) of
the complete owner workflow: launch/select league/Draft Setup/mock/Suggestions/Compare/Cheat
Sheets/Show Ballers/Search/Queue/Draft/Undo/Player Drawer/Roster/Recent Picks -- all real,
working, zero console errors at every step. **Real fix**: `marginalRosterUtility` (the real
primary ordering signal) had ZERO frontend consumer anywhere (verified by source grep) --
added the TS contract fields + one Player Drawer line rendering the backend's own real label/
explanation; verified live. **Two real, disclosed gaps left open** (also zero frontend
consumers, verified by grep): `bestTurnPlan` (no UI panel at all) and status/risk display
(read side; write side already known) -- deferred, the latter to section 8's own explicit
scope. Frontend typecheck + 142 tests clean. Both real boards and the real owner data hash
re-verified unchanged.

## Section 3 — Reconcile Freeze V4 with final HEAD (DONE)

Full evidence: `docs/codex/NWR_NEXT_DRAFT_FREEZE_RECONCILIATION_V1_20260908.md`. Real diff
proof: V4's own HEAD (26c455d9) vs the prior session's reported final commit (d00f51dd)
differ only by 2 docs-only commits -- V4 remains accurate through that point. This
directive's own sections 1-2 (80a28ffc, e2041107) DID change real executable code since,
making V4 now stale. Per the directive's own rule, not rewriting V4 -- deferring a real,
single V5 freeze to this directive's own section 10 (its natural, final completion point),
since cutting one now would go stale again at the next executable change in sections 4-9.

## Section 4 — Real ESPN Top-250 coverage audit (DONE, corrected methodology)

Full evidence: `docs/codex/NWR_ESPN_TOP250_COVERAGE_AUDIT_V2_20260908.md`. Corrected an earlier
mistake: used the owner's real ESPN ADP snapshot's full 294-row match_report (not just the
276-row pre-matched `entries` subset, which silently excluded 18 real ADP-importer-rejected
players including Brooks/Diggs). Real result: 241/250 raw FULLY_MODELED_FOR_RECOMMENDATION
(before: 235/250), corrected to 243/250 (97.2%) after fixing 2 diagnostic-script-only nickname
misses (Kenny Gainwell, Cam Ward -- both already real, confirmed FULLY_MODELED in production).
5 of the +6 gain directly attributed to this session's Diggs-class fix. 6 real
VISIBLE_REVIEW_ONLY (correctly excluded from the recommendation count) + 1 real, genuine
SOURCE_GAP (Travis Hunter, absent from the registry snapshot) -- every remaining gap
individually named. No code change.

## Section 5 — Close the 403 13/14 gap (DONE, legitimately unmodeled)

Full evidence: `docs/codex/NWR_403_14TH_PICK_GAP_CLOSURE_V1_20260908.md`. The real 14th pick
is HOU D/ST (real round 14, `player_id=manual:DST:HOU`). Identity/projection/status/market/
fallback all individually checked and ruled out as the cause -- the real reason is category
OTHER: K/DST are a permanent, project-wide design boundary (never NWR-scored), already
re-confirmed weak and correctly not promoted this same session (K/DST direct-model research).
13/14 is the real, legitimate ceiling for this roster; not fixed, per the directive's own
explicit "do not fabricate a model" instruction. No code change.

## Section 6 — Verify Brooks/Diggs fixes are actually live (DONE, major honest correction)

Full evidence: `docs/codex/NWR_BROOKS_DIGGS_LIVE_STATUS_VERIFICATION_V1_20260908.md`. **The
single most important finding of this directive**: traced precisely that
`build_current_projection_candidate`/`build_insufficient_history_fallback_candidate` are
NEVER called from the live facade -- only from offline build scripts. Verified directly: the
real, currently-installed owner `current.csv` (608 rows) contains ZERO of the 5 real Diggs-
class names. Every earlier "FULLY_MODELED"/coverage finding this session reported was
real and correct as a CODE-LEVEL proof, but conflated with "live in the product today" --
corrected explicitly here, per-surface, for both classes. Built and staged a real, fresh
candidate artifact (`docs/codex/nwr_redraft_2026_projection_admission_CANDIDATE_v2_20260908/`,
576 rows, all 5 Diggs-class names present) proving the fix is deployable, via the existing,
unmodified admission-build script -- NOT installed (real governance approval required, not
self-issuable, consistent with established project policy already baked into that script's
own EXECUTIVE_VERDICT.md). Real, disclosed action items recorded for the owner.

## Section 7 — One more safe latency profiling pass (DONE, no new optimization, STOP)

Full evidence: `docs/codex/NWR_NEXT_DRAFT_LATENCY_FINAL_PASS_V1_20260908.md`. Two fresh, real
cProfile passes (heavy synthetic + FAST-preset-matched) both confirm the identical hot-path
signature already found and disclosed in the prior class-time run: `_seeded_unit`'s real
cryptographic jitter cost (untouchable, per instruction) plus two already-disclosed,
already-assessed-as-too-risky structural issues (roster Counter rebuild, pool iteration).
Reviewed `_seeded_unit` directly for a safe micro-optimization; found none (already minimal;
a cross-trial memoization would be pure overhead given real Monte Carlo seed variance). No new
safe optimization exists. Per the directive's own explicit rule, STOPPED. ~5.8-6.95s remains
the accepted next-draft latency. No code change.

## Section 8 — Status/Ballers UI (bounded) (DONE)

Full evidence: `docs/codex/NWR_SECTION8_STATUS_BALLERS_UI_V1_20260908.md`. Found FOUR real
facade methods (`import_udk_pdf_rankings`, `rollback_udk_position_rankings`,
`submit_player_status_override`, `list_player_status_overrides`) with zero HTTP route or UI.
Real finding: the PDF path's own docstring claimed to follow `import_udk_unmodeled_skill_
assets`'s file-path convention, but that method itself has zero real callers anywhere -- no
Tauri file-dialog precedent exists in this product at all. Built, full-stack, tested: UDK
rollback-one-position (no file needed -- a button in Cheat Sheets) and status/risk intake read
+ write (a new Player Drawer "Status / Risk" section, closing section 2's disclosed read-side
gap too). Deliberately left the Ballers PDF import UI backend-ready-only (no route added either
-- an unconsumed route is not "ready", it's untested surface) with a documented manual
workaround (existing CSV lane, or direct facade invocation), per the directive's own escape
valve -- adding the missing Tauri dialog-plugin infrastructure from scratch is not small/bounded.
Also disclosed: the shipped status form omits the directive's literal "optional end date" field
since the real backend contract has no such field (already-known gap, not invented here).
Typecheck clean, 142/142 frontend tests, 2 new + 48 total backend HTTP/facade tests passed, 5/46
unchanged pre-existing baseline failures in `test_desktop_application_api.py`. Both real boards
and the real owner `current.csv` hash re-verified unchanged.

## Section 9 — Next-draft full mock battery (DONE)

Full evidence: `docs/codex/NWR_NEXT_DRAFT_FULL_MOCK_BATTERY_V1_20260908.md`. Real, current
owner profiles confirmed "Fantasy Gamers" (Sleeper, 10-team 1QB, drafts 2026-09-09) is the
real next-draft-relevant league -- gave it two real slots/seeds per the directive. Isolated,
in-memory, dynamically-dated synthetic fixture (never real owner data -- the real snapshot is
itself still blocked by section 1's freshness gate). Re-ran the prior class-time session's own
multi-league battery methodology (`run_complete_mock`) across 8/10(x2)/12/16-team 1QB +
12-team Superflex -- **6/6 legally complete**, K/DST timing correctly scaling with round count
in every case, independently reconfirming the prior finding a second time. Closed that prior
battery's own disclosed gap: added real `build_live_decision_bundle()` sampling (3 real,
progressively-later draft states per case) for DecisionBundle latency (0.94s-3.19s, scales
with team_count, explicitly NOT compared to section 7's own 5.8-6.95s production figure --
different harness scale, disclosed), DQ coverage (276/288, 95.8%, identical in every case --
traced exactly to K/DST's own permanent unmodeled-by-NWR design boundary, not a new gap), and
tie frequency (0/48, disclosed as a synthetic-fixture artifact -- the fixture's smooth
monotonic ranking makes a genuine tie very unlikely regardless of real engine behavior). No
code change; both real boards and the real owner `current.csv` hash re-verified unchanged.
