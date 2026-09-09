# NWR Strategic Closure Validation Contract (preregistered)

Filed BEFORE running the fresh walk-forward (section 7 of this session's mission) against
`work/nwr-full-historical-tuning-v1-20260904` (or any equivalent historical corpus). The Test 18
counterfactual replay (section 5, real 2023-outcome-value synthetic board) and the
`marginal_roster_utility_v2` unit tests were already run before this file was written -- those are
disclosed as such in the final report, not silently reordered to look pre-registered. This contract
governs ONLY the historical walk-forward evaluation in section 7.

REFERENCE = `marginal_roster_utility` (shadow_numeric_authorities_service.py, live-promoted, commit
`fdf3bdd7` and unchanged by this session).
CHALLENGER = `marginal_roster_utility_v2` (same module, this session's addition, empirically re-derived
from real nflverse 2019/2021/2022/2023 weekly outcome data -- see the module comment block above its
definition and `bench_marginal_utility_study_v1.py`).

## Gates

1. **Mean external-outcome delta >= 0.** Across whatever paired historical draft-slot/season
   observations the corpus makes available, CHALLENGER's mean external-outcome metric (real
   season-outcome-based roster value, whatever the corpus's own established metric is -- not
   re-defined here) must not be worse, on average, than REFERENCE's.
2. **Majority of paired drafts won.** CHALLENGER must win (strictly better external outcome) more
   paired observations than it loses, ties excluded from the denominator.
3. **No season materially regresses.** No single evaluated season's mean outcome under CHALLENGER
   falls more than a small, disclosed tolerance (10% of that season's own REFERENCE mean, or 5 raw
   points, whichever is larger) below REFERENCE.
4. **Legal recommendation rate = 100%.** Every CHALLENGER-selected candidate at every simulated pick
   must independently pass `evaluate_draft_pick_legality` for the roster state at that pick. A single
   illegal recommendation fails this gate outright.
5. **Position-hoarding rate improves or does not regress.** Measured as: fraction of simulated drafts
   reaching a single-position count >= 7 (the real Test 18 WR8 shape) by the end of the draft. Must be
   <= REFERENCE's rate.
6. **Superflex remains valid.** Re-running the same corpus (or a subset) under a Superflex league shape
   must not violate gate 4, and QB counts must remain sane (no more QBs than real roster capacity
   allows to matter).
7. **Latency acceptable.** `marginal_roster_utility_v2` must not be asymptotically worse than v1 -- both
   are O(1) per candidate given an already-computed `roster_composition_report`; a real per-call timing
   comparison is reported in section 9, not asserted here.

## Leakage discipline

Only development-season chronological data may be used to build or evaluate CHALLENGER.
2016, 2024, and 2025 remain burned holdouts (per repo memory:
`nwr-team-score-v1-frozen-2016-burned.md`, `nwr-2025-final-holdout-passed-program-complete.md`) and
must not be reopened as a blind holdout in this pass. If the historical corpus worktree is reachable
only read-only and its own admitted seasons already exclude 2016/2024/2025, no further exclusion is
needed beyond confirming that boundary holds.

## Adoption disposition if all gates pass

`marginal_roster_utility_v2` becomes a **documented, tested CHALLENGER available for a future,
separately-authorized promotion decision** -- this pass does NOT flip the live candidate sort in
`decision_bundle_service.py`. Promotion (if ever) requires its own preregistered walk-forward pass
against the full corpus, following this repo's established promotion-gate precedent
(`nwr-post-draft-engine-forensics-v1.md`), not a same-session self-promotion.

## Adoption disposition if any gate fails

Report exactly which gate failed and why, with real numbers. Do not silently narrow the evaluation
scope to hide a failing gate. A partial pass (e.g., gates 1-4 pass but 5 is inconclusive due to corpus
size) is reported as partial, not rounded up to a clean pass.
