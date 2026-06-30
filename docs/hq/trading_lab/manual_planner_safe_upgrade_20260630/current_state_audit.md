# Trading Lab Manual Planner Safe Upgrade Current-State Audit

Date: 2026-06-30

Branch: work/lane-trading-lab-upgrade-20260630

Base: e598249a2a9915366fc2087991bb0519be7c8403

## Finding

The Trading Lab page was already scoped as draft-day decision support, but the active UI and service still exposed recommendation-adjacent behavior:

- package review labels could imply a directional outcome
- visible-score gap framing appeared in the primary summary
- a market sanity panel rendered package-level market totals and gap labels
- Trade Away and Trade For pick planners used comma-split text rows instead of structured manual rows
- checklist rows were static rather than editable

## Safety Classification

SAFE_NOW:

- remove directional package review labels
- remove visible-score gap and side total framing
- remove the primary market sanity panel
- replace comma-split planner rows with structured manual rows
- add editable checklist state
- add manual memo exports with the required no-valuation disclaimer
- add missing-evidence placeholders while nflverse refresh-health is not merged green

WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN:

- roster, weekly roster, injury, depth chart, snap count, raw production, draft-pick, and contract context cards
- ff_playerids identity joins
- freshness labels from newly refreshed nflverse datasets

BLOCKED:

- automatic trade finder
- automatic offer generation
- pick or package valuation
- market, ADP, DynastyProcess, or KTC valuation
- hidden sort or source-truth mutation
