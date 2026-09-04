# NWR Historical Redraft Data → Draft Upgrade — consumer handoff (current)

Draft Upgrade HQ is the downstream MODEL / CONSUMER authority. This
document is the living contract: what the Historical Redraft Data lane
needs to hand off, in what shape, for Draft Upgrade's existing (built,
tested) consumption code to run for real. It does not describe new work
for Draft Upgrade to do — every mechanism named below already exists and
is already tested against synthetic and small real-shaped fixtures.

Machine-readable twin: `docs/codex/NWR_HISTORICAL_REDRAFT_CONSUMER_HANDOFF_CURRENT.json`
(same content, structured for a script to consume). Update both files
together; this is a "CURRENT" doc, edited in place as the contract
changes, not a dated point-in-time snapshot.

## 1. Current Draft Upgrade state

- **Worktree**: `C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq`
- **Branch**: `work/nwr-draft-upgrade-hq-v1-20260903`
- **HEAD**: `4ae2a96bd5433597f69c53d9f78d4cd50d1ef44e`
- **Tree**: 6 uncommitted paths at handoff time — 5 pre-existing,
  unrelated `docs/model_v4/*.md` diffs and 1 untracked
  `desktop/launch-draft-upgrade-preview.bat` (a prior-wave Preview
  launcher script, not yet committed). Nothing historical-data-related
  is uncommitted. No push. No merge. No deploy.
- **Relevant current artifacts** (all offline research/consumer
  infrastructure — none wired to a live HTTP route or frontend page
  yet):
  - `src/services/historical_replay_data_adapter_service.py` (schema/
    identity/leakage validation, loader, chronological split, generic
    strategy-replay evaluator)
  - `src/services/historical_ranking_bridge_service.py` (historical row
    → real `RankingResult`)
  - `src/services/historical_decision_state_service.py`
    (`HistoricalDecisionState` + real Team Score/Championship
    Equity/Pick Score/Cost-of-Waiting wiring for a historical pick)
  - `src/services/outcome_evaluation_framework_service.py` (player/
    pick/roster/season-level calibration metrics)
  - `src/services/point_in_time_feature_store_service.py` (the shared
    point-in-time feature contract both live and historical paths use)
  - `scripts/run_historical_calibration_readiness_v1.py` (one-command
    entrypoint, section 12)
  - `docs/codex/HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md`,
    `HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md`,
    `HISTORICAL_RANKINGRESULT_FIELD_MAP_20260903.md`,
    `HISTORICAL_ADAPTER_EXPLICIT_STATUS_CODES_20260903.md`,
    `HISTORICAL_REPLAY_DATA_ADAPTER_20260903.md`,
    `HISTORICAL_CALIBRATION_READINESS_ENTRYPOINT_20260903.md` +
    `HISTORICAL_CALIBRATION_READINESS_REPORT.json`
  - `sample_data/kha_real_draft_2026/` — the 2026 KHA fixture. This is
    **same-season postmortem evidence, not a leakage-safe prior-season
    backtest substrate** — see section 15.

## 2. The ACTUAL current historical data contract used by code

Source of truth: `docs/codex/HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md`
(the requirements) enforced concretely by
`historical_replay_data_adapter_service.REQUIRED_PRE_DRAFT_FIELDS` +
`OUTCOME_ONLY_FIELDS` (the schema actually checked in code). A row is one
`(player_id, season)` record split into two strictly separate namespaces:
`pre_draft` (ranking-input-eligible) and `outcome` (scoring-only, never a
ranking input) — the split itself is the leakage guard.

## 3. Tier 1 minimum required fields

**Schema-blocking** (from `REQUIRED_PRE_DRAFT_FIELDS`; missing/empty on
any row → that row is `BLOCKED_SCHEMA`):

```
player_id, player_name, position, team, season,
draft_date, projection_as_of, platform_adp, adp_as_of,
status_as_of, scoring_format
```

**Important gap the schema check alone does not catch**:
`REQUIRED_PRE_DRAFT_FIELDS` names no real stat magnitude at all. A
dataset can pass schema and leakage validation cleanly and still be
useless to the ranking bridge — every player with no populated stat
field is excluded from scoring, and if *every* row lacks stats, the
bridge refuses outright (`HistoricalRankingBridgeError`). In practice,
treat the following as Tier 1 too for anything beyond a
PLATFORM_ADP-only mechanics replay:

