# Trading Lab NWR Integration Contract Map - 2026-06-18

This map defines future integration seams. It does not approve wiring, data ingestion, generated outputs, or cross-lane edits.

| Source category | Future source lane | Expected fields | Current status | Allowed future integration type | Blocked behavior | Validation needed before wiring |
|---|---|---|---|---|---|---|
| NWR private value | Future approved NWR value source | `asset_id`, `display_name`, `nwr_value`, `position`, `keeper_status`, `notes` | Fixture-only | Read-only adapter | Mutating NWR values, replacing public value, generated outputs | Contract tests, provenance labels, missing-value fallback |
| Public fantasy market value | Future approved public fantasy source | `asset_id`, `display_name`, `public_market_value`, `source_name`, `last_updated_label` | Fixture-only | Read-only adapter | API calls without approval, scraping without approval, overwriting NWR value | Source policy review, staleness labels, no-secret tests |
| Roster context | Future approved roster context | `team_name`, `position_depth`, `bench_pressure`, `starter_slots`, `notes` | Fixture-only | Read-only adapter | File writes, generated roster exports, automatic moves | Missing-context tests, manual review copy |
| Keeper context | Future approved keeper context | `asset_id`, `keeper_status`, `keeper_cost`, `keeper_tier`, `notes` | Fixture-only | Read-only adapter | Automatic keeper decisions | Explainability tests, manual review labels |
| Drop pressure | Future approved drop-pressure context | `asset_id`, `drop_pressure_tag`, `cut_risk`, `roster_slot_note` | Fixture-only | Read-only adapter | Automatic drop actions | Fallback tests, warning tests |
| Rookie pick context | Future approved Rookie lane output | `pick_id`, `round`, `rookie_pick_context`, `draft_tier`, `notes` | Fixture-only | Read-only adapter | Editing Rookie lane, importing generated artifacts | Contract tests, provenance tests |
| Mock draft context | Future approved Mock Draft output | `pick_id`, `mock_range`, `target_tier`, `draft_plan_note` | Fixture-only | Read-only adapter | Editing Mock Draft lane, generated outputs | Not-wired labels, review-gate tests |
| Opponent team context | Future approved manual/opponent context | `team_name`, `roster_needs`, `surplus_tags`, `trade_style`, `notes` | Fixture-only | Manual or read-only adapter | Private league scraping without approval, automatic offer targeting | Privacy review, fixture fallback tests |

## Required Approval Language

Any future integration prompt must name the source, allowed files, read/write behavior, validation commands, and rollback expectations.

## Current Verdict

GREEN for seam documentation. HOLD for every real integration.
