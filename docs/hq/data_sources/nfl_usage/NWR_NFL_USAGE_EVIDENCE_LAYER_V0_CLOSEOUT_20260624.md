# NFL Usage Evidence Layer V0 Closeout

## Final Verdict

YELLOW safe. The research-only evidence infrastructure is complete, but live nflreadpy sampling is blocked because `nflreadpy` is not installed and no dependency install was approved.

## What Was Built

- Master plan and backlog
- Source contract, allowlist, blocklist, source inventory, and field inventory plan
- Environment/cache smoke report
- Core usage loader service and review artifacts
- Derived red-zone/first-down/touch service and review artifacts
- Advanced context inventory and route proxy policy
- Validation, quarantine, and schema fingerprint harness
- Review artifacts and final report
- Promotion gate, backtest plan, and candidate list
- Operator quickstart
- CFBD parking-lot doc as a separate future lane

## Source Families

player_stats, pbp, snap_counts, nextgen_stats, participation, ftn_charting, pfr_advstats, and roster/player ID crosswalks.

## Supported Fields

Factual V0 targets: snaps, offensive snap share, targets, carries, receptions, rushing yards, receiving yards, air yards, YAC when present, first downs, red-zone/inside-10/inside-5 event counts when derived from pbp, and public NGS fields as inventory candidates.

## Proxies

Route participation proxy, TPRR-like proxy, YPRR-like proxy, first-downs-per-touch proxy, red-zone share proxy, inside-10 share proxy, and inside-5 share proxy.

## Gaps

True routes run, true TPRR, true YPRR, and exact full route assignment data remain licensed-data gaps unless a later approved source contract proves otherwise.

## Blocked Status

RotoWire live scraping is blocked. Vendor ranks, projections, ADP, market/trade values, analyst blurbs, start/sit grades, betting odds, DFS salaries, proprietary scores, and raw external payloads are blocked.

## Validation And Quarantine

Validation/quarantine services cover required columns, blocked fields, schema fingerprinting, row collapse, duplicates, stale metadata, null spikes, license/attribution, permission flags, and unsupported route truth claims.

## Guardrails

- Raw data tracked: no
- App wiring: no
- Model input: no
- latest_candidate/latest_approved: untouched
- Frozen board/source-truth/rank files: untouched by this lane

## Known Caveats

Live row counts and exact fields are pending dependency approval. Advanced context inventories are policy-backed and doc-backed, not live sampled.

## Recommended Next Step

Approve and install `nflreadpy` through the normal dependency workflow, then run a tiny field-only smoke and regenerate schema fingerprints without committing raw payloads.
