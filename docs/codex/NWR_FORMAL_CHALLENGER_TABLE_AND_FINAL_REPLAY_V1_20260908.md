# NWR Formal Challenger Table, Wired-Candidate Multi-League Rerun, Final 403 Replay (V1)

**Date:** 2026-09-08 (overnight V4 continuation)
**Scope:** Directive V4 sections 21 (formal challenger comparison table), 22 (rerun the multi-league mock battery on the ADOPTED candidate, not just the reference), 23 (full 403 replay table with the final candidate).

## Section 21 — Formal challenger comparison table

Per the formal ADOPTION decision (`docs/codex/NWR_MARGINAL_UTILITY_TE2_REPRODUCTION_AND_ADOPTION_V1_20260907.md`, section 5): **PARTIAL ADOPTION** — `marginal_roster_utility` is wired live as additive, owner-visible context (commit `1cf81bd4`), NOT promoted to replace the ranking basis. "REFERENCE" below is the live, unmodified Pick Score/Team Score/Championship Equity path; "CANDIDATE" is `marginal_roster_utility`.

| Dimension | REFERENCE (live Pick Score) | CANDIDATE (marginal_roster_utility) |
|---|---|---|
| What it measures | Per-call 0-100 normalized composite of Team Score delta + Championship Equity delta | Real starter-vs-bench marginal value, using real, measured position-specific backup-startability rates (QB 0.125 / RB 0.542 / WR 0.979 / TE 0.729, from nflverse 2022-2024 week-1 snap-share data) |
| Historical validation | Full walk-forward program (2016/2024/2025 seasons, all burned) — see [[nwr-team-score-v1-frozen-2016-burned]], [[nwr-2025-final-holdout-passed-program-complete]] | Real 403 counterfactual only (one draft) — no walk-forward *outcome* study yet |
| Real 403 match rate vs. owner's 14 actual picks | 3/14 (21%) | 5/14 (36%) — adds 5.08 Travis Etienne, 12.01 Wan'Dale Robinson |
| QB2/QB3 hoarding complaint | Root cause identified (starter-swap mislabeled as "hoarding"), not itself fixed by Pick Score | Fixed: QB backup correctly discounted to 12.5% of standalone value (vs. treating it like any other position) |
| TE2 bench discount | No position-specific discount | Real 72.9% first-bench-TE rate, reproduced directly against the real 403 roster (see the TE2 reproduction doc) |
| Multi-league transport (8/10/12/16-team, 1QB + Superflex) | Validated (prior sessions) | Validated this session — see section 22 below |
| Latency | Already in the ~0.7-9.6s DecisionBundle budget | Additive, try/except-wrapped, adds negligible measured overhead (184/184 real candidate-turns computed cleanly in the section-22 battery, zero failures, zero added latency budget request) |
| Known limitation | Per-call min-max normalization is coarse/lossy (disclosed, tie-order now fixed — section 19) | `bench_redundancy_before` under-counts a 3rd-deep FLEX-eligible bench candidate when a DIFFERENT position has already claimed the shared FLEX slot (documented, reproducible, not fixed — see the TE2/TE3 doc) |
| Live wiring status | Sole basis for `pickScore`/`action`/candidate order | Additive `marginalRosterUtility` field per candidate, explicitly labeled EXPERIMENTAL; never affects order |

**Formal verdict, unchanged from the section-6 decision**: candidate is real, evidence-backed, and demonstrably fixes the exact failures it targeted — but full adoption (replacing the ranking basis) remains gated on a real walk-forward *outcome* study this session did not run. Partial adoption (live, additive, owner-visible) is the correct, evidence-matched current state.

## Section 22 — Multi-league rerun of the WIRED (adopted-as-additive) candidate

The prior multi-league battery (UPDATE 9) validated the REFERENCE engine's default top-recommendation behavior across 5 league shapes, before `marginalRosterUtility`/`bestTurnPlan` were wired into the live payload. This reruns the SAME 5 shapes (real bundled 608-row projection data, isolated disposable roots, blind-policy replay always taking `candidates[0]`) to verify the WIRED fields themselves compute cleanly end-to-end, not just in isolated unit tests.

