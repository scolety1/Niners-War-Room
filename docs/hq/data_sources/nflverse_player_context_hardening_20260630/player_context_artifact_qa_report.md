# NFLVerse Player Context Artifact QA Report

Artifact rows: `294`
Safe display rows: `240`
Identity review rows: `54`
Duplicate non-missing `nwr_player_id` values: `0`
Missing `nwr_player_id` values: `54`
Safe rows with missing core nflverse identity fields: `0`
Safe rows with suspicious team mismatch after alias normalization: `31`
Contract context anomalies: `0`
Safe rows missing draft capital context: `165`
Forbidden flag true count: `0`
Missing-as-zero/healthy/no-role/UDFA wording hits: `0`

## Freshness

Injury context season counts: `{'2025': 203, '2024': 21, 'Not enough information': 16}`
Depth context source freshness: `depth_charts remains review-only/status-only; source coverage is 2024 in the underlying refresh-health record`
Snap recency season counts: `{'2025': 217, '2024': 6, 'Not enough information': 17}`
Schedule safe rows after hardening overlay: `240`

## Decision

No identity proposals were approved. The artifact was rebuilt only to add approved current/future team-level schedule display context to rows that were already `SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.