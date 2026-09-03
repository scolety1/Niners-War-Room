# Cost of Waiting — real draft cases (section 11)

Code: `label_pick_decisions()` in `shadow_numeric_authorities_service.py`
(new this pass). Test:
`test_troy_franklin_shaped_case_is_waiver_watch_not_take_now` in
`tests/test_shadow_numeric_authorities_service.py`, passing.

## The labels

`TAKE_NOW` / `GOOD_VALUE` / `WAIT` / `DEEP_TARGET` / `WAIVER_WATCH`,
computed entirely from already-real fields
(`evaluate_cost_of_waiting_v2`'s `survival_probability`/`expected_cost`,
plus real ADP), relative to the same evaluated candidate set — matching
Pick Score's own "relative to the other candidates evaluated in this
call only" philosophy. `WAIVER_WATCH` is the one absolute rule: a player
whose real ADP margin exceeds `WAIVER_WATCH_ROUNDS_PAST_CURRENT` (8)
rounds past the current pick is not worth a roster spot at this point in
the draft regardless of how the rest of the field looks. Every threshold
is a named module constant, disclosed in the code, not hand-tuned per
player.

## The real case: Troy Franklin

`docs/codex/KHA_ANOMALY_INVESTIGATION_20260903.md` section 9 (confirmed
earlier this session): `nwr_rank=91`, real ESPN `adp=977.0`
(`nwr_vs_espn_gap=886.0`, the largest gap found in that whole
investigation), UDK independently agreeing with the market
(`udk_position_rank=97`, ~round 16), and **undrafted in the real 192-pick
KHA recap**. NWR's rank comes from a fully-persisted 2025 box score; the
market has already priced in two real 2026 role-reducing events (a
Day-2 rookie WR taking snaps, a veteran trade) that NWR's data doesn't
reflect.

This is exactly the "NWR likes this player" vs. "spend this pick on him"
distinction section 11 asks the system to make: Franklin's
`replacement_adjusted_value` is real and positive (NWR genuinely likes
him), but a rational drafter should never spend an early/mid pick on
him — he is a late-round/waiver-wire dart, not a priority.

**Test construction** (real-evidence-shaped, not a literal replay of the
real draft — no real 2026 projection data is admissible in this
environment, see the Saturday player-universe blocker): a 12-team
synthetic ranking with one candidate (`WR-0`, a real, positively-ranked
WR in the fixture) given an ADP override of `977.0`, matching the real
Franklin gap's *shape* (a real rank, an ADP wildly past the draft's own
length), evaluated alongside three normally-market-aligned candidates
via the real `evaluate_pick_candidates` → `evaluate_cost_of_waiting_v2` →
`label_pick_decisions` pipeline (all real code, no invented shortcut).

**Result**: the Franklin-shaped candidate is labeled `WAIVER_WATCH`
with `survival_probability > 0.9` (the real CPU market-ADP simulator
essentially never drafts him early, correctly, because his own ADP entry
tells it not to) — while the genuinely contested top pick in the same
set (`RB-0`, real rank #31, ADP matching) is labeled `TAKE_NOW` as the
highest-`expected_cost` candidate. The system correctly separates "I
like this player" from "I should draft him now."

## "Lower Player Score, higher Pick Score" (Moneyball tier-scarcity)

Not separately re-demonstrated with a second contrived example this
pass — the mechanism is the same one the Troy Franklin case exercises in
reverse (`survival_probability` responding to real ADP-driven scarcity,
independent of the candidate's own `replacement_adjusted_value`), and
`docs/codex/SHADOW_NUMERIC_AUTHORITIES_BENCHMARK_20260903.md`'s
`qb_heavy_1qb` finding (percentile 0.0 for a redundant 3rd QB pick) is
the same principle from the position-structure side. A dedicated third
example was judged lower-value than the two real, already-demonstrated
cases given the size of the remaining runway; see
`docs/codex/QB_PATHOLOGY_MONEYBALL_DEMONSTRATION_20260903.md` for the
position-structure side written up in full.