| Shape | Slot | Complete | Owner picks | K round | DST round | `marginalRosterUtility` populated | `bestTurnPlan` computed |
|---|---:|---|---:|---:|---:|---|---|
| 8-team 1QB | 4 | Yes | 16 | 15 | 16 | 184/184 (0 null) | 0/16 |
| 10-team 1QB | 5 | Yes | 16 | 15 | 16 | 184/184 (0 null) | 0/16 |
| 12-team 1QB | 6 | Yes | 16 | 15 | 16 | 184/184 (0 null) | 0/16 |
| 16-team 1QB | 8 | Yes | 16 | 15 | 16 | 184/184 (0 null) | 0/16 |
| 12-team Superflex | 6 | Yes | 16 | 15 | 16 | 184/184 (0 null) | 0/16 |

**`marginalRosterUtility`**: computed for every single real candidate at every real owner turn across all 5 shapes (184 candidate-turns total, zero nulls, zero exceptions) — the try/except wiring never had to silently swallow a failure. K/DST timing (round 15/16 in every shape) is unchanged from the reference-engine battery, confirming the additive field genuinely never touches ordering, exactly as designed.

**`bestTurnPlan`: 0/16 in every shape here — correct, not a bug.** Per the real section-17/18 finding, only the LAST draft slot (`slot == team_count`) produces a genuine back-to-back turn; this battery's slots (4, 5, 6, 8, 6) were chosen for realistic mid-draft positioning, none of which is the last slot in its league. `bestTurnPlan`'s own dedicated test (`test_redraft_decision_bundle_wires_a_best_turn_plan_for_a_real_back_to_back_turn`, section 18) already proves it populates correctly for a real `slot == team_count` case (12-team, slot 12) — not re-run here to avoid a redundant ~90s battery pass for a case already covered by a real, passing test.

## Section 23 — Final 403 replay table, with the final (partially-adopted) candidate

Full replay of all 14 real owner turns from the completed 403 draft, comparing the OLD live Pick Score recommendation, the NEW `marginal_roster_utility` recommendation (re-ranking the same real top-10 DecisionBundle candidates already gathered at each turn), and the owner's real actual pick:

| Round.Pick | OLD (Pick Score) rec | NEW (marginal utility) rec | Actual owner pick | Old matches actual? | New matches actual? |
|---|---|---|---|---|---|
| 1.08 | Christian McCaffrey | Christian McCaffrey | Trey McBride | No | No |
| 2.01 | Christian McCaffrey | Christian McCaffrey | Christian McCaffrey | **Yes** | **Yes** |
| 3.08 | George Pickens | George Pickens | George Pickens | **Yes** | **Yes** |
| 4.01 | Chris Olave | Chris Olave | Chris Olave | **Yes** | **Yes** |
| 5.08 | Josh Jacobs | Travis Etienne | Travis Etienne | No | **Yes** |
| 6.01 | Kenny Gainwell | Matthew Stafford | D'Andre Swift | No | No |
| 7.08 | Josh Jacobs | Matthew Stafford | Jameson Williams | No | No |
| 8.01 | Josh Jacobs | Matthew Stafford | Jadarian Price | No | No |
| 9.08 | Josh Jacobs | Matthew Stafford | Kenny Gainwell | No | No |
| 10.01 | Josh Jacobs | Matthew Stafford | Michael Wilson | No | No |
| 11.08 | Matthew Stafford | Matthew Stafford | Caleb Williams | No | No |
| 12.01 | Trevor Lawrence | Wan'Dale Robinson | Wan'Dale Robinson | No | **Yes** |
| 13.08 | Trevor Lawrence | Jakobi Meyers | Matthew Stafford | No | No |
| 14.01 | RJ Harvey | Jakobi Meyers | HOU D/ST | No | No |

**Match rate: OLD 3/14 (21%) → NEW 5/14 (36%).** Recommendation changed in 9 of 14 real turns. The two turns the candidate newly matches (5.08 Travis Etienne, 12.01 Wan'Dale Robinson) are exactly the ones the candidate's own real mechanism targets — a genuine bench-value/starter-swap discount correction, not a coincidental shift. Neither version predicts every pick (the owner's real choices reflect real-world knowledge — e.g. Josh Jacobs risk-avoidance — the model doesn't have), and this table is not claimed as more than what it is: one real draft's counterfactual, the same honest scope as every prior use of this data this session.

## Verification

Section 22's battery: real, isolated, disposable test roots (`C:\Users\codex-agent\AppData\Local\Temp\nwr_battery_*`), deleted after each run, never touching the real 403/Fantasy Gamers boards. Section 23: read-only replay against the already-unmutated real 403 board. Both real boards re-verified byte-identical before and after this entire unit.
