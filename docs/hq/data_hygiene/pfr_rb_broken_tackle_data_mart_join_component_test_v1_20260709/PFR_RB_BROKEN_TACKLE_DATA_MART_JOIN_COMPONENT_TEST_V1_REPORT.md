# PFR RB Broken Tackle Data Mart Join / Component Test V1 Report

## Verdict

`RED_PFR_RB_BROKEN_TACKLE_NO_INCREMENTAL_SIGNAL`

## Executive Summary

Actual narrow PFR RB broken-tackle values were found locally in the nflverse public PFR advanced rushing parquet cache. The primary source hash is `28f44be62bd30291d5310ff62a453025d804b4d0b6720da820cb6cd943c45187`, matching the hash recorded by the prior PFR addendum. The lane built a review-only sidecar and ran a focused RB-only component signal test using lagged source season N to target season N+1.

The result is not production, not a broad PFR promotion, and not ranking integration. PFR broken-tackle context is partial because source coverage begins in 2018, not 2013. The joined values are descriptive, but the focused component test did not show incremental signal beyond PYF or multi-year production, so this branch should be parked rather than advanced into another formula test.

## Source and Coverage

- Source file: `C:\NWR_REVIEW\pfr_advanced_source_provenance_hardening_v1_20260707\advstats_season_rush.parquet`
- Source seasons: `2018-2025`
- Lagged source seasons tested: `2018-2024`
- Formula Mart RB rows: `1429`
- Lag-eligible RB rows: `789`
- Joined/tested RB rows: `716`
- Lag-eligible join coverage: `90.7%`
- Overall RB sidecar coverage: `50.1%`
- Missingness among lag-eligible rows: `9.3%`

## Signal Result

- PYF Spearman on same joined RB rows: `0.655`
- Raw broken-tackle Spearman: `0.595`
- Per-game broken-tackle Spearman: `0.553`
- Best PFR primary signal: `PFR_BRK_TKL_RAW_REVIEW_ONLY`
- Best PFR delta vs PYF on same rows: `-0.060`
- Season-stability positive raw delta seasons: `0 / 7`

## Interpretation

PFR broken tackles do not replace PYF or multi-year production. Raw and per-game tackle-breaking values trail PYF on the same joined rows and trail PYF in every tested target season. High broken-tackle buckets mostly identify productive prior-year RBs that the existing production fields already capture. The output files include partial residual and incremental diagnostic checks; those are review-only diagnostics, not formula weights.

`per_attempt` remains diagnostic only because it can overstate low-attempt players.

## Gates Preserved

- PFR production/model-use remains blocked.
- Broad PFR feature promotion remains blocked.
- PFR QB passing remains blocked.
- PFF Elusive Rating and `nwr_elusive_proxy_review_only` remain blocked.
- Production/model-use and rankings integration remain blocked.
- App/runtime/model behavior did not change.
- Canonical `local_exports` was not written.
