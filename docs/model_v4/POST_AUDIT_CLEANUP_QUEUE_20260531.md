# Post-Audit Cleanup Queue

Date: 2026-05-31

Mode: paused / inspect-and-repair only.

This queue follows the external audit verdict:
`repair_gate_passed_for_review_only_source_routing`.

Purpose: clean internal naming and dead legacy lanes before any formula work. This is
not a tuning queue.

## Hard Guardrails

- Do not tune formulas.
- Do not change model weights, veteran age curves, rookie weights, pick baselines,
  VORP, replacement formulas, market-gap thresholds, confidence cap magnitudes, or
  startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, or trade-calculator
  logic to private value.
- Do not turn review labels into final trade, cut, keep, draft, buy, sell, defer,
  or target recommendations.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, or generated model outputs.
- Do not run blind `git add .`.

## Repeatable Cleanup Prompt

```text
You are working on the Niners War Room dynasty fantasy football analyzer.

Repo:
C:\Dev\niners-war-room

Current mode:
Paused / inspect-and-repair only.

Read first:
1. docs/model_v4/5-30_NEW_CHAT_HANDOFF.md
2. docs/model_v4/REPAIR_TASK_QUEUE_20260530.md
3. docs/model_v4/MODEL_V4_REPAIR_EXTERNAL_AUDIT_PACKAGE_20260530.md
4. docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md
5. The next queued cleanup task marked Pending or In progress

Implement exactly one cleanup task.

Hard guardrails:
- Do not tune formulas.
- Do not change model weights, veteran age curves, rookie weights, pick baselines,
  VORP, replacement formulas, market-gap thresholds, confidence cap magnitudes, or
  startup-slot conversion.
- Do not add ADP/rankings/projections/consensus/market/trade-calculator logic to
  private value.
- Do not turn review labels into final trade/cut/keep/draft/buy/sell/defer/target
  recommendations.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, or generated model outputs.
- Do not run blind `git add .`.

Before editing, briefly confirm:
1. current cleanup task,
2. allowed scope,
3. forbidden scope,
4. tests you will add/run.

Then:
1. Implement only that task.
2. Add/update focused tests.
3. Run focused tests.
4. Update docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md with task status and audit notes.
5. End with changed files, tests run, results, remaining risks, and next recommended cleanup task.
```

## Queue

| ID | Cleanup Task | Allowed Scope | Tests | Status | Audit Notes |
|---|---|---|---|---|---|
| C01 | Neutralize Trade Central internal variable names | Rename internal `sell_frame`, `buy_frame`, `sell_tab`, `buy_tab`, `filtered_buys`, and related local-only names in `app/pages/04_trade_central.py` to roster/external/context terms without changing visible UI, service APIs, exports, formulas, or data semantics | Static UI/copy tests plus `tests/test_navigation_compression.py` | Done | Renamed local page variables to `roster_context_frame`, `external_asset_context_frame`, `market_context_frame`, `context_pairing_frame`, `roster_tab`, `external_asset_tab`, and `filtered_external_assets`; preserved compatibility service fields such as `board.buy_signals`; focused UI tests and ruff pass. |
| C02 | Add legacy/deprecated service inventory | Create a docs inventory of old services/pages still carrying legacy, market-edge, target, buy, sell, or trade-for compatibility lanes; classify each as active repaired, compatibility-only, deprecated, or needs later quarantine | Docs readback test | Done | Added `POST_AUDIT_LEGACY_COMPATIBILITY_INVENTORY_20260531.md` with active repaired, compatibility-only, deprecated, and needs-later-quarantine classifications; readback test covers known legacy/private-score, market display, trade service, and trade-for alias lanes. |
| C03 | Quarantine comments for compatibility-only legacy lanes | Add short code comments or constants on compatibility-only fields that must remain non-primary, especially old trade/asset lanes exposing legacy active-pack values; no behavior changes | Focused tests proving primary score fields remain blank/comparison-only | Done | Added quarantine markers/comments to old Trade Central compatibility fields, Unified Asset legacy active-pack score disclosure, and Sprint 14C `trade_for_rows`/`TRADE_FOR_HEADER` aliases; focused marker and existing legacy-score behavior tests pass. |
| C04 | Strengthen static banned-term checks for internal UI copy | Expand static tests so repaired pages cannot reintroduce visible `Buy Targets`, `Sell Candidates`, `Trade-For Candidate`, `target`, `edge`, or recommendation wording on main review pages | UI copy tests | Done | Added visible-string AST banned-phrase test for main repaired pages and neutralized user-facing `Model Edge`, route/target/snap, pick-defer, and legacy recommendation-label copy; preserved internal keys and behavior. |
| C05 | Full focused-suite rerun after cleanup | Re-run final sentinel suite plus cleanup tests; update residual risk notes | Existing focused suite | Done | Re-ran final sentinel suite plus C02-C04 cleanup tests: `81 passed`; later readiness pass ran full repo suite: `1214 passed`; full `ruff check app src tests` passed. |

## Definition Of Done

This cleanup queue is done when:

- Visible UI remains neutral and review-only.
- Internal naming on repaired surfaces no longer invites buy/sell/target confusion.
- Legacy and market compatibility lanes are documented as comparison-only or
  display-only.
- Final sentinel tests still pass.
- No formula tuning, source data mutation, active state mutation, or recommendation
  logic has occurred.

## Recommended First Task

Start with C01. It is local, low-risk, and directly addresses the external audit’s
clearest code-hygiene finding.
