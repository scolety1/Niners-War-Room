# Build Sprint 5G - Cutoff Policy Repair

## Scope

Sprint 5G repaired or formally governed row-family cutoff policy for `offseason_carryover` and `rookie_post_draft`. It did not rebuild snapshots, train calibrated models, create app percentages, create player-facing probabilities, create rankings, push, or deploy.

## Readiness Verdict

`READY_AFTER_MANUAL_CUTOFF_APPROVAL`

Sprint 5H can start only after HQ approves the rookie post-draft cutoff policy. `offseason_carryover` remains blocked until an earlier source snapshot or source availability manifest exists.

## Offseason Carryover Cutoff Finding

- Row family: `offseason_carryover`
- Current cutoff: `YYYY-02-15`
- Observed source date: `2026-05-15`
- Reason: `blocked_by_source_after_cutoff`
- Decision: `cutoff_policy_should_remain`
- Repair path: `needs_earlier_source_snapshot`, `needs_source_availability_manifest`, `blocked_until_next_data_refresh`

The `YYYY-02-15` cutoff carries a distinct business meaning: early offseason carryover after prior-season labels but before later offseason/draft/current-state refreshes. Moving the cutoff later simply to admit a May source file would change that meaning and is not approved in this sprint.

## Rookie Post-Draft Cutoff Finding

- Row family: `rookie_post_draft`
- Current cutoff: `YYYY-05-01`
- Observed draft manifest timestamp: `2026-05-25T23:45:00+00:00`
- Reason: `blocked_by_manifest_after_cutoff`
- Source status: `user_download_factual_draft_result_local_only`
- Allowed use from manifest: `prospect_prior_draft_capital_after_identity_validation`

The fixed `YYYY-05-01` policy fails for the current 2026 manifest. The safer policy is a season-specific post-draft cutoff approved by HQ and anchored to factual draft-result availability, such as the draft manifest source timestamp. This is source-safe because it uses factual draft results only, not ADP, ranks, projections, consensus, trade calculators, or market data.

## Draft Cutoff Policy Options

| Option | Recommendation | Reason |
| --- | --- | --- |
| Fixed `YYYY-05-01` | reject as default | Fails the current 2026 manifest and may precede actual draft-result availability. |
| First Monday after NFL Draft | defer | Requires a registered local draft-calendar source, which is not present in this sprint. |
| Draft manifest source timestamp | approve after HQ review | Directly proves factual draft capital was available. |
| Manually approved cutoff per season | recommended | Preserves auditability across variable draft calendars and source receipt timing. |
| Market/rank-based availability | blocked | Violates NWR source firewall. |

## Proposed Cutoff Registry

| Row family | Current status | Proposed policy |
| --- | --- | --- |
| `all_player_pre_week1` | `eligible_now` | Fixed `YYYY-09-01` before Week 1; source timestamps must be on/before cutoff. |
| `offseason_carryover` | `eligible_after_earlier_snapshot` | Keep fixed `YYYY-02-15`; require earlier source snapshot/availability manifest. |
| `rookie_post_draft` | `eligible_after_manifest_approval` | Use manually approved season-specific post-draft cutoff on/after factual draft manifest availability. |

## Snapshot Rebuild Eligibility

- `all_player_pre_week1`: `eligible_now`
- `offseason_carryover`: `eligible_after_earlier_snapshot`
- `rookie_post_draft`: `eligible_after_manifest_approval`

No snapshot rebuild was run in Sprint 5G.

## Local Exports

Local-only outputs were written to:

`C:\Dev\niners-war-room\local_exports\outcome_probability\sprint_5g_cutoff_policy_repair`

- `cutoff_policy_registry_proposal.csv`
- `offseason_carryover_cutoff_audit.csv`
- `rookie_post_draft_cutoff_audit.csv`
- `draft_manifest_policy_options.csv`
- `snapshot_rebuild_eligibility.csv`
- `README_SPRINT_5G.md`

## Remaining Blockers Before True Calibrated Modeling

- broader legal historical rows and more seasons
- approved cutoff policy for rookie post-draft snapshots
- earlier source snapshots for offseason carryover, or a formally revised business definition
- optional source timestamp registration if richer feature sets are desired
- out-of-time validation plan
- confidence gates
- app display gates
- final leakage audit
