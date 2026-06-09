# No-Blind-Tuning Calibration Pass

Date: 2026-05-12

Scope: active pack `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`
with active stats-first preview sources in
`local_exports/active_veteran_model_public_sources`.

## Summary

This pass did not change scoring weights. The named stats-first formula fixtures pass,
so there is no evidence yet for a silent formula retune. Two audit-layer bugs were
patched:

- Luther Burden receipt matching failed when the receipt source used `Luther Burden III`.
  The name normalizer stripped `II` before `III`, creating a bad match key.
- The named audit pair `Kaleb Johnson vs older fragile RB` resolved to Kyren Williams
  before actual older RB examples. It now resolves to Derrick Henry, Alvin Kamara,
  Austin Ekeler, or Joe Mixon before using Kyren as a fallback.

## Current Named Pair Read

| pair | current leader | classification | explanation |
|---|---|---|---|
| BTJ vs Luther Burden | Brian Thomas | source coverage / lifecycle evidence | BTJ has real year-two NFL evidence. Luther is a year-one bridge player with missing projection, depth chart, participation, and injury inputs. |
| Luther Burden vs Chase Brown | Chase Brown | source coverage / acceptable model disagreement | Chase has more NFL evidence. Luther's bridge prior is visible, but low confidence keeps this review-only. |
| Kaleb Johnson vs older fragile RB | Derrick Henry | data / source coverage | Kaleb is missing NFL evidence and remains low confidence. The comparison now uses an actual older RB example instead of Kyren. |
| JSN vs Tee Higgins | Tee Higgins | possible source-data review, not formula proof | Active normalized data gives Tee stronger target earning, production, and route role than JSN. If that contradicts trusted football stats, patch the imported source data, not weights. |
| Kyren vs Bijan | Bijan | passes sanity | Bijan stays ahead on dynasty hold and age-window profile. |
| Kyren vs Gibbs | Gibbs | passes sanity | Gibbs stays slightly ahead; Kyren remains high but flagged for RB workload/injury fragility. |
| Kyren vs Jeanty | Kyren | source coverage / lifecycle limitation | Jeanty has low-confidence year-one/incoming evidence. This should remain review-only until rookie/prospect and projection inputs are stronger. |

## Formula Imbalance Notes

No formula patch was applied. The evidence points to review/data issues rather than a
safe coefficient change:

- Many rows still carry `missing_participation_proxy`, so route/snap participation
  features are not as strong as they should be.
- Market values are neutral defaults for many players. This does not affect private
  model value, but it makes market-edge views unusable.
- Year-one bridge players with little NFL evidence should stay review-only. The bridge
  prior is visible, but it is not enough to declare a player decision-ready.
- JSN vs Tee needs a source-data check. The formula fixture proves that if JSN has
  superior target earning, production, route role, and age inputs, JSN beats Tee. The
  active imported inputs currently do not show that profile.

## Next Actions

1. Verify the raw nflverse/source rows behind JSN and Tee before changing any WR formula.
2. Fill or accept participation proxy gaps before trusting route/role-driven rankings.
3. Keep incoming and year-one players review-only unless rookie/prospect priors and
   current projection inputs are complete enough to explain the rank.
4. Load a legal market/liquidity source before using Model vs Market views for trade
   action.

Rankings remain review-only.