- **Non-K/DST positions**: at least one of
  `historical_ranking_bridge_service.PROJECTION_STAT_FIELDS` —
  `passing_yards, passing_tds, interceptions, rushing_yards,
  rushing_tds, receiving_yards, receptions, receiving_tds,
  passing_first_downs, rushing_first_downs, receiving_first_downs,
  return_yards, return_tds, fumbles_lost`.
- **K/DST**: `projected_points_override` (a single real pre-draft point
  total — these positions never use `PROJECTION_STAT_FIELDS`).
- Missing this → the player is **excluded**, not scored as an implicit
  zero, and the exclusion is recorded with `value_status =
  MISSING_PROJECTION_STATS`.

**For the optional identity check** (`historical_picks.csv`): every real
historical pick must resolve to exactly one `player_id` present in the
row set, or carry an explicit, disclosed `identity_status`.

## 4. Preferred but nonblocking fields

| Field | Default if absent | Note |
|---|---|---|
| `rookie` | `False` | Never inferred from name/round — only a real disclosed value or the default. |
| `availability_status` | No feature value built at all | `status_as_of` (the date) IS schema-required, but the *value* it describes is optional; absent, nothing is fabricated (not even `UNKNOWN`). |
| `historical_picks.csv` | Identity check simply skipped | Not required to run the rest of the pipeline. |
| Seasons beyond the schema minimum of one | — | Preferred for a real chronological train/validate/test split (section 15), not required for one season's mechanics. |

## 5. Exact historical cutoff / as-of semantics

| Field | Rule |
|---|---|
| `projection_as_of` | strictly `<` `draft_date` |
| `adp_as_of` | strictly `<` `draft_date` |
| `status_as_of` | `<=` `draft_date` (same-day allowed) |
| `outcome_as_of` | `>=` `draft_date`, **and** `>= draft_date + 140 days` (`MATURITY_MIN_DAYS_AFTER_DRAFT` — a disclosed, round-number floor, not calibrated against any real dataset yet) or the row is `BLOCKED_IMMATURE_OUTCOME` |

Hard leakage exclusions — none of the following may ever be a *ranking
input* for season Y: realized season-Y stats/outcomes; injuries/
depth-chart/trade news learned after the draft date; current
(present-day) NWR rankings/projections; future ADP; retrospective
analysis written after the season. Enforced two ways: a column-name
guard (`BLOCKED_FEATURE_TOKENS = adp, market, ranking, projection,
fantasy_points, fantasy_points_ppr, trade_calculator, sleeper_adp` — a
deliberate literal copy of `scripts/build_backtest_dataset_v0.py`'s own
guard) and the date checks above.

## 6. Historical-row → RankingResult bridge requirements

`historical_ranking_bridge_service.build_ranking_result_from_historical_rows(rows, profile, *, generated_at_utc, source_sha256) -> HistoricalRankingBridgeResult`

