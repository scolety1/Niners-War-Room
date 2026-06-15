# Rookie Analyzer Pick-Fit Engine - 2026-06-13

## Verdict

Verdict: GREEN.

Stage 4 adds explicit pick-fit fields to the rookie analyzer export. This is analyzer/export-only and does not approve production promotion, production ranking replacement, private-score changes, app or Streamlit wiring, probabilities, bands, outcome columns, or veteran outcome-head usage.

## Added Fields

The analyzer now includes:

- `fit_1_03`
- `fit_1_04`
- `fit_2_04`
- `fit_2_08`
- `fit_5_04`
- `best_pick_fit`
- `trade_down_signal`
- `emergency_stop_signal`

These are descriptive manual-review signals, not scores.

## 1.03 Handling

`1.03` remains not forced open.

Because no player is source-cleared for `1.03`, every row receives:

`fit_1_03 = trade_down_or_manual_review_only_no_player_cleared`

This means Tim can treat `1.03` as a trade-down/manual-review slot unless a later approved source-safe artifact explicitly opens it. Stage 4 does not backfill a `1.04` player into `1.03`.

## Pick-Fit Meaning

The fit fields describe whether a row is usable at a pick only as review context:

- `premium_fit_with_visible_warnings`: premium candidate can be considered only with visible warnings.
- `round2_rb_fit_with_visible_warnings`: Round 2 RB profile requires visible RB survival warnings.
- `round2_wr_fit_with_visible_warnings`: Round 2 WR profile requires visible WR evidence warnings.
- `5_04_asymmetric_dart_with_visible_warnings`: late dart profile with warnings attached.
- `manual_review_hold`: human review must happen before draft use.
- `do_not_use_blocked`: row is blocked.
- `do_not_use_unavailable`: row is unavailable.

## Trade-Down Signal

`trade_down_signal` is a manual context field:

- `yes_1_03_and_premium_bar_not_cleared` when a premium row exists but the premium bar is not clean ready;
- `yes_if_only_blocked_or_unavailable_options_remain` when the row is blocked or unavailable;
- `no` otherwise.

It does not recommend a market trade value and does not use trade calculators.

## Emergency Stop Signal

`emergency_stop_signal` flags manual stop conditions:

- blocked or unavailable rows;
- manual-review-required rows;
- visible injury review;
- visible source-conflict review.

It does not create probabilities, bands, or production scores.

## Guardrails Preserved

- Warnings remain visible.
- `rankable_with_warning` rows remain separate from clean `ready`.
- No probabilities or bands are created.
- No app-ready output is created.
- No production score is created.
- No market/rank/projection/trade/ADP/private-score input is used.
- No veteran outcome heads are used.
- `data/` remains untouched and uncommitted.
- `local_exports/` remains uncommitted.

## Stage 4 Gate

Stage 4 is GREEN if strict builds pass, direct harnesses pass, pick-fit fields are present in the analyzer output, `1.03` remains trade-down/manual-review only, and only the allowed Stage 4 tracked files are committed.
