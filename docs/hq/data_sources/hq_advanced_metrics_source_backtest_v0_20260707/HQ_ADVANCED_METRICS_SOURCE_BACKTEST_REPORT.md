# HQ Advanced Metrics Source Backtest V0 Report

Verdict: `YELLOW_HQ_ADVANCED_METRICS_BACKTEST_MIXED`

Branch: `work/lane-hq-advanced-metrics-source-backtest-v0-20260707`
HEAD: `a2e81615f202a3c1ab00c4b176c810f80ca98555`
Pre-run status: `?? tmp_advanced_metrics_lane.py`

This lane acquired public/legal review-only data directly from nflverse and ffopportunity release assets. Raw downloaded files were cached outside the repo at `C:\NWR_REVIEW\advanced_metrics_source_cache_20260707` and are not tracked. The repo packet contains compact inventories, join coverage, missingness, use gates, and a compact joined review panel only.

## Acquired Source Families

- espn_qbr_season
- espn_qbr_week
- ffopportunity_weekly
- ftn_charting
- ngs_passing
- ngs_receiving
- ngs_rushing
- pfr_advstats_pass
- pfr_advstats_rec
- pfr_advstats_rush

## Blocked/Failed Source Families

- None from public URL acquisition.


## HQ Baseline Confirmation

- Canonical branch used: `work/hq-parallel-control` via clean lane branch.
- Lane base/head: `a2e81615f202a3c1ab00c4b176c810f80ca98555`.
- `master` is absent and `origin/main` is stale versus HQ per the prior recon.
- The prior non-canonical advanced audit path `docs/hq/data_sources/advanced_metrics_audit_20260707/` is absent here.
- The master recon packet itself was not committed to HQ, so this lane used the recon facts from the request plus canonical HQ artifacts.
- Primary dirty repo was not touched.

## Shadow Backtest Headline

Position-specific season-forward complete-case backtests ran against `next_nwr_ppg`. In this bounded V0, advanced additions did not improve MAE versus the canonical core-usage baseline. That is useful evidence: source acquisition is green/yellow, but backtest evidence is mixed/negative and not ready for formula promotion.

## Guardrails

- No production rankings formula changed.
- No app/display integration added.
- No hidden sort, recommendations, or source-truth promotion.
- No paid/proprietary data copied.
- Exact PFF Elusive Rating remains `RED_BLOCKED_PROPRIETARY`.
- Name fallback joins were not used.