Constructs a real `ProjectionSnapshot` from the rows and calls the real,
**unmodified** `redraft_engine_v1_service.generate_rankings()` — the
exact function a live draft uses. No second scoring engine exists.
`profile` must already carry the historical league's real scoring/roster
rules for that season (the caller's responsibility — never guessed).

Output: `bridge_version`, `ranking` (`RankingResult`), `adp`
(`AdpSnapshot`), `feature_store` (`PointInTimeFeatureStore`),
`included_player_ids`, `excluded_players`.

Failure modes: `HistoricalRankingBridgeError` if `rows` is empty, or if
not one row in the whole set has usable stat components.
`generate_rankings()`'s pre-existing "insufficient universe" guard still
applies unchanged (a position needing N roster slots needs ≥ N+1 scored
players, else `RankingResult.errors` is non-empty for that season —
never bypassed to force a result).

## 7. HistoricalDecisionState requirements

`historical_decision_state_service.build_historical_decision_state(bridge_result, *, season, as_of, pick_number>=1, round_number, owner_slot, rosters_by_slot, strategy_version, manual_assets=()) -> HistoricalDecisionState`

`rosters_by_slot` must be built by the caller using **only** picks
`1..pick_number-1` for that historical draft — the constructor cannot
verify this itself, but does enforce that `available_player_ids` never
includes an already-rostered or bridge-excluded player.

`historical_decision_state_service.evaluate_historical_candidates(state, *, candidate_player_ids, comparable_leagues, provenance, player_scores=None, picks_until_next_turn=1, seasons=200, base_seed=20260903) -> DecisionBundle`

Reuses the real, unmodified `team_score()` / `championship_equity()` /
`pick_score()` from `shadow_numeric_authorities_service` — the same
functions the live Draft Room's DecisionBundle uses. Cost of Waiting
uses a disclosed, versioned ADP-distance survival heuristic
(`estimate_historical_survival_probability`,
`SURVIVAL_HEURISTIC_VERSION = historical-adp-survival-heuristic-v1`) —
**not** the live Draft Room's CPU Monte Carlo. `evaluate_pick_candidates`
/ `evaluate_cost_of_waiting_v2` / `simulate_pick_now` are deliberately
not reused: they depend on a separate `draft_order()` implementation in
`redraft_draft_room_v1_service`, and bridging the two without dedicated
alignment testing risks a silent team-slot misattribution.

Every historical `CandidateBundle.action` is fixed to `"UNSCORED"` —
never mislabeled with the live TAKE_NOW/GOOD_VALUE/WAIT/DEEP_TARGET/
WAIVER_WATCH taxonomy, which this heuristic path does not produce.
`uncertainty` is tagged `HISTORICAL_PROXY (...)`. This module has **no
realized-outcome input at all** — outcome data is attached only
afterward by the outcome evaluator, never during recommendation
generation.

## 8. Identity requirements

- One stable `player_id` per real player across every row/pick for a
  season.
- Every real historical pick resolves to exactly one `player_id` in the
  supplied row set, or is explicitly flagged with a disclosed
  `identity_status` — an unflagged gap is always a hard block
  (`BLOCKED_IDENTITY`), never silently dropped.
- Reuses the same identity-status disclosure convention already used by
  the live-draft identity reconciliation work elsewhere in this
  codebase, rather than inventing a new vocabulary.
- The data contract additionally asks for team-code aliasing (LA/LAR,
  AZ/ARI, JAX/JAC-style) and a draft-scoped name-alias registry per
  player per season. Neither has a dedicated enforced validator in this
  lane's code today — resolve to one canonical team code and name before
  handoff.

## 9. Missingness semantics

**Generic feature value status** (`point_in_time_feature_store_service.FEATURE_VALUE_STATUSES`):

| Status | Meaning |
|---|---|
| `KNOWN` | a real value is present |
| `UNKNOWN` | no value could be resolved — never defaulted to zero or a guess |
| `NOT_APPLICABLE` | the feature does not apply to this player/context |
| `BLOCKED` | a value exists upstream but is blocked from use (e.g. an unmatched ADP lookup) |
| `STALE` | a real value exists but is dated outside its point-in-time validity window |

**Bridge-specific exclusion reasons**: `MISSING_PROJECTION_STATS`
(no usable stat components), `UNAVAILABLE_HISTORICALLY`,
`NOT_APPLICABLE`.

**Dataset-level validation status** (`DATASET_VALIDATION_STATUSES`, one
per `validate_historical_dataset()` call, fixed priority order):
`BLOCKED_SCHEMA` → `BLOCKED_IDENTITY` → `BLOCKED_LEAKAGE` →
`BLOCKED_DUPLICATE_PLAYER_SEASON` → `BLOCKED_IMMATURE_OUTCOME` → `OK`.
Full per-check detail is always attached, even after a status is chosen.

**Readiness-script top-level status**: `PASS_READY_FOR_REPLAY`,
`BLOCKED_NO_DATASET_FOUND`, or one of the `DATASET_VALIDATION_STATUSES`
above when validation itself fails.

## 10. Minimum outcome substrate for calibration

**Shared base requirement for all four**: weekly realized fantasy
production per player for the target season, scored under that
league's real scoring rules (`OUTCOME_ONLY_FIELDS`:
`realized_weekly_points`, `outcome_as_of`) — the same rows the base data
contract already requires for "scoring the replay only." No additional
deliverable beyond what section 3 already names.

- **Team Score calibration**: `roster_level_metrics(realized_roster, profile, replacement_points_by_position=None)` — `realized_roster` is a caller-built `Sequence[RosterPlayer]` whose `.value` is REALIZED (not projected) production. Reuses the real `roster_composition_report`/`optimal_starting_lineup_value` — no second lineup algorithm.
- **Pick Score evaluation**: `pick_level_metrics(pick_number, selected_player_id, selected_realized_production, available_pool_realized_production, replacement_points=None, next_pick_available_player_ids=None)` — `available_pool_realized_production` must be every OTHER candidate that was actually available at that pick (the same point-in-time boundary discipline as everywhere else).
- **Championship Equity calibration**: `season_level_metrics(source, regular_season_strength_percentile, simulated_playoff_rate, simulated_championship_rate, sample_size)` — `source=OBSERVED` forbids any `*_rate` field (a single realized season has no observed probability); `source=SIMULATED` is required to report playoff/championship rates at all. **Real bracket/schedule data is not required for this pilot** — only to ever claim `source=OBSERVED`, which this pass deliberately avoids.
- **Cost of Waiting calibration**: `player_rank_correlation(predicted_ranks, realized_ranks)` (Spearman + Kendall tau) plus `pick_level_metrics.made_it_back` (did the passed-on top alternative survive to the next pick) — both computable from the same `realized_weekly_points` substrate, no separate deliverable.

