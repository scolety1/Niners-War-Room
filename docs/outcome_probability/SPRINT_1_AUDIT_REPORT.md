# Sprint 1 Audit Report - Historical Scoring and Outcome Labels

Date: 2026-06-10

Branch: `nwr-outcome-build-sprint-1-scoring-labels`

Verdict: `PASS WITH TODOs`

## Executive Summary

Build Sprint 1 is safe as a scoring/label scaffold. It does not create player probabilities, does not create app percentage values, does not overwrite active Rankings, and does not train a model.

The one audit finding was a small forbidden-input coverage gap: `rotowire_value` and `prior_fantasy_draft_history` were not explicit fragments in `forbidden_input_violations`. That was repaired and covered by test.

Remaining TODOs are expected Sprint 1 boundary items: historical raw player-week data, scoring calendar persistence, player identity dimension, opportunity/injury policy inputs, and row-per-label audit exports.

## Files Audited

Sprint 1 files:

- `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`
- `src/services/nwr_outcome_scoring_service.py`
- `tests/test_nwr_outcome_scoring_service.py`
- `docs/outcome_probability/BUILD_PROCESS_PACKET.md`
- `tests/test_outcome_probability_build_packet.py`

Prior-prep files inspected but kept separate:

- `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md`
- `src/services/outcome_column_package_service.py`
- `scripts/validate_outcome_column_package.py`
- `tests/test_outcome_column_integration_contract.py`
- `tests/test_outcome_column_package_service.py`

## Audit Answers

1. Scoring config matches required weights: PASS.
   - Passing yards: `0.03333333333333333`
   - Passing TD: `3.0`
   - INT: `-1.0`
   - Rush yards: `0.1`
   - Receiving yards: `0.1`
   - Rush TD: `4.0`
   - Receiving TD: `4.0`
   - Rush first down: `0.4`
   - Receiving first down: `0.4`
   - Reception: `0.0`
   - Fumble lost: `-1.0`
   - Return yards: `0.03333333333333333`
   - Return TD: `4.0`
   - Passing/rushing/receiving 2-point conversions: `2.0`
   - Passing first down: `0.0`
   - Sack suffered: `0.0`

2. Scoring weights are versioned/configurable: PASS.
   - Config lives at `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`.
   - Service loads it through `load_scoring_rules`.
   - Defaults exist in `ScoringRules` for pure tests, but the canonical values are in the versioned config.

3. Weekly scoring reconstructs from raw stat components: PASS.
   - `score_player_week` uses passing/rushing/receiving/turnover/return raw components.
   - It does not import fantasy totals as scoring labels.

4. Kickers ignored/not applicable: PASS.
   - `aggregate_season_scores` includes only `QB/RB/WR/TE`.
   - Replacement-line logic includes only modeled positions and FLEX positions.

5. Qualified PPG minimum games default: PASS.
   - Default is `8`.
   - Config and service both carry `qualified_games_min`.

6. Internal finish labels: PASS.
   - QB: Top 6 / 12 / 18 / 24.
   - RB: Top 6 / 12 / 24 / 36 / 48.
   - WR: Top 6 / 12 / 24 / 36 / 48.
   - TE: Top 3 / 6 / 12 / 18 / 24.

7. App-tier labels: PASS.
   - Difference-maker = QB Top 6 / RB Top 12 / WR Top 12 / TE Top 3.
   - Starter = QB Top 12 / RB Top 24 / WR Top 24 / TE Top 6.
   - Useful = QB Top 18 / RB Top 36 / WR Top 36 / TE Top 12.

8. Difference-maker implies Starter implies Useful: PASS.
   - `app_tier_labels` explicitly cascades tier booleans.

9. Replacement-line algorithm: PASS WITH TODO.
   - Required slots are filled first.
   - FLEX is filled from remaining RB/WR/TE.
   - Threshold lines and cutoff tie counts are stored.
   - The service sorts deterministically for selecting a bounded set, but downstream line interpretation uses threshold scores rather than player-id-based membership. Future full-table audit should ensure above-line flags use `>= threshold`.

