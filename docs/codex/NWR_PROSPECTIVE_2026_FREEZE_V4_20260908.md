# NWR Prospective 2026 Freeze V4 (2026-09-08, class-time autonomous hardening)

**Verdict: `FULL_ADOPTION_MARGINAL_ROSTER_UTILITY_PRIMARY_ORDERING_PLUS_CLASS_TIME_HARDENING`**

**HEAD:** `26c455d94d10d03d95957b0133b56ca7a3145c9b`

Does NOT overwrite V1 (`NWR_PROSPECTIVE_2026_FREEZE_20260907.md`, commit `d815c633`), V2
(`NWR_PROSPECTIVE_2026_FREEZE_V2_20260908.md`, commit `5ec89064`), or V3
(`NWR_PROSPECTIVE_2026_FREEZE_V3_20260908.md`, commit `c318a10c`). This freeze covers the real
work of the "NWR class-time autonomous hardening" run (2026-09-08, owner in class,
sections 1-18 of that directive), starting from V3's own HEAD and ending at the commit above.

## What changed since V3 (real, committed, this run)

1. **DecisionBundle latency** (V3's top disclosed limitation): two real, zero-behavior-change
   fixes (`00446dcd`) reduced real measured latency from ~13.4s to ~5.8-6.95s. Target `<5s` not
   fully reached; stopped per "do not force a risky rewrite" -- still the top real follow-up.
2. **Shared-FLEX/deep-bench marginal utility bug fixed** (`4ba8ce00`): `roster_composition_report`
   now derives `position_redundancy` from the real starter assignment instead of an
   independent, double-counting-prone formula. Re-validated the promoted `marginal_roster_utility`
   walk-forward afterward (mean_delta +91.78 vs pre-fix +92.49, wins 32/48 unchanged, all 3
   gates still pass) -- promotion remained KEPT.
3. **Diggs-class + Brooks-class source gaps fixed** (`40a84565`, `37ddf29f`): acquisition
   universe widened from 910 to 973 real players (real retirement false-positive guard via a
   seasonal-rosters cross-check); a new, reused (not duplicated) insufficient-history fallback
   admits real players with draft capital but no usable own history (kept review-only,
   honest negative historical spot-check disclosed, never promoted to a point estimate).
   Real market-pack coverage: 216/220 (98.2%) FULLY_MODELED (`1b65517e`).
4. **Judkins/role-change**: investigated, real findings documented, left reference-only --
   no real current-role data source exists yet; not force-built (`4031a021`).
5. **Status/risk write path wired** (`e336e7ce`): the real intake contract
   (`add_verified_status_override`) is now reachable from the facade
   (`submit_player_status_override`/`list_player_status_overrides`); a compact frontend form
   remains the next step.
6. **Ballers/UDK PDF import + real versioning/rollback wired** (`773e9477`): PDF import
   reachable from the facade for the first time; per-position version history + rollback added
   (previously nonexistent); preview enriched with per-position counts + duplicate detection.
7. **K/DST readiness confirmed** (no gap found, `8e8d2f05`); **K/DST direct-model research
   baseline built and correctly NOT promoted** (real, weak, walk-forward-evaluated,
   `ea309888`); **K/DST timing stress-tested**, 8/8 named scenarios pass, 2 real limitations
   disclosed (`2569ef5b`).
8. **Pick Score tie-order externally validated** -- no harm found, no adjustment (`6bda7392`).
   **Pair-turn planner GREEDY-vs-JOINT analysis** -- one real divergence showed a concerning
   team_score/win_probability disagreement; kept informational, not promoted (`fa225147`).
9. **FFA/ESPN outlier audit** -- zero real CURRENT_ROLE_CHANGE cases found among top
   disagreements, supporting item 4's reference-only disposition (`83b86f07`).
10. **Rookie bias subgroup follow-up** -- real, decade-stable, pervasive (~-16.7pt) bias with
    no coherent subgroup concentration found; no calibration challenger built, per the
    directive's own no-global-bump rule (`e2f9e4f2`).
11. **Real 403 replay** with all accepted fixes: 13/14 real owner picks FULLY_MODELED today
    (`d85bc153`). **Multi-league battery**: 6/6 real complete mock drafts legal, K/DST timing
    correctly scales with round count (`9b92fee5`).
12. **A real, universal first-load crash found and fixed** via real Chrome rendering
    (`26c455d9`): the no-active-profile bootstrap fallback's `udkRankings.positions` shape
    (`{}` vs the real `[...]` contract) crashed the entire Draft Room on every fresh install.

## What did NOT change

Team Score, Championship Equity, and Pick Score's own underlying VALUES/formulas; the
historical burned-holdout rule (2016/2024/2025 remain permanently excluded); K/DST's
manual/unmodeled status; the pair-turn planner's informational-only status; `action` labeling.

## Updated frozen component versions (delta from V3)

| Component | V3 status | V4 status |
|---|---|---|
| DecisionBundle latency | ~13.4s, root-caused, not fixed | **~5.8-6.95s** (two zero-behavior-change fixes; target `<5s` not fully reached) |
| `marginal_roster_utility` FLEX/bench accounting | Real, known, disclosed double-count bug | **Fixed** (derived from real starter assignment); walk-forward re-validated, promotion still KEPT |
| Acquisition universe (admitted players) | 910 (post-QB-rate-fix baseline) | **973** (+63 net, Diggs-class widening + real retirement guard) |
| Insufficient-history coverage | Not built | **New, review-only fallback** (real draft-capital cohort median; honest negative historical spot-check; not promoted as a point estimate) |
| Real market-pack coverage | Not measured this way | **216/220 (98.2%)** FULLY_MODELED (FFA pack) |
| Status/risk intake | Backend contract existed, unreachable | **Facade-reachable** (write + read); frontend form still pending |
| Ballers/UDK PDF import | Parser existed, unreachable | **Facade-reachable**; real per-position versioning + rollback added |
| K/DST direct model | Feasibility inventoried, not built | **Built, real walk-forward evaluated, correctly NOT promoted** (weak signal, honestly disclosed) |
| K/DST timing policy | Verified for the normal + 1 counterexample case | **8/8 named scenarios verified**; 2 real limitations disclosed |
| Pick Score tie-order | Built, unvalidated externally | **Externally validated** -- no harm found, no adjustment |
| Pair-turn planner (`bestTurnPlan`) | Additive/informational | **Analyzed** (GREEDY vs JOINT); real concerning divergence found in 1/3 cases; kept informational per the directive's own safety rule |
| Rookie bias | Measured (-16.7pt), no subgroup analysis | **Subgroup analysis complete** -- no coherent subgroup found, no challenger built |
| Owner-runtime first-load crash | Unknown (not tested) | **Found and fixed** via real Chrome rendering |

Every other V3 component/limitation entry stands unchanged.

## Real coverage/count summary

- Admitted universe: 973 real players (QB/RB/WR/TE, all sources).
- Real market-pack (FFA) coverage: 216/220 (98.2%) FULLY_MODELED.
- Real 403-league owner-pick coverage: 13/14 (the one non-modeled pick is a manual/unmodeled
  DST, by design).
- DecisionBundle latency: ~5.8-6.95s (down from ~13.4s at V3).

## Known limitations carried forward (honest, not fixed this run)

1. DecisionBundle latency still above the `<5s` target.
2. A real, pre-existing, disclosed projection-snapshot freshness-window bug blocks a clean
   fresh-dev-environment bootstrap (found independently in Sections 7 and 18; not this
   session's introduction; not fixed -- flagged for a future session).
3. A compact status/risk intake UI form and a unified Ballers import UI control are backend-
   ready but not frontend-built.
4. K/DST direct model remains research-only, correctly not promoted.
5. The insufficient-history fallback (Brooks-class) is correctly not promoted as a calibrated
   point estimate -- real value is visibility/coverage, not accuracy.
6. Real, honest edge case: under extreme multi-position scarcity, the CPU auto-pick logic can
   legally finish a draft without K or DST (skill-position priority wins even at the last
   pick) -- disclosed in Section 10, not changed.

## Prospective evaluation protocol (unchanged from V1/V2/V3, restated)

1. 2016/2024/2025 remain permanently excluded from this engine's evaluation.
2. When 2026 season results become available, compare against this frozen state honestly.
3. Do not retune Team Score/Championship Equity/Pick Score's own values based on this freeze
   or any single 2026 outcome.
4. If 2026 real outcomes suggest any promoted-this-run component underperforms, that is real,
   new prospective evidence to be evaluated on its own terms, not silently reverted.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
