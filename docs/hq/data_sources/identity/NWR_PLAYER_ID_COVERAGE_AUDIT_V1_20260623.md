# NWR Player ID Coverage Audit V1 - 20260623

## Verdict
YELLOW-GREEN

The audit now covers frozen board, PDF free agents, Outcome support rows, DynastyProcess crosswalk rows, and current candidate/live draft overlays. High-confidence matches require existing ID evidence or exact name+position support from admitted crosswalks. No silent fuzzy join is trusted.

## Counts
- Identity rows audited: 1139
- Confidence counts: `{'HIGH': 1065, 'MEDIUM': 52, 'LOW': 22}`
- Manual review rows: 74
- Surface counts: `{'frozen_final_board_v1': 66, 'lve_pdf_page3_free_agents': 77, 'outcome_numeric_display_support': 66, 'dynastyprocess_market_baseline_crosswalk': 330, 'tuned_v2_candidate_overlay': 66, 'emergency_cross_asset_candidate_overlay': 294, 'full_dynasty_board_model_v4': 240}`

## Manual Review Sample
| source_surface | player_name | position | match_method | reason |
| --- | --- | --- | --- | --- |
| frozen_final_board_v1 | Lewis Bond | WR | exact_name_position_sleeper | sleeper_match |
| frozen_final_board_v1 | Kentrel Bullock | RB | exact_name_position_sleeper | sleeper_match |
| frozen_final_board_v1 | Kejon Owens | RB | exact_name_position_sleeper | sleeper_match |
| frozen_final_board_v1 | Sieh Bangura | RB | unresolved | No stable ID or exact name+position match; keep visible but require manual review. |
| frozen_final_board_v1 | Jacob De Jesus | WR | exact_name_position_sleeper | sleeper_match |
| frozen_final_board_v1 | Dominic Richardson | RB | exact_name_position_sleeper | sleeper_match |
| frozen_final_board_v1 | Devin Voisin | WR | unresolved | No stable ID or exact name+position match; keep visible but require manual review. |
| frozen_final_board_v1 | Hank Beatty | WR | exact_name_position_sleeper | sleeper_match |

## Guardrail
Unresolved players remain visible in reports/app contexts, but must carry manual review / `Not enough information` instead of fabricated evidence.
