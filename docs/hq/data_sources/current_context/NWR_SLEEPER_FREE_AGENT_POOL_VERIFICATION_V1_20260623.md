# NWR Sleeper Free-Agent Pool Verification V1 - 20260623

## Verdict
GREEN_RUNTIME_PULL

Sleeper is used here as a current league-state verifier and metadata layer. The LVE PDF page 3 free-agent list remains the human-confirmed 2026 draftable pool unless Tim/Master changes policy.

## Counts
- PDF page 3 rows: 77
- PDF include-default rows: 63
- PDF K/DST hidden/excluded by default: 14
- Sleeper/PDF audit rows: 3986
- Audit categories: `{'PDF_MATCHED_BUT_ROSTERED_CONFLICT': 9, 'PDF_MATCHED_SLEEPER_FA': 54, 'PDF_KDST_HIDDEN_DEFAULT': 14, 'SLEEPER_FA_NOT_IN_PDF': 3909}`

## Sample PDF Audit Rows
| player | pos | audit_category | sleeper_current_roster_state | status_warning |
| --- | --- | --- | --- | --- |
| Tyreek Hill | WR | PDF_MATCHED_BUT_ROSTERED_CONFLICT | rostered_conflict | injury/status review |
| Ryan Flournoy | WR | PDF_MATCHED_SLEEPER_FA | unrostered | clean |
| John Metchie | WR | PDF_MATCHED_SLEEPER_FA | unrostered | team/status mismatch |
| Dallas Goedert | TE | PDF_MATCHED_BUT_ROSTERED_CONFLICT | rostered_conflict | clean |
| Evan McPherson | K | PDF_KDST_HIDDEN_DEFAULT | unrostered | clean |
| Olamide Zaccheaus | WR | PDF_MATCHED_SLEEPER_FA | unrostered | clean |
| Juwan Johnson | TE | PDF_MATCHED_BUT_ROSTERED_CONFLICT | rostered_conflict | clean |
| Tyler Loop | K | PDF_KDST_HIDDEN_DEFAULT | unrostered | clean |

## Guardrails
- PDF ranks and Sleeper metadata are display/source context only.
- Sleeper unrostered rows that are not in the PDF are verifier/update candidates, not draftable source truth.
- K/DST are retained in audit where present but hidden by default.
- No rank, model, frozen board, latest, approved, or pinned artifact was mutated.
