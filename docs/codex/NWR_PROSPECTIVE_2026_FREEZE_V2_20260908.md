# NWR Prospective 2026 Freeze V2 (2026-09-08, post-draft overnight V4)

**Verdict: `PARTIAL_ADOPTION_MARGINAL_ROSTER_UTILITY_WIRED_ADDITIVE_REFERENCE_ORDERING_UNCHANGED`**

This does NOT overwrite `NWR_PROSPECTIVE_2026_FREEZE_20260907.md` ("V1") — that document remains the historical record of state at commit `d815c633`. This V2 documents the real, substantial state as of tonight's overnight V4 continuation (commits `1cf81bd4`..`d7389b24`), where a genuine (partial) adoption occurred and several other real product changes shipped. Anyone comparing prospective outcomes against a frozen reference must know which freeze (V1 or V2) their comparison point actually is.

## What changed since V1 (real, shipped, summarized — see `nwr-post-draft-engine-forensics-v1` memory UPDATEs 11-22 and the linked `docs/codex/` reports for full detail)

1. **`marginal_roster_utility` PARTIALLY ADOPTED** (commit `1cf81bd4`): wired live into the real `redraft_decision_bundle()` HTTP response as an additive `marginalRosterUtility` field per candidate, explicitly labeled EXPERIMENTAL. `pickScore`/`action`/candidate ORDER are unchanged — the calibrated Pick Score remains the sole ranking basis. Formal gate-by-gate adoption decision: fixes the targeted QB2/QB3/TE2 failures (PASS, real evidence), transports across league sizes/Superflex (PASS), maintains latency (qualitative PASS at the time — see item 6 below for a real, later-discovered caveat), but historical external-outcome validation is NOT DONE — full adoption (replacing the ranking basis) remains gated on that.
2. **Pick Score tie-order is now deterministic** (commit `be3bd093`): a real secondary comparator (`raw_decision_utility`, then `player_id`) replaces an unexamined, accidental input-order tie-break. Does not change any non-tied ordering.
3. **Pair-pick optimizer's "BEST TURN PLAN" wired live** (commit `0d1eb9e0`): additive `bestTurnPlan` field, computed only for a genuine back-to-back turn, across the top 3 already-computed candidates. Never affects `pickScore`/`action`/order.
4. **Real status/risk event intake contract added** (commit `635accb9`): `add_verified_status_override()` — the first real, validated WRITE path for the pre-existing status-override read layer (previously hand-edited only). No UI form built yet; a facade/UI caller would sit on top of this contract.
5. **Ballers/UDK PDF ingestion pipeline built** (commit `31272045`): `parse_udk_position_pdf()`, tested against a representative fixture; the real-sample structural-fidelity gap remains explicitly `BLOCKED_PENDING_OWNER_SAMPLE` (V1's "no PDF ingestion pipeline exists" limitation is now "pipeline exists, unverified against a real sample").
6. **A real, severe DecisionBundle latency issue was found (NOT fixed)** (`docs/codex/NWR_OWNER_UI_RENDERING_VERIFICATION_V1_20260908.md`): FAST-speed calls against a real, full-scale (~530-row) pool measured at **~10-13 seconds**, not the ~0.7s the V1 freeze's own latency assumptions (and the original `DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md`) relied on. Root-caused via cProfile to `_select_asset`'s cost inside the Raw Action Value Monte Carlo continuation loop, scaling with real pool size. **This is the single most important new disclosed limitation this freeze carries** — it materially affects real owner-facing reliability for any league with a real, full-scale player pool, and was not previously known. A related real bug (an uncaught connection-abort crash in the HTTP server, the direct downstream symptom of this latency) was found and fixed (commit `a3b57a8f`).
7. **FFA Sept-4 admission decision made**: **D, retain as reference-only** (commit `43000259`) — was undecided in V1.
8. **Make-It-Back's flagged 0.500-vs-0.595 gap resolved with real statistics** (commit `ed08e15d`): Wilson 95% CI `[0.445, 0.730]` comfortably contains the predicted value; a real second independent draft (Fantasy Gamers, `LIVE_READ_ONLY`, 91/150 real picks) populated the two buckets the 403 board could never produce data for, and every bucket's prediction falls inside its real CI. No recalibration — confirms V1's calibration was already sound, now with real statistical backing instead of a qualitative hedge.
9. **K/DST rounds-15/16 timing investigated and confirmed real, correctly-designed, not a hidden hard-coded round** (commit `6c001750`) — a real two-layer system (dynamic urgency check + an explicit, round-count-relative last-2-rounds backstop), both independently verified via counterexamples.
10. **Brooks/Diggs/Judkins real pipeline root-causes found** (commit `43000259`): Diggs — a real acquisition-stage `last_season` staleness edge case (not fixed, systemic, scoped); Brooks — correctly blocked (no prior-season stat line), a real coverage gap between the veteran and rookie models (not fixed, scoped); Judkins — classified as a real, disclosed persistence-model role-change blind spot (no fix needed/proposed).
11. **Rookie-specific bias study done** (commit `7a8bc040`): rookies are systematically UNDER-predicted (-16.70 pts/season mean), the OPPOSITE direction from the general age-cohort study V1 already carries forward — confirms rookies are a genuinely distinct population. No correction applied.

## Frozen component versions (V2, supersedes V1's table for anyone comparing from tonight forward)

| Component | Version / identity | Status vs. V1 |
|---|---|---|
| Player Score / RAV | `replacement_adjusted_value` via `score_projection` | UNCHANGED |
| Team Score | `shadow-team-score-v1` | UNCHANGED |
| Championship Equity | `shadow-championship-equity-v1` | UNCHANGED |
| Pick Score value | `shadow-pick-score-v1` (`RESEARCH_ONLY_PICK_SCORE`) | UNCHANGED |
| Pick Score tie-order | `_candidate_sort_key` (pick_score → raw_decision_utility → player_id) | **NEW this pass** (was unexamined stable-sort order) |
| Decision policy | Pick-Score-descending sort (now with the real tie-break above), top row = recommendation | Ordering-preserving change only |
| `marginal_roster_utility` | `POSITION_BACKUP_UTILITY_RATE` real rates (QB .125/RB .542/WR .979/TE .729) | UNCHANGED formula since V1; **now WIRED LIVE as additive context** (was dead/unwired at V1) |
| `bestTurnPlan` / pair-pick optimizer | `evaluate_pick_pairs` | **NEW WIRING this pass** (function existed at V1, unwired) |
| Status/risk intake | `add_verified_status_override()` | **NEW this pass** (read-only at V1) |
| Ballers/UDK import | CSV (unchanged) + **PDF (new, fixture-tested, real-sample gap disclosed)** | Extended |
| Projection snapshot | `NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V1`, sha256 `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25` | UNCHANGED VALUES |
| Market source (403 N 18th) | Real draft COMPLETED live 2026-09-07 ~8pm MDT (118 real picks) | Draft completed since V1 (V1 was pre-draft-completion) |
| DecisionBundle FAST latency | ~10-13s measured against a real 530-row pool | **NEW, real, disclosed regression from the documented ~0.7s assumption** |

## Real evidence this freeze carries forward from V1 (still true, not retuned)

- Age/experience bias: general study still rejects "NWR undervalues youth" broadly (opposite bias found); a NARROWER, real, distinct rookie-specific bias WAS found this pass (item 11 above) and is a genuinely separate fact, not a reopening of the general study.
- Historical Player/Team Score validation (2016/2024/2025, all burned) — untouched, not reopened.

## Prospective evaluation protocol (unchanged from V1, restated)

1. Record this document's commit as the V2 reference point; V1's commit (`d815c633`) remains the earlier reference point for anything measured before tonight.
2. When 2026 season results become available, compare REALIZED points against the frozen projection snapshot — an honest, prospective, walk-forward comparison.
3. Any future full-adoption decision for `marginal_roster_utility` (replacing the ranking basis, not just the additive field) requires a real walk-forward outcome study — not another single-draft counterfactual.
4. Do not retune Player Score / Team Score / Championship Equity / RAV / Pick Score's VALUE based on a single draft's outcome. (Pick Score's tie-order fix this pass is a determinism fix, not a value retune — explicitly distinguished.)

## Real limitations disclosed, not fixed, carried into 2026 (V2 list — supersedes V1's, closing items now resolved)

- **DecisionBundle FAST latency (~10-13s against a real full-scale pool) — new, real, highest-priority disclosed limitation.** Root-caused via cProfile (`_select_asset`'s cost, scales with real pool size), not fixed.
- Ballers/UDK PDF ingestion: built and tested against a representative fixture; real-sample structural-fidelity check remains `BLOCKED_PENDING_OWNER_SAMPLE` (no real owner PDF has ever been provided).
- `marginal_roster_utility`'s `bench_redundancy_before` under-counts a 3rd-deep FLEX-eligible bench candidate when a DIFFERENT position has already claimed the shared FLEX slot (real, reproduced, documented; not fixed).
- Status/risk intake has a real backend contract now but no UI form yet — no owner-facing way to submit a new event without a script.
- No real, direct K/DST projection MODEL exists (feasibility confirmed real and direct this pass — nflverse has the needed data — but not built).
- A real coverage gap between the veteran persistence model and rookie model for 2nd/3rd-year players who lost their rookie season to injury (Brooks-class cases) — root-caused, not fixed.
- Diggs-class acquisition-stage `last_season` staleness edge case — root-caused, not fixed (changes the universe for every future veteran build, needs its own validation).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
