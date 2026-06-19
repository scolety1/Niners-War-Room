# Mock Draft Real Input Candidate Validation Report

Date: 2026-06-19

Lane: `C:\NWR\Niners-War-Room-mock-draft`

Branch verified before validation: `work/mock-draft-simulator`

HEAD verified before validation: `df0991ad67278f447ed0bc2d4becafadcbb5936a`

## Scope

This report validates Master-identified candidate input sources by path, header,
row count, ownership, and current Mock Draft contract compatibility. It does not
promote any archive file into draft-use input.

No simulations were run.

No real data was copied into the Mock Draft lane.

No real input manifest was created.

ADP and market data remain behavior-only context for opponent behavior,
availability, and likely pick timing. They must never become NWR private value,
private ranking, default sort, probability, band, or promoted artifact.

## Current Contract Expectations

The lane-local contracts currently expect these real-input shapes before draft
use can move out of HOLD:

| Input | Required or key columns |
| --- | --- |
| Frozen rookie input | `asset_id`, `player`, `position`, `asset_type`, `nwr_private_value`, `source_status` |
| Dropped or available veteran pool | `asset_id`, `player`, `position`, `nfl_team`, `availability_source`, `review_status` |
| Final pick order | `overall_pick`, `round`, `round_pick`, `pick_label`, `current_owner`, `original_owner` |
| NWR/my picks | `overall_pick`, `pick_label`, `owner`, `is_nwr_pick` |
| Rosters/keepers | `team_id`, `team_name`, `player`, `position`, `keeper_status` |
| Team needs/opponent tendencies | `team_id`, `team_name`, `position`, `need_weight`, `tendency_note` |
| NWR private values | `asset_id`, `player`, `position`, `nwr_private_value`, `value_source`, `separation_note` |
| ADP/market behavior | `asset_id`, `player`, `position`, `market_adp_pick`, `market_source`, `opponent_likelihood_signal`, `allowed_use`, `separation_note` |

## Candidate Validation

