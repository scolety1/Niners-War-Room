# NWR Master Safe Evidence Operator Quickstart

Date: 2026-06-26

## Start Here

```powershell
cd C:\NWR\Niners-War-Room-master-cfbd-identity-final-integration
git status --short -b
.\scripts\start_draft_day_app.ps1 -Port 8531
```

Open:

`http://127.0.0.1:8531/drafting-mode`

## What To Use For Draft/Decision Work

- Draft cockpit: `/drafting-mode`
- Full dynasty rankings: `/rankings`
- Live draft board: `/live-draft-room`
- Cheat sheet: `/cheat-sheets`
- Player comparison: `/player-compare`
- Trade review: `/trading-lab`
- Post-draft recap: `/post-draft-mode`
- Settings/Data Health: `/settings-data-health`

## Evidence Review Only

- Unified Universe: `/unified-universe-review`
- NFL Usage Evidence: `/nfl-usage-evidence-review`
- Evidence Integration Summary: `/evidence-integration-review`

Use these pages to inspect evidence status, not to make automated ranking decisions.

## Plain-English Safety Rules

- CFBD is not model input.
- NFL usage is not model input.
- Unified Universe is not wired into Drafting Mode or Dynasty Rankings.
- DynastyProcess is market context only.
- Outcome columns are display-only.
- Proxy drop evidence is not training truth.
- RotoWire scraping is blocked.
- Missing data remains `Not enough information`.

## If Something Looks Wrong

1. Check `/settings-data-health`.
2. Check `/evidence-integration-review`.
3. Confirm the app is running from the Master worktree, not an old lane preview.
4. Confirm `git status --short -b` is clean.
5. Do not copy raw cache files into the repo.

## Raw Data That Must Stay Outside Git

- `C:\NWR_SHARED_DATA\`
- `local_exports\`
- runtime JSON exports
- raw nflverse / CFBD payloads
- secrets, keys, cookies, tokens

## Next Safe Work

The next best lane is a human-review gate, not automatic wiring:

1. Review CFBD identity rows.
2. Resolve Unified Universe identity/age blockers.
3. Decide whether NFL usage fields are display-only candidates.
4. Only then consider app review toggles or model-candidate evaluation.
