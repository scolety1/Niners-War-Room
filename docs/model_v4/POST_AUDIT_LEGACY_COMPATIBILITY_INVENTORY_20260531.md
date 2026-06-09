# Post-Audit Legacy Compatibility Inventory

Date: 2026-05-31

Mode: paused / inspect-and-repair only.

Purpose: Inventory only. Identify old services and pages that still carry legacy,
market-edge, target, buy, sell, or trade-for compatibility lanes after the
review-only source-routing repair. This is an inventory only; do not delete,
rewrite, tune, promote, or mutate these lanes from this document.

## Guardrails

- Do not tune formulas.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, or trade-calculator
  logic to private value.
- Do not turn review labels into final trade, cut, keep, draft, buy, sell,
  defer, or target recommendations.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, or generated model outputs.

## Classification Legend

- `active_repaired`: currently part of the repaired review-only route and
  covered by focused sentinels.
- `compatibility_only`: old names or API fields retained so existing pages or
  tests keep working; not a primary score, recommendation, or source of private
  value.
- `deprecated`: old lane is not part of the repaired path and should not be
  used for new work.
- `needs_later_quarantine`: should receive comments, adapters, or stronger
  tests in a later cleanup task; no behavior change is authorized here.

## Inventory

| File | Classification | Compatibility / Legacy Lane | Current Constraint |
|---|---|---|---|
| `src/services/review_score_envelope_service.py` | `active_repaired` | Shared `ReviewScoreEnvelope` schema, `checkpoint_review_score`, `dynasty_asset_value_review_score`, `legacy_active_pack_score`, `market_display_only`, allowed/blocked use, warnings, and lineage metadata. | Canonical source resolver must fail closed for unknown, market-only, or legacy lineages. Market context is display-only and cannot populate primary review score. |
| `src/services/player_board_score_service.py` | `active_repaired` | Player Board score hydration from `current_player_value_review_rows.csv` using `checkpoint_review_score`; old active-pack `private_score` is exposed only as `legacy_active_pack_score`. | Player Board primary value must not default to active-pack `private_score`; legacy values are comparison-only. |
| `src/services/market_gap_service.py` | `active_repaired` | Cross-asset market context rows expose `market_display_only=True` and legacy `trade_for_rows` naming on a display-only payload. | Market, ADP, rank, projection, mock, startup, or consensus context must remain display-only and cannot fill a primary review score. |
| `src/services/model_v4_sprint14c_trade_review_service.py` | `active_repaired`, `compatibility_only` | Canonical external asset review rows remain the repaired review-only lane; `TRADE_FOR_HEADER` and `trade_for_rows` are compatibility aliases for external asset rows. | Treat `trade_for_rows` as an alias only. It must not become a trade-for recommendation or acquisition instruction. |
| `src/services/trade_service.py` | `compatibility_only`, `needs_later_quarantine` | Older Trade Central board still exposes service API names including `sell_rows`, `buy_rows`, `buy_signals`, `market_edge_rows`, `market_edge_warning`, `legacy_active_pack_score`, and market-edge sort labels. | Keep API stable until a future adapter/quarantine task. Do not build new private value, recommendations, or formula behavior from these compatibility names. |
| `app/pages/04_trade_central.py` | `active_repaired`, `compatibility_only` | Page-local names have been neutralized to roster/external/context wording, but the page still reads compatibility service fields such as `board.sell_rows`, `board.buy_rows`, `board.buy_signals`, and `board.market_edge_rows`. | Visible UI must remain review-only. Compatibility field reads are allowed only as service API glue. |
| `src/services/asset_board_service.py` | `compatibility_only`, `needs_later_quarantine` | Unified asset board still carries `legacy_active_pack_score`, `score_lineage_class`, and `score_source_column` metadata for old active-pack comparisons. | Legacy active-pack values remain comparison-only; they must not become primary model value. |
| `app/pages/05_rankings.py` | `active_repaired` | Player Board displays `legacy_active_pack_score` as "Legacy Score (Comparison Only)" and routes primary value through repaired Player Board score service. | Keenan Allen `82.4` and Darius Slayton `78.88` legacy active-pack scores must not appear as primary Player Board Model Value. |
| `app/pages/06_draft_board.py` | `active_repaired` | Rookie and pick review UI still includes historical warning codes such as review-only no final recommendation language. | Draft Board remains review-only; labels must not become final draft recommendations. |
| `app/pages/08_june15_review.py` | `active_repaired`, `compatibility_only` | June 15 review page displays generated review-only rows and warning labels, including legacy "No final recommendation" strings and model-value columns sourced from review exports. | The page may show review bands and warnings only; it must not create final trade, cut, keep, draft, buy, sell, defer, or target recommendations. |
| `src/config/constants.py` | `compatibility_only`, `needs_later_quarantine` | `DEFAULT_DATA_PACK` still points at the legacy active pack root for older services. | Do not mutate active data packs in cleanup tasks. Repaired score services must quarantine active-pack `private_score`. |
| `src/services/market_influence_policy_service.py` | `compatibility_only` | Shared helpers still compute market status, market warnings, and market-edge classifications for display lanes. | Market context can inform warnings and display rows only; it cannot become private value input. |
| `src/services/legacy_label_quarantine_service.py` | `active_repaired` | Quarantine helper for old recommendation/action labels. | Keep labels neutralized and review-only on repaired surfaces. |

## Deprecated / Do-Not-Extend Lanes

- Active-pack `private_score` from `local_exports/data_packs/...` is deprecated
  as a primary Player Board score source.
- Old Trade Central service fields named `sell_rows`, `buy_rows`, and
  `buy_signals` are compatibility-only until a future adapter removes or wraps
  them.
- `trade_for_rows` and `TRADE_FOR_HEADER` are compatibility aliases for
  External Asset Reviews, not final trade-for instructions.
- Any `market_edge` display lane is display-only unless a later audited task
  explicitly says otherwise.

## Later Quarantine Candidates

- Add short comments or adapter constants around `src/services/trade_service.py`
  compatibility fields.
- Add comments near `TRADE_FOR_HEADER` and `trade_for_rows` in
  `src/services/model_v4_sprint14c_trade_review_service.py`.
- Add comments near `DEFAULT_DATA_PACK` consumers that still depend on legacy
  active-pack data.
- Consider a future service API rename only after tests can prove visible UI,
  exports, and generated outputs are unchanged.
