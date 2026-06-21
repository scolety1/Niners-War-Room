# NWR Draft-Day Review Export V1 - 2026-06-22

Status: GREEN for local-only review export. No model is approved.

This document records the local draft-day review package built from the repaired
and post-tune-audited Model Candidate V1 research package. It does not approve
private value, rankings, hidden sort, Mock Draft behavior, simulations, final
draft advice, deployment, `latest_candidate`, or `latest_approved`.

## Local-Only Export

Export package root:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_review_package_20260622`

Static HTML dashboard:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_review_package_20260622\index.html`

Optional zip package:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_review_package_20260622.zip`

The export package is local-only and is not committed to the repository.

## How To Open

Open this file locally:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_review_package_20260622\index.html`

Double-click `index.html` to open it in a browser. No server, port, hosted
deployment, or public access is required. To move it to another computer, copy
the full folder:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_review_package_20260622`

## Model Posture

| Position | Posture |
| --- | --- |
| QB | Baseline/control preferred for review; no V1 research candidate selected. |
| RB | `role_usage_core` remains a local-only research candidate. |
| TE | Baseline/reference preferred for review; no V1 research candidate selected. |
| WR | `safe_no_snap_no_depth_rank` remains a local-only research candidate. |
| WR vendor | `vendor_rotowire_receiving_redzone` remains research-only / yellow hold / source-license review required. |

## Repaired Candidate Summary

| Position | Candidate | Top-N | Years beating baseline | Worst drawdown | Status |
| --- | --- | ---: | ---: | ---: | --- |
| RB | `role_usage_core` | 0.500 | 3 | -0.042 | research evidence only |
| WR | `safe_no_snap_no_depth_rank` | 0.528 | 2 | -0.028 | research evidence only |

These candidates are safe to review as evidence, but they are not approved for
private value, rankings, hidden sort, Mock Draft logic, simulations, final draft
advice, `latest_candidate`, or `latest_approved`.

## Vendor Hold Status

WR `vendor_rotowire_receiving_redzone` remains `VENDOR_RESEARCH_ONLY` and
`YELLOW_HOLD`. It requires source/license review and must not be used as a safe
model signal, private-value source, ranking source, Mock Draft source,
simulation source, or final advice source.

## Export Contents

The local-only export package includes:

- `README_START_HERE.md`
- `index.html`
- `LOCAL_ACCESS_INSTRUCTIONS.md`
- `MODEL_POSTURE_BY_POSITION.csv`
- `SAFE_RESEARCH_CANDIDATES.csv`
- `HOLD_AND_REJECTED_VARIANTS.csv`
- `VENDOR_RESEARCH_HOLD.md`
- `GUARDRAILS_STATUS.md`
- `WHAT_IS_SAFE_TO_USE_TOMORROW.md`
- `WHAT_IS_NOT_APPROVED.md`
- `REPAIR_AND_QA_SUMMARY.md`
- `SOURCE_PATHS.md`

The repo doc contains no raw local artifact dumps, raw vendor rows, raw
prediction dumps, private value, final rankings, or final draft advice.

## Guardrail Statement

This export is a practical local review package only. It does not create or
update `latest_candidate` or `latest_approved`, does not approve private value
or rankings, does not update Mock Draft behavior, does not run simulations, and
does not authorize vendor-source use.
