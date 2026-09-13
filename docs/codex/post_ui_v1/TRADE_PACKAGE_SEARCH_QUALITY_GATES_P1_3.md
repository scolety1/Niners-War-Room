# Trade Package Search -- Preregistered Quality Gates (P1-3, Worker 6)

Written and committed BEFORE `src/services/trade_package_search_service.py`
was implemented (this project's discipline: evaluation criteria set before
results are seen). `test_trade_package_search_service.py` asserts every gate
below directly -- none of these numbers were tuned after looking at output.

Scope: this is the SEARCH layer over Trade Analysis's existing multi-player
`evaluate_trade` (`redraft_trade_analysis_service.py`, untouched). It
generates 1-for-1, 2-for-1, 1-for-2, and 2-for-2 candidate packages and
filters them through the gates below. No acceptance-probability or
"likely to accept" figure is computed anywhere in this module, in any mode --
explicitly forbidden by the product spec.

## 1. Legality

Both rosters (the owner's and the counterparty's) must be LEGAL after the
trade. "Legal" here is a NEW, disclosed, POST-DRAFT definition -- it does
**not** change `redraft_roster_legality_service.py`'s own draft-time
hard-maxima rules, which that module's own docstring already says have "no
meaning post-draft" (`roster_limits` are a draft-time construct). Legal,
for this search layer, means: the resulting roster's player COUNT does not
exceed the league's configured total roster capacity --
`qb+rb+wr+te+flex+superflex+k+dst+bench_size` on `LeagueProfile.roster`.
Position maxima (`DraftContext.roster_limits`) are NOT enforced here,
matching the existing, already-shipped disclosed design in
`redraft_trade_analysis_service.py`/`trade_finder_service.py` (composition-
level plausibility, not the draft-time engine). A package that would leave
EITHER side over that roster-size cap is never returned -- checked with a
cheap set-arithmetic count BEFORE the expensive `evaluate_trade` call, so
illegal packages never reach real scoring at all (see gate 6).

## 2. Owner utility baseline

- **FIND_WIN_WIN** and **IMPROVE_POSITION** modes: the owner's
  `net_marginal_utility` (from `evaluate_trade`) must be strictly `> 0.0` --
  the trade must make the owner's real roster better, not merely neutral.
- **TARGET_PLAYER** mode: no owner-side net-utility floor is applied. The
  owner explicitly asked for a specific player and may rationally accept a
  net marginal-utility cost to acquire him; gating that away would silently
  hide the exact packages the owner asked to see. Instead, a narrower, still
  real gate applies: the target player's OWN per-player marginal utility
  (his `TradeSideImpact.marginal_utility` on the owner's receiving side)
  must be `> 0.0` -- searching for a way to acquire a player who would not
  even help the roster once rostered is not a sensible thing to return.

## 3. Opponent utility

- **FIND_WIN_WIN** mode: the opponent's `net_marginal_utility` must be
  strictly `> 0.0` (real mutual benefit -- both sides must gain under the
  same governed model).
- **TARGET_PLAYER** and **IMPROVE_POSITION** modes: the opponent's
  `net_marginal_utility` must be `>= 0.0` (non-negative). This app makes no
  acceptance claim either way, but a package that leaves the counterparty
  RAW WORSE OFF under the same governed model is not generated at all.

## 4. Dominance filtering

Within one (owner, opponent) pairing, a package is discarded if any OTHER
already-gate-passing package for the SAME opponent, of equal or smaller
total player count (`len(gives) + len(receives)`), has an owner
net-utility `>=` this package's owner net-utility AND an opponent
net-utility `>=` this package's opponent net-utility (weakly dominates on
both real axes, and is not identical on both). A full pairwise Pareto sweep
per opponent, not just a 1-for-1-vs-everything check -- e.g. a 2-for-2 that
is strictly worse on both axes than an available 1-for-1 is never surfaced.

## 5. Duplicate / symmetric packages

Every package is generated exactly once, from the OWNER's perspective
(`you_send` / `you_receive`), keyed by
`(opponent_roster_id, frozenset(gives_ids), frozenset(receives_ids))` in an
explicit seen-set. The counterparty's mirror of the same trade
(`opponent_give_X_for_Y` restated as `owner_give_Y_for_X`) is the identical
key from the owner's own perspective and is never separately generated or
counted twice.

## 6. Pruning / bounded search (explicitly NOT brute force)

- Each side's give/receive candidate pool is bounded to its top
  `DEFAULT_CANDIDATES_PER_SIDE` (default 6) players, ordered by the REAL
  existing `rank_drop_candidates` ascending-marginal-utility signal
  (weakest/most-expendable first) for FIND_WIN_WIN and TARGET_PLAYER
  filler slots -- never a team's best players. IMPROVE_POSITION's receive
  pool is instead the opponent's own players AT the requested position,
  ordered by real ROS `replacement_adjusted_value` descending, bounded the
  same way -- a deliberately different, real signal for "who might they
  reasonably trade at this position" than "what's their expendable bench."
- Multi-player combinations are built ONLY from that bounded pool
  (`itertools.combinations`, sizes 1 and 2) -- packages larger than 2-for-2
  are explicitly out of scope for this pass (a disclosed remainder, not a
  silent gap).
- A package is skipped BEFORE any `evaluate_trade` call (the expensive
  step) if: either side's post-trade roster size is illegal (gate 1), the
  package gives and receives the same player, or (IMPROVE_POSITION only)
  the receive side does not include a player at the requested position.
- Two hard caps stop the search even if legal, ungated combinations remain
  unexplored: `MAX_PACKAGES_EVALUATED_PER_OPPONENT` (default 120, real
  `evaluate_trade` calls scored against one opponent) and
  `MAX_TOTAL_PACKAGES_EVALUATED` (default 900, across the whole search
  call). This is a disclosed, bounded heuristic search, not a
  guaranteed-globally-optimal one.

## 7. Latency target

FIND_WIN_WIN (the broadest mode -- every opponent, both directions, sizes
1-2) must complete in **under 5 real wall-clock seconds** for a realistic
12-team league (11 opponents x 15-player rosters, default pruning
constants). Asserted directly with a wall-clock timer in
`test_trade_package_search_service.py`, not just claimed in prose.

## 8. No acceptance probability

This module computes and returns NO acceptance-likelihood, "will they
accept," fit-score, or similar probability/confidence-of-acceptance field
anywhere, for any package, in any mode. `why_it_may_fit_them` is a
structured list of REAL computed deltas from the opponent's own
`evaluate_trade` result (net marginal utility, ROS delta, starter-hole/
redundancy changes) -- never a fabricated likelihood number.