10. Future-window labels nullable when censored: PASS.
    - `future_window_label` returns `None` when the full window is not observable.

11. Injury-lost / ambiguous / replacement-level / bust scaffold: PASS WITH TODO.
    - `companion_labels` prevents injury-lost and ambiguous seasons from being forced into bust.
    - Replacement-level and bust are mutually safe.
    - Full inference requires future opportunity/injury data and should not be guessed.

12. Forbidden-input detection coverage: PASS AFTER FIX.
    - Covers FantasyPros, ADP, consensus, startup, trade calculators, public projections, RotoWire rankings/projections/outlooks/values, market rank, league rank, prior/private score, prior fantasy draft history, and hindsight notes.

13. Forbidden fields used by Sprint 1 scoring/label logic: PASS.
    - Forbidden names appear only in the blocked-fragment detector, docs, and tests.
    - They are not used by `score_player_week`, season aggregation, finish labels, app-tier labels, or replacement-line computation.

14. Critical guardrail tests: PASS.
    - Tests cover scoring weights, raw component scoring, season totals, qualified PPG, duplicate player-week keys, monotonic ranks, K exclusion, finish/tier labels, companion label precedence, censoring, forbidden inputs, and replacement-line tie thresholds.

15. Prior-prep files dependency: PASS.
    - Prior-prep files are separate landing-zone/validator work.
    - Sprint 1 scoring/label tests do not require `outcome_column_package_service`.
    - They can be committed separately or together, but Sprint 1-only commit should exclude prior-prep files.

## Scoring Mismatch

None found.

## Leakage Concern

No active leakage found in Sprint 1 logic.

Small repaired issue:

- Added explicit forbidden fragments for `rotowire_value` and `prior_fantasy_draft_history`.

## Prior-Prep Dependency Assessment

The prior-prep files are useful for future incoming outcome zip validation, but they are not required for Sprint 1 historical scoring and labels. They should not be included in a strict Sprint 1-only commit unless the user wants to include landing-zone prep in the same checkpoint.

## Tests Run

- `pytest tests/test_nwr_outcome_scoring_service.py tests/test_outcome_probability_build_packet.py -q`
  - Result: `14 passed`
- Focused guardrail/outcome set:
  - `tests/test_outcome_column_integration_contract.py`
  - `tests/test_outcome_column_package_service.py`
  - `tests/test_dynasty_rankings_page.py`
  - `tests/test_player_detail_card_service.py`
  - `tests/test_player_detail_card_component.py`
  - `tests/test_birthday_demo_guardrails.py`
  - Result: `42 passed`
- Combined rerun:
  - Result: `56 passed`
- `py_compile` on changed Python files:
  - Result: passed
- `ruff check` on changed Python/test files:
  - Result: passed
- `git diff --check`
  - Result: passed

## Sprint 1 Commit Safety

Sprint 1 files are safe to commit separately after review.

Exact Sprint 1-only add list:

```powershell
git add -- `
  config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json `
  src/services/nwr_outcome_scoring_service.py `
  tests/test_nwr_outcome_scoring_service.py `
  docs/outcome_probability/BUILD_PROCESS_PACKET.md `
  docs/outcome_probability/SPRINT_1_AUDIT_REPORT.md `
  tests/test_outcome_probability_build_packet.py
```

Do not include these in a strict Sprint 1-only commit:

```powershell
docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md
src/services/outcome_column_package_service.py
scripts/validate_outcome_column_package.py
tests/test_outcome_column_integration_contract.py
tests/test_outcome_column_package_service.py
```

## Proceed To Sprint 2?

Yes, after the Sprint 1 checkpoint is reviewed and committed. Do not build Sprint 2 in this audit pass.

## Remaining Blockers

- Historical raw weekly stat components are not committed.
- Scoring calendar table/export is not yet implemented.
- Historical player dimension/crosswalk is not yet wired.
- Injury/opportunity evidence is needed before true injury-lost, ambiguous, replacement-level, and bust inference.
- Row-per-label audit export is not persisted yet.
- Point-in-time feature legality belongs to Sprint 2.
