# NWR GitHub-Safe Draft-Day Export - 2026-06-22

Status: GREEN.

This document records the sanitized repo-contained static export of Final Draft
Board V1. It exists so Tim can `git pull` on his laptop and open the board
locally without access to the local shared-data folder.

## Repo Export Folder

`docs/draft_day_exports/final_board_v1_20260622/`

Open first:
`docs/draft_day_exports/final_board_v1_20260622/OPEN_THIS_FIRST.html`

Static dashboard:
`docs/draft_day_exports/final_board_v1_20260622/index.html`

Board CSV:
`docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`

Board workbook:
`docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.xlsx`

## Included Files

| File | Size bytes |
| --- | ---: |
| `FINAL_DRAFT_BOARD_V1_FROZEN.csv` | 62085 |
| `FINAL_DRAFT_BOARD_V1_FROZEN.xlsx` | 32769 |
| `FREEZE_MANIFEST.csv` | 1261 |
| `GUARDRAILS_STATUS.md` | 409 |
| `index.html` | 16852 |
| `LOCAL_ACCESS_INSTRUCTIONS.md` | 344 |
| `OPEN_THIS_FIRST.html` | 1194 |
| `README_START_HERE.md` | 941 |
| `WHAT_NOT_TO_USE_TOMORROW.md` | 353 |
| `WHAT_TO_USE_TOMORROW.md` | 270 |

## Board Summary

| Check | Result |
| --- | --- |
| Board rows | 66 |
| Required visible rank fields | present |
| Hidden sort fields | none |
| Vendor safe-signal rows | none |
| Raw vendor rows | none |
| Raw prediction dumps | none |
| Local shared-data paths in board CSV | removed |
| Credential-like strings | none found |

The repo CSV removes the local-only source path column from the frozen shared
package so Tim's laptop copy is portable and GitHub-safe.

## Laptop Instructions

After pulling `work/hq-parallel-control`, open:

`docs/draft_day_exports/final_board_v1_20260622/OPEN_THIS_FIRST.html`

Fallbacks:

- `docs/draft_day_exports/final_board_v1_20260622/index.html`
- `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.xlsx`
- `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`

No server, exposed port, deployment, GitHub Pages, or public hosting is needed.

## Guardrails

- Did not commit raw vendor CSVs.
- Did not commit raw prediction dumps.
- Did not commit the full shared-data tree.
- Did not expose credentials.
- Did not deploy or enable hosted/public access.
- Did not mutate pinned snapshot.
- Did not update `latest_candidate` or `latest_approved`.
- Did not change Mock Draft logic.
- Did not create hidden sort fields.
- Did not include vendor research rows.
- Did not add final draft advice beyond the already frozen visible board.