| Category | Candidate file path | Owner lane | Exists | Header summary | Row count including header | Schema compatibility | Current/final confidence | Verdict | Safe for future read-only manifest | Owner confirmation needed |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| Frozen rookie mock draft input | `C:\NWR_LOCAL_ARCHIVE\laptop_retirement_20260618\local_exports_archive\other_review_only\rookie_hq\local_exports\rookie_framework\final_post_fill_runway_20260616\rookie_2026_mock_draft_input_20260616.csv` | Rookie HQ | Yes | `rookie_rank`, `player`, `position`, `nfl_team`, `age`, `nfl_draft_capital`, `adp_market_rank`, `depth_chart_role`, `tier_label`, `draft_action`, `warning_severity`, `upside_band`, `bust_risk_band`, `manual_question`, `rookie_source_status`, `formula_name`, `board_order_frozen` | 55 | Partial. Identity columns exist, but current Mock Draft real contract expects `asset_id`, `asset_type`, `nwr_private_value`, and `source_status` aliases or normalized fields. | Archived candidate only. It appears frozen, but it is local archive material, not an active lane export. | YELLOW | Yes, after owner confirmation and alias mapping review. | Rookie HQ must confirm this is the final frozen rookie source or re-export a current normalized file. |
| Pick order, normalized review | `C:\NWR_LOCAL_ARCHIVE\laptop_retirement_20260618\local_exports_archive\other_review_only\mock_draft\local_exports\mock_draft_simulator\input_snapshots\lve_rosters_061326\draft_pick_rows_normalized_review.csv` | Mock Draft source intake from league roster/pick packet | Yes | `source_pdf`, `source_page`, `source_row`, `current_owner`, `manager`, `pick_label`, `season`, `round_text`, `asset_type`, `original_owner`, `is_niners_pick`, `input_status` | 152 | Partial. Owner/pick fields exist, but the current contract expects numeric `overall_pick`, `round`, and `round_pick`. | Archived review output. Final/current league source is unclear. | YELLOW | Yes, read-only only. | Mock Draft source intake owner must confirm source packet currency and normalization lineage. |
| Pick order and my picks, simulator-ready derived | `C:\NWR_LOCAL_ARCHIVE\laptop_retirement_20260618\local_exports_archive\other_review_only\mock_draft\local_exports\mock_draft\combined_simulator_state_20260616\simulator_ready_2026_pick_rows.csv` | Mock Draft source intake from league roster/pick packet | Yes | `overall_pick`, `round`, `round_pick`, `pick_label`, `current_owner`, `original_owner`, `is_my_pick`, `source_status`, `source_season` | 52 | Stronger for pick order. My-picks field is `is_my_pick`, while current contract expects `is_nwr_pick` and separate owner field for the my-picks source. | Archived derived output. Final/current source is unclear. | YELLOW | Yes, read-only only. | Mock Draft source intake owner must confirm this derived file was generated from the final league packet and define `is_my_pick` to `is_nwr_pick` mapping. |
| Pick order and my picks, regeneration smoke derived | `C:\NWR_LOCAL_ARCHIVE\laptop_retirement_20260618\local_exports_archive\other_review_only\mock_draft\local_exports\mock_draft\regeneration_smoke_20260617\combined_simulator_state\simulator_ready_2026_pick_rows.csv` | Mock Draft source intake from league roster/pick packet | Yes | `overall_pick`, `round`, `round_pick`, `pick_label`, `current_owner`, `manager`, `original_owner`, `is_my_pick`, `source_status`, `source_season` | 52 | Stronger for pick order than the normalized review file. My-picks alias still needs explicit mapping. | Archived smoke/regeneration output. It is not final draft-use input. | YELLOW | Yes, read-only only. | Mock Draft source intake owner must confirm this is only a derivation check or identify the canonical current export. |
| Roster/keeper candidate | `C:\NWR_LOCAL_ARCHIVE\laptop_retirement_20260618\local_exports_archive\other_review_only\mock_draft\local_exports\mock_draft_simulator\input_snapshots\lve_rosters_061326\roster_rows_normalized_review.csv` | Drop Decision / roster declaration owner | Yes | `source_pdf`, `source_page`, `source_row`, `team_name`, `manager`, `roster_slot`, `player_name`, `position`, `nfl_team`, `overall_rank`, `input_status` | 295 | Partial. Team/player fields exist, but current contract expects normalized `team_id`, `player`, and `keeper_status`. | Archived review output. Final post-declaration roster/keeper source is unclear. | YELLOW | Yes, read-only only. | Drop Decision or roster declaration owner must confirm final roster/keeper state and required field mapping. |
| Dropped/available veteran pool final source | No final canonical source found. Template at `C:\NWR\Niners-War-Room-mock-draft\docs\model_v4\mock_draft_input_templates_20260617\dropped_veterans_template.csv` | Drop Decision / roster declaration owner | Final source missing; template exists | Template header: `player`, `position`, `source_label`, `review_flags`, `nfl_team`, `previous_team`, `previous_manager`, `drop_sequence`, `input_status` | 2 | Template is guidance only and does not satisfy final real source. Current contract expects `asset_id`, `availability_source`, and `review_status` for the veteran pool. | Missing final source. | RED | Template may be referenced in a future manifest; no final data can be referenced yet. | Drop Decision / roster declaration owner must create or approve final dropped/available veteran source. |
| Team needs/opponent tendencies | No current canonical source found. Template or fixture-style material only. | Mock Draft / league behavior owner | Missing | No current real header validated. | 0 | Missing. Current contract expects `team_id`, `team_name`, `position`, `need_weight`, and `tendency_note`, and forbids private value columns. | Missing current source. | YELLOW | Not until a real behavior-only source exists. | Owner must supply current opponent tendency inputs or approve manual read-only notes converted to contract shape. |
| NWR private value/ranking source | Rookie private value is present conceptually inside the frozen rookie candidate; veteran private value source is missing/unclear. Template at `C:\NWR\Niners-War-Room-mock-draft\docs\model_v4\mock_draft_input_templates_20260617\nwr_veteran_value_guidance_template.csv` | Rookie HQ for rookies; Drop Decision / Master value owner for veterans | Partial | Veteran template header: `asset_id`, `player`, `position`, `source_label`, `nwr_value_status`, `nwr_guidance_label`, `nwr_warning`, `draft_action`, `source_status`, `approved_numeric_nwr_value` | 2 | Partial. Rookie candidate needs aliasing to Mock Draft `nwr_private_value`; veteran final source is not present. | Partial for rookies, missing/unclear for veterans. | YELLOW/RED | Rookie candidate only after owner confirmation; veteran source not yet. | Rookie HQ must confirm rookie private value export. Veteran value owner must define final private value source and keep market columns out. |
| ADP/market behavior source | No real feed found. Template at `C:\NWR\Niners-War-Room-mock-draft\docs\model_v4\mock_draft_input_templates_20260617\behavior_only_adp_market_template.csv` | Mock Draft / opponent behavior owner | Real source missing; template exists | Template header: `asset_id`, `player`, `position`, `source_name`, `source_type`, `source_timestamp`, `market_adp`, `overall_adp`, `expected_pick`, `sample_size`, `identity_match_method`, `review_flags` | 2 | Template needs mapping to `market_adp_pick`, `market_source`, `opponent_likelihood_signal`, `allowed_use`, and `separation_note`. Must not contain NWR private value columns. | Missing real behavior-only feed. | YELLOW | Template may be referenced later; real feed cannot be referenced yet. | Mock Draft owner must supply or approve a behavior-only market source and confirm no private value leakage. |

