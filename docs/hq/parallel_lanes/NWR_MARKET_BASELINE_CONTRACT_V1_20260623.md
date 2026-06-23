# NWR Market Baseline Contract V1 - 2026-06-23

## Verdict

GREEN contract for a modular, display-only market baseline lane. DynastyProcess may be used
as market context, crosswalk support, and sanity-review material. It is not a model input,
rank source, candidate rank driver, source-truth replacement, or hidden sort layer.

## Current Inventory

Already exists:

- `src/connectors/dynastyprocess_connector.py` fetches explicit DynastyProcess files,
  validates required upstream schemas, records row counts, SHA-256 values, ETags,
  scrape dates, and upstream commit metadata.
- `scripts/build_dynastyprocess_market_baseline_v1.py` writes repo-safe derived CSVs
  under `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/`.
- `scripts/refresh_dynastyprocess_market_baseline_v1.py` adds stale-cache fallback.
- `scripts/run_dynastyprocess_refresh_task.ps1` wraps the refresh and writes logs outside
  the repo under `C:\NWR_SHARED_DATA`.
- `scripts/register_dynastyprocess_refresh_task.ps1` and
  `scripts/unregister_dynastyprocess_refresh_task.ps1` manage the local task named
  `NWR DynastyProcess Market Baseline Refresh`.
- Existing docs describe the connector, upstream schedule, local schedule, and current
  derived artifact outputs.

Missing before this contract:

- A stable app-facing contract that says exactly what market baseline can and cannot do.
- A page/lane integration map decoupled from the current Streamlit layout.
- A service/API surface so future pages do not reimplement joins.
- A page usage registry that makes display fields opt-in and explicitly non-ranking.
- Stable schema definitions for future artifact names.

## Allowed Uses

DynastyProcess may be used as:

- Display-only market baseline.
- Market sanity flag for human review.
- Age, external ID, and pick-value crosswalk source.
- Trade sanity context for package review and recap.

Allowed display labels must keep the market lane visibly separate from NWR truth:

- `Market Baseline / Display-Only`
- `NWR higher than market`
- `NWR lower than market`
- `Aligned with market`
- `No market match`
- `Market data stale`

## Banned Uses Without Future Approval

DynastyProcess must not be used as:

- Final rank source.
- Candidate rank source.
- Private model score input.
- Hidden sort driver.
- Source truth replacement.
- Dynasty Rank overwrite.
- `final_board_rank` overwrite.
- Any update to `latest_candidate`, `latest_approved`, or pinned snapshots.

Any future promotion requires a separate approval, tests, acceptance doc, and explicit
guardrail update.

## Freshness Contract

Required statuses:

| Status | Meaning | Required behavior |
| --- | --- | --- |
| `GREEN_CURRENT` | Current weekly scrape and usable cache. | Display-only context may appear normally. |
| `GREEN_SAME_WEEK_NO_CHANGE` | Current week, no upstream value change. | Display-only context may appear with no-change note. |
| `YELLOW_STALE` | Older than expected weekly window. | Show `Market data stale`; do not use for sort or advice. |
| `RED_STALE` | Older than 14 days. | Hide detailed values by default or show only with strong stale warning. |
| `YELLOW_FETCH_FAILED_USING_LAST_CACHE` | Fetch failed, last cache usable. | Show stale/fallback warning. |
| `RED_NO_VALID_CACHE` | No valid cache. | Show unavailable state; do not show market values. |

Every app-facing artifact must carry `freshness_status`. Yellow or red status must produce
visible stale display language.

## Join Confidence Contract

Allowed join confidence path:

| Join path | Confidence | Display rule |
| --- | --- | --- |
| Exact ID match | High | Safe for normal display-only market context. |
| Exact name + position | Medium | Safe for display-only context. |
| Normalized name + position | Review | Display with manual-review caution where space allows. |
| Unmatched | Manual review | Show `No market match`; do not fabricate values. |

Market joins must preserve the caller's existing row order unless a page makes a future,
explicit, visible UI sort from non-market fields.

## Fallback Behavior

If player market context is missing, stale, or unmatched:

- Preserve all NWR rank/model/source fields exactly as received.
- Add `No market match`, `Market data stale`, or unavailable labels.
- Do not backfill candidate rank, final board rank, Dynasty Rank, model score, or source truth.
- Do not create hidden sort fields.

If pick market context is missing:

- Return no market value for the pick.
- Keep Trading Lab and recap logic on existing NWR values.
- Show display-only market unavailable copy where the page owner chooses to expose it.

## Attribution And License

Every public-facing or durable artifact that exposes DynastyProcess data must identify:

- Source: DynastyProcess public data.
- Repository: `https://github.com/dynastyprocess/data`.
- License: GPL-3.0 as published by the upstream data repository.
- NWR use: display-only market baseline, not NWR source truth.

Raw upstream dumps, cache files, and logs remain outside the repo under `C:\NWR_SHARED_DATA`
and must not be committed.

## Page And Lane Boundaries

The connector owns fetching, schema validation, cache metadata, and freshness metadata.

The builder owns repo-safe derived CSVs and crosswalk/audit artifacts.

`src/services/market_baseline_service.py` owns page-facing reads, joins, labels, and safe
fallback behavior.

`src/services/market_baseline_registry.py` owns page opt-in rules. For now, every page entry
has `model_input_allowed=False` and `sort_allowed=False`.

App pages own presentation only. They must not promote market baseline fields into rank,
model, source-truth, or hidden sort behavior.
