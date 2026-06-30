# Trading Lab Manual Planner Safe Upgrade Manifest

Lane name: Trading Lab Manual Planner Safe Upgrade

Worktree: C:\NWR\Niners-War-Room-lane-trading-lab-upgrade-20260630

Branch: work/lane-trading-lab-upgrade-20260630

Base commit: e598249a2a9915366fc2087991bb0519be7c8403

Final commit: reported by Codex after commit creation

## SAFE_NOW Items Implemented

- neutral package context status
- no visible-score gap display
- no side score total display
- no market sanity panel
- structured manual planner rows
- editable manual checklist
- manual memo export with required disclaimer
- NFLVerse display-only player context panel for approved safe identity rows
- NFLVerse identity-review status display with player context details hidden
- missing-evidence panel with explicit next game/opponent/bye deferral

## NFLVerse Context Activated

- identity and availability cards use the tracked player context display artifact
- role and production/activity cards use tracked artifact facts only
- draft and non-financial contract context use tracked artifact facts only
- source/as-of/freshness labels are displayed where available
- NWR Player ID is used for manual row identity lookup where supplied
- selected board rows can resolve to the artifact's approved NWR Player ID when the artifact has a unique safe visible identity match
- identity-review rows show status only and hide details

## NFLVerse Items Still Deferred

- next game, opponent, and bye context
- identity proposal rows
- any `NEED_*`, `BLOCKED_*`, `Review needed`, or `Not enough information` value as a positive fact
- `ff_rankings`

## NEED_MODEL_GATE Items

- any model-derived roster or package score
- any confidence score
- any role or opportunity score

## BLOCKED Items

- trade calculator
- automatic trade finder
- automatic offer generator
- least-I-can-pay or minimum-offer logic
- pick valuation
- trade/package valuation
- market, ADP, DynastyProcess, or KTC valuation
- hidden sort
- source-truth or rank mutation

## Guardrail Confirmation

This lane keeps Trading Lab as manual planning only. It does not wire raw NFLVerse data, import external datasets from app pages, fetch public sources, mutate ranks, create hidden scores, calculate trade or pick values, or deploy.

## Known Limitations

- schedule, opponent, and bye context remain unavailable.
- identity proposals remain unapproved and hidden from details.
- human review still needs to confirm the page workflow in browser.

## Merge Readiness Verdict

Pending final validation in Codex report.