## Preflight Interpretation

Archived preflight rows from the laptop handoff reported the following staged
inputs as missing or invalid for full readiness:

| Gate | Status | Meaning |
| --- | --- | --- |
| `staging:post_drop_rosters.csv` | YELLOW | Required staged input missing or invalid. |
| `staging:post_drop_draft_order.csv` | YELLOW | Required staged input missing or invalid. |
| `staging:team_managers.csv` | YELLOW | Required staged input missing or invalid. |
| `staging:dropped_veterans.csv` | YELLOW | Optional or review-required staged input missing. |
| `staging:behavior_only_adp_market.csv` | YELLOW | Optional or review-required staged input missing. |
| `staging:nwr_veteran_value_guidance.csv` | YELLOW | Optional or review-required staged input missing. |

That preflight state matches this validation: infrastructure is ready to inspect
inputs, but the lane must remain HOLD for real draft use until owning lanes
confirm current final sources.

## Missing or Unclear Inputs

- Final dropped/available veteran pool is missing.
- Final post-declaration rosters/keepers are unclear.
- Final pick order and NWR pick numbers are archived/derived candidates only.
- Current team needs/opponent tendency source is missing.
- Veteran NWR private value source is missing or unclear.
- Real ADP/market behavior source is missing and must remain separate from NWR
  private value.

## Future Read-Only Manifest Eligibility

Safe for future read-only manifest after owner confirmation:

- Frozen rookie mock draft input candidate.
- Archived pick order candidates.
- Archived roster/keeper candidate.

Not safe for final manifest yet:

- Dropped/available veteran pool.
- Team needs/opponent tendencies.
- Veteran NWR private value source.
- Real ADP/market behavior source.

## Final Validation Verdict

Overall verdict: YELLOW.

Reason: candidate files were found for rookie, picks, and roster/keeper intake,
but they are archive/local-only candidates with final/current ownership still
unclear. Several required real draft-use inputs remain missing. Mock Draft may
perform future read-only validation against owner-approved paths, but it must not
run simulations or treat these archived candidates as final draft-use inputs.
