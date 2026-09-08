# NWR Marginal Roster Utility — TE2/TE3 Non-Inferential Reproduction + Formal Adoption Decision (V1)

**Date:** 2026-09-07 (overnight V4 continuation)
**Scope:** Directive V4 sections 3 (QB1→QB2→QB3 / TE1→TE2→TE3 chain validation), 4 (TE2 reproduction, non-inference-only), and 6 (formal ADOPTION rule application).
**Status:** Real, reproducible, read-only against the completed real 403 N 18th draft board. No data mutated.

---

## 1. Why this document exists

The prior pass (`nwr-post-draft-engine-forensics-v1.md`, UPDATE 10) referenced a "McBride → Pitts scenario (6.01)" as evidence of TE2 behavior. Re-running that exact script this session (`phase21_counterfactual.py`, reproduced below) shows that scenario is **not actually a TE2 case at all** — at real pick 6.01, the owner had not yet drafted any TE, so every one of that turn's top-8 candidates (including Kyle Pitts) evaluates as `becomes_starter=True` (open TE slot, full value, no discount). Labeling that as "TE2 evidence" in the prior update was imprecise; this document corrects it with a genuine, directly-computed TE2 (and TE3) case built from the owner's own real, completed roster.

## 2. Real inputs

- Real league: 403 N 18th and friends (profile `4b4a990faf124ce7a5d612537ba5943b`), roster `qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench=7`. `TE` is FLEX-eligible in this league (`FLEX_ELIGIBLE = {RB, WR, TE}`), which matters below.
- Real, completed draft board (118 total picks, drafted live 2026-09-07 ~8:00pm MDT — `updated_at_utc: 2026-09-08T02:50:29Z`). The owner's real 14 picks were used as-is; nothing simulated.
- Real ranking values (`replacement_adjusted_value`) from the live-active projection snapshot, same values Suggestions actually showed the owner during the draft.
- The exact production function under test: `marginal_roster_utility()` in `shadow_numeric_authorities_service.py` (commit `35d072c3`), called directly — not through a synthetic test fixture.

## 3. TE2: the owner's real roster, a real second TE candidate

The owner's actual, real, final roster (14 real picks) has exactly **one** TE (Trey McBride, drafted 1.08, real value 186.1 — a genuine starter, full value, no discount). `roster_composition_report` on this real roster shows position redundancy `{QB: 1, RB: 2, WR: 2, TE: 0}` (RB/WR already deeply bench-redundant: 5 rostered at each position against a usable capacity of 3; TE's usable capacity of 2 — the 1 TE slot plus the 1 shared FLEX slot — is not yet exceeded by 1 rostered TE).

Evaluating real, still-in-the-ranking-pool TE candidates the owner did **not** draft, against this real roster:

| Candidate TE | Real standalone value | `marginal_roster_utility` | `becomes_starter` | `bench_redundancy_before` |
|---|---:|---:|---|---:|
| Kyle Pitts | 81.0 | **59.05** | False | 0 |
| Travis Kelce | 61.4 | **44.76** | False | 0 |
| Tyler Warren | 58.7 | **42.79** | False | 0 |
| Harold Fannin Jr. | 56.6 | **41.26** | False | 0 |
| Jake Ferguson | 56.3 | **41.04** | False | 0 |
| Dallas Goedert | 55.3 | **40.31** | False | 0 |

Every real candidate lands at exactly `standalone_value × 0.729` (0.729 = `POSITION_BACKUP_UTILITY_RATE["TE"]`, the real, measured week-1-snap-share startability rate from nflverse 2022-2024 — see UPDATE 10). `becomes_starter=False` for all of them because the owner's real FLEX slot is already occupied (via the real, shared `_select_starting_lineup` greedy fill) by a real RB/WR whose value exceeds any of these TEs — genuinely correct: a 2nd TE does **not** get to double-count as "fills an open slot" once FLEX is already spoken for by a better real asset. This is the reproduction directive section 4 asked for: real, direct, deterministic — rerunning the same script against the same (unmutated) real board reproduces these exact numbers every time. Not inferred from aggregate statistics; not narrated from memory.

## 4. TE1 → TE2 → TE3 chain

Extending to a real TE3 case (owner roster + real McBride as TE1 + a hypothetically-added real Pitts as TE2, evaluating real Travis Kelce as a 3rd TE):

```
TE1 McBride: drafted as the owner's real starter at 1.08 (full value, no discount — becomes_starter path)
TE2 Pitts:   utility = 59.05  (standalone 81.0  x 0.729^1)
TE3 Kelce:   utility = 44.76  (standalone 61.4  x 0.729^1)   <-- see finding below
```

**Real finding, not glossed over:** TE3 Kelce's `bench_redundancy_before` came back **0**, not 1 — so it received the same single-order discount (`0.729^1`) as TE2 Pitts, rather than a compounded `0.729^2`. Root cause, verified directly: `roster_composition_report`'s `position_redundancy` computes each position's "usable capacity" independently (`required_slots + flex_needed_if_eligible + superflex_needed_if_eligible`), then treats `rostered - usable` as redundant. Because the single real FLEX slot is credited separately to RB, WR, *and* TE's own usable-capacity math (rather than as one slot shared once across all three), a position that has not yet "spent" its own FLEX credit — even when that FLEX slot is almost certainly already claimed by a genuinely more crowded position (this real roster has 5 rostered RBs and 5 rostered WRs against a usable capacity of 3 each) — is under-counted as non-redundant. This is a real, structural limitation of the current redundancy accounting, not a hypothetical concern: it is directly reproducible against the real 403 roster above.