`outcome_evaluation_framework_service` is pure and deterministic — it
reads no file or service itself, only transforms whatever realized
production a caller supplies. All four calibration types are already
implemented and unit-tested; none are blocked on new code, only on a
real `realized_weekly_points` substrate arriving.

## 11. Exact accepted input formats / schemas

- **Primary file**: `<dataset-dir>/historical_replay_rows.csv` — one row
  per (player, season), columns = `REQUIRED_PRE_DRAFT_FIELDS` ∪
  `OUTCOME_ONLY_FIELDS` ∪ (`PROJECTION_STAT_FIELDS` or
  `projected_points_override`, per the Tier-1 gap noted in section 3 —
  **not yet formally added to `REQUIRED_PRE_DRAFT_FIELDS` itself**; if
  the producer lane wants this schema-explicit, that is exactly the
  shape of a bounded `HISTORICAL_DATA_CONSUMER_REQUIREMENT` worth
  emitting).
- **Optional file**: `<dataset-dir>/historical_picks.csv` — real
  historical pick order, for the identity-completeness check only.
- No fixed file format is mandated by the Python contract itself
  (`validate_schema`/`validate_leakage` accept any
  `Sequence[Mapping[str, Any]]`) — CSV-with-these-column-names is simply
  what the one existing entrypoint script expects. Parsed JSON records
  with the same keys would work identically.
- All `*_as_of`/`draft_date` fields must be ISO-8601 date strings
  (`date.fromisoformat`-parseable). Numeric fields (`platform_adp`,
  `PROJECTION_STAT_FIELDS` values, `projected_points_override`,
  `realized_weekly_points`) must be float-parseable. `rookie` is boolean
  or omitted.

## 12. Exact one-command calibration entrypoint

```
python scripts/run_historical_calibration_readiness_v1.py --dataset-dir "C:\path\to\dataset"
```

Expects `<dataset-dir>/historical_replay_rows.csv` and optionally
`historical_picks.csv`. Without `--dataset-dir`, or if that file isn't
found there, the identical pipeline runs against a deterministic
`SYNTHETIC_PIPELINE_TEST_ONLY` dataset instead — every output explicitly
labeled, never mistaken for a real result. Every run (real or synthetic)
writes `docs/codex/HISTORICAL_CALIBRATION_READINESS_REPORT.json` plus a
console summary.

**Note on a stale claim in that doc's own writeup**:
`HISTORICAL_CALIBRATION_READINESS_ENTRYPOINT_20260903.md` (committed
17:13 on 2026-09-03) states `CHAMPIONSHIP_EQUITY_CALIBRATION`/
`PICK_SCORE_EVALUATION`/`COST_OF_WAITING_CALIBRATION` are blocked
pending a `RankingResult` adapter. That adapter
(`historical_ranking_bridge_service.py`) was built later the same day
(commits at 17:39–17:50). **This handoff document is the current source
of truth on that point** — sections 6, 7, and 10 above supersede that
specific claim.

## 13. Errors / statuses on an invalid candidate package

| Layer | Behavior |
|---|---|
| `validate_historical_dataset` | Returns one `DATASET_VALIDATION_STATUSES` value (section 9) with full per-check detail attached |
| `load_historical_replay_dataset` | Returns `HistoricalReplayUnavailable(reason: str)` — never raises, never fabricates — when rows are empty or fail schema/leakage |
| `chronological_split` | Raises `HistoricalReplayDataError` for overlapping season assignments, an unassigned dataset season, or non-strictly-chronological split order |
| `run_replay_evaluation` | Raises `HistoricalReplayDataError` if a season has fewer available players than `team_count` |
| `build_ranking_result_from_historical_rows` | Raises `HistoricalRankingBridgeError` for empty rows or zero rows with usable stat data; `generate_rankings()`'s own insufficient-universe guard still applies and returns `RankingResult.errors` non-empty rather than raising |
| `build_historical_decision_state` | Raises `HistoricalDecisionStateError` if `pick_number < 1` |
| Readiness script top level | `BLOCKED_NO_DATASET_FOUND` for a missing/absent dataset directory — exit code 0, a validation block is a normal well-formed result, not a crash |

