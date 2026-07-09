# Provider Response Reopen Conditions V1

## Reopen Standard

The route source recovery lane should stay closed unless one of the following occurs:

1. a provider grants usable permission or a license,
2. a stable legal API/export is found,
3. a separate source-admission lane validates identity, coverage, reproducibility, missingness, provenance, and decision-date safety.

## Provider Response That May Reopen

A provider response may justify reopening only if it confirms, in writing or contract terms:

- actual player-level `routes_run`
- WR, TE, and RB pass-catcher coverage, or documented omissions
- stable player ID fields
- player name, team, season, and position fields
- season grain at minimum
- week or game grain if available
- field dictionary
- historical coverage range
- update cadence
- missingness or eligibility rules
- reproducible API, export, static file, data room, or signed delivery path
- internal storage permission
- permission to compute derived internal YPRR and TPRR
- redistribution, display, retention, and model-use restrictions
- provenance, checksum, schema version, or source update timestamp

## Response That Does Not Reopen

Do not reopen for:

- public page visibility alone
- client object visibility alone
- screenshots
- manual copy permission
- a sample spreadsheet without terms
- name-only player rows
- UI-only access
- no export/API/support path
- no storage permission
- no derived metric permission
- no RB coverage without documented omission policy
- private-account or paywalled-only access without contract review

## If A Response Arrives

Record response metadata only. Do not copy raw route data into the repo. Do not calculate YPRR or TPRR. Open a separate source-admission lane if the response appears to satisfy the reopen standard.

## Current Closeout State

No provider response is confirmed in this closeout state. No source-admission lane is triggered.
