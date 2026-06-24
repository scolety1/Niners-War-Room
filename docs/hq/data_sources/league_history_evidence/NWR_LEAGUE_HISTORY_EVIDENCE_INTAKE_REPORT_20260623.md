# NWR League History Evidence Intake Report - 2026-06-23

## Verdict

YELLOW-GREEN. The evidence layer is safe and reviewable, but the direct 2026 draft-log and trade-history input paths were placeholders and could not be imported.

## Imported Evidence

| Evidence source | Imported now? | Count | Notes |
| --- | ---: | ---: | --- |
| Actual 2026 draft log | No | 0 rows | `REPLACE_WITH_2026_DRAFT_LOG_PATH` did not exist. A normalized schema file was created for later import. |
| Actual trade-history export | No | 0 events / 0 assets | `REPLACE_WITH_TRADE_HISTORY_PATH` did not exist. Event and asset schema files were created for later import. |
| Gmail league-history metadata | Yes | 11 queue rows | Search metadata only. No raw bodies or raw exports were stored. |
| Historical evidence upgrade queue | Yes | 10 rows | Focused on actual/free-agent, accepted-trade, inferred drop-list, proxy drop-list, and rules upgrades. |

## Repo Evidence Found

Existing repo artifacts indicate several useful evidence families:

- Current context docs for Sleeper status and free-agent pool verification.
- Historical drop-list reconstruction files under `docs/hq/data_sources/historical_drop_lists/`.
- Draft-day export/frozen-board files under `docs/draft_day_exports/final_board_v1_20260622/`.
- Draft/runtime/app services and tests that can help validate future normalizers.
- Data accountability repair scripts and docs that already separate human-confirmed PDF free agents from verifier-only Sleeper rows.

## Gmail Search Summary

Metadata-only Gmail search found candidate league-history evidence for:

- 2026 roster/ranking PDFs and rules attachments.
- 2025 and 2026 accepted-trade candidates.
- A 2026 proposal candidate that must not be treated as accepted without follow-up evidence.
- 2026 roster declaration / cut-or-keeper context around Brian Thomas Jr.

No raw email body text was committed. The tracked queue stores only date, subject, short parsed league entities, source status, and notes.

## Trade Asset Parsing

No direct trade export was available. Therefore:

- `NWR_LEAGUE_TRADE_HISTORY_EVENTS_NORMALIZED.csv` is schema-only.
- `NWR_LEAGUE_TRADE_HISTORY_ASSETS_NORMALIZED.csv` is schema-only.
- Gmail trade candidates are queued as REVIEW_NEEDED/FOUND metadata, not normalized actual trade events.

Future normalization should split each accepted trade into one event row and multiple asset rows, preserving raw asset text only in `asset_text_raw`.

## Draft Log Normalization

No direct draft-log export was available. Therefore:

- `NWR_ACTUAL_2026_DRAFT_LOG_NORMALIZED.csv` is schema-only.
- No missing picks were inferred.
- No player IDs or pick ownership were fabricated.

## Privacy Boundary

Not ingested:

- Raw Gmail exports.
- Raw email bodies.
- Unrelated personal email content.
- Personal sender email addresses.
- Full attachment contents.

Allowed and tracked:

- Search query pack.
- Subject/date metadata.
- Short league-entity notes.
- Review-needed status.

## Model/Backtest Use

This layer can improve future model/backtest work by separating:

- actual draft decisions,
- actual trades,
- actual drop/keeper evidence,
- proxy/sensitivity-only historical rows,
- verifier-only current API context.

It is not yet a model input. Promotion into modeling should happen only after evidence rows are reviewed, normalized, ID-matched, and approved in a separate lane.

## Recommended Next Step

1. Provide the actual 2026 draft-log export path.
2. Provide the actual Sleeper trade-history export path or authorize a read-only Sleeper trade pull.
3. Review the queued Gmail candidates and attachments with explicit privacy controls.
4. Rerun normalization to populate actual draft and trade CSVs.
5. Use the upgrade queue to replace PROXY/INFERRED rows only where ACTUAL evidence exists.
