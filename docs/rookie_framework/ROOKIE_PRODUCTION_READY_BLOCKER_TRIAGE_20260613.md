# Rookie Production Ready Blocker Triage - 2026-06-13

## 1. Executive Verdict

Verdict: GREEN for planning, not approved for implementation.

The Rookie Production Approval Queue is GREEN because the readiness docs, candidate contract, candidate builder, candidate audit, proposal, and checkpoint all preserve source safety and avoid production/app promotion. Implementation is not approved because the candidate export is conservative, has `0` `ready` rows, and still exposes premium/manual blockers.

The `0` ready rows are correct under the current narrow definition of `ready`: a row must have no manual warnings, no remaining gaps, no quarantined source terms, no low source confidence, and no blockers. That definition is safe but too strict for a future production ranking that can display warnings beside the order.

Conclusion: the current builder is safe, but its status semantics are ambiguous for the next gate. A production-candidate ranking needs a middle status between "fully clean" and "warning exists."

## 2. Blocker Inventory

### True Football/Source Blockers

- `1.03` has no source-safe player cleared for the premium bar.
- Ted Hurst is low source confidence in the premium group.
- Mike Washington has low source confidence and no clear matched Deep Research evidence behind the inherited tag.
- Savion Red is `needs_data` with broad RB survival gaps.
- Low-confidence `5.04` rows with no role path remain parking-lot names, not live production movement candidates.

### Premium-Pick Manual-Review Blockers

- Jeremiyah Love: explosive rate, pass protection, and RB survival gaps.
- Kaelon Black: short-yardage, injury, receiving/goal-line gaps.
- Denzel Boston: route, separation, first downs, contested-target, red-zone, and YAC/press gaps.
- KC Concepcion: route, separation, press, manufactured-touch, and target-rate gaps.
- Makai Lemon: route, separation, press, YAC, and target-rate gaps.
- Jordyn Tyson: injury, route, separation, press, YAC, and target-rate gaps.
- Chris Bell: route, manufactured touch, source warning, and target-rate gaps.
- Germie Bernard: route, separation, manufactured touch, and target-rate gaps.
- Zachariah Branch: route, separation, manufactured touch, and role/special-teams translation.
- Ted Hurst: low source confidence plus broad WR proof gaps.

### Missing-Data Blockers

- Premium WR route/separation/press/YAC and target-rate fields.
- RB routes, pass protection, short-yardage, first-down, fumble, receiving, goal-line, contact, and injury fields.
- Round 2 RB support for inherited tags.
- `2.04` has no separate row set; current Round 2 rows remain `2.08`.
- TE exception route participation, target command, receiving-vs-blocking usage, and injury context.

### Source-Safety Blockers

- Quarantined ADP/ranking/projection terms remain warning-only.
- `manual_review_only` evidence cannot become positive private value.
- `use_as_soft_flag` evidence cannot open `1.03`, override caps, or become hard private value.
- Low-confidence rows cannot be promoted without source discovery.
- Source conflicts would block affected movement if they alter role, injury, identity, or premium evidence.

### Implementation/Contract Blockers

- No app-read approval exists.
- No feature flag is approved.
- No production ranking replacement contract exists.
- No HQ implementation prompt names exact files/actions.
- Current candidate output is local-only and `app_read_allowed=no`.
- Candidate exports are not committed and must remain local.

### Overly Strict Gate / Semantic Blockers

- Current `ready` means "warning-free," not "rankable with displayed warnings."
- Every row with any manual warning, soft flag, remaining gap, or quarantined source term is pushed out of `ready`.
- Low-confidence `5.04` rows are still `manual_warning` rather than a separate "watchlist/source_limited" status.
- The `manual_warning` bucket mixes players who may be rankable with warnings and players who should only be displayed as parking-lot reviews.

## 3. Ready-Status Semantics Review

Current statuses:

- `ready`
- `manual_warning`
- `blocked`
- `unavailable`

The current semantics are safe for a checkpoint but too strict for a production ranking that can display warnings. A useful production-candidate export should distinguish "rankable but warned" from "manual review still required."

Recommended future statuses:

- `ready`: clean row, no visible blockers or warnings.
- `rankable_with_warning`: can be ordered in a production-candidate ranking if warnings are displayed and no hard blocker exists.
- `manual_review_required`: not blocked forever, but Tim must answer a specific question before production movement.
- `blocked`: hard cap, source conflict, prohibited-source dependency, or premium injury/source blocker.
- `unavailable`: insufficient source-safe evidence or roster-declaration dependency.

Interpretation:

- `ready` should remain rare.
- `rankable_with_warning` should be allowed only for rows where warnings are displayable caveats rather than stop conditions.
- `manual_review_required` should be the default for unresolved premium-pick questions.
- `blocked` should be reserved for hard caps, source conflicts, prohibited-source dependence, or unresolved premium injury/source blockers.

## 4. Candidate Export Review

Current full candidate export:

- `ready`: `0`
- `manual_warning`: `133`
- `blocked`: `43`
- `unavailable`: `35`
- total rows: `211`

Premium / `1.04`:

- `10` rows.
- `9` are `manual_warning`.
- `1` is `unavailable` due to low source confidence.
- All remain `1.04`; `1.03` remains empty.

Round 2:

