# Model v4 Phase 1 Checkpoint

Created: 2026-05-16

Phase 1 ends with Model v4 still frozen for audit. The project now has a rules
lock, official roster-rank lock, feature/source contract, scoring-constant tests,
official roster-rank tests, and legacy-label quarantine. No player formulas were
rebuilt in Phase 1.

## Official Rules Locked

Canonical source:

- `docs/model_v4/LEAGUE_RULES_LOCK.md`

Locked league context:

- 10-team dynasty league.
- Official team name: Niners.
- Roster Declaration Day / drop date: June 15, 2026.
- Offseason roster limit before declaration: 24.
- Keeper limit at declaration: 23.
- Starting lineup from 2025 onward: 1 QB, 2 RB, 3 WR, 1 TE, 2 WR/RB/TE flex, 1 K, 14 bench.
- Model value scope is QB/RB/WR/TE. Kickers are roster mechanics only unless explicitly expanded later.

Locked offensive scoring:

| Event | Value |
| --- | ---: |
| Passing yards | 1 per 30 |
| Passing TD | 3 |
| Interception | -1 |
| Rushing yards | 1 per 10 |
| Rushing TD | 4 |
| Receiving yards | 1 per 10 |
| Receiving TD | 4 |
| Reception | 0 |
| Rush or receiving first down | 0.4 |
| Fumble lost | -1 |

Model v4 implication:

- No PPR.
- No TE premium.
- Passing interceptions are -1, not -2.
- Outside projection point totals must be recomputed to this exact LVE scoring.
- No readiness badge can override the rules lock.

## Official Roster Ranks Locked

Canonical sources:

- `docs/model_v4/OFFSEASON_RANKING_SHEET_LOCK.md`
- `docs/model_v4/official_inputs/NINERS_ROSTER_RANKS_20260331.csv`

The official input has 24 Niners rows, numeric league ranks, and roster ranks
1-24. League rank is rule context only. It is not Dynasty Asset Value and must
not be used as player quality.

The locked `Roster's League-Rank Top Five` is:

1. De'Von Achane
2. Lamar Jackson
3. Chase Brown
4. Luther Burden
5. Brian Thomas

Model v4 implication:

- The `Required Top-Five Release Slot` can be chosen only from those five players.
- Non-top-five cuts may be shown as secondary roster context only.
- Any UI that centers non-top-five drops as the required release decision is wrong.

## Allowed Scoring Inputs

Canonical source:

- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.csv`

The following inputs may contribute to a future Model v4 scoring lane after
identity, freshness, receipt, and test requirements pass:

- nflverse production
- rushing first downs
- receiving first downs
- targets
- carries
- derived target share
- derived carry share
- age/bio
- identity

The following inputs may contribute only with explicit limitations and confidence
penalties:

- red-zone usage
- goal-line usage
- snap share
- recomputed raw-stat projections
- young-player draft capital
- structured sourced college/prospect profile

These inputs must preserve source status into normalized feature rows, receipts,
and source coverage. Hidden neutral defaults are not allowed to masquerade as
real evidence.

## Context-Only Inputs

These can explain roster/trade/draft context or confidence, but cannot increase
private football value:

- injury status/history, unless later upgraded by a sourced structured contract
- league rank
- trade market/liquidity

League rank is allowed only for roster-declaration mechanics, especially the
`Roster's League-Rank Top Five`. Market/liquidity is allowed only for trade
context and Model-vs-Market opportunity; it contributes 0 percent to private
football value.

## Rejected Or Unavailable Inputs

Rejected:

- manual agent player-stat tables
- restricted route data exports
- supplied fantasy projection point totals that are not recomputed to LVE rules

Unavailable from safe free/public structured sources until a legal structured
source is approved:

- route participation
- routes run
- TPRR
- YPRR

Review-only:

- estimated first-down projections from historical rates

Model v4 implication:

- Snap share may not masquerade as route participation.
- Route fields cannot be filled with neutral defaults that look like real data.
- Unsourced healthy injury context cannot boost confidence.
- Young-player draft capital cannot score established veterans.

## Remaining Data Gaps

Phase 1 intentionally did not solve data coverage. The remaining pre-scoring
work starts in Phase 2:

- Build truth-set fixtures from the locked football sanity beliefs.
- Verify structured nflverse production, first downs, usage derivations, snap share, age/bio, and identity joins.
- Preserve route-metric unavailability unless a legal structured source is approved.
- Define receipt rows for every v4 output lane before formulas use the features.
- Confirm projection recompute uses the locked scoring constants and labels first-down estimates separately.
- Keep injury and market data separated from private value unless a future contract explicitly upgrades them.

## Tests Added Or Verified

Phase 1 now has tests covering:

- LVE scoring constants against the rules lock.
- No-PPR / first-down scoring derivation.
- Official Niners roster-rank shape: 24 rows, numeric league ranks, roster ranks 1-24.
- Locked Niners `Roster's League-Rank Top Five`.
- League rank as `rule_context_only`, not Dynasty Asset Value.
- Required forced-release candidate pool is top-five-only.
- Ranking readiness remains review-only during Model v4 rebuild freeze.
- Final calibration gate remains blocked/review-only during Model v4 rebuild freeze.
- Roster decision readiness remains review-only during Model v4 rebuild freeze.
- Legacy labels are quarantined during freeze.

## Phase 1 Status

No formulas were rebuilt.

Legacy rankings remain review-only. Legacy labels such as `Core Hold`, `Bubble`,
`Shop`, `Release`, `Decision Ready`, `Roster Decisions Ready`, and `Draft Ready`
are quarantined while the Model v4 rebuild freeze is active.

The v4 feature/source contract is ready for Phase 2 truth-set fixtures.

Formula rebuild work can begin only after Phase 2 creates truth-set fixtures,
receipt expectations, and source-preservation tests from this contract. The next
work should not tune rankings directly; it should prove that trusted evidence can
flow into v4 fixture rows with visible receipts.