**Disposition:** Not fixed in this pass. A correct fix (a single shared-FLEX-capacity allocation across FLEX-eligible positions, allocated to whichever position's marginal player would actually win the greedy FLEX assignment) is a real architecture change to `roster_composition_report`, and per this program's own no-arbitrary-constants discipline it needs its own empirical validation before shipping — not a same-night patch bolted onto an already-late pass. Flagged here as a concrete, scoped follow-up with a precise reproduction case (this document) rather than left as a vague TODO.

**Practical impact:** narrow. It only under-discounts a *third*-or-later redundant player at a FLEX-eligible position when that position hasn't yet been assigned its own bench-redundant player — QB (not FLEX-eligible in most leagues) is unaffected; the real, owner-facing QB2/QB3 and single-TE2 cases already computed correctly above and throughout UPDATE 10's 403 replay are unaffected, since none of those involved a 3rd-deep FLEX-eligible bench candidate.

## 5. Formal ADOPTION decision (directive section 6)

Applying the directive's own adoption gate, honestly, to real evidence gathered this session:

| Gate | Verdict | Evidence |
|---|---|---|
| Fixes the positional-redundancy failures (QB2/QB3 hoarding, TE2) it targeted | **PASS** | Real 403 counterfactual: match-rate against the owner's 14 actual picks improved 3/14 → 5/14 (UPDATE 10); QB1 starter-swap correctly distinguished from QB2 bench value (0.125 discount) instead of one universal 0.5; real TE2 case above discounts correctly. |
| Does not materially regress historical external outcomes | **NOT VALIDATED** | Only one real draft's worth of counterfactual evidence exists. No walk-forward study against real season *outcomes* (points scored, not just pick-matching) has been run for this specific challenger — that is a genuinely separate, larger undertaking than what this pass completed. |
| Transports across league sizes | **PASS** | 8/10/12/16-team 1QB batteries + 12-team Superflex all completed cleanly on the underlying `_select_starting_lineup`/`roster_composition_report` machinery this challenger reuses (no Superflex-specific special-casing needed) — see UPDATE 9/phase20 battery. |
| Preserves Superflex | **PASS** | Same evidence as above; `POSITION_BACKUP_UTILITY_RATE` has no Superflex-specific branch, and superflex eligibility flows through the shared `_select_starting_lineup` unmodified. |
| Maintains latency | **PASS (qualitative)** | `marginal_roster_utility` is O(candidates) calls to the already-fast `_select_starting_lineup`/`roster_composition_report`, wrapped in try/except in the live payload; no timing regression observed in the decision-bundle regression suite (still comfortably under the 90s pick clock — full backend suite runs in ~11-17s for 120 tests exercising this code path repeatedly). Not separately load-tested against a full 16-team live draft session with wiring active, which is the one piece of this gate not independently re-measured after wiring (vs. before, where only the underlying formula itself was timed).

**Decision: PARTIAL ADOPTION, honestly scoped — not silently promoted to the ranking basis.**

- **What is adopted today:** `marginal_roster_utility()` / `explain_marginal_roster_reason()` are wired live into the real `redraft_decision_bundle()` HTTP response (commit `1cf81bd4`) as an additive, explicitly-labeled `marginalRosterUtility` field on every candidate — real, owner-visible, computed from real data, not dead code.
- **What is explicitly NOT adopted:** `pickScore`, `action`, and candidate ORDER remain entirely on the existing, calibrated, historically-validated Pick Score / Team Score / Championship Equity path. This challenger has not been promoted to replace or reweight that ranking basis.
- **Why not full adoption:** the "does not materially regress historical outcomes" gate is the one genuine, unmet bar — not because the challenger looks bad, but because a proper answer requires a real walk-forward study (multiple real drafts' worth of *season outcomes*, not just pick-matching against one draft), which was not completed this session. Promoting an experimental formula to the primary ranking basis without that evidence would violate this program's own repeated discipline (no historical holdout claims without real validation; 2016/2024/2025 stay burned).
- **What would flip this to full adoption:** a walk-forward outcome study (the kind already run for Player Score / Team Score V1 in earlier sessions) applied to `marginal_roster_utility` as an alternate/blended ranking signal, showing it does not regress final-standing/points-scored outcomes relative to the current live Pick Score across multiple historical seasons. That is a distinct, larger unit of work, correctly sequenced as a follow-up rather than rushed tonight.

## 6. Reproducibility

Every number in sections 3-4 was produced by a short, disposable script directly calling the real `marginal_roster_utility` against the real, unmutated 403 board (`draft_boards/4b4a990faf124ce7a5d612537ba5943b.json`) — re-running it against the same (unmutated) board reproduces byte-identical output. No number in this document was narrated from memory or inferred from aggregate statistics without a corresponding direct function call.
