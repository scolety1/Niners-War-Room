# Rookie CFB API Historical Feature Coverage Audit - 2026-06-15

## Executive verdict

Verdict: YELLOW.

The rookie lane has a configured CollegeFootballData API surface and verified local CFBD snapshots for 2021-2026, including 2021-2023 completed historical player production and team denominator data. That means the recent complete-window backtest years can be feature-built from local CFBD exports.

Manual 2010-2019 backfill is not proven avoidable yet. It may be avoidable if Tim enables the existing CFBD API key/live-cache gate or provides an approved cached CFBD export for 2010-2020, but this audit did not make live API calls because `CFBD_API_KEY` is not configured and `MODEL_V4_LIVE_API_ENABLED=false`.

No tuning, v2 board, production ranking, private-score overwrite, app wiring, probability, band, hidden sort key, or promoted artifact was created.

## API/config audit

| Item | Result |
| --- | --- |
| CFBD API base | configured as `https://api.collegefootballdata.com` |
| CFBD API key | missing; value not printed |
| Live API gate | disabled |
| `.env` | absent; only `.env.example` present |
| Cache root | `local_exports/api_cache` |
| Live sampling | skipped because key/gate are not both available |

The repo fails closed for live API work. This is correct for source safety and secret hygiene.

## Years sampled

The audit sampled/planned checks for 2010, 2015, 2020, 2021, 2022, 2023, and 2026.

Local cached CFBD samples:

| Year | Passing | Rushing | Receiving | Team denominators | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| 2010 | 0 | 0 | 0 | 0 | not locally cached; live API not enabled |
| 2015 | 0 | 0 | 0 | 0 | not locally cached; live API not enabled |
| 2020 | 0 | 0 | 0 | 0 | not locally cached; live API not enabled |
| 2021 | 4,732 | 10,555 | 13,625 | 8,190 | cached |
| 2022 | 7,266 | 16,115 | 20,915 | 8,253 | cached |
| 2023 | 6,867 | 15,070 | 19,875 | 8,376 | cached |
| 2026 | 0 | 0 | 0 | 0 | season not complete; live API not enabled |

## Local cache inventory

| Cache | Coverage | Notes |
| --- | --- | --- |
| `local_exports/model_v4/prospect_sources/latest/files/source_project/data/college_football_data/raw` | 2021-2026 | manifest-only local snapshot; 2026 player/team rows are zero because the season is not complete |
| `local_exports/model_v4/prospect_sources/latest/files/source_project/data/college_football_data/processed` | 2021-2026 | processed college player seasons, market share, team seasons, draft, recruiting, roster |
| `data/college_football_data/raw` | 2025 only | untracked local cache; inspected read-only and not committed |

## Feature families available

| Feature family | Local years | API/cache source | Leakage risk | Status |
| --- | --- | --- | --- | --- |
| College production box score | 2021-2025 | CFBD `/stats/player/season` | low | available for 2021-2023 backtest years |
| Team denominators | 2021-2025 | CFBD `/stats/season` | low | available for market-share derivation |
| Market share / dominator | 2021-2025 | local processed CFBD `college_market_share` | medium | usable only if derived from same-season raw stats |
| Draft capital / identity | 2021-2026 | CFBD `/draft/picks` | mixed | completed draft round/pick factual; rank/grade fields quarantined |
| Recruiting rank/ratings | 2021-2026 | CFBD `/recruiting/players` | high | not approved as private score input in this audit |
| Usage/advanced charting | none found | not in audited CFBD cache | medium | still needs licensed/manual source |
| Injury history | none found | not in audited CFBD cache | medium | still needs Tim-provided/source-safe file |

## Feature coverage matrix summary

The generated matrix has 28 rows: 7 sampled years x QB/RB/WR/TE.

| Coverage status | Rows | Meaning |
| --- | ---: | --- |
| `green_local_cache_available` | 12 | 2021-2023 for QB/RB/WR/TE have player stats, team denominators, and processed market-share data |
| `red_not_available_locally` | 12 | sampled 2010, 2015, and 2020 have no local CFBD cache |
| `yellow_future_or_current_year_no_completed_stats` | 4 | 2026 has no completed college season stats |

Position-level implications:

- QB: passing plus rushing production can be built for cached completed years.
- RB: rushing plus receiving production can be built for cached completed years.
- WR/TE: receiving plus occasional rushing production can be built for cached completed years.
- All positions: team denominators and same-season market-share features are available for 2021-2023.