## 14. Current dataset admission gates

- **Schema**: every `REQUIRED_PRE_DRAFT_FIELDS` key non-empty, every
  `*_as_of`/`draft_date` field a parseable ISO date.
- **Identity**: every historical pick resolves 1:1 to a row `player_id`
  or carries a disclosed `identity_status` (only checked when
  `historical_picks` is supplied).
- **Leakage**: `BLOCKED_FEATURE_TOKENS` column-name check plus strict
  as-of date ordering (section 5).
- **Provenance**: `source_sha256` + `generated_at_utc` threaded through
  `ProjectionSnapshot`/`AdpSnapshot`/`HistoricalRankingBridgeResult`,
  and every `FeatureValue` carries its own `provenance_hash`/
  `source_as_of`/`feature_version` — the **same** provenance discipline
  the live DecisionBundle path uses
  (`score_provenance_service.build_score_provenance`), not a separate,
  weaker standard for historical data.
- **Temporal validity**: `chronological_split`'s strict train < validate
  < test season ordering, plus the 140-day outcome-maturity floor.
- **Scoring compatibility**: the caller-supplied `LeagueProfile` must
  carry the historical league's real scoring/roster rules for that
  season (never inferred), and `generate_rankings()`'s pre-existing
  insufficient-universe guard (≥ required+1 scored players per position)
  still applies unchanged to historical seasons.
- **Duplicate player-season**: at most one row per `(player_id,
  season)`.

## 15. What Historical Redraft Data HQ does NOT need to provide for the first useful 3-season calibration pilot

- **Real bracket/schedule/playoff data.** `season_level_metrics` can run
  entirely under `source=SIMULATED` for playoff/championship rate; real
  bracket data is only needed to ever claim `source=OBSERVED`, which
  this pass deliberately avoids.
- **Complete `PROJECTION_STAT_FIELDS` coverage for every player.** The
  bridge includes any player with at least one populated stat field (or
  K/DST override) and honestly excludes the rest via
  `excluded_players`; partial per-player stat coverage is acceptable as
  long as it is disclosed, not silently backfilled.
- **100% resolved historical-pick identity.** An explicitly disclosed
  `identity_status` on an unresolved pick does not block the dataset;
  only an undisclosed gap does.
- **Availability/injury/depth-chart status data.** `availability_status`
  is preferred-but-nonblocking; absent, the feature is simply not built
  rather than defaulted to a fabricated `ACTIVE`.
- **A pre-built RankingResult, DecisionBundle, or any NWR scoring
  output.** Draft Upgrade's own code builds all of that from raw rows;
  the producer lane supplies rows only.
- **More than one full past season to prove basic replay mechanics.**
  One season with a real full snake draft plus a genuinely-dated
  pre-draft board is the literal floor per the data contract; three
  consecutive seasons is Draft Upgrade's *preferred* target for a real
  chronological train/validate/test split, not a blocking minimum for
  the first useful signal.
- **A new missingness/status vocabulary.** Reuse `KNOWN`/`UNKNOWN`/
  `NOT_APPLICABLE`/`BLOCKED`/`STALE` and the existing `identity_status`
  disclosure convention rather than inventing new terms.
- **Any historical calibration/evaluation code, metric definitions, or
  the calibration report itself.** All already built, tested, and
  waiting only on real rows.

## What is currently missing (unchanged verdict)

Per `docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md`: no
full prior-season **redraft** snake draft (veterans + rookies, all
rounds, real pick order) exists anywhere in this repo for any past
season, and no genuinely-dated pre-draft ranking/ADP/projection board
for a past season exists either. The 2026 KHA fixture
(`sample_data/kha_real_draft_2026/`) is real, current-season evidence —
useful for the already-shipped rank-proxy shadow replay
(`scripts/run_kha_shadow_optimizer_replay_v1.py` →
`docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv`) — but it is **not** a
leakage-safe prior-season backtest substrate, and cannot become one no
matter how it's processed. This is the one gap only the Historical
Redraft Data lane can close; everything else in this document describes
code that is ready the moment real rows arrive.

## Process note

If Draft Upgrade discovers a new data need while consuming a candidate
package, it will emit a bounded `HISTORICAL_DATA_CONSUMER_REQUIREMENT`
rather than acquiring the source itself, and will not modify the
Historical Redraft Data worktree. Draft Upgrade owns validation,
admission, replay, calibration, and model consequences once a candidate
package arrives. No push. No merge. No deploy.
