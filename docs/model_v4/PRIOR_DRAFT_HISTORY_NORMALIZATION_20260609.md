# Prior Draft History Normalization - 2026-06-09

## Package
- Source root: `local_exports\league_history\drafts\incoming\draft_prep_codex_package\draft_prep_codex_package`
- Normalized CSV: `local_exports/model_v4/draft_prep/latest/prior_league_draft_history_review_rows.csv`

## Row counts by source
| Source | Rows |
| --- | ---: |
| `2024 NFL Draft, Dad's Dynasty.xlsx` | 67 |
| `2025 NFL Draft, Dad's Dynasty.xlsx` | 145 |
| `Drafts.pdf` | 200 |

## 2025 workbook handling
- The left side is preserved as `mock_board`.
- The right side is preserved as `user_rank_board`.
- `Drafted at`, rank, player, NFL team, position, draft capital, age, notes, and visible fill context are preserved where present.
- Explicit 2025 user drafted list is ground truth: Kaleb Johnson, Jayden Higgins, Luther Burden III, Dylan Sampson, Trevor Etienne.
- Green fill is retained only as `highlight_color_context`; it is not used as drafted ground truth.
- Yellow fill is interpreted as `user_must_draft_at_cost_flag=true`, meaning high-interest at cost, not draft at any cost.
- Yellow/highlight rows found: 7.

## PDF handling
- The image-only league-manager PDF is represented through `drafts_pdf_official_transcription_best_effort.csv`.
- Low-confidence PDF rows found: 23.
- Low-confidence rows carry `data_needed=Verify against included page image before relying on this row.`
- No unreadable picks were invented.

## Guardrails
- Prior draft history, spreadsheet highlights, and user notes are display-only/context-only.
- They are blocked from NWR private value, NWR Draft Value, pick baselines, VORP, replacement, and final draft recommendations.
