# NWR DynastyProcess Sustainable Connector V1 - 2026-06-22

## Verdict

GREEN for connector, cache, transform, and review-only artifacts. DynastyProcess is now available as a reusable public market baseline, player ID crosswalk, age source candidate, and pick-value sanity layer. It is not wired into app ranking, model scoring, candidate rank, hidden sort, or source truth.

## Sources And Attribution

- Data repo: https://github.com/dynastyprocess/data
- Values methodology: https://dynastyprocess.com/values/
- Open data file list: https://dynastyprocess.com/
- License: GPL-3.0 in the DynastyProcess data repo.

DynastyProcess says its values are produced from FantasyPros Dynasty ECR and transformed into trade values with an exponential decay approach. NWR treats this as external market context only.

## Refresh Method

Connector:

- `src/connectors/dynastyprocess_connector.py`

Build command:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\build_dynastyprocess_market_baseline_v1.py --snapshot-label 20260623_dynastyprocess_v1
```

Recommended refresh command:

```powershell
.\.venv\Scripts\python.exe scripts\refresh_dynastyprocess_market_baseline_v1.py
```

Raw cache path:

- `C:\NWR_SHARED_DATA\market_sources\dynastyprocess\20260623_dynastyprocess_v1`

The connector fetches explicit upstream file names, records source URL, fetch timestamp, row count, scrape date where present, ETag, SHA-256, and current upstream GitHub commit metadata. Raw upstream files remain outside the repo and must not be committed.

Snapshot metadata:

- Upstream commit: `a38911c0080e5623741eaa3bfcd63d1db98a5342`
- Upstream commit date: `2026-06-19T07:33:57Z`
- Fetch timestamp: `2026-06-23T22:37:05+00:00`
- Upstream scrape date for values/ECR files: `2026-06-19`
- Freshness status: `GREEN_CURRENT`

## Refresh Schedule And Freshness

- Upstream workflow: `weekly-playervalues`
- Upstream cron: `23 2 * * 5`
- Upstream time: Friday `02:23 UTC`
- NWR recommended pull time: Friday `06:00 America/Denver`
- Backup retry: Saturday morning America/Denver when Friday pull sees stale or unchanged data.

Freshness statuses:

- `GREEN_CURRENT`: scrape date is within expected weekly window and newer than the prior local snapshot.
- `GREEN_SAME_WEEK_NO_CHANGE`: scrape date is current week but values are unchanged from the prior local snapshot.
- `YELLOW_STALE`: scrape date is older than 8 days or upstream commit is older than expected.
- `RED_STALE`: scrape date is older than 14 days.
- `YELLOW_FETCH_FAILED_USING_LAST_CACHE`: upstream fetch failed but a usable local cache exists.
- `RED_NO_VALID_CACHE`: fetch failed and no usable cache exists.

Every derived artifact now includes freshness columns, including `freshness_status` and `market_baseline_stale_warning`. Yellow/red rows must be shown as stale market context if exposed later.

## Upstream Files

| File | Rows | SHA-256 |
| --- | ---: | --- |
| `values.csv` | 769 | `2200422a58320add7c09ff3a805acf5c1d2998fc6561029cbedcb3029edac4bc` |
| `values-players.csv` | 684 | `a95e5f6937359b4faf287a85d0be4478de447b378f1d94eb11c182c73a1ea682` |
| `values-picks.csv` | 85 | `67ea19002e29f49e53c4cc8aa1b75654c00d1539912d89fb788e5219e86a3148` |
| `db_playerids.csv` | 12,462 | `ec74fa354944042ff90b5f2220c0dc5ee050eb9966a6db3b6c83a718ac00695d` |
| `db_fpecr_latest.csv` | 6,967 | `e8659aa6ad471e93cf7f7d41fe7ef805cd11e06f1ddf78f04e076bc24843ab6d` |

## Schema Fields

Validated required fields:

- Player values: `player`, `pos`, `team`, `age`, `draft_year`, `ecr_1qb`, `ecr_pos`, `value_1qb`, `scrape_date`, `fp_id`
- Pick values: `player`, `pos`, `ecr_1qb`, `ecr_2qb`, `scrape_date`, `pick`
- Player IDs: `fantasypros_id`, `sleeper_id`, `gsis_id`, `name`, `position`, `team`, `birthdate`, `age`, `draft_year`
- ECR latest: `fp_page`, `page_type`, `ecr_type`, `player`, `id`, `pos`, `team`, `ecr`, `scrape_date`

If any required field disappears, the connector raises a schema error instead of silently producing stale joins.

## Derived Artifacts

Repo-safe outputs:

- `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_market_baseline_context.csv`
- `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_pick_value_context.csv`
- `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_playerid_crosswalk_audit.csv`
- `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_nwr_join_coverage.csv`
- `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_freshness_report.csv`

Every market row carries:

`Display-only DynastyProcess market baseline; not NWR source truth; not used for model inputs, candidate rank, or hidden sort.`

## Join Coverage

| NWR source | Rows | DP matches | Match rate | NWR age rows before DP | DP age rows when matched | Possible age gain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full dynasty rankings | 240 | 232 | 96.67% | 3 | 233 | 230 |
| Frozen board 66 | 66 | 49 | 74.24% | 40 | 49 | 9 |
| PDF free-agent pool | 77 | 62 | 80.52% | 77 | 62 | 0 |
| Current candidate overlay | 66 | 49 | 74.24% | 40 | 49 | 9 |
| Combined NWR universe | 380 | 330 | 86.84% | 117 | 330 | review |

Join order:

1. `sleeper_id`, `gsis_id`, or `fp_id` when available.
2. Exact player name plus position.
3. Normalized player name plus position.
4. Unmatched players remain manual review.

## Age Coverage Gain

DynastyProcess has useful age and birthdate fields in `db_playerids.csv`, and player-value rows carry `age`. For the full 240-player dynasty board, the DP match set can add ages for roughly 230 rows that did not already have NWR age populated. For the frozen/candidate 66, DP adds age coverage for 9 additional matched rows. Missing ages remain missing; no ages are fabricated.

Known top-player caveat:

- Jeremiyah Love has a DP market row and NWR join, but the DP age field is blank in the current snapshot. Keep his age as "Not enough information" unless another verified source is approved.

## Pick-Value Usefulness

DynastyProcess pick values provide a display-only sanity layer for future-pick language:

| Pick | DP value 1QB | DP ECR 1QB | Scrape date |
| --- | ---: | ---: | --- |
| 2026 1.04 | 3920 | 41.925 | 2026-06-19 |
| 2026 2.03 | 466 | 132.58 | 2026-06-19 |
| 2028 1st | 1490 | 83.094482 | 2026-06-19 |

These values are useful for Trading Lab sanity checks and review notes, but they are not source truth and are not model inputs.

## NWR Vs Market Examples

| Asset | NWR review rank basis | DP ECR 1QB | DP value 1QB | Flag |
| --- | ---: | ---: | ---: | --- |
| Jeremiyah Love | 1 | 15.1 | 7363 | aligned |
| Zay Flowers | 2 | 41.0 | 4006 | NWR much higher than market |
| Chris Olave | 3 | 23.3 | 6073 | NWR much higher than market |
| Jameson Williams | 6 | 53.3 | 3001 | NWR much higher than market |
| Drake Maye | 20 | 25.1 | 5821 | aligned |
| Brian Thomas Jr. | 29 | 60.8 | 2516 | NWR much higher than market |
| Jaylen Warren | 25 | 118.7 | 645 | NWR much higher than market |
| Rashee Rice | 26 | 40.4 | 4063 | aligned |
| Brock Purdy | 65 | 66.1 | 2221 | aligned |
| Dak Prescott | 53 | 85.0 | 1425 | NWR much higher than market |
| Tyreek Hill | no candidate/frozen basis | 128.1 | 517 | aligned/no NWR basis |
| Dallas Goedert | no candidate/frozen basis | 141.1 | 381 | aligned/no NWR basis |

The largest disagreements should be treated as review prompts, not automatic overrides. They may reflect league format, NWR board strategy, player-specific risk posture, or stale/incomplete NWR context.

## Safe Use Policy

Allowed now:

- Display-only market baseline in review docs.
- Player ID crosswalk audit.
- Age and birthdate source audit, with missing values preserved.
- Pick-value sanity context for human review.
- NWR-vs-market disagreement flags.

Not allowed without Master approval:

- Ranking formula inputs.
- Candidate rank overrides.
- Hidden sort fields.
- Private value, recommendations, simulations, or final draft decisions.
- Source-truth replacement for NWR board/rank fields.

## Optional App Exposure Plan

Future app exposure should remain explicitly labeled display-only:

- Player Compare: market baseline block.
- Trading Lab: market sanity warning and pick-value reference.
- Post-Draft Mode: trade recap context.
- Dynasty Rankings: optional market sanity column.
- Live Draft: warning note only, never a rank driver.

## Future Work

- Add scheduled/on-demand refresh only after Master approves the operational path.
- Add manual review overrides for unmatched NWR players.
- Add a stricter player ID normalization table if NWR adopts a durable internal player ID registry.
- Evaluate whether a market baseline can be blended into model logic only after a separate approval, test plan, and policy update.
