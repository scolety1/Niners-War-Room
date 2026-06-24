# NWR League History Evidence Intake Method - 2026-06-23

## Purpose

This layer captures reviewable league-history evidence for future model accountability and backtesting. It does not feed rankings, candidate values, draft logic, or model features in this task.

## Source Classes

| Source class | Meaning | Current use |
| --- | --- | --- |
| ACTUAL_DRAFT_LOG | Direct actual draft-log export from the league platform or user-provided final draft log | Not yet imported; source path placeholder missing |
| ACTUAL_TRADE_HISTORY | Direct trade-history export from Sleeper or league records | Not yet imported; source path placeholder missing |
| EMAIL_METADATA_FOUND | Gmail search metadata indicates a likely league-history evidence message | Review queue only |
| PDF_CONFIRMED_DRAFTABLE_POOL | User-provided league PDF page/list already used as human-confirmed draftable pool | Evidence/reference layer only |
| CURRENT_API_VERIFIER | Sleeper/current API context used for verification or ID/status crosswalks | Verification only |
| INFERRED_OR_MIXED | Existing historical reconstruction with some actual/inferred basis | Upgrade queue only |
| PROXY | Proxy historical evidence created for sensitivity analysis | Not model truth |
| SOURCE_NEEDED | Expected source was not available | TODO |

## Normalization Rules

- Draft-log rows require season, round/pick fields, selecting team, player, source path, confidence, and notes.
- Trade events are split into event rows and asset rows.
- Unknown trade assets remain UNKNOWN or raw asset text with REVIEW_NEEDED notes. They are not forced into fake structured values.
- Missing player IDs are allowed but must be flagged in confidence/notes.
- Evidence rows can support future reviews, but promotion into model inputs requires a separate approval lane.

## Gmail Privacy Rules

- Gmail search was limited to league-history terms.
- No raw email bodies were committed.
- No raw Gmail exports were committed.
- No unrelated personal content was committed.
- Repo-tracked Gmail evidence is limited to message date, subject, source status, short parsed league entities, and review notes.

## What This Does Not Do

- Does not change app code.
- Does not mutate frozen board, Dynasty Rank, latest_candidate, latest_approved, or pinned snapshot.
- Does not use trade/draft/Gmail evidence as model input.
- Does not promote DynastyProcess, ADP, or market data into model truth.

## Recommended Next Step

Provide concrete actual draft-log and trade-history exports, then run a follow-up normalizer that fills the currently header-only ACTUAL_DRAFT_LOG and ACTUAL_TRADE_HISTORY CSVs. For Gmail candidates, review message bodies/attachments in a privacy-safe session and normalize only league-relevant rows.