## Can 2010-2019 be API-built instead of manually provided?

Verdict: not proven yet, but likely worth testing.

The existing CFBD import pattern already uses endpoints that should be the correct source family for the missing data:

- `/stats/player/season` for passing, rushing, and receiving;
- `/stats/season` for team denominators;
- processed `college_market_share` for same-season player/team share features.

However, this run cannot confirm 2010-2019 availability from the live API because no CFBD credential is configured and the live API gate is disabled. Tim should not manually backfill 2010-2019 until one narrow cached CFBD sample pass is approved and run for 2010, 2015, and 2020. If those years return the same categories and team stats, the manual production backfill should be avoidable.

## Missing fields

Still missing from CFBD/API cache:

- 2010-2020 local player season stats and team denominator cache;
- route participation, YPRR, targets per route, contested catch, YAC, missed tackles, yards after contact, and pass-pro fields;
- historical pre-draft injury flags;
- historical ADP/market overlay, which must remain display-only;
- a locked identity QA pass for any newly fetched older CFBD rows.

## What Tim should provide or approve

Priority 1:

- CFBD API key plus explicit approval for a cached, narrow live sample/import. Do not print the key or commit it.
- Or an approved cached CFBD export for 2010-2020 player stats and team stats.

Priority 2:

- Historical college injury flags.
- Licensed/manual advanced charting for route, YAC, missed-tackle, yards-after-contact, and pass-pro context.

Priority 3:

- Historical rookie ADP/market overlay for display-only manual draft context.

## Rate-limit/cache/API risk

- Live API calls are currently blocked by design.
- A future run should fetch narrowly and cache locally under `local_exports/`, then produce manifests and row-count checks before any feature backfill.
- Do not full-fetch 2010-2020 until the sample years prove endpoint availability and field stability.
- Do not commit `data/` or `local_exports/`.
- Do not allow rank, grade, projection, market, or recruiting-rating fields into private scoring without a separate source-safety approval.

## Anti-cheat / leakage audit

| Check | Result |
| --- | --- |
| No tuning performed | PASS |
| No v2 board created | PASS |
| Outcome labels not used as features | PASS |
| Player names/IDs used only for identity/display/join audit | PASS |
| ADP/market excluded from private scoring | PASS |
| CFBD preDraftRanking/preDraftGrade/recruiting ranks quarantined | PASS |
| No player/class/school/team-specific tuning rule added | PASS |
| No future stats or known outcomes used as features | PASS |
| No API keys printed or committed | PASS |

## Exports created

Local-only exports:

- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/cfb_api_config_inventory_20260615.csv`
- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/cfb_api_cached_data_inventory_20260615.csv`
- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/cfb_api_sample_plan_and_results_20260615.csv`
- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/cfb_api_feature_coverage_matrix_20260615.csv`
- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/cfb_api_feature_family_summary_20260615.csv`
- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/cfb_api_missing_fields_and_tim_requests_20260615.csv`
- `local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615/README_CFB_API_HISTORICAL_FEATURE_COVERAGE_AUDIT_20260615.md`

These exports are audit-only and were not committed.

## Commands run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `rg -n --hidden -S "CFBD|CollegeFootballData|collegefootballdata|cfb|college football|api_key|API_KEY|CFB|Bearer|Authorization|dotenv|\\.env" -g "!data/**" -g "!local_exports/**" -g "!.git/**"`
- `Get-Content .env.example`
- `Get-Content src\config\api_settings.py`
- `Get-Content config\api_source_permissions.csv`
- safe API-config inspection through `get_api_settings()`
- local CFBD cache inventory commands
- `python scripts\rookie_framework\audit_rookie_cfb_api_historical_feature_coverage_v1.py`
- `python tests\test_rookie_cfb_api_historical_feature_coverage_v1.py`
- `python -m py_compile scripts\rookie_framework\audit_rookie_cfb_api_historical_feature_coverage_v1.py tests\test_rookie_cfb_api_historical_feature_coverage_v1.py`

## Final recommendation

Do not tune yet and do not create a v2 board.

Next rookie-only task: run a narrow, cached CFBD sample import proposal for 2010, 2015, and 2020 only after Tim explicitly provides/configures the CFBD key and approves live cached sampling. If that sample is GREEN, build a 2010-2020 CFBD production/team-denominator backfill package and keep advanced charting/injury needs separate.
