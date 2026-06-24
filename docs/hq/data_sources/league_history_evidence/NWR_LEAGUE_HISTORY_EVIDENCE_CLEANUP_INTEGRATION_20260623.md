# League History Evidence Cleanup Integration - 2026-06-23

## Starting Point

- Master branch: `work/hq-parallel-control`
- Starting HEAD: `8db66aa3c1e621900a90e20e7b644b371d6e3fb0`
- Live Draft V2 Persistence + Trade Events: already integrated at starting HEAD.

## Integration Source

No reachable cleanup-lane commit, worktree, patch, or zip was found by filename search under `C:\NWR`, Downloads, or Codex attachments. The integration was reconstructed from the provided lane summary and applied as docs/CSV-only evidence cleanup.

## Files Added

- `actual_2026_draft_log_INPUT_TEMPLATE.csv`
- `sleeper_trade_history_INPUT_TEMPLATE.csv`
- `league_history_hard_input_request.md`
- `league_history_current_yellow_status.md`
- `league_history_owner_team_mapping.csv`
- `league_history_confirmed_events_summary.md`
- `league_history_evidence_method.md`
- `league_history_missing_items_backlog.csv`

## Files Updated

- `NWR_PRE_SLEEPER_GMAIL_EVIDENCE_QUEUE_20260623.csv`
- `NWR_HISTORICAL_EVIDENCE_UPGRADE_QUEUE_20260623.csv`

## Brian Thomas Jr. Handling

Brian Thomas Jr. was tightened from an implied cut/drop review posture to:

- evidence type: `UNKNOWN`
- confidence/relevance: `LOW`
- `model_use_allowed=no`
- `training_allowed=no`
- `sensitivity_only=yes`

Reason: the phrase about dropping Brian Thomas Jr. from a top 5 does not prove actual roster drop, unprotected status, free-agent availability, draft/acquisition, or final cut.

## Boundaries Preserved

- Gmail evidence remains metadata-only and review-only unless confirmed by hard input.
- Free-agent snapshots are not treated as drop proof.
- Unprotected is not treated as dropped.
- No 2026 draft rows were invented.
- No Sleeper trade rows were invented.
- Nothing was marked training-allowed.
- No app code, model code, rank data, frozen board, latest files, or pinned snapshot was changed.

## Validation Run

- CSV load validation: PASS.
- Required-column validation: PASS.
- Brian Thomas Jr. queue-state validation (`UNKNOWN / LOW`): PASS.
- Backlog model/training flags (`model_use_allowed=no`, `training_allowed=no`, `sensitivity_only=yes`): PASS.
- Privacy scan for raw email bodies, raw Gmail exports, email addresses, and unrelated personal markers: PASS.
- `git diff --check`: PASS, with line-ending warnings only.
- App/model/source-truth diff check: PASS, docs/CSV evidence files only.
- Frozen board row count and pinned hash confirmation: PASS.
