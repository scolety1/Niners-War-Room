# NWR Prospective 2026 Freeze V3 (2026-09-08, marginal_roster_utility PROMOTED)

**Verdict: `FULL_ADOPTION_MARGINAL_ROSTER_UTILITY_PRIMARY_ORDERING`**

**UPDATE (same day):** the owner flagged a real temporal-leakage gap in the walk-forward evaluation below; verification also found an independent QB-rate computation bug. Both confirmed real; a corrected, leakage-safe rerun still passed all 3 preregistered gates (mean_delta +92.49 vs the original +74.65, wins unchanged at 32/48) — **promotion KEPT**. The live `POSITION_BACKUP_UTILITY_RATE["QB"]` constant was corrected from 0.125 to 0.5556 (a real, verified arithmetic-error fix, independent of the leakage question). Full corrected evidence: `docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md`, section 8 ("TEMPORAL-LEAKAGE VERIFICATION ADDENDUM"). Evidence label: `LEAKAGE-CLEAN_WALK_FORWARD_DEVELOPMENT_VALIDATION`, not a pristine historical holdout — this remains real development/replay evidence (2020-2023); the next independent proof is prospective 2026.

Does NOT overwrite V1 (`NWR_PROSPECTIVE_2026_FREEZE_20260907.md`, commit `d815c633`) or V2 (`NWR_PROSPECTIVE_2026_FREEZE_V2_20260908.md`, commit `5ec89064`). This is a short, explicit correction/supersession notice: V1 and V2's own text ("PARTIAL_ADOPTION... `pickScore`/`action`/candidate ORDER are unchanged") is **now stale** as of commit `c318a10c` and must not be relied on for anything after that commit.

## What changed

Per an explicit owner directive, `marginal_roster_utility` underwent a real, preregistered walk-forward evaluation (4 real historical seasons — 2020-2023, deliberately excluding the 3 permanently-burned holdouts 2016/2024/2025 — 48 real paired draft simulations using real leakage-safe projections and real realized nflverse outcomes). **All 3 preregistered gates passed** (mean_delta +74.65, CHALLENGER won 32/48 = 67%, worst single-season regression -1.4%, well inside the 5% tolerance). Full protocol, results, and case-study evidence: `docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md`.

`marginal_roster_utility` is now the **primary candidate-ordering signal** in the live `build_decision_bundle()` — `_candidate_sort_key` sorts by `marginal_utility` first, with `pick_score`/`raw_decision_utility`/`player_id` as real tie-breaks. This is a genuine change to what "NWR PICK NOW" means in the live product, not merely additive context.

## What did NOT change

- Team Score, Championship Equity, and Pick Score's own underlying VALUES/formulas — completely unchanged.
- K/DST handling, the pair-pick optimizer (`bestTurnPlan`), Cost-of-Waiting/Make-It-Back, `action` labeling.
- The historical burned-holdout rule itself — 2016/2024/2025 remain permanently excluded from any future evaluation of this engine.

## Updated frozen component versions (delta from V2)

| Component | V2 status | V3 status |
|---|---|---|
| Candidate ordering basis | Pick Score (marginal_utility additive-only) | **`marginal_utility` PRIMARY**, Pick Score/raw_decision_utility real tie-breaks |
| `marginal_roster_utility` adoption | PARTIAL (wired, not ranking basis) | **FULL** (walk-forward validated, gates passed, promoted) |
| DecisionBundle latency regression (V2's top disclosed limitation) | Found, root-caused, not fixed | **Unchanged — still not fixed.** This promotion did not touch or resolve it; still the single highest-priority follow-up. |

Every other V2 component/limitation entry stands unchanged.

## Prospective evaluation protocol (unchanged from V1/V2, restated)

1. 2016/2024/2025 remain permanently excluded from this engine's evaluation, this promotion included.
2. When 2026 season results become available, compare against this frozen state honestly — this promotion's own real evidence is 2020-2023, not 2026; 2026 is the first genuinely prospective test of the now-live promoted ordering.
3. Do not retune Team Score/Championship Equity/Pick Score's own values based on this promotion or any single season's 2026 outcome.
4. If 2026 real outcomes suggest `marginal_utility`-primary ordering underperforms, that is real, new prospective evidence and should be evaluated on its own terms — not used to justify silently reverting without documentation.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