- `9` rows.
- `5` are `manual_warning`.
- `4` are `unavailable`.
- All are RBs and all carry `pick_zone=2.08`.

`5.04`:

- `119` watchlist rows in the split `5.04` export.
- All `119` are `manual_warning`.
- Full export has `144` rows at `5.04` because capped/manual context is also retained outside the split watchlist.

## 5. Premium Pick Triage

### 1.03

`1.03` remains empty because no rookie has enough source-safe evidence to clear the premium bar without unresolved manual warnings, source caveats, injury questions, or missing fields.

Production can safely represent `1.03` as:

- `no_player_cleared`;
- `trade_down_review`;
- `hold`;
- `manual_review_required`.

It should not force a player into `1.03`.

### 1.04

Closest to production-rankable with warnings:

- Jeremiyah Love: closest because source confidence is high, but pass protection, explosive rate, RB survival gaps, and quarantined ADP warning remain.
- KC Concepcion: medium source confidence with role/archetype clarity, but route/separation/press/manufactured-touch and target-rate fields remain manual.
- Makai Lemon: medium confidence and useful WR evidence, but press/YAC and target-rate gaps remain.
- Denzel Boston: medium confidence, but several target-earning fields remain manual and projection/ranking warnings are quarantined.
- Jordyn Tyson: medium confidence, but injury review is a true premium blocker.
- Germie Bernard and Zachariah Branch: medium confidence, but target-rate/role proof remains unresolved.
- Kaelon Black: medium confidence, but injury and short-yardage questions remain.
- Chris Bell: medium confidence, but route/manufactured usage and ranking warnings remain.
- Ted Hurst: not close; low confidence and broad proof gaps.

Blockers that could be displayed as warnings instead of blocking rank order:

- `SOURCE_LIMITED` caveat when independent source-safe evidence exists.
- Quarantined source terms when not used as private value.
- Remaining non-core gaps that do not define the player's role.
- Soft flags that are not opening zones or overriding caps.

Blockers that truly prevent production ranking movement:

- unresolved premium injury risk, especially Jordyn Tyson;
- source conflict affecting role, injury, or identity;
- prohibited-source dependence;
- low source confidence for a premium row;
- missing role-defining evidence such as target earning for WR or pass-pro/survival profile for RB;
- any attempt to open `1.03` from soft evidence.

## 6. Round 2 / 5.04 Triage

### Round 2

Production-rankable with warnings:

- J'Mari Taylor: high source confidence; still needs explosive/pass-pro/short-yardage/first-down/goal-line/injury review.
- Adam Randall: medium confidence; pass protection and RB survival gaps remain.
- Emmett Johnson: medium confidence; soft explosive/pass-pro/first-down flags need warning treatment.
- Jamal Haynes: medium confidence; injury and broad survival gaps remain.
- Jamarion Miller: medium confidence; explosive committee profile with injury/pass-pro blockers.

Truly unavailable or blocked for now:

- Mike Washington: low confidence and inherited tag support is not enough.
- Savion Red: `needs_data` and broad survival gaps.
- Dean Connors: low confidence and broad survival gaps.
- Nicholas Singleton: low confidence and broad survival gaps.

### 5.04

Production-rankable with warnings:

- Skyler Bell: possible target-earning dart if warnings remain visible.
- Demond Claiborne: early-down RB dart if RB survival gaps remain visible.
- Kaytron Allen: early-down dart with warnings.
- Seth McGowan: early-down dart with warnings.
- Eli Stowers: TE receiving exception only as `manual_review_required`.
- Sam Roush: TE receiving exception only as `manual_review_required`.

Truly blocked/unavailable for production movement:

- source-limited names with no role path;
- generic safe/low-upside names;
- TE-only replaceable profiles without receiving exception evidence;
- any QB exception invented from current artifacts.

## 7. Patch Recommendations

Recommended path: patch production candidate builder to add `rankable_with_warning`, plus patch docs/tests to enforce warning visibility.

Why:

- The current `ready` gate is intentionally strict and should remain strict.
- The next useful distinction is not making rows `ready`; it is separating rows that can be ordered with warnings from rows that require manual review, are blocked, or are unavailable.
- This preserves safety while making the candidate export more useful for a later HQ decision.

Do not patch production rankings, app files, private scores, formulas, probabilities, bands, outcome files, or veteran files.

Suggested future status rules:

- `ready`: no warnings/blockers.
- `rankable_with_warning`: no hard cap, no source conflict, no premium injury blocker, not low-confidence premium, and warnings are displayable rather than role-defining blockers.
- `manual_review_required`: premium pick unresolved, TE exception unresolved, injury review unresolved, or role-defining fields missing.
- `blocked`: hard cap, source conflict, prohibited-source dependence, or capped review status.
- `unavailable`: needs data, low-confidence non-dart, roster declaration dependency, or no evidence.

## 8. Safe Next Step

Exact next rookie-only task:

Create a candidate-status semantics patch for `build_rookie_production_candidate_v03.py`, its tests, and the candidate contract docs.

The patch should:

- add `rankable_with_warning`;
- preserve all warning fields;
- keep `ready` strict;
- keep `1.03` empty;
- keep app-read disabled;
- keep probabilities/bands disabled;
- keep local exports uncommitted;
- prove with tests that warning visibility is preserved.

Do not implement production promotion.
