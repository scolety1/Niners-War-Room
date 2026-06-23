# NWR Market Baseline App Integration Map V1 - 2026-06-23

## Purpose

This map defines where DynastyProcess market baseline can appear once app/lane work resumes.
It is intentionally modular: pages should call `src/services/market_baseline_service.py` and
opt in through `src/services/market_baseline_registry.py` instead of hand-joining CSVs.

## Player Compare

Fit:

- Market baseline block labeled `Market Baseline / Display-Only`.
- NWR vs market gap using `NWR higher than market`, `NWR lower than market`, or
  `Aligned with market`.
- Age and source cross-check where join confidence is high or medium.
- Pick/player value context when comparing a player against a pick package.

Rules:

- No candidate rank, final board rank, Dynasty Rank, or model score changes.
- No default sort from market fields.
- Stale data shows `Market data stale`.

## Trading Lab

Fit:

- Pick values for 2026, 2027, and 2028 picks.
- Player market value baseline for package sanity checks.
- Market side vs NWR side recap language.
- Display-only package context, not final advice.

Rules:

- Use market values as sanity context only.
- Existing NWR trade math remains the decision surface.
- Missing pick labels return unavailable market context, not inferred values.

## Dynasty Rankings

Fit:

- Optional market sanity columns in an advanced or configurable view.
- Optional filter for NWR much higher/lower than market.
- No default clutter in the main rankings table.

Rules:

- Market columns are hidden by default.
- Market rank is never the default rank, fallback rank, or tie-break sort.
- No hidden sort fields.

## Live Draft Room

Fit:

- Warning-only and timing-only context.
- Optional advanced-view market gap.
- Market stale/unavailable banner in data health area, not rank logic.

Rules:

- Never drive default draft rank.
- Never update frozen final board rank.
- Keep market context behind explicit advanced display.

## Post-Draft Mode

Fit:

- Trade recap context.
- Draft value recap.
- Market vs NWR disagreement review queue.
- Future pick value tracking.

Rules:

- Market disagreement is a review prompt, not a retroactive rank correction.
- Keep recap language clear that market values were display-only context.

## Settings / Data Health

Fit:

- Freshness status.
- Last scrape date.
- Upstream source commit.
- Local cache path.
- Scheduled task status.
- Manual refresh command text:
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_dynastyprocess_refresh_task.ps1`

Rules:

- Data Health may display operational paths and commands.
- It must not register, unregister, or run hosted deployment actions without explicit user action.

## Registry Pattern

Future pages should request their market baseline usage from
`src/services/market_baseline_registry.py`.

Each page defines:

- Enabled yes/no.
- Fields allowed.
- Display label.
- Default visible yes/no.
- Stale behavior.
- Sort allowed.
- Model input allowed.

Current global rule: `model_input_allowed=False` and `sort_allowed=False` for every page.
