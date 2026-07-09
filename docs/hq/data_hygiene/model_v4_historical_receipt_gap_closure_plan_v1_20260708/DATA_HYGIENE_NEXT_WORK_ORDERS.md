# Data Hygiene Next Work Orders

## 1. Model v4 Historical Receipt Locator and Ledger V1

Purpose: Locate existing season-by-season Model v4 receipt candidates and create a canonical availability ledger.

Why Data Hygiene owns it: This is source trace, receipt chain, hash, schema, coverage, and reproducibility work.

Expected output packet:

`docs/hq/data_hygiene/model_v4_historical_receipt_locator_ledger_v1_YYYYMMDD/`

Master HQ handoff condition: Any recovered receipt is proposed for canonical admission or regeneration is requested.

Blocked actions: no formula execution, no source promotion, no local_exports writes, no app/ranking behavior changes.

## 2. Checkpoint Review Score Receipt Recovery V1

Purpose: Prove whether historical `checkpoint_review_score` rows exist.

Search first:

- recovered current-value folders
- timestamped data packs
- old local artifacts and handoff manifests
- prior Model v4 worktrees

Expected output: file availability, schema, SHA256, row/season coverage, identity safety, and leakage status.

## 3. Position-Specific Component Receipt Recovery V1

Purpose: Locate historical component rows and transform receipts for QB/RB/WR/TE.

Expected output: component receipt matrix by feature season and position.

## 4. Lifecycle / Age / Confidence Receipt Recovery V1

Purpose: Resolve historical lifecycle and confidence receipt gaps.

Expected output: age/lifecycle/confidence source trace, with as-of safety review.

## 5. WR/QB V2 Overlay Receipt Human Review Packet

Purpose: Determine whether current overlay logic can be replayed historically or must remain a current-board-only candidate overlay.

Expected output: overlay decision map and human review checklist.

## 6. Formula Gauntlet Component Signal Execution Contract

Purpose: If Master HQ chooses to proceed, create a contract for component signal tests only.

Owner: Master HQ / Formula Gauntlet, with Data Hygiene evidence support.

Blocked until: Master HQ explicitly approves execution scope.

## 7. Route Recovery Dependency

Purpose: Admit or block route/YPRR/TPRR denominator sources.

Owner: Route Recovery lane.

Data Hygiene role: source admission and receipt-chain review after source evidence exists.
